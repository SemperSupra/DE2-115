#!/usr/bin/env python3
import argparse
import subprocess
import sys
import time

from litex import RemoteClient


def run_ping(host, count):
    result = subprocess.run(
        ["ping", host, "-n", str(count)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=max(10, count * 3),
    )
    print(result.stdout.strip())
    if result.returncode != 0:
        raise SystemExit(f"ping failed with exit code {result.returncode}")


def wait_for_server(port, timeout_s):
    deadline = time.time() + timeout_s
    last_error = None
    while time.time() < deadline:
        try:
            wb = RemoteClient(host="127.0.0.1", port=port)
            wb.open()
            wb.close()
            return
        except Exception as e:
            last_error = e
            time.sleep(0.25)
    raise RuntimeError(f"litex_server did not become ready: {last_error}")


def etherbone_smoke(args):
    wb = RemoteClient(host="127.0.0.1", port=args.bind_port, csr_csv=args.csr_csv)
    wb.open()
    try:
        ident = "".join(chr(wb.read(0xF0006000 + 4 * i) & 0xFF) for i in range(24))
        print(f"IDENT_PREFIX {ident!r}")

        before_g = wb.regs.leds_g_out.read()
        before_r = wb.regs.leds_r_out.read()
        # Firmware owns the green LEDs as a heartbeat, so use them only as a
        # best-effort access probe. Red LEDs are stable for sustained CSR stress.
        wb.regs.leds_g_out.write(0x5A)
        probe_g = wb.regs.leds_g_out.read()
        for i in range(args.csr_loops):
            r = (0xA55A ^ (i * 0x1111)) & 0xFFFF
            wb.regs.leds_r_out.write(r)
            got_r = wb.regs.leds_r_out.read()
            if got_r != r:
                raise RuntimeError(f"CSR mismatch loop={i} leds_r 0x{got_r:x}/0x{r:x}")
        print(
            f"ETHERBONE_CSR_STRESS_OK loops={args.csr_loops} "
            f"leds_g_start=0x{before_g:08x} leds_g_probe=0x{probe_g:08x} "
            f"leds_r_start=0x{before_r:08x}"
        )
    finally:
        wb.close()


def main():
    p = argparse.ArgumentParser(description="DE2-115 low-speed Ethernet regression test")
    p.add_argument("--board-ip", default="192.168.178.50")
    p.add_argument("--board-udp-port", type=int, default=1234)
    p.add_argument("--bind-port", type=int, default=1235)
    p.add_argument("--csr-csv", default="build/terasic_de2_115/csr.csv")
    p.add_argument("--ping-count", type=int, default=20)
    p.add_argument("--csr-loops", type=int, default=128)
    p.add_argument("--server-start-timeout", type=float, default=8.0)
    args = p.parse_args()

    run_ping(args.board_ip, args.ping_count)

    cmd = [
        "litex_server",
        "--udp",
        "--udp-ip", args.board_ip,
        "--udp-port", str(args.board_udp_port),
        "--bind-ip", "127.0.0.1",
        "--bind-port", str(args.bind_port),
    ]
    server = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        wait_for_server(args.bind_port, args.server_start_timeout)
        etherbone_smoke(args)
        print("ETHERNET_LOW_SPEED_TEST_PASS")
    finally:
        server.terminate()
        try:
            out, _ = server.communicate(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()
            out, _ = server.communicate(timeout=3)
        if out:
            sys.stdout.write(out)


if __name__ == "__main__":
    main()
