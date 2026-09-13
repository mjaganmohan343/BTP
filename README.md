# BTP Project — Over-The-Air SDR Modulation Research
### **16-HexQAM (HQAM) vs. Square 16-QAM: Simulation, BER Analysis & Hardware Transceiver**

---

## 📋 Table of Contents

- [Project Overview](#-project-overview)
- [Repository Structure](#-repository-structure)
- [Modulation Schemes](#-modulation-schemes)
- [System Architecture](#-system-architecture)
- [Key Files & Scripts](#-key-files--scripts)
- [Hardware Setup](#-hardware-setup)
- [BER Performance Results](#-ber-performance-results)
- [📝 QPSK Text Transceiver (Over-the-Air)](#-qpsk-text-transceiver-over-the-air)
- [🔊 BPSK Audio Transceiver (Over-the-Air)](#-bpsk-audio-transceiver-over-the-air)
- [Test Infrastructure](#-test-infrastructure)
- [Hardware Tuning Guide (Quick Start)](#-hardware-tuning-guide-quick-start)
- [Running the Code](#-running-the-code)
- [Dependencies](#-dependencies)

---

## 🔬 Project Overview

This B.Tech Project investigates **Hexagonal QAM (HQAM)** as an alternative to conventional **Square 16-QAM** for wireless digital communications. The research covers:

1. **Theoretical BER analysis** — Closed-form BER curves for both 16-HexQAM and Square 16-QAM, derived from the Q-function and constellation geometry.
2. **GNU Radio simulation** — SDR flowgraphs (`16_HQAM.grc`, `QAM16.grc`) running modulation/demodulation chains with AWGN channels.
3. **Over-the-air QPSK hardware transceiver** — Real-time QPSK TX/RX using two Ettus USRP B210 boards with live BER & SNR monitoring.
4. **Over-the-air QPSK Text Transceiver** — Repeating custom text messages wirelessly over QPSK with framing, CRC32 integrity, PRBS whitening, and live Qt GUI display.
5. **Over-the-air BPSK Audio Transceiver** — Real-time audio (WAV file / microphone) transmitted wirelessly over BPSK using USRP B210 boards, with recovered audio saved as WAV.
6. **End-to-end test suite** — 65+ automated DSP verification test cases across a 4-tier hierarchy.

---

## 📁 Repository Structure

```
BTP_files/
│
├── README.md                           ← This file
├── .gitignore
│
└── BTP_related/
    │
    ├── golden values/                  ← Archived GRC flowgraphs (hardware iterations)
    │   ├── 915/
    │   │   └── rx_hardware.grc         ← 915 MHz RX prototype flowgraph
    │   ├── ber/
    │   │   ├── rx_hardware.grc         ← BER-measurement receiver
    │   │   ├── tx_hardware_ber.grc     ← BER-measurement transmitter
    │   │   └── ber with snr/           ← BER+SNR combined measurement iteration
    │   ├── bpsk/
    │   │   ├── rx_bpsk_hardware_ber.grc
    │   │   ├── tx_bpsk_hardware_ber.grc
    │   │   └── the best/               ← Best-performing BPSK configuration
    │   ├── no flip/                    ← No differential encoding variant
    │   │   ├── rx_hardware.grc / .py
    │   │   └── rx_hardware_epy_block_0.py
    │   └── qpsk_maybe/                 ← QPSK iteration history
    │       ├── rx_qpsk_hardware_ber.grc / .py
    │       ├── tx_qpsk_hardware_ber.grc / .py
    │       ├── rx_qpsk_repeating_text.grc / .py
    │       ├── tx_qpsk_repeating_text.grc / .py
    │       ├── ber_log_qpsk.csv        ← Historical BER measurements (1.3 MB)
    │       ├── rx_text_log.txt         ← Received text log (8.4 MB)
    │       └── slightly better/ ...    ← Sub-iterations
    │
    └── hqam_stuf/                      ← Main project directory
        │
        ├── PROJECT.md                  ← Architecture & feature inventory
        ├── TEST_INFRA.md               ← 4-tier test specification
        ├── TUNING_GUIDE.md             ← Hardware bring-up & tuning protocol
        │
        ├── ── SIMULATION FLOWGRAPHS ──
        ├── 16_HQAM.grc                 ← 16-HexQAM GNU Radio Companion flowgraph
        ├── HQAM16.py                   ← Auto-generated Python (16-HexQAM simulation)
        ├── QAM16.grc                   ← Square 16-QAM comparison flowgraph
        ├── TP5_1.py                    ← Additional simulation script
        │
        ├── ── BER ANALYSIS SCRIPTS ──
        ├── 16_Q_A_M.txt                ← BER data script: Square 16-QAM (theoretical + sim)
        ├── H_Q_A_M.txt                 ← BER data script: 16-HexQAM (theoretical + sim)
        ├── plot_comparison.py          ← BER comparison plot (HQAM vs 16-QAM)
        ├── ber_comparison.png          ← Output: BER vs Eb/N0 comparison chart
        ├── ber_bpsk_log.csv            ← BPSK hardware BER log
        ├── ber_log_qpsk.csv            ← QPSK simulation BER log
        ├── ber_qpsk_log.csv            ← QPSK hardware BER log
        │
        ├── ── GRC GENERATION SCRIPTS ──
        ├── generate.py                 ← Generates TX/RX hardware GRC files from YAML
        ├── generate_qpsk_reference.py  ← Generates QPSK reference/comparison flowgraphs
        ├── generate_rx.py              ← Generates the QPSK hardware RX flowgraph (909 lines)
        │
        ├── ── TEST SUITE ──
        ├── test_qpsk_ber_engine.py     ← 65-test automated DSP verification suite
        ├── test_m1_tx_adversarial_challenge.py ← Adversarial TX stress tests
        │
        ├── ── IQ DATA & SCATTER ──
        ├── IQ_HQAM/
        │   ├── 16_HQAM_Sactter_Plot.jpg
        │   ├── 2D_HexQAM_Mapping_20260607_193542.csv
        │   ├── Input_data_symbol_16_HQAM_20260607_193542.csv
        │   └── Received_IQ_data_16_HQAM_20260607_193542.csv
        │
        ├── hqam_approx.pdf             ← Research paper: HQAM approximation theory
        │
        ├── ── HARDWARE TRANSCEIVER ──
        └── hardware_test/              ← Production QPSK over-the-air hardware system
            ├── rx_hardware.grc / .py           ← QPSK receiver (full DSP sync chain)
            ├── rx_hardware_epy_block_0.py       ← RX embedded Python: frame detect
            ├── rx_hardware_epy_block_1.py       ← RX embedded Python: BER/SNR engine (5.6 KB)
            ├── tx_hardware.grc / .py            ← Basic QPSK transmitter
            ├── tx_hardware_ber.grc / .py        ← QPSK TX with frame generator (BER mode)
            ├── tx_hardware_ber_awgn.grc / .py   ← QPSK TX with AWGN channel emulation
            ├── tx_hardware_epy_block_0.py       ← TX frame generator (preamble + PRBS)
            ├── tx_hardware_epy_block_1.py       ← TX utility block
            ├── ber_log.csv                      ← Live hardware BER log
            ├── rx_bits.bin                      ← Raw captured RX bitstream (27 MB)
            ├── data_and_plots/
            │   ├── ber_log.csv                  ← Extended BER dataset (551 KB)
            │   ├── ber_plot.png                 ← BER curve plot
            │   ├── ber_snr_plot.png             ← BER vs SNR dual-axis plot
            │   └── rx_bits.bin                  ← Full RX capture (71 MB)
            └── media_and_reference/
                ├── constellation.mp4            ← Live constellation screen recording
                └── reference.txt                ← Reference notes
```

---

## 📡 Modulation Schemes

### 16-HexQAM (HQAM)

A **hexagonal lattice** QAM constellation with 16 points arranged to maximize minimum Euclidean distance for a given average power.

**Theoretical BER** (closed-form from `hqam_approx.pdf`):

$$P_s = A \cdot Q\!\left(\sqrt{\kappa \cdot E_s/N_0}\right) - B \cdot Q\!\left(\sqrt{\tfrac{10}{11}\kappa \cdot E_s/N_0}\right) \cdot Q\!\left(\sqrt{\tfrac{1}{3}\kappa \cdot E_s/N_0}\right)$$

$$\text{BER} = \frac{P_s}{\log_2 M}, \quad M=16,\ A=4.125,\ B=4.4948,\ \kappa=\frac{2}{9}$$

- **Quasi-Gray** symbol mapping (adjacent symbols differ by ≤ 1 bit)
- Simulated in `16_HQAM.grc` / `HQAM16.py`
- IQ scatter: `IQ_HQAM/16_HQAM_Sactter_Plot.jpg`

### Conventional Square 16-QAM

Standard rectangular 4×4 grid constellation with Gray coding.

**Theoretical BER**:

$$\text{BER} = \tfrac{3}{4}Q\!\left(\sqrt{\tfrac{4}{5}\tfrac{E_b}{N_0}}\right) + \tfrac{1}{2}Q\!\left(3\sqrt{\tfrac{4}{5}\tfrac{E_b}{N_0}}\right) - \tfrac{1}{4}Q\!\left(5\sqrt{\tfrac{4}{5}\tfrac{E_b}{N_0}}\right)$$

- Simulated in `QAM16.grc`
- BER data/scripts in `16_Q_A_M.txt`

### QPSK / BPSK Baseline

QPSK (4-QAM) is used for the **hardware over-the-air transceiver** due to its robustness under real channel impairments. BPSK serves as reference baseline.

- **Gray-coded** constellation points: $\{-0.707 \pm 0.707j,\ +0.707 \pm 0.707j\}$
- **Differential encoding** (modulo-4) to resolve 90° phase ambiguity

---

## 🏗️ System Architecture

### Over-The-Air QPSK Hardware Transceiver

```
┌──────────────────────────────── TRANSMITTER ────────────────────────────────┐
│                                                                              │
│  [Frame Generator]  ──► Preamble (32-bit sync) + PRBS payload (968 bits)   │
│         │                                                                    │
│  [QPSK Constellation Modulator]                                              │
│         │  Gray Map + Differential Encode + RRC Pulse Shaping (SPS=4, α=0.35)│
│         │                                                                    │
│  [UHD USRP Sink — B210]  ──► 2.85 GHz · 1.0 MSps · TX Gain slider         │
└──────────────────────────────────────────────────────────────────────────────┘
                      ║ Over-The-Air RF (2.85 GHz)
┌──────────────────────────────── RECEIVER ───────────────────────────────────┐
│                                                                              │
│  [UHD USRP Source — B210]  ◄── RX2 antenna · 1.0 MSps · RX Gain slider    │
│         │                                                                    │
│  [Analog AGC]  ──► Amplitude normalization → |z| ≈ 1.0                     │
│         │                                                                    │
│  [FLL Band-Edge Filter]  ──► Coarse CFO correction                          │
│         │                                                                    │
│  [RRC Matched Filter]  ──► α=0.35, 44 taps                                  │
│         │                                                                    │
│  [Symbol Synchronizer]  ──► Gardner/ML TED · 8-tap MMSE · SPS=4→1          │
│         │                                                                    │
│  [Adaptive CMA/LMS Equalizer]  ──► 15 taps · step-size slider               │
│         │                                                                    │
│  [4th-Order Costas Loop]  ──► Carrier phase lock + fine CFO                 │
│         │                                                                    │
│  [Decoder Chain]  ──► Constellation Decoder → Diff Decoder (mod 4)         │
│                        → Gray Inverse Map → Bit Unpacker (k=2)              │
│         │                                                                    │
│  [BER & SNR Engine]  ──► Frame sync · BER counter · DD-SNR estimator        │
│                           Live Qt GUI overlay · CSV logger (ber_log.csv)    │
└──────────────────────────────────────────────────────────────────────────────┘
```

**Hardware Impairment Countermeasures:**

| Impairment | Cause | DSP Countermeasure |
|---|---|---|
| Carrier Frequency Offset (CFO) | LO crystal ppm offset (~±10–30 kHz @ 2.85 GHz) | FLL Band-Edge + 4th-Order Costas Loop |
| Sampling Frequency Offset (SFO) | Master clock drift (30.72/61.44 MHz) | Symbol Synchronizer (MMSE TED) |
| 90° Phase Ambiguity | Costas Loop 4-fold symmetry | Differential Encoding/Decoding (mod 4) |
| Dynamic Range Variation | Path loss / antenna orientation | Analog AGC (reference = 1.0) |
| Inter-Symbol Interference (ISI) | Bandwidth limitation | Matched RRC Filter (α=0.35, 11×SPS taps) |
| DC Offset / LO Leakage | AD9361 direct-conversion RFIC | Hardware DC offset tracking + AGC |

---

## 📂 Key Files & Scripts

| File | Description |
|---|---|
| `16_HQAM.grc` | GNU Radio Companion flowgraph — 16-HexQAM simulation |
| `HQAM16.py` | Auto-generated Python — 16-HexQAM simulation (GRC export) |
| `QAM16.grc` | GNU Radio Companion flowgraph — Square 16-QAM simulation |
| `plot_comparison.py` | Plots BER vs Eb/N0 for both schemes → `ber_comparison.png` |
| `16_Q_A_M.txt` | Square 16-QAM BER data + theoretical curve (runnable Python) |
| `H_Q_A_M.txt` | 16-HexQAM BER data + theoretical curve (runnable Python) |
| `generate.py` | Programmatically generates TX/RX hardware GRC flowgraphs from YAML |
| `generate_rx.py` | Generates the full QPSK hardware receiver GRC flowgraph (909 lines) |
| `generate_qpsk_reference.py` | Generates QPSK reference comparison flowgraphs |
| `hardware_test/tx_hardware_ber.grc` | **Production TX** — QPSK transmitter with PRBS frame generator |
| `hardware_test/rx_hardware.grc` | **Production RX** — Full DSP sync chain + BER/SNR measurement |
| `hardware_test/rx_hardware_epy_block_1.py` | Embedded Python: dual-port BER/SNR + Qt GUI overlay + CSV logger |
| `hardware_test/tx_hardware_epy_block_0.py` | Embedded Python: TX frame generator (preamble + PRBS-42) |
| `test_qpsk_ber_engine.py` | **65-test** automated 4-tier DSP verification suite |
| `test_m1_tx_adversarial_challenge.py` | Adversarial TX stress tests (milestone M1) |
| `ber_comparison.png` | BER comparison chart (HQAM vs Square 16-QAM) |
| `hqam_approx.pdf` | Reference paper: HQAM closed-form BER approximation |
| `PROJECT.md` | Full architecture, feature inventory & milestone status |
| `TEST_INFRA.md` | Complete 4-tier test specification & test catalog |
| `TUNING_GUIDE.md` | Step-by-step hardware bring-up & slider tuning protocol |

---

## 🔧 Hardware Setup

### Equipment

| Component | Specification |
|---|---|
| SDR Boards | 2× Ettus USRP B210 (connected via USB 3.0) |
| RF Frontend | AD9361 RFIC (direct-conversion homodyne) |
| Center Frequency | 2.85 GHz |
| Sample Rate | 1.0 MSps |
| TX Gain | 30–45 dB (slider-adjustable in GRC) |
| RX Gain | 38 dB default (slider-adjustable in GRC) |
| Antenna Port | RX2 (receiver) |
| Host OS | Windows (Radioconda environment) |

### Interface Contracts

**TX Frame Format** (1000 bits = 125 bytes packed MSB-first):
```
Frame = [Preamble (32 bits)] + [PRBS Payload (968 bits, numpy seed=42)]
```

**Sync Word (32 bits):**
```
[1,1,1,1,1,0,0,1,1,0,1,0,1,1,1,1,1,1,0,0,1,1,0,1,0,1,1,0,0,1,0,1]
```

**BER/SNR Engine Input Ports:**
- Port 0 (`in_bits`): `uint8` unpacked bits from `Bit Unpacker (k=2)`
- Port 1 (`in_iq`): `complex64` post-Costas IQ samples (1 SPS)

**CSV Log Format** (`ber_log.csv`):
```csv
timestamp,frame,total_bits,bit_errors,ber,snr_db
1234.567,42,100000,0,0.0000e+00,22.35
```

---

## 📊 BER Performance Results

BER vs $E_b/N_0$ comparison across 0–20 dB for both modulation schemes:

| Eb/N0 (dB) | BER — Square 16-QAM (sim) | BER — 16-HexQAM (sim) |
|:---:|:---:|:---:|
| 0.00 | 1.42 × 10⁻¹ | 1.52 × 10⁻¹ |
| 6.02 | 2.82 × 10⁻² | 3.05 × 10⁻² |
| 9.90 | 2.04 × 10⁻³ | 1.65 × 10⁻³ |
| 13.15 | 2.00 × 10⁻⁵ | 1.02 × 10⁻⁵ |
| 17.08 | 6.19 × 10⁻¹¹ | 8.42 × 10⁻¹² |
| 18.42 | 3.33 × 10⁻¹⁴ | 2.11 × 10⁻¹⁵ |

> **Key finding:** 16-HexQAM demonstrates a power efficiency advantage (~0.5–1 dB SNR gain) over Square 16-QAM at mid-to-high SNR, consistent with hexagonal lattice packing theory.

Regenerate the chart:
```bash
python BTP_related/hqam_stuf/plot_comparison.py
# Output: BTP_related/hqam_stuf/ber_comparison.png
```

---

## 📝 QPSK Text Transceiver (Over-the-Air)

Beyond raw BER measurements, the project implemented a complete **over-the-air text messaging system** over QPSK using the same USRP B210 hardware. This demonstrates real-world application-layer data transfer on top of the physical-layer DSP chain.

### What It Does

- The **transmitter** continuously encodes a user-defined text message into structured packets and modulates them over QPSK at 2.85 GHz.
- The **receiver** demodulates the QPSK signal, deframes the packets, verifies data integrity, and displays decoded messages live in the GNU Radio Qt GUI.
- A **timestamped log file** (`rx_text_log.txt`) records every received packet with sequence number and reception time.

### Packet Format

```
┌────────────────────────────────────────────────────────────────────┐
│  Preamble (32 QPSK symbols)                                        │
│  Header (7 bytes, whitened):                                       │
│    Magic (2B: 0x5AA5) | Type (1B: 0x01) | Seq# (2B) | Len (2B)   │
│  Payload (N bytes, whitened): UTF-8 text + "[Pkt #XXXXX]" suffix  │
│  CRC32 (4 bytes, whitened): integrity check over Header+Payload    │
└────────────────────────────────────────────────────────────────────┘
```

### Key Features

| Feature | Detail |
|---|---|
| **Framing** | 32-symbol preamble with Hamming distance tolerance (≤2 errors) |
| **Data Integrity** | CRC32 over unwhitened Header + Payload; mismatch logged as CRC error |
| **PRBS Whitening** | XOR with 2048-byte keystream (seed=42) to suppress repetitive ASCII spectral tones |
| **Sequence Numbers** | 16-bit wrap-around counter per packet for ordering & loss detection |
| **Live Qt GUI** | Color-coded status overlay: packet count, CRC error rate, last seq#, scrolling decoded text |
| **Log File** | Appending `rx_text_log.txt` with timestamped entries |

### Files

| File | Description |
|---|---|
| `miscellenious/tx_qpsk_repeating_text.grc` | **TX flowgraph** — QPSK text transmitter (GRC) |
| `miscellenious/tx_qpsk_repeating_text.py` | Auto-generated Python TX |
| `miscellenious/tx_qpsk_repeating_text_epy_block_0.py` | Embedded TX block: packet builder (preamble + whitened header + CRC32) |
| `miscellenious/rx_qpsk_repeating_text.grc` | **RX flowgraph** — QPSK text receiver (GRC) |
| `miscellenious/rx_qpsk_repeating_text.py` | Auto-generated Python RX |
| `miscellenious/rx_qpsk_repeating_text_epy_block_1.py` | Embedded RX block: deframer + CRC verifier + Qt GUI + logger |
| `miscellenious/rx_text_log.txt` | Captured received text session log (8.4 MB) |
| `golden values/qpsk_maybe/the ultimate/text transfer/` | Archived iterations of the text TX/RX system |

### Pipeline

```
TX: [Text Message] → [Packet Builder: Preamble+Header+Whitened Payload+CRC32]
    → [QPSK Constellation Modulator + RRC Pulse Shaping]
    → [USRP B210 @ 2.85 GHz]

RX: [USRP B210 @ 2.85 GHz]
    → [AGC → FLL → RRC → Symbol Sync → Costas Loop → Decoder]
    → [Text Packet Deframer: preamble detect → descramble → CRC32 verify]
    → [Qt GUI live display + rx_text_log.txt]
```

---

## 🔊 BPSK Audio Transceiver (Over-the-Air)

The project also implemented a **real-time over-the-air audio link** using BPSK modulation on USRP B210 SDRs. This demonstrates voice/audio transmission over SDR hardware — a classic SDR application.

### What It Does

- The **transmitter** reads audio from a WAV file (`voice-telephony-8khz.wav`) at 8 kHz sample rate, digitizes it, and modulates it over BPSK at the configured center frequency.
- The **receiver** demodulates the BPSK signal and recovers the audio stream, saving it as `rx_recovered_audio.wav`.

### Key Parameters

| Parameter | Value |
|---|---|
| Modulation | BPSK (Binary Phase Shift Keying) |
| Audio Sample Rate | 8 kHz (telephony quality) |
| SDR Hardware | Ettus USRP B210 (TX) + USRP B210 (RX) |
| TX Audio Source | `voice-telephony-8khz.wav` |
| RX Audio Output | `rx_recovered_audio.wav` |

### Files

| File | Description |
|---|---|
| `golden values/bpsk/the best/bpsk audio/tx_bpsk_hardware_audio.grc` | **TX flowgraph** — BPSK audio transmitter (GRC) |
| `golden values/bpsk/the best/bpsk audio/rx_bpsk_hardware_audio.grc` | **RX flowgraph** — BPSK audio receiver (GRC) |
| `golden values/bpsk/the best/bpsk audio/voice-telephony-8khz.wav` | Input audio file transmitted over the air (8 kHz, ~421 KB) |
| `golden values/bpsk/the best/bpsk audio/rx_recovered_audio.wav` | Recovered/demodulated audio captured at the receiver (~578 KB) |

### Pipeline

```
TX: [WAV File Source: voice-telephony-8khz.wav @ 8 kHz]
    → [Audio → Bits conversion]
    → [BPSK Constellation Modulator + RRC Pulse Shaping]
    → [USRP B210 TX]

                ║ Over-The-Air RF

RX: [USRP B210 RX]
    → [AGC → FLL → Matched Filter → Symbol Sync → BPSK Costas Loop]
    → [BPSK Demodulator]
    → [WAV File Sink: rx_recovered_audio.wav @ 8 kHz]
```

> The recovered audio file `rx_recovered_audio.wav` demonstrates successful audio reconstruction after over-the-air BPSK transmission using USRP B210 hardware.

---

## 🧪 Test Infrastructure


The automated test suite (`test_qpsk_ber_engine.py`) covers **65+ test cases** across 4 tiers:

| Tier | Scope | Coverage |
|---|---|---|
| **Tier 1** | Unit & Feature Coverage | Frame generation, QPSK constellation, preamble correlation, BER counter (0%/1%/5%/50%), DD-SNR estimator (5–25 dB), rotational invariance, CSV logger |
| **Tier 2** | Boundary & Stress Cases | Empty buffers, single-byte streaming, preamble Hamming threshold, extreme SNR (−10 to +60 dB), 1M+ bit memory stress |
| **Tier 3** | Cross-Feature Integration | E2E TX→AWGN→RX pipeline, theoretical BER waterfall curve, 90° phase slip recovery, burst noise re-acquisition |
| **Tier 4** | Real-World Hardware Emulation | USRP B210 CFO+SFO+AWGN impairments, Rayleigh/Rician fading, dynamic SNR step profile, 100+ frame long-duration stability |

**Run the full test suite (Radioconda):**
```powershell
C:\Users\<user>\radioconda\python.exe .\BTP_related\hqam_stuf\test_qpsk_ber_engine.py
```

**Expected:** ≥ 40 test cases · 100% pass rate · < 15 seconds execution time

---

## ⚙️ Hardware Tuning Guide (Quick Start)

Tune the GRC sliders in this **exact sequential order** for fastest lock:

```
Step 1: RF Gains       → TX: 30–45 dB  |  RX: 38 dB (adjust so carrier is 20–35 dB above noise floor)
Step 2: AGC Verify     → Raw RX constellation radius ≈ 1.0
Step 3: FLL BW         → Start 0.020; increase to 0.040 if large CFO; settle at 0.010–0.020
Step 4: Symbol Sync BW → Start 0.030; increase to 0.050 until ring sharpens; lower to 0.020–0.030
Step 5: Costas Loop BW → Start 0.0628; increase to 0.080–0.120 until rotation stops; lower to 0.030–0.050
Step 6: Verify BER     → Qt GUI overlay turns Dark Green | ber_log.csv logs live data
```

**Constellation Diagnostic Reference:**

| What you see | State | Action |
|---|---|---|
| Diffuse uniform cloud | No signal / RX saturated | Adjust RX Gain; carrier must be 20 dB above noise |
| Thin rotating ring (red trace) | Timing locked, carrier phase unlocked | Increase Costas Loop BW |
| 4 spinning blobs / pinwheel (blue trace) | Residual frequency offset | Increase FLL BW to 0.03–0.05 |
| **4 sharp stationary dots at ±0.707±0.707j** | **✅ Full lock achieved** | Lower Costas BW to tighten clusters; BER → 0 |
| Ellipse / skewed axes | IQ quadrature imbalance | Normal on B210; differential decoding tolerates ≤15° |

> Full guide with troubleshooting matrix: `TUNING_GUIDE.md`

---

## 🚀 Running the Code

### 1. BER Comparison Plot (no hardware needed)

```bash
python BTP_related/hqam_stuf/plot_comparison.py
# Output → BTP_related/hqam_stuf/ber_comparison.png
```

### 2. 16-HexQAM Simulation (GNU Radio)

Open `BTP_related/hqam_stuf/16_HQAM.grc` in **GNU Radio Companion** and press ▶ Run, or:

```bash
python BTP_related/hqam_stuf/HQAM16.py
```

### 3. Square 16-QAM Simulation (GNU Radio)

```
Open: BTP_related/hqam_stuf/QAM16.grc in GNU Radio Companion
```

### 4. Hardware QPSK Transceiver — BER Mode (2× USRP B210 required)

**Transmitter terminal:**
```bash
python BTP_related/hqam_stuf/hardware_test/tx_hardware_ber.py
# or open tx_hardware_ber.grc in GRC and run
```

**Receiver terminal:**
```bash
python BTP_related/hqam_stuf/hardware_test/rx_hardware.py
# or open rx_hardware.grc in GRC and run
```

### 5. QPSK Text Transceiver (2× USRP B210 required)

Send a repeating text message wirelessly over QPSK.

**Transmitter terminal:**
```bash
# Open in GNU Radio Companion and run:
# BTP_related/hqam_stuf/miscellenious/tx_qpsk_repeating_text.grc
# or run the Python directly:
python "BTP_related/hqam_stuf/miscellenious/tx_qpsk_repeating_text.py"
```

**Receiver terminal:**
```bash
# Open in GNU Radio Companion and run:
# BTP_related/hqam_stuf/miscellenious/rx_qpsk_repeating_text.grc
# or run the Python directly:
python "BTP_related/hqam_stuf/miscellenious/rx_qpsk_repeating_text.py"
# Decoded messages appear in Qt GUI and are logged to rx_text_log.txt
```

### 6. BPSK Audio Transceiver (2× USRP B210 required)

Transmit a WAV audio file wirelessly over BPSK and recover it at the receiver.

**Transmitter terminal:**
```bash
# Open in GNU Radio Companion and run:
# BTP_related/golden values/bpsk/the best/bpsk audio/tx_bpsk_hardware_audio.grc
# Plays voice-telephony-8khz.wav over the air via BPSK
```

**Receiver terminal:**
```bash
# Open in GNU Radio Companion and run:
# BTP_related/golden values/bpsk/the best/bpsk audio/rx_bpsk_hardware_audio.grc
# Recovered audio saved to: rx_recovered_audio.wav
```

### 7. Automated DSP Test Suite

```powershell
# Windows (Radioconda)
C:\Users\<user>\radioconda\python.exe .\BTP_related\hqam_stuf\test_qpsk_ber_engine.py

# Linux/Mac (Radioconda or system GR Python)
python BTP_related/hqam_stuf/test_qpsk_ber_engine.py
```

### 8. Regenerate GRC Flowgraphs Programmatically

```bash
python BTP_related/hqam_stuf/generate.py           # TX + RX hardware GRC
python BTP_related/hqam_stuf/generate_rx.py        # QPSK hardware receiver GRC
python BTP_related/hqam_stuf/generate_qpsk_reference.py  # QPSK reference flowgraphs
```

### 9. Individual BER Curve Scripts

```bash
python BTP_related/hqam_stuf/16_Q_A_M.txt   # Square 16-QAM BER plot
python BTP_related/hqam_stuf/H_Q_A_M.txt    # 16-HexQAM BER plot
```


---

## 📦 Dependencies

| Package | Version / Notes |
|---|---|
| **GNU Radio** | 3.10.12.0 |
| **Python** | 3.12 (Radioconda recommended) |
| **PyQt5** | Qt GUI for flowgraph sinks & interactive sliders |
| **NumPy** | Array math, PRBS generation, DSP |
| **SciPy** | `erfc` for Q-function in BER analysis scripts |
| **Matplotlib** | BER curve plotting & scatter plots |
| **UHD / gr-uhd** | Ettus USRP B210 driver & GNU Radio USRP sink/source |
| **PyYAML** | Parsing/generating GRC flowgraph YAML files |

**Install via Radioconda (recommended for Windows):**
```bash
conda install -c conda-forge gnuradio uhd
pip install pyyaml
```

---

## 📝 Notes

- All `.grc` files require **GNU Radio Companion (GRC) 3.10.x** to open and run.
- The `golden values/` directory contains **archived experimental iterations** used during development — not for production use.
- `rx_bits.bin` files are raw binary captures of received bits (up to 71 MB) stored for offline post-processing and BER analysis.
- `hardware_test/media_and_reference/constellation.mp4` is a screen recording of a live QPSK constellation diagram during an over-the-air transmission session.
- Hardware tests require both USRP B210 boards plugged into **native USB 3.0 ports** (blue ports) to avoid underflow/overflow errors.

---

*For full architecture details → [`PROJECT.md`](BTP_related/hqam_stuf/PROJECT.md)*  
*For test specification → [`TEST_INFRA.md`](BTP_related/hqam_stuf/TEST_INFRA.md)*  
*For hardware tuning → [`TUNING_GUIDE.md`](BTP_related/hqam_stuf/TUNING_GUIDE.md)*
