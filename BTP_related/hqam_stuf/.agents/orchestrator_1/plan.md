# Orchestration Plan: Over-the-Air QPSK Transceiver System

## Objective
Implement and verify an end-to-end OTA QPSK transmission and reception system for USRP B210 in GNU Radio 3.10, featuring full synchronization, GUI tuning sliders, embedded real-time BER/SNR estimation with CSV logging, and a comprehensive tuning guide.

## Phases
1. **Phase 0: Survey & Spec Mining**
   - Survey reference files: `miscellenious/Qpsk_modem.grc`, `miscellenious/tx_bpsk_hardware_ber.grc`, `miscellenious/rx_bpsk_hardware_ber.grc`, `miscellenious/tx_qpsk_hardware.grc`, `miscellenious/rx_qpsk_hardware.grc`.
   - Extract exact parameters, GRC block schemas, UHD sink/source parameters, embedded python block structures.
2. **Phase 1: Architecture & Decomposition (PROJECT.md)**
   - Define exact parameters, variables, block graphs, port interfaces, and slider specifications.
3. **Phase 2: Milestone 1 - QPSK Hardware Transmitter (`tx_qpsk_hardware_ber.grc`)**
   - Frame generator with preamble + pseudo-random payload.
   - Gray-coded QPSK mapping, differential encoding.
   - RRC filter (sps=4, alpha=0.35), UHD USRP Sink.
4. **Phase 3: Milestone 2 - Tunable QPSK Hardware Receiver (`rx_qpsk_hardware_ber.grc`)**
   - AGC -> FLL Band-Edge -> RRC Matched Filter -> Symbol Synchronizer (Gardner/MM) -> Costas Loop -> Adaptive Equalizer (CMA/LMS) -> Constellation Decoder -> Differential Decoder -> Gray Map -> Bit Unpacker.
   - Full QT GUI range sliders and Multi-trace Constellation / Time / Frequency sinks.
5. **Phase 4: Milestone 3 - Embedded Real-Time BER & SNR Measurement Engine**
   - Embedded Python sync block with preamble correlation, frame alignment, BER & quadrant variance SNR estimation, QT GUI status overlay, timestamped CSV logging (`ber_qpsk_log.csv`).
6. **Phase 5: Milestone 4 - Hardware Tuning & Locking Protocol (`TUNING_GUIDE.md`)**
   - Sequential tuning guide (RF Gains -> AGC -> FLL -> Symbol Sync -> Costas -> Equalizer), constellation signatures, diagnostic troubleshooting.
7. **Phase 6: E2E Testing, Compilation & Adversarial Verification**
   - `grcc` compilation tests on flowgraphs, unit tests of Python blocks, BER/SNR engine validation, challenger test runs, and forensic audit.
8. **Phase 7: Final Synthesis & Completion Report**
