# Milestone 1: QPSK Hardware Transmitter Adversarial Challenge Report

**Agent**: `m1_challenger_1`  
**Role**: critic, specialist  
**Date**: 2026-08-18  
**Verdict**: `APPROVE`  
**Target Files**:
- `miscellenious/tx_qpsk_hardware_ber_epy_block_0.py`
- `miscellenious/tx_qpsk_hardware_ber.grc`
- `miscellenious/tx_qpsk_hardware_ber.py`

---

## 1. Observation

Direct observations from independent empirical testing, code inspection, and execution logs:

1. **Preamble and Payload Definition**:
   - In `tx_qpsk_hardware_ber_epy_block_0.py` lines 15-20:
     ```python
     self.preamble = np.array([
         1, 1, 1, 1, 1, 0, 0, 1,
         1, 0, 1, 0, 1, 1, 1, 1,
         1, 1, 0, 0, 1, 1, 0, 1,
         0, 1, 1, 0, 0, 1, 0, 1
     ], dtype=np.uint8)
     ```
     This 32-bit sequence exactly matches the specification in `PROJECT.md` line 46.
   - Lines 21-23:
     ```python
     np.random.seed(42)
     self.payload_ref = np.random.randint(0, 2, size=968, dtype=np.uint8)
     ```
     Payload length is exactly 968 bits, bringing total frame length to 1000 bits ($32 + 968 = 1000$).

2. **MSB-First Byte Packing**:
   - Lines 28-35:
     ```python
     n_bytes = len(self.packet) // 8
     self.packed_packet = np.zeros(n_bytes, dtype=np.uint8)
     for i in range(n_bytes):
         byte_val = 0
         for b in range(8):
             byte_val = (byte_val << 1) | (int(self.packet[8*i + b]) & 1)
         self.packed_packet[i] = byte_val
     ```
   - First 4 packed bytes evaluate exactly to:
     - Byte 0: `0b11111001 = 0xF9` (decimal 249)
     - Byte 1: `0b10101111 = 0xAF` (decimal 175)
     - Byte 2: `0b11001101 = 0xCD` (decimal 205)
     - Byte 3: `0b01100101 = 0x65` (decimal 101)
   - When all 125 packed bytes are unpacked MSB-first across all 1000 bit positions, the recovered bit vector is identical to `self.packet` with 0 mismatches.

3. **Buffer Read Boundary & Streaming Integrity**:
   - In `tx_qpsk_hardware_ber_epy_block_0.py` lines 39-54:
     ```python
     def general_work(self, input_items, output_items):
         in0 = input_items[0]
         out = output_items[0]
         n_out = len(out)
         written = 0
         read = min(len(in0), n_out)
         
         while written < read:
             rem = len(self.packed_packet) - self.ptr
             to_write = min(rem, read - written)
             out[written:written+to_write] = self.packed_packet[self.ptr:self.ptr+to_write]
             self.ptr = (self.ptr + to_write) % len(self.packed_packet)
             written += to_write
             
         self.consume(0, read)
         return written
     ```
   - Executed adversarial streaming test suite (`test_m1_tx_adversarial_challenge.py`):
     - **Single-byte chunks (1 byte)**: 10,000 iterations $\to$ 80 full frames streamed with 0 dropped/corrupted bytes.
     - **Prime-sized chunks (2, 3, 5, 7, ..., 251 bytes)**: All non-divisible prime buffer chunks streamed seamlessly.
     - **Boundary-straddling chunks (124, 125, 126, 249, 250, 251 bytes)**: Zero off-by-one errors across frame wraps.
     - **Massive randomized chunks (1..4096 bytes)**: 5,000,000 bytes (40,000 frames) streamed continuously. Concatenated output stream matched the reference frame cycle perfectly: `np.array_equal(collected, expected) == True`.
     - **Asymmetric buffers and zero lengths**: Handled cleanly without exceptions or buffer overflows.

4. **Modulation & Differential QPSK Phase Ambiguity Invariance**:
   - Simulated full modulation loopback (`test_13_modulator_differential_encoding_loopback` and `test_14_differential_phase_ambiguity_invariance`).
   - Under all 4 Costas loop phase lock quadrant ambiguities ($0^\circ, 90^\circ, 180^\circ, 270^\circ$), differential demodulation achieved 0 bit errors.

5. **Tool & Compiler Verification**:
   - `grcc` compilation:
     `& "C:\Users\prana\radioconda\Scripts\grcc.exe" -o c:/Users/prana/OneDrive/Desktop/hqam_stuf/miscellenious c:/Users/prana/OneDrive/Desktop/hqam_stuf/miscellenious/tx_qpsk_hardware_ber.grc`
     Exited with returncode `0`.
   - Standalone test suite:
     `& "C:\Users\prana\radioconda\python.exe" c:/Users/prana/OneDrive/Desktop/hqam_stuf/test_m1_tx_adversarial_challenge.py`
     Result: 14 tests run, 14 passed in 1.583s.
   - Comprehensive test suite:
     `& "C:\Users\prana\radioconda\python.exe" c:/Users/prana/OneDrive/Desktop/hqam_stuf/test_qpsk_ber_engine.py`
     Result: 65 tests run, 65 passed in 14.603s.

---

## 2. Logic Chain

1. **Frame Sizing & Bit-Packing Exactness**:
   - Total frame length is $32 + 968 = 1000$ bits.
   - $1000 \pmod 8 = 0$, dividing cleanly into exactly 125 bytes ($n\_bytes = 125$).
   - The packing loop iterates $i \in [0..124]$ and shifts bits into `byte_val` MSB-first (`(byte_val << 1) | bit`).
   - Unpacking each byte with `(byte >> (7 - b)) & 1` for $b \in [0..7]$ exactly reproduces the original bit sequence.

2. **Pointer Wrapping & Cyclic Continuity**:
   - The embedded block tracks `self.ptr` in $[0, 125)$.
   - In `general_work()`, `rem = len(self.packed_packet) - self.ptr` computes remaining bytes in the current frame.
   - `to_write = min(rem, read - written)` slices the exact sub-array and copies it to `out[written:written+to_write]`.
   - `self.ptr = (self.ptr + to_write) % len(self.packed_packet)` cyclically wraps the pointer back to index 0 when a frame boundary is crossed.
   - Because `written` is incremented by `to_write` in each loop until `written == read`, no bytes are skipped or duplicated, regardless of how fragmented `read` is.

3. **Demodulation Compatibility**:
   - Each byte yields 4 QPSK symbols ($125 \times 4 = 500$ symbols per frame).
   - Constellation modulator parameters match the demodulator chain in `PROJECT.md` (differential encoding, Gray mapping `[0, 1, 3, 2]`, SPS=4, $\alpha=0.35$).
   - Testing confirms 100% bit recovery across arbitrary phase shifts.

---

## 3. Caveats

- **No Caveats**: The implementation was verified empirically across 14 dedicated stress tests, millions of samples, multiple buffer fragmentation patterns, and the full 65-test project test suite.

---

## 4. Conclusion

**Verdict**: `APPROVE`

The Milestone 1 QPSK Transmitter (`tx_qpsk_hardware_ber_epy_block_0.py` and `tx_qpsk_hardware_ber.grc`) satisfies all requirements and passes all adversarial challenges:
- Produces seamless, uncorrupted periodic frames across arbitrary buffer boundaries (verified up to 5,000,000 bytes).
- 1000-bit frame correctly packs MSB-first into 125 bytes and unpacks with 100% bit-level fidelity.
- Preamble (32 bits) and PRBS-42 payload (968 bits) adhere strictly to specification.
- Flowgraph compiles cleanly with `grcc` without warnings or errors.

---

## 5. Verification Method

To independently execute the adversarial challenge suite and verify these findings:

1. **Run Dedicated Adversarial Challenge Suite**:
   ```powershell
   & "C:\Users\prana\radioconda\python.exe" c:/Users/prana/OneDrive/Desktop/hqam_stuf/test_m1_tx_adversarial_challenge.py
   ```
   *Expected Output*: 14 tests run, 14 passed (OK).

2. **Run 4-Tier E2E Project Test Suite**:
   ```powershell
   & "C:\Users\prana\radioconda\python.exe" c:/Users/prana/OneDrive/Desktop/hqam_stuf/test_qpsk_ber_engine.py
   ```
   *Expected Output*: 65 tests run, 65 passed (OK).

3. **Re-compile Flowgraph**:
   ```powershell
   & "C:\Users\prana\radioconda\Scripts\grcc.exe" -o c:/Users/prana/OneDrive/Desktop/hqam_stuf/miscellenious c:/Users/prana/OneDrive/Desktop/hqam_stuf/miscellenious/tx_qpsk_hardware_ber.grc
   ```
   *Expected Output*: Exit code `0`.
