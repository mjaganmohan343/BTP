import numpy as np
from gnuradio import gr
import inspect

class blk(gr.sync_block):
    """Raw ADC Power Meter (Pre-AGC)"""
    def __init__(self, samp_rate=1000000):
        gr.sync_block.__init__(
            self,
            name='Raw Power Meter',
            in_sig=[np.complex64],
            out_sig=[]
        )
        self.samp_rate = samp_rate
        self.p_raw = 0.0
        
        self.top_block = None
        for frame_info in inspect.stack():
            frame = frame_info.frame
            if 'self' in frame.f_locals:
                val = frame.f_locals['self']
                if hasattr(val, 'top_grid_layout'):
                    self.top_block = val
                    break

    def work(self, input_items, output_items):
        in0 = input_items[0]
        n_avail = len(in0)
        if n_avail > 0:
            p_inst = float(np.mean(np.abs(in0)**2))
            if self.p_raw == 0.0:
                self.p_raw = p_inst
            else:
                self.p_raw = 0.92 * self.p_raw + 0.08 * p_inst
                
            if self.top_block:
                self.top_block.p_raw = self.p_raw
                
        return n_avail
