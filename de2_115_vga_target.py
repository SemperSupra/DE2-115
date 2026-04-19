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
from altera_rgmii import LiteEthPHYRGMII
from litescope import LiteScopeAnalyzer

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
        self.cd_eth    = ClockDomain()

        # Clk / Rst
        clk50 = platform.request("clk50")
        self.comb += self.rst.eq(~platform.request("buttons", 0))

        # PLL
        self.pll = pll = CycloneIVPLL(speedgrade="-7")
        self.comb += pll.reset.eq(self.rst)
        pll.register_clkin(clk50, 50e6)
        pll.create_clkout(self.cd_sys,    sys_clk_freq)
        pll.create_clkout(self.cd_sys_ps, sys_clk_freq, phase=90)
        pll.create_clkout(self.cd_vga,    25e6)
        pll.create_clkout(self.cd_eth,    125e6)

        # Blinker (to verify sys_clk)
        self.counter = counter = Signal(32)
        self.sync.sys += counter.eq(counter + 1)
        self.comb += platform.request("user_led", 17).eq(counter[24])

        # SDRAM clock
        self.specials += DDROutput(1, 0, platform.request("sdram_clock"), ClockSignal("sys_ps"))

# --- Simple VGA Generator ---
class SimpleVGA(LiteXModule):
    def __init__(self, pads, hsync_n, vsync_n):
        # 640x480 with a 25 MHz pixel clock.
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
            pads.blank_n.eq(display_on),
            If(display_on,
                If(h_cnt < 160,
                    pads.r.eq(0xff),
                    pads.g.eq(0x00),
                    pads.b.eq(0x00)
                ).Elif(h_cnt < 320,
                    pads.r.eq(0x00),
                    pads.g.eq(0xff),
                    pads.b.eq(0x00)
                ).Elif(h_cnt < 480,
                    pads.r.eq(0x00),
                    pads.g.eq(0x00),
                    pads.b.eq(0xff)
                ).Else(
                    pads.r.eq(0xff),
                    pads.g.eq(0xff),
                    pads.b.eq(0xff)
                ),
                If((h_cnt < 8) | (h_cnt >= (h_active - 8)) | (v_cnt < 8) | (v_cnt >= (v_active - 8)),
                    pads.r.eq(0xff),
                    pads.g.eq(0xff),
                    pads.b.eq(0x00)
                )
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
        eth_port = 0
        eth_core_ip = os.environ.get("DE2_ETH_CORE_IP", "192.168.178.50")
        # LiteX requires ethmac_local_ip != ip_address when with_ethmac=True.
        ethmac_local_ip = os.environ.get("DE2_ETH_LOCAL_IP", "192.168.178.51")
        eth_remote_ip = os.environ.get("DE2_ETH_REMOTE_IP", "192.168.178.27")
        
        # Enable key components
        kwargs["cpu_type"] = "vexriscv"
        kwargs["integrated_rom_size"] = 0x10000
        kwargs["cpu_reset_address"] = 0x00000000
        
        # SoCCore
        SoCCore.__init__(self, self.platform, sys_clk_freq, ident="LiteX VGA Test SoC on DE2-115", **kwargs)
        
        # CRG
        self.crg = _CRG(self.platform, sys_clk_freq)
        self.cd_vga = self.crg.cd_vga

        # SDRAM
        self.sdrphy = GENSDRPHY(self.platform.request("sdram"), sys_clk_freq)
        self.add_sdram("sdram",
            phy           = self.sdrphy,
            module        = IS42S16320(self.clk_freq, "1:1"),
            l2_cache_size = kwargs.get("l2_size", 8192)
        )

        # Ethernet
        self.submodules.ethphy = LiteEthPHYRGMII(
            clock_pads = self.platform.request("eth_clocks", eth_port),
            pads       = self.platform.request("rgmii_eth", eth_port),
        )
        self.add_etherbone(
            phy=self.ethphy,
            ip_address=eth_core_ip,
            udp_port=1234,
            with_ethmac=True,
            ethmac_local_ip=ethmac_local_ip,
            ethmac_remote_ip=eth_remote_ip,
        )

        # Timer & UART
        self.add_timer()
        self.add_uart()

        # SD Card
        self.add_sdcard()

        # System ID
        sysid = int(time.time())
        self.add_constant("SYSTEM_ID", sysid)
        
        # VGA
        vga_pads = self.platform.request("vga")
        hsync_n = self.platform.request("ping_hsync")
        vsync_n = self.platform.request("ping_vsync")

        self.platform.add_source("vga_text_console.v")
        self.vga_text_bus = wishbone.Interface(data_width=32, adr_width=14)
        self.specials += Instance("vga_text_console",
            i_sys_clk=ClockSignal("sys"),
            i_sys_rst=ResetSignal("sys"),
            i_wb_adr=self.vga_text_bus.adr,
            i_wb_dat_w=self.vga_text_bus.dat_w,
            o_wb_dat_r=self.vga_text_bus.dat_r,
            i_wb_cyc=self.vga_text_bus.cyc,
            i_wb_stb=self.vga_text_bus.stb,
            i_wb_we=self.vga_text_bus.we,
            o_wb_ack=self.vga_text_bus.ack,
            i_vga_clk=ClockSignal("vga"),
            o_vga_r=vga_pads.r,
            o_vga_g=vga_pads.g,
            o_vga_b=vga_pads.b,
            o_vga_blank_n=vga_pads.blank_n,
            o_vga_hsync_n=hsync_n,
            o_vga_vsync_n=vsync_n,
        )
        self.bus.add_slave("vga_text", self.vga_text_bus,
            region=SoCRegion(origin=0x83000000, size=0x10000, cached=False))
        
        # Connect VGA Signals
        self.comb += vga_pads.sync_n.eq(0)
        self.specials += DDROutput(0, 1, vga_pads.clk, ClockSignal("vga"))

        # Add Peripherals
        for i in range(8):
            seg = self.platform.request("seven_seg", i)
            setattr(self.submodules, f"hex{i}", GPIOOut(Cat(seg.a, seg.b, seg.c, seg.d, seg.e, seg.f, seg.g)))
        
        self.submodules.leds_g = GPIOOut(self.platform.request("leds_g"))
        self.submodules.leds_r = GPIOOut(Cat([self.platform.request("user_led", i) for i in range(17)]))
        self.submodules.switches = GPIOIn(self.platform.request("switches", 0))

        # LCD Control
        lcd = self.platform.request("lcd")
        self.submodules.lcd = GPIOOut(Cat(lcd.on, lcd.blon, lcd.en, lcd.rw, lcd.rs, lcd.data))

        # USB (ISP1761)
        usb_pads = self.platform.request("usb_otg")
        
        # Drive USB strapping pins for HPI mode:
        # DREQ should be LOW, DACK# should be HIGH at reset de-assertion.
        self.comb += [
            usb_pads.dack_n.eq(0b11),
        ]

        self.platform.add_source("CY7C67200_IF.v")
        self.platform.add_source("cy7c67200_wb_bridge.v")
        
        diag_in = Cat(self.crg.pll.locked, self.crg.counter[24])
        self.submodules.usb_otg = ISP1761Bridge(usb_pads, diag_in=diag_in)
        self.bus.add_slave("usb_otg", self.usb_otg.bus,
            region=SoCRegion(origin=0x82000000, size=0x10000, cached=False))

        # LiteX-native debug core for HPI/Wishbone bring-up.
        sys_rst_debug = Signal()
        self.comb += sys_rst_debug.eq(ResetSignal("sys"))
        self.submodules.hpi_analyzer = LiteScopeAnalyzer(
            [
                self.crg.pll.locked,
                sys_rst_debug,
                self.usb_otg.bus.adr,
                self.usb_otg.bus.dat_w,
                self.usb_otg.bus.dat_r,
                self.usb_otg.bus.cyc,
                self.usb_otg.bus.stb,
                self.usb_otg.bus.we,
                self.usb_otg.bus.ack,
                usb_pads.addr,
                usb_pads.rd_n,
                usb_pads.wr_n,
                usb_pads.cs_n,
                usb_pads.rst_n,
                self.usb_otg.dbg_probe,
            ],
            depth        = 2048,
            clock_domain = "sys",
            register     = True,
            csr_csv      = "analyzer.csv",
        )

        # Leave CY7C67200 boot-selection pins to the board straps. Driving HPI
        # data pins during reset caused readback to float high on this board.
        # The registered Terasic HPI interface now owns OTG_RST_N.
        self.comb += self.usb_otg.force_hpi_boot.eq(0)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="LiteX SoC on DE2-115")
    parser.add_argument("--with-firmware", help="Path to firmware binary to integrate into ROM")
    args = parser.parse_args()

    soc_kwargs = soc_core_argdict(args)
    if args.with_firmware:
        soc_kwargs["integrated_rom_size"] = 0x10000
        soc_kwargs["integrated_rom_init"] = get_mem_data(args.with_firmware, endianness="little")

    soc = DE2_115VGAMaster(**soc_kwargs)
    builder = Builder(soc, output_dir="build/terasic_de2_115", compile_software=True)
    builder.build(run=False)
