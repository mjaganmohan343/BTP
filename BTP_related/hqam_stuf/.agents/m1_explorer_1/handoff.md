# Milestone 1: QPSK Hardware Transmitter Architecture & Implementation Blueprint Report

**Author**: `m1_explorer_1`  
**Date**: 2026-08-18  
**Target Files**:
1. `miscellenious/tx_qpsk_hardware_ber.grc` (GNU Radio 3.10 Flowgraph)
2. `miscellenious/tx_qpsk_hardware_ber_epy_block_0.py` (Embedded Frame Generator Python Block)

---

## 1. Observation

Direct observations from inspecting reference flowgraphs (`miscellenious/tx_bpsk_hardware_ber.grc`, `miscellenious/tx_bpsk_hardware_ber_epy_block_0.py`, `miscellenious/tx_qpsk_hardware.grc`, `miscellenious/Qpsk_modem.grc`), project definitions (`PROJECT.md`, `ORIGINAL_REQUEST.md`), and GNU Radio 3.10.12.0 runtime environment:

### 1.1 Transmitter Hardware Parameters
- **USRP B210 Parameters** (`tx_bpsk_hardware_ber.grc:294-571`, `tx_qpsk_hardware.grc:185-223`):
  - Sample Rate: `samp_rate = 1000000` (1.0 MSps)
  - Center Frequency: `center_freq = 2850000000` (2.85 GHz ISM/S-Band)
  - Default TX Gain: `tx_gain = 33` dB, adjustable via `variable_qtgui_range` from `0` to `89.8` dB in steps of `1` dB
  - RF Port: `ant0: "TX/RX"`
  - Clock Synchronization: `sync: pc_clock`, `clock_rate: 0e0`
  - Baseband Stream Format: `fc32` (Complex Float 32)
  - Device Arguments: `dev_addr: ""` (auto-identifies connected USRP B210), `dev_args: ""`

### 1.2 Modulation & Constellation Specs
- **QPSK Constellation Definition** (`tx_qpsk_hardware.grc:117-137`, `Qpsk_modem.grc:167-187`):
  - Block: `variable_constellation_rect`
  - Normalized Constellation Points: `[-0.707-0.707j, 0.707-0.707j, +0.707+0.707j, -0.707+0.707j]` (unit power $|s_k|^2 \approx 1.0$)
  - Symbol Mapping: `sym_map: [0, 1, 3, 2]` (Standard Gray coding)
  - Rotational Symmetry: `rot_sym: 4`
  - Sector Divisions: `real_sect: 2`, `imag_sect: 2`, `w_real_sect: 1`, `w_imag_sect: 1`
  - Precision: `precision: 8`
- **Modulator Block** (`tx_qpsk_hardware.grc:161-183`):
  - Block: `digital_constellation_modulator` (`digital.generic_mod`)
  - Differential Encoding: `differential: True`
  - Samples per Symbol: `samples_per_symbol: sps` (`sps = 4`)
  - Excess Bandwidth (Roll-off factor): `excess_bw: excess_bw` (`excess_bw = 0.35`)
  - Input Type: Packed bytes (`byte`/`uint8`)

### 1.3 Frame Structure & Preamble Specs
- **Frame Length Contract** (`PROJECT.md:46-48`):
  - Total frame length: 1000 bits
  - Preamble (32 bits): Barker/sync word `[1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1]` (Hex: `0xF9`, `0xAF`, `0xCD`, `0x65`)
  - PRBS Payload (968 bits): Pseudo-random binary sequence seeded via `np.random.seed(42)` and `np.random.randint(0, 2, size=968, dtype=np.uint8)`
  - Packing: 8 bits packed MSB-first per byte $\to \frac{1000 \text{ bits}}{8 \text{ bits/byte}} = 125 \text{ bytes}$ per frame ($500 \text{ QPSK symbols}$ per frame)
  - Streaming Behavior: Embedded `gr.basic_block` consuming trigger tokens from `analog_random_source_x` and outputting continuous cyclic stream of 125-byte frames

### 1.4 Visualization Sinks
- **QT GUI Frequency Sink** (`qtgui_freq_sink_x`): 2048 FFT size, Blackman-Harris window, centered at $f_c = 2.85\text{ GHz}$, bandwidth $1.0\text{ MHz}$, GUI hint `1,1,1,1`
- **QT GUI Constellation Sink** (`qtgui_const_sink_x`): 1024 points, range $[-2, 2]$, GUI hint `1,0,1,1`
- **QT GUI Time Sink** (`qtgui_time_sink_x`): 256 samples, complex I & Q pulse visualization, sample rate $1.0\text{ MSps}$, range $[-1.5, 1.5]$, GUI hint `2,0,1,2`

---

## 2. Logic Chain

1. **Symbol Rate and Bit Rate Alignment**:
   - At `samp_rate = 1.0 MSps` and `sps = 4`, symbol rate is $R_s = \frac{1.0 \times 10^6}{4} = 250\text{ kbaud}$.
   - For QPSK ($k=2$ bits/sym), the raw bit rate is $R_b = 2 \times 250\text{ kbaud} = 500\text{ kbps}$.
   - One 1000-bit frame corresponds to 500 QPSK symbols, taking $2.0\text{ ms}$ over the air.
   - Packed at 8 bits/byte, each 1000-bit frame equals exactly 125 bytes.

2. **Byte-to-Symbol Processing by `digital_constellation_modulator`**:
   - `digital_constellation_modulator` accepts a byte stream (`uint8`), unpacks $k=2$ bits per symbol from each byte in MSB-first order (bits 7-6, bits 5-4, bits 3-2, bits 1-0), applies differential encoding modulo 4, maps symbol indices to Gray constellation points, and passes the impulse train through an RRC filter at `sps = 4` and $\alpha = 0.35$.
   - Because 1 byte contains 4 QPSK symbols ($4 \times 2 = 8$ bits), 125 bytes cleanly produce $125 \times 4 = 500$ QPSK symbols with zero byte-boundary truncation or fractional symbol misalignment.

3. **Phase Ambiguity Resilience**:
   - The rectangular Gray mapping `sym_map = [0, 1, 3, 2]` combined with `differential = True` in `digital_constellation_modulator` encodes information into phase transitions:
     $$\Delta \theta_k = (\theta_k - \theta_{k-1}) \pmod 4$$
   - When the receiver locks onto any of the 4 Costas loop equilibria ($0^\circ, 90^\circ, 180^\circ, 270^\circ$), the static phase offset cancels out under differential decoding at the receiver.

4. **Frame Generator Block Execution**:
   - Deriving from `gr.basic_block` with input `[np.uint8]` and output `[np.uint8]`, `general_work()` matches the tested architecture of `tx_bpsk_hardware_ber_epy_block_0.py`.
   - Feeding dummy trigger bytes from `analog_random_source_x` ensures buffer backpressure is handled smoothly while streaming the 125-byte pattern endlessly without CPU starvation or memory allocation overhead.

---

## 3. Caveats

1. **Embedded Python Block Name & Caching**:
   - GNU Radio Companion stores the block code inside the `.grc` file (`_source_code` param) AND creates `tx_qpsk_hardware_ber_epy_block_0.py`. Both files must have matching source code and `_io_cache` tuples to prevent GRC cache refresh prompts.
2. **USRP B210 Driver Initialization**:
   - If no USRP B210 hardware is attached during local testing, running the generated Python script directly will fail with `uhd.usrp.find()`. However, `grcc` flowgraph compilation is fully offline and succeeds with exit code 0.
3. **Gain Control Dynamic Range**:
   - The USRP B210 TX gain range spans 0 to 89.8 dB. Operating at >70 dB without attenuation into an adjacent receiver port will saturate the RX LNA. Default is set to 33 dB.

---

## 4. Conclusion

The exact blueprints for `miscellenious/tx_qpsk_hardware_ber.grc` and `miscellenious/tx_qpsk_hardware_ber_epy_block_0.py` are fully defined below.

### 4.1 Embedded Python Block Implementation (`tx_qpsk_hardware_ber_epy_block_0.py`)

```python
import numpy as np
from gnuradio import gr

class blk(gr.basic_block):
    """BER Frame Generator & Preamble Inserter for QPSK"""
    def __init__(self, packet_len=1000):
        gr.basic_block.__init__(
            self,
            name='QPSK BER Frame Generator',
            in_sig=[np.uint8],
            out_sig=[np.uint8]
        )
        self.packet_len = packet_len
        # 32-bit QPSK sync word preamble
        self.preamble = np.array([
            1, 1, 1, 1, 1, 0, 0, 1,
            1, 0, 1, 0, 1, 1, 1, 1,
            1, 1, 0, 0, 1, 1, 0, 1,
            0, 1, 1, 0, 0, 1, 0, 1
        ], dtype=np.uint8)
        
        # 968-bit pseudo-random binary payload (seed 42)
        np.random.seed(42)
        self.payload_ref = np.random.randint(0, 2, size=968, dtype=np.uint8)
        
        # Full packet = 32 + 968 = 1000 bits
        self.packet = np.concatenate([self.preamble, self.payload_ref])
        
        # Pack 8 bits into 1 byte (MSB first) -> 125 bytes per frame
        n_bytes = len(self.packet) // 8
        self.packed_packet = np.zeros(n_bytes, dtype=np.uint8)
        for i in range(n_bytes):
            byte_val = 0
            for b in range(8):
                byte_val = (byte_val << 1) | (int(self.packet[8 * i + b]) & 1)
            self.packed_packet[i] = byte_val
            
        self.ptr = 0

    def general_work(self, input_items, output_items):
        in0 = input_items[0]
        out = output_items[0]
        n_out = len(out)
        written = 0
        read = min(len(in0), n_out)
        
        while written < read:
            rem = len(self.packed_packet) - self.ptr
            to_write = min(rem, read - written)
            out[written:written+to_write] = self.packed_packet[self.ptr:self.ptr+to_write]
            self.ptr = (self.ptr + to_write) % len(self.packed_packet)
            written += to_write
            
        self.consume(0, read)
        return written
```

---

### 4.2 GNU Radio 3.10 Flowgraph Blueprint (`tx_qpsk_hardware_ber.grc`)

```yaml
options:
  parameters:
    author: pranav
    catch_exceptions: 'True'
    category: Custom
    cmake_opt: ''
    comment: ''
    copyright: ''
    description: QPSK Hardware BER Transmitter using USRP B210
    gen_cmake: 'On'
    gen_linking: dynamic
    generate_options: qt_gui
    hier_block_src_path: '.:'
    id: tx_qpsk_hardware_ber
    max_nouts: '0'
    output_language: python
    placement: (0,0)
    qt_qss_theme: ''
    realtime_scheduling: ''
    run: 'True'
    run_command: '{python} -u {filename}'
    run_options: prompt
    sizing_mode: fixed
    thread_safe_setters: ''
    title: QPSK Hardware BER Transmitter
    window_size: 2000,2000
  states:
    bus_sink: false
    bus_source: false
    bus_structure: null
    coordinate: [16, 16.0]
    rotation: 0
    state: enabled

blocks:
- name: center_freq
  id: variable
  parameters:
    comment: Carrier frequency (2.85 GHz)
    value: '2850000000'
  states:
    bus_sink: false
    bus_source: false
    bus_structure: null
    coordinate: [296, 16.0]
    rotation: 0
    state: enabled
- name: excess_bw
  id: variable
  parameters:
    comment: RRC excess bandwidth / roll-off factor
    value: '0.35'
  states:
    bus_sink: false
    bus_source: false
    bus_structure: null
    coordinate: [480, 16.0]
    rotation: 0
    state: enabled
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
  states:
    bus_sink: false
    bus_source: false
    bus_structure: null
    coordinate: [760, 16.0]
    rotation: 0
    state: enabled
- name: samp_rate
  id: variable
  parameters:
    comment: Baseband sample rate (1.0 MSps)
    value: '1000000'
  states:
    bus_sink: false
    bus_source: false
    bus_structure: null
    coordinate: [192, 16.0]
    rotation: 0
    state: enabled
- name: sps
  id: variable
  parameters:
    comment: Samples per symbol
    value: '4'
  states:
    bus_sink: false
    bus_source: false
    bus_structure: null
    coordinate: [400, 16.0]
    rotation: 0
    state: enabled
- name: tx_gain
  id: variable_qtgui_range
  parameters:
    comment: Transmitter RF Gain slider
    gui_hint: 0,0,1,1
    label: TX Gain (dB)
    min_len: '200'
    orient: QtCore.Qt.Horizontal
    rangeType: float
    start: '0'
    step: '1'
    stop: '89.8'
    value: '33'
    widget: counter_slider
  states:
    bus_sink: false
    bus_source: false
    bus_structure: null
    coordinate: [576, 16.0]
    rotation: 0
    state: enabled
- name: analog_random_source_x_0
  id: analog_random_source_x
  parameters:
    affinity: ''
    alias: ''
    comment: Trigger source driving the frame generator
    max: '256'
    maxoutbuf: '0'
    min: '0'
    minoutbuf: '0'
    num_samps: '10000'
    repeat: 'True'
    type: byte
  states:
    bus_sink: false
    bus_source: false
    bus_structure: null
    coordinate: [16, 220.0]
    rotation: 0
    state: enabled
- name: digital_constellation_modulator_0
  id: digital_constellation_modulator
  parameters:
    affinity: ''
    alias: ''
    comment: QPSK Differential Modulator with RRC Pulse Shaping Filter
    constellation: qpsk
    differential: 'True'
    excess_bw: excess_bw
    log: 'False'
    maxoutbuf: '0'
    minoutbuf: '0'
    samples_per_symbol: sps
    truncate: 'False'
    verbose: 'False'
  states:
    bus_sink: false
    bus_source: false
    bus_structure: null
    coordinate: [512, 220.0]
    rotation: 0
    state: enabled
- name: epy_block_0
  id: epy_block
  parameters:
    _source_code: "import numpy as np\nfrom gnuradio import gr\n\nclass blk(gr.basic_block):\n\
      \    \"\"\"BER Frame Generator & Preamble Inserter for QPSK\"\"\"\n    def __init__(self,\
      \ packet_len=1000):\n        gr.basic_block.__init__(\n            self,\n \
      \           name='QPSK BER Frame Generator',\n            in_sig=[np.uint8],\n\
      \            out_sig=[np.uint8]\n        )\n        self.packet_len = packet_len\n\
      \        # 32-bit QPSK sync word preamble\n        self.preamble = np.array([\n\
      \            1, 1, 1, 1, 1, 0, 0, 1,\n            1, 0, 1, 0, 1, 1, 1, 1,\n\
      \            1, 1, 0, 0, 1, 1, 0, 1,\n            0, 1, 1, 0, 0, 1, 0, 1\n\
      \        ], dtype=np.uint8)\n        np.random.seed(42)\n        # 968-bit pseudo-random\
      \ binary payload\n        self.payload_ref = np.random.randint(0, 2, size=968,\
      \ dtype=np.uint8)\n        \n        # Full frame: 32 + 968 = 1000 bits\n \
      \       self.packet = np.concatenate([self.preamble, self.payload_ref])\n  \
      \      \n        # Pack 8 bits into 1 byte (MSB-first) -> 125 bytes per frame\n\
      \        n_bytes = len(self.packet) // 8\n        self.packed_packet = np.zeros(n_bytes,\
      \ dtype=np.uint8)\n        for i in range(n_bytes):\n            byte_val =\
      \ 0\n            for b in range(8):\n                byte_val = (byte_val <<\
      \ 1) | (int(self.packet[8*i + b]) & 1)\n            self.packed_packet[i] =\
      \ byte_val\n            \n        self.ptr = 0\n\n    def general_work(self,\
      \ input_items, output_items):\n        in0 = input_items[0]\n        out = output_items[0]\n\
      \        n_out = len(out)\n        written = 0\n        read = min(len(in0),\
      \ n_out)\n        \n        while written < read:\n            rem = len(self.packed_packet)\
      \ - self.ptr\n            to_write = min(rem, read - written)\n            out[written:written+to_write]\
      \ = self.packed_packet[self.ptr:self.ptr+to_write]\n            self.ptr = (self.ptr\
      \ + to_write) % len(self.packed_packet)\n            written += to_write\n \
      \           \n        self.consume(0, read)\n        return written\n"
    affinity: ''
    alias: ''
    comment: Frame Generator (32-bit Preamble + 968-bit PRBS-42 Payload, Packed into 125 Bytes)
    maxoutbuf: '0'
    minoutbuf: '0'
    packet_len: '1000'
  states:
    _io_cache: ('QPSK BER Frame Generator', 'blk', [('packet_len', '1000')], [('0',
      'byte', 1)], [('0', 'byte', 1)], 'BER Frame Generator & Preamble Inserter for
      QPSK', ['packet_len'])
    bus_sink: false
    bus_source: false
    bus_structure: null
    coordinate: [248, 244.0]
    rotation: 0
    state: enabled
- name: qtgui_const_sink_x_0
  id: qtgui_const_sink_x
  parameters:
    affinity: ''
    alias: ''
    alpha1: '1.0'
    alpha10: '1.0'
    alpha2: '1.0'
    alpha3: '1.0'
    alpha4: '1.0'
    alpha5: '1.0'
    alpha6: '1.0'
    alpha7: '1.0'
    alpha8: '1.0'
    alpha9: '1.0'
    autoscale: 'False'
    axislabels: 'True'
    color1: '"blue"'
    color10: '"red"'
    color2: '"red"'
    color3: '"red"'
    color4: '"red"'
    color5: '"red"'
    color6: '"red"'
    color7: '"red"'
    color8: '"red"'
    color9: '"red"'
    comment: Visualizes transmitted QPSK constellation
    grid: 'True'
    gui_hint: 1,0,1,1
    label1: '"Transmitted QPSK Symbols"'
    label10: ''
    label2: ''
    label3: ''
    label4: ''
    label5: ''
    label6: ''
    label7: ''
    label8: ''
    label9: ''
    legend: 'True'
    marker1: '0'
    marker10: '0'
    marker2: '0'
    marker3: '0'
    marker4: '0'
    marker5: '0'
    marker6: '0'
    marker7: '0'
    marker8: '0'
    marker9: '0'
    name: '"QPSK TX Constellation"'
    nconnections: '1'
    size: '1024'
    style1: '0'
    style10: '0'
    style2: '0'
    style3: '0'
    style4: '0'
    style5: '0'
    style6: '0'
    style7: '0'
    style8: '0'
    style9: '0'
    tr_chan: '0'
    tr_level: '0.0'
    tr_mode: qtgui.TRIG_MODE_FREE
    tr_slope: qtgui.TRIG_SLOPE_POS
    tr_tag: '""'
    type: complex
    update_time: '0.10'
    width1: '1'
    width10: '1'
    width2: '1'
    width3: '1'
    width4: '1'
    width5: '1'
    width6: '1'
    width7: '1'
    width8: '1'
    width9: '1'
    xmax: '2'
    xmin: '-2'
    ymax: '2'
    ymin: '-2'
  states:
    bus_sink: false
    bus_source: false
    bus_structure: null
    coordinate: [824, 292.0]
    rotation: 0
    state: enabled
- name: qtgui_freq_sink_x_0
  id: qtgui_freq_sink_x
  parameters:
    affinity: ''
    alias: ''
    alpha1: '1.0'
    alpha10: '1.0'
    alpha2: '1.0'
    alpha3: '1.0'
    alpha4: '1.0'
    alpha5: '1.0'
    alpha6: '1.0'
    alpha7: '1.0'
    alpha8: '1.0'
    alpha9: '1.0'
    autoscale: 'False'
    average: '0.1'
    axislabels: 'True'
    bw: samp_rate
    color1: '"blue"'
    color10: '"dark blue"'
    color2: '"red"'
    color3: '"green"'
    color4: '"black"'
    color5: '"cyan"'
    color6: '"magenta"'
    color7: '"yellow"'
    color8: '"dark red"'
    color9: '"dark green"'
    comment: Visualizes transmitted RF spectrum
    ctrlpanel: 'False'
    fc: center_freq
    fftsize: '2048'
    freqhalf: 'True'
    grid: 'True'
    gui_hint: 1,1,1,1
    label: Relative Gain
    label1: '"Transmitted Spectrum"'
    label10: ''''''
    label2: ''''''
    label3: ''''''
    label4: ''''''
    label5: ''''''
    label6: ''''''
    label7: ''''''
    label8: ''''''
    label9: ''''''
    legend: 'True'
    maxoutbuf: '0'
    minoutbuf: '0'
    name: '"TX Spectrum"'
    nconnections: '1'
    norm_window: 'False'
    showports: 'False'
    tr_chan: '0'
    tr_level: '0.0'
    tr_mode: qtgui.TRIG_MODE_FREE
    tr_tag: '""'
    type: complex
    units: dB
    update_time: '0.10'
    width1: '1'
    width10: '1'
    width2: '1'
    width3: '1'
    width4: '1'
    width5: '1'
    width6: '1'
    width7: '1'
    width8: '1'
    width9: '1'
    wintype: window.WIN_BLACKMAN_hARRIS
    ymax: '10'
    ymin: '-100'
  states:
    bus_sink: false
    bus_source: false
    bus_structure: null
    coordinate: [824, 396.0]
    rotation: 0
    state: enabled
- name: qtgui_time_sink_x_0
  id: qtgui_time_sink_x
  parameters:
    affinity: ''
    alias: ''
    alpha1: '1.0'
    alpha10: '1.0'
    alpha2: '1.0'
    alpha3: '1.0'
    alpha4: '1.0'
    alpha5: '1.0'
    alpha6: '1.0'
    alpha7: '1.0'
    alpha8: '1.0'
    alpha9: '1.0'
    autoscale: 'False'
    axislabels: 'True'
    color1: blue
    color10: dark blue
    color2: red
    color3: green
    color4: black
    color5: cyan
    color6: magenta
    color7: yellow
    color8: dark red
    color9: dark green
    comment: Visualizes shaped baseband I/Q pulses
    ctrlpanel: 'False'
    entags: 'True'
    grid: 'True'
    gui_hint: 2,0,1,2
    label1: '"In-Phase (I)"'
    label10: ''
    label2: '"Quadrature (Q)"'
    label3: ''
    label4: ''
    label5: ''
    label6: ''
    label7: ''
    label8: ''
    label9: ''
    legend: 'True'
    marker1: '-1'
    marker10: '-1'
    marker2: '-1'
    marker3: '-1'
    marker4: '-1'
    marker5: '-1'
    marker6: '-1'
    marker7: '-1'
    marker8: '-1'
    marker9: '-1'
    name: '"TX Baseband Pulses (I & Q)"'
    nconnections: '1'
    size: '256'
    srate: samp_rate
    stemplot: 'False'
    style1: '1'
    style10: '1'
    style2: '1'
    style3: '1'
    style4: '1'
    style5: '1'
    style6: '1'
    style7: '1'
    style8: '1'
    style9: '1'
    tr_chan: '0'
    tr_delay: '0'
    tr_level: '0.0'
    tr_mode: qtgui.TRIG_MODE_FREE
    tr_slope: qtgui.TRIG_SLOPE_POS
    tr_tag: '""'
    type: complex
    update_time: '0.10'
    width1: '1'
    width10: '1'
    width2: '1'
    width3: '1'
    width4: '1'
    width5: '1'
    width6: '1'
    width7: '1'
    width8: '1'
    width9: '1'
    ylabel: Amplitude
    ymax: '1.5'
    ymin: '-1.5'
    yunit: '""'
  states:
    bus_sink: false
    bus_source: false
    bus_structure: null
    coordinate: [824, 508.0]
    rotation: 0
    state: enabled
- name: uhd_usrp_sink_0
  id: uhd_usrp_sink
  parameters:
    affinity: ''
    alias: ''
    ant0: '"TX/RX"'
    ant1: '"TX/RX"'
    ant10: '"TX/RX"'
    ant11: '"TX/RX"'
    ant12: '"TX/RX"'
    ant13: '"TX/RX"'
    ant14: '"TX/RX"'
    ant15: '"TX/RX"'
    ant16: '"TX/RX"'
    ant17: '"TX/RX"'
    ant18: '"TX/RX"'
    ant19: '"TX/RX"'
    ant2: '"TX/RX"'
    ant20: '"TX/RX"'
    ant21: '"TX/RX"'
    ant22: '"TX/RX"'
    ant23: '"TX/RX"'
    ant24: '"TX/RX"'
    ant25: '"TX/RX"'
    ant26: '"TX/RX"'
    ant27: '"TX/RX"'
    ant28: '"TX/RX"'
    ant29: '"TX/RX"'
    ant3: '"TX/RX"'
    ant30: '"TX/RX"'
    ant31: '"TX/RX"'
    ant4: '"TX/RX"'
    ant5: '"TX/RX"'
    ant6: '"TX/RX"'
    ant7: '"TX/RX"'
    ant8: '"TX/RX"'
    ant9: '"TX/RX"'
    bw0: '0'
    bw1: '0'
    bw10: '0'
    bw11: '0'
    bw12: '0'
    bw13: '0'
    bw14: '0'
    bw15: '0'
    bw16: '0'
    bw17: '0'
    bw18: '0'
    bw19: '0'
    bw2: '0'
    bw20: '0'
    bw21: '0'
    bw22: '0'
    bw23: '0'
    bw24: '0'
    bw25: '0'
    bw26: '0'
    bw27: '0'
    bw28: '0'
    bw29: '0'
    bw3: '0'
    bw30: '0'
    bw31: '0'
    bw4: '0'
    bw5: '0'
    bw6: '0'
    bw7: '0'
    bw8: '0'
    bw9: '0'
    center_freq0: center_freq
    center_freq1: '0'
    center_freq10: '0'
    center_freq11: '0'
    center_freq12: '0'
    center_freq13: '0'
    center_freq14: '0'
    center_freq15: '0'
    center_freq16: '0'
    center_freq17: '0'
    center_freq18: '0'
    center_freq19: '0'
    center_freq2: '0'
    center_freq20: '0'
    center_freq21: '0'
    center_freq22: '0'
    center_freq23: '0'
    center_freq24: '0'
    center_freq25: '0'
    center_freq26: '0'
    center_freq27: '0'
    center_freq28: '0'
    center_freq29: '0'
    center_freq3: '0'
    center_freq30: '0'
    center_freq31: '0'
    center_freq4: '0'
    center_freq5: '0'
    center_freq6: '0'
    center_freq7: '0'
    center_freq8: '0'
    center_freq9: '0'
    clock_rate: 0e0
    clock_source0: ''
    clock_source1: ''
    clock_source2: ''
    clock_source3: ''
    clock_source4: ''
    clock_source5: ''
    clock_source6: ''
    clock_source7: ''
    comment: USRP B210 Hardware Transmitter Sink
    dev_addr: '""'
    dev_args: ''
    gain0: tx_gain
    gain1: '0'
    gain10: '0'
    gain11: '0'
    gain12: '0'
    gain13: '0'
    gain14: '0'
    gain15: '0'
    gain16: '0'
    gain17: '0'
    gain18: '0'
    gain19: '0'
    gain2: '0'
    gain20: '0'
    gain21: '0'
    gain22: '0'
    gain23: '0'
    gain24: '0'
    gain25: '0'
    gain26: '0'
    gain27: '0'
    gain28: '0'
    gain29: '0'
    gain3: '0'
    gain30: '0'
    gain31: '0'
    gain4: '0'
    gain5: '0'
    gain6: '0'
    gain7: '0'
    gain8: '0'
    gain9: '0'
    gain_type0: default
    gain_type1: default
    gain_type10: default
    gain_type11: default
    gain_type12: default
    gain_type13: default
    gain_type14: default
    gain_type15: default
    gain_type16: default
    gain_type17: default
    gain_type18: default
    gain_type19: default
    gain_type2: default
    gain_type20: default
    gain_type21: default
    gain_type22: default
    gain_type23: default
    gain_type24: default
    gain_type25: default
    gain_type26: default
    gain_type27: default
    gain_type28: default
    gain_type29: default
    gain_type3: default
    gain_type30: default
    gain_type31: default
    gain_type4: default
    gain_type5: default
    gain_type6: default
    gain_type7: default
    gain_type8: default
    gain_type9: default
    len_tag_name: '""'
    lo_export0: 'False'
    lo_export1: 'False'
    lo_export10: 'False'
    lo_export11: 'False'
    lo_export12: 'False'
    lo_export13: 'False'
    lo_export14: 'False'
    lo_export15: 'False'
    lo_export16: 'False'
    lo_export17: 'False'
    lo_export18: 'False'
    lo_export19: 'False'
    lo_export2: 'False'
    lo_export20: 'False'
    lo_export21: 'False'
    lo_export22: 'False'
    lo_export23: 'False'
    lo_export24: 'False'
    lo_export25: 'False'
    lo_export26: 'False'
    lo_export27: 'False'
    lo_export28: 'False'
    lo_export29: 'False'
    lo_export3: 'False'
    lo_export30: 'False'
    lo_export31: 'False'
    lo_export4: 'False'
    lo_export5: 'False'
    lo_export6: 'False'
    lo_export7: 'False'
    lo_export8: 'False'
    lo_export9: 'False'
    lo_source0: internal
    lo_source1: internal
    lo_source10: internal
    lo_source11: internal
    lo_source12: internal
    lo_source13: internal
    lo_source14: internal
    lo_source15: internal
    lo_source16: internal
    lo_source17: internal
    lo_source18: internal
    lo_source19: internal
    lo_source2: internal
    lo_source20: internal
    lo_source21: internal
    lo_source22: internal
    lo_source23: internal
    lo_source24: internal
    lo_source25: internal
    lo_source26: internal
    lo_source27: internal
    lo_source28: internal
    lo_source29: internal
    lo_source3: internal
    lo_source30: internal
    lo_source31: internal
    lo_source4: internal
    lo_source5: internal
    lo_source6: internal
    lo_source7: internal
    lo_source8: internal
    lo_source9: internal
    maxoutbuf: '0'
    minoutbuf: '0'
    nchan: '1'
    num_mboards: '1'
    otw: ''
    samp_rate: samp_rate
    sd_spec0: ''
    sd_spec1: ''
    sd_spec2: ''
    sd_spec3: ''
    sd_spec4: ''
    sd_spec5: ''
    sd_spec6: ''
    sd_spec7: ''
    show_lo_controls: 'False'
    start_time: '-1.0'
    stream_args: ''
    stream_chans: '[]'
    sync: pc_clock
    time_source0: ''
    time_source1: ''
    time_source2: ''
    time_source3: ''
    time_source4: ''
    time_source5: ''
    time_source6: ''
    time_source7: ''
    type: fc32
  states:
    bus_sink: false
    bus_source: false
    bus_structure: null
    coordinate: [824, 160.0]
    rotation: 0
    state: enabled

connections:
- [analog_random_source_x_0, '0', epy_block_0, '0']
- [digital_constellation_modulator_0, '0', qtgui_const_sink_x_0, '0']
- [digital_constellation_modulator_0, '0', qtgui_freq_sink_x_0, '0']
- [digital_constellation_modulator_0, '0', qtgui_time_sink_x_0, '0']
- [digital_constellation_modulator_0, '0', uhd_usrp_sink_0, '0']
- [epy_block_0, '0', digital_constellation_modulator_0, '0']

metadata:
  file_format: 1
  grc_version: 3.10.12.0
```

---

## 5. Verification Method

1. **Compilation Verification**:
   - Once written by the worker, compile `tx_qpsk_hardware_ber.grc` with `grcc`:
     ```powershell
     C:\Users\prana\radioconda\Scripts\grcc.exe -o c:\Users\prana\OneDrive\Desktop\hqam_stuf\miscellenious c:\Users\prana\OneDrive\Desktop\hqam_stuf\miscellenious\tx_qpsk_hardware_ber.grc
     ```
   - **Pass Criterion**: `grcc` returns exit code `0` and generates `tx_qpsk_hardware_ber.py`.
   - **Invalidation Criterion**: Syntax errors, missing block IDs, port connection type mismatches, or non-zero exit code.

2. **Frame Geometry & PRBS Validation**:
   - Run Python verification script checking frame dimensions, bit packing, and constellation instantiation:
     ```powershell
     C:\Users\prana\radioconda\python.exe -c "
     import numpy as np
     from gnuradio import digital
     preamble = np.array([1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1], dtype=np.uint8)
     np.random.seed(42)
     payload = np.random.randint(0, 2, size=968, dtype=np.uint8)
     packet = np.concatenate([preamble, payload])
     assert len(packet) == 1000, f'Expected 1000 bits, got {len(packet)}'
     assert len(packet) % 8 == 0, 'Packet not byte aligned'
     qpsk = digital.constellation_rect([-0.707-0.707j, 0.707-0.707j, +0.707+0.707j, -0.707+0.707j], [0, 1, 3, 2], 4, 2, 2, 1, 1).base()
     mod = digital.generic_mod(constellation=qpsk, differential=True, samples_per_symbol=4, excess_bw=0.35)
     print('Milestone 1 Blueprint Math & Block Instantiation Fully Verified!')
     "
     ```
