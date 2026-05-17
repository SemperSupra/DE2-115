import time
from litex import RemoteClient
from litescope.software.driver.analyzer import LiteScopeAnalyzerDriver

def capture():
    wb = RemoteClient()
    wb.open()
    
    print("Initializing HPI Analyzer...")
    # hpi_analyzer is at 0xf0001800
    # The driver needs the regs object and the basename
    analyzer = LiteScopeAnalyzerDriver(wb.regs, "hpi_analyzer", config_csv="analyzer.csv")
    
    print("Configuring trigger on usb_otg_cs_n falling edge...")
    # usb_otg_cs_n is a signal name in analyzer.csv
    analyzer.add_falling_edge_trigger("usb_otg_cs_n")
    
    print("Starting capture...")
    analyzer.run(offset=128, length=1024)
    
    print("Triggering HPI cycles...")
    # Run the trigger logic here or externally
    # I'll just wait a bit if I run it externally
    
    print("Waiting for trigger and capture to complete...")
    while not analyzer.done():
        print(f"Progress: {analyzer.get_level()}/{analyzer.length}")
        time.sleep(0.5)
        
    print("Capture complete! Dumping to VCD...")
    analyzer.upload()
    analyzer.save("hpi_capture.vcd")
    
    wb.close()

if __name__ == "__main__":
    capture()
