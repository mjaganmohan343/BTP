import numpy as np
from gnuradio import gr

class blk(gr.sync_block):
    """Phase Ambiguity Resolver"""
    def __init__(self):
        gr.sync_block.__init__(
            self,
            name='Phase Ambiguity Resolver',
            in_sig=[np.complex64],
            out_sig=[np.complex64]
        )
        self.flip_state = 1.0

    def work(self, input_items, output_items):
        in0 = input_items[0]
        out = output_items[0]
        
        if len(in0) >= 10:
            k = max(2, int(len(in0) * 0.04))
            sorted_real = np.sort(in0.real)
            top_mag = np.mean(sorted_real[-k:])
            bot_mag = np.abs(np.mean(sorted_real[:k]))
            
            if top_mag > bot_mag * 1.06:
                self.flip_state = 1.0
            elif bot_mag > top_mag * 1.06:
                self.flip_state = -1.0
                
        out[:] = in0 * self.flip_state
        return len(out)
