## 2026-08-18T12:10:21Z
You are survey_spec_miner_1.
Your working directory: c:/Users/prana/OneDrive/Desktop/hqam_stuf/.agents/survey_spec_miner_1
Project root: c:/Users/prana/OneDrive/Desktop/hqam_stuf
Flowgraph directory: c:/Users/prana/OneDrive/Desktop/hqam_stuf/miscellenious

Authoritative User Request: c:/Users/prana/OneDrive/Desktop/hqam_stuf/.agents/ORIGINAL_REQUEST.md

Task:
Thoroughly inspect the reference QPSK simulation and hardware flowgraphs in c:/Users/prana/OneDrive/Desktop/hqam_stuf/miscellenious/:
1. Qpsk_modem.grc
2. 	x_qpsk_hardware.grc
3. 
x_qpsk_hardware.grc

Analyze and extract exact specifications for GNU Radio 3.10 QPSK implementation:
- Constellation Object configuration (constellation type, symbol points, Gray map, pre_diff_code/encoding).
- Differential Encoder / Decoder parameters (modulus = 4 for QPSK).
- Symbol Synchronizer parameters (timing error detector e.g. Gardner / Mueller & Müller, damping factor, loop bandwidth, interpolation filter, samples per symbol = 4).
- 4th-order Costas Loop parameters (loop bandwidth, order = 4).
- FLL Band-Edge parameters (samples per symbol = 4, rolloff = 0.35, filter size = 45, bandwidth).
- Adaptive Equalizer (CMA / LMS) parameters (num taps, modulus, step size mu, bypass/enable logic).
- Root Raised Cosine (RRC) filter taps and parameters (gain, sample_rate, symbol_rate, alpha=0.35, ntaps).
- QT GUI slider definitions, ranges, step sizes, and default values.

Write your findings to c:/Users/prana/OneDrive/Desktop/hqam_stuf/.agents/survey_spec_miner_1/handoff.md and send a message back with your summary.
