from migen import *
from litex.soc.interconnect import wishbone


class ISP1761Bridge(Module):
    """
    LiteX Wishbone bridge for the DE2-115 CY7C67200 HPI port.

    Terasic's working bridge is intentionally simple: HPI control/address/data
    follow the CPU bus directly, and the CPU-side fabric supplies wait states.
    Keep that behavior here and use a small FSM only to delay/serialize the
    Wishbone acknowledgement.
    """
    def __init__(self, pads, diag_in=0):
        self.bus = bus = wishbone.Interface()
        self.force_hpi_boot = Signal()
        self.dbg_probe = Signal(160)

        self.specials += Instance("cy7c67200_wb_bridge",
            i_clk=ClockSignal(),
            i_rst=ResetSignal(),
            i_wb_adr=bus.adr,
            i_wb_dat_w=bus.dat_w,
            o_wb_dat_r=bus.dat_r,
            i_wb_cyc=bus.cyc,
            i_wb_stb=bus.stb,
            i_wb_we=bus.we,
            o_wb_ack=bus.ack,
            io_hpi_data=pads.data,
            o_hpi_addr=pads.addr,
            o_hpi_rd_n=pads.rd_n,
            o_hpi_wr_n=pads.wr_n,
            o_hpi_cs_n=pads.cs_n,
            o_hpi_rst_n=pads.rst_n,
            i_diag_in=diag_in,
            o_dbg_probe=self.dbg_probe,
        )
