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
        self.preamble = np.array([8, 8, 8, 15, 15, 15, 8, 15, 15, 8, 15], dtype=np.uint8)
        np.random.seed(42)
        self.payload_ref = np.random.randint(0, 16, size=989, dtype=np.uint8)
        
        # Inverse Gray map to map symbol values to constellation indices
        self.inv_map = np.array([4, 15, 3, 6, 5, 2, 1, 0, 8, 9, 7, 10, 12, 13, 11, 14], dtype=np.uint8)
        
        # Map preamble and payload to the corresponding constellation indices
        self.preamble_tx = self.inv_map[self.preamble]
        self.payload_tx = self.inv_map[self.payload_ref]
        
        self.packet = np.concatenate([self.preamble_tx, self.payload_tx])
        
        # Pack 4-bit symbols into 8-bit bytes
        self.packed_packet = np.zeros(len(self.packet) // 2, dtype=np.uint8)
        for i in range(len(self.packed_packet)):
            self.packed_packet[i] = (self.packet[2*i] << 4) | self.packet[2*i+1]
            
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
