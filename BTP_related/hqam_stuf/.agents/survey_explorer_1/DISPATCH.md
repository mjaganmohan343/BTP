## 2026-08-18T12:10:21Z
<USER_REQUEST>
You are survey_explorer_1.
Your working directory: c:/Users/prana/OneDrive/Desktop/hqam_stuf/.agents/survey_explorer_1
Project root: c:/Users/prana/OneDrive/Desktop/hqam_stuf
Flowgraph directory: c:/Users/prana/OneDrive/Desktop/hqam_stuf/miscellenious

Authoritative User Request: c:/Users/prana/OneDrive/Desktop/hqam_stuf/.agents/ORIGINAL_REQUEST.md

Task:
Thoroughly inspect the existing reference hardware flowgraphs in `c:/Users/prana/OneDrive/Desktop/hqam_stuf/miscellenious/`:
1. `tx_bpsk_hardware_ber.grc` and `tx_bpsk_hardware_ber_epy_block_0.py`
2. `rx_bpsk_hardware_ber.grc`
3. Any other generated python files or scripts.

Analyze and document:
- The exact structure of the BPSK hardware transmitter and receiver (UHD device arguments, sample rates, center frequency, gain variables, filter taps, framing/preamble generation).
- How the embedded python blocks work (framing, preamble, BER calculation, CSV logging, QT GUI display).
- How GNU Radio 3.10 GRC files are formatted (YAML format, blocks, connections, variables, GUI hints).
- How to transition from BPSK (1 bit/sym) to QPSK (2 bits/sym, differential encoding, Gray coding, 4th order Costas loop, constellation points).

Write your comprehensive findings to `c:/Users/prana/OneDrive/Desktop/hqam_stuf/.agents/survey_explorer_1/handoff.md` and send a message back with your summary.
</USER_REQUEST>
