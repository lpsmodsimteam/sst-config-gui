package counter

import chisel3.iotesters.{PeekPokeTester, Driver, ChiselFlatSpec}
import java.io.RandomAccessFile
import scala.util.control.Breaks._

class CounterTest(c: Counter) extends PeekPokeTester(c) {
	//Get file pointers to the FIFOs
	val output = new RandomAccessFile("/tmp/output", "rw")
	val input  = new RandomAccessFile("/tmp/input", "r")

	breakable{ while(true){
		//Read a line from the input FIFO
		//!!!!! NEEDS TO SEE A NEWLINE CHARACTER OR IT WILL HANG !!!!!
		val cmd = input.readLine()
		if (cmd.startsWith("q")){
			break
		}
		//First char is load boolean
		val l = Integer.parseInt(cmd(0).toString,2)
		//Last two chars are data in hex
		val d = Integer.parseInt(cmd.substring(1,3),16)
		poke(c.io.load, l)
		poke(c.io.data, d)
		step(1)
		//Read out the counter in hex
		output.writeBytes(peek(c.io.out).toString(16))
	}}
	output.close()
	input.close()
}

class CounterTester extends ChiselFlatSpec {
	behavior of "Counter"
	backends foreach {backend =>
		it should s"increment by 1 counter that is loadable" in {
			Driver(() => new Counter(8))(c => new CounterTest(c))
		}
	}
}
