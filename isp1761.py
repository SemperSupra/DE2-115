from migen import *
from migen.fhdl.specials import Tristate
from litex.soc.interconnect import wishbone

class ISP1761Bridge(Module):
    """
    LiteX Wishbone Bridge for NXP ISP1761 USB Controller.
    Added wait-states for asynchronous timing compatibility.
    """
    def __init__(self, pads):
        self.bus = bus = wishbone.Interface()
        
        data_width = len(pads.data)
        data_w = Signal(data_width)
        data_r = Signal(data_width)
        data_oe = Signal()
        self.specials += Tristate(pads.data, data_w, data_oe, data_r)

        # Wait-state counter
        count = Signal(3)
        
        self.comb += [
            pads.cs_n.eq(~bus.cyc | ~bus.stb),
            pads.rd_n.eq(~bus.cyc | ~bus.stb | bus.we),
            pads.wr_n.eq(~bus.cyc | ~bus.stb | ~bus.we),
            
            pads.addr.eq(bus.adr[0:len(pads.addr)]),
            
            data_oe.eq(bus.we & bus.cyc & bus.stb),
            data_w.eq(bus.dat_w[:data_width]),
            bus.dat_r.eq(data_r)
        ]
        
        self.sync += [
            If(bus.cyc & bus.stb & ~bus.ack,
                count.eq(count + 1),
                If(count == 5, # 5-cycle wait state
                    bus.ack.eq(1)
                )
            ).Else(
                count.eq(0),
                bus.ack.eq(0)
            )
        ]
