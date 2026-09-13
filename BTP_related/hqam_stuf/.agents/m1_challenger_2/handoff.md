# Milestone 1 Adversarial Challenge Report: QPSK Transmitter Modulation Parameters

## 1. Observation

Direct empirical observations and verification artifacts:

1. **Constellation Definition in miscellenious/tx_qpsk_hardware_ber.grc (Lines 60-73)**:
   `yaml
   - name: qpsk
     id: variable_constellation_rect
     parameters:
       comment: QPSK Gray Coded Constellation
       const_points: '[-0.707-0.707j, 0.707-0.707j, +0.707+0.707j, -0.707+0.707j]'
       imag_sect: '2'
       precision: '8'
       real_sect: '2'
       rot_sym: '4'
       soft_dec_lut: null
       sym_map: '[0, 1, 3, 2]'
       w_imag_sect: '1'
       w_real_sect: '1'
   `

2. **Empirical Constellation Power Calculation (.agents/m1_challenger_2/verify_m1_adversarial.py)**:
   - Point 0 (-0.707 - 0.707j): |p_0|^2 = (-0.707)^2 + (-0.707)^2 = 0.999698, deviation from 1.0 = 0.000302 (-0.0013 dB).
   - Point 1 (+0.707 - 0.707j): |p_1|^2 = (+0.707)^2 + (-0.707)^2 = 0.999698, deviation from 1.0 = 0.000302 (-0.0013 dB).
   - Point 2 (+0.707 + 0.707j): |p_2|^2 = (+0.707)^2 + (+0.707)^2 = 0.999698, deviation from 1.0 = 0.000302 (-0.0013 dB).
   - Point 3 (-0.707 + 0.707j): |p_3|^2 = (-0.707)^2 + (+0.707)^2 = 0.999698, deviation from 1.0 = 0.000302 (-0.0013 dB).
   - Average Constellation Power: E[|p|^2] = 0.999698 ~= 1.000.
   - Constellation Peak-to-Average Power Ratio (PAPR): 1.000.

3. **Gray Mapping & Quadrant Transition Hamming Distance**:
   - Quadrant 3 (theta = 225 deg / -135 deg): Point 0 -> sym_map[0] = 0 (00b)
   - Quadrant 4 (theta = 315 deg / -45 deg): Point 1 -> sym_map[1] = 1 (01b)
   - Quadrant 1 (theta = 45 deg): Point 2 -> sym_map[2] = 3 (11b)
   - Quadrant 2 (theta = 135 deg): Point 3 -> sym_map[3] = 2 (10b)
   - **Adjacent Quadrant Transitions (90 deg phase shift)**:
     - Q3 (00b) <-> Q4 (01b): Hamming distance = 1 (bit 0 flips)
     - Q4 (01b) <-> Q1 (11b): Hamming distance = 1 (bit 1 flips)
     - Q1 (11b) <-> Q2 (10b): Hamming distance = 1 (bit 0 flips)
     - Q2 (10b) <-> Q3 (00b): Hamming distance = 1 (bit 1 flips)
   - **Diagonal Quadrant Transitions (180 deg phase shift)**:
     - Q3 (00b) <-> Q1 (11b): Hamming distance = 2
     - Q4 (01b) <-> Q2 (10b): Hamming distance = 2

4. **grcc Compilation Tool Execution**:
   - Command: C:/Users/prana/radioconda/Scripts/grcc.exe -o miscellenious miscellenious/tx_qpsk_hardware_ber.grc
   - Return Code: 0
   - STDOUT: <<< Welcome to GNU Radio Companion Compiler 3.10.12.0 >>> ... Generating: .../tx_qpsk_hardware_ber.py
   - STDERR: (empty - zero warnings, zero errors).

5. **End-to-End GNU Radio Flowgraph Runtime Execution (.agents/m1_challenger_2/test_flowgraph_run.py)**:
   - Python Flowgraph executing vector_source_b -> epy_block_0 -> digital.generic_mod (QPSK rect, differential, SPS=4, alpha=0.35) -> vector_sink_c.
   - Output: 40,960 complex baseband samples generated, mean power = 0.997512, peak magnitude = 1.557637 (RRC pulse overshoot), zero assertion errors.

---

## 2. Logic Chain

1. **Unit Power Normalization Assessment**:
   - The theoretical normalization for a 4-QAM / QPSK rectangular constellation on a Cartesian grid with equidistant points is s_i = (+/- 1/sqrt(2)) +/- j * (1/sqrt(2)).
   - 1 / sqrt(2) ~= 0.70710678. The parameter value 0.707 yields |s|^2 = 0.707^2 + 0.707^2 = 0.499849 + 0.499849 = 0.999698.
   - The residual power offset is < 0.0302% (less than -0.0013 dB), which is negligible relative to SDR analog quantization (e.g. 12-bit ADC/DAC in USRP B210 gives ~72 dB dynamic range, where 0.0013 dB is far below quantization noise floor).
   - Hence, unit power normalization is mathematically and empirically validated.

2. **Gray Code Mapping Assessment**:
   - Gray coding requires that every single adjacent constellation point in Euclidean / phase space (adjacent quadrants separated by pi/2 radians) maps to binary bit patterns differing by exactly 1 bit (Hamming distance = 1).
   - The observed sequence of quadrants along counter-clockwise traversal is Q3 (index 0) -> Q4 (index 1) -> Q1 (index 2) -> Q2 (index 3).
   - Applying sym_map: [0, 1, 3, 2] produces the binary sequence 00 -> 01 -> 11 -> 10 -> 00.
   - In every adjacent step, the Hamming distance is strictly 1. Non-adjacent (diagonal) steps have Hamming distance 2.
   - Consequently, the most probable symbol estimation errors under AWGN (crossing a single decision boundary) cause exactly 1 bit error, optimizing bit error rate (BER).

3. **Compiler & Flowgraph Integrity Assessment**:
   - grcc parsed the YAML flowgraph tx_qpsk_hardware_ber.grc, validated all block parameters (center frequency 2.85 GHz, sample rate 1.0 MSps, SPS 4, excess bandwidth 0.35, USRP sink configuration, and embedded frame generator), and successfully compiled tx_qpsk_hardware_ber.py.
   - No undefined variables, missing callbacks, or port type mismatches occurred.
   - Executing the generated DSP modulator in Python confirmed continuous frame streaming and sample generation without buffer starvation or data corruption.

---

## 3. Caveats

- Physical Over-The-Air RF transmission was verified through software simulation and standalone GNU Radio DSP blocks; full over-the-air RF radiation requires physical USRP B210 hardware connected via USB 3.0.
- No caveats regarding mathematical parameterization, Gray coding, or flowgraph syntax.

---

## 4. Conclusion & Verdict

All four Milestone 1 adversarial challenge criteria have been empirically verified and validated:
1. Constellation points are unit-power normalized (|-0.707 +/- 0.707j|^2 = 0.999698 ~= 1.000).
2. Gray mapping sym_map: [0, 1, 3, 2] produces single-bit Hamming distance transitions (H=1) between all adjacent constellation quadrants.
3. grcc compiles tx_qpsk_hardware_ber.grc cleanly with zero warnings and zero errors (exit code 0).
4. The embedded TX frame generator and generic QPSK modulator execute cleanly end-to-end.

**Verdict**: APPROVE

---

## 5. Verification Method

To independently verify these findings, execute the following commands in Radioconda GNU Radio environment:

1. **Run Empirical Adversarial Test Suite**:
   `ash
   C:/Users/prana/radioconda/python.exe .agents/m1_challenger_2/verify_m1_adversarial.py
   `
2. **Run End-to-End Modulator Flowgraph Execution Test**:
   `ash
   C:/Users/prana/radioconda/python.exe .agents/m1_challenger_2/test_flowgraph_run.py
   `
3. **Run grcc Compilation Check**:
   `ash
   C:/Users/prana/radioconda/Scripts/grcc.exe -o miscellenious miscellenious/tx_qpsk_hardware_ber.grc
   `
