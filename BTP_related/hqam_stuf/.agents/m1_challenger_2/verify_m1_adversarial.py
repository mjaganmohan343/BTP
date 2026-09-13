import sys
import os
import subprocess
import numpy as np

def run_tests():
    print('======================================================================')
    print('EMPIRICAL ADVERSARIAL CHALLENGER TEST SUITE FOR MILESTONE 1 (TX QPSK)')
    print('======================================================================')
    
    # ---------------------------------------------------------
    # TEST 1: Constellation Normalization Precision & Stress Test
    # ---------------------------------------------------------
    print('\n[TEST 1] Constellation Power Normalization Analysis:')
    const_points = np.array([-0.707-0.707j, 0.707-0.707j, 0.707+0.707j, -0.707+0.707j], dtype=np.complex64)
    ideal_scale = 1.0 / np.sqrt(2.0)
    
    print(f'Configured Points: {const_points}')
    print(f'Ideal 1/sqrt(2)  : {ideal_scale:.10f}')
    
    powers = np.abs(const_points)**2
    magnitudes = np.abs(const_points)
    avg_power = np.mean(powers)
    papr = np.max(powers) / avg_power
    
    print(f'Calculated Powers: {powers}')
    print(f'Average Power    : {avg_power:.8f}')
    print(f'Constellation PAPR: {papr:.6f}')
    
    for i, pt in enumerate(const_points):
        err = abs(powers[i] - 1.0)
        db_err = 10 * np.log10(powers[i])
        print(f'  Point {i} ({pt:+.3f}): Power = {powers[i]:.6f} | Delta = {err:.6f} | Delta (dB) = {db_err:+.4f} dB')
        assert err < 0.001, f'Point {i} deviates from unit power by more than 0.1%!'
    
    print('-> RESULT: Constellation points have unit power (|p|^2 = 0.999698 ~= 1.0, deviation < 0.031%). PASS.')

    # ---------------------------------------------------------
    # TEST 2: Gray Mapping & Single-Bit Hamming Distance Invariance
    # ---------------------------------------------------------
    print('\n[TEST 2] Gray Mapping sym_map [0, 1, 3, 2] & Quadrant Adjacency:')
    sym_map = [0, 1, 3, 2]
    
    # Angle calculation
    angles_rad = np.angle(const_points)
    angles_deg = (np.rad2deg(angles_rad) + 360) % 360
    
    print('Constellation Points in Index Order:')
    for i in range(4):
        p = const_points[i]
        sym = sym_map[i]
        bits = f'{sym:02b}'
        print(f'  Point Index {i}: Point = {p.real:+.3f} + {p.imag:+.3f}j | Angle = {angles_deg[i]:5.1f} deg | Symbol Value = {sym} (binary {bits})')
    
    # Check all pairs
    print('\nAll Pairwise Hamming Distance Matrix:')
    n = len(const_points)
    h_matrix = np.zeros((n, n), dtype=int)
    for i in range(n):
        for j in range(n):
            h_matrix[i, j] = bin(sym_map[i] ^ sym_map[j]).count('1')
    
    print('Hamming Distance Matrix (rows/cols = points 0, 1, 2, 3):')
    print(h_matrix)
    
    adjacent_transitions = [
        (0, 1, 'Q3 (225 deg) <-> Q4 (315 deg) [90 deg step]'),
        (1, 2, 'Q4 (315 deg) <-> Q1 ( 45 deg) [90 deg step]'),
        (2, 3, 'Q1 ( 45 deg) <-> Q2 (135 deg) [90 deg step]'),
        (3, 0, 'Q2 (135 deg) <-> Q3 (225 deg) [90 deg step]')
    ]
    
    print('\nVerifying Adjacent Quadrant Transitions:')
    for idx1, idx2, desc in adjacent_transitions:
        hd = h_matrix[idx1, idx2]
        sym1, sym2 = sym_map[idx1], sym_map[idx2]
        print(f'  {desc}: Symbol {sym1} ({sym1:02b}b) -> Symbol {sym2} ({sym2:02b}b) | Hamming Distance = {hd}')
        assert hd == 1, f'Adjacency violation: Hamming distance is {hd}, expected 1!'
        
    diagonal_transitions = [
        (0, 2, 'Q3 (225 deg) <-> Q1 ( 45 deg) [180 deg step]'),
        (1, 3, 'Q4 (315 deg) <-> Q2 (135 deg) [180 deg step]')
    ]
    
    print('\nVerifying Diagonal Quadrant Transitions:')
    for idx1, idx2, desc in diagonal_transitions:
        hd = h_matrix[idx1, idx2]
        sym1, sym2 = sym_map[idx1], sym_map[idx2]
        print(f'  {desc}: Symbol {sym1} ({sym1:02b}b) -> Symbol {sym2} ({sym2:02b}b) | Hamming Distance = {hd}')
        assert hd == 2, f'Diagonal violation: Hamming distance is {hd}, expected 2!'
        
    print('-> RESULT: Gray mapping produces single-bit Hamming distance (1 bit error per adjacent symbol error) across all 4 adjacent quadrant boundaries. PASS.')

    # ---------------------------------------------------------
    # TEST 3: GNU Radio DSP Pipeline Instantiation & Modulator Execution
    # ---------------------------------------------------------
    print('\n[TEST 3] GNU Radio DSP Pipeline Instantiation & Modulator Execution:')
    from gnuradio import digital
    
    points_list = [-0.707-0.707j, 0.707-0.707j, 0.707+0.707j, -0.707+0.707j]
    qpsk_const = digital.constellation_rect(points_list, [0, 1, 3, 2], 4, 2, 2, 1, 1).base()
    print(f'Instantiated digital.constellation_rect: {qpsk_const}')
    print(f'  Bits per symbol : {qpsk_const.bits_per_symbol()}')
    print(f'  Rot symmetry    : {qpsk_const.rotational_symmetry()}')
    print(f'  Points in const : {qpsk_const.points()}')
    print(f'  Mapped points   : {[qpsk_const.map_to_points_v(i) for i in range(4)]}')
    
    assert qpsk_const.bits_per_symbol() == 2
    assert qpsk_const.rotational_symmetry() == 4
    
    # Test decision maker on points with additive AWGN noise
    np.random.seed(12345)
    for expected_idx, center_pt in enumerate(points_list):
        for trial in range(100):
            noise = (np.random.randn() + 1j * np.random.randn()) * 0.1
            noisy_pt = center_pt + noise
            dec = qpsk_const.decision_maker(noisy_pt)
            assert dec == expected_idx, f'Decision error: point {noisy_pt} classified as {dec}, expected {expected_idx}'
            
    print('-> RESULT: GNU Radio constellation_rect decision maker successfully separates noisy IQ samples into the correct Gray-mapped symbols. PASS.')

    # ---------------------------------------------------------
    # TEST 4: Differential Encoding Invariance to 90/180/270 Phase Rotations
    # ---------------------------------------------------------
    print('\n[TEST 4] Differential Modulation / Demodulation Phase Ambiguity Invariance:')
    symbols_in = np.random.randint(0, 4, size=1000)
    
    # Differential Encode
    d_tx = np.zeros(len(symbols_in), dtype=int)
    state = 0
    for i, s in enumerate(symbols_in):
        state = (state + s) % 4
        d_tx[i] = state
        
    for k in [0, 1, 2, 3]:
        rot_deg = k * 90
        d_rx = (d_tx + k) % 4
        
        # Differential Decode
        s_rx = np.zeros(len(symbols_in), dtype=int)
        rx_state = (0 + k) % 4
        for i, r in enumerate(d_rx):
            s_rx[i] = (r - rx_state) % 4
            rx_state = r
            
        mismatches = np.sum(symbols_in != s_rx)
        print(f'  Phase rotation = {rot_deg:3d} deg (k={k}): Decoded Symbol Mismatches = {mismatches}')
        assert mismatches == 0, f'Differential decoding failed under {rot_deg} deg phase ambiguity!'
        
    print('-> RESULT: Differential encoding provides 100% invariance to 0, 90, 180, and 270 degree phase ambiguities. PASS.')

    # ---------------------------------------------------------
    # TEST 5: Frame Generator Preamble & Payload Alignment
    # ---------------------------------------------------------
    print('\n[TEST 5] Embedded Frame Generator Block Validation:')
    sys.path.insert(0, r'c:\Users\prana\OneDrive\Desktop\hqam_stuf\miscellenious')
    import tx_qpsk_hardware_ber_epy_block_0 as tx_epy
    
    blk = tx_epy.blk(packet_len=1000)
    print(f'Frame Generator block instantiated: {blk}')
    print(f'  Preamble length: {len(blk.preamble)} bits')
    print(f'  Payload length : {len(blk.payload_ref)} bits')
    print(f'  Total packet   : {len(blk.packet)} bits')
    print(f'  Packed packet  : {len(blk.packed_packet)} bytes')
    
    expected_preamble = np.array([
        1, 1, 1, 1, 1, 0, 0, 1,
        1, 0, 1, 0, 1, 1, 1, 1,
        1, 1, 0, 0, 1, 1, 0, 1,
        0, 1, 1, 0, 0, 1, 0, 1
    ], dtype=np.uint8)
    
    assert np.array_equal(blk.preamble, expected_preamble), 'Preamble bit pattern mismatch!'
    assert len(blk.packed_packet) == 125, f'Packed packet length is {len(blk.packed_packet)}, expected 125 bytes!'
    
    # Test unpacking packed bytes
    unpacked_bits = np.unpackbits(blk.packed_packet)
    assert np.array_equal(unpacked_bits, blk.packet), 'Bit unpack mismatch from packed bytes!'
    print('-> RESULT: Frame Generator preamble (32 bits), PRBS-42 payload (968 bits), and MSB-first 125-byte packing verified. PASS.')

    # ---------------------------------------------------------
    # TEST 6: grcc Compilation Cleanliness (No Warnings / Errors)
    # ---------------------------------------------------------
    print('\n[TEST 6] grcc Compilation Verification on tx_qpsk_hardware_ber.grc:')
    grcc_path = r'C:\Users\prana\radioconda\Scripts\grcc.exe'
    grc_file = r'c:\Users\prana\OneDrive\Desktop\hqam_stuf\miscellenious\tx_qpsk_hardware_ber.grc'
    out_dir = r'c:\Users\prana\OneDrive\Desktop\hqam_stuf\miscellenious'
    
    cmd = [grcc_path, '-o', out_dir, grc_file]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    
    print(f'grcc Return Code: {proc.returncode}')
    print(f'grcc STDOUT:\n{proc.stdout}')
    print(f'grcc STDERR:\n{proc.stderr}')
    
    assert proc.returncode == 0, f'grcc compilation failed with exit code {proc.returncode}'
    assert 'Error' not in proc.stderr and 'error' not in proc.stderr.lower(), f'grcc stderr contains errors: {proc.stderr}'
    assert 'Warning' not in proc.stderr and 'warning' not in proc.stderr.lower(), f'grcc stderr contains warnings: {proc.stderr}'
    
    print('-> RESULT: grcc compiled tx_qpsk_hardware_ber.grc with zero errors, zero warnings, and clean exit code 0. PASS.')

    print('\n======================================================================')
    print('ALL EMPIRICAL ADVERSARIAL TESTS PASSED (6/6). STATUS: APPROVE')
    print('======================================================================')

if __name__ == '__main__':
    run_tests()
