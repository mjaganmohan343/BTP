import numpy as np
from gnuradio import gr
import time
import os
import inspect

class blk(gr.sync_block):
    """Robust QPSK BER & Y-Factor SNR Calculator & CSV Logger"""
    def __init__(self):
        gr.sync_block.__init__(
            self,
            name='BER & SNR Calculator',
            in_sig=[np.uint8, np.complex64],  # Port 0: Decoded Bytes, Port 1: Costas Symbols
            out_sig=[]
        )
        self.preamble = np.array([3, 3, 3, 3, 3, 0, 0, 3, 3, 0, 3, 0, 3, 3, 3, 3, 3, 3, 0, 0, 3, 3, 0, 3, 0, 3, 3, 0, 0, 3, 0, 3], dtype=np.uint8)
        np.random.seed(42)
        self.payload_ref = np.random.randint(0, 4, size=968, dtype=np.uint8)
        
        # Precompute 4x4 Hamming distance LUT for QPSK (2 bits)
        self.LUT = np.zeros((4, 4), dtype=np.uint8)
        for i in range(4):
            for j in range(4):
                self.LUT[i, j] = bin(i ^ j).count('1')
                
        self.buffer = np.array([], dtype=np.uint8)
        self.total_bits = 0
        self.total_errors = 0
        self.frame_count = 0
        self.p_off = 0.0
        self.eb_n0_db = 0.0
        self.es_n0_db = 0.0
        
        dir_path = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else '.'
        self.cal_path = os.path.join(dir_path, 'p_off_cal.txt')
        if os.path.exists(self.cal_path):
            try:
                with open(self.cal_path, 'r') as f:
                    self.p_off = float(f.read().strip())
                print(f"[Y-FACTOR] Loaded saved P_off = {self.p_off:.4e}")
            except Exception:
                self.p_off = 0.0
                
        self.csv_path = os.path.join(dir_path, 'ber_log_qpsk.csv')
        self.csv_file = open(self.csv_path, 'w')
        self.csv_file.write("timestamp,frame,total_bits,total_errors,ber,p_raw,p_off,eb_n0_db,es_n0_db\n")
        self.csv_file.flush()

        # GUI Injection
        self.top_block = None
        self.ber_label = None
        self.power_label = None
        self.btn_capture = None
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
                from PyQt5.QtWidgets import QLabel, QPushButton
                from PyQt5.QtCore import QTimer
                
                self.ber_label = QLabel("Total Bits: 0 | Errors: 0 | BER: 0.00e+00")
                self.ber_label.setStyleSheet("font-size: 16px; font-weight: bold; color: blue; padding: 6px;")
                
                self.power_label = QLabel("P_raw: 0.000e+00 | P_off: Not Set | Eb/N0: -- dB | Es/N0: -- dB")
                self.power_label.setStyleSheet("font-size: 15px; font-weight: bold; color: darkgreen; padding: 6px;")
                
                btn_text = f"P_off: {10*np.log10(self.p_off):.1f} dB (Click to re-capture)" if self.p_off > 0 else "Capture P_off (Tx OFF)"
                btn_color = "#ccffcc" if self.p_off > 0 else "#ffcccc"
                self.btn_capture = QPushButton(btn_text)
                self.btn_capture.setStyleSheet(f"font-size: 13px; font-weight: bold; background-color: {btn_color}; padding: 8px; border-radius: 4px;")
                self.btn_capture.clicked.connect(self.capture_poff)
                
                self.top_block.top_grid_layout.addWidget(self.ber_label, 0, 0, 1, 3)
                self.top_block.top_grid_layout.addWidget(self.power_label, 1, 0, 1, 2)
                self.top_block.top_grid_layout.addWidget(self.btn_capture, 1, 2, 1, 1)
                
                self.gui_timer = QTimer()
                self.gui_timer.setInterval(200)
                self.gui_timer.timeout.connect(self.update_gui)
                self.gui_timer.start()
                print(f"[BER/SNR] Successfully initialized. Logging to: {self.csv_path}")
            except Exception as e:
                print(f"[BER/SNR] GUI Init Warning: {e}")

    def capture_poff(self):
        p_raw = getattr(self.top_block, 'p_raw', 0.0) if self.top_block else 0.0
        if p_raw > 0:
            self.p_off = p_raw
            dir_path = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else '.'
            try:
                with open(self.cal_path, 'w') as f:
                    f.write(str(self.p_off))
            except Exception:
                pass
            p_off_db = 10.0 * np.log10(self.p_off)
            print(f"[Y-FACTOR] Successfully set P_off = {self.p_off:.4e} ({p_off_db:.2f} dB)")
            if self.btn_capture:
                self.btn_capture.setText(f"P_off: {p_off_db:.1f} dB (Click to re-capture)")
                self.btn_capture.setStyleSheet("font-size: 13px; font-weight: bold; background-color: #ccffcc; padding: 8px; border-radius: 4px;")

    def update_gui(self):
        if self.top_block:
            bits = self.total_bits
            errs = self.total_errors
            ber = errs / bits if bits > 0 else 0
            if self.ber_label:
                self.ber_label.setText(f"Total Bits: {bits:,} | Errors: {errs:,} | BER: {ber:.2e}")
                
            p_raw = getattr(self.top_block, 'p_raw', 0.0)
            p_raw_db = 10.0 * np.log10(max(p_raw, 1e-15))
            
            if self.p_off > 0 and p_raw > self.p_off:
                # Y-factor SNR: Eb/N0 = 2 * (P_on - P_off) / P_off
                snr_lin = 2.0 * (p_raw - self.p_off) / self.p_off
                self.eb_n0_db = 10.0 * np.log10(snr_lin)
                self.es_n0_db = self.eb_n0_db + 3.01
                if self.power_label:
                    self.power_label.setText(f"P_raw: {p_raw:.2e} ({p_raw_db:.1f} dB) | P_off: {self.p_off:.2e} | Eb/N0: {self.eb_n0_db:.2f} dB | Es/N0: {self.es_n0_db:.2f} dB")
            else:
                p_off_str = f"{self.p_off:.2e}" if self.p_off > 0 else "Not Set"
                if self.power_label:
                    self.power_label.setText(f"P_raw: {p_raw:.2e} ({p_raw_db:.1f} dB) | P_off: {p_off_str} | Eb/N0: -- dB (Tx Off / Standby)")

    def work(self, input_items, output_items):
        in_bytes = input_items[0]
        in_syms = input_items[1]
        
        # Frame Parsing & BER Computation
        data = np.concatenate([self.buffer, in_bytes])
        idx = 0
        while idx + 1000 <= len(data):
            window = data[idx : idx + 32]
            mismatches = int(np.sum(window != self.preamble))
            
            if mismatches <= 2:
                rx_pay = data[idx + 32 : idx + 1000]
                errors = int(np.sum(self.LUT[rx_pay, self.payload_ref]))
                self.total_errors += errors
                self.total_bits += 968 * 2
                self.frame_count += 1
                
                ber = self.total_errors / self.total_bits if self.total_bits > 0 else 0
                p_raw = getattr(self.top_block, 'p_raw', 0.0) if self.top_block else 0.0
                
                if self.frame_count % 50 == 0:
                    print(f"[BER] Frame: {self.frame_count} | Bits: {self.total_bits:,} | Errors: {self.total_errors:,} | BER: {ber:.2e} | Eb/N0: {self.eb_n0_db:.2f} dB | P_raw: {p_raw:.2e}")
                
                self.csv_file.write(f"{time.time()},{self.frame_count},{self.total_bits},{self.total_errors},{ber:.2e},{p_raw:.6e},{self.p_off:.6e},{self.eb_n0_db:.2f},{self.es_n0_db:.2f}\n")
                self.csv_file.flush()
                
                idx += 1000
            else:
                idx += 1
                
        self.buffer = data[idx:]
        return len(in_bytes)

    def stop(self):
        if hasattr(self, 'gui_timer') and self.gui_timer:
            self.gui_timer.stop()
        if hasattr(self, 'csv_file') and self.csv_file:
            self.csv_file.close()
        return True
