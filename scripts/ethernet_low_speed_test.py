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
        # Firmware owns the green and red LEDs as heartbeats in USB diagnostic
        # idle, so use green only as a best-effort access probe and stress a
        # firmware-stable display CSR instead.
        wb.regs.leds_g_out.write(0x5A)
        probe_g = wb.regs.leds_g_out.read()
        stress_reg_name = "lcd_out" if hasattr(wb.regs, "lcd_out") else "hex7_out"
        stress_reg = getattr(wb.regs, stress_reg_name)
        stress_mask = 0x7FF if stress_reg_name == "lcd_out" else 0x7F
        before_stress = stress_reg.read()
        for i in range(args.csr_loops):
            value = (0x5A5 ^ (i * 0x111)) & stress_mask
            stress_reg.write(value)
            got = stress_reg.read() & stress_mask
            if got != value:
                raise RuntimeError(
                    f"CSR mismatch loop={i} {stress_reg_name} 0x{got:x}/0x{value:x}"
                )
        stress_reg.write(before_stress)
        print(
            f"ETHERBONE_CSR_STRESS_OK loops={args.csr_loops} "
            f"stress={stress_reg_name} "
            f"leds_g_start=0x{before_g:08x} leds_g_probe=0x{probe_g:08x} "
            f"{stress_reg_name}_start=0x{before_stress:08x}"
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
