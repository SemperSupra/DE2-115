
import time
from litex import RemoteClient
from litescope import LiteScopeAnalyzerDriver

def main():
    wb = RemoteClient(host="localhost", port=1234, csr_csv="build/terasic_de2_115/csr.csv")
    wb.open()
    
    try:
        # Initialize Analyzer
        analyzer = LiteScopeAnalyzerDriver(wb.regs, "hpi_analyzer", config_csv="hpi_analyzer.csv", debug=True)
        analyzer.configure_group(0)
        analyzer.configure_subsampler(1)
        
        # Add trigger on falling edge of usb_otg_rd_n
        analyzer.add_falling_edge_trigger("usb_otg_rd_n")
        
        print("Starting analyzer...")
        analyzer.run(offset=32)
        
        # Give it a moment to start
        time.sleep(0.5)
        
        # Perform HPI access
        print("Performing HPI access...")
        # These addresses match usb_hpi_host_diag.py logic
        BRIDGE_BASE = 0x82000000
        BRIDGE_CFG0 = BRIDGE_BASE + 0x00
        BRIDGE_CTRL = BRIDGE_BASE + 0x04
        BRIDGE_DATA = BRIDGE_BASE + 0x08
        
        # Write
        addr = 0x1000
        data = 0x1234
        wb.write(BRIDGE_CFG0, addr)
        wb.write(BRIDGE_DATA, data)
        wb.write(BRIDGE_CTRL, (1 << 8) | (1 << 0)) # Write command
        
        # Read
        wb.write(BRIDGE_CFG0, addr)
        wb.write(BRIDGE_CTRL, (1 << 9) | (1 << 0)) # Read command
        
        print("Waiting for analyzer to finish...")
        # Check if done
        for i in range(10):
            if analyzer.done():
                print("Analyzer done!")
                break
            time.sleep(0.5)
        else:
            print("Analyzer timed out (maybe trigger didn't fire?)")
            
        if analyzer.done():
            analyzer.upload()
            analyzer.save("local_artifacts/hpi_combined_capture.vcd")
            print("Capture saved to local_artifacts/hpi_combined_capture.vcd")
            
    finally:
        wb.close()

if __name__ == "__main__":
    main()
