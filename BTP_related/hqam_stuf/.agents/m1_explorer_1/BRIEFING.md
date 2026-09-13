# BRIEFING — 2026-08-18T12:22:00Z

## Mission
Design the exact GNU Radio 3.10 YAML flowgraph structure and Python embedded block blueprint for the QPSK Hardware Transmitter (`tx_qpsk_hardware_ber.grc` & `tx_qpsk_hardware_ber_epy_block_0.py`) for Milestone 1.

## 🔒 My Identity
- Archetype: Teamwork explorer
- Roles: Milestone 1 Explorer (QPSK Hardware Transmitter Design)
- Working directory: c:/Users/prana/OneDrive/Desktop/hqam_stuf/.agents/m1_explorer_1
- Original parent: 5ec8b7d3-ea92-47e6-aed4-ec20f5b6f567
- Milestone: Milestone 1 (QPSK Hardware Transmitter)

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Produce exact YAML flowgraph blueprint for `tx_qpsk_hardware_ber.grc`
- Produce exact embedded Python block blueprint for `tx_qpsk_hardware_ber_epy_block_0.py`
- Follow GNU Radio 3.10 YAML and block specifications
- Keep BRIEFING under ~100 lines

## Current Parent
- Conversation ID: 5ec8b7d3-ea92-47e6-aed4-ec20f5b6f567
- Updated: not yet

## Investigation State
- **Explored paths**: `PROJECT.md`, `ORIGINAL_REQUEST.md`, `miscellenious/tx_bpsk_hardware_ber.grc`, `miscellenious/tx_qpsk_hardware.grc`, `miscellenious/Qpsk_modem.grc`, `miscellenious/tx_bpsk_hardware_ber_epy_block_0.py`, `.agents/survey_explorer_1/handoff.md`, `.agents/survey_spec_miner_1/handoff.md`
- **Key findings**:
  - GRC version 3.10.12.0 format.
  - Frame: 32-bit Barker/sync word + 968-bit PRBS-42 payload = 1000 bits = 125 bytes per frame.
  - Rectangular Gray-coded QPSK constellation: `variable_constellation_rect` with `const_points: '[-0.707-0.707j, 0.707-0.707j, +0.707+0.707j, -0.707+0.707j]'` and `sym_map: '[0, 1, 3, 2]'`.
  - Modulator: `digital_constellation_modulator` with `differential: True`, `excess_bw: 0.35`, `samples_per_symbol: 4`.
  - Sinks: USRP Sink (B210, 2.85 GHz, 1.0 MSps, TX Gain slider 0-89.8 dB), QT GUI Constellation Sink, QT GUI Frequency Sink, QT GUI Time Sink for baseband pulses.
- **Unexplored areas**: None for M1 scope.

## Key Decisions Made
- Frame size 1000 bits (32 preamble + 968 PRBS payload) packed into 125 bytes.
- Modulator receives byte stream and outputs complex samples at 4 sps.
- Visualization includes Frequency Sink (Spectrum), Constellation Sink (Constellation), and Time Sink (Baseband I & Q pulses).

## Artifact Index
- `.agents/m1_explorer_1/BRIEFING.md` — Agent memory & state
- `.agents/m1_explorer_1/progress.md` — Progress tracker and heartbeat
- `.agents/m1_explorer_1/handoff.md` — Milestone 1 Specification & Implementation Blueprint Report
