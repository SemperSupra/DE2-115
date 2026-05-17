from migen import *

class Test(Module):
    def __init__(self):
        self.a = Signal()
        self.b = Signal()
        self.comb += self.b.eq(~self.a)

def tb(dut):
    yield dut.a.eq(0)
    yield
    assert (yield dut.b) == 1
    yield dut.a.eq(1)
    yield
    assert (yield dut.b) == 0

if __name__ == "__main__":
    dut = Test()
    run_simulation(dut, tb(dut))
    print("Migen sim works")
