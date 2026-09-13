# Test Infrastructure & Verification Specification
## Over-The-Air QPSK Hardware Transceiver with Real-Time BER & SNR Monitoring

### Document Version: 1.0.0
### Date: 2026-08-18
### Environment: Radioconda Python 3.12 / GNU Radio 3.10.12.0 (Windows)

---

## 1. Overview & Testing Philosophy

This test infrastructure defines the verification framework for the Over-The-Air (OTA) QPSK Hardware Transceiver implemented in GNU Radio 3.10 and Ettus USRP B210 SDRs. 

The test strategy employs a **4-Tier Hierarchical Testing Methodology**:
- **Tier 1: Unit & Feature Coverage** — Exhaustive deterministic verification ($\ge 5$ test cases per feature) of all mathematical, DSP, bit-level, and logging primitives.
- **Tier 2: Boundary, Edge, and Stress Cases** — Extreme values, degenerate inputs, buffer boundaries, non-ideal phase jitter, corrupted preambles, and memory stress ($\ge 5$ test cases per feature).
- **Tier 3: Cross-Feature Integration Combinations** — Multi-block end-to-end processing pipelines, theoretical BER waterfall validation vs. AWGN, dynamic phase slips, frame recovery after noise bursts, and live CSV logger integration.
- **Tier 4: Real-World Hardware & Environmental Scenarios** — Emulation of physical hardware impairments (USRP B210 Carrier Frequency Offset, Sample Frequency Offset / clock drift, multipath Rayleigh/Rician fading channels, dynamic SNR step profiles, and 100+ continuous frame tracking).

---

## 2. 4-Tier Test Matrix & Specifications

```
+-----------------------------------------------------------------------------------------+
|                                    4-TIER TEST ARCHITECTURE                             |
+-----------------------------------------------------------------------------------------+
|  Tier 1: Feature Coverage (>=5/feature)                                                 |
|    * Frame Gen & Byte Packing (1.1-1.5)        * Constellation & Modulator (2.1-2.5)   |
|    * Demapping & Diff Decoding (3.1-3.5)       * Preamble Correlation & Lock (4.1-4.5)  |
|    * Bit Error Rate Engine (5.1-5.5)           * 4-Quadrant SNR Estimator (6.1-6.5)    |
|    * Rotational Invariance (7.1-7.5)           * CSV Logger & Formatting (8.1-8.5)     |
|    * GRC Flowgraph Compilation (9.1-9.5)                                                |
+-----------------------------------------------------------------------------------------+
|  Tier 2: Boundary & Corner Cases (>=5/feature)                                          |
|    * Buffer Boundaries & Zero-Length Items     * Single-Byte/Sample Fragmentation       |
|    * Preamble Hamming Threshold Transitions    * Arbitrary Bit Alignment Offsets (0-999)|
|    * Extreme SNR Ranges (-10 dB to +40 dB)     * Phase Jitter Tolerance (5-30 deg)      |
|    * High Throughput Stress (1M+ bits)         * CSV Path & IO Resilience               |
+-----------------------------------------------------------------------------------------+
|  Tier 3: Cross-Feature Combinations                                                     |
|    * End-to-End TX -> Channel -> RX Chain      * Theoretical Waterfall BER Curve (AWGN) |
|    * Dynamic Phase Slip (90 deg) Recovery      * Burst Noise Frame Re-acquisition       |
|    * Multi-Frame Cumulative State Tracking     * Live CSV Log Stream Integrity          |
+-----------------------------------------------------------------------------------------+
|  Tier 4: Real-World Application Scenarios                                               |
|    * USRP B210 Impairment Emulation (CFO + SFO + Phase Drift + AWGN)                    |
|    * Multipath Rayleigh/Rician Fading Channel  * Dynamic SNR Step Profile Tracking      |
|    * 100+ Frame Long-Duration Stability        * Intermittent Burst Frame Alignment     |
+-----------------------------------------------------------------------------------------+
```

---

## 3. Detailed Test Catalog

### Tier 1: Unit & Feature Coverage

#### Feature 1: Frame Generation & Byte Packing
- **T1.1.1 Frame Length & Preamble Structure**: Verify transmitted frame is exactly 1000 bits starting with 32-bit sync sequence `[1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1]`.
- **T1.1.2 Deterministic PRBS Payload**: Verify 968 payload bits generated with `numpy.random.seed(42)` match authoritative PRBS sequence.
- **T1.1.3 Byte Packing (MSB-First)**: Verify 1000 bits are packed into exactly 125 bytes using MSB-first packing `byte[i] = sum(bit[8*i + b] << (7-b))`.
- **T1.1.4 Cyclic Stream Continuity**: Verify continuous stream generation wraps pointer at frame boundaries without bit loss or insertion.
- **T1.1.5 Bit Unpacking Roundtrip Invariance**: Verify unpacked bitstream from packed bytes is bit-identical to the original 1000-bit frame.

#### Feature 2: Constellation Mapping & Modulation
- **T1.2.1 Normalized Symbol Energies**: Verify 4 constellation points `[-0.707-0.707j, 0.707-0.707j, 0.707+0.707j, -0.707+0.707j]` have unit average power $\mathbb{E}[|s|^2] \approx 1.0$.
- **T1.2.2 Gray Code Mapping**: Verify mapping table `[0, 1, 3, 2]` maps adjacent constellation points with Hamming distance 1.
- **T1.2.3 4-Fold 90-Degree Rotational Symmetry**: Verify rotating constellation points by $\pi/2$ maps points cyclically $k \to (k+1) \pmod 4$.
- **T1.2.4 Decision Boundaries**: Verify 4-quadrant slicer partitions complex plane at $\text{Re}(z)=0$ and $\text{Im}(z)=0$.
- **T1.2.5 Differential Modulation State Transition**: Verify transmitter differential encoder computes $s_k = (s_{k-1} + g_k) \pmod 4$.

#### Feature 3: Demapping & Differential Decoding
- **T1.3.1 Euclidean Slicer Precision**: Verify noiseless QPSK symbols slice to exact quadrant indices $\{0, 1, 2, 3\}$.
- **T1.3.2 Modulo-4 Differential Decoding**: Verify differential decoder computes $d_k = (r_k - r_{k-1}) \pmod 4$.
- **T1.3.3 Gray Inverse Mapping**: Verify mapped symbol values convert correctly via table `[0, 1, 3, 2]`.
- **T1.3.4 2-Bit Unpacking**: Verify 2 bits unpacked per symbol byte match $(d \gg 1) \& 1$ and $d \& 1$.
- **T1.3.5 Noiseless End-to-End Roundtrip**: Verify total bits demodulated in noiseless channel achieve $\text{BER} = 0.00000$.

#### Feature 4: Preamble Correlation & Frame Lock
- **T1.4.1 Cross-Correlation Peak**: Verify sliding cross-correlation of bitstream with 32-bit preamble yields unambiguous peak at frame offset 0.
- **T1.4.2 Hamming Distance Metric**: Verify exact Hamming distance calculation across 32 bits.
- **T1.4.3 Zero-Error Preamble Detection**: Verify frame lock triggers when $\text{Hamming Distance} = 0$.
- **T1.4.4 1-Bit Error Tolerance**: Verify frame lock triggers when $\text{Hamming Distance} = 1 \le \text{Threshold}$.
- **T1.4.5 2-Bit Error Tolerance**: Verify frame lock triggers when $\text{Hamming Distance} = 2 \le \text{Threshold} (2)$.

#### Feature 5: Real-Time Bit Error Rate (BER) Calculation
- **T1.5.1 Injected 0% BER**: Verify measured $\text{BER} = 0.00000$ when no errors are injected into payload.
- **T1.5.2 Injected 1% BER**: Verify measured $\text{BER} \approx 0.01033$ when 10 bit errors are injected into 968 payload bits.
- **T1.5.3 Injected 5% BER**: Verify measured $\text{BER} \approx 0.04959$ when 48 bit errors are injected into 968 payload bits.
- **T1.5.4 Injected 50% BER**: Verify measured $\text{BER} \approx 0.50000$ on completely random uncorrelated bits.
- **T1.5.5 Monotonic Accumulator**: Verify cumulative total bits and cumulative bit errors increase monotonically across successive frames.

#### Feature 6: Decision-Directed 4-Quadrant SNR Estimator
- **T1.6.1 SNR Estimation at 5 dB AWGN**: Verify decision-directed SNR estimate is within $\pm 0.5$ dB of 5.0 dB.
- **T1.6.2 SNR Estimation at 10 dB AWGN**: Verify decision-directed SNR estimate is within $\pm 0.5$ dB of 10.0 dB.
- **T1.6.3 SNR Estimation at 15 dB AWGN**: Verify decision-directed SNR estimate is within $\pm 0.5$ dB of 15.0 dB.
- **T1.6.4 SNR Estimation at 20 dB AWGN**: Verify decision-directed SNR estimate is within $\pm 0.5$ dB of 20.0 dB.
- **T1.6.5 SNR Estimation at 25 dB AWGN**: Verify decision-directed SNR estimate is within $\pm 0.5$ dB of 25.0 dB.

#### Feature 7: Rotational Invariance under Carrier Phase Ambiguity
- **T1.7.1 0-Degree Phase Lock**: Verify steady-state $\text{BER} = 0.00000$ with $0^\circ$ carrier phase shift.
- **T1.7.2 90-Degree Phase Lock**: Verify steady-state $\text{BER} = 0.00000$ with $+90^\circ$ carrier phase shift.
- **T1.7.3 180-Degree Phase Lock**: Verify steady-state $\text{BER} = 0.00000$ with $+180^\circ$ carrier phase shift.
- **T1.7.4 270-Degree Phase Lock**: Verify steady-state $\text{BER} = 0.00000$ with $+270^\circ$ carrier phase shift.
- **T1.7.5 Dynamic Phase Jumps**: Verify differential decoder recovers 0 BER within 1 symbol after a $90^\circ$ phase jump.

#### Feature 8: CSV Logging Engine & Formatting
- **T1.8.1 Header Schema Validation**: Verify CSV header matches `timestamp,frame,total_bits,bit_errors,ber,snr_db`.
- **T1.8.2 Row Format & Precision**: Verify row matches `%.3f,%d,%d,%d,%.4e,%.2f`.
- **T1.8.3 Timestamp Monotonicity**: Verify timestamps are strictly increasing.
- **T1.8.4 Multi-Chunk Persistence**: Verify log entries append without truncating previous records.
- **T1.8.5 CSV Parser Roundtrip**: Verify standard Python `csv.reader` correctly parses all columns and numeric types.

#### Feature 9: Flowgraph Compilation Validation (`grcc`)
- **T1.9.1 Compilation of `Qpsk_modem.grc`**: Verify exit code 0 and valid Python script output.
- **T1.9.2 Compilation of `tx_qpsk_hardware.grc`**: Verify exit code 0.
- **T1.9.3 Compilation of `rx_qpsk_hardware.grc`**: Verify exit code 0.
- **T1.9.4 Compilation of `tx_bpsk_hardware_ber.grc`**: Verify exit code 0.
- **T1.9.5 Compilation of Target Hardware Flowgraphs**: Verify compilation of all hardware GRC flowgraphs in `miscellenious/`.

---

### Tier 2: Boundary, Edge, and Stress Cases

- **T2.1 Empty / Zero-Length Buffer Handling**: Verify DSP blocks handle `len(in_bits) == 0` without exception or crash.
- **T2.2 Fragmented Streaming (Single-Byte Chunks)**: Verify frame synchronization works when bits arrive 1 byte or 1 bit at a time.
- **T2.3 Preamble Error Boundary (Threshold vs Threshold+1)**: Verify lock with $\le 2$ errors and rejection with $\ge 3$ errors.
- **T2.4 Arbitrary Bit Alignment Offsets**: Test frame synchronization at initial bit offsets $\Delta \in \{0, 1, 7, 13, 100, 500, 999\}$.
- **T2.5 Extreme Low SNR (-10 dB to 0 dB)**: Verify SNR estimator and BER counter operate gracefully under deep noise without NaN or crash.
- **T2.6 Extreme High SNR (+40 dB to +60 dB)**: Verify numerical stability without division by zero when noise variance $\to 0$.
- **T2.7 Phase Jitter Tolerance**: Test differential decoder under continuous Gaussian phase jitter $\sigma_\theta \in [5^\circ, 15^\circ, 30^\circ]$.
- **T2.8 Large-Scale Memory & Throughput Stress**: Process 1,000,000 bits continuously verifying zero memory growth and constant throughput.
- **T2.9 CSV Directory Auto-Creation**: Verify logger automatically creates missing directory paths without failing.
- **T2.10 Degenerate Payload Sequences**: Test all-zeros, all-ones, and alternating 0101 payloads for pattern-dependent bias.

---

### Tier 3: Cross-Feature Integration Combinations

- **T3.1 Full E2E TX-Channel-RX Pipeline**: Integrated test connecting Frame Generator $\to$ QPSK Modulator $\to$ AWGN Channel $\to$ Slicer $\to$ Diff Decoder $\to$ Unpacker $\to$ Measurement Engine.
- **T3.2 Theoretical Waterfall BER vs SNR Curve**: Validate measured BER against theoretical QPSK curve $P_b = Q(\sqrt{2 E_b/N_0})$ across SNR $\in [2, 4, 6, 8, 10]$ dB.
- **T3.3 Dynamic Phase Slip Recovery**: Inject 90° phase jumps mid-transmission; verify automatic re-alignment and BER convergence to 0.
- **T3.4 Burst Noise Frame Re-acquisition**: Corrupt 1 full frame (1000 bits) with random noise; verify immediate recovery on subsequent clean frame.
- **T3.5 Multi-Frame Cumulative Tracking & CSV Integrity**: Verify multi-frame cumulative stats match exact ground truth across 20 consecutive frames with active CSV logging.

---

### Tier 4: Real-World Hardware & Environmental Scenarios

- **T4.1 USRP B210 Impairment Emulation**: Simulate simultaneous Carrier Frequency Offset (CFO = $\pm 5$ kHz), Carrier Phase Drift, Sample Frequency Offset (SFO = 50 ppm), and AWGN channel.
- **T4.2 Multipath Rayleigh & Rician Fading**: Simulate multipath fading channels with delay spread and Doppler, verifying equalizer convergence and frame synchronization.
- **T4.3 Dynamic SNR Step Profile Tracking**: Apply sudden SNR step changes ($20 \text{ dB} \to 8 \text{ dB} \to 15 \text{ dB} \to 25 \text{ dB}$) and verify EMA smoothing response time and asymptotic accuracy.
- **T4.4 100+ Frame Long-Duration Stability**: Stream 100 consecutive frames (100,000 bits) continuously, verifying cumulative vs instantaneous BER convergence and zero drift.
- **T4.5 Burst Transmission with Intermittent Frame Gaps**: Transmit frames separated by random zero-padding / silence intervals, verifying robust burst preamble acquisition without false positives.

---

## 4. Test Execution & Verification

### Test Harness Command
To execute the complete 4-tier test suite using the Radioconda Python environment:

```powershell
C:\Users\prana\radioconda\python.exe c:\Users\prana\OneDrive\Desktop\hqam_stuf\test_qpsk_ber_engine.py
```

### Expected Test Output
- Total Tests Executed: $\ge 40$ test cases across 4 tiers.
- Success Rate: 100% Pass.
- Execution Time: $< 15$ seconds.
- Flowgraph Compilation: All discovered `.grc` flowgraphs compiled cleanly via `grcc`.
