# Original User Request

## 2026-08-18T12:09:20Z

Implement over-the-air (OTA) QPSK transmission and reception for Ettus USRP B210 SDRs in GNU Radio 3.10, featuring real-time synchronization, GUI tuning sliders for hardware impairments, live BER/SNR calculation, and an explicit step-by-step locking procedure.

Working directory: `c:/Users/prana/OneDrive/Desktop/hqam_stuf/miscellenious`
Integrity mode: development

## Reference Materials
- Official GNU Radio QPSK Simulation Tutorial: `miscellenious/Qpsk_modem.grc` (Reference URL: https://wiki.gnuradio.org/index.php?title=QPSK_Mod_and_Demod)
- Existing BPSK Hardware Transmitter: `miscellenious/tx_bpsk_hardware_ber.grc`
- Existing BPSK Hardware Receiver: `miscellenious/rx_bpsk_hardware_ber.grc`

## Requirements

### R1. QPSK Hardware Transmitter (`tx_qpsk_hardware_ber.grc`)
- Implement a frame generator transmitting a known preamble (QPSK Barker/sync sequence) and pseudo-random payload for bit error rate testing.
- Gray-coded QPSK symbol mapping with differential encoding to eliminate four-fold (90°) phase ambiguity.
- Root Raised Cosine (RRC) pulse shaping filter with configurable samples-per-symbol (SPS = 4) and roll-off factor ($\alpha = 0.35$).
- UHD USRP Sink configured for USRP B210 with parameterized carrier frequency, sample rate, and TX gain.

### R2. Tunable QPSK Hardware Receiver (`rx_qpsk_hardware_ber.grc`)
- Complete receiver DSP synchronization pipeline addressing hardware impairments:
  - **Power Normalization:** Automatic Gain Control (AGC) for dynamic range adjustment.
  - **Carrier Frequency Offset (CFO):** FLL Band-Edge filter for coarse frequency acquisition.
  - **Matched Filtering:** Root Raised Cosine (RRC) matched filter.
  - **Symbol Timing Recovery:** Symbol Synchronizer (e.g. Gardner / Mueller & Müller) with GUI slider for timing loop bandwidth.
  - **Carrier Phase & Fine Frequency Recovery:** 4th-order Costas Loop with GUI slider for phase loop bandwidth.
  - **Multipath Mitigation:** Adaptive Equalizer (CMA / LMS) with a GUI bypass/enable control and step-size ($\mu$) slider.
  - **Demapping & Differential Decoding:** Constellation Decoder $\to$ Differential Decoder (mod 4) $\to$ Gray Map $\to$ Bit Unpacker ($k=2$).
- Interactive QT GUI range sliders:
  - RF RX Gain (dB), AGC Rate, FLL Bandwidth, Timing Loop Bandwidth, Costas Phase Loop Bandwidth, Equalizer Gain/Bypass.
- Multi-trace Constellation Sink visualizing pre-sync, post-timing sync, and post-phase lock constellations, along with time and frequency sinks.

### R3. Embedded Real-Time BER & SNR Measurement Engine
- Embedded Python sync block in the receiver that performs:
  - Frame synchronization via correlation with the known QPSK preamble.
  - Cumulative and instantaneous Bit Error Rate (BER) computation against the reference payload.
  - Real-time SNR estimation computed from decision-directed symbol variance across four quadrants.
  - Live QT GUI overlay displaying Total Bits, Bit Errors, Instantaneous BER, and Estimated SNR (dB).
  - Timestamped CSV logging to `ber_qpsk_log.csv`.

### R4. Step-by-Step Hardware Tuning & Locking Protocol (`TUNING_GUIDE.md`)
- Provide a rigorous, sequential tuning guide explaining the exact order of slider adjustments (RF Gains $\to$ AGC $\to$ FLL Band Edge $\to$ Symbol Sync $\to$ Costas Loop $\to$ Equalizer).
- Provide visual constellation diagnostic signatures for each stage (e.g., amplitude circle $\to$ rotating ring $\to$ 4 rotating clusters $\to$ 4 locked stationary constellation points) and troubleshooting steps for common failure modes.

## Acceptance Criteria

### Flowgraph Integrity & Compilation
- [ ] `tx_qpsk_hardware_ber.grc` and `rx_qpsk_hardware_ber.grc` are syntactically valid GNU Radio 3.10 YAML flowgraphs.
- [ ] Both flowgraphs compile into Python scripts via `grcc` without syntax errors, missing variables, or port type mismatches.

### Synchronization & DSP Functionality
- [ ] Receiver flowgraph contains all necessary stages (AGC, FLL, RRC, Symbol Sync, 4th-order Costas Loop, Equalizer, Differential Decoder) properly interconnected.
- [ ] Sliders exist for all critical synchronization parameters and are functional in the QT GUI layout.

### Verification & Documentation
- [ ] Real-time BER and SNR calculation logic correctly accounts for 2-bits-per-symbol QPSK unpacking and frame correlation.
- [ ] `TUNING_GUIDE.md` provides unambiguous, step-by-step instructions for bringing up and locking the link over the air.
