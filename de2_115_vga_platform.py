from litex_boards.platforms.terasic_de2_115 import Platform as BasePlatform
from litex.build.generic_platform import *

# Based on Terasic DE2-115 BasePlatform.
_extra_io = [
    # VGA Data (640x480 @ RGB888) - Bank 3 (3.3V)
    ("vga", 0,
        Subsignal("r",     Pins("E12 E11 D10 F12 G10 J12 H10 H8")),
        Subsignal("g",     Pins("G8 G11 F8 H12 C8 B8 F10 C9")),
        Subsignal("b",     Pins("B10 A10 C11 B11 A11 C12 D11 D12")),
        Subsignal("clk",   Pins("A12")),
        Subsignal("de",    Pins("F11")),
        Subsignal("sync_n",  Pins("C10")),
        IOStandard("3.3-V LVTTL")
    ),
    
    # Generic names to avoid all LiteX auto-DDR mapping logic
    ("ping_hsync", 0, Pins("G13"), IOStandard("3.3-V LVTTL")),
    ("ping_vsync", 0, Pins("C13"), IOStandard("3.3-V LVTTL")),

    # Switches (18)
    ("switches", 0, Pins(
        "AB28 AC28 AD27 AD28 AB27 AC26 AD26 AB26 AC25",
        "AB25 AC24 AB24 AB23 AA24 AA23 AA22 Y24 Y23"),
        IOStandard("3.3-V LVTTL")
    ),

    # Buttons (Reset)
    ("buttons", 0, Pins("M23 M21 N21 R24"), IOStandard("3.3-V LVTTL")),

    # Green LEDs (9)
    ("leds_g", 0, Pins("E21 E22 E25 E24 H21 G20 G22 G21 F17"), IOStandard("2.5 V")),

    # 7-Segment Displays (HEX1 to HEX7)
    ("seven_seg", 1, Pins("M24 Y22 W21 W22 W25 U23 U24"), IOStandard("3.3-V LVTTL")),
    ("seven_seg", 2, Pins("AA25 AA26 Y25 W26 Y26 W27 W28"), IOStandard("3.3-V LVTTL")),
    ("seven_seg", 3, Pins("V21 U21 AB20 AA21 AD24 AF23 Y19"), IOStandard("3.3-V LVTTL")),
    ("seven_seg", 4, Pins("AB19 AA19 AG21 AH21 AE19 AF19 AE18"), IOStandard("3.3-V LVTTL")),
    ("seven_seg", 5, Pins("AD18 AC18 AB18 AH19 AG19 AF18 AH18"), IOStandard("3.3-V LVTTL")),
    ("seven_seg", 6, Pins("AA17 AB16 AA16 AB17 AB15 AA15 AC17"), IOStandard("3.3-V LVTTL")),
    ("seven_seg", 7, Pins("AD17 AE17 AG17 AH17 AF17 AG18 AA14"), IOStandard("3.3-V LVTTL")),

    # LCD
    ("lcd", 0,
        Subsignal("data", Pins("L3 L1 L2 K7 K1 K2 M3 M5")),
        Subsignal("en", Pins("L4")),
        Subsignal("rw", Pins("M1")),
        Subsignal("rs", Pins("M2")),
        Subsignal("on", Pins("L5")),
        Subsignal("blon", Pins("L6")),
        IOStandard("3.3-V LVTTL")
    ),

    # USB
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
]

class Platform(BasePlatform):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_extension(_extra_io)
