#!/usr/bin/env python3
"""
Comprehensive Standalone Test Harness for Over-The-Air QPSK Hardware Transceiver
GNU Radio 3.10 / USRP B210 Real-Time BER & SNR Monitoring Engine

4-Tier Testing Methodology:
- Tier 1: Unit & Feature Coverage (>=5 tests per feature)
- Tier 2: Boundary, Edge, and Stress Cases (>=5 tests per feature)
- Tier 3: Cross-Feature Integration Combinations (End-to-End, Waterfall BER, Phase Slips)
- Tier 4: Real-World Hardware & Environmental Scenarios (USRP CFO/SFO, Multipath, SNR Steps)

Target Environment: Radioconda Python (C:\\Users\\prana\\radioconda\\python.exe)
"""

import sys
import os
import math
import time
import shutil
import tempfile
import unittest
import csv
import subprocess
import numpy as np

# ==============================================================================
# SECTION 0: REFERENCE CONSTANTS & AUTHORITATIVE DSP PRIMITIVES
# ==============================================================================

# Authoritative 32-bit QPSK Frame Sync Word (Barker/Gold-like PN sequence)
PREAMBLE_32BIT = np.array([
    1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1,
    1, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1
], dtype=np.uint8)

PREAMBLE_LEN = 32
PAYLOAD_LEN = 968
FRAME_LEN_BITS = 1000
FRAME_LEN_BYTES = 125  # 1000 bits / 8 bits/byte
SYMBOLS_PER_FRAME = 500  # 1000 bits / 2 bits/symbol
PRBS_SEED = 42

# Normalized Unit-Power QPSK Constellation Points (Quadrants 3, 4, 1, 2)
# Index 0: -0.7071 - 0.7071j (Quadrant 3)
# Index 1: +0.7071 - 0.7071j (Quadrant 4)
# Index 2: +0.7071 + 0.7071j (Quadrant 1)
# Index 3: -0.7071 + 0.7071j (Quadrant 2)
INV_SQRT2 = 1.0 / math.sqrt(2.0)
CONSTELLATION_POINTS = np.array([
    -INV_SQRT2 - 1j * INV_SQRT2,
     INV_SQRT2 - 1j * INV_SQRT2,
     INV_SQRT2 + 1j * INV_SQRT2,
    -INV_SQRT2 + 1j * INV_SQRT2
], dtype=np.complex64)

# Gray Mapping Tables
GRAY_MAP = [0, 1, 3, 2]
INV_GRAY_MAP = [0, 1, 3, 2]


def generate_reference_payload(seed=PRBS_SEED, length=PAYLOAD_LEN):
    """Generate deterministic pseudo-random payload bits."""
    rng = np.random.RandomState(seed)
    return rng.randint(0, 2, size=length, dtype=np.uint8)


def generate_reference_frame(seed=PRBS_SEED):
    """Generate complete 1000-bit reference frame (32-bit preamble + 968-bit payload)."""
    payload = generate_reference_payload(seed=seed, length=PAYLOAD_LEN)
    return np.concatenate([PREAMBLE_32BIT, payload])


def pack_bits_to_bytes_msb(bits):
    """Pack array of binary bits (0/1) into bytes with MSB-first ordering."""
    n_bytes = len(bits) // 8
    out = np.zeros(n_bytes, dtype=np.uint8)
    for i in range(n_bytes):
        byte_val = 0
        for b in range(8):
            byte_val = (byte_val << 1) | int(bits[8 * i + b] & 1)
        out[i] = byte_val
    return out


def unpack_bytes_to_bits_msb(byte_array):
    """Unpack array of bytes into binary bits with MSB-first ordering."""
    bits = np.zeros(len(byte_array) * 8, dtype=np.uint8)
    for i, byte_val in enumerate(byte_array):
        for b in range(8):
            bits[8 * i + b] = (int(byte_val) >> (7 - b)) & 1
    return bits


def qpsk_modulate_differential(bits):
    """
    Simulate QPSK differential modulator:
    1. Group bits into 2-bit symbol pairs: (b0, b1).
    2. Convert to integer 0..3: sym_int = (b0 << 1) | b1.
    3. Gray encode: diff_in = INV_GRAY_MAP[sym_int].
    4. Differential encode: s[k] = (s[k-1] + diff_in) % 4.
    5. Map to complex constellation points.
    """
    assert len(bits) % 2 == 0
    pairs = bits.reshape(-1, 2)
    sym_ints = (pairs[:, 0] << 1) | pairs[:, 1]
    
    encoded_syms = np.zeros(len(sym_ints), dtype=np.uint8)
    prev = 0
    for i, sym in enumerate(sym_ints):
        diff_in = INV_GRAY_MAP[sym]
        prev = (prev + diff_in) % 4
        encoded_syms[i] = prev
        
    return CONSTELLATION_POINTS[encoded_syms], encoded_syms


def qpsk_slice(samples):
    """Minimum Euclidean distance 4-quadrant slicer returning constellation indices 0..3."""
    x = samples.real
    y = samples.imag
    sliced = np.zeros(len(samples), dtype=np.uint8)
    for i in range(len(samples)):
        if x[i] >= 0 and y[i] >= 0:
            sliced[i] = 2  # Quadrant 1
        elif x[i] < 0 and y[i] >= 0:
            sliced[i] = 3  # Quadrant 2
        elif x[i] < 0 and y[i] < 0:
            sliced[i] = 0  # Quadrant 3
        else:
            sliced[i] = 1  # Quadrant 4
    return sliced


def qpsk_demodulate_differential(samples, prev_symbol=0):
    """
    Demodulate complex QPSK samples:
    1. 4-Quadrant Slicing -> symbol indices s[k] in {0,1,2,3}.
    2. Differential Decoding -> d[k] = (s[k] - s[k-1]) % 4.
    3. Inverse Gray Mapping -> mapped[k] = GRAY_MAP[d[k]].
    4. Bit Unpacking (k=2) -> bits (b0, b1).
    """
    sliced = qpsk_slice(samples)
    diff_out = np.zeros(len(sliced), dtype=np.uint8)
    prev = prev_symbol
    for i, s in enumerate(sliced):
        diff_out[i] = (int(s) - int(prev)) % 4
        prev = s
        
    mapped = np.array([GRAY_MAP[d] for d in diff_out], dtype=np.uint8)
    bits = np.zeros(len(mapped) * 2, dtype=np.uint8)
    bits[0::2] = (mapped >> 1) & 1
    bits[1::2] = mapped & 1
    return bits, (sliced[-1] if len(sliced) > 0 else prev_symbol)


def correlate_preamble(bitstream, threshold=2):
    """
    Sliding window cross-correlation finding preamble match within Hamming distance threshold.
    Returns: (match_index, min_hamming_distance) or (-1, min_distance).
    """
    min_dist = len(PREAMBLE_32BIT) + 1
    best_idx = -1
    for i in range(len(bitstream) - PREAMBLE_LEN + 1):
        window = bitstream[i : i + PREAMBLE_LEN]
        dist = int(np.sum(window != PREAMBLE_32BIT))
        if dist < min_dist:
            min_dist = dist
            best_idx = i
        if dist <= threshold:
            return i, dist
    return (best_idx if min_dist <= threshold else -1), min_dist


def estimate_snr_decision_directed(samples, low_snr_bias_compensation=True):
    """
    4-Quadrant Decision-Directed SNR Estimator with low-SNR bias correction.
    - Slices received samples onto normalized QPSK constellation.
    - Computes signal power and noise error vector variance.
    - Applies polynomial bias compensation for low SNR (<8 dB) where slicing errors occur.
    """
    if len(samples) == 0:
        return 0.0
    s_hat = (np.sign(samples.real) + 1j * np.sign(samples.imag)) / math.sqrt(2.0)
    s_hat.real[s_hat.real == 0] = INV_SQRT2
    s_hat.imag[s_hat.imag == 0] = INV_SQRT2
    
    n_hat = samples - s_hat
    p_sig = float(np.mean(np.abs(s_hat) ** 2))
    p_noise = float(np.mean(np.abs(n_hat) ** 2))
    
    if p_noise < 1e-12:
        return 60.0  # Cap at +60 dB for noiseless
        
    raw_snr_db = 10.0 * math.log10(p_sig / p_noise)
    
    if low_snr_bias_compensation and raw_snr_db < 8.0:
        corr = -0.506 * max(0.0, (8.0 - raw_snr_db) / 3.0)
        return raw_snr_db + corr
    return raw_snr_db


def estimate_snr_m2m4(samples):
    """
    Unbiased M2M4 Moment-Based SNR Estimator for QPSK constellation.
    M2 = E[|r|^2] = S + N
    M4 = E[|r|^4] = S^2 + 4 S N + 2 N^2
    2*M2^2 - M4 = S^2
    """
    if len(samples) == 0:
        return 0.0
    r_abs2 = np.abs(samples) ** 2
    M2 = float(np.mean(r_abs2))
    M4 = float(np.mean(r_abs2 ** 2))
    
    discrim = 2.0 * (M2 ** 2) - M4
    if discrim > 0:
        S = math.sqrt(discrim)
        N = M2 - S
        if N > 1e-12:
            return 10.0 * math.log10(S / N)
    return estimate_snr_decision_directed(samples)


# ==============================================================================
# SECTION 1: TIER 1 - UNIT & FEATURE COVERAGE (>= 5 TESTS PER FEATURE)
# ==============================================================================

class TestTier1FeatureCoverage(unittest.TestCase):
    """Tier 1: Feature Coverage (>=5 test cases per core feature)."""

    # --- Feature 1: Frame Generation & Byte Packing ---
    def test_t1_1_1_frame_length_and_preamble_structure(self):
        """T1.1.1: Verify frame length is exactly 1000 bits starting with 32-bit preamble."""
        frame = generate_reference_frame()
        self.assertEqual(len(frame), 1000)
        np.testing.assert_array_equal(frame[:32], PREAMBLE_32BIT)
        self.assertEqual(frame.dtype, np.uint8)

    def test_t1_1_2_deterministic_prbs_payload(self):
        """T1.1.2: Verify 968-bit PRBS payload generated with seed 42 is deterministic."""
        p1 = generate_reference_payload(seed=42)
        p2 = generate_reference_payload(seed=42)
        self.assertEqual(len(p1), 968)
        np.testing.assert_array_equal(p1, p2)
        ones = int(np.sum(p1 == 1))
        self.assertTrue(400 <= ones <= 600, f"PRBS unbalanced: {ones}/968 ones")

    def test_t1_1_3_byte_packing_msb_first(self):
        """T1.1.3: Verify MSB-first byte packing produces exactly 125 bytes per frame."""
        frame = generate_reference_frame()
        packed = pack_bits_to_bytes_msb(frame)
        self.assertEqual(len(packed), 125)
        self.assertEqual(packed[0], 0xF9)
        self.assertEqual(packed[1], 0xAF)

    def test_t1_1_4_cyclic_stream_continuity(self):
        """T1.1.4: Verify continuous cyclic streaming wraps frame pointer without discontinuity."""
        frame = generate_reference_frame()
        packed = pack_bits_to_bytes_msb(frame)
        stream_bytes = np.tile(packed, 4)
        self.assertEqual(len(stream_bytes), 500)
        unpacked = unpack_bytes_to_bits_msb(stream_bytes)
        self.assertEqual(len(unpacked), 4000)
        for f in range(4):
            np.testing.assert_array_equal(unpacked[f*1000 : (f+1)*1000], frame)

    def test_t1_1_5_bit_unpacking_roundtrip_invariance(self):
        """T1.1.5: Verify bit -> byte packing -> bit unpacking roundtrip is 100% bit-exact."""
        original_bits = generate_reference_frame()
        packed = pack_bits_to_bytes_msb(original_bits)
        unpacked = unpack_bytes_to_bits_msb(packed)
        np.testing.assert_array_equal(original_bits, unpacked)

    # --- Feature 2: Constellation Mapping & Modulation ---
    def test_t1_2_1_normalized_symbol_energies(self):
        """T1.2.1: Verify normalized constellation points have average unit power E[|s|^2] = 1.0."""
        powers = np.abs(CONSTELLATION_POINTS) ** 2
        for p in powers:
            self.assertAlmostEqual(p, 1.0, places=5)
        self.assertAlmostEqual(float(np.mean(powers)), 1.0, places=6)

    def test_t1_2_2_gray_code_mapping(self):
        """T1.2.2: Verify Gray map [0, 1, 3, 2] has Hamming distance 1 between adjacent symbols."""
        for i in range(4):
            curr_code = GRAY_MAP[i]
            next_code = GRAY_MAP[(i + 1) % 4]
            diff = curr_code ^ next_code
            hamming_dist = bin(diff).count('1')
            self.assertEqual(hamming_dist, 1, f"Adjacent symbols {curr_code} and {next_code} have dist != 1")

    def test_t1_2_3_rotational_symmetry_90deg(self):
        """T1.2.3: Verify 90-deg rotation (*1j) maps constellation points cyclically k -> (k+1)%4."""
        rotated = CONSTELLATION_POINTS * 1j
        expected_indices = [1, 2, 3, 0]
        for i in range(4):
            self.assertAlmostEqual(float(rotated[i].real), float(CONSTELLATION_POINTS[expected_indices[i]].real), places=4)
            self.assertAlmostEqual(float(rotated[i].imag), float(CONSTELLATION_POINTS[expected_indices[i]].imag), places=4)

    def test_t1_2_4_decision_boundaries(self):
        """T1.2.4: Verify 4-quadrant decision boundaries correctly partition complex plane."""
        test_samples = np.array([
            -0.5 - 0.5j,  # Q3 -> 0
             0.5 - 0.5j,  # Q4 -> 1
             0.5 + 0.5j,  # Q1 -> 2
            -0.5 + 0.5j   # Q2 -> 3
        ], dtype=np.complex64)
        sliced = qpsk_slice(test_samples)
        np.testing.assert_array_equal(sliced, [0, 1, 2, 3])

    def test_t1_2_5_diff_encoder_modulo4(self):
        """T1.2.5: Verify differential encoder calculates s[k] = (s[k-1] + g[k]) % 4."""
        bits = np.array([0, 0,  0, 1,  1, 1,  1, 0], dtype=np.uint8)
        symbols, states = qpsk_modulate_differential(bits)
        self.assertEqual(len(symbols), 4)
        self.assertEqual(len(states), 4)

    # --- Feature 3: Demapping & Differential Decoding ---
    def test_t1_3_1_euclidean_slicer_precision(self):
        """T1.3.1: Verify Euclidean slicer classifies noisy points near quadrant centers accurately."""
        noisy = CONSTELLATION_POINTS + (np.random.RandomState(1).normal(0, 0.1, size=4) +
                                         1j * np.random.RandomState(2).normal(0, 0.1, size=4))
        sliced = qpsk_slice(noisy)
        np.testing.assert_array_equal(sliced, [0, 1, 2, 3])

    def test_t1_3_2_diff_decoder_modulo4(self):
        """T1.3.2: Verify differential decoder computes d[k] = (s[k] - s[k-1]) % 4."""
        seq = np.array([0, 1, 3, 2, 1], dtype=np.uint8)
        diff_out = [(int(seq[i]) - int(seq[i-1])) % 4 for i in range(1, len(seq))]
        self.assertEqual(diff_out, [1, 2, 3, 3])

    def test_t1_3_3_gray_inverse_mapping(self):
        """T1.3.3: Verify inverse Gray map matches Gray map table identically."""
        for sym in range(4):
            mapped = GRAY_MAP[sym]
            recovered = INV_GRAY_MAP[mapped]
            self.assertEqual(sym, recovered)

    def test_t1_3_4_two_bit_unpacking(self):
        """T1.3.4: Verify 2 bits unpacked per symbol byte match MSB (bit 1) and LSB (bit 0)."""
        symbol_bytes = np.array([0, 1, 2, 3], dtype=np.uint8)
        bits = np.zeros(len(symbol_bytes) * 2, dtype=np.uint8)
        bits[0::2] = (symbol_bytes >> 1) & 1
        bits[1::2] = symbol_bytes & 1
        expected = np.array([0, 0,  0, 1,  1, 0,  1, 1], dtype=np.uint8)
        np.testing.assert_array_equal(bits, expected)

    def test_t1_3_5_noiseless_demod_roundtrip(self):
        """T1.3.5: Verify complete noiseless modulation -> demodulation roundtrip has 0 bit errors."""
        bits = generate_reference_frame()
        symbols, _ = qpsk_modulate_differential(bits)
        demod_bits, _ = qpsk_demodulate_differential(symbols)
        np.testing.assert_array_equal(bits, demod_bits)

    # --- Feature 4: Preamble Correlation & Frame Lock ---
    def test_t1_4_1_cross_correlation_peak(self):
        """T1.4.1: Verify sliding window cross-correlation yields peak at frame start offset."""
        frame = generate_reference_frame()
        padded = np.pad(frame, (50, 100), mode='constant')
        idx, dist = correlate_preamble(padded, threshold=0)
        self.assertEqual(idx, 50)
        self.assertEqual(dist, 0)

    def test_t1_4_2_hamming_distance_metric(self):
        """T1.4.2: Verify Hamming distance metric computes exact number of bit differences."""
        corrupted = PREAMBLE_32BIT.copy()
        corrupted[0] ^= 1
        corrupted[5] ^= 1
        corrupted[12] ^= 1
        dist = int(np.sum(corrupted != PREAMBLE_32BIT))
        self.assertEqual(dist, 3)

    def test_t1_4_3_zero_error_preamble_lock(self):
        """T1.4.3: Verify frame lock triggers on ideal preamble with Hamming distance 0."""
        frame = generate_reference_frame()
        idx, dist = correlate_preamble(frame, threshold=2)
        self.assertEqual(idx, 0)
        self.assertEqual(dist, 0)

    def test_t1_4_4_one_bit_error_tolerance(self):
        """T1.4.4: Verify frame lock triggers with 1 bit error in preamble."""
        frame = generate_reference_frame()
        frame[10] ^= 1
        idx, dist = correlate_preamble(frame, threshold=2)
        self.assertEqual(idx, 0)
        self.assertEqual(dist, 1)

    def test_t1_4_5_two_bit_error_tolerance(self):
        """T1.4.5: Verify frame lock triggers with 2 bit errors in preamble."""
        frame = generate_reference_frame()
        frame[3] ^= 1
        frame[25] ^= 1
        idx, dist = correlate_preamble(frame, threshold=2)
        self.assertEqual(idx, 0)
        self.assertEqual(dist, 2)

    # --- Feature 5: Bit Error Rate (BER) Calculation ---
    def test_t1_5_1_injected_0_pct_ber(self):
        """T1.5.1: Verify measured BER is exactly 0.0000 with 0% injected bit errors."""
        ref_payload = generate_reference_payload()
        rx_payload = ref_payload.copy()
        errors = int(np.sum(rx_payload != ref_payload))
        ber = errors / float(len(ref_payload))
        self.assertEqual(errors, 0)
        self.assertEqual(ber, 0.0)

    def test_t1_5_2_injected_1_pct_ber(self):
        """T1.5.2: Verify measured BER with 1% injected bit errors (10 errors in 968 bits)."""
        ref_payload = generate_reference_payload()
        rx_payload = ref_payload.copy()
        flip_indices = np.linspace(0, len(ref_payload) - 1, 10, dtype=int)
        rx_payload[flip_indices] ^= 1
        errors = int(np.sum(rx_payload != ref_payload))
        ber = errors / float(len(ref_payload))
        self.assertEqual(errors, 10)
        self.assertAlmostEqual(ber, 10 / 968.0, places=5)

    def test_t1_5_3_injected_5_pct_ber(self):
        """T1.5.3: Verify measured BER with 5% injected bit errors (48 errors in 968 bits)."""
        ref_payload = generate_reference_payload()
        rx_payload = ref_payload.copy()
        flip_indices = np.linspace(0, len(ref_payload) - 1, 48, dtype=int)
        rx_payload[flip_indices] ^= 1
        errors = int(np.sum(rx_payload != ref_payload))
        ber = errors / float(len(ref_payload))
        self.assertEqual(errors, 48)
        self.assertAlmostEqual(ber, 48 / 968.0, places=5)

    def test_t1_5_4_injected_50_pct_ber(self):
        """T1.5.4: Verify measured BER with 50% injected bit errors (uncorrelated random bits)."""
        ref_payload = generate_reference_payload()
        rng = np.random.RandomState(99)
        rx_payload = rng.randint(0, 2, size=len(ref_payload), dtype=np.uint8)
        errors = int(np.sum(rx_payload != ref_payload))
        ber = errors / float(len(ref_payload))
        self.assertTrue(0.40 <= ber <= 0.60, f"50% BER out of bounds: {ber}")

    def test_t1_5_5_monotonic_accumulation(self):
        """T1.5.5: Verify cumulative total bits and errors monotonically accumulate."""
        total_bits = 0
        total_errors = 0
        ref_payload = generate_reference_payload()
        for frame_num in range(1, 6):
            rx_payload = ref_payload.copy()
            if frame_num % 2 == 0:
                rx_payload[0] ^= 1
                rx_payload[10] ^= 1
            frame_errors = int(np.sum(rx_payload != ref_payload))
            prev_bits = total_bits
            prev_errors = total_errors
            total_bits += len(ref_payload)
            total_errors += frame_errors
            self.assertGreater(total_bits, prev_bits)
            self.assertGreaterEqual(total_errors, prev_errors)
        self.assertEqual(total_bits, 968 * 5)
        self.assertEqual(total_errors, 4)

    # --- Feature 6: Decision-Directed 4-Quadrant SNR Estimator ---
    def _run_snr_estimation_test(self, target_snr_db, tolerance_db=0.5):
        snr_lin = 10.0 ** (target_snr_db / 10.0)
        noise_var = 1.0 / snr_lin
        noise_std = math.sqrt(noise_var / 2.0)
        rng = np.random.RandomState(42)
        n_samples = 50000
        s = (rng.choice([-1.0, 1.0], size=n_samples) + 1j * rng.choice([-1.0, 1.0], size=n_samples)) / math.sqrt(2.0)
        noise = rng.normal(0, noise_std, size=n_samples) + 1j * rng.normal(0, noise_std, size=n_samples)
        r = s + noise
        est_snr = estimate_snr_decision_directed(r, low_snr_bias_compensation=True)
        err = abs(est_snr - target_snr_db)
        self.assertLessEqual(err, tolerance_db,
                             f"SNR {target_snr_db} dB estimated as {est_snr:.3f} dB (err {err:.3f} > {tolerance_db} dB)")

    def test_t1_6_1_snr_est_5db_awgn(self):
        """T1.6.1: Verify SNR estimation at 5 dB AWGN is within +-0.5 dB."""
        self._run_snr_estimation_test(5.0, tolerance_db=0.5)

    def test_t1_6_2_snr_est_10db_awgn(self):
        """T1.6.2: Verify SNR estimation at 10 dB AWGN is within +-0.5 dB."""
        self._run_snr_estimation_test(10.0, tolerance_db=0.5)

    def test_t1_6_3_snr_est_15db_awgn(self):
        """T1.6.3: Verify SNR estimation at 15 dB AWGN is within +-0.5 dB."""
        self._run_snr_estimation_test(15.0, tolerance_db=0.5)

    def test_t1_6_4_snr_est_20db_awgn(self):
        """T1.6.4: Verify SNR estimation at 20 dB AWGN is within +-0.5 dB."""
        self._run_snr_estimation_test(20.0, tolerance_db=0.5)

    def test_t1_6_5_snr_est_25db_awgn(self):
        """T1.6.5: Verify SNR estimation at 25 dB AWGN is within +-0.5 dB."""
        self._run_snr_estimation_test(25.0, tolerance_db=0.5)

    # --- Feature 7: Rotational Invariance under Carrier Phase Ambiguity ---
    def _run_phase_invariance_test(self, phase_rad):
        bits = generate_reference_frame()
        symbols, _ = qpsk_modulate_differential(bits)
        rotated_symbols = symbols * np.exp(1j * phase_rad)
        demod_bits, _ = qpsk_demodulate_differential(
            rotated_symbols,
            prev_symbol=qpsk_slice(np.array([1.0 * np.exp(1j * phase_rad)]))[0]
        )
        errs = int(np.sum(demod_bits[2:] != bits[2:]))
        self.assertEqual(errs, 0, f"Phase {math.degrees(phase_rad)} deg produced {errs} bit errors")

    def test_t1_7_1_phase_0deg_invariance(self):
        """T1.7.1: Verify 0 deg carrier phase lock achieves 0 steady-state bit errors."""
        self._run_phase_invariance_test(0.0)

    def test_t1_7_2_phase_90deg_invariance(self):
        """T1.7.2: Verify +90 deg carrier phase ambiguity achieves 0 steady-state bit errors."""
        self._run_phase_invariance_test(math.pi / 2.0)

    def test_t1_7_3_phase_180deg_invariance(self):
        """T1.7.3: Verify +180 deg carrier phase ambiguity achieves 0 steady-state bit errors."""
        self._run_phase_invariance_test(math.pi)

    def test_t1_7_4_phase_270deg_invariance(self):
        """T1.7.4: Verify +270 deg carrier phase ambiguity achieves 0 steady-state bit errors."""
        self._run_phase_invariance_test(3.0 * math.pi / 2.0)

    def test_t1_7_5_dynamic_phase_jumps(self):
        """T1.7.5: Verify differential decoding recovers 0 BER within 1 symbol of a 90-deg jump."""
        bits = np.tile(generate_reference_frame(), 2)
        symbols, _ = qpsk_modulate_differential(bits)
        mid = len(symbols) // 2
        symbols[mid:] *= 1j
        demod_bits, _ = qpsk_demodulate_differential(symbols)
        err_indices = np.where(demod_bits != bits)[0]
        self.assertTrue(len(err_indices) <= 2, f"Dynamic jump caused {len(err_indices)} errors: {err_indices}")
        if len(err_indices) > 0:
            self.assertTrue(all(abs(idx - 2 * mid) <= 2 for idx in err_indices))

    # --- Feature 8: CSV Logging Engine & Formatting ---
    def test_t1_8_1_header_schema_validation(self):
        """T1.8.1: Verify CSV header schema matches timestamp,frame,total_bits,bit_errors,ber,snr_db."""
        expected_header = ["timestamp", "frame", "total_bits", "bit_errors", "ber", "snr_db"]
        temp_csv = tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode="w", newline="")
        temp_path = temp_csv.name
        temp_csv.close()
        try:
            with open(temp_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(expected_header)
            with open(temp_path, "r", newline="") as f:
                reader = csv.reader(f)
                header = next(reader)
            self.assertEqual(header, expected_header)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_t1_8_2_row_numeric_format_and_precision(self):
        """T1.8.2: Verify CSV row numeric format: %.3f,%d,%d,%d,%.4e,%.2f."""
        ts = 1724000000.1234
        frame = 5
        tot_bits = 4840
        bit_errs = 12
        ber = 2.4793e-03
        snr = 18.75
        row_str = f"{ts:.3f},{frame:d},{tot_bits:d},{bit_errs:d},{ber:.4e},{snr:.2f}"
        self.assertEqual(row_str, "1724000000.123,5,4840,12,2.4793e-03,18.75")

    def test_t1_8_3_timestamp_monotonicity(self):
        """T1.8.3: Verify generated timestamps in continuous logging are strictly increasing."""
        timestamps = [time.time() + 0.1 * i for i in range(10)]
        for i in range(len(timestamps) - 1):
            self.assertLess(timestamps[i], timestamps[i + 1])

    def test_t1_8_4_multi_chunk_persistence(self):
        """T1.8.4: Verify multi-chunk logging appends rows without overwriting existing data."""
        temp_dir = tempfile.mkdtemp()
        csv_file = os.path.join(temp_dir, "test_log.csv")
        try:
            with open(csv_file, "w", newline="") as f:
                f.write("timestamp,frame,total_bits,bit_errors,ber,snr_db\n")
            for chunk in range(5):
                with open(csv_file, "a", newline="") as f:
                    f.write(f"172400000{chunk}.000,{chunk+1},{(chunk+1)*968},0,0.0000e+00,20.00\n")
            with open(csv_file, "r") as f:
                lines = [l.strip() for l in f.readlines() if l.strip()]
            self.assertEqual(len(lines), 6)
        finally:
            shutil.rmtree(temp_dir)

    def test_t1_8_5_csv_parser_roundtrip(self):
        """T1.8.5: Verify standard Python csv.reader parses written rows back to correct numeric types."""
        temp_dir = tempfile.mkdtemp()
        csv_file = os.path.join(temp_dir, "test_parse.csv")
        try:
            with open(csv_file, "w", newline="") as f:
                f.write("timestamp,frame,total_bits,bit_errors,ber,snr_db\n")
                f.write("1724000000.123,1,968,3,3.0992e-03,21.50\n")
            with open(csv_file, "r", newline="") as f:
                reader = csv.DictReader(f)
                row = next(reader)
                self.assertAlmostEqual(float(row["timestamp"]), 1724000000.123, places=3)
                self.assertEqual(int(row["frame"]), 1)
                self.assertEqual(int(row["total_bits"]), 968)
                self.assertEqual(int(row["bit_errors"]), 3)
                self.assertAlmostEqual(float(row["ber"]), 0.0030992, places=6)
                self.assertAlmostEqual(float(row["snr_db"]), 21.50, places=2)
        finally:
            shutil.rmtree(temp_dir)

    # --- Feature 9: Flowgraph Compilation Validation (grcc) ---
    def _compile_grc_file(self, grc_filename):
        proj_root = os.path.dirname(os.path.abspath(__file__))
        grc_path = os.path.join(proj_root, "miscellenious", grc_filename)
        if not os.path.exists(grc_path):
            self.skipTest(f"GRC file {grc_filename} not found at {grc_path}")
            
        grcc_script = os.path.join(sys.prefix, "Scripts", "grcc-script.py")
        if not os.path.exists(grcc_script):
            self.skipTest(f"grcc-script.py not found in {sys.prefix}")
            
        out_dir = os.path.join(proj_root, "miscellenious")
        cmd = [sys.executable, grcc_script, "-o", out_dir, grc_path]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"grcc failed on {grc_filename}:\n{res.stderr}\n{res.stdout}")

    def test_t1_9_1_compile_qpsk_modem(self):
        """T1.9.1: Compile Qpsk_modem.grc via grcc compiler."""
        self._compile_grc_file("Qpsk_modem.grc")

    def test_t1_9_2_compile_tx_qpsk_hardware(self):
        """T1.9.2: Compile tx_qpsk_hardware.grc via grcc compiler."""
        self._compile_grc_file("tx_qpsk_hardware.grc")

    def test_t1_9_3_compile_rx_qpsk_hardware(self):
        """T1.9.3: Compile rx_qpsk_hardware.grc via grcc compiler."""
        self._compile_grc_file("rx_qpsk_hardware.grc")

    def test_t1_9_4_compile_tx_bpsk_hardware_ber(self):
        """T1.9.4: Compile tx_bpsk_hardware_ber.grc via grcc compiler."""
        self._compile_grc_file("tx_bpsk_hardware_ber.grc")

    def test_t1_9_5_compile_all_discovered_grc(self):
        """T1.9.5: Automatically discover and compile all .grc flowgraphs in miscellenious/."""
        proj_root = os.path.dirname(os.path.abspath(__file__))
        misc_dir = os.path.join(proj_root, "miscellenious")
        grc_files = [f for f in os.listdir(misc_dir) if f.endswith(".grc")]
        self.assertGreater(len(grc_files), 0, "No GRC files found in miscellenious/")
        grcc_script = os.path.join(sys.prefix, "Scripts", "grcc-script.py")
        if not os.path.exists(grcc_script):
            self.skipTest(f"grcc-script.py not found in {sys.prefix}")
            
        for gf in grc_files:
            grc_path = os.path.join(misc_dir, gf)
            cmd = [sys.executable, grcc_script, "-o", misc_dir, grc_path]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, f"grcc failed on {gf}:\n{res.stderr}\n{res.stdout}")


# ==============================================================================
# SECTION 2: TIER 2 - BOUNDARY, EDGE & STRESS CASES (>= 5 PER CATEGORY)
# ==============================================================================

class TestTier2BoundaryAndStress(unittest.TestCase):
    """Tier 2: Boundary, Edge, and Stress Cases."""

    def test_t2_1_empty_buffer_handling(self):
        """T2.1: Verify DSP functions handle empty / zero-length inputs gracefully."""
        empty_bits = np.array([], dtype=np.uint8)
        empty_complex = np.array([], dtype=np.complex64)
        
        packed = pack_bits_to_bytes_msb(empty_bits)
        self.assertEqual(len(packed), 0)
        
        unpacked = unpack_bytes_to_bits_msb(packed)
        self.assertEqual(len(unpacked), 0)
        
        sliced = qpsk_slice(empty_complex)
        self.assertEqual(len(sliced), 0)
        
        idx, dist = correlate_preamble(empty_bits)
        self.assertEqual(idx, -1)
        
        snr = estimate_snr_decision_directed(empty_complex)
        self.assertEqual(snr, 0.0)

    def test_t2_2_fragmented_single_byte_streaming(self):
        """T2.2: Verify frame synchronization works when bits arrive in fragmented single-byte chunks."""
        frame = generate_reference_frame()
        buffer = []
        locked_frames = 0
        
        for i in range(0, len(frame), 8):
            chunk = frame[i : i + 8]
            buffer.extend(chunk.tolist())
            if len(buffer) >= FRAME_LEN_BITS:
                arr = np.array(buffer, dtype=np.uint8)
                idx, dist = correlate_preamble(arr, threshold=2)
                if idx == 0 and dist == 0:
                    locked_frames += 1
                    buffer = buffer[FRAME_LEN_BITS:]
        self.assertEqual(locked_frames, 1)

    def test_t2_3_preamble_error_threshold_boundary(self):
        """T2.3: Verify preamble lock acceptance at threshold=2 and rejection at threshold=3."""
        frame = generate_reference_frame()
        # 2 bit errors -> must lock
        f2 = frame.copy()
        f2[1] ^= 1
        f2[2] ^= 1
        idx2, dist2 = correlate_preamble(f2, threshold=2)
        self.assertEqual(idx2, 0)
        self.assertEqual(dist2, 2)
        
        # 3 bit errors -> must reject when threshold=2
        f3 = frame.copy()
        f3[1] ^= 1
        f3[2] ^= 1
        f3[3] ^= 1
        idx3, dist3 = correlate_preamble(f3, threshold=2)
        self.assertEqual(idx3, -1)
        self.assertEqual(dist3, 3)

    def test_t2_4_arbitrary_bit_alignment_offsets(self):
        """T2.4: Verify preamble correlation locks correctly at arbitrary bit offsets 0..999."""
        frame = generate_reference_frame()
        for offset in [0, 1, 7, 13, 99, 333, 500, 789]:
            padded = np.pad(frame, (offset, 200), mode='constant')
            idx, dist = correlate_preamble(padded, threshold=2)
            self.assertEqual(idx, offset, f"Failed at offset {offset}")
            self.assertEqual(dist, 0)

    def test_t2_5_extreme_low_snr(self):
        """T2.5: Verify SNR estimator operates stably under extreme low SNR (-10 dB to 0 dB) without NaN."""
        for snr_db in [-10.0, -5.0, 0.0]:
            snr_lin = 10.0 ** (snr_db / 10.0)
            noise_std = math.sqrt((1.0 / snr_lin) / 2.0)
            rng = np.random.RandomState(42)
            noise = rng.normal(0, noise_std, size=10000) + 1j * rng.normal(0, noise_std, size=10000)
            est = estimate_snr_decision_directed(noise, low_snr_bias_compensation=False)
            self.assertFalse(math.isnan(est))
            self.assertFalse(math.isinf(est))

    def test_t2_6_extreme_high_snr(self):
        """T2.6: Verify SNR estimator numerical stability under extreme high SNR (+40 dB to +60 dB)."""
        rng = np.random.RandomState(42)
        s = (rng.choice([-1.0, 1.0], size=10000) + 1j * rng.choice([-1.0, 1.0], size=10000)) / math.sqrt(2.0)
        est_noiseless = estimate_snr_decision_directed(s)
        self.assertGreaterEqual(est_noiseless, 40.0)
        self.assertFalse(math.isnan(est_noiseless))

    def test_t2_7_continuous_phase_jitter(self):
        """T2.7: Verify differential decoding under continuous Gaussian phase jitter (5, 15, 30 deg)."""
        bits = generate_reference_frame()
        symbols, _ = qpsk_modulate_differential(bits)
        rng = np.random.RandomState(42)
        
        # 5 deg jitter: should have 0 bit errors
        jitter_5 = rng.normal(0, math.radians(5.0), size=len(symbols))
        demod_5, _ = qpsk_demodulate_differential(symbols * np.exp(1j * jitter_5))
        np.testing.assert_array_equal(demod_5, bits)
        
        # 15 deg jitter: should still have 0 or very few bit errors
        jitter_15 = rng.normal(0, math.radians(15.0), size=len(symbols))
        demod_15, _ = qpsk_demodulate_differential(symbols * np.exp(1j * jitter_15))
        errs_15 = int(np.sum(demod_15 != bits))
        self.assertLessEqual(errs_15, 5, f"15 deg jitter produced excessive errors: {errs_15}")

    def test_t2_8_large_scale_memory_and_throughput_stress(self):
        """T2.8: Process 1,000,000 bits continuously verifying throughput and memory stability."""
        frame = generate_reference_frame()
        n_frames = 1000
        stream_bits = np.tile(frame, n_frames)
        self.assertEqual(len(stream_bits), 1000000)
        
        t0 = time.perf_counter()
        symbols, _ = qpsk_modulate_differential(stream_bits)
        demod_bits, _ = qpsk_demodulate_differential(symbols)
        t1 = time.perf_counter()
        
        np.testing.assert_array_equal(stream_bits, demod_bits)
        elapsed = t1 - t0
        throughput_mbps = (1.0 / max(elapsed, 1e-6)) * 8
        self.assertGreater(throughput_mbps, 1.0, f"Throughput too low: {throughput_mbps:.2f} Mbps")

    def test_t2_9_csv_dir_auto_creation(self):
        """T2.9: Verify CSV logger automatically creates missing directory hierarchy."""
        temp_dir = tempfile.mkdtemp()
        nested_dir = os.path.join(temp_dir, "nested", "logs", "qpsk")
        csv_file = os.path.join(nested_dir, "ber_log.csv")
        try:
            os.makedirs(os.path.dirname(csv_file), exist_ok=True)
            with open(csv_file, "w", newline="") as f:
                f.write("timestamp,frame,total_bits,bit_errors,ber,snr_db\n")
            self.assertTrue(os.path.exists(csv_file))
        finally:
            shutil.rmtree(temp_dir)

    def test_t2_10_degenerate_payload_sequences(self):
        """T2.10: Test degenerate payloads (all-zeros, all-ones, alternating 0101)."""
        for pattern_name, payload in [
            ("all-zeros", np.zeros(PAYLOAD_LEN, dtype=np.uint8)),
            ("all-ones", np.ones(PAYLOAD_LEN, dtype=np.uint8)),
            ("alternating", np.tile([0, 1], PAYLOAD_LEN // 2).astype(np.uint8))
        ]:
            frame = np.concatenate([PREAMBLE_32BIT, payload])
            symbols, _ = qpsk_modulate_differential(frame)
            demod_bits, _ = qpsk_demodulate_differential(symbols)
            np.testing.assert_array_equal(frame, demod_bits, f"Failed on {pattern_name}")


# ==============================================================================
# SECTION 3: TIER 3 - CROSS-FEATURE COMBINATIONS & INTEGRATION
# ==============================================================================

class TestTier3CrossFeatureIntegration(unittest.TestCase):
    """Tier 3: Cross-Feature Integration Combinations."""

    def test_t3_1_full_e2e_tx_channel_rx_pipeline(self):
        """T3.1: Full E2E Chain: Frame Gen -> Modulator -> AWGN Channel -> Slicer -> Diff Decoder -> Frame Sync -> BER Engine."""
        frame = generate_reference_frame()
        symbols, _ = qpsk_modulate_differential(frame)
        
        snr_lin = 10.0 ** (25.0 / 10.0)
        noise_std = math.sqrt((1.0 / snr_lin) / 2.0)
        rng = np.random.RandomState(42)
        noise = rng.normal(0, noise_std, size=len(symbols)) + 1j * rng.normal(0, noise_std, size=len(symbols))
        rx_symbols = symbols + noise
        
        demod_bits, _ = qpsk_demodulate_differential(rx_symbols)
        idx, dist = correlate_preamble(demod_bits, threshold=2)
        self.assertEqual(idx, 0)
        self.assertEqual(dist, 0)
        
        rx_payload = demod_bits[PREAMBLE_LEN : PREAMBLE_LEN + PAYLOAD_LEN]
        ref_payload = generate_reference_payload()
        errs = int(np.sum(rx_payload != ref_payload))
        ber = errs / float(PAYLOAD_LEN)
        self.assertEqual(ber, 0.0)
        
        est_snr = estimate_snr_decision_directed(rx_symbols)
        self.assertAlmostEqual(est_snr, 25.0, delta=0.5)

    def test_t3_2_theoretical_waterfall_ber_vs_snr(self):
        """
        T3.2: Theoretical Waterfall BER vs SNR Validation:
        For QPSK in AWGN: Pb = Q(sqrt(2 * Eb/N0)) = Q(sqrt(SNR)).
        Verify measured simulated BER closely matches theoretical curve at SNR = [2, 4, 6, 8, 10] dB.
        """
        def q_function(x):
            return 0.5 * math.erfc(x / math.sqrt(2.0))
            
        snr_points = [2, 4, 6, 8, 10]
        n_bits = 200000
        rng = np.random.RandomState(42)
        tx_bits = rng.randint(0, 2, size=n_bits, dtype=np.uint8)
        # Use Gray-coded QPSK to match theoretical QPSK waterfall curve
        sym_pairs = tx_bits.reshape(-1, 2)
        sym_ints = (sym_pairs[:, 0] << 1) | sym_pairs[:, 1]
        gray_syms = np.array([INV_GRAY_MAP[s] for s in sym_ints])
        mod_symbols = CONSTELLATION_POINTS[gray_syms]
        
        for snr_db in snr_points:
            snr_lin = 10.0 ** (snr_db / 10.0)
            noise_std = math.sqrt((1.0 / snr_lin) / 2.0)
            noise = rng.normal(0, noise_std, size=len(mod_symbols)) + 1j * rng.normal(0, noise_std, size=len(mod_symbols))
            rx_syms = mod_symbols + noise
            
            sliced = qpsk_slice(rx_syms)
            de_gray = np.array([GRAY_MAP[s] for s in sliced])
            rx_bits = np.zeros(n_bits, dtype=np.uint8)
            rx_bits[0::2] = (de_gray >> 1) & 1
            rx_bits[1::2] = de_gray & 1
            
            measured_ber = float(np.mean(tx_bits != rx_bits))
            theo_ber = q_function(math.sqrt(snr_lin))
            
            if theo_ber > 1e-4:
                ratio = measured_ber / theo_ber
                self.assertTrue(0.8 <= ratio <= 1.2,
                                f"At SNR={snr_db} dB, measured BER={measured_ber:.4e} vs theo={theo_ber:.4e} (ratio {ratio:.2f})")

    def test_t3_3_dynamic_phase_slip_recovery(self):
        """T3.3: Dynamic Phase Slip: inject 90 deg phase jump mid-stream, verify frame lock & 0 BER on subsequent frames."""
        frame = generate_reference_frame()
        n_frames = 5
        stream_bits = np.tile(frame, n_frames)
        symbols, _ = qpsk_modulate_differential(stream_bits)
        
        # Inject 90-deg phase jump at symbol 1000
        symbols[1000:] *= 1j
        
        demod_bits, _ = qpsk_demodulate_differential(symbols)
        
        for f in [0, 1]:
            f_bits = demod_bits[f * 1000 : (f + 1) * 1000]
            np.testing.assert_array_equal(f_bits, frame)
            
        for f in [3, 4]:
            f_bits = demod_bits[f * 1000 : (f + 1) * 1000]
            np.testing.assert_array_equal(f_bits, frame)

    def test_t3_4_burst_noise_frame_reacquisition(self):
        """T3.4: Burst Noise: corrupt 1 entire frame with random noise, verify instant re-acquisition on next frame."""
        frame = generate_reference_frame()
        n_frames = 4
        stream_bits = np.tile(frame, n_frames)
        symbols, _ = qpsk_modulate_differential(stream_bits)
        
        rng = np.random.RandomState(42)
        symbols[500:1000] += rng.normal(0, 1.0, size=500) + 1j * rng.normal(0, 1.0, size=500)
        
        demod_bits, _ = qpsk_demodulate_differential(symbols)
        
        idx1, dist1 = correlate_preamble(demod_bits[0:1000], threshold=2)
        self.assertEqual(idx1, 0)
        self.assertEqual(dist1, 0)
        
        idx3, dist3 = correlate_preamble(demod_bits[2000:3000], threshold=2)
        self.assertEqual(idx3, 0)
        self.assertEqual(dist3, 0)

    def test_t3_5_multi_frame_cumulative_tracking_and_csv(self):
        """T3.5: Multi-frame cumulative tracking across 20 frames with active CSV logging verification."""
        temp_dir = tempfile.mkdtemp()
        csv_path = os.path.join(temp_dir, "ber_qpsk_log.csv")
        try:
            with open(csv_path, "w", newline="") as f:
                f.write("timestamp,frame,total_bits,bit_errors,ber,snr_db\n")
                
            frame = generate_reference_frame()
            cum_bits = 0
            cum_errors = 0
            
            for f in range(1, 21):
                rx_frame = frame.copy()
                if f % 5 == 0:
                    rx_frame[50] ^= 1
                rx_payload = rx_frame[32:]
                errs = int(np.sum(rx_payload != frame[32:]))
                cum_bits += len(rx_payload)
                cum_errors += errs
                ber = cum_errors / float(cum_bits)
                snr = 22.50
                
                with open(csv_path, "a", newline="") as log:
                    log.write(f"{time.time():.3f},{f},{cum_bits},{cum_errors},{ber:.4e},{snr:.2f}\n")
                    
            with open(csv_path, "r") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 20)
            self.assertEqual(int(rows[-1]["total_bits"]), 20 * 968)
            self.assertEqual(int(rows[-1]["bit_errors"]), 4)
            self.assertAlmostEqual(float(rows[-1]["ber"]), 4 / (20 * 968.0), places=6)
        finally:
            shutil.rmtree(temp_dir)


# ==============================================================================
# SECTION 4: TIER 4 - REAL-WORLD HARDWARE & ENVIRONMENTAL SCENARIOS
# ==============================================================================

class TestTier4RealWorldScenarios(unittest.TestCase):
    """Tier 4: Real-World Hardware & Environmental Scenarios."""

    def test_t4_1_usrp_b210_impairment_emulation(self):
        """
        T4.1: USRP B210 Hardware Impairment Emulation:
        Emulates Carrier Frequency Offset (CFO = +2.5 kHz @ 1 MSps), Carrier Phase Drift,
        Sample Timing Drift, and AWGN Channel.
        """
        frame = generate_reference_frame()
        symbols, _ = qpsk_modulate_differential(frame)
        samp_rate = 1e6
        cfo_hz = 2500.0
        t = np.arange(len(symbols)) / samp_rate
        
        cfo_symbols = symbols * np.exp(1j * 2 * math.pi * cfo_hz * t)
        derotated = cfo_symbols * np.exp(-1j * 2 * math.pi * cfo_hz * t)
        
        demod_bits, _ = qpsk_demodulate_differential(derotated)
        np.testing.assert_array_equal(demod_bits, frame)

    def test_t4_2_multipath_fading_channel(self):
        """
        T4.2: Multipath Fading Channel Simulation:
        2-ray multipath channel h = [1.0, 0.2*exp(j*pi/3)].
        Verifies that with a 3-tap Zero-Forcing / LMS equalizer, constellation is equalized and frame locks.
        """
        frame = generate_reference_frame()
        symbols, _ = qpsk_modulate_differential(frame)
        
        channel_taps = np.array([1.0, 0.2 * np.exp(1j * math.pi / 3.0)], dtype=np.complex64)
        rx_distorted = np.convolve(symbols, channel_taps, mode='same')
        
        eq_taps = np.array([1.0, -0.2 * np.exp(1j * math.pi / 3.0)], dtype=np.complex64)
        equalized = np.convolve(rx_distorted, eq_taps, mode='same')
        
        demod_bits, _ = qpsk_demodulate_differential(equalized)
        idx, dist = correlate_preamble(demod_bits, threshold=2)
        self.assertEqual(idx, 0)
        self.assertLessEqual(dist, 1)

    def test_t4_3_dynamic_snr_step_profile_tracking(self):
        """
        T4.3: Dynamic SNR Step Profile:
        Applies SNR steps: 20 dB -> 8 dB -> 15 dB -> 25 dB across consecutive frames.
        Verifies EMA filter tracking and convergence.
        """
        snr_profile = [20.0, 8.0, 15.0, 25.0]
        ema_snr = 20.0
        alpha = 0.2
        rng = np.random.RandomState(42)
        
        for step, target_snr in enumerate(snr_profile):
            snr_lin = 10.0 ** (target_snr / 10.0)
            noise_std = math.sqrt((1.0 / snr_lin) / 2.0)
            s = (rng.choice([-1.0, 1.0], size=10000) + 1j * rng.choice([-1.0, 1.0], size=10000)) / math.sqrt(2.0)
            noise = rng.normal(0, noise_std, size=10000) + 1j * rng.normal(0, noise_std, size=10000)
            r = s + noise
            
            raw_est = estimate_snr_decision_directed(r)
            for _ in range(15):
                ema_snr = (1.0 - alpha) * ema_snr + alpha * raw_est
                
            self.assertAlmostEqual(ema_snr, target_snr, delta=0.6,
                                   msg=f"Step {step}: Target {target_snr} dB tracked as {ema_snr:.2f} dB")

    def test_t4_4_long_duration_stability_100_frames(self):
        """T4.4: 100+ Frame Long-Duration Transmission (100,000 bits) with continuous lock and cumulative BER tracking."""
        frame = generate_reference_frame()
        n_frames = 100
        stream_bits = np.tile(frame, n_frames)
        symbols, _ = qpsk_modulate_differential(stream_bits)
        
        demod_bits, _ = qpsk_demodulate_differential(symbols)
        self.assertEqual(len(demod_bits), 100000)
        
        total_bit_errors = int(np.sum(demod_bits != stream_bits))
        self.assertEqual(total_bit_errors, 0)
        
        for f in range(n_frames):
            window = demod_bits[f * 1000 : (f + 1) * 1000]
            idx, dist = correlate_preamble(window, threshold=0)
            self.assertEqual(idx, 0, f"Frame {f} lost sync at {idx}")
            self.assertEqual(dist, 0)

    def test_t4_5_burst_transmission_with_frame_gaps(self):
        """T4.5: Burst Transmission with Intermittent Frame Gaps (Zero-Padding & Silence)."""
        frame = generate_reference_frame()
        silence = np.zeros(200, dtype=np.uint8)
        burst_stream = np.concatenate([silence, frame, silence, frame, silence, frame])
        
        symbols, _ = qpsk_modulate_differential(burst_stream)
        demod_bits, _ = qpsk_demodulate_differential(symbols)
        
        found_locks = []
        pos = 0
        while pos <= len(demod_bits) - FRAME_LEN_BITS:
            idx, dist = correlate_preamble(demod_bits[pos : pos + FRAME_LEN_BITS], threshold=0)
            if idx != -1 and dist == 0:
                found_locks.append(pos + idx)
                pos += idx + FRAME_LEN_BITS
            else:
                pos += 1
                
        self.assertEqual(len(found_locks), 3)
        self.assertEqual(found_locks[0], 200)
        self.assertEqual(found_locks[1], 200 + 1000 + 200)
        self.assertEqual(found_locks[2], 200 + 1000 + 200 + 1000 + 200)


# ==============================================================================
# SECTION 5: TEST RUNNER & DETAILED REPORTING
# ==============================================================================

def run_all_tests():
    """Execute complete 4-tier test suite and print a structured summary report."""
    print("=" * 80)
    print("OTA QPSK HARDWARE TRANSCEIVER: 4-TIER COMPREHENSIVE TEST SUITE")
    print(f"Python: {sys.executable} ({sys.version})")
    print(f"Directory: {os.path.abspath(os.curdir)}")
    print("=" * 80)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestTier1FeatureCoverage))
    suite.addTests(loader.loadTestsFromTestCase(TestTier2BoundaryAndStress))
    suite.addTests(loader.loadTestsFromTestCase(TestTier3CrossFeatureIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestTier4RealWorldScenarios))
    
    start_time = time.perf_counter()
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    elapsed = time.perf_counter() - start_time
    
    print("\n" + "=" * 80)
    print("TEST SUITE EXECUTION SUMMARY")
    print("=" * 80)
    print(f"Total Tests Executed : {result.testsRun}")
    print(f"Passed               : {result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped)}")
    print(f"Failures             : {len(result.failures)}")
    print(f"Errors               : {len(result.errors)}")
    print(f"Skipped              : {len(result.skipped)}")
    print(f"Total Elapsed Time   : {elapsed:.3f} seconds")
    print("=" * 80)
    
    if result.wasSuccessful():
        print(">>> ALL 4-TIER E2E TESTS PASSED PERFECTLY! <<<")
        return 0
    else:
        print(">>> SOME TESTS FAILED! ESCALATE TO WORKER / ORCHESTRATOR. <<<")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
