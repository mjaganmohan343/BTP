import yaml
import os

def generate_flowgraphs():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    miscellenious_dir = os.path.join(base_dir, 'miscellenious')
    
    # ---------------------------------------------------------
    # TX FLOWGRAPH
    # ---------------------------------------------------------
    tx_grc_path = os.path.join(miscellenious_dir, 'tx_qpsk_hardware_ber.grc')
    
    tx = {
        'options': {
            'parameters': {
                'author': 'pranav',
                'catch_exceptions': 'True',
                'category': 'Custom',
                'cmake_opt': '',
                'comment': '',
                'copyright': '',
                'description': 'QPSK BER Hardware Transmitter',
                'gen_cmake': 'On',
                'gen_linking': 'dynamic',
                'generate_options': 'qt_gui',
                'hier_block_src_path': '.:',
                'id': 'tx_qpsk_hardware_ber',
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
                'title': 'QPSK BER Hardware Transmitter',
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
        },
        'blocks': [
            {
                'name': 'Alpha', 'id': 'variable',
                'parameters': {'comment': '', 'value': '0.35'},
                'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [416, 4.0], 'rotation': 0, 'state': 'enabled'}
            },
            {
                'name': 'center_freq', 'id': 'variable',
                'parameters': {'comment': '', 'value': '2850000000'},
                'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [700, 16.0], 'rotation': 0, 'state': 'enabled'}
            },
            {
                'name': 'qpsk_const', 'id': 'variable_constellation',
                'parameters': {
                    'comment': '',
                    'const_points': '[-1-1j, -1+1j, 1+1j, 1-1j]',
                    'dims': '1',
                    'normalization': 'digital.constellation.AMPLITUDE_NORMALIZATION',
                    'npwr': '1.0',
                    'precision': '8',
                    'rot_sym': '4',
                    'soft_dec_lut': 'None',
                    'sym_map': '[0, 1, 3, 2]',
                    'type': 'calcdist'
                },
                'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [1184, 12.0], 'rotation': 0, 'state': 'true'}
            },
            {
                'name': 'samp_rate', 'id': 'variable',
                'parameters': {'comment': '', 'value': '1000000'},
                'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [216, 4.0], 'rotation': 0, 'state': 'enabled'}
            },
            {
                'name': 'sps', 'id': 'variable',
                'parameters': {'comment': '', 'value': '4'},
                'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [328, 4.0], 'rotation': 0, 'state': 'enabled'}
            },
            {
                'name': 'tx_gain', 'id': 'variable',
                'parameters': {'comment': '', 'value': '55'},
                'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [820, 16.0], 'rotation': 0, 'state': 'enabled'}
            },
            {
                'name': 'analog_random_source_x_0', 'id': 'analog_random_source_x',
                'parameters': {
                    'affinity': '', 'alias': '', 'comment': '',
                    'max': '255', 'maxoutbuf': '0', 'min': '0', 'minoutbuf': '0',
                    'num_samps': '10000', 'repeat': 'True', 'type': 'byte'
                },
                'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [16, 220.0], 'rotation': 0, 'state': 'enabled'}
            },
            {
                'name': 'digital_constellation_modulator_0', 'id': 'digital_constellation_modulator',
                'parameters': {
                    'affinity': '', 'alias': '', 'comment': 'Maps bytes to QPSK, applies RRC',
                    'constellation': 'qpsk_const', 'differential': 'True', 'excess_bw': 'Alpha',
                    'log': 'False', 'maxoutbuf': '0', 'minoutbuf': '0', 'samples_per_symbol': 'sps',
                    'truncate': 'False', 'verbose': 'False'
                },
                'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [432, 228.0], 'rotation': 0, 'state': 'enabled'}
            },
            {
                'name': 'epy_block_0', 'id': 'epy_block',
                'parameters': {
                    '_source_code': (
                        "import numpy as np\n"
                        "from gnuradio import gr\n\n"
                        "class blk(gr.basic_block):\n"
                        "    \"\"\"BER Frame Generator & Preamble Inserter\"\"\"\n"
                        "    def __init__(self, packet_len=1000):\n"
                        "        gr.basic_block.__init__(\n"
                        "            self,\n"
                        "            name='BER Frame Generator',\n"
                        "            in_sig=[np.uint8],\n"
                        "            out_sig=[np.uint8]\n"
                        "        )\n"
                        "        self.packet_len = packet_len\n"
                        "        # QPSK has 4 symbols (2 bits). Let's use a 32-symbol preamble\n"
                        "        self.preamble = np.array([3, 3, 3, 3, 3, 0, 0, 3, 3, 0, 3, 0, 3, 3, 3, 3, 3, 3, 0, 0, 3, 3, 0, 3, 0, 3, 3, 0, 0, 3, 0, 3], dtype=np.uint8)\n"
                        "        np.random.seed(42)\n"
                        "        self.payload_ref = np.random.randint(0, 4, size=968, dtype=np.uint8)\n"
                        "        self.packet = np.concatenate([self.preamble, self.payload_ref])\n"
                        "        \n"
                        "        # Pack 2-bit symbols into 8-bit bytes (4 symbols per byte)\n"
                        "        self.packed_packet = np.zeros(len(self.packet) // 4, dtype=np.uint8)\n"
                        "        for i in range(len(self.packed_packet)):\n"
                        "            self.packed_packet[i] = (self.packet[4*i] << 6) | (self.packet[4*i+1] << 4) | (self.packet[4*i+2] << 2) | self.packet[4*i+3]\n"
                        "            \n"
                        "        self.ptr = 0\n\n"
                        "    def general_work(self, input_items, output_items):\n"
                        "        in0 = input_items[0]\n"
                        "        out = output_items[0]\n"
                        "        n_out = len(out)\n"
                        "        written = 0\n"
                        "        read = min(len(in0), n_out)\n"
                        "        \n"
                        "        while written < read:\n"
                        "            rem = len(self.packed_packet) - self.ptr\n"
                        "            to_write = min(rem, read - written)\n"
                        "            out[written:written+to_write] = self.packed_packet[self.ptr:self.ptr+to_write]\n"
                        "            self.ptr = (self.ptr + to_write) % len(self.packed_packet)\n"
                        "            written += to_write\n"
                        "            \n"
                        "        self.consume(0, read)\n"
                        "        return written\n"
                    ),
                    'affinity': '', 'alias': '', 'comment': '', 'maxoutbuf': '0', 'minoutbuf': '0', 'packet_len': '1000'
                },
                'states': {
                    '_io_cache': "('BER Frame Generator', 'blk', [('packet_len', '1000')], [('0', 'byte', 1)], [('0', 'byte', 1)], 'BER Frame Generator & Preamble Inserter', ['packet_len'])",
                    'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [224, 192.0], 'rotation': 0, 'state': 'enabled'
                }
            },
            {
                'name': 'qtgui_const_sink_x_0', 'id': 'qtgui_const_sink_x',
                'parameters': {
                    'affinity': '', 'alias': '', 'alpha1': '1.0', 'alpha10': '1.0', 'alpha2': '1.0', 'alpha3': '1.0',
                    'alpha4': '1.0', 'alpha5': '1.0', 'alpha6': '1.0', 'alpha7': '1.0', 'alpha8': '1.0', 'alpha9': '1.0',
                    'autoscale': 'False', 'axislabels': 'True', 'color1': '"blue"', 'color10': '"dark blue"',
                    'color2': '"red"', 'color3': '"green"', 'color4': '"black"', 'color5': '"cyan"', 'color6': '"magenta"',
                    'color7': '"yellow"', 'color8': '"dark red"', 'color9': '"dark green"', 'comment': '', 'grid': 'False',
                    'gui_hint': '', 'label1': '', 'label10': '', 'label2': '', 'label3': '', 'label4': '', 'label5': '',
                    'label6': '', 'label7': '', 'label8': '', 'label9': '', 'legend': 'True', 'marker1': '0',
                    'marker10': '0', 'marker2': '0', 'marker3': '0', 'marker4': '0', 'marker5': '0', 'marker6': '0',
                    'marker7': '0', 'marker8': '0', 'marker9': '0', 'name': '""', 'nconnections': '1', 'size': '1024',
                    'style1': '0', 'style10': '0', 'style2': '0', 'style3': '0', 'style4': '0', 'style5': '0',
                    'style6': '0', 'style7': '0', 'style8': '0', 'style9': '0', 'tr_chan': '0', 'tr_level': '0.0',
                    'tr_mode': 'qtgui.TRIG_MODE_FREE', 'tr_slope': 'qtgui.TRIG_SLOPE_POS', 'tr_tag': '""', 'type': 'complex',
                    'update_time': '0.10', 'width1': '1', 'width10': '1', 'width2': '1', 'width3': '1', 'width4': '1',
                    'width5': '1', 'width6': '1', 'width7': '1', 'width8': '1', 'width9': '1', 'xmax': '2', 'xmin': '-2',
                    'ymax': '2', 'ymin': '-2'
                },
                'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [920, 436.0], 'rotation': 0, 'state': 'enabled'}
            },
            {
                'name': 'uhd_usrp_sink_0', 'id': 'uhd_usrp_sink',
                'parameters': {
                    'affinity': '', 'alias': '', 'ant0': '"TX/RX"',
                    'bw0': '0', 'center_freq0': 'center_freq', 'clock_rate': '0e0',
                    'clock_source0': '', 'comment': '', 'dev_addr': '""', 'dev_args': '',
                    'gain0': 'tx_gain', 'gain_type0': 'default', 'len_tag_name': '""',
                    'lo_export0': 'False', 'lo_source0': 'internal', 'maxoutbuf': '0',
                    'minoutbuf': '0', 'nchan': '1', 'num_mboards': '1', 'otw': '',
                    'samp_rate': 'samp_rate', 'sd_spec0': '', 'show_lo_controls': 'False',
                    'start_time': '-1.0', 'stream_args': '', 'stream_chans': '[]',
                    'sync': 'pc_clock', 'time_source0': '', 'type': 'fc32'
                },
                'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [824, 224.0], 'rotation': 0, 'state': 'enabled'}
            }
        ],
        'connections': [
            ['analog_random_source_x_0', '0', 'epy_block_0', '0'],
            ['digital_constellation_modulator_0', '0', 'qtgui_const_sink_x_0', '0'],
            ['digital_constellation_modulator_0', '0', 'uhd_usrp_sink_0', '0'],
            ['epy_block_0', '0', 'digital_constellation_modulator_0', '0']
        ],
        'metadata': {'file_format': 1, 'grc_version': '3.10.12.0'}
    }
    
    with open(tx_grc_path, 'w', encoding='utf-8') as f:
        yaml.dump(tx, f, default_flow_style=False, sort_keys=False)
    
    # ---------------------------------------------------------
    # RX FLOWGRAPH
    # ---------------------------------------------------------
    rx_grc_path = os.path.join(miscellenious_dir, 'rx_qpsk_hardware_ber.grc')
    
    rx = {
        'options': {
            'parameters': {
                'author': 'pranav',
                'catch_exceptions': 'True',
                'category': 'Custom',
                'cmake_opt': '',
                'comment': '',
                'copyright': '',
                'description': 'QPSK Hardware Receiver',
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
                'title': 'QPSK Hardware Receiver',
                'window_size': '2000,2000'
            },
            'states': {
                'bus_sink': False, 'bus_source': False, 'bus_structure': None,
                'coordinate': [16, 16.0], 'rotation': 0, 'state': 'enabled'
            }
        },
        'blocks': [
            {
                'name': 'Alpha', 'id': 'variable',
                'parameters': {'comment': '', 'value': '0.35'},
                'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [416, 4.0], 'rotation': 0, 'state': 'enabled'}
            },
            {
                'name': 'center_freq', 'id': 'variable',
                'parameters': {'comment': '', 'value': '2850000000'},
                'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [224, 84.0], 'rotation': 0, 'state': 'enabled'}
            },
            {
                'name': 'cma_algo', 'id': 'variable_adaptive_algorithm',
                'parameters': {
                    'comment': '', 'cons': 'qpsk_const', 'delta': '10.0', 'ffactor': '0.99',
                    'modulus': '1', 'step_size': 'eq_gain', 'type': 'cma'
                },
                'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [1264, 12.0], 'rotation': 0, 'state': 'enabled'}
            },
            {
                'name': 'eq_gain', 'id': 'variable_qtgui_range',
                'parameters': {
                    'comment': '', 'gui_hint': '', 'label': 'CMA EQ Gain', 'min_len': '200', 'orient': 'QtCore.Qt.Horizontal', 'rangeType': 'float', 'start': '0.0001', 'step': '0.0001', 'stop': '0.01', 'value': '0.0005', 'widget': 'counter_slider'
                },
                'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [1096, 20.0], 'rotation': 0, 'state': 'enabled'}
            },
            {
                'name': 'qpsk_const', 'id': 'variable_constellation',
                'parameters': {
                    'comment': '',
                    'const_points': '[-1-1j, -1+1j, 1+1j, 1-1j]',
                    'dims': '1',
                    'normalization': 'digital.constellation.AMPLITUDE_NORMALIZATION',
                    'npwr': '1.0',
                    'precision': '8',
                    'rot_sym': '4',
                    'soft_dec_lut': 'None',
                    'sym_map': '[0, 1, 3, 2]',
                    'type': 'calcdist'
                },
                'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [1432, 4.0], 'rotation': 0, 'state': 'true'}
            },
            {
                'name': 'nfilts', 'id': 'variable',
                'parameters': {'comment': '', 'value': '32'},
                'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [520, 4.0], 'rotation': 0, 'state': 'enabled'}
            },
            {
                'name': 'rrc_taps', 'id': 'variable',
                'parameters': {'comment': '', 'value': 'firdes.root_raised_cosine(nfilts, nfilts, 1.0/float(sps), Alpha, 11*sps*nfilts)'},
                'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [608, 4.0], 'rotation': 0, 'state': 'enabled'}
            },
            {
                'name': 'rx_gain', 'id': 'variable_qtgui_range',
                'parameters': {'comment': '', 'gui_hint': '', 'label': 'RX Gain', 'min_len': '200', 'orient': 'QtCore.Qt.Horizontal', 'rangeType': 'float', 'start': '0', 'step': '1', 'stop': '76', 'value': '38', 'widget': 'counter_slider'},
                'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [984, 4.0], 'rotation': 0, 'state': 'enabled'}
            },
            {
                'name': 'samp_rate', 'id': 'variable',
                'parameters': {'comment': '', 'value': '1000000'},
                'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [216, 4.0], 'rotation': 0, 'state': 'enabled'}
            },
            {
                'name': 'sps', 'id': 'variable',
                'parameters': {'comment': '', 'value': '4'},
                'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [328, 4.0], 'rotation': 0, 'state': 'enabled'}
            },
            {
                'name': 'timing_loop_bw', 'id': 'variable_qtgui_range',
                'parameters': {'comment': '', 'gui_hint': '', 'label': 'Timing Loop BW', 'min_len': '200', 'orient': 'QtCore.Qt.Horizontal', 'rangeType': 'float', 'start': '0.001', 'step': '0.001', 'stop': '0.1', 'value': '0.03', 'widget': 'counter_slider'},
                'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [768, 20.0], 'rotation': 0, 'state': 'enabled'}
            },
            {
                'name': 'costas_loop_bw', 'id': 'variable_qtgui_range',
                'parameters': {'comment': '', 'gui_hint': '', 'label': 'Costas Loop BW', 'min_len': '200', 'orient': 'QtCore.Qt.Horizontal', 'rangeType': 'float', 'start': '0.001', 'step': '0.001', 'stop': '0.2', 'value': '0.0628', 'widget': 'counter_slider'},
                'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [1352, 92.0], 'rotation': 0, 'state': 'enabled'}
            },
            {
                'name': 'uhd_usrp_source_0', 'id': 'uhd_usrp_source',
                'parameters': {
                    'affinity': '', 'alias': '', 'ant0': '"RX2"', 'bw0': 'samp_rate', 'center_freq0': 'center_freq',
                    'clock_rate': '0e0', 'clock_source0': '', 'comment': '', 'dc_offs0': '0+0j', 'dc_offs_enb0': 'default',
                    'dev_addr': '""', 'dev_args': '', 'gain0': 'rx_gain', 'gain_type0': 'default', 'iq_imbal0': '0+0j',
                    'iq_imbal_enb0': 'default', 'lo_export0': 'False', 'lo_source0': 'internal', 'maxoutbuf': '0', 'minoutbuf': '0',
                    'nchan': '1', 'num_mboards': '1', 'otw': '', 'rx_agc0': 'Disabled', 'samp_rate': 'samp_rate', 'sd_spec0': '',
                    'show_lo_controls': 'False', 'start_time': '-1.0', 'stream_args': '', 'stream_chans': '[]', 'sync': 'pc_clock',
                    'time_source0': '', 'type': 'fc32'
                },
                'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [16, 212.0], 'rotation': 0, 'state': 'enabled'}
            },
            {
                'name': 'digital_fll_band_edge_cc_0', 'id': 'digital_fll_band_edge_cc',
                'parameters': {
                    'affinity': '', 'alias': '', 'comment': '', 'filter_size': '45', 'maxoutbuf': '0', 'minoutbuf': '0',
                    'rolloff': 'Alpha', 'samps_per_sym': 'sps', 'type': 'cc', 'w': '0.02'
                },
                'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [320, 216.0], 'rotation': 0, 'state': 'enabled'}
            },
            {
                'name': 'digital_symbol_sync_xx_0', 'id': 'digital_symbol_sync_xx',
                'parameters': {
                    'affinity': '', 'alias': '', 'comment': '', 'constellation': 'digital.constellation_qpsk().base()',
                    'damping': '1.0', 'loop_bw': 'timing_loop_bw', 'max_dev': '1.5', 'maxoutbuf': '0', 'minoutbuf': '0',
                    'nfilters': 'nfilts', 'osps': '1', 'pfb_mf_taps': 'rrc_taps', 'resamp_type': 'digital.IR_PFB_MF',
                    'sps': 'sps', 'ted_gain': '1.0', 'ted_type': 'digital.TED_SIGNAL_TIMES_SLOPE_ML', 'type': 'cc'
                },
                'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [616, 212.0], 'rotation': 0, 'state': 'enabled'}
            },
            {
                'name': 'digital_linear_equalizer_0', 'id': 'digital_linear_equalizer',
                'parameters': {
                    'adapt_after_training': 'True', 'affinity': '', 'alg': 'cma_algo', 'alias': '', 'comment': '',
                    'maxoutbuf': '0', 'minoutbuf': '0', 'num_taps': '15', 'sps': '1', 'training_sequence': '[]', 'training_start_tag': '""'
                },
                'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [936, 240.0], 'rotation': 0, 'state': 'enabled'}
            },
            {
                'name': 'digital_costas_loop_cc_0', 'id': 'digital_costas_loop_cc',
                'parameters': {
                    'affinity': '', 'alias': '', 'comment': '', 'maxoutbuf': '0', 'minoutbuf': '0', 'order': '4', 'use_snr': 'False', 'w': 'costas_loop_bw'
                },
                'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [1208, 248.0], 'rotation': 0, 'state': 'enabled'}
            },
            {
                'name': 'digital_constellation_decoder_cb_0', 'id': 'digital_constellation_decoder_cb',
                'parameters': {
                    'affinity': '', 'alias': '', 'comment': '', 'constellation': 'qpsk_const', 'maxoutbuf': '0', 'minoutbuf': '0'
                },
                'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [1472, 256.0], 'rotation': 0, 'state': 'enabled'}
            },
            {
                'name': 'digital_diff_decoder_bb_0', 'id': 'digital_diff_decoder_bb',
                'parameters': {
                    'affinity': '', 'alias': '', 'coding': 'digital.DIFF_DIFFERENTIAL', 'comment': '', 'maxoutbuf': '0', 'minoutbuf': '0', 'modulus': '4'
                },
                'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [1728, 244.0], 'rotation': 0, 'state': 'enabled'}
            },
            {
                'name': 'digital_map_bb_0', 'id': 'digital_map_bb',
                'parameters': {
                    'affinity': '', 'alias': '', 'comment': '', 'map': '[0, 1, 3, 2]', 'maxoutbuf': '0', 'minoutbuf': '0'
                },
                'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [1928, 256.0], 'rotation': 0, 'state': 'enabled'}
            },
            {
                'name': 'epy_block_1', 'id': 'epy_block',
                'parameters': {
                    '_source_code': (
                        "import numpy as np\n"
                        "from gnuradio import gr\n"
                        "import time\n"
                        "import os\n"
                        "import inspect\n\n"
                        "class blk(gr.sync_block):\n"
                        "    \"\"\"Robust QPSK BER Calculator & CSV Logger (Frame Jump Parser)\"\"\"\n"
                        "    def __init__(self):\n"
                        "        gr.sync_block.__init__(\n"
                        "            self,\n"
                        "            name='BER Calculator & CSV Logger',\n"
                        "            in_sig=[np.uint8],\n"
                        "            out_sig=[]\n"
                        "        )\n"
                        "        self.preamble = np.array([3, 3, 3, 3, 3, 0, 0, 3, 3, 0, 3, 0, 3, 3, 3, 3, 3, 3, 0, 0, 3, 3, 0, 3, 0, 3, 3, 0, 0, 3, 0, 3], dtype=np.uint8)\n"
                        "        np.random.seed(42)\n"
                        "        self.payload_ref = np.random.randint(0, 4, size=968, dtype=np.uint8)\n"
                        "        \n"
                        "        # Precompute 4x4 Hamming distance LUT for QPSK (2 bits)\n"
                        "        self.LUT = np.zeros((4, 4), dtype=np.uint8)\n"
                        "        for i in range(4):\n"
                        "            for j in range(4):\n"
                        "                self.LUT[i, j] = bin(i ^ j).count('1')\n"
                        "                \n"
                        "        self.buffer = np.array([], dtype=np.uint8)\n"
                        "        self.total_bits = 0\n"
                        "        self.total_errors = 0\n"
                        "        self.frame_count = 0\n"
                        "        self.printed_debug = False\n"
                        "        \n"
                        "        dir_path = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else '.'\n"
                        "        self.csv_path = os.path.join(dir_path, 'ber_log_qpsk.csv')\n"
                        "        self.csv_file = open(self.csv_path, 'w')\n"
                        "        self.csv_file.write(\"timestamp,frame,total_bits,total_errors,ber,snr_db\\n\")\n"
                        "        self.csv_file.flush()\n\n"
                        "        # GUI Label Injection\n"
                        "        self.top_block = None\n"
                        "        self.ber_label = None\n"
                        "        self.gui_timer = None\n"
                        "        \n"
                        "        for frame_info in inspect.stack():\n"
                        "            frame = frame_info.frame\n"
                        "            if 'self' in frame.f_locals:\n"
                        "                val = frame.f_locals['self']\n"
                        "                if hasattr(val, 'top_grid_layout'):\n"
                        "                    self.top_block = val\n"
                        "                    break\n"
                        "                    \n"
                        "        if self.top_block:\n"
                        "            try:\n"
                        "                from PyQt5.QtWidgets import QLabel\n"
                        "                from PyQt5.QtCore import QTimer\n"
                        "                \n"
                        "                self.ber_label = QLabel(\"Total Bits: 0 | Errors: 0 | BER: 0.00e+00 | SNR: 0.0 dB\")\n"
                        "                self.ber_label.setStyleSheet(\"font-size: 16px; font-weight: bold; color: blue; padding: 10px;\")\n"
                        "                self.top_block.top_grid_layout.addWidget(self.ber_label, 0, 0, 1, 2)\n"
                        "                \n"
                        "                self.gui_timer = QTimer()\n"
                        "                self.gui_timer.setInterval(200)\n"
                        "                self.gui_timer.timeout.connect(self.update_gui)\n"
                        "                self.gui_timer.start()\n"
                        "                print(f\"[BER] Successfully injected GUI label and timer. CSV logging to: {self.csv_path}\")\n"
                        "            except Exception as e:\n"
                        "                print(f\"[BER] Failed to initialize GUI components: {e}\")\n\n"
                        "    def update_gui(self):\n"
                        "        if self.ber_label and self.top_block:\n"
                        "            bits = self.total_bits\n"
                        "            errs = self.total_errors\n"
                        "            ber = errs / bits if bits > 0 else 0\n"
                        "            \n"
                        "            self.ber_label.setText(f\"Total Bits: {bits:,} | Errors: {errs:,} | BER: {ber:.2e}\")\n\n"
                        "    def work(self, input_items, output_items):\n"
                        "        in0 = input_items[0]\n"
                        "        \n"
                        "        data = np.concatenate([self.buffer, in0])\n"
                        "        \n"
                        "        idx = 0\n"
                        "        while idx + 1000 <= len(data):\n"
                        "            window = data[idx : idx + 32]\n"
                        "            mismatches = int(np.sum(window != self.preamble))\n"
                        "            \n"
                        "            if mismatches <= 2:\n"
                        "                rx_pay = data[idx + 32 : idx + 1000]\n"
                        "                errors = int(np.sum(self.LUT[rx_pay, self.payload_ref]))\n"
                        "                self.total_errors += errors\n"
                        "                self.total_bits += 968 * 2\n"
                        "                self.frame_count += 1\n"
                        "                \n"
                        "                if self.frame_count % 50 == 0:\n"
                        "                    ber = self.total_errors / self.total_bits if self.total_bits > 0 else 0\n"
                        "                    print(f\"[BER] Frame: {self.frame_count} | Total Bits: {self.total_bits:,} | Errors: {self.total_errors:,} | BER: {ber:.2e}\")\n"
                        "                \n"
                        "                self.csv_file.write(f\"{time.time()},{self.frame_count},{self.total_bits},{self.total_errors},{self.total_errors/self.total_bits:.2e}\\n\")\n"
                        "                self.csv_file.flush()\n"
                        "                \n"
                        "                idx += 1000\n"
                        "            else:\n"
                        "                idx += 1\n"
                        "                \n"
                        "        self.buffer = data[idx:]\n"
                        "        return len(in0)\n\n"
                        "    def stop(self):\n"
                        "        if hasattr(self, 'gui_timer') and self.gui_timer:\n"
                        "            self.gui_timer.stop()\n"
                        "        if hasattr(self, 'csv_file') and self.csv_file:\n"
                        "            self.csv_file.close()\n"
                        "        return True\n"
                    ),
                    'affinity': '', 'alias': '', 'comment': '', 'maxoutbuf': '0', 'minoutbuf': '0'
                },
                'states': {
                    '_io_cache': "('BER Calculator & CSV Logger', 'blk', [], [('0', 'byte', 1)], [], 'Phase Ambiguity Resolver', [])",
                    'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [2136, 248.0], 'rotation': 0, 'state': 'enabled'
                }
            },
            {
                'name': 'qtgui_const_sink_x_0', 'id': 'qtgui_const_sink_x',
                'parameters': {
                    'affinity': '', 'alias': '', 'alpha1': '1.0', 'alpha10': '1.0', 'alpha2': '1.0', 'alpha3': '1.0',
                    'alpha4': '1.0', 'alpha5': '1.0', 'alpha6': '1.0', 'alpha7': '1.0', 'alpha8': '1.0', 'alpha9': '1.0',
                    'autoscale': 'False', 'axislabels': 'True', 'color1': '"blue"', 'color10': '"dark blue"',
                    'color2': '"red"', 'color3': '"green"', 'color4': '"black"', 'color5': '"cyan"', 'color6': '"magenta"',
                    'color7': '"yellow"', 'color8': '"dark red"', 'color9': '"dark green"', 'comment': '', 'grid': 'False',
                    'gui_hint': '', 'label1': '', 'label10': '', 'label2': '', 'label3': '', 'label4': '', 'label5': '',
                    'label6': '', 'label7': '', 'label8': '', 'label9': '', 'legend': 'True', 'marker1': '0', 'marker10': '0',
                    'marker2': '0', 'marker3': '0', 'marker4': '0', 'marker5': '0', 'marker6': '0', 'marker7': '0', 'marker8': '0',
                    'marker9': '0', 'name': '""', 'nconnections': '1', 'size': '1024', 'style1': '0', 'style10': '0', 'style2': '0',
                    'style3': '0', 'style4': '0', 'style5': '0', 'style6': '0', 'style7': '0', 'style8': '0', 'style9': '0',
                    'tr_chan': '0', 'tr_level': '0.0', 'tr_mode': 'qtgui.TRIG_MODE_FREE', 'tr_slope': 'qtgui.TRIG_SLOPE_POS',
                    'tr_tag': '""', 'type': 'complex', 'update_time': '0.10', 'width1': '1', 'width10': '1', 'width2': '1',
                    'width3': '1', 'width4': '1', 'width5': '1', 'width6': '1', 'width7': '1', 'width8': '1', 'width9': '1',
                    'xmax': '2', 'xmin': '-2', 'ymax': '2', 'ymin': '-2'
                },
                'states': {'bus_sink': False, 'bus_source': False, 'bus_structure': None, 'coordinate': [1472, 364.0], 'rotation': 0, 'state': 'enabled'}
            }
        ],
        'connections': [
            ['uhd_usrp_source_0', '0', 'digital_fll_band_edge_cc_0', '0'],
            ['digital_fll_band_edge_cc_0', '0', 'digital_symbol_sync_xx_0', '0'],
            ['digital_symbol_sync_xx_0', '0', 'digital_linear_equalizer_0', '0'],
            ['digital_linear_equalizer_0', '0', 'digital_costas_loop_cc_0', '0'],
            ['digital_costas_loop_cc_0', '0', 'digital_constellation_decoder_cb_0', '0'],
            ['digital_costas_loop_cc_0', '0', 'qtgui_const_sink_x_0', '0'],
            ['digital_constellation_decoder_cb_0', '0', 'digital_diff_decoder_bb_0', '0'],
            ['digital_diff_decoder_bb_0', '0', 'digital_map_bb_0', '0'],
            ['digital_map_bb_0', '0', 'epy_block_1', '0']
        ],
        'metadata': {'file_format': 1, 'grc_version': '3.10.12.0'}
    }
    
    with open(rx_grc_path, 'w', encoding='utf-8') as f:
        yaml.dump(rx, f, default_flow_style=False, sort_keys=False)
        
    print(f'Successfully generated TX and RX QPSK flowgraphs.')

if __name__ == '__main__':
    generate_flowgraphs()
