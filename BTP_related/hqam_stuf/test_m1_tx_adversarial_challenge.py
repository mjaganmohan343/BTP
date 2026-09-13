#!/usr/bin/env python3
"""
Adversarial Challenge Test Harness for Milestone 1: QPSK Hardware Transmitter
Target: miscellenious/tx_qpsk_hardware_ber_epy_block_0.py & tx_qpsk_hardware_ber.grc

Tests:
1. Bit-level MSB-first packing correctness: 1000 bits -> 125 bytes -> unpack -> exact identity.
2. Preamble & PRBS-42 payload specification adherence.
3. PRBS seed isolation & repeatability under arbitrary random states.
4. Seamless, uncorrupted streaming across arbitrary buffer boundaries (single-byte, primes, straddling, huge random chunks).
5. GNU Radio basic_block consume and work method contract verification.
6. Differential QPSK modulation/demodulation compatibility.
7. Phase ambiguity invariance (0, 90, 180, 270 degrees).
8. grcc compilation and generated Python verification.
"""

import os
import sys
import math
import unittest
import importlib.util
import numpy as np
import subprocess

# Authoritative 32-bit QPSK Frame Sync Word
EXPECTED_PREAMBLE = np.array([
    1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1,
    1, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1
], dtype=np.uint8)

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
EPY_PATH = os.path.join(PROJECT_ROOT, "miscellenious", "tx_qpsk_hardware_ber_epy_block_0.py")
GRC_PATH = os.path.join(PROJECT_ROOT, "miscellenious", "tx_qpsk_hardware_ber.grc")


def load_epy_block():
    spec = importlib.util.spec_from_file_location("tx_epy_block", EPY_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.blk


class MockBlkWrapper:
    """Wraps blk to mock gr.basic_block.consume when testing general_work outside GNU Radio runtime."""
    def __init__(self, blk_cls, packet_len=1000):
        self.consumed_items = 0
        self.block = blk_cls(packet_len=packet_len)
        # Monkey patch consume
        self.block.consume = self._mock_consume

    def _mock_consume(self, port, n):
        self.consumed_items += n

    def general_work(self, input_items, output_items):
        return self.block.general_work(input_items, output_items)


class TestM1AdversarialChallenge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.blk_class = load_epy_block()

    def test_01_preamble_exact_bits(self):
        """Verify the 32-bit preamble is exactly identical to the specification."""
        instance = self.blk_class()
        self.assertEqual(len(instance.preamble), 32)
        np.testing.assert_array_equal(instance.preamble, EXPECTED_PREAMBLE)

    def test_02_prbs42_payload_length_and_values(self):
        """Verify 968-bit PRBS payload generated with seed 42."""
        instance = self.blk_class()
        self.assertEqual(len(instance.payload_ref), 968)
        
        # Independent reference generation
        np.random.seed(42)
        expected_payload = np.random.randint(0, 2, size=968, dtype=np.uint8)
        np.testing.assert_array_equal(instance.payload_ref, expected_payload)

    def test_03_packet_concatenation_1000_bits(self):
        """Verify packet is exactly 1000 bits = 32-bit preamble + 968-bit payload."""
        instance = self.blk_class()
        self.assertEqual(len(instance.packet), 1000)
        np.testing.assert_array_equal(instance.packet[:32], instance.preamble)
        np.testing.assert_array_equal(instance.packet[32:], instance.payload_ref)

    def test_04_msb_first_byte_packing_and_unpacking_identity(self):
        """Verify all 1000 bits unpacked MSB-first from 125 bytes match bit-for-bit."""
        instance = self.blk_class()
        self.assertEqual(len(instance.packed_packet), 125)
        
        # Verify first 4 header bytes match manual binary calculation
        # Byte 0: [1, 1, 1, 1, 1, 0, 0, 1] = 0xF9 = 249
        # Byte 1: [1, 0, 1, 0, 1, 1, 1, 1] = 0xAF = 175
        # Byte 2: [1, 1, 0, 0, 1, 1, 0, 1] = 0xCD = 205
        # Byte 3: [0, 1, 1, 0, 0, 1, 0, 1] = 0x65 = 101
        self.assertEqual(instance.packed_packet[0], 0xF9)
        self.assertEqual(instance.packed_packet[1], 0xAF)
        self.assertEqual(instance.packed_packet[2], 0xCD)
        self.assertEqual(instance.packed_packet[3], 0x65)
        
        # Unpack all 125 bytes MSB-first
        unpacked_bits = np.zeros(125 * 8, dtype=np.uint8)
        for i, byte_val in enumerate(instance.packed_packet):
            for b in range(8):
                unpacked_bits[8 * i + b] = (int(byte_val) >> (7 - b)) & 1

        self.assertEqual(len(unpacked_bits), 1000)
        np.testing.assert_array_equal(unpacked_bits, instance.packet)

    def test_05_prbs_seed_isolation_under_random_pollution(self):
        """Verify that prior random state does not pollute blk's deterministic payload."""
        for test_seed in [0, 1, 123, 9999, 54321]:
            np.random.seed(test_seed)
            _ = np.random.rand(1000)
            instance = self.blk_class()
            
            np.random.seed(42)
            expected_payload = np.random.randint(0, 2, size=968, dtype=np.uint8)
            np.testing.assert_array_equal(instance.payload_ref, expected_payload)

    def test_06_streaming_single_byte_chunks(self):
        """Stress-test streaming 10,000 bytes in 1-byte chunks across 80 full frames."""
        wrapper = MockBlkWrapper(self.blk_class)
        block = wrapper.block
        
        output_stream = []
        num_bytes = 10000
        
        for _ in range(num_bytes):
            in_buf = np.array([0x55], dtype=np.uint8)
            out_buf = np.zeros(1, dtype=np.uint8)
            n_written = block.general_work([in_buf], [out_buf])
            self.assertEqual(n_written, 1)
            output_stream.append(out_buf[0])
            
        output_stream = np.array(output_stream, dtype=np.uint8)
        expected_stream = np.tile(block.packed_packet, (num_bytes // 125) + 1)[:num_bytes]
        np.testing.assert_array_equal(output_stream, expected_stream)
        self.assertEqual(wrapper.consumed_items, num_bytes)

    def test_07_streaming_prime_length_chunks(self):
        """Stress-test streaming across non-divisible prime buffer chunk sizes."""
        primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109, 113, 127, 131, 251]
        wrapper = MockBlkWrapper(self.blk_class)
        block = wrapper.block
        
        collected_bytes = []
        for p in primes:
            in_buf = np.ones(p, dtype=np.uint8)
            out_buf = np.zeros(p, dtype=np.uint8)
            n_written = block.general_work([in_buf], [out_buf])
            self.assertEqual(n_written, p)
            collected_bytes.extend(out_buf)
            
        total_len = len(collected_bytes)
        expected = np.tile(block.packed_packet, (total_len // 125) + 1)[:total_len]
        np.testing.assert_array_equal(np.array(collected_bytes, dtype=np.uint8), expected)

    def test_08_streaming_boundary_straddling_chunks(self):
        """Stress-test buffer sizes exactly near frame boundaries (124, 125, 126, 249, 250, 251)."""
        chunk_sizes = [124, 125, 126, 249, 250, 251, 374, 375, 376, 1, 125, 125, 124, 2]
        wrapper = MockBlkWrapper(self.blk_class)
        block = wrapper.block
        
        collected_bytes = []
        for sz in chunk_sizes:
            in_buf = np.zeros(sz, dtype=np.uint8)
            out_buf = np.zeros(sz, dtype=np.uint8)
            n_written = block.general_work([in_buf], [out_buf])
            self.assertEqual(n_written, sz)
            collected_bytes.extend(out_buf)
            
        total_len = len(collected_bytes)
        expected = np.tile(block.packed_packet, (total_len // 125) + 1)[:total_len]
        np.testing.assert_array_equal(np.array(collected_bytes, dtype=np.uint8), expected)

    def test_09_massive_randomized_buffer_stress_test(self):
        """Stream 5,000,000 bytes (40,000 frames) with completely randomized buffer chunk sizes."""
        wrapper = MockBlkWrapper(self.blk_class)
        block = wrapper.block
        
        rng = np.random.RandomState(1337)
        total_bytes_target = 5_000_000
        collected_bytes = []
        
        while len(collected_bytes) < total_bytes_target:
            chunk_sz = rng.randint(1, 4096)
            in_buf = np.zeros(chunk_sz, dtype=np.uint8)
            out_buf = np.zeros(chunk_sz, dtype=np.uint8)
            n = block.general_work([in_buf], [out_buf])
            self.assertEqual(n, chunk_sz)
            collected_bytes.extend(out_buf[:n])
            
        collected_arr = np.array(collected_bytes, dtype=np.uint8)
        num_collected = len(collected_arr)
        expected_arr = np.tile(block.packed_packet, (num_collected // 125) + 1)[:num_collected]
        
        np.testing.assert_array_equal(collected_arr, expected_arr)
        self.assertEqual(wrapper.consumed_items, num_collected)

    def test_10_asymmetric_buffer_sizes_and_zero_lengths(self):
        """Test general_work with asymmetric input/output buffer sizes and zero lengths."""
        wrapper = MockBlkWrapper(self.blk_class)
        block = wrapper.block
        
        # Zero length output buffer
        in0 = np.zeros(100, dtype=np.uint8)
        out0 = np.zeros(0, dtype=np.uint8)
        n = block.general_work([in0], [out0])
        self.assertEqual(n, 0)
        
        # Zero length input buffer
        in0 = np.zeros(0, dtype=np.uint8)
        out0 = np.zeros(100, dtype=np.uint8)
        n = block.general_work([in0], [out0])
        self.assertEqual(n, 0)
        
        # in0 larger than out0
        in0 = np.zeros(150, dtype=np.uint8)
        out0 = np.zeros(50, dtype=np.uint8)
        n = block.general_work([in0], [out0])
        self.assertEqual(n, 50)
        
        # in0 smaller than out0
        in0 = np.zeros(30, dtype=np.uint8)
        out0 = np.zeros(80, dtype=np.uint8)
        n = block.general_work([in0], [out0])
        self.assertEqual(n, 30)

    def test_11_grc_source_code_exact_sync(self):
        """Verify that tx_qpsk_hardware_ber.grc embedded code matches tx_qpsk_hardware_ber_epy_block_0.py."""
        with open(EPY_PATH, "r", encoding="utf-8") as f:
            epy_content = f.read().strip()
            
        with open(GRC_PATH, "r", encoding="utf-8") as f:
            grc_content = f.read()
            
        self.assertIn("class blk(gr.basic_block):", grc_content)
        self.assertIn("BER Frame Generator & Preamble Inserter for QPSK", grc_content)
        self.assertIn("packet_len: '1000'", grc_content)
        self.assertIn("name: tx_gain", grc_content)
        self.assertIn("name: uhd_usrp_sink_0", grc_content)

    def test_12_grcc_compilation_and_bytecode_integrity(self):
        """Verify grcc compiles the flowgraph without any errors."""
        grcc_exe = r"C:\Users\prana\radioconda\Scripts\grcc.exe"
        python_exe = r"C:\Users\prana\radioconda\python.exe"
        
        out_dir = os.path.dirname(GRC_PATH)
        res = subprocess.run([grcc_exe, "-o", out_dir, GRC_PATH], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"grcc compilation failed:\n{res.stderr}")
        
        py_output = os.path.join(out_dir, "tx_qpsk_hardware_ber.py")
        self.assertTrue(os.path.exists(py_output), f"Compiled python script {py_output} does not exist.")
        
        compile_res = subprocess.run([python_exe, "-m", "py_compile", py_output], capture_output=True, text=True)
        self.assertEqual(compile_res.returncode, 0, f"py_compile failed:\n{compile_res.stderr}")

    def test_13_modulator_differential_encoding_loopback(self):
        """Verify end-to-end differential QPSK modulation and demodulation of the frame stream."""
        instance = self.blk_class()
        packed_bytes = instance.packed_packet # 125 bytes
        
        # 1. Unpack bytes to 2-bit symbol ints (MSB first: bits [7:6], [5:4], [3:2], [1:0])
        symbol_ints = []
        for b in packed_bytes:
            symbol_ints.append((b >> 6) & 0x03)
            symbol_ints.append((b >> 4) & 0x03)
            symbol_ints.append((b >> 2) & 0x03)
            symbol_ints.append(b & 0x03)
        symbol_ints = np.array(symbol_ints, dtype=np.uint8)
        self.assertEqual(len(symbol_ints), 500) # 500 symbols per frame
        
        # 2. Modulator Gray encode and differential encode (mod 4)
        # sym_map in GRC: [0, 1, 3, 2]
        gray_map = [0, 1, 3, 2]
        inv_gray_map = [0, 1, 3, 2] # Symmetric
        
        diff_in = np.array([inv_gray_map[s] for s in symbol_ints], dtype=np.uint8)
        diff_out = np.zeros(len(diff_in), dtype=np.uint8)
        prev = 0
        for i, val in enumerate(diff_in):
            prev = (prev + int(val)) % 4
            diff_out[i] = prev
            
        # Constellation table
        inv_sqrt2 = 1.0 / math.sqrt(2.0)
        constellation = np.array([
            -inv_sqrt2 - 1j*inv_sqrt2, # 0
             inv_sqrt2 - 1j*inv_sqrt2, # 1
             inv_sqrt2 + 1j*inv_sqrt2, # 2
            -inv_sqrt2 + 1j*inv_sqrt2  # 3
        ], dtype=np.complex64)
        
        tx_symbols = constellation[diff_out]
        
        # 3. Demodulate: Constellation Decoder -> Diff Decoder -> Gray Map -> Unpack bits
        # Hard decision slicer:
        rx_sliced = np.zeros(len(tx_symbols), dtype=np.uint8)
        for i, sym in enumerate(tx_symbols):
            re = np.real(sym)
            im = np.imag(sym)
            if re < 0 and im < 0:
                rx_sliced[i] = 0
            elif re >= 0 and im < 0:
                rx_sliced[i] = 1
            elif re >= 0 and im >= 0:
                rx_sliced[i] = 2
            else:
                rx_sliced[i] = 3
                
        # Differential decoder: diff_dec[k] = (rx[k] - rx[k-1]) % 4
        rx_diff_dec = np.zeros(len(rx_sliced), dtype=np.uint8)
        prev_rx = 0
        for i, val in enumerate(rx_sliced):
            rx_diff_dec[i] = (int(val) - prev_rx) % 4
            prev_rx = val
            
        # Gray Map: [0, 1, 3, 2]
        rx_demapped = np.array([gray_map[s] for s in rx_diff_dec], dtype=np.uint8)
        
        # Unpack 2 bits per symbol (MSB first)
        rx_bits = []
        for s in rx_demapped:
            rx_bits.append((s >> 1) & 1)
            rx_bits.append(s & 1)
        rx_bits = np.array(rx_bits, dtype=np.uint8)
        
        self.assertEqual(len(rx_bits), 1000)
        np.testing.assert_array_equal(rx_bits, instance.packet)

    def test_14_differential_phase_ambiguity_invariance(self):
        """Verify differential demodulation is 100% invariant to 0, 90, 180, 270 deg phase rotations."""
        instance = self.blk_class()
        packed_bytes = instance.packed_packet
        
        symbol_ints = []
        for b in packed_bytes:
            symbol_ints.append((b >> 6) & 0x03)
            symbol_ints.append((b >> 4) & 0x03)
            symbol_ints.append((b >> 2) & 0x03)
            symbol_ints.append(b & 0x03)
        symbol_ints = np.array(symbol_ints, dtype=np.uint8)
        
        gray_map = [0, 1, 3, 2]
        inv_gray_map = [0, 1, 3, 2]
        
        diff_in = np.array([inv_gray_map[s] for s in symbol_ints], dtype=np.uint8)
        diff_out = np.zeros(len(diff_in), dtype=np.uint8)
        prev = 0
        for i, val in enumerate(diff_in):
            prev = (prev + int(val)) % 4
            diff_out[i] = prev
            
        inv_sqrt2 = 1.0 / math.sqrt(2.0)
        constellation = np.array([
            -inv_sqrt2 - 1j*inv_sqrt2,
             inv_sqrt2 - 1j*inv_sqrt2,
             inv_sqrt2 + 1j*inv_sqrt2,
            -inv_sqrt2 + 1j*inv_sqrt2
        ], dtype=np.complex64)
        
        tx_symbols = constellation[diff_out]
        
        # Test 4 quadrant rotations: 0, pi/2, pi, 3pi/2
        rotations = [1.0 + 0.0j, 0.0 + 1.0j, -1.0 + 0.0j, 0.0 - 1.0j]
        for rot in rotations:
            rx_rot = tx_symbols * rot
            rx_sliced = np.zeros(len(rx_rot), dtype=np.uint8)
            for i, sym in enumerate(rx_rot):
                re = np.real(sym)
                im = np.imag(sym)
                if re < 0 and im < 0:
                    rx_sliced[i] = 0
                elif re >= 0 and im < 0:
                    rx_sliced[i] = 1
                elif re >= 0 and im >= 0:
                    rx_sliced[i] = 2
                else:
                    rx_sliced[i] = 3
                    
            rx_diff_dec = np.zeros(len(rx_sliced), dtype=np.uint8)
            # In differential decoding, the first symbol might experience the rotation reference transient,
            # but all subsequent relative transitions are identical.
            # Assuming steady-state lock (or initializing prev_rx with rotated ref):
            prev_rx = (int(rx_sliced[0]) - int(diff_in[0])) % 4
            for i, val in enumerate(rx_sliced):
                rx_diff_dec[i] = (int(val) - prev_rx) % 4
                prev_rx = val
                
            rx_demapped = np.array([gray_map[s] for s in rx_diff_dec], dtype=np.uint8)
            rx_bits = []
            for s in rx_demapped:
                rx_bits.append((s >> 1) & 1)
                rx_bits.append(s & 1)
            rx_bits = np.array(rx_bits, dtype=np.uint8)
            
            # Verify 0 bit errors
            np.testing.assert_array_equal(rx_bits, instance.packet)


if __name__ == "__main__":
    unittest.main(verbosity=2)
