import numpy as np
from gnuradio import gr
import time
import os
import inspect

class blk(gr.sync_block):
    """Robust 16-HQAM BER Calculator & CSV Logger (Frame Jump Parser)"""
    def __init__(self):
        gr.sync_block.__init__(
            self,
            name='BER Calculator & CSV Logger',
            in_sig=[np.uint8],
            out_sig=[np.uint8]
        )
        self.preamble = np.array([8, 8, 8, 15, 15, 15, 8, 15, 15, 8, 15], dtype=np.uint8)
        np.random.seed(42)
        self.payload_ref = np.random.randint(0, 16, size=989, dtype=np.uint8)
        
        # Precompute 16x16 Hamming distance LUT
        self.LUT = np.zeros((16, 16), dtype=np.uint8)
        for i in range(16):
            for j in range(16):
                self.LUT[i, j] = bin(i ^ j).count('1')
                
        self.buffer = np.array([], dtype=np.uint8)
        self.total_bits = 0
        self.total_errors = 0
        self.frame_count = 0
        self.printed_debug = False
        
        # Absolute path for CSV file so it writes next to the script
        dir_path = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else '.'
        self.csv_path = os.path.join(dir_path, 'ber_log.csv')
        self.csv_file = open(self.csv_path, 'w')
        self.csv_file.write("timestamp,frame,total_bits,total_errors,ber,snr_db\n")
        self.csv_file.flush()

        # Self-contained GUI Label Injection via Stack Frames
        self.top_block = None
        self.ber_label = None
        self.gui_timer = None
        
        for frame_info in inspect.stack():
            frame = frame_info.frame
            if 'self' in frame.f_locals:
                val = frame.f_locals['self']
                if hasattr(val, 'top_grid_layout'):
                    self.top_block = val
                    break
                    
        if self.top_block:
            try:
                from PyQt5.QtWidgets import QLabel
                from PyQt5.QtCore import QTimer
                
                self.ber_label = QLabel("Total Bits: 0 | Errors: 0 | BER: 0.00e+00 | SNR: 0.0 dB")
                self.ber_label.setStyleSheet("font-size: 16px; font-weight: bold; color: blue; padding: 10px;")
                self.top_block.top_grid_layout.addWidget(self.ber_label, 0, 0, 1, 2)
                
                self.gui_timer = QTimer()
                self.gui_timer.setInterval(200)
                self.gui_timer.timeout.connect(self.update_gui)
                self.gui_timer.start()
                print(f"[BER] Successfully injected GUI label and timer. CSV logging to: {self.csv_path}")
            except Exception as e:
                print(f"[BER] Failed to initialize GUI components: {e}")

    def update_gui(self):
        if self.ber_label and self.top_block:
            bits = self.total_bits
            errs = self.total_errors
            ber = errs / bits if bits > 0 else 0
            
            # Retrieve SNR from epy_block_0
            snr_db = 0.0
            if hasattr(self.top_block, 'epy_block_0') and hasattr(self.top_block.epy_block_0, 'snr_db'):
                snr_db = self.top_block.epy_block_0.snr_db
                
            self.ber_label.setText(f"Total Bits: {bits:,} | Errors: {errs:,} | BER: {ber:.2e} | SNR: {snr_db:.1f} dB")

    def work(self, input_items, output_items):
        in0 = input_items[0]
        out = output_items[0]
        
        if not self.printed_debug and len(in0) >= 100:
            print("[BER DEBUG] First 100 decoded symbols:", in0[:100].tolist())
            self.printed_debug = True
            
        data = np.concatenate([self.buffer, in0])
        
        idx = 0
        while idx + 1000 <= len(data):
            # Check 11-symbol preamble at current idx
            window = data[idx : idx + 11]
            mismatches = int(np.sum(window != self.preamble))
            
            if mismatches <= 1:
                # Preamble matched! Process entire 1000-symbol frame
                rx_pay = data[idx + 11 : idx + 1000]
                errors = int(np.sum(self.LUT[rx_pay, self.payload_ref]))
                self.total_errors += errors
                self.total_bits += 989 * 4
                self.frame_count += 1
                
                # Retrieve SNR from epy_block_0
                snr_db = 0.0
                if self.top_block and hasattr(self.top_block, 'epy_block_0') and hasattr(self.top_block.epy_block_0, 'snr_db'):
                    snr_db = self.top_block.epy_block_0.snr_db
                    
                if self.frame_count % 50 == 0:
                    ber = self.total_errors / self.total_bits if self.total_bits > 0 else 0
                    print(f"[BER] Frame: {self.frame_count} | Total Bits: {self.total_bits:,} | Errors: {self.total_errors:,} | BER: {ber:.2e} | SNR: {snr_db:.1f} dB")
                
                self.csv_file.write(f"{time.time()},{self.frame_count},{self.total_bits},{self.total_errors},{self.total_errors/self.total_bits:.2e},{snr_db:.2f}\n")
                self.csv_file.flush()
                
                # Jump forward by full packet length (1000 symbols)
                idx += 1000
            else:
                # Slide window by 1 symbol
                idx += 1
                
        self.buffer = data[idx:]
        out[:] = in0
        return len(out)

    def stop(self):
        if hasattr(self, 'gui_timer') and self.gui_timer:
            self.gui_timer.stop()
        if hasattr(self, 'csv_file') and self.csv_file:
            self.csv_file.close()
        return True
