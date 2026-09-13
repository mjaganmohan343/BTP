import numpy as np
from gnuradio import gr

class blk(gr.interp_block):
    """HQAM Gray Modulator"""
    def __init__(self, sps=4):
        gr.interp_block.__init__(
            self,
            name='HQAM Gray Modulator',
            in_sig=[np.uint8],
            out_sig=[np.complex64],
            interp=2*sps
        )
        self.sps = sps
        
        self.constellation = np.array([
            -0.3333+1.1547j,  0.3333+1.1547j, -0.6667+0.5774j,  0.0000+0.5774j,
             0.6667+0.5774j,  1.3333+0.5774j, -0.3333+0j,       0.3333+0j,
             1.0000+0j,      -0.6667-0.5774j,  0.0000-0.5774j,  0.6667-0.5774j,
             1.3333-0.5774j, -0.3333-1.1547j,  0.3333-1.1547j, -1.0000+0j
        ], dtype=np.complex64)
        
        best_perm = [7, 6, 5, 2, 0, 4, 3, 10, 8, 9, 11, 14, 12, 13, 15, 1]
        self.map_table = np.zeros(16, dtype=np.complex64)
        for i, gray_sym in enumerate(best_perm):
            self.map_table[gray_sym] = self.constellation[i]

    def work(self, input_items, output_items):
        in0 = input_items[0]
        out = output_items[0]
        
        syms = np.zeros(2 * len(in0), dtype=np.uint8)
        syms[0::2] = (in0 >> 4) & 0x0F
        syms[1::2] = in0 & 0x0F
        
        complex_syms = self.map_table[syms]
        
        out[:] = 0.0
        out[::self.sps] = complex_syms
        
        return len(out)
