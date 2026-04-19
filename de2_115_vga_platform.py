from litex_boards.platforms.terasic_de2_115 import Platform as BasePlatform
from litex.build.generic_platform import *

# Definitive DE2-115 Bank Voltages from NIOS Demo .pin file:
# Bank 1, 2, 3, 4, 8: 3.3V
# Bank 5, 6, 7: 2.5V

_extra_io = [
    # VGA - Bank 3 (3.3V) & Bank 8 (3.3V)
    ("vga", 0,
        Subsignal("r",     Pins("E12 E11 D10 F12 G10 J12 H8 H10"), IOStandard("3.3-V LVTTL")),
        Subsignal("g",     Pins("G8 G11 F8 H12 C8 B8 F10 C9"), IOStandard("3.3-V LVTTL")),
        Subsignal("b",     Pins("B10 A10 C11 B11 A11 C12 D11 D12"), IOStandard("3.3-V LVTTL")),
        Subsignal("clk",   Pins("A12"), IOStandard("3.3-V LVTTL")),
        Subsignal("blank_n", Pins("F11"), IOStandard("3.3-V LVTTL")),
        Subsignal("sync_n",  Pins("C10"), IOStandard("3.3-V LVTTL")),
    ),
    
    ("ping_hsync", 0, Pins("G13"), IOStandard("3.3-V LVTTL")), # Bank 8
    ("ping_vsync", 0, Pins("C13"), IOStandard("3.3-V LVTTL")), # Bank 8

    ("enet_clk", 0, Pins("A14"), IOStandard("3.3-V LVTTL")),

    # Switches - Bank 3, 4 (3.3V)
    ("switches", 0, Pins(
        "AB28 AC28 AD27 AD28 AB27 AC26 AD26 AB26 AC25",
        "AB25 AC24 AB24 AB23 AA24 AA23 AA22 Y24 Y23"),
        IOStandard("3.3-V LVTTL")
    ),

    # Buttons - Bank 7 (2.5V)
    ("buttons", 0, Pins("M23"), IOStandard("2.5 V")), # KEY0
    ("buttons", 1, Pins("M21"), IOStandard("2.5 V")), # KEY1
    ("buttons", 2, Pins("N21"), IOStandard("2.5 V")), # KEY2
    ("buttons", 3, Pins("R24"), IOStandard("2.5 V")), # KEY3

    # Green LEDs - Bank 7 (2.5V)
    ("leds_g", 0, Pins("E21 E22 E25 E24 H21 G20 G22 G21 F17"), IOStandard("2.5 V")),

    # 7-Segment Displays
    ("seven_seg", 0,
        Subsignal("a", Pins("G18"), IOStandard("2.5 V")),
        Subsignal("b", Pins("F22"), IOStandard("2.5 V")),
        Subsignal("c", Pins("E17"), IOStandard("2.5 V")),
        Subsignal("d", Pins("L26"), IOStandard("2.5 V")),
        Subsignal("e", Pins("L25"), IOStandard("2.5 V")),
        Subsignal("f", Pins("J22"), IOStandard("2.5 V")),
        Subsignal("g", Pins("H22"), IOStandard("2.5 V")),
    ),
    ("seven_seg", 1,
        Subsignal("a", Pins("M24"), IOStandard("2.5 V")),
        Subsignal("b", Pins("Y22"), IOStandard("2.5 V")),
        Subsignal("c", Pins("W21"), IOStandard("2.5 V")),
        Subsignal("d", Pins("W22"), IOStandard("2.5 V")),
        Subsignal("e", Pins("W25"), IOStandard("2.5 V")),
        Subsignal("f", Pins("U23"), IOStandard("2.5 V")),
        Subsignal("g", Pins("U24"), IOStandard("2.5 V")),
    ),
    ("seven_seg", 2,
        Subsignal("a", Pins("AA25"), IOStandard("2.5 V")),
        Subsignal("b", Pins("AA26"), IOStandard("2.5 V")),
        Subsignal("c", Pins("Y25"), IOStandard("2.5 V")),
        Subsignal("d", Pins("W26"), IOStandard("2.5 V")),
        Subsignal("e", Pins("Y26"), IOStandard("2.5 V")),
        Subsignal("f", Pins("W27"), IOStandard("2.5 V")),
        Subsignal("g", Pins("W28"), IOStandard("2.5 V")),
    ),
    ("seven_seg", 3,
        Subsignal("a", Pins("V21"), IOStandard("2.5 V")),
        Subsignal("b", Pins("U21"), IOStandard("2.5 V")),
        Subsignal("c", Pins("AB20"), IOStandard("3.3-V LVTTL")),
        Subsignal("d", Pins("AA21"), IOStandard("3.3-V LVTTL")),
        Subsignal("e", Pins("AD24"), IOStandard("3.3-V LVTTL")),
        Subsignal("f", Pins("AF23"), IOStandard("3.3-V LVTTL")),
        Subsignal("g", Pins("Y19"), IOStandard("3.3-V LVTTL")),
    ),
    ("seven_seg", 4,
        Subsignal("a", Pins("AB19"), IOStandard("3.3-V LVTTL")),
        Subsignal("b", Pins("AA19"), IOStandard("3.3-V LVTTL")),
        Subsignal("c", Pins("AG21"), IOStandard("3.3-V LVTTL")),
        Subsignal("d", Pins("AH21"), IOStandard("3.3-V LVTTL")),
        Subsignal("e", Pins("AE19"), IOStandard("3.3-V LVTTL")),
        Subsignal("f", Pins("AF19"), IOStandard("3.3-V LVTTL")),
        Subsignal("g", Pins("AE18"), IOStandard("3.3-V LVTTL")),
    ),
    ("seven_seg", 5,
        Subsignal("a", Pins("AD18"), IOStandard("3.3-V LVTTL")),
        Subsignal("b", Pins("AC18"), IOStandard("3.3-V LVTTL")),
        Subsignal("c", Pins("AB18"), IOStandard("3.3-V LVTTL")),
        Subsignal("d", Pins("AH19"), IOStandard("3.3-V LVTTL")),
        Subsignal("e", Pins("AG19"), IOStandard("3.3-V LVTTL")),
        Subsignal("f", Pins("AF18"), IOStandard("3.3-V LVTTL")),
        Subsignal("g", Pins("AH18"), IOStandard("3.3-V LVTTL")),
    ),
    ("seven_seg", 6,
        Subsignal("a", Pins("AA17"), IOStandard("3.3-V LVTTL")),
        Subsignal("b", Pins("AB16"), IOStandard("3.3-V LVTTL")),
        Subsignal("c", Pins("AA16"), IOStandard("3.3-V LVTTL")),
        Subsignal("d", Pins("AB17"), IOStandard("3.3-V LVTTL")),
        Subsignal("e", Pins("AB15"), IOStandard("3.3-V LVTTL")),
        Subsignal("f", Pins("AA15"), IOStandard("3.3-V LVTTL")),
        Subsignal("g", Pins("AC17"), IOStandard("3.3-V LVTTL")),
    ),
    ("seven_seg", 7,
        Subsignal("a", Pins("AD17"), IOStandard("3.3-V LVTTL")),
        Subsignal("b", Pins("AE17"), IOStandard("3.3-V LVTTL")),
        Subsignal("c", Pins("AG17"), IOStandard("3.3-V LVTTL")),
        Subsignal("d", Pins("AH17"), IOStandard("3.3-V LVTTL")),
        Subsignal("e", Pins("AF17"), IOStandard("3.3-V LVTTL")),
        Subsignal("f", Pins("AG18"), IOStandard("3.3-V LVTTL")),
        Subsignal("g", Pins("AA14"), IOStandard("3.3-V LVTTL")),
    ),

    # LCD - Bank 1 (3.3V)
    ("lcd", 0,
        Subsignal("data", Pins("L3 L1 L2 K7 K1 K2 M3 M5")),
        Subsignal("en", Pins("L4")),
        Subsignal("rw", Pins("M1")),
        Subsignal("rs", Pins("M2")),
        Subsignal("on", Pins("L5")),
        Subsignal("blon", Pins("L6")),
        IOStandard("3.3-V LVTTL")
    ),

    # USB - Bank 1 & 8 (3.3V)
    ("usb_otg", 0,
        Subsignal("data", Pins(
            "J6 K4 J5 K3 J4 J3 J7 H6",
            "H3 H4 G1 G2 G3 F1 F3 G4")),
        Subsignal("addr", Pins("H7 C3")),
        Subsignal("cs_n", Pins("A3")),
        Subsignal("rd_n", Pins("B3")),
        Subsignal("wr_n", Pins("A4")),
        Subsignal("rst_n", Pins("C5")),
        Subsignal("int0", Pins("D5")),
        Subsignal("int1", Pins("E5")),
        Subsignal("dack_n", Pins("C4 D4")),
        Subsignal("dreq", Pins("B4 J1")),
        IOStandard("3.3-V LVTTL")
    ),
    
    # On-board RGMII Ethernet (Marvell 88E1111)
    ("eth_clocks", 0,
        Subsignal("tx", Pins("B17")),
        Subsignal("rx", Pins("A15")),
        IOStandard("2.5 V")
    ),
    ("rgmii_eth", 0,
        Subsignal("rst_n",   Pins("C19")),
        Subsignal("mdio",    Pins("B21")),
        Subsignal("mdc",     Pins("C20")),
        Subsignal("rx_ctl",  Pins("C17")),
        Subsignal("rx_data", Pins("C16 D16 D17 C15")),
        Subsignal("tx_ctl",  Pins("A18")),
        Subsignal("tx_data", Pins("C18 D19 A19 B19")),
        IOStandard("2.5 V")
    ),
    ("eth_clocks", 1,
        Subsignal("tx", Pins("C23")),
        Subsignal("rx", Pins("L15")),
        IOStandard("2.5 V")
    ),
    ("rgmii_eth", 1,
        Subsignal("rst_n",   Pins("D7")),
        Subsignal("mdio",    Pins("D13")),
        Subsignal("mdc",     Pins("D23")),
        Subsignal("rx_ctl",  Pins("M21")),
        Subsignal("rx_data", Pins("T20 T21 U21 U22")),
        Subsignal("tx_ctl",  Pins("B25")),
        Subsignal("tx_data", Pins("C25 A26 B26 C26")),
        IOStandard("2.5 V")
    ),
]

class Platform(BasePlatform):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_extension(_extra_io)
