from migen import *
from migen.fhdl.specials import Tristate
from litex.gen import *
from litex.build.io import DDROutput
from litex.soc.interconnect import wishbone
from litex.soc.cores.clock import CycloneIVPLL
from litex.soc.cores.gpio import GPIOIn, GPIOOut
from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *
from litex.soc.integration.soc import SoCRegion

from litedram.modules import IS42S16320
from litedram.phy import GENSDRPHY
from liteeth.phy.mii import LiteEthPHYMII

import de2_115_vga_platform
import time
import os
from isp1761 import ISP1761Bridge

# --- CRG ---
class _CRG(LiteXModule):
    def __init__(self, platform, sys_clk_freq):
        self.rst       = Signal()
        self.cd_sys    = ClockDomain()
        self.cd_sys_ps = ClockDomain() 
        self.cd_vga    = ClockDomain()

        # Clk / Rst
        clk50 = platform.request("clk50")
        self.comb += self.rst.eq(~platform.request("buttons", 0))

        # PLL
        self.pll = pll = CycloneIVPLL(speedgrade="-7")
        self.comb += pll.reset.eq(self.rst)
        pll.register_clkin(clk50, 50e6)
        pll.create_clkout(self.cd_sys,    sys_clk_freq)
        pll.create_clkout(self.cd_sys_ps, sys_clk_freq, phase=90)
        pll.create_clkout(self.cd_vga,    25.175e6)

        # SDRAM clock
        self.specials += DDROutput(1, 0, platform.request("sdram_clock"), ClockSignal("sys_ps"))

# --- Simple VGA Generator ---
class SimpleVGA(LiteXModule):
    def __init__(self, pads, hsync_n, vsync_n):
        # 640x480 @ 60Hz timings
        h_active = 640
        h_fp     = 16
        h_sync   = 96
        h_bp     = 48
        h_total  = h_active + h_fp + h_sync + h_bp

        v_active = 480
        v_fp     = 10
        v_sync   = 2
        v_bp     = 33
        v_total  = v_active + v_fp + v_sync + v_bp

        # Counters
        h_cnt = Signal(11)
        v_cnt = Signal(11)

        self.sync.vga += [
            If(h_cnt == h_total - 1,
                h_cnt.eq(0),
                If(v_cnt == v_total - 1,
                    v_cnt.eq(0)
                ).Else(
                    v_cnt.eq(v_cnt + 1)
                )
            ).Else(
                h_cnt.eq(h_cnt + 1)
            )
        ]

        # Sync Signals (Active Low)
        h_sync_active = (h_cnt >= (h_active + h_fp)) & (h_cnt < (h_active + h_fp + h_sync))
        v_sync_active = (v_cnt >= (v_active + v_fp)) & (v_cnt < (v_active + v_fp + v_sync))
        
        self.comb += [
            If(h_sync_active, hsync_n.eq(0)).Else(hsync_n.eq(1)),
            If(v_sync_active, vsync_n.eq(0)).Else(vsync_n.eq(1)),
        ]
        
        # RGB Signals (Simple pattern)
        display_on = (h_cnt < h_active) & (v_cnt < v_active)
        self.comb += [
            pads.de.eq(display_on),
            If(display_on,
                pads.r.eq(h_cnt[2:10]),
                pads.g.eq(v_cnt[2:10]),
                pads.b.eq(h_cnt[2:10] ^ v_cnt[2:10])
            ).Else(
                pads.r.eq(0),
                pads.g.eq(0),
                pads.b.eq(0)
            )
        ]

# --- Master SoC ---
class DE2_115VGAMaster(SoCCore):
    def __init__(self, sys_clk_freq=50e6, **kwargs):
        self.platform = de2_115_vga_platform.Platform()
        
        # Enable key components
        kwargs["cpu_type"] = "vexriscv"
        kwargs["integrated_rom_size"] = 0x20000 
        
        # SoCCore
        SoCCore.__init__(self, self.platform, sys_clk_freq, ident="LiteX VGA Test SoC on DE2-115", **kwargs)

        # CRG
        self.crg = _CRG(self.platform, sys_clk_freq)

        # SDRAM
        self.sdrphy = GENSDRPHY(self.platform.request("sdram"), sys_clk_freq)
        self.add_sdram("sdram",
            phy           = self.sdrphy,
            module        = IS42S16320(self.clk_freq, "1:1"),
            l2_cache_size = kwargs.get("l2_size", 8192)
        )

        # Ethernet
        self.submodules.ethphy = LiteEthPHYMII(
            clock_pads = self.platform.request("eth_clocks", 0),
            pads       = self.platform.request("eth", 0),
        )
        self.add_ethernet(phy=self.ethphy, dynamic_ip=False, local_ip="192.168.1.50")

        # SD Card
        self.add_sdcard()

        # System ID
        sysid = int(time.time())
        self.add_constant("SYSTEM_ID", sysid)
        
        # VGA
        vga_pads = self.platform.request("vga")
        hsync_n = self.platform.request("ping_hsync")
        vsync_n = self.platform.request("ping_vsync")
        
        # Simple VGA Generator (Bypasses LiteX Video cores)
        self.submodules.vga = SimpleVGA(vga_pads, hsync_n, vsync_n)
        
        # Connect VGA Signals
        self.comb += vga_pads.sync_n.eq(0)
        self.specials += DDROutput(0, 1, vga_pads.clk, ClockSignal("vga"))

        # Status I/O
        self.submodules.switches = GPIOIn(self.platform.request("switches"))
        self.submodules.leds_r   = GPIOOut(Cat([self.platform.request("user_led", i) for i in range(18)]))
        self.submodules.leds_g   = GPIOOut(self.platform.request("leds_g"))
        
        # 7 HEX displays
        for i in range(1, 8): 
            setattr(self.submodules, f"hex{i}", GPIOOut(self.platform.request("seven_seg", i)))

        # LCD Control
        lcd = self.platform.request("lcd")
        self.submodules.lcd = GPIOOut(Cat(lcd.on, lcd.blon, lcd.en, lcd.rw, lcd.rs, lcd.data))

        # USB (ISP1761)
        usb_pads = self.platform.request("usb_otg")
        self.submodules.usb_otg = ISP1761Bridge(usb_pads)
        self.bus.add_slave("usb_otg", self.usb_otg.bus, region=SoCRegion(origin=0x30000000, size=0x10000))
        self.comb += usb_pads.rst_n.eq(1) # Keep out of reset

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="LiteX SoC on DE2-115")
    parser.add_argument("--with-firmware", help="Path to firmware binary to integrate into ROM")
    args = parser.parse_args()

    soc_kwargs = {}
    if args.with_firmware:
        soc_kwargs["integrated_rom_init"] = get_mem_data(args.with_firmware, endianness="little")

    soc = DE2_115VGAMaster(**soc_kwargs)
    builder = Builder(soc, output_dir="build/terasic_de2_115", compile_software=True)
    builder.build(run=False)
