import os
import yaml

def generate_rx_qpsk():
    dst_qpsk = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'miscellenious', 'rx_qpsk_hardware_ber.grc')
    
    qpsk_rx = {}
    qpsk_rx['options'] = {
        'parameters': {
            'author': 'pranav',
            'catch_exceptions': 'True',
            'category': 'Custom',
            'cmake_opt': '',
            'comment': '',
            'copyright': '',
            'description': 'QPSK Hardware BER Receiver using USRP B210',
            'gen_cmake': 'On',
            'gen_linking': 'dynamic',
            'generate_options': 'qt_gui',
            'hier_block_src_path': '.:',
            'id': 'rx_qpsk_hardware_ber',
            'max_nouts': '0',
            'output_language': 'python',
            'placement': '(0,0)',
            'qt_qss_theme': '',
            'realtime_scheduling': '',
            'run': 'True',
            'run_command': '{python} -u {filename}',
            'run_options': 'prompt',
            'sizing_mode': 'fixed',
            'thread_safe_setters': '',
            'title': 'QPSK BER Hardware Receiver (Tunable)',
            'window_size': '2000,2000'
        },
        'states': {
            'bus_sink': False,
            'bus_source': False,
            'bus_structure': None,
            'coordinate': [16, 16.0],
            'rotation': 0,
            'state': 'enabled'
        }
    }
    
    epy_source = (
        "import numpy as np\n"
        "from gnuradio import gr\n"
        "import time\n"
        "import os\n"
        "import inspect\n\n"
        "class blk(gr.sync_block):\n"
        "    \"\"\"QPSK BER & SNR Calculator & CSV Logger\"\"\"\n"
        "    def __init__(self):\n"
        "        gr.sync_block.__init__(\n"
        "            self,\n"
        "            name='QPSK BER & SNR Engine',\n"
        "            in_sig=[np.uint8, np.complex64],\n"
        "            out_sig=[np.uint8]\n"
        "        )\n"
        "        # 32-bit QPSK sync preamble\n"
        "        self.preamble_bits = np.array([\n"
        "            1, 1, 1, 1, 1, 0, 0, 1,\n"
        "            1, 0, 1, 0, 1, 1, 1, 1,\n"
        "            1, 1, 0, 0, 1, 1, 0, 1,\n"
        "            0, 1, 1, 0, 0, 1, 0, 1\n"
        "        ], dtype=np.uint8)\n"
        "        np.random.seed(42)\n"
        "        self.payload_ref = np.random.randint(0, 2, size=968, dtype=np.uint8)\n\n"
        "        self.bit_buffer = np.array([], dtype=np.uint8)\n"
        "        self.total_bits = 0\n"
        "        self.total_errors = 0\n"
        "        self.frame_count = 0\n\n"
        "        # Real-time Decision-Directed SNR Estimation\n"
        "        self.avg_signal_power = 1.0\n"
        "        self.avg_noise_power = 0.01\n"
        "        self.snr_db = 0.0\n\n"
        "        # CSV Logging\n"
        "        dir_path = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else '.'\n"
        "        self.csv_path = os.path.join(dir_path, 'ber_qpsk_log.csv')\n"
        "        try:\n"
        "            self.csv_file = open(self.csv_path, 'w')\n"
        "            self.csv_file.write(\"timestamp,frame,total_bits,total_errors,ber,snr_db\\n\")\n"
        "            self.csv_file.flush()\n"
        "        except Exception:\n"
        "            self.csv_file = None\n\n"
        "        # Self-contained GUI Label Injection\n"
        "        self.top_block = None\n"
        "        self.ber_label = None\n"
        "        self.gui_timer = None\n\n"
        "        for frame_info in inspect.stack():\n"
        "            frame = frame_info.frame\n"
        "            if 'self' in frame.f_locals:\n"
        "                val = frame.f_locals['self']\n"
        "                if hasattr(val, 'top_grid_layout'):\n"
        "                    self.top_block = val\n"
        "                    break\n\n"
        "        if self.top_block:\n"
        "            try:\n"
        "                from PyQt5.QtWidgets import QLabel\n"
        "                from PyQt5.QtCore import QTimer\n\n"
        "                self.ber_label = QLabel(\"Total Bits: 0 | Errors: 0 | BER: 0.00e+00 | SNR: 0.0 dB\")\n"
        "                self.ber_label.setStyleSheet(\"font-size: 16px; font-weight: bold; color: darkblue; padding: 8px; background-color: #f0f0f0; border: 1px solid #ccc;\")\n"
        "                self.top_block.top_grid_layout.addWidget(self.ber_label, 0, 0, 1, 5)\n\n"
        "                self.gui_timer = QTimer()\n"
        "                self.gui_timer.setInterval(200)\n"
        "                self.gui_timer.timeout.connect(self.update_gui)\n"
        "                self.gui_timer.start()\n"
        "                print(f\"[QPSK BER] Injected GUI Label. CSV logging to: {self.csv_path}\")\n"
        "            except Exception as e:\n"
        "                print(f\"[QPSK BER] GUI initialization notice: {e}\")\n\n"
        "    def update_gui(self):\n"
        "        if self.ber_label:\n"
        "            bits = self.total_bits\n"
        "            errs = self.total_errors\n"
        "            ber = errs / bits if bits > 0 else 0.0\n"
        "            snr = self.snr_db\n"
        "            color = \"darkgreen\" if (bits > 0 and ber < 1e-3) else \"darkblue\"\n"
        "            self.ber_label.setStyleSheet(f\"font-size: 16px; font-weight: bold; color: {color}; padding: 8px; background-color: #f0f0f0; border: 1px solid #ccc;\")\n"
        "            self.ber_label.setText(f\"Total Bits: {bits:,} | Errors: {errs:,} | BER: {ber:.2e} | SNR: {snr:.1f} dB\")\n\n"
        "    def work(self, input_items, output_items):\n"
        "        in_syms = input_items[0]\n"
        "        in_iq = input_items[1]\n"
        "        out_syms = output_items[0]\n\n"
        "        n_samps = min(len(in_syms), len(in_iq))\n"
        "        if n_samps == 0:\n"
        "            return 0\n\n"
        "        # 1. Decision-Directed SNR from IQ samples\n"
        "        iq_samps = in_iq[:n_samps]\n"
        "        reals = np.sign(iq_samps.real)\n"
        "        imags = np.sign(iq_samps.imag)\n"
        "        reals[reals == 0] = 1.0\n"
        "        imags[imags == 0] = 1.0\n"
        "        sliced = (reals + 1j * imags) * 0.70710678\n\n"
        "        noise = iq_samps - sliced\n"
        "        noise_p = float(np.mean(np.abs(noise)**2))\n"
        "        signal_p = float(np.mean(np.abs(sliced)**2))\n\n"
        "        alpha_ema = 0.05\n"
        "        self.avg_signal_power = (1.0 - alpha_ema) * self.avg_signal_power + alpha_ema * signal_p\n"
        "        self.avg_noise_power = (1.0 - alpha_ema) * self.avg_noise_power + alpha_ema * noise_p\n\n"
        "        if self.avg_noise_power > 1e-12:\n"
        "            raw_snr = 10.0 * np.log10(self.avg_signal_power / self.avg_noise_power)\n"
        "            self.snr_db = float(raw_snr)\n"
        "        else:\n"
        "            self.snr_db = 40.0\n\n"
        "        # 2. Fast Frame Sync & BER from symbols\n"
        "        syms = in_syms[:n_samps]\n"
        "        # Unpack symbols (0..3) to bits: 2 bits per symbol\n"
        "        bits = np.zeros(n_samps * 2, dtype=np.uint8)\n"
        "        bits[0::2] = (syms >> 1) & 1\n"
        "        bits[1::2] = syms & 1\n\n"
        "        buf = np.concatenate([self.bit_buffer, bits]) if len(self.bit_buffer) > 0 else bits\n"
        "        buf_len = len(buf)\n\n"
        "        idx = 0\n"
        "        while idx + 1000 <= buf_len:\n"
        "            window_bits = buf[idx : idx + 32]\n"
        "            mismatches = int(np.sum(window_bits != self.preamble_bits))\n"
        "            if mismatches <= 2:\n"
        "                rx_payload = buf[idx + 32 : idx + 1000]\n"
        "                errors = int(np.sum(rx_payload ^ self.payload_ref))\n"
        "                self.total_errors += errors\n"
        "                self.total_bits += 968\n"
        "                self.frame_count += 1\n\n"
        "                if self.frame_count % 20 == 0:\n"
        "                    ber = self.total_errors / self.total_bits if self.total_bits > 0 else 0.0\n"
        "                    print(f\"[QPSK BER] Frame: {self.frame_count} | Bits: {self.total_bits:,} | Errors: {self.total_errors} | BER: {ber:.2e} | SNR: {self.snr_db:.1f} dB\")\n\n"
        "                if self.csv_file:\n"
        "                    ber_curr = self.total_errors / self.total_bits if self.total_bits > 0 else 0.0\n"
        "                    self.csv_file.write(f\"{time.time():.3f},{self.frame_count},{self.total_bits},{self.total_errors},{ber_curr:.4e},{self.snr_db:.2f}\\n\")\n"
        "                    self.csv_file.flush()\n\n"
        "                idx += 1000\n"
        "            else:\n"
        "                idx += 1\n\n"
        "        self.bit_buffer = buf[idx:]\n"
        "        if len(self.bit_buffer) > 4000:\n"
        "            self.bit_buffer = self.bit_buffer[-1000:]\n\n"
        "        out_syms[:n_samps] = syms\n"
        "        return n_samps\n\n"
        "    def stop(self):\n"
        "        if hasattr(self, 'gui_timer') and self.gui_timer:\n"
        "            self.gui_timer.stop()\n"
        "        if hasattr(self, 'csv_file') and self.csv_file:\n"
        "            self.csv_file.close()\n"
        "        return True\n"
    )
    
    blocks = [
        {
            'name': 'center_freq',
            'id': 'variable',
            'parameters': {'comment': 'Carrier frequency (2.85 GHz)', 'value': '2850000000'},
            'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [296, 16.0], 'rotation': 0, 'state': 'enabled'}
        },
        {
            'name': 'excess_bw',
            'id': 'variable',
            'parameters': {'comment': 'RRC excess bandwidth / roll-off factor', 'value': '0.35'},
            'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [480, 16.0], 'rotation': 0, 'state': 'enabled'}
        },
        {
            'name': 'qpsk',
            'id': 'variable_constellation_rect',
            'parameters': {
                'comment': 'QPSK Gray Coded Constellation',
                'const_points': '[-0.707-0.707j, 0.707-0.707j, +0.707+0.707j, -0.707+0.707j]',
                'imag_sect': '2',
                'precision': '8',
                'real_sect': '2',
                'rot_sym': '4',
                'soft_dec_lut': None,
                'sym_map': '[0, 1, 3, 2]',
                'w_imag_sect': '1',
                'w_real_sect': '1'
            },
            'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [1448, 16.0], 'rotation': 0, 'state': 'enabled'}
        },
        {
            'name': 'samp_rate',
            'id': 'variable',
            'parameters': {'comment': 'Baseband sample rate (1.0 MSps)', 'value': '1000000'},
            'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [192, 16.0], 'rotation': 0, 'state': 'enabled'}
        },
        {
            'name': 'sps',
            'id': 'variable',
            'parameters': {'comment': 'Samples per symbol', 'value': '4'},
            'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [400, 16.0], 'rotation': 0, 'state': 'enabled'}
        },
        {
            'name': 'rx_gain',
            'id': 'variable_qtgui_range',
            'parameters': {
                'comment': 'Hardware RX Gain slider',
                'gui_hint': '0,0,1,1',
                'label': 'RX Gain (dB)',
                'min_len': '200',
                'orient': 'QtCore.Qt.Horizontal',
                'rangeType': 'float',
                'start': '0',
                'step': '1',
                'stop': '76',
                'value': '38',
                'widget': 'counter_slider'
            },
            'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [576, 16.0], 'rotation': 0, 'state': 'enabled'}
        },
        {
            'name': 'fll_loop_bw',
            'id': 'variable_qtgui_range',
            'parameters': {
                'comment': 'Coarse Frequency Offset Recovery BW',
                'gui_hint': '0,1,1,1',
                'label': 'FLL Band-Edge BW',
                'min_len': '200',
                'orient': 'QtCore.Qt.Horizontal',
                'rangeType': 'float',
                'start': '0.001',
                'step': '0.001',
                'stop': '0.1',
                'value': '0.02',
                'widget': 'counter_slider'
            },
            'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [736, 16.0], 'rotation': 0, 'state': 'enabled'}
        },
        {
            'name': 'timing_loop_bw',
            'id': 'variable_qtgui_range',
            'parameters': {
                'comment': 'Symbol Timing Recovery BW',
                'gui_hint': '0,2,1,1',
                'label': 'Symbol Sync Timing BW',
                'min_len': '200',
                'orient': 'QtCore.Qt.Horizontal',
                'rangeType': 'float',
                'start': '0.001',
                'step': '0.001',
                'stop': '0.1',
                'value': '0.03',
                'widget': 'counter_slider'
            },
            'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [896, 16.0], 'rotation': 0, 'state': 'enabled'}
        },
        {
            'name': 'costas_loop_bw',
            'id': 'variable_qtgui_range',
            'parameters': {
                'comment': 'Phase and Fine Frequency Lock BW',
                'gui_hint': '0,3,1,1',
                'label': 'Costas Loop BW',
                'min_len': '200',
                'orient': 'QtCore.Qt.Horizontal',
                'rangeType': 'float',
                'start': '0.001',
                'step': '0.001',
                'stop': '0.2',
                'value': '0.0628',
                'widget': 'counter_slider'
            },
            'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [1056, 16.0], 'rotation': 0, 'state': 'enabled'}
        },
        {
            'name': 'uhd_usrp_source_0',
            'id': 'uhd_usrp_source',
            'parameters': {
                'affinity': '',
                'alias': '',
                'ant0': '"RX2"',
                'ant1': '"RX2"',
                'bw0': 'samp_rate',
                'center_freq0': 'center_freq',
                'clock_rate': '0e0',
                'clock_source0': '',
                'comment': 'USRP B210 Hardware Receiver Source',
                'dc_offs0': '0+0j',
                'dc_offs_enb0': 'default',
                'dev_addr': '""',
                'dev_args': '',
                'gain0': 'rx_gain',
                'gain_type0': 'default',
                'iq_imbal0': '0+0j',
                'iq_imbal_enb0': 'default',
                'lo_export0': 'False',
                'lo_source0': 'internal',
                'maxoutbuf': '0',
                'minoutbuf': '0',
                'nchan': '1',
                'num_mboards': '1',
                'otw': '',
                'rx_agc0': 'Disabled',
                'samp_rate': 'samp_rate',
                'sd_spec0': '',
                'show_lo_controls': 'False',
                'start_time': '-1.0',
                'stream_args': '',
                'stream_chans': '[]',
                'sync': 'pc_clock',
                'time_source0': '',
                'type': 'fc32'
            },
            'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [16, 260.0], 'rotation': 0, 'state': 'enabled'}
        },
        {
            'name': 'analog_agc_xx_0',
            'id': 'analog_agc_xx',
            'parameters': {
                'affinity': '',
                'alias': '',
                'comment': 'Power Normalization / Dynamic Range Scaling',
                'gain': '1.0',
                'max_gain': '65536',
                'maxoutbuf': '0',
                'minoutbuf': '0',
                'rate': '1e-4',
                'reference': '1.0',
                'type': 'complex'
            },
            'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [280, 268.0], 'rotation': 0, 'state': 'enabled'}
        },
        {
            'name': 'digital_fll_band_edge_cc_0',
            'id': 'digital_fll_band_edge_cc',
            'parameters': {
                'affinity': '',
                'alias': '',
                'comment': 'Coarse Carrier Frequency Offset (CFO) Recovery',
                'filter_size': '45',
                'maxoutbuf': '0',
                'minoutbuf': '0',
                'rolloff': 'excess_bw',
                'samps_per_sym': 'sps',
                'type': 'cc',
                'w': 'fll_loop_bw'
            },
            'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [464, 260.0], 'rotation': 0, 'state': 'enabled'}
        },
        {
            'name': 'root_raised_cosine_filter_0',
            'id': 'root_raised_cosine_filter',
            'parameters': {
                'affinity': '',
                'alias': '',
                'alpha': 'excess_bw',
                'comment': 'Matched Filter (RRC, Alpha=0.35, Taps=11*SPS)',
                'decim': '1',
                'gain': '1.0',
                'interp': '1',
                'maxoutbuf': '0',
                'minoutbuf': '0',
                'ntaps': '11*sps',
                'samp_rate': 'samp_rate',
                'sym_rate': 'samp_rate/sps',
                'type': 'fir_filter_ccf'
            },
            'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [704, 268.0], 'rotation': 0, 'state': 'enabled'}
        },
        {
            'name': 'digital_symbol_sync_xx_0',
            'id': 'digital_symbol_sync_xx',
            'parameters': {
                'affinity': '',
                'alias': '',
                'comment': 'Symbol Timing Recovery (SPS -> 1 Sym/Samp)',
                'constellation': 'digital.constellation_qpsk().base()',
                'damping': '1.0',
                'loop_bw': 'timing_loop_bw',
                'max_dev': '1.5',
                'maxoutbuf': '0',
                'minoutbuf': '0',
                'nfilters': '128',
                'osps': '1',
                'pfb_mf_taps': '[]',
                'resamp_type': 'digital.IR_MMSE_8TAP',
                'sps': 'sps',
                'ted_gain': '1.0',
                'ted_type': 'digital.TED_SIGNAL_TIMES_SLOPE_ML',
                'type': 'cc'
            },
            'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [944, 252.0], 'rotation': 0, 'state': 'enabled'}
        },
        {
            'name': 'digital_costas_loop_cc_0',
            'id': 'digital_costas_loop_cc',
            'parameters': {
                'affinity': '',
                'alias': '',
                'comment': '4th-Order Costas Loop for QPSK Phase & Fine Frequency Lock',
                'maxoutbuf': '0',
                'minoutbuf': '0',
                'order': '4',
                'use_snr': 'False',
                'w': 'costas_loop_bw'
            },
            'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [1264, 296.0], 'rotation': 0, 'state': 'enabled'}
        },
        {
            'name': 'digital_constellation_decoder_cb_0',
            'id': 'digital_constellation_decoder_cb',
            'parameters': {
                'affinity': '',
                'alias': '',
                'comment': 'Slices complex symbols to QPSK indices (0,1,2,3)',
                'constellation': 'qpsk',
                'maxoutbuf': '0',
                'minoutbuf': '0'
            },
            'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [1504, 308.0], 'rotation': 0, 'state': 'enabled'}
        },
        {
            'name': 'digital_diff_decoder_bb_0',
            'id': 'digital_diff_decoder_bb',
            'parameters': {
                'affinity': '',
                'alias': '',
                'coding': 'digital.DIFF_DIFFERENTIAL',
                'comment': 'Differential Decoder (Modulus 4) resolves 90-deg phase ambiguity',
                'maxoutbuf': '0',
                'minoutbuf': '0',
                'modulus': '4'
            },
            'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [16, 508.0], 'rotation': 0, 'state': 'enabled'}
        },
        {
            'name': 'digital_map_bb_0',
            'id': 'digital_map_bb',
            'parameters': {
                'affinity': '',
                'alias': '',
                'comment': 'Inverse Gray Mapping',
                'map': '[0, 1, 3, 2]',
                'maxoutbuf': '0',
                'minoutbuf': '0'
            },
            'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [248, 516.0], 'rotation': 0, 'state': 'enabled'}
        },
        {
            'name': 'epy_block_1',
            'id': 'epy_block',
            'parameters': {
                '_source_code': epy_source,
                'affinity': '',
                'alias': '',
                'comment': 'Real-Time QPSK Frame Sync, BER & SNR Calculator, GUI Stats & CSV Logging',
                'maxoutbuf': '0',
                'minoutbuf': '0'
            },
            'states': {
                '_io_cache': "('QPSK BER & SNR Engine', 'blk', [], [('0', 'byte', 1), ('1', 'complex', 1)], [('0', 'byte', 1)], 'QPSK BER & SNR Calculator & CSV Logger', [])",
                'bus_sink': False,
                'bus_source': False,
                'bus_structure': None,
                'coordinate': [464, 504.0],
                'rotation': 0,
                'state': 'enabled'
            }
        },
        {
            'name': 'blocks_unpack_k_bits_bb_0',
            'id': 'blocks_unpack_k_bits_bb',
            'parameters': {
                'affinity': '',
                'alias': '',
                'comment': 'Unpacks 2 bits per QPSK symbol',
                'k': '2',
                'maxoutbuf': '0',
                'minoutbuf': '0'
            },
            'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [760, 516.0], 'rotation': 0, 'state': 'enabled'}
        },
        {
            'name': 'blocks_char_to_float_0',
            'id': 'blocks_char_to_float',
            'parameters': {'affinity': '', 'alias': '', 'comment': '', 'maxoutbuf': '0', 'minoutbuf': '0', 'scale': '1', 'vlen': '1'},
            'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [980, 516.0], 'rotation': 0, 'state': 'enabled'}
        },
        {
            'name': 'blocks_file_sink_0',
            'id': 'blocks_file_sink',
            'parameters': {'affinity': '', 'alias': '', 'append': 'False', 'comment': 'Capture unpacked bits for offline verification', 'file': 'rx_qpsk_bits.bin', 'type': 'byte', 'unbuffered': 'False', 'vlen': '1'},
            'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [980, 596.0], 'rotation': 0, 'state': 'enabled'}
        },
        {
            'name': 'qtgui_const_sink_x_0',
            'id': 'qtgui_const_sink_x',
            'parameters': {
                'affinity': '',
                'alias': '',
                'alpha1': '1.0',
                'alpha10': '1.0',
                'alpha2': '0.4',
                'alpha3': '1.0',
                'alpha4': '1.0',
                'alpha5': '1.0',
                'alpha6': '1.0',
                'alpha7': '1.0',
                'alpha8': '1.0',
                'alpha9': '1.0',
                'autoscale': 'False',
                'axislabels': 'True',
                'color1': '"blue"',
                'color10': '"red"',
                'color2': '"red"',
                'color3': '"red"',
                'color4': '"red"',
                'color5': '"red"',
                'color6': '"red"',
                'color7': '"red"',
                'color8': '"red"',
                'color9': '"red"',
                'comment': 'Visualizes Locked Constellation (Blue) vs Pre-Costas Constellation (Red)',
                'grid': 'True',
                'gui_hint': '1,0,1,1',
                'label1': '"Costas Phase Locked"',
                'label10': '',
                'label2': '"Post Symbol-Sync (Rotating)"',
                'label3': '',
                'label4': '',
                'label5': '',
                'label6': '',
                'label7': '',
                'label8': '',
                'label9': '',
                'legend': 'True',
                'marker1': '0',
                'marker10': '0',
                'marker2': '0',
                'marker3': '0',
                'marker4': '0',
                'marker5': '0',
                'marker6': '0',
                'marker7': '0',
                'marker8': '0',
                'marker9': '0',
                'name': '"QPSK Received Constellation"',
                'nconnections': '2',
                'size': '1024',
                'style1': '0',
                'style10': '0',
                'style2': '0',
                'style3': '0',
                'style4': '0',
                'style5': '0',
                'style6': '0',
                'style7': '0',
                'style8': '0',
                'style9': '0',
                'tr_chan': '0',
                'tr_level': '0.0',
                'tr_mode': 'qtgui.TRIG_MODE_FREE',
                'tr_slope': 'qtgui.TRIG_SLOPE_POS',
                'tr_tag': '""',
                'type': 'complex',
                'update_time': '0.10',
                'width1': '1',
                'width10': '1',
                'width2': '1',
                'width3': '1',
                'width4': '1',
                'width5': '1',
                'width6': '1',
                'width7': '1',
                'width8': '1',
                'width9': '1',
                'xmax': '2',
                'xmin': '-2',
                'ymax': '2',
                'ymin': '-2'
            },
            'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [1504, 180.0], 'rotation': 0, 'state': 'enabled'}
        },
        {
            'name': 'qtgui_freq_sink_x_0',
            'id': 'qtgui_freq_sink_x',
            'parameters': {
                'affinity': '',
                'alias': '',
                'alpha1': '1.0',
                'alpha10': '1.0',
                'alpha2': '1.0',
                'alpha3': '1.0',
                'alpha4': '1.0',
                'alpha5': '1.0',
                'alpha6': '1.0',
                'alpha7': '1.0',
                'alpha8': '1.0',
                'alpha9': '1.0',
                'autoscale': 'False',
                'average': '0.1',
                'axislabels': 'True',
                'bw': 'samp_rate',
                'color1': '"blue"',
                'color10': '"dark blue"',
                'color2': '"red"',
                'color3': '"green"',
                'color4': '"black"',
                'color5': '"cyan"',
                'color6': '"magenta"',
                'color7': '"yellow"',
                'color8': '"dark red"',
                'color9': '"dark green"',
                'comment': 'Visualizes RF spectrum',
                'ctrlpanel': 'False',
                'fc': 'center_freq',
                'fftsize': '2048',
                'freqhalf': 'True',
                'grid': 'True',
                'gui_hint': '1,1,1,1',
                'label': 'Relative Gain',
                'label1': '"Received RF Spectrum"',
                'label10': "''''''",
                'label2': "''''''",
                'label3': "''''''",
                'label4': "''''''",
                'label5': "''''''",
                'label6': "''''''",
                'label7': "''''''",
                'label8': "''''''",
                'label9': "''''''",
                'legend': 'True',
                'maxoutbuf': '0',
                'minoutbuf': '0',
                'name': '"RX Spectrum"',
                'nconnections': '1',
                'norm_window': 'False',
                'showports': 'False',
                'tr_chan': '0',
                'tr_level': '0.0',
                'tr_mode': 'qtgui.TRIG_MODE_FREE',
                'tr_tag': '""',
                'type': 'complex',
                'units': 'dB',
                'update_time': '0.10',
                'width1': '1',
                'width10': '1',
                'width2': '1',
                'width3': '1',
                'width4': '1',
                'width5': '1',
                'width6': '1',
                'width7': '1',
                'width8': '1',
                'width9': '1',
                'wintype': 'window.WIN_BLACKMAN_hARRIS',
                'ymax': '10',
                'ymin': '-100'
            },
            'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [280, 404.0], 'rotation': 0, 'state': 'enabled'}
        },
        {
            'name': 'qtgui_time_sink_x_0',
            'id': 'qtgui_time_sink_x',
            'parameters': {
                'affinity': '',
                'alias': '',
                'alpha1': '1.0',
                'alpha10': '1.0',
                'alpha2': '1.0',
                'alpha3': '1.0',
                'alpha4': '1.0',
                'alpha5': '1.0',
                'alpha6': '1.0',
                'alpha7': '1.0',
                'alpha8': '1.0',
                'alpha9': '1.0',
                'autoscale': 'False',
                'axislabels': 'True',
                'color1': 'blue',
                'color10': 'dark blue',
                'color2': 'red',
                'color3': 'green',
                'color4': 'black',
                'color5': 'cyan',
                'color6': 'magenta',
                'color7': 'yellow',
                'color8': 'dark red',
                'color9': 'dark green',
                'comment': 'Visualizes post-Costas I/Q components',
                'ctrlpanel': 'False',
                'entags': 'True',
                'grid': 'True',
                'gui_hint': '2,0,1,1',
                'label1': '"In-Phase (I)"',
                'label10': '',
                'label2': '"Quadrature (Q)"',
                'label3': '',
                'label4': '',
                'label5': '',
                'label6': '',
                'label7': '',
                'label8': '',
                'label9': '',
                'legend': 'True',
                'marker1': '-1',
                'marker10': '-1',
                'marker2': '-1',
                'marker3': '-1',
                'marker4': '-1',
                'marker5': '-1',
                'marker6': '-1',
                'marker7': '-1',
                'marker8': '-1',
                'marker9': '-1',
                'name': '"Demodulated I & Q Symbols"',
                'nconnections': '1',
                'size': '128',
                'srate': 'samp_rate / sps',
                'stemplot': 'False',
                'style1': '1',
                'style10': '1',
                'style2': '1',
                'style3': '1',
                'style4': '1',
                'style5': '1',
                'style6': '1',
                'style7': '1',
                'style8': '1',
                'style9': '1',
                'tr_chan': '0',
                'tr_delay': '0',
                'tr_level': '0.0',
                'tr_mode': 'qtgui.TRIG_MODE_FREE',
                'tr_slope': 'qtgui.TRIG_SLOPE_POS',
                'tr_tag': '""',
                'type': 'complex',
                'update_time': '0.10',
                'width1': '1',
                'width10': '1',
                'width2': '1',
                'width3': '1',
                'width4': '1',
                'width5': '1',
                'width6': '1',
                'width7': '1',
                'width8': '1',
                'width9': '1',
                'ylabel': 'Amplitude',
                'ymax': '1.5',
                'ymin': '-1.5',
                'yunit': '""'
            },
            'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [1504, 404.0], 'rotation': 0, 'state': 'enabled'}
        },
        {
            'name': 'qtgui_time_sink_x_0_0',
            'id': 'qtgui_time_sink_x',
            'parameters': {
                'affinity': '',
                'alias': '',
                'alpha1': '1.0',
                'alpha10': '1.0',
                'alpha2': '1.0',
                'alpha3': '1.0',
                'alpha4': '1.0',
                'alpha5': '1.0',
                'alpha6': '1.0',
                'alpha7': '1.0',
                'alpha8': '1.0',
                'alpha9': '1.0',
                'autoscale': 'True',
                'axislabels': 'True',
                'color1': 'dark blue',
                'color10': 'dark blue',
                'color2': 'red',
                'color3': 'green',
                'color4': 'black',
                'color5': 'cyan',
                'color6': 'magenta',
                'color7': 'yellow',
                'color8': 'dark red',
                'color9': 'dark green',
                'comment': 'Visualizes decoded bit stream',
                'ctrlpanel': 'False',
                'entags': 'True',
                'grid': 'True',
                'gui_hint': '2,1,1,1',
                'label1': '"Decoded QPSK Bits"',
                'label10': '',
                'label2': '',
                'label3': '',
                'label4': '',
                'label5': '',
                'label6': '',
                'label7': '',
                'label8': '',
                'label9': '',
                'legend': 'True',
                'marker1': '-1',
                'marker10': '-1',
                'marker2': '-1',
                'marker3': '-1',
                'marker4': '-1',
                'marker5': '-1',
                'marker6': '-1',
                'marker7': '-1',
                'marker8': '-1',
                'marker9': '-1',
                'name': '"Decoded QPSK Bitstream"',
                'nconnections': '1',
                'size': '128',
                'srate': '(samp_rate / sps) * 2',
                'stemplot': 'False',
                'style1': '1',
                'style10': '1',
                'style2': '1',
                'style3': '1',
                'style4': '1',
                'style5': '1',
                'style6': '1',
                'style7': '1',
                'style8': '1',
                'style9': '1',
                'tr_chan': '0',
                'tr_delay': '0',
                'tr_level': '0.0',
                'tr_mode': 'qtgui.TRIG_MODE_AUTO',
                'tr_slope': 'qtgui.TRIG_SLOPE_POS',
                'tr_tag': '""',
                'type': 'float',
                'update_time': '0.10',
                'width1': '1',
                'width10': '1',
                'width2': '1',
                'width3': '1',
                'width4': '1',
                'width5': '1',
                'width6': '1',
                'width7': '1',
                'width8': '1',
                'width9': '1',
                'ylabel': 'Bit Value',
                'ymax': '1.5',
                'ymin': '-0.5',
                'yunit': '""'
            },
            'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [1200, 508.0], 'rotation': 0, 'state': 'enabled'}
        }
    ]
    
    connections = [
        ['uhd_usrp_source_0', '0', 'analog_agc_xx_0', '0'],
        ['uhd_usrp_source_0', '0', 'qtgui_freq_sink_x_0', '0'],
        ['analog_agc_xx_0', '0', 'digital_fll_band_edge_cc_0', '0'],
        ['digital_fll_band_edge_cc_0', '0', 'root_raised_cosine_filter_0', '0'],
        ['root_raised_cosine_filter_0', '0', 'digital_symbol_sync_xx_0', '0'],
        ['digital_symbol_sync_xx_0', '0', 'digital_costas_loop_cc_0', '0'],
        ['digital_symbol_sync_xx_0', '0', 'qtgui_const_sink_x_0', '1'],
        ['digital_costas_loop_cc_0', '0', 'digital_constellation_decoder_cb_0', '0'],
        ['digital_costas_loop_cc_0', '0', 'epy_block_1', '1'],
        ['digital_costas_loop_cc_0', '0', 'qtgui_const_sink_x_0', '0'],
        ['digital_costas_loop_cc_0', '0', 'qtgui_time_sink_x_0', '0'],
        ['digital_constellation_decoder_cb_0', '0', 'digital_diff_decoder_bb_0', '0'],
        ['digital_diff_decoder_bb_0', '0', 'digital_map_bb_0', '0'],
        ['digital_map_bb_0', '0', 'epy_block_1', '0'],
        ['epy_block_1', '0', 'blocks_unpack_k_bits_bb_0', '0'],
        ['blocks_unpack_k_bits_bb_0', '0', 'blocks_file_sink_0', '0'],
        ['blocks_unpack_k_bits_bb_0', '0', 'blocks_char_to_float_0', '0'],
        ['blocks_char_to_float_0', '0', 'qtgui_time_sink_x_0_0', '0']
    ]
    
    qpsk_rx['blocks'] = blocks
    qpsk_rx['connections'] = connections
    qpsk_rx['metadata'] = {'file_format': 1, 'grc_version': '3.10.12.0'}
    
    with open(dst_qpsk, 'w', encoding='utf-8') as f:
        yaml.dump(qpsk_rx, f, default_flow_style=False, sort_keys=False)
        
    print(f'Successfully generated: {dst_qpsk}')

if __name__ == '__main__':
    generate_rx_qpsk()
