import numpy as np
from gnuradio import gr
import struct
import zlib

# Synchronous PRBS whitening keystream (seed=42 matches BER setup)
_rng = np.random.RandomState(42)
WHITENING_KEY = _rng.randint(0, 256, size=2048, dtype=np.uint8)

class blk(gr.basic_block):
    """QPSK Repeating Text Frame Generator with PRBS Whitening & CRC32"""
    def __init__(self, message="Hello USRP B210 QPSK Link!"):
        gr.basic_block.__init__(
            self,
            name='Text Frame Generator',
            in_sig=[np.uint8],
            out_sig=[np.uint8]
        )
        self.message = str(message)
        self.seq_num = 0
        
        # 32-symbol preamble (same robust sequence as BER setup)
        self.preamble = np.array([3, 3, 3, 3, 3, 0, 0, 3, 3, 0, 3, 0, 3, 3, 3, 3,
                                  3, 3, 0, 0, 3, 3, 0, 3, 0, 3, 3, 0, 0, 3, 0, 3], dtype=np.uint8)
        
        self.current_frame = np.array([], dtype=np.uint8)
        self.ptr = 0

    def set_message(self, message):
        self.message = str(message)

    def bytes_to_symbols(self, data_bytes):
        """Convert bytes into 2-bit QPSK symbols (4 symbols per byte, MSB first)"""
        syms = []
        for b in data_bytes:
            syms.append((b >> 6) & 0x03)
            syms.append((b >> 4) & 0x03)
            syms.append((b >> 2) & 0x03)
            syms.append(b & 0x03)
        return np.array(syms, dtype=np.uint8)

    def pack_symbols_to_bytes(self, symbols):
        """Pack 4 2-bit symbols into one 8-bit byte for Constellation Modulator"""
        rem = len(symbols) % 4
        if rem != 0:
            symbols = np.pad(symbols, (0, 4 - rem), 'constant', constant_values=0)
        
        packed = np.zeros(len(symbols) // 4, dtype=np.uint8)
        for i in range(len(packed)):
            packed[i] = (int(symbols[4*i]) << 6) | (int(symbols[4*i+1]) << 4) | (int(symbols[4*i+2]) << 2) | int(symbols[4*i+3])
        return packed

    def build_packet(self):
        """Builds one framed packet: Preamble + Whitened(Header + Payload + CRC32)"""
        payload_text = f"{self.message} [Pkt #{self.seq_num:05d}]"
        payload_bytes = payload_text.encode('utf-8')
        
        # Header (7 bytes):
        # Magic (2B: 0x5A, 0xA5)
        # Type (1B: 0x01 for repeating text)
        # Seq Num (2B: uint16)
        # Payload Len (2B: uint16)
        magic = 0x5AA5
        pkt_type = 0x01
        header_bytes = struct.pack('>H B H H', magic, pkt_type, self.seq_num, len(payload_bytes))
        
        # CRC32 over unwhitened Header + Payload
        crc = zlib.crc32(header_bytes + payload_bytes) & 0xFFFFFFFF
        crc_bytes = struct.pack('>I', crc)
        
        # Assemble raw data bytes
        raw_data = bytearray(header_bytes + payload_bytes + crc_bytes)
        
        # Whiten data bytes to eliminate repetitive ASCII patterns & discrete CW tones
        for i in range(len(raw_data)):
            raw_data[i] ^= int(WHITENING_KEY[i % len(WHITENING_KEY)])
            
        # Convert whitened data to symbols
        data_syms = self.bytes_to_symbols(raw_data)
        
        # Continuous streaming: Preamble + Whitened Data (no dead unmodulated zeros!)
        full_symbols = np.concatenate([self.preamble, data_syms])
        packed = self.pack_symbols_to_bytes(full_symbols)
        
        self.seq_num = (self.seq_num + 1) & 0xFFFF
        return packed

    def general_work(self, input_items, output_items):
        in0 = input_items[0]
        out = output_items[0]
        n_out = len(out)
        written = 0
        read = min(len(in0), n_out)
        
        while written < read:
            if self.ptr >= len(self.current_frame):
                self.current_frame = self.build_packet()
                self.ptr = 0
                
            rem = len(self.current_frame) - self.ptr
            to_write = min(rem, read - written)
            out[written:written+to_write] = self.current_frame[self.ptr:self.ptr+to_write]
            self.ptr += to_write
            written += to_write
            
        self.consume(0, read)
        return written
