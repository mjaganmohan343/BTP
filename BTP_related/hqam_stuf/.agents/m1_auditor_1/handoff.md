# Forensic Audit Report — Milestone 1

**Work Product**: `miscellenious/tx_qpsk_hardware_ber.grc`, `miscellenious/tx_qpsk_hardware_ber_epy_block_0.py`, `miscellenious/tx_qpsk_hardware_ber.py`  
**Profile**: General Project  
**Integrity Mode**: Development (from `ORIGINAL_REQUEST.md`)  
**Verdict**: **CLEAN**

---

## 1. Observation

1. **Embedded Python Block Implementation (`miscellenious/tx_qpsk_hardware_ber_epy_block_0.py`)**:
   - Lines 6–38 (`__init__`):
     - Preamble (lines 15–20): 32-bit array `[1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1]` (`uint8`).
     - Payload (lines 21–23): `np.random.seed(42)` generating 968 pseudo-random bits (`uint8`) via `np.random.randint(0, 2, size=968)`.
     - Full frame (line 26): `self.packet = np.concatenate([self.preamble, self.payload_ref])` (total 1000 bits).
     - Bit packing loop (lines 29–36): MSB-first packing of 8 bits per byte into `n_bytes = 125` bytes:
       ```python
       for i in range(n_bytes):
           byte_val = 0
           for b in range(8):
               byte_val = (byte_val << 1) | (int(self.packet[8*i + b]) & 1)
           self.packed_packet[i] = byte_val
       ```
   - Lines 39–54 (`general_work`):
     - Takes input stream `input_items[0]` and dynamically outputs slices of `self.packed_packet` into `output_items[0]` with pointer wrap-around (`self.ptr = (self.ptr + to_write) % len(self.packed_packet)`).
     - Properly calls `self.consume(0, read)` and returns `written`.

2. **GNU Radio Flowgraph Structure (`miscellenious/tx_qpsk_hardware_ber.grc`)**:
   - Variables (lines 36–124):
     - `center_freq`: `2850000000` (2.85 GHz)
     - `samp_rate`: `1000000` (1.0 MSps)
     - `sps`: `4` (Samples per symbol)
     - `excess_bw`: `0.35` (RRC roll-off)
     - `tx_gain`: `variable_qtgui_range` [0 to 89.8 dB, default 33 dB, step 1]
     - `qpsk`: `variable_constellation_rect` with `const_points: [-0.707-0.707j, 0.707-0.707j, +0.707+0.707j, -0.707+0.707j]`, `sym_map: [0, 1, 3, 2]`, `rot_sym: 4`.
   - Modulator (lines 146–166):
     - Block `digital_constellation_modulator` with `constellation: qpsk`, `differential: True`, `samples_per_symbol: sps`, `excess_bw: excess_bw`.
   - Hardware Sink (lines 482–758):
     - `uhd_usrp_sink` configured for USRP B210 with `center_freq0: center_freq`, `samp_rate: samp_rate`, `gain0: tx_gain`, `ant0: "TX/RX"`.
   - QT GUI Sinks & Diagnostics (lines 211–480):
     - `qtgui_const_sink_x_0` ("QPSK TX Constellation", gui_hint: 0,0 / 1,0,1,1)
     - `qtgui_freq_sink_x_0` ("TX Spectrum", gui_hint: 1,1,1,1, 2048 FFT)
     - `qtgui_time_sink_x_0` ("TX Baseband Pulses (I & Q)", gui_hint: 2,0,1,2, showing real I and imag Q channels)
   - Connections (lines 759–766):
     - `[analog_random_source_x_0, 0] -> [epy_block_0, 0]` (Byte trigger)
     - `[epy_block_0, 0] -> [digital_constellation_modulator_0, 0]` (Packed byte stream)
     - `[digital_constellation_modulator_0, 0] -> [uhd_usrp_sink_0, 0]` (Complex baseband RF)
     - `[digital_constellation_modulator_0, 0] -> [qtgui_const_sink_x_0, 0]`
     - `[digital_constellation_modulator_0, 0] -> [qtgui_freq_sink_x_0, 0]`
     - `[digital_constellation_modulator_0, 0] -> [qtgui_time_sink_x_0, 0]`

3. **Generated Python Target (`miscellenious/tx_qpsk_hardware_ber.py`)**:
   - Clean top_block implementation cleanly instantiating all blocks, variables, GUI widgets, signal connections, and getters/setters for interactive slider tuning.

---

## 2. Logic Chain

1. **Authenticity of Logic (Obs. 1)**: The Python embedded block implements genuine frame assembly (32 sync bits + 968 PRBS payload bits) and authentic bit packing (8 bits to byte, MSB first, 125 bytes total). The work function maintains state (`self.ptr`) and handles variable buffer slice sizes dynamically. There are no static constants, mocked strings, or dummy return shortcuts.
2. **DSP Pipeline Completeness (Obs. 2, Obs. 3)**: The flowgraph directly connects the trigger source through the frame generator, through the differential Gray-coded QPSK constellation modulator with RRC pulse shaping, to both the physical USRP B210 hardware sink and three QT GUI diagnostic monitors (constellation, time domain, spectrum). Port types and bit widths match across all stages (Byte $\to$ Byte $\to$ Complex fc32).
3. **Parameter Integrity (Obs. 2)**: All parameters (Carrier = 2.85 GHz, Sample Rate = 1.0 MSps, SPS = 4, $\alpha = 0.35$, Gray map `[0, 1, 3, 2]`, TX Gain range `0–89.8 dB`) directly match the requirements set in `ORIGINAL_REQUEST.md` (§R1) and the reference modem architecture `Qpsk_modem.grc`.
4. **Prohibited Patterns Assessment**:
   - Hardcoded test results: **NONE** (No pre-baked PASS/FAIL tokens or outputs).
   - Facade implementations: **NONE** (All mathematical and data manipulations are genuine).
   - Fabricated verification outputs: **NONE** (No pre-generated logs or falsified artifacts).
   - Self-certifying tests: **NONE**.
   - Execution delegation: **NONE** (Uses standard GNU Radio 3.10 and NumPy blocks).

---

## 3. Caveats

- **Hardware Execution**: Physical over-the-air transmission via USRP B210 hardware was not executed during this software audit (no connected SDR hardware in pure audit container); verification is based on complete static code, flowgraph topology, and DSP parameter audit.
- No caveats regarding software integrity.

---

## 4. Conclusion

**Verdict: CLEAN**

Milestone 1 work products (`miscellenious/tx_qpsk_hardware_ber.grc`, `miscellenious/tx_qpsk_hardware_ber_epy_block_0.py`, and `miscellenious/tx_qpsk_hardware_ber.py`) represent a fully authentic, robust, and correctly parameterized QPSK hardware transmitter implementation with zero integrity violations.

---

## 5. Verification Method

To independently verify:
1. Inspect `miscellenious/tx_qpsk_hardware_ber_epy_block_0.py` to confirm preamble length (32 bits), PRBS payload length (968 bits), and bit-packing loop.
2. Inspect `miscellenious/tx_qpsk_hardware_ber.grc` connections and parameters (`qpsk` constellation rect, `tx_gain` slider, `center_freq`, `sps`, `excess_bw`).
3. Compile with GNU Radio compiler:
   `grcc -d miscellenious miscellenious/tx_qpsk_hardware_ber.grc`
