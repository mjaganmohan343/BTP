# Comprehensive Survey & Architectural Analysis Report: BPSK to QPSK Hardware Modem Migration

**Author**: survey_explorer_1  
**Date**: 2026-08-18  
**Scope**: Analysis of Reference Flowgraphs (`miscellenious/tx_bpsk_hardware_ber.grc`, `miscellenious/rx_bpsk_hardware_ber.grc`, `miscellenious/Qpsk_modem.grc`, `miscellenious/tx_qpsk_hardware.grc`, `miscellenious/rx_qpsk_hardware.grc`, `miscellenious/tx_bpsk_hardware_ber_epy_block_0.py`, and `hardware_test/rx_hardware_epy_block_1.py`).

---

## 1. Observation

Direct observations from the reference flowgraphs and embedded scripts in `miscellenious/` and `hardware_test/`:

### 1.1 BPSK Hardware Transmitter Structure (`tx_bpsk_hardware_ber.grc` & `tx_bpsk_hardware_ber_epy_block_0.py`)
- **Metadata**: YAML format (`file_format: 1`, `grc_version: 3.10.12.0`, `generate_options: qt_gui`).
- **UHD Sink Configuration** (Lines 294–571):
  - Device Arguments: `dev_addr: ""` (auto-detects USRP B210), `dev_args: ""`
  - Sample Rate: `samp_rate = 1000000` (1.0 Msps)
  - Carrier Frequency: `center_freq = 2850000000` (2.85 GHz)
  - TX Gain: `tx_gain = 33` dB
  - Antenna: `ant0: "TX/RX"`
  - Clock Sync: `sync: pc_clock`, `clock_rate: 0e0`
  - Stream Format: `fc32` (complex float 32)
- **Modulation Parameters**:
  - `bpsk_const`: `variable_constellation` with `const_points: [-1+0j, 1+0j]`, `sym_map: [0, 1]`, `rot_sym: 2`, `type: bpsk`, `normalization: AMPLITUDE_NORMALIZATION`.
  - Samples per Symbol: `sps = 4`
  - Roll-off factor: `Alpha = 0.35`
- **Embedded Python Frame Generator Block** (`tx_bpsk_hardware_ber_epy_block_0.py`):
  - Derives from `gr.basic_block` with input `[np.uint8]` and output `[np.uint8]`.
  - Frame length: 1000 symbols.
  - Preamble: 11 symbols `[1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 0]` (Barker sequence).
  - Payload Reference: 989 pseudo-random bits generated via `np.random.seed(42)` and `np.random.randint(0, 2, size=989, dtype=np.uint8)`.
  - Packing: Packs 8 BPSK symbols into 1 byte (`n_bytes = 1000 // 8 = 125` bytes per frame).
  - Work Function: `general_work` consumes input bytes and writes `self.packed_packet` cyclically into `output_items[0]` based on internal pointer `self.ptr`.
- **Modulator**: `digital_constellation_modulator` with `differential: True`, `excess_bw: Alpha`, `samples_per_symbol: sps` (4), internally performing RRC pulse shaping.

### 1.2 BPSK Hardware Receiver Structure (`rx_bpsk_hardware_ber.grc`)
- **UHD Source Configuration** (Lines 758–1193):
  - Sample Rate: `samp_rate = 1000000` (1.0 Msps)
  - Center Frequency: `center_freq = 2850000000` (2.85 GHz)
  - RX Gain: `rx_gain = 38` dB
  - Antenna: `ant0: "RX2"`
  - Bandwidth: `bw0: 1000000`
  - Stream Format: `fc32`
- **DSP Synchronization Pipeline**:
  1. **Automatic Gain Control (AGC)**: `analog_agc_xx` (`gain: 1.0`, `max_gain: 65536`, `rate: 1e-4`, `reference: 1.0`).
  2. **Frequency Lock Loop (FLL Band-Edge)**: `digital_fll_band_edge_cc` (`filter_size: 45`, `rolloff: 0.35`, `samps_per_sym: 4`, `w: 0.02`).
  3. **Matched Filter (RRC)**: `root_raised_cosine_filter` (`alpha: 0.35`, `ntaps: 11*sps = 44`, `samp_rate: 1e6`, `sym_rate: 2.5e5`, `gain: 1.0`).
  4. **Symbol Timing Synchronizer**: `digital_symbol_sync_xx` (`constellation: digital.constellation_bpsk().base()`, `damping: 1.0`, `loop_bw: 0.03`, `max_dev: 1.5`, `nfilters: 128`, `osps: 1`, `ted_type: digital.TED_GARDNER`, `resamp_type: digital.IR_MMSE_8TAP`).
  5. **Carrier Phase & Fine Frequency Recovery**: `digital_constellation_receiver_cb` (or 2nd-order Costas loop) outputting phase-corrected complex samples on port 4.
  6. **Demodulation & Differential Decoding**:
     - `digital_constellation_decoder_cb` (`bpsk_const`) $\to$ `digital_diff_decoder_bb` (`modulus: 2`).
  7. **Embedded BER & SNR Calculator Block** (`epy_block_1`):
     - Derives from `gr.sync_block` with inputs `[np.uint8, np.complex64]` (port 0 = decoded bits, port 1 = phase-locked IQ symbols).
     - Frame synchronization: Sliding window correlation matching the 11-bit Barker preamble (`mismatches <= 1`).
     - Bit Error Rate (BER): XOR comparison of 989 received payload bits with `self.payload_ref`. Frame jump parsing jumps `idx += 1000` on match.
     - Real-Time SNR Estimation: Slices IQ real axis (`sliced = np.where(reals >= 0, 1.0+0j, -1.0+0j)`), computes noise variance `noise_p = mean(|iq - sliced|^2)`, tracks EMA filtered powers ($\alpha = 0.05$), calculates `snr_db = 10 * log10(avg_signal / avg_noise)`.
     - Injected QT GUI Display: Uses `inspect.stack()` to retrieve `top_block.top_grid_layout`, injects `QLabel` and `QTimer` (200 ms interval) displaying `Total Bits`, `Errors`, `BER`, and `SNR (dB)`.
     - CSV Logging: Logs timestamp, frame count, total bits, total errors, BER, and SNR (dB) to `ber_bpsk_log.csv`.
  8. **Bit Unpacking & GUI Sinks**:
     - `blocks_unpack_k_bits_bb` (`k: 1`) $\to$ `blocks_char_to_float` $\to$ `qtgui_time_sink_x` & `blocks_file_sink`.
     - `qtgui_const_sink_x`: Dual-trace showing "Post-Costas" (locked constellation) and "Post-Sync" (pre-Costas constellation ring).

### 1.3 QPSK Simulation & Prototype Flowgraphs (`Qpsk_modem.grc`, `tx_qpsk_hardware.grc`, `rx_qpsk_hardware.grc`)
- **QPSK Constellation Definition**:
  - `id: variable_constellation_rect`
  - `const_points: '[-0.707-0.707j, 0.707-0.707j, +0.707+0.707j, -0.707+0.707j]'`
  - `sym_map: '[0, 1, 3, 2]'` (Gray coding)
  - `rot_sym: '4'`
- **QPSK Receiver Pipeline in `Qpsk_modem.grc` & `rx_qpsk_hardware.grc`**:
  - RRC Matched Filter (`alpha: 0.35`, `ntaps: 44`)
  - Symbol Synchronizer (`digital_symbol_sync_xx`, `ted_type: TED_SIGNAL_TIMES_SLOPE_ML` or `TED_GARDNER`, `sps: 4`, `osps: 1`)
  - Costas Loop: `digital_costas_loop_cc` with `order: '4'`, `w: costas_loop_bw` (0.0628 rad/sample)
  - Constellation Decoder: `digital_constellation_decoder_cb` (`qpsk`)
  - Differential Decoder: `digital_diff_decoder_bb` (`modulus: '4'`, `coding: digital.DIFF_DIFFERENTIAL`)
  - Gray Inverse Map: `digital_map_bb` (`map: '[0, 1, 3, 2]'`)
  - Bit Unpacker: `blocks_unpack_k_bits_bb` (`k: '2'`)

---

## 2. Logic Chain

1. **Hardware Parameters**:
   - The USRP B210 operates reliably with `samp_rate = 1.0 Msps`, `center_freq = 2.85 GHz`, `tx_gain = 33` dB, and `rx_gain = 38` dB. `ant0: "TX/RX"` on transmitter and `ant0: "RX2"` on receiver match standard B210 SMA port designations.
   - At `samp_rate = 1.0 Msps` and `sps = 4`, the symbol rate is $R_s = 250\text{ kbaud}$. For BPSK, bit rate is $250\text{ kbps}$; for QPSK, bit rate is $500\text{ kbps}$.

2. **Transition from BPSK to QPSK Modulation**:
   - **Bit Packing**: In BPSK (1 bit/sym), each byte holds 8 symbols ($1000 \text{ symbols} / 8 = 125 \text{ bytes}$). In QPSK (2 bits/sym), each byte holds 4 symbols ($1000 \text{ symbols} \times 2 \text{ bits} / 8 = 250 \text{ bytes}$).
   - **Phase Ambiguity & Differential Coding**: A QPSK constellation has a 4-fold ($90^\circ, 180^\circ, 270^\circ, 360^\circ$) rotational ambiguity. Differential encoding modulo 4 (`digital_diff_decoder_bb` with `modulus = 4`) combined with Gray mapping (`sym_map = [0, 1, 3, 2]`) ensures that any $90^\circ$ carrier phase slip does not corrupt the decoded bitstream.
   - **Carrier Recovery**: QPSK requires a 4th-order Costas loop (`digital_costas_loop_cc` with `order = 4`), which calculates phase error across all 4 quadrants ($I \cdot \text{sgn}(Q) - Q \cdot \text{sgn}(I)$).

3. **Frame Structure & Embedded Block Design for QPSK**:
   - **Preamble**: To provide robust frame acquisition in QPSK, the preamble should be defined as a known sequence of QPSK symbols (e.g. an 11-symbol or 16-symbol sequence with low periodic and aperiodic cross-correlation).
   - **Payload**: Pseudo-random integer symbols in range $[0, 3]$ (or PRBS bits unpacked to symbol pairs).
   - **BER Calculation**: Receiver can either compare unpacked bits ($k=2$) or decoded symbol indices with a Gray-coded LUT. Direct bit comparison ($k=2$ unpacked bits) matches the standard BER definition ($\text{BER} = N_{\text{errors}} / N_{\text{bits}}$).
   - **SNR Estimation for QPSK**: For normalized QPSK points $(\pm 1 \pm j)/\sqrt{2}$, the decision slicer is:
     $$\hat{s}_k = \frac{\text{sgn}(\text{Re}(y_k)) + j \cdot \text{sgn}(\text{Im}(y_k))}{\sqrt{2}}$$
     Noise error vector: $e_k = y_k - \hat{s}_k$.
     Signal power: $P_s = 1.0$; Noise power: $P_n = \text{EMA}\left(|e_k|^2\right)$.
     $$\text{SNR}_{\text{dB}} = 10 \log_{10}\left(\frac{P_s}{P_n}\right)$$

4. **Multipath Mitigation & Equalization**:
   - For hardware OTA links with multipath reflections, an adaptive equalizer (e.g., `digital_cma_equalizer_cc` or `digital_lms_dd_equalizer_cc` with $\mu$ slider and bypass option) inserted between the symbol synchronizer and Costas loop eliminates inter-symbol interference (ISI).

5. **GRC File Generation Rules**:
   - GRC 3.10 uses standard YAML syntax. Block definitions require specific port naming (`'0'`, `'1'`, etc.), coordinate placement `[x, y]`, and valid variable expressions.
   - Sliders (`variable_qtgui_range`) provide interactive run-time tuning for hardware gain, AGC rate, FLL bandwidth, timing loop bandwidth, Costas loop bandwidth, and equalizer gain.

---

## 3. Caveats

1. **Hardware Clock Drift**: The USRP B210 internal TCXO has an initial frequency offset of up to $\pm 2.0\text{ ppm}$ ($\approx \pm 5.7\text{ kHz}$ at $2.85\text{ GHz}$). FLL Band-Edge filter bandwidth must be wide enough ($w \approx 0.02$) during initial acquisition, then narrowed for low phase jitter.
2. **Differential Decoding Error Multiplication**: In differential decoding, a single isolated symbol decision error causes two adjacent decoded symbol errors. BER comparisons against theoretical curves must account for the standard differential penalty factor ($P_{b,\text{diff}} \approx 2 P_{b,\text{coherent}}$ at high SNR).
3. **Preamble False Locking**: In low SNR conditions, sliding window correlation requires a strict threshold (e.g., $\le 1$ bit mismatch over 22 bits) and frame jump locking to prevent false positive frame alignments.

---

## 4. Conclusion

The reference BPSK hardware flowgraphs provide a verified baseline for USRP B210 streaming, embedded python block frame generation, real-time GUI injection, and CSV logging. The migration to QPSK requires:
1. **Transmitter (`tx_qpsk_hardware_ber.grc`)**: Frame generator producing 1000 QPSK symbols (2000 bits / 250 bytes), Gray-coded QPSK constellation, differential modulator, RRC pulse shaping ($sps=4, \alpha=0.35$), UHD sink ($2.85\text{ GHz}, 1\text{ Msps}$).
2. **Receiver (`rx_qpsk_hardware_ber.grc`)**: AGC $\to$ FLL Band-Edge $\to$ RRC Matched Filter $\to$ Symbol Sync (Gardner / MM) $\to$ CMA/LMS Equalizer (with GUI bypass/gain) $\to$ 4th-Order Costas Loop $\to$ Constellation Decoder $\to$ Differential Decoder (mod 4) $\to$ Gray Inverse Map $\to$ Embedded BER/SNR Engine & GUI Overlay $\to$ Bit Unpacker ($k=2$).
3. **Embedded Receiver Engine**: Enhanced sync block supporting 2-bit/sym QPSK correlation, decision-directed 4-quadrant SNR estimation, live Qt GUI metrics, and `ber_qpsk_log.csv` logging.

---

## 5. Verification Method

1. **File Inspection**:
   - Check `miscellenious/tx_bpsk_hardware_ber.grc`, `rx_bpsk_hardware_ber.grc`, and `Qpsk_modem.grc` for consistency with GNU Radio 3.10 block specifications.
2. **Flowgraph Compilation**:
   - Run `grcc` on generated `.grc` flowgraphs:
     ```powershell
     grcc miscellenious/tx_qpsk_hardware_ber.grc
     grcc miscellenious/rx_qpsk_hardware_ber.grc
     ```
   - Invalidation condition: `grcc` returns non-zero exit code or unresolved block errors.
3. **BER & SNR Accuracy**:
   - Validate mathematical correctness of QPSK quadrant slicing, Gray code mapping table `[0, 1, 3, 2]`, and 2-bit unpacking logic.
