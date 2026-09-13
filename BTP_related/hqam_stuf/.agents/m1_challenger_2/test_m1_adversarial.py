import sys
import numpy as np

def test_constellation_normalization():
    print('=== TEST 1: Constellation Point Normalization ===')
    points = np.array([-0.707-0.707j, 0.707-0.707j, 0.707+0.707j, -0.707+0.707j], dtype=np.complex64)
    print(f'Constellation points: {points}')
    
    magnitudes = np.abs(points)
    powers = np.abs(points)**2
    avg_power = np.mean(powers)
    
    print(f'Magnitudes: {magnitudes}')
    print(f'Powers: {powers}')
    print(f'Average Power: {avg_power:.6f}')
    
    for i, p in enumerate(points):
        pwr = np.abs(p)**2
        err = abs(pwr - 1.0)
        print(f'Point {i} ({p}): power = {pwr:.6f}, error from 1.0 = {err:.6f} ({err*100:.4f}%)')
        assert err < 0.001, f'Point {i} power deviation {err} is too high!'
    
    print('PASS: All constellation points normalized to unit power within 0.03% precision (0.707 ~= 1/sqrt(2)).\n')

def test_gray_mapping_hamming_distance():
    print('=== TEST 2: Gray Mapping & Quadrant Hamming Distance ===')
    points = np.array([-0.707-0.707j, 0.707-0.707j, 0.707+0.707j, -0.707+0.707j], dtype=np.complex64)
    sym_map = [0, 1, 3, 2]
    
    # Calculate geometric angle for each constellation point
    angles_rad = np.angle(points)
    angles_deg = np.rad2deg(angles_rad) % 360
    
    print('Constellation Points & Assigned Symbols:')
    for i in range(4):
        p = points[i]
        sym = sym_map[i]
        bits = f'{sym:02b}'
        ang = angles_deg[i]
        print(f'  Index {i}: Point = {p:+.3f} | Angle = {ang:5.1f} deg | Symbol = {sym} ({bits}b)')
        
    print('\nTesting Adjacent Quadrant Transitions (pi/2 angular distance):')
    adjacent_pairs = [(0, 1), (1, 2), (2, 3), (3, 0)]
    for idx_a, idx_b in adjacent_pairs:
        sym_a = sym_map[idx_a]
        sym_b = sym_map[idx_b]
        xor_val = sym_a ^ sym_b
        hamming_dist = bin(xor_val).count('1')
        print(f'  Adjacent transition: Point {idx_a} ({sym_a:02b}b, {angles_deg[idx_a]:.0f} deg) <-> Point {idx_b} ({sym_b:02b}b, {angles_deg[idx_b]:.0f} deg) | Hamming dist = {hamming_dist}')
        assert hamming_dist == 1, f'Adjacency violation between {idx_a} and {idx_b}: Hamming dist {hamming_dist} != 1'
        
    print('\nTesting Diagonal (Non-Adjacent) Quadrant Transitions (pi angular distance):')
    diagonal_pairs = [(0, 2), (1, 3)]
    for idx_a, idx_b in diagonal_pairs:
        sym_a = sym_map[idx_a]
        sym_b = sym_map[idx_b]
        xor_val = sym_a ^ sym_b
        hamming_dist = bin(xor_val).count('1')
        print(f'  Diagonal transition: Point {idx_a} ({sym_a:02b}b, {angles_deg[idx_a]:.0f} deg) <-> Point {idx_b} ({sym_b:02b}b, {angles_deg[idx_b]:.0f} deg) | Hamming dist = {hamming_dist}')
        assert hamming_dist == 2, f'Diagonal violation between {idx_a} and {idx_b}: Hamming dist {hamming_dist} != 2'
        
    print('PASS: All adjacent constellation quadrant transitions have Hamming distance EXACTLY 1 (Gray Property).\n')

def test_gnuradio_constellation_rect():
    print('=== TEST 3: GNU Radio digital.constellation_rect Validation ===')
    from gnuradio import digital
    points = [-0.707-0.707j, 0.707-0.707j, 0.707+0.707j, -0.707+0.707j]
    sym_map = [0, 1, 3, 2]
    
    constel = digital.constellation_rect(points, sym_map, 4, 2, 2, 1, 1, 8)
    print(f'Constellation: {constel}')
    print(f'Points: {constel.points()}')
    print(f'Symbol Map: {constel.map()}')
    print(f'Rotational symmetry: {constel.rotational_symmetry()}')
    print(f'Bits per symbol: {constel.bits_per_symbol()}')
    
    # Test decision maker for quadrant points
    for i, pt in enumerate(points):
        dec = constel.decision_maker(pt)
        mapped_pt = constel.map_to_points(dec)
        print(f'Point {i} ({pt}) -> decision: {dec}, map_to_points: {mapped_pt}')
        assert dec == i, f'Decision {dec} did not match expected index {i}'
        
    print('PASS: GNU Radio constellation_rect validated successfully.\n')

if __name__ == '__main__':
    test_constellation_normalization()
    test_gray_mapping_hamming_distance()
    test_gnuradio_constellation_rect()
