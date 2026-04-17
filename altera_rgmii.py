from migen import *
from migen.genlib.resetsync import AsyncResetSynchronizer

from litex.gen import *

from litex.build.io import DDROutput, DDRInput

from liteeth.common import *
from liteeth.phy.common import *

# LiteEth PHY RGMII TX -----------------------------------------------------------------------------

class LiteEthPHYRGMIITX(LiteXModule):
    def __init__(self, pads):
        self.sink = sink = stream.Endpoint(eth_phy_description(8))

        # # #

        self.specials += [
            DDROutput(
                clk = ClockSignal("eth_tx"),
                i1  = sink.valid,
                i2  = sink.valid,
                o   = pads.tx_ctl,
            )
        ]
        for i in range(4):
            self.specials += [
                DDROutput(
                    clk = ClockSignal("eth_tx"),
                    i1  = sink.data[i],
                    i2  = sink.data[4+i],
                    o   = pads.tx_data[i],
                )
            ]
        self.comb += sink.ready.eq(1)

# LiteEth PHY RGMII RX -----------------------------------------------------------------------------

class LiteEthPHYRGMIIRX(LiteXModule):
    def __init__(self, pads, with_inband_status=True):
        self.source = source = stream.Endpoint(eth_phy_description(8))

        if with_inband_status:
            self.inband_status = CSRStatus(fields=[
                CSRField("link_status", size=1, values=[
                    ("``0b0``", "Link down."),
                    ("``0b1``", "Link up."),
                ]),
                CSRField("clock_speed", size=2, values=[
                    ("``0b00``", "2.5MHz   (10Mbps)."),
                    ("``0b01``", "25MHz   (100MBps)."),
                    ("``0b10``", "125MHz (1000MBps)."),
                ]),
                CSRField("duplex_status", size=1, values=[
                    ("``0b0``", "Half-duplex."),
                    ("``0b1``", "Full-duplex."),
                ]),
            ])

        # # #

        rx_ctl         = Signal(2)
        rx_ctl_reg     = Signal(2)
        rx_data        = Signal(8)
        rx_data_reg    = Signal(8)

        self.specials += [
            DDRInput(
                clk = ClockSignal("eth_rx"),
                i   = pads.rx_ctl,
                o1  = rx_ctl[0],
                o2  = rx_ctl[1],
            )
        ]
        self.sync += rx_ctl_reg.eq(rx_ctl)
        for i in range(4):
            self.specials += [
                DDRInput(
                    clk = ClockSignal("eth_rx"),
                    i   = pads.rx_data[i],
                    o1  = rx_data[i],
                    o2  = rx_data[i+4],
                )
            ]
        self.sync += rx_data_reg.eq(rx_data)

        rx_ctl_reg_d = Signal(2)
        self.sync += rx_ctl_reg_d.eq(rx_ctl_reg)

        last = Signal()
        self.comb += last.eq(~rx_ctl_reg[0] & rx_ctl_reg_d[0])
        self.sync += [
            source.valid.eq(rx_ctl_reg[0]),
            source.data.eq(rx_data_reg)
        ]
        self.comb += source.last.eq(last)

        if with_inband_status:
            self.sync += [
                If(rx_ctl == 0b00,
                    self.inband_status.fields.link_status.eq(  rx_data[0]),
                    self.inband_status.fields.clock_speed.eq(  rx_data[1:3]),
                    self.inband_status.fields.duplex_status.eq(rx_data[3]),
                )
            ]

# LiteEth PHY RGMII CRG ----------------------------------------------------------------------------

class LiteEthPHYRGMIICRG(LiteXModule):
    def __init__(self, clock_pads, pads, with_hw_init_reset, tx_clk=None):
        self._reset = CSRStorage()

        # # #

        # RX Clock
        self.cd_eth_rx = ClockDomain()
        self.comb += self.cd_eth_rx.clk.eq(clock_pads.rx)

        # TX Clock
        self.cd_eth_tx = ClockDomain()
        if isinstance(tx_clk, Signal):
            self.comb += self.cd_eth_tx.clk.eq(tx_clk)
        else:
            self.comb += self.cd_eth_tx.clk.eq(self.cd_eth_rx.clk)

        self.specials += [
            DDROutput(
                clk = ClockSignal("eth_tx"),
                i1  = 1,
                i2  = 0,
                o   = clock_pads.tx,
            )
        ]

        # Reset
        self.reset = reset = Signal()
        if with_hw_init_reset:
            self.hw_reset = LiteEthPHYHWReset()
            self.comb += reset.eq(self._reset.storage | self.hw_reset.reset)
        else:
            self.comb += reset.eq(self._reset.storage)
        if hasattr(pads, "rst_n"):
            self.comb += pads.rst_n.eq(~reset)
        self.specials += [
            AsyncResetSynchronizer(self.cd_eth_tx, reset),
            AsyncResetSynchronizer(self.cd_eth_rx, reset),
        ]

class LiteEthPHYRGMII(LiteXModule):
    dw          = 8
    tx_clk_freq = 125e6
    rx_clk_freq = 125e6
    def __init__(self, clock_pads, pads, with_hw_init_reset=True,
        with_inband_status = True,
        tx_clk             = None,
        ):
        self.crg = LiteEthPHYRGMIICRG(clock_pads, pads, with_hw_init_reset, tx_clk)
        self.tx  = ClockDomainsRenamer("eth_tx")(LiteEthPHYRGMIITX(pads))
        self.rx  = ClockDomainsRenamer("eth_rx")(LiteEthPHYRGMIIRX(pads, with_inband_status))
        self.sink, self.source = self.tx.sink, self.rx.source

        if hasattr(pads, "mdc"):
            self.mdio = LiteEthPHYMDIO(pads)
