import numpy as np
from gnuradio import gr

class blk(gr.basic_block):
    """BER Frame Generator & Preamble Inserter"""
    def __init__(self, packet_len=1000):
        gr.basic_block.__init__(
            self,
            name='BER Frame Generator',
            in_sig=[np.uint8],
            out_sig=[np.uint8]
        )
        self.packet_len = packet_len
        # QPSK has 4 symbols (2 bits). Let's use a 32-symbol preamble
        self.preamble = np.array([3, 3, 3, 3, 3, 0, 0, 3, 3, 0, 3, 0, 3, 3, 3, 3, 3, 3, 0, 0, 3, 3, 0, 3, 0, 3, 3, 0, 0, 3, 0, 3], dtype=np.uint8)
        np.random.seed(42)
        self.payload_ref = np.random.randint(0, 4, size=968, dtype=np.uint8)
        self.packet = np.concatenate([self.preamble, self.payload_ref])
        
        # Pack 2-bit symbols into 8-bit bytes (4 symbols per byte)
        self.packed_packet = np.zeros(len(self.packet) // 4, dtype=np.uint8)
        for i in range(len(self.packed_packet)):
            self.packed_packet[i] = (self.packet[4*i] << 6) | (self.packet[4*i+1] << 4) | (self.packet[4*i+2] << 2) | self.packet[4*i+3]
            
        self.ptr = 0

    def general_work(self, input_items, output_items):
        in0 = input_items[0]
        out = output_items[0]
        n_out = len(out)
        written = 0
        read = min(len(in0), n_out)
        
        while written < read:
            rem = len(self.packed_packet) - self.ptr
            to_write = min(rem, read - written)
            out[written:written+to_write] = self.packed_packet[self.ptr:self.ptr+to_write]
            self.ptr = (self.ptr + to_write) % len(self.packed_packet)
            written += to_write
            
        self.consume(0, read)
        return written
