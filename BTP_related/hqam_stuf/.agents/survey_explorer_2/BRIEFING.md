# BRIEFING — 2026-08-18

## Mission
Investigate R3 (Embedded Real-Time BER & SNR Measurement Engine), R4 (Hardware Tuning & Locking Protocol), and Test & Verification strategy for over-the-air QPSK transceiver system.

## 🔒 My Identity
- Archetype: explorer
- Roles: survey, analysis, synthesis
- Working directory: c:/Users/prana/OneDrive/Desktop/hqam_stuf/.agents/survey_explorer_2
- Original parent: 5ec8b7d3-ea92-47e6-aed4-ec20f5b6f567
- Milestone: survey_phase

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Analyze R3 (BER/SNR engine), R4 (Tuning Guide), and Test/Verification strategy for QPSK PlutoSDR/USRP transceiver system.

## Current Parent
- Conversation ID: 5ec8b7d3-ea92-47e6-aed4-ec20f5b6f567
- Updated: 2026-08-18

## Investigation State
- **Explored paths**:
  - `ORIGINAL_REQUEST.md`: System requirements and acceptance criteria.
  - `miscellenious/rx_bpsk_hardware_ber.grc`: Prior BPSK BER and SNR embedded block implementation.
  - `miscellenious/tx_bpsk_hardware_ber_epy_block_0.py`: Prior BPSK frame generator block.
  - `miscellenious/Qpsk_modem.grc`: GNU Radio QPSK reference simulation flowgraph (constellation, differential decoding, Gray mapping `[0, 1, 3, 2]`, 2-bit unpacking).
  - `miscellenious/tx_qpsk_hardware.grc` & `miscellenious/rx_qpsk_hardware.grc`: Existing QPSK hardware flowgraphs.
  - Environment investigation: Radioconda (`C:\Users\prana\radioconda`), GNU Radio 3.10.12.0, `grcc` compiler executable (`C:\Users\prana\radioconda\Scripts\grcc.exe`).
- **Key findings**:
  - Validated frame synchronization on unpacked bitstreams using Hamming correlation with 32-bit Barker/PN preamble and 968-bit pseudo-random payload (1000-bit frame).
  - Validated Decision-Directed Quadrant Symbol Variance SNR Estimator ($\text{SNR}_{\text{dB}} = 10 \log_{10}(P_{\text{sig}} / \sigma^2_{\text{noise}})$) with dynamic amplitude scaling across diverse SNR conditions (5 to 25 dB).
  - Verified stack inspection (`inspect.stack()`) PyQt5 `QLabel` / `QTimer` overlay injection and CSV logging mechanism.
  - Formulated 7-stage sequential tuning protocol (RF Gains $\to$ AGC $\to$ FLL $\to$ Symbol Sync $\to$ Costas Loop $\to$ Equalizer $\to$ Frame Sync) and corresponding visual constellation signatures.
  - Verified standalone Python unit test framework and `grcc` flowgraph compilation commands.
- **Unexplored areas**: None.

## Key Decisions Made
- Confirmed dual-port embedded block architecture (`in_bits` byte, `in_iq` complex64) as the most robust architecture for decoupled bit-level frame sync and symbol-level SNR estimation.

## Artifact Index
- handoff.md — Complete 5-component survey and analysis report.
