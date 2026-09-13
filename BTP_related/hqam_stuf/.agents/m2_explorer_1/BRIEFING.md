# BRIEFING — 2026-08-18T12:39:00Z

## Mission
Design the complete GNU Radio 3.10 YAML flowgraph blueprint for `miscellenious/rx_qpsk_hardware_ber.grc` and the embedded Python block `miscellenious/rx_qpsk_hardware_ber_epy_block_1.py`.

## 🔒 My Identity
- Archetype: Teamwork explorer
- Roles: Read-only investigation, analysis, synthesis, blueprint generation
- Working directory: c:/Users/prana/OneDrive/Desktop/hqam_stuf/.agents/m2_explorer_1
- Original parent: 5ec8b7d3-ea92-47e6-aed4-ec20f5b6f567
- Milestone: M2 - QPSK Hardware BER Flowgraph & Engine Design

## 🔒 Key Constraints
- Read-only investigation — do NOT implement directly in source repository yet; write blueprints to handoff report
- Accurate GNU Radio 3.10 YAML schema compliance
- Correct QPSK differential mapping and bit demapping: `digital_constellation_decoder_cb` -> `digital_diff_decoder_bb (modulus=4)` -> `digital_map_bb ([0, 1, 3, 2])` -> `blocks_unpack_k_bits_bb (k=2)`
- Correct synchronization parameters, CMA/LMS equalizer with bypass selector, 4th-order Costas loop
- Embedded Python sync_block with 2 input ports (unpacked bits and phase-locked complex symbols), sliding window correlation for 32-bit sync word, PRBS-42 payload BER, decision-directed 4-quadrant SNR estimation with EMA, live Qt GUI status overlay, CSV logging

## Current Parent
- Conversation ID: 5ec8b7d3-ea92-47e6-aed4-ec20f5b6f567
- Updated: 2026-08-18T12:39:00Z

## Investigation State
- **Explored paths**: [TBD]
- **Key findings**: [TBD]
- **Unexplored areas**: Reference GRC files (`rx_bpsk_hardware_ber.grc`, `rx_qpsk_hardware.grc`, `Qpsk_modem.grc`, existing epy blocks, and project docs)

## Key Decisions Made
- Initializing structured investigation into reference flowgraphs and Python blocks.

## Artifact Index
- DISPATCH.md — Dispatch log
- BRIEFING.md — Persistent working memory
- progress.md — Heartbeat progress log
- handoff.md — Final 5-component handoff report containing complete blueprints
