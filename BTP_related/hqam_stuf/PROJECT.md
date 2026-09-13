# Project: Over-The-Air QPSK Hardware Transceiver with Real-Time BER & SNR Monitoring

## Architecture
- **Transmitter**: Frame Generator (Preamble + Seeded PRBS Payload) -> Rectangular QPSK Constellation Modulator (Differential + Gray Coding + RRC Pulse Shaping at SPS=4, alpha=0.35) -> UHD USRP Sink (B210, 2.85 GHz, 1.0 MSps, TX Gain Slider).
- **Receiver DSP Synchronization Pipeline**: UHD USRP Source (B210, 2.85 GHz, 1.0 MSps, RX Gain Slider) -> AGC (Power Normalization) -> FLL Band-Edge (Coarse CFO Correction) -> RRC Matched Filter (alpha=0.35, 44 taps) -> Symbol Synchronizer (Gardner/ML TED, 8-tap MMSE, SPS=4 -> OSPS=1) -> Adaptive Equalizer (CMA/LMS, 15 taps, step-size slider, bypass selector) -> 4th-Order Costas Loop (Phase Lock & Fine CFO) -> Multi-trace Sinks.
- **Demodulation & Decoding Chain**: Costas Loop -> Constellation Decoder -> Differential Decoder (modulo 4) -> Gray Inverse Map [0, 1, 3, 2] -> Bit Unpacker (k=2).
- **Embedded Python Measurement Engine**: Dual-port Sync Block taking unpacked bitstream (Port 0) and phase-locked complex IQ (Port 1) -> Preamble Correlation & Frame Lock -> Bit Error Rate (BER) Counter -> Decision-Directed 4-Quadrant SNR Estimator with EMA -> Live Qt GUI Status Overlay (`QLabel` + `QTimer`) -> Timestamped CSV Logger (`ber_qpsk_log.csv`).

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | TX Frame Generator | Preamble (32 bits) + Pseudo-Random Payload (968 bits, seed 42) frame generator packed 8 bits/byte | M1 | ORIGINAL_REQUEST §R1 |
| 2 | QPSK Constellation Object | `variable_constellation_rect` with Gray mapping `[0, 1, 3, 2]` and normalized points | M1, M2 | ORIGINAL_REQUEST §R1 |
| 3 | QPSK Differential Modulator | `digital_constellation_modulator` with differential encoding and RRC pulse shaping (SPS=4, $\alpha=0.35$) | M1 | ORIGINAL_REQUEST §R1 |
| 4 | UHD USRP Sink | USRP B210 TX sink at 2.85 GHz, 1.0 MSps with parameterized TX gain slider | M1 | ORIGINAL_REQUEST §R1 |
| 5 | UHD USRP Source | USRP B210 RX source at 2.85 GHz, 1.0 MSps with parameterized RX gain slider | M2 | ORIGINAL_REQUEST §R2 |
| 6 | Automatic Gain Control | Complex AGC (`analog_agc_cc`) normalizing amplitude to 1.0 with rate slider | M2 | ORIGINAL_REQUEST §R2 |
| 7 | FLL Band-Edge Filter | Coarse CFO correction (`digital_fll_band_edge_cc`) with loop bandwidth slider | M2 | ORIGINAL_REQUEST §R2 |
| 8 | RRC Matched Filter | Matched filtering (`root_raised_cosine_filter`) with $\alpha=0.35$, 44 taps at 1.0 MSps | M2 | ORIGINAL_REQUEST §R2 |
| 9 | Symbol Synchronizer | Timing recovery (`digital_symbol_sync_cc`) with Gardner/ML TED, 8-tap MMSE, timing loop BW slider | M2 | ORIGINAL_REQUEST §R2 |
| 10 | Adaptive Equalizer | Multipath equalizer (`digital_linear_equalizer` CMA/LMS) with step size slider and bypass selector | M2 | ORIGINAL_REQUEST §R2 |
| 11 | 4th-Order Costas Loop | Carrier phase & fine frequency tracking (`digital_costas_loop_cc`, order=4) with Costas loop BW slider | M2 | ORIGINAL_REQUEST §R2 |
| 12 | Demapping & Diff Decoding | Constellation Decoder -> Diff Decoder (mod 4) -> Gray Map [0,1,3,2] -> Bit Unpacker (k=2) | M2 | ORIGINAL_REQUEST §R2 |
| 13 | QT GUI Interactive Sliders | Sliders for RF Gains, AGC Rate, FLL BW, Timing BW, Costas BW, Equalizer $\mu$/Bypass | M2 | ORIGINAL_REQUEST §R2 |
| 14 | Multi-Trace Sinks | Constellation Sink (Pre-Sync, Post-Sync, Post-Costas), Time Domain Sink, Frequency Sink | M2 | ORIGINAL_REQUEST §R2 |
| 15 | Frame Synchronization | Preamble sliding window correlation with Hamming error tolerance | M3 | ORIGINAL_REQUEST §R3 |
| 16 | Real-Time BER Calculator | Cumulative & Instantaneous BER calculation against reference PRBS payload | M3 | ORIGINAL_REQUEST §R3 |
| 17 | Decision-Directed SNR Engine | 4-quadrant decision-directed noise variance estimation with EMA smoothing | M3 | ORIGINAL_REQUEST §R3 |
| 18 | Live Qt GUI Status Overlay | Dynamic color-coded Qt status text injected via call-stack inspection | M3 | ORIGINAL_REQUEST §R3 |
| 19 | CSV Logging Engine | Timestamped real-time logging to `ber_qpsk_log.csv` | M3 | ORIGINAL_REQUEST §R3 |
| 20 | Sequential Tuning Guide | 7-stage sequential bring-up and locking procedure documented in `TUNING_GUIDE.md` | M4 | ORIGINAL_REQUEST §R4 |
| 21 | Diagnostic Visual Signatures | Visual constellation signatures and troubleshooting matrix in `TUNING_GUIDE.md` | M4 | ORIGINAL_REQUEST §R4 |
| 22 | Flowgraph Compilation & E2E Validation | Syntax validation, `grcc` compilation without errors, and standalone Python unit tests | E2E | Acceptance Criteria |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | M1: QPSK Hardware Transmitter | `tx_qpsk_hardware_ber.grc` & TX Frame Generator embedded block | None | DONE |
| 2 | M2: Tunable QPSK Hardware Receiver | `rx_qpsk_hardware_ber.grc` with complete DSP sync chain & QT GUI sliders | M1 | PLANNED |
| 3 | M3: Embedded Real-Time BER & SNR Engine | `rx_qpsk_hardware_ber_epy_block_1.py` dual-port sync block, Qt GUI overlay, CSV logger | M2 | PLANNED |
| 4 | M4: Hardware Tuning & Locking Protocol | `TUNING_GUIDE.md` comprehensive step-by-step locking guide & troubleshooting matrix | M1, M2, M3 | PLANNED |
| 5 | E2E: Compilation & Test Verification | Multi-tier test suite, standalone unit tests, `grcc` compilation checks | M1, M2, M3, M4 | PLANNED |

## Interface Contracts
### TX Frame Generator -> QPSK Modulator
- Frame Length: 1000 bits (32-bit sync word `[1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1]` + 968-bit PRBS payload seeded at 42).
- Output Port 0: `uint8` byte stream (packed 8 bits per byte = 125 bytes per frame).
- Modulator: `digital_constellation_modulator` with `constellation: qpsk`, `differential: True`, `pre_diff_code: True`, `samples_per_symbol: 4`, `excess_bw: 0.35`.

### Demodulation Chain -> BER & SNR Engine
- Port 0 (`in_bits`): `uint8` stream of individual unpacked bits (0 or 1) from `blocks_unpack_k_bits_bb (k=2)` after `digital_map_bb ([0, 1, 3, 2])`, `digital_diff_decoder_bb (modulus=4)`, and `digital_constellation_decoder_cb (qpsk)`.
- Port 1 (`in_iq`): `complex64` stream of phase-locked 1 SPS constellation symbols from `digital_costas_loop_cc`.
- Output Port 0: `uint8` stream of validated payload bits.

### CSV Log Format (`ber_qpsk_log.csv`)
- Header: `timestamp,frame,total_bits,bit_errors,ber,snr_db`
- Row Format: `%.3f,%d,%d,%d,%.4e,%.2f`

## Code Layout
- `miscellenious/tx_qpsk_hardware_ber.grc`: QPSK Hardware Transmitter GNU Radio 3.10 flowgraph.
- `miscellenious/rx_qpsk_hardware_ber.grc`: Tunable QPSK Hardware Receiver GNU Radio 3.10 flowgraph.
- `miscellenious/tx_qpsk_hardware_ber_epy_block_0.py`: Embedded TX Frame Generator Python block.
- `miscellenious/rx_qpsk_hardware_ber_epy_block_1.py`: Embedded RX BER/SNR Measurement & GUI/CSV Logger Python block.
- `miscellenious/TUNING_GUIDE.md`: Comprehensive Hardware Tuning & Locking Protocol.
- `test_qpsk_ber_engine.py`: Standalone Python DSP test suite covering frame sync, BER accumulation, SNR estimator precision, phase ambiguity invariance, and CSV formatting.
