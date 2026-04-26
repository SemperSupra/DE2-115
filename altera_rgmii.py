from migen import *
from migen.genlib.resetsync import AsyncResetSynchronizer

from litex.gen import *

from litex.build.io import DDROutput, DDRInput

from liteeth.common import *
from liteeth.phy.common import *

# LiteEth PHY RGMII TX -----------------------------------------------------------------------------

class LiteEthPHYRGMIITX(LiteXModule):
    def __init__(self, pads, mode_1000=None):
        self.sink = sink = stream.Endpoint(eth_phy_description(8))

        # # #

        gmii_mode = mode_1000 if mode_1000 is not None else Constant(1)
        mii_mode = Signal()
        self.comb += mii_mode.eq(~gmii_mode)

        mii_converter = stream.Converter(8, 4)
        self.submodules += mii_converter

        mii_tx_valid = Signal()
        mii_tx_data = Signal(4)
        self.comb += [
            mii_converter.sink.valid.eq(sink.valid & mii_mode),
            mii_converter.sink.data.eq(sink.data),
            mii_converter.source.ready.eq(1),
            sink.ready.eq(Mux(mii_mode, mii_converter.sink.ready, 1)),
            mii_tx_valid.eq(mii_converter.source.valid),
            mii_tx_data.eq(mii_converter.source.data),
        ]

        tx_sample_valid = Signal()
        self.comb += tx_sample_valid.eq(sink.valid & sink.ready)

        mii_phy_half = Signal()
        mii_phy_low = Signal(4)
        mii_phy_byte = Signal(8)
        mii_phy_byte_valid = Signal()
        self.sync += [
            mii_phy_byte_valid.eq(0),
            If(mii_mode & mii_tx_valid,
                If(~mii_phy_half,
                    mii_phy_low.eq(mii_tx_data),
                    mii_phy_half.eq(1),
                ).Else(
                    mii_phy_byte.eq(Cat(mii_phy_low, mii_tx_data)),
                    mii_phy_byte_valid.eq(1),
                    mii_phy_half.eq(0),
                )
            ).Elif(~mii_tx_valid,
                mii_phy_half.eq(0),
            )
        ]

        eth_tx_dbg_source = Signal(4)
        eth_tx_dbg_bytes = [Signal(8, name=f"eth_tx_dbg_byte{i}") for i in range(16)]
        eth_tx_dbg_ctl = Signal(32)
        eth_tx_dbg_len = Signal(12)
        eth_tx_dbg_count = Signal(5)
        eth_tx_dbg_frames = Signal(8)
        eth_tx_dbg_active = Signal()
        eth_tx_dbg_done = Signal()
        eth_tx_valid_d = Signal()
        eth_tx_dbg_mode = Signal(3)
        eth_tx_phy_sample_valid = Signal()
        eth_tx_phy_sample_data = Signal(8)
        eth_tx_dbg_sample_valid = Signal()
        eth_tx_dbg_sample_data = Signal(8)

        self.comb += [
            eth_tx_dbg_mode.eq(eth_tx_dbg_source[1:4]),
            eth_tx_phy_sample_valid.eq(Mux(mii_mode, mii_phy_byte_valid, sink.valid)),
            eth_tx_phy_sample_data.eq(Mux(mii_mode, mii_phy_byte, sink.data)),
            eth_tx_dbg_sample_valid.eq(Mux(eth_tx_dbg_mode == 1, eth_tx_phy_sample_valid, tx_sample_valid)),
            eth_tx_dbg_sample_data.eq(Mux(eth_tx_dbg_mode == 1, eth_tx_phy_sample_data, sink.data)),
        ]
        self.sync += eth_tx_valid_d.eq(eth_tx_dbg_sample_valid)
        eth_tx_start = Signal()
        self.comb += eth_tx_start.eq(eth_tx_dbg_sample_valid & ~eth_tx_valid_d)

        clear_eth_tx_debug = [
            eth_tx_dbg_ctl.eq(0),
            eth_tx_dbg_len.eq(0),
            eth_tx_dbg_count.eq(0),
            eth_tx_dbg_frames.eq(0),
            eth_tx_dbg_active.eq(0),
            eth_tx_dbg_done.eq(0),
        ] + [byte.eq(0) for byte in eth_tx_dbg_bytes]
        store_eth_tx_byte = {}
        for i in range(16):
            store_eth_tx_byte[i] = [
                eth_tx_dbg_bytes[i].eq(eth_tx_dbg_sample_data),
                eth_tx_dbg_ctl[2*i:2*i+2].eq(Cat(eth_tx_dbg_sample_valid, eth_tx_dbg_sample_valid)),
            ]

        self.sync += [
            If(eth_tx_dbg_source[0],
                *clear_eth_tx_debug
            ).Elif(~eth_tx_dbg_done,
                If(~eth_tx_dbg_active & eth_tx_start,
                    eth_tx_dbg_frames.eq(eth_tx_dbg_frames + 1),
                    eth_tx_dbg_active.eq(1),
                    eth_tx_dbg_len.eq(1),
                    eth_tx_dbg_count.eq(1),
                    eth_tx_dbg_bytes[0].eq(eth_tx_dbg_sample_data),
                    eth_tx_dbg_ctl[0:2].eq(Cat(eth_tx_dbg_sample_valid, eth_tx_dbg_sample_valid)),
                ).Elif(eth_tx_dbg_active,
                    If(eth_tx_dbg_sample_valid,
                        eth_tx_dbg_len.eq(eth_tx_dbg_len + 1),
                        If(eth_tx_dbg_count < 16,
                            Case(eth_tx_dbg_count, store_eth_tx_byte),
                            eth_tx_dbg_count.eq(eth_tx_dbg_count + 1),
                        )
                    ).Else(
                        eth_tx_dbg_active.eq(0),
                        eth_tx_dbg_done.eq(1),
                    )
                )
            )
        ]

        eth_tx_dbg_probe = Cat(
            Cat(*eth_tx_dbg_bytes),
            eth_tx_dbg_ctl,
            eth_tx_dbg_len,
            eth_tx_dbg_count,
            eth_tx_dbg_frames,
            Constant(0, 4),
            eth_tx_dbg_sample_valid,
            eth_tx_dbg_active,
            eth_tx_dbg_done,
        )
        self.specials += Instance("altsource_probe",
            p_sld_auto_instance_index="YES",
            p_sld_instance_index=2,
            p_instance_id="ETX0",
            p_probe_width=192,
            p_source_width=4,
            p_source_initial_value="0",
            i_probe=eth_tx_dbg_probe,
            o_source=eth_tx_dbg_source,
        )

        tx_ctl = Signal()
        self.comb += tx_ctl.eq(Mux(mii_mode, mii_tx_valid, sink.valid))
        self.specials += [
            DDROutput(
                clk = ClockSignal("eth_tx"),
                i1  = tx_ctl,
                i2  = tx_ctl,
                o   = pads.tx_ctl,
            )
        ]
        for i in range(4):
            self.specials += [
                DDROutput(
                    clk = ClockSignal("eth_tx"),
                    i1  = Mux(mii_mode, mii_tx_data[i], sink.data[i]),
                    i2  = Mux(mii_mode, mii_tx_data[i], sink.data[4+i]),
                    o   = pads.tx_data[i],
                )
            ]

# LiteEth PHY RGMII RX -----------------------------------------------------------------------------

class LiteEthPHYRGMIIRX(LiteXModule):
    def __init__(self, pads, with_inband_status=True, force_mii=False):
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
        rx_link_status = Signal()
        rx_clock_speed = Signal(2, reset=2)
        rx_duplex_status = Signal()
        self.mode_1000 = Signal()
        self.comb += self.mode_1000.eq(0 if force_mii else (rx_clock_speed == 0b10))

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

        gmii_valid = Signal()
        gmii_valid_d = Signal()
        gmii_data = Signal(8)
        gmii_last = Signal()
        self.sync += [
            gmii_valid.eq(rx_ctl_reg[0]),
            gmii_valid_d.eq(gmii_valid),
            gmii_data.eq(rx_data_reg),
        ]
        self.comb += gmii_last.eq(~gmii_valid & gmii_valid_d)

        mii_converter = ResetInserter()(stream.Converter(4, 8))
        self.submodules += mii_converter
        self.sync += [
            mii_converter.reset.eq(~rx_ctl_reg[0]),
            mii_converter.sink.valid.eq(1),
            mii_converter.sink.data.eq(rx_data_reg[0:4]),
        ]
        self.comb += [
            mii_converter.sink.last.eq(~rx_ctl_reg[0]),
            mii_converter.source.ready.eq(Mux(self.mode_1000, 1, source.ready)),
            source.valid.eq(Mux(self.mode_1000, gmii_valid, mii_converter.source.valid)),
            source.data.eq(Mux(self.mode_1000, gmii_data, mii_converter.source.data)),
            source.last.eq(Mux(self.mode_1000, gmii_last, mii_converter.source.last)),
        ]

        eth_dbg_source = Signal(4)
        eth_dbg_bytes = [Signal(8, name=f"eth_dbg_byte{i}") for i in range(16)]
        eth_dbg_ctl = Signal(32)
        eth_dbg_len = Signal(12)
        eth_dbg_count = Signal(5)
        eth_dbg_frames = Signal(8)
        eth_dbg_errors = Signal(4)
        eth_dbg_active = Signal()
        eth_dbg_done = Signal()
        eth_rx_start = Signal()
        eth_rx_er = Signal()
        eth_dbg_mode = Signal(3)
        eth_dbg_wait_sfd = Signal()
        source_valid_d = Signal()
        eth_dbg_sample_valid = Signal()
        eth_dbg_sample_start = Signal()
        eth_dbg_sample_data = Signal(8)
        eth_dbg_sample_ctl = Signal(2)
        self.sync += source_valid_d.eq(source.valid)
        self.comb += [
            eth_rx_start.eq(rx_ctl_reg[0] & ~rx_ctl_reg_d[0]),
            eth_rx_er.eq(rx_ctl_reg[0] ^ rx_ctl_reg[1]),
            eth_dbg_mode.eq(eth_dbg_source[1:4]),
            eth_dbg_sample_valid.eq(Mux(eth_dbg_mode == 2, source.valid, rx_ctl_reg[0])),
            eth_dbg_sample_start.eq(Mux(eth_dbg_mode == 2, source.valid & ~source_valid_d, eth_rx_start)),
            eth_dbg_sample_data.eq(Mux(eth_dbg_mode == 2, source.data, rx_data_reg)),
            eth_dbg_sample_ctl.eq(Mux(eth_dbg_mode == 2, Cat(source.valid, source.valid), rx_ctl_reg)),
        ]

        clear_eth_debug = [
            eth_dbg_ctl.eq(0),
            eth_dbg_len.eq(0),
            eth_dbg_count.eq(0),
            eth_dbg_frames.eq(0),
            eth_dbg_errors.eq(0),
            eth_dbg_active.eq(0),
            eth_dbg_done.eq(0),
            eth_dbg_wait_sfd.eq(0),
        ] + [byte.eq(0) for byte in eth_dbg_bytes]
        store_eth_byte = {}
        for i in range(16):
            store_eth_byte[i] = [
                eth_dbg_bytes[i].eq(eth_dbg_sample_data),
                eth_dbg_ctl[2*i:2*i+2].eq(eth_dbg_sample_ctl),
            ]

        self.sync += [
            If(eth_dbg_source[0],
                *clear_eth_debug
            ).Elif(~eth_dbg_done,
                If(~eth_dbg_active,
                    If(eth_dbg_mode == 1,
                        If(~eth_dbg_wait_sfd & eth_rx_start,
                            eth_dbg_frames.eq(eth_dbg_frames + 1),
                            eth_dbg_wait_sfd.eq(1),
                            If(eth_rx_er, eth_dbg_errors.eq(eth_dbg_errors + 1))
                        ).Elif(eth_dbg_wait_sfd,
                            If(rx_ctl_reg[0],
                                If(rx_data_reg == 0xd5,
                                    eth_dbg_wait_sfd.eq(0),
                                    eth_dbg_active.eq(1),
                                    eth_dbg_len.eq(0),
                                    eth_dbg_count.eq(0),
                                ),
                                If(eth_rx_er, eth_dbg_errors.eq(eth_dbg_errors + 1))
                            ).Else(
                                eth_dbg_wait_sfd.eq(0)
                            )
                        )
                    ).Elif(eth_dbg_sample_start,
                        eth_dbg_frames.eq(eth_dbg_frames + 1),
                        eth_dbg_active.eq(1),
                        eth_dbg_len.eq(1),
                        eth_dbg_count.eq(1),
                        eth_dbg_bytes[0].eq(eth_dbg_sample_data),
                        eth_dbg_ctl[0:2].eq(eth_dbg_sample_ctl),
                        If(eth_rx_er, eth_dbg_errors.eq(eth_dbg_errors + 1))
                    )
                ).Elif(eth_dbg_active,
                    If(eth_dbg_sample_valid,
                        eth_dbg_len.eq(eth_dbg_len + 1),
                        If(eth_dbg_count < 16,
                            Case(eth_dbg_count, store_eth_byte),
                            eth_dbg_count.eq(eth_dbg_count + 1),
                        ),
                        If(eth_rx_er, eth_dbg_errors.eq(eth_dbg_errors + 1))
                    ).Else(
                        eth_dbg_active.eq(0),
                        eth_dbg_done.eq(1),
                    )
                )
            )
        ]

        eth_dbg_probe = Cat(
            Cat(*eth_dbg_bytes),
            eth_dbg_ctl,
            eth_dbg_len,
            eth_dbg_count,
            eth_dbg_frames,
            eth_dbg_errors,
            rx_ctl_reg[0],
            eth_dbg_active,
            eth_dbg_done,
        )
        self.specials += Instance("altsource_probe",
            p_sld_auto_instance_index="YES",
            p_sld_instance_index=1,
            p_instance_id="ETH0",
            p_probe_width=192,
            p_source_width=4,
            p_source_initial_value="0",
            i_probe=eth_dbg_probe,
            o_source=eth_dbg_source,
        )

        if with_inband_status:
            self.comb += [
                self.inband_status.fields.link_status.eq(rx_link_status),
                self.inband_status.fields.clock_speed.eq(rx_clock_speed),
                self.inband_status.fields.duplex_status.eq(rx_duplex_status),
            ]
        self.sync += [
            If(rx_ctl == 0b00,
                rx_link_status.eq(rx_data[0]),
                rx_clock_speed.eq(rx_data[1:3]),
                rx_duplex_status.eq(rx_data[3]),
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
        force_mii          = False,
        ):
        self.crg = LiteEthPHYRGMIICRG(clock_pads, pads, with_hw_init_reset, tx_clk)
        self.rx  = ClockDomainsRenamer("eth_rx")(LiteEthPHYRGMIIRX(pads, with_inband_status, force_mii))
        self.tx  = ClockDomainsRenamer("eth_tx")(LiteEthPHYRGMIITX(pads, mode_1000=self.rx.mode_1000))
        self.sink, self.source = self.tx.sink, self.rx.source

        if hasattr(pads, "mdc"):
            self.mdio = LiteEthPHYMDIO(pads)
