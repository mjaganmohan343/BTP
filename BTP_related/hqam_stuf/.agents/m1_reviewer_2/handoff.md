# Milestone 1 Review & Adversarial Challenge Report

**Reviewer**: m1_reviewer_2
**Roles**: reviewer, critic
**Date**: 2026-08-18
**Verdict**: **APPROVE**

---

## 1. Observation

Direct observations from independent static inspection, compilation, and test execution:

1. **Embedded Python Block (`miscellenious/tx_qpsk_hardware_ber_epy_block_0.py`)**:
   - Class `blk(gr.basic_block)` implements authentic frame generation and preamble insertion (lines 4-55).
   - `self.preamble` (lines 15-20) defines the exact 32-bit sync sequence:
     `[1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1]`
   - `self.payload_ref` (lines 21-23) initializes PRBS payload with `np.random.seed(42)` and `np.random.randint(0, 2, size=968)`.
   - MSB-first packing (lines 28-35) packs 1000 bits into 125 bytes, beginning with `0xF9` and `0xAF`.
   - `general_work()` (lines 39-54) streams out chunks matching `read = min(len(in0), n_out)` with circular pointer wrapping and `self.consume(0, read)`.
   - Zero hardcoded test shortcuts, facades, or dummy implementations found.

2. **GRC Flowgraph Schema & Layout (`miscellenious/tx_qpsk_hardware_ber.grc`)**:
   - Flowgraph ID `tx_qpsk_hardware_ber`, generate options `qt_gui`, GRC version `3.10.12.0`.
   - Parameters: `center_freq = 2.85 GHz`, `samp_rate = 1.0 MSps`, `sps = 4`, `excess_bw = 0.35`, `tx_gain` range `[0..89.8 dB, default 33 dB, gui_hint 0,0,1,1]`.
   - `qpsk` constellation rect: Gray map `[0, 1, 3, 2]`, 4 rotational symmetries, normalized constellation points.
   - Sinks: `uhd_usrp_sink_0` (fc32, USRP B210 TX/RX), `qtgui_const_sink_x_0` (gui_hint `1,0,1,1`), `qtgui_freq_sink_x_0` (gui_hint `1,1,1,1`), `qtgui_time_sink_x_0` (gui_hint `2,0,1,2`).
   - Connections: `analog_random_source_x_0` -> `epy_block_0` -> `digital_constellation_modulator_0` -> `uhd_usrp_sink_0` and GUI sinks.

3. **Compilation & Runtime Verification**:
   - `grcc` compilation: Generated `miscellenious/tx_qpsk_hardware_ber.py` with exit code `0`.
   - `py_compile` bytecode compilation: Exited with code `0` on both transmitter files.
   - Standalone GNU Radio flowgraph execution: Successfully streamed 2560 bytes through `tx_qpsk_hardware_ber_epy_block_0.blk` with 100% byte fidelity and cyclic periodicity.
   - Full 4-tier test harness (`test_qpsk_ber_engine.py`): 65/65 tests passed in 13.589s.

---

## 2. Logic Chain

1. **Authenticity & Integrity**:
   - Direct inspection confirms that the Python block contains real pseudo-random binary sequence generation, bit-to-byte packing loops, and stream buffer management without hardcoded shortcuts.
2. **Downstream Receiver Compatibility (Milestones 2 & 3)**:
   - Total frame size is 1000 bits (32 preamble + 968 PRBS payload) which packs exactly into 125 integer bytes without residual bits.
   - Differential Gray encoding [0, 1, 3, 2] eliminates 90-degree phase ambiguities upon downstream demodulation.
3. **Flowgraph Conformance**:
   - Parameter definitions, types, connections, and GUI layout hints match project requirements.

---

## 3. Caveats

1. **Hardware Presence**: Verification was performed via offline compilation (grcc), GNU Radio software flowgraphs, and DSP test suites. Over-the-air RF radiation requires a physically connected USRP B210 on USB 3.0.
2. **RF Safety**: Default TX gain is 33 dB. In direct cable loopback setups, use 30 dB RF attenuators if TX gain is set above 60 dB.

---

## 4. Conclusion

**Verdict: APPROVE**

Milestone 1 satisfies all requirements in PROJECT.md and ORIGINAL_REQUEST.md.

---

## 5. Verification Method

1. **Compile Flowgraph**:
   ```powershell
   & "C:\Users\prana\radioconda\Scripts\grcc.exe" -o c:/Users/prana/OneDrive/Desktop/hqam_stuf/miscellenious c:/Users/prana/OneDrive/Desktop/hqam_stuf/miscellenious/tx_qpsk_hardware_ber.grc
   ```
   *Expected Output*: Exit code `0`, generating `tx_qpsk_hardware_ber.py`.

2. **Verify Python Bytecode**:
   ```powershell
   & "C:\Users\prana\radioconda\python.exe" -m py_compile c:/Users/prana/OneDrive/Desktop/hqam_stuf/miscellenious/tx_qpsk_hardware_ber.py c:/Users/prana/OneDrive/Desktop/hqam_stuf/miscellenious/tx_qpsk_hardware_ber_epy_block_0.py
   ```
   *Expected Output*: Exit code `0`.

3. **Execute Full 4-Tier Test Suite**:
   ```powershell
   & "C:\Users\prana\radioconda\python.exe" c:/Users/prana/OneDrive/Desktop/hqam_stuf/test_qpsk_ber_engine.py
   ```
   *Expected Output*: 65 tests run, 65 passed, 0 failures, 0 errors.
