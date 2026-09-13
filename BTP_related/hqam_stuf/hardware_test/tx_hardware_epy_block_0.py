import numpy as np
from gnuradio import gr

class blk(gr.basic_block):
    """Preamble Inserter Block"""
    def __init__(self, packet_len=1000):
        gr.basic_block.__init__(
            self,
            name='Preamble Inserter',
            in_sig=[np.uint8],
            out_sig=[np.uint8]
        )
        self.packet_len = packet_len
        self.preamble = np.array([8, 8, 8, 15, 15, 15, 8, 15, 15, 8, 15], dtype=np.uint8)
        self.ptr = 0
        self.state = 0

    def general_work(self, input_items, output_items):
        in0 = input_items[0]
        out = output_items[0]
        n_out = len(out)
        written = 0
        read = 0
        while written < n_out:
            if self.state == 0:
                rem = len(self.preamble) - self.ptr
                to_write = min(rem, n_out - written)
                out[written:written+to_write] = self.preamble[self.ptr:self.ptr+to_write]
                self.ptr += to_write
                written += to_write
                if self.ptr == len(self.preamble):
                    self.state = 1
                    self.ptr = 0
            elif self.state == 1:
                available = len(in0) - read
                if available == 0:
                    break
                rem = self.packet_len - self.ptr
                to_write = min(rem, available, n_out - written)
                out[written:written+to_write] = in0[read:read+to_write]
                self.ptr += to_write
                written += to_write
                read += to_write
                if self.ptr == self.packet_len:
                    self.state = 0
                    self.ptr = 0
        self.consume(0, read)
        return written
