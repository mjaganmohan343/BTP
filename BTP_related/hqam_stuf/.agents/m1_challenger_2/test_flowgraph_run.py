import sys
import numpy as np
from gnuradio import gr, blocks, digital

sys.path.insert(0, r'c:/Users/prana/OneDrive/Desktop/hqam_stuf/miscellenious')
import tx_qpsk_hardware_ber_epy_block_0 as epy_block_0

class TestFlowgraph(gr.top_block):
    def __init__(self):
        gr.top_block.__init__(self, 'Test TX Flowgraph')
        self.src = blocks.vector_source_b(list(range(256)) * 10, False)
        self.frame_gen = epy_block_0.blk(packet_len=1000)
        self.qpsk = digital.constellation_rect(
            [-0.707-0.707j, 0.707-0.707j, +0.707+0.707j, -0.707+0.707j],
            [0, 1, 3, 2], 4, 2, 2, 1, 1
        ).base()
        self.mod = digital.generic_mod(
            constellation=self.qpsk,
            differential=True,
            samples_per_symbol=4,
            pre_diff_code=True,
            excess_bw=0.35,
            verbose=False,
            log=False,
            truncate=False
        )
        self.snk = blocks.vector_sink_c()
        
        self.connect(self.src, self.frame_gen)
        self.connect(self.frame_gen, self.mod)
        self.connect(self.mod, self.snk)

tb = TestFlowgraph()
tb.run()

data = np.array(tb.snk.data())
print(f'Flowgraph executed successfully!')
print(f'Generated {len(data)} complex baseband samples.')
print(f'Sample mean: {np.mean(data):.6f}')
print(f'Sample power: {np.mean(np.abs(data)**2):.6f}')
print(f'Max magnitude: {np.max(np.abs(data)):.6f}')
assert len(data) > 0, 'No samples produced!'
assert np.mean(np.abs(data)**2) > 0.01, 'Output power is zero!'
print('PASS: Top-block flowgraph running end-to-end.')
