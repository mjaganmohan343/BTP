# BRIEFING — 2026-08-18T12:12:30Z

## Mission
Investigate and document the reference hardware flowgraphs in `miscellenious/` (tx/rx BPSK, QPSK, embedded python blocks, GRC format, transition requirements to QPSK).

## 🔒 My Identity
- Archetype: explorer
- Roles: investigator, synthesis
- Working directory: c:/Users/prana/OneDrive/Desktop/hqam_stuf/.agents/survey_explorer_1
- Original parent: 5ec8b7d3-ea92-47e6-aed4-ec20f5b6f567
- Milestone: milestone-1-survey

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Analyze BPSK hardware TX/RX flowgraphs and embedded python blocks
- Examine GRC YAML syntax and structure in GNU Radio 3.10
- Detail transition steps from BPSK to QPSK with hardware considerations

## Current Parent
- Conversation ID: 5ec8b7d3-ea92-47e6-aed4-ec20f5b6f567
- Updated: 2026-08-18T12:12:30Z

## Investigation State
- **Explored paths**:
  - `miscellenious/tx_bpsk_hardware_ber.grc` & `tx_bpsk_hardware_ber_epy_block_0.py`
  - `miscellenious/rx_bpsk_hardware_ber.grc`
  - `miscellenious/Qpsk_modem.grc`
  - `miscellenious/tx_qpsk_hardware.grc` & `rx_qpsk_hardware.grc`
  - `hardware_test/rx_hardware_epy_block_1.py` & `rx_hardware_epy_block_0.py`
- **Key findings**:
  - Documented exact USRP parameters (2.85 GHz, 1 Msps, TX gain 33 dB, RX gain 38 dB, sps=4, RRC alpha=0.35).
  - Analyzed embedded Python framing, sliding window preamble correlation, XOR BER calculation, 4-quadrant decision-directed SNR estimation, Stack frame Qt GUI injection, and CSV logging.
  - Specified full DSP pipeline transition to QPSK (modulus-4 differential decoding, Gray mapping, 4th-order Costas loop, 2-bit symbol unpacker, CMA/LMS equalizer).
- **Unexplored areas**: None for survey milestone.

## Key Decisions Made
- Completed comprehensive 5-component survey and architectural handoff report in `handoff.md`.

## Artifact Index
- `c:/Users/prana/OneDrive/Desktop/hqam_stuf/.agents/survey_explorer_1/handoff.md` — Comprehensive Survey & Architecture Report
