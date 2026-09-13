import numpy as np
from gnuradio import gr

class blk(gr.sync_block):
    """Asymmetry-Based Automatic Blind Phase Resolver & SNR Estimator"""
    def __init__(self):
        gr.sync_block.__init__(
            self,
            name='Phase Ambiguity Resolver',
            in_sig=[np.complex64],
            out_sig=[np.complex64]
        )
        self.flip_state = 1.0
        self.score = 0
        
        # 16-HQAM constellation points for slicing and SNR estimation
        self.constellation = np.array([
            -0.3333+1.1547j,  0.3333+1.1547j, -0.6667+0.5774j,  0.0000+0.5774j,
             0.6667+0.5774j,  1.3333+0.5774j, -0.3333+0j,       0.3333+0j,
             1.0000+0j,      -0.6667-0.5774j,  0.0000-0.5774j,  0.6667-0.5774j,
             1.3333-0.5774j, -0.3333-1.1547j,  0.3333-1.1547j, -1.0000+0j
        ], dtype=np.complex64)
        
        self.avg_signal_power = 1.0
        self.avg_noise_power = 0.05
        self.snr_db = 13.0

    def work(self, input_items, output_items):
        in0 = input_items[0]
        out = output_items[0]
        
        if len(in0) == 0:
            return 0
            
        # Count extreme symbols on real axis (+1.33 vs -1.33)
        k = max(2, int(len(in0) * 0.04))
        sorted_real = np.sort(in0.real)
        top_mag = np.mean(sorted_real[-k:])
        bot_mag = np.abs(np.mean(sorted_real[:k]))
        
        if top_mag > bot_mag * 1.06:
            self.flip_state = 1.0
        elif bot_mag > top_mag * 1.06:
            self.flip_state = -1.0
            
        corrected = in0 * self.flip_state
        out[:] = corrected
        
        # Vectorized constellation slicing for SNR estimation
        dists = np.abs(corrected[:, np.newaxis] - self.constellation[np.newaxis, :])
        closest_idx = np.argmin(dists, axis=1)
        closest_pts = self.constellation[closest_idx]
        
        noise_vect = corrected - closest_pts
        noise_p = np.mean(np.abs(noise_vect)**2)
        signal_p = np.mean(np.abs(closest_pts)**2)
        
        alpha_ema = 0.05
        self.avg_signal_power = (1.0 - alpha_ema) * self.avg_signal_power + alpha_ema * signal_p
        self.avg_noise_power = (1.0 - alpha_ema) * self.avg_noise_power + alpha_ema * noise_p
        
        if self.avg_noise_power > 0:
            self.snr_db = 10 * np.log10(self.avg_signal_power / self.avg_noise_power)
        else:
            self.snr_db = 0.0
            
        return len(out)
