import numpy as np
from gnuradio import gr
import struct
import zlib
import time
import os
import inspect
from collections import deque

# Synchronous PRBS whitening keystream matching transmitter
_rng = np.random.RandomState(42)
WHITENING_KEY = _rng.randint(0, 256, size=2048, dtype=np.uint8)

class blk(gr.sync_block):
    """Robust QPSK Text Packet Deframer, Descrambler, CRC32 Verifier & Qt GUI Display"""
    def __init__(self, log_to_file=True):
        gr.sync_block.__init__(
            self,
            name='Text Packet Deframer & GUI',
            in_sig=[np.uint8],
            out_sig=[]
        )
        self.log_to_file = bool(log_to_file)
        
        # 32-symbol preamble matching transmitter
        self.preamble = np.array([3, 3, 3, 3, 3, 0, 0, 3, 3, 0, 3, 0, 3, 3, 3, 3,
                                  3, 3, 0, 0, 3, 3, 0, 3, 0, 3, 3, 0, 0, 3, 0, 3], dtype=np.uint8)
        
        self.buffer = np.array([], dtype=np.uint8)
        
        # Statistics
        self.total_packets = 0
        self.crc_errors = 0
        self.last_seq = -1
        self.last_text = ""
        self.recent_messages = deque(maxlen=50)
        
        # File Logging
        dir_path = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else '.'
        self.log_path = os.path.join(dir_path, 'rx_text_log.txt')
        self.log_file = None
        if self.log_to_file:
            try:
                self.log_file = open(self.log_path, 'a', encoding='utf-8')
                self.log_file.write(f"\n=== QPSK Text Receiver Started: {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
                self.log_file.flush()
            except Exception as e:
                print(f"[RX Deframer] File log init warning: {e}")
                
        # Qt GUI Widget Injection
        self.top_block = None
        self.status_label = None
        self.text_display = None
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
                from PyQt5.QtWidgets import QLabel, QTextEdit, QVBoxLayout, QWidget
                from PyQt5.QtCore import QTimer
                
                self.gui_container = QWidget()
                layout = QVBoxLayout(self.gui_container)
                layout.setContentsMargins(4, 4, 4, 4)
                layout.setSpacing(4)
                
                self.status_label = QLabel("Waiting for QPSK signal... [Packets: 0 | CRC Errors: 0]")
                self.status_label.setStyleSheet(
                    "background-color: #1e1e2e; color: #a6e3a1; font-size: 14px; font-weight: bold; padding: 6px; border-radius: 4px;"
                )
                layout.addWidget(self.status_label)
                
                self.text_display = QTextEdit()
                self.text_display.setReadOnly(True)
                self.text_display.setStyleSheet(
                    "background-color: #181825; color: #cdd6f4; font-family: 'Consolas', monospace; font-size: 12px; border: 1px solid #313244; border-radius: 4px;"
                )
                self.text_display.setMinimumHeight(180)
                layout.addWidget(self.text_display)
                
                # Add to GNU Radio QT GUI layout (top row)
                self.top_block.top_grid_layout.addWidget(self.gui_container, 0, 0, 1, 2)
                
                self.gui_timer = QTimer()
                self.gui_timer.setInterval(150)
                self.gui_timer.timeout.connect(self.update_gui)
                self.gui_timer.start()
                print(f"[RX Deframer] GUI initialized. Log file: {self.log_path}")
            except Exception as e:
                print(f"[RX Deframer] GUI setup warning: {e}")

    def symbols_to_bytes(self, syms):
        """Convert array of 2-bit symbols to bytes (4 symbols per byte)"""
        n_bytes = len(syms) // 4
        byte_arr = bytearray(n_bytes)
        for i in range(n_bytes):
            s0 = int(syms[4*i])
            s1 = int(syms[4*i + 1])
            s2 = int(syms[4*i + 2])
            s3 = int(syms[4*i + 3])
            byte_arr[i] = (s0 << 6) | (s1 << 4) | (s2 << 2) | s3
        return bytes(byte_arr)

    def update_gui(self):
        if not self.status_label or not self.text_display:
            return
            
        total = self.total_packets
        errs = self.crc_errors
        total_attempts = total + errs
        success_pct = (total / total_attempts * 100.0) if total_attempts > 0 else 100.0
        
        status_text = (
            f"Received Packets: {total:,}  |  CRC Errors: {errs:,}  |  "
            f"Pass Rate: {success_pct:.1f}%  |  Last Seq: #{self.last_seq}"
        )
        self.status_label.setText(status_text)
        
        lines = []
        while self.recent_messages:
            lines.append(self.recent_messages.popleft())
            
        if lines:
            self.text_display.append("\n".join(lines))
            sb = self.text_display.verticalScrollBar()
            sb.setValue(sb.maximum())

    def work(self, input_items, output_items):
        in_syms = input_items[0]
        if len(in_syms) == 0:
            return 0
            
        data = np.concatenate([self.buffer, in_syms])
        idx = 0
        n_data = len(data)
        
        # Preamble (32) + Header (28) = 60 symbols minimum
        while idx + 60 <= n_data:
            window = data[idx : idx + 32]
            mismatches = int(np.sum(window != self.preamble))
            
            if mismatches <= 2:
                # Descramble 7 header bytes
                header_raw = bytearray(self.symbols_to_bytes(data[idx + 32 : idx + 60]))
                for i in range(7):
                    header_raw[i] ^= int(WHITENING_KEY[i % len(WHITENING_KEY)])
                
                magic, pkt_type, seq_num, payload_len = struct.unpack('>H B H H', bytes(header_raw))
                
                if magic != 0x5AA5 or payload_len > 512:
                    idx += 1
                    continue
                    
                total_pkt_syms = 32 + 28 + (4 * payload_len) + 16
                if idx + total_pkt_syms > n_data:
                    break
                    
                # Descramble payload bytes
                payload_raw = bytearray(self.symbols_to_bytes(data[idx + 60 : idx + 60 + 4 * payload_len]))
                for j in range(len(payload_raw)):
                    payload_raw[j] ^= int(WHITENING_KEY[(7 + j) % len(WHITENING_KEY)])
                
                # Descramble CRC bytes
                crc_raw = bytearray(self.symbols_to_bytes(data[idx + 60 + 4 * payload_len : idx + total_pkt_syms]))
                for k in range(4):
                    crc_raw[k] ^= int(WHITENING_KEY[(7 + payload_len + k) % len(WHITENING_KEY)])
                
                rx_crc = struct.unpack('>I', bytes(crc_raw))[0]
                calc_crc = zlib.crc32(bytes(header_raw) + bytes(payload_raw)) & 0xFFFFFFFF
                
                if calc_crc == rx_crc:
                    self.total_packets += 1
                    self.last_seq = seq_num
                    msg = bytes(payload_raw).decode('utf-8', errors='replace')
                    self.last_text = msg
                    
                    log_entry = f"[{time.strftime('%H:%M:%S')}] [Pkt #{seq_num:05d}] {msg}"
                    self.recent_messages.append(log_entry)
                    
                    if self.total_packets % 25 == 0 or self.total_packets <= 5:
                        print(f"[RX QPSK] Received Pkt #{seq_num:05d}: {msg} (CRC OK)")
                        
                    if self.log_file:
                        try:
                            self.log_file.write(f"{log_entry}\n")
                            if self.total_packets % 10 == 0:
                                self.log_file.flush()
                        except Exception:
                            pass
                            
                    idx += total_pkt_syms
                else:
                    self.crc_errors += 1
                    if self.crc_errors % 25 == 0 or self.crc_errors <= 5:
                        print(f"[RX QPSK WARNING] CRC Error on Pkt #{seq_num} (calc={hex(calc_crc)}, rx={hex(rx_crc)})")
                    idx += total_pkt_syms
            else:
                idx += 1
                
        if idx < n_data:
            self.buffer = data[idx:]
        else:
            self.buffer = np.array([], dtype=np.uint8)
            
        if len(self.buffer) > 10000:
            self.buffer = self.buffer[-2000:]
            
        return len(in_syms)

    def stop(self):
        if hasattr(self, 'gui_timer') and self.gui_timer:
            self.gui_timer.stop()
        if hasattr(self, 'log_file') and self.log_file:
            try:
                self.log_file.flush()
                self.log_file.close()
            except Exception:
                pass
        return True
