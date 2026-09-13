## 2026-08-18T12:38:50Z
You are m2_explorer_1.
Your working directory: c:/Users/prana/OneDrive/Desktop/hqam_stuf/.agents/m2_explorer_1
Project root: c:/Users/prana/OneDrive/Desktop/hqam_stuf
Flowgraph directory: c:/Users/prana/OneDrive/Desktop/hqam_stuf/miscellenious

Authoritative User Request: c:/Users/prana/OneDrive/Desktop/hqam_stuf/.agents/ORIGINAL_REQUEST.md
Project Scope: c:/Users/prana/OneDrive/Desktop/hqam_stuf/PROJECT.md
Reference Files: `miscellenious/rx_bpsk_hardware_ber.grc`, `miscellenious/rx_qpsk_hardware.grc`, `miscellenious/Qpsk_modem.grc`

Task:
Design the complete GNU Radio 3.10 YAML flowgraph blueprint for `miscellenious/rx_qpsk_hardware_ber.grc` and the embedded Python block `miscellenious/rx_qpsk_hardware_ber_epy_block_1.py`.

Requirements to synthesize into the blueprint:
1. Complete DSP Synchronization Pipeline:
   - UHD USRP Source (B210, `2.85 GHz`, `1.0 MSps`, antenna `"RX2"`, `stream_args: fc32`, `rx_gain` slider).
   - AGC: `analog_agc_cc` (`rate: agc_rate`, `reference: 1.0`, `max_gain: 65536`).
   - FLL Band-Edge: `digital_fll_band_edge_cc` (`filter_size: 45`, `rolloff: excess_bw`, `samps_per_sym: sps`, `w: fll_loop_bw`).
   - Matched Filter: `root_raised_cosine_filter` / FIR filter (`alpha: excess_bw`, `ntaps: 11*sps`, `samp_rate: samp_rate`, `sym_rate: samp_rate/sps`).
   - Symbol Sync: `digital_symbol_sync_cc` (`ted_type: digital.TED_SIGNAL_TIMES_SLOPE_ML` or `TED_GARDNER`, `sps: 4`, `osps: 1`, `loop_bw: timing_loop_bw`, `damping: 1.0`, `resamp_type: digital.IR_MMSE_8TAP`).
   - Adaptive Equalizer: `digital_linear_equalizer` with CMA/LMS algorithm (`num_taps: 15`, `sps: 1`, `modulus: 1`, `step_size: eq_mu`), with `blocks_selector` bypass switch controlled by `eq_bypass`.
   - 4th-Order Costas Loop: `digital_costas_loop_cc` (`order: 4`, `w: costas_loop_bw`).
   - Demapping & Differential Decoding: `digital_constellation_decoder_cb` -> `digital_diff_decoder_bb (modulus=4)` -> `digital_map_bb ([0, 1, 3, 2])` -> `blocks_unpack_k_bits_bb (k=2)`.
2. Embedded Real-Time BER & SNR Engine (`rx_qpsk_hardware_ber_epy_block_1.py`):
   - Derives from `gr.sync_block`, inputs `[np.uint8, np.complex64]` (Port 0 = unpacked bits, Port 1 = phase-locked IQ symbols from Costas loop).
   - Preamble sliding window correlation matching 32-bit sync word `[1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1]` with Hamming error tolerance (`mismatches <= 2`).
   - Cumulative and instantaneous BER computation against 968-bit PRBS-42 payload (`np.random.seed(42)`).
   - Real-time decision-directed 4-quadrant SNR variance estimation with EMA smoothing ($\alpha = 0.05$).
   - Live Qt GUI status overlay (injects `QLabel` and `QTimer` via `inspect.stack()`) displaying status, total bits, errors, BER, and SNR.
   - Timestamped CSV logging to `c:/Users/prana/OneDrive/Desktop/hqam_stuf/miscellenious/ber_qpsk_log.csv` (or relative path).
3. QT GUI Sliders and Layout:
   - Sliders: `rx_gain` (0-76 dB), `agc_rate` (1e-5 to 1e-2), `fll_loop_bw` (0.001 to 0.1), `timing_loop_bw` (0.001 to 0.1), `costas_loop_bw` (0.001 to 0.2), `eq_mu` (1e-5 to 1e-2), `eq_bypass` (0/1).
   - Sinks: Multi-trace Constellation Sink (Trace 1: Post-Costas locked, Trace 2: Post-Sync / Pre-Costas orbit, Trace 3: Pre-Sync input), Frequency Sink, and Time Sink.

Write the complete YAML and Python implementation blueprints in `c:/Users/prana/OneDrive/Desktop/hqam_stuf/.agents/m2_explorer_1/handoff.md` and send a message back.
