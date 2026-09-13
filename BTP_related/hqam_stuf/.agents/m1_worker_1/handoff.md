# Milestone 1: QPSK Hardware Transmitter Implementation Handoff Report

**Author**: `m1_worker_1`  
**Role**: implementer, qa, specialist  
**Date**: 2026-08-18  
**Artifacts Produced**:
- `miscellenious/tx_qpsk_hardware_ber_epy_block_0.py`
- `miscellenious/tx_qpsk_hardware_ber.grc`
- `miscellenious/tx_qpsk_hardware_ber.py` (Compiled artifact via `grcc`)

---

## 1. Observation

Direct observations from codebase inspection, execution logs, and compilation verification:

1. **Embedded Python Block**:
   - `miscellenious/tx_qpsk_hardware_ber_epy_block_0.py` implements class `blk(gr.basic_block)` with `name='QPSK BER Frame Generator'`, `in_sig=[np.uint8]`, and `out_sig=[np.uint8]`.
   - Frame length: 1000 bits partitioned into 32-bit preamble (`PREAMBLE_32BIT = [1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1]`) and 968-bit PRBS-42 payload (`np.random.seed(42)`, `np.random.randint(0, 2, size=968, dtype=np.uint8)`).
   - Packing: Bits are packed MSB-first into 125 bytes per frame. First two bytes evaluate to `0xF9` and `0xAF`.
   - Work method: `general_work()` streams out cyclic chunks matching input items length and calls `self.consume(0, read)`.

2. **GRC Flowgraph Schema & Connections**:
   - `miscellenious/tx_qpsk_hardware_ber.grc` defines GNU Radio 3.10 YAML flowgraph:
     - `options`: id `tx_qpsk_hardware_ber`, title `QPSK Hardware BER Transmitter`, generate options `qt_gui`.
     - Variables: `samp_rate = 1000000`, `center_freq = 2850000000`, `sps = 4`, `excess_bw = 0.35`, `tx_gain` (range 0..89.8 dB, default 33 dB), `qpsk` (`variable_constellation_rect` with `sym_map: [0, 1, 3, 2]`, `rot_sym: 4`).
     - Blocks: `analog_random_source_x_0` $\to$ `epy_block_0` $\to$ `digital_constellation_modulator_0` $\to$ `uhd_usrp_sink_0`, `qtgui_const_sink_x_0`, `qtgui_freq_sink_x_0`, `qtgui_time_sink_x_0`.
     - Metadata: `file_format: 1`, `grc_version: 3.10.12.0`.

3. **Compilation & Test Execution Results**:
   - `grcc` compilation command:
     `& "C:\Users\prana\radioconda\Scripts\grcc.exe" -o c:/Users/prana/OneDrive/Desktop/hqam_stuf/miscellenious c:/Users/prana/OneDrive/Desktop/hqam_stuf/miscellenious/tx_qpsk_hardware_ber.grc`
     Result: Exited with code `0`, generating `miscellenious/tx_qpsk_hardware_ber.py`.
   - Python bytecode compilation:
     `& "C:\Users\prana\radioconda\python.exe" -m py_compile c:/Users/prana/OneDrive/Desktop/hqam_stuf/miscellenious/tx_qpsk_hardware_ber.py`
     Result: Exited with code `0`.
   - Test harness execution:
     `& "C:\Users\prana\radioconda\python.exe" c:/Users/prana/OneDrive/Desktop/hqam_stuf/test_qpsk_ber_engine.py`
     Result: Ran 65 tests in 13.029s. All 65 passed (65 passed, 0 failures, 0 errors, 0 skipped).

---

## 2. Logic Chain

1. **Bit-to-Byte Alignment**:
   - Total frame size is 1000 bits ($32 + 968 = 1000$).
   - Since $1000 \pmod 8 = 0$, the frame exactly packs into 125 integer bytes without leftover bits.
   - Modulator (`digital_constellation_modulator`) unpacks 2 bits per symbol from each byte (MSB-first: 4 symbols per byte).
   - $125 \text{ bytes} \times 4 \text{ symbols/byte} = 500 \text{ symbols/frame}$.
   - At $sps = 4$ and $samp\_rate = 1.0\text{ MSps}$, each frame occupies $500 \times 4 = 2000\text{ baseband samples}$ ($2.0\text{ ms}$).

2. **Phase Ambiguity Resilience**:
   - Differential encoding (`differential: True` in modulator) with Gray mapping `[0, 1, 3, 2]` encodes bits into phase transitions modulo 4.
   - When carrier phase in receiver locks at any 90-degree quadrant rotation ($0^\circ, 90^\circ, 180^\circ, 270^\circ$), the differential decoder cancels the static phase offset, ensuring error-free payload decoding.

3. **Flowgraph & Embedded Block Synchronization**:
   - In GNU Radio Companion, `_io_cache` in the GRC file matches the signature of `blk` in `tx_qpsk_hardware_ber_epy_block_0.py`.
   - `grcc` validates port types: `analog_random_source_x` (byte) $\to$ `epy_block_0` (byte in, byte out) $\to$ `digital_constellation_modulator` (byte in, complex out) $\to$ `uhd_usrp_sink` (complex in) and GUI sinks (complex in).

---

## 3. Caveats

1. **Hardware Presence**: Direct real-time execution of `tx_qpsk_hardware_ber.py` requires a connected Ettus USRP B210 on USB 3.0. Offline compilation (`grcc`) and DSP unit testing run independently without hardware attached.
2. **RF Gain Safety**: The TX gain slider defaults to 33 dB. In loopback or near-field cable tests into the receiver port, appropriate 30 dB RF attenuators should be used if TX gain is raised above 60 dB to prevent RX LNA saturation.

---

## 4. Conclusion

Milestone 1 is complete:
- `tx_qpsk_hardware_ber_epy_block_0.py` and `tx_qpsk_hardware_ber.grc` are fully implemented with genuine DSP logic matching the project specifications.
- `grcc` flowgraph compilation generates valid, error-free Python code.
- All 65 unit, boundary, integration, and environmental test cases in `test_qpsk_ber_engine.py` pass cleanly.

---

## 5. Verification Method

To independently verify this milestone:

1. **Compile Flowgraph**:
   ```powershell
   & "C:\Users\prana\radioconda\Scripts\grcc.exe" -o c:/Users/prana/OneDrive/Desktop/hqam_stuf/miscellenious c:/Users/prana/OneDrive/Desktop/hqam_stuf/miscellenious/tx_qpsk_hardware_ber.grc
   ```
   *Expected Output*: Exit code `0`, `Generating: .../tx_qpsk_hardware_ber.py`.

2. **Verify Python Syntax**:
   ```powershell
   & "C:\Users\prana\radioconda\python.exe" -m py_compile c:/Users/prana/OneDrive/Desktop/hqam_stuf/miscellenious/tx_qpsk_hardware_ber.py
   ```
   *Expected Output*: Exit code `0`.

3. **Run 4-Tier Test Suite**:
   ```powershell
   & "C:\Users\prana\radioconda\python.exe" c:/Users/prana/OneDrive/Desktop/hqam_stuf/test_qpsk_ber_engine.py
   ```
   *Expected Output*: 65 tests run, 65 passed, 0 failures, 0 errors.
