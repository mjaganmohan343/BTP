import sys
import numpy as np
sys.path.insert(0, r'c:\Users\prana\OneDrive\Desktop\hqam_stuf\miscellenious')
import tx_qpsk_hardware_ber_epy_block_0 as tx_epy

def test_frame_generator_stress():
    print('Testing Frame Generator under irregular buffer chunk requests...')
    blk = tx_epy.blk(packet_len=1000)
    
    # Simulate irregular chunk sizes from 1 to 5000 bytes
    chunk_sizes = [1, 2, 7, 13, 125, 250, 333, 1000, 4096, 8192]
    accumulated_bytes = []
    
    for csize in chunk_sizes:
        in_buf = np.zeros(csize, dtype=np.uint8)
        out_buf = np.zeros(csize, dtype=np.uint8)
        n_written = blk.general_work([in_buf], [out_buf])
        assert n_written == csize, f'general_work wrote {n_written} instead of {csize}'
        accumulated_bytes.extend(out_buf.tolist())
        
    total_bytes = len(accumulated_bytes)
    print(f'Total bytes generated across irregular chunks: {total_bytes}')
    
    # Verify cyclic periodicity with period 125 bytes
    ref_packet = blk.packed_packet
    for i in range(total_bytes):
        expected_byte = ref_packet[i % 125]
        actual_byte = accumulated_bytes[i]
        assert actual_byte == expected_byte, f'Byte mismatch at index {i}: expected {expected_byte}, got {actual_byte}'
        
    print('PASS: Frame Generator perfectly maintained 125-byte periodicity across all chunk sizes.\n')

if __name__ == '__main__':
    test_frame_generator_stress()
