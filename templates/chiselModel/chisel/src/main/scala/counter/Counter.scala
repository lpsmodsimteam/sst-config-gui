package counter

import chisel3._

//A n-bit loadable +1 counter
class Counter(val n:Int) extends Module {
	val io = IO(new Bundle {
		val load = Input(Bool())
		val data = Input(UInt(n.W))
		val out  = Output(UInt(n.W))
	})
	
	//wire up the n-bit adder with a mux to load data in
	val adder   = Module(new Adder(n))
	//initialize the register to 0
	val counter = RegInit(0.U(n.W))
	when (io.load) {
		counter := io.data
	}.otherwise {
		counter := adder.io.Sum
	}
	adder.io.A   := counter
	adder.io.B   := 1.U(n.W)
	adder.io.Cin := 0.U(1.W)
	io.out       := counter
}
