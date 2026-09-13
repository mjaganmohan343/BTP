import yaml
import os

def generate():
    # Load the original 16_HQAM.grc
    with open('16_HQAM.grc', 'r') as f:
        sim_data = yaml.safe_load(f)

    # Helper function to find a block by name/id
    def find_block(blocks, name):
        for b in blocks:
            if b.get('name') == name:
                return b
        return None

    # Helper function to copy a block
    def copy_block(block):
        import copy
        return copy.deepcopy(block)

    # We need the USRP blocks from noma_tx1.grc and noma_rx1.grc
    # Let's load them to extract the exact USRP sink and source blocks
    with open('../gnuradi/noma_tx1.grc', 'r') as f:
        noma_tx = yaml.safe_load(f)
    usrp_sink_sim = find_block(noma_tx['blocks'], 'uhd_usrp_sink_0')

    with open('../gnuradi/noma_rx1.grc', 'r') as f:
        noma_rx = yaml.safe_load(f)
    usrp_source_sim = find_block(noma_rx['blocks'], 'uhd_usrp_source_0')

    # Ensure output folder exists
    os.makedirs('hardware_test', exist_ok=True)

    # ========================================================
    # 1. CREATE TX FLOWGRAPH
    # ========================================================
    tx_blocks = []
    
    # Options block
    tx_options = copy_block(sim_data['options'])
    tx_options['parameters']['id'] = 'tx_hardware'
    tx_options['parameters']['title'] = '16-HQAM Hardware Transmitter'

    # Parameters & Variables
    tx_blocks.append(find_block(sim_data['blocks'], 'Alpha'))
    tx_blocks.append(find_block(sim_data['blocks'], 'hqam_const'))
    tx_blocks.append(find_block(sim_data['blocks'], 'sps'))
    
    samp_rate_var = copy_block(find_block(sim_data['blocks'], 'samp_rate'))
    samp_rate_var['parameters']['value'] = '1000000' # 1 Msps
    tx_blocks.append(samp_rate_var)

    # Add hardware specific variables
    center_freq_var = {
        'name': 'center_freq',
        'id': 'variable',
        'parameters': {
            'comment': '',
            'value': '2450000000' # 2.45 GHz
        },
        'states': {
            'bus_sink': False,
            'bus_source': False,
            'bus_structure': None,
            'coordinate': [700, 16.0],
            'rotation': 0,
            'state': 'enabled'
        }
    }
    tx_blocks.append(center_freq_var)

    tx_gain_var = {
        'name': 'tx_gain',
        'id': 'variable',
        'parameters': {
            'comment': '',
            'value': '40' # 40 dB Tx Gain
        },
        'states': {
            'bus_sink': False,
            'bus_source': False,
            'bus_structure': None,
            'coordinate': [820, 16.0],
            'rotation': 0,
            'state': 'enabled'
        }
    }
    tx_blocks.append(tx_gain_var)

    # Core TX DSP Blocks
    rand_src = copy_block(find_block(sim_data['blocks'], 'analog_random_source_x_0'))
    rand_src['states']['coordinate'] = [16, 220.0]
    tx_blocks.append(rand_src)

    # Modulator (Ensure differential is False)
    const_mod = copy_block(find_block(sim_data['blocks'], 'digital_constellation_modulator_0'))
    const_mod['states']['coordinate'] = [216, 220.0]
    const_mod['parameters']['differential'] = 'False'
    tx_blocks.append(const_mod)

    # USRP Sink
    usrp_sink = copy_block(usrp_sink_sim)
    usrp_sink['states']['coordinate'] = [480, 220.0]
    usrp_sink['parameters']['samp_rate'] = 'samp_rate'
    usrp_sink['parameters']['center_freq0'] = 'center_freq'
    usrp_sink['parameters']['gain0'] = 'tx_gain'
    usrp_sink['parameters']['ant0'] = '"TX/RX"'
    tx_blocks.append(usrp_sink)

    tx_connections = [
        ['analog_random_source_x_0', '0', 'digital_constellation_modulator_0', '0'],
        ['digital_constellation_modulator_0', '0', 'uhd_usrp_sink_0', '0']
    ]

    tx_grc = {
        'options': tx_options,
        'blocks': tx_blocks,
        'connections': tx_connections,
        'metadata': sim_data['metadata']
    }

    with open('hardware_test/tx_hardware.grc', 'w') as f:
        yaml.dump(tx_grc, f, default_flow_style=False)
    print("Generated tx_hardware.grc successfully!")

    # ========================================================
    # 2. CREATE RX FLOWGRAPH
    # ========================================================
    rx_blocks = []

    # Options block
    rx_options = copy_block(sim_data['options'])
    rx_options['parameters']['id'] = 'rx_hardware'
    rx_options['parameters']['title'] = '16-HQAM Hardware Receiver'

    # Variables
    rx_blocks.append(find_block(sim_data['blocks'], 'Alpha'))
    rx_blocks.append(find_block(sim_data['blocks'], 'hqam_const'))
    rx_blocks.append(find_block(sim_data['blocks'], 'nfilts'))
    rx_blocks.append(find_block(sim_data['blocks'], 'sps'))
    rx_blocks.append(find_block(sim_data['blocks'], 'timing_loop_bw'))
    rx_blocks.append(find_block(sim_data['blocks'], 'rrc_taps'))

    rx_samp_rate_var = copy_block(find_block(sim_data['blocks'], 'samp_rate'))
    rx_samp_rate_var['parameters']['value'] = '1000000' # 1 Msps
    rx_blocks.append(rx_samp_rate_var)

    # Center Freq, Rx Gain, and Equalizer Step Size variables
    rx_center_freq_var = {
        'name': 'center_freq',
        'id': 'variable',
        'parameters': {
            'comment': '',
            'value': '2450000000'
        },
        'states': {
            'bus_sink': False,
            'bus_source': False,
            'bus_structure': None,
            'coordinate': [700, 16.0],
            'rotation': 0,
            'state': 'enabled'
        }
    }
    rx_blocks.append(rx_center_freq_var)

    rx_gain_var = {
        'name': 'rx_gain',
        'id': 'variable',
        'parameters': {
            'comment': '',
            'value': '40'
        },
        'states': {
            'bus_sink': False,
            'bus_source': False,
            'bus_structure': None,
            'coordinate': [820, 16.0],
            'rotation': 0,
            'state': 'enabled'
        }
    }
    rx_blocks.append(rx_gain_var)

    rx_eq_gain_var = {
        'name': 'eq_gain',
        'id': 'variable',
        'parameters': {
            'comment': '',
            'value': '0.001' # LMS adaptation step size
        },
        'states': {
            'bus_sink': False,
            'bus_source': False,
            'bus_structure': None,
            'coordinate': [940, 16.0],
            'rotation': 0,
            'state': 'enabled'
        }
    }
    rx_blocks.append(rx_eq_gain_var)

    # Adaptive Algorithm Variable Block
    adaptive_algo_block = {
        'name': 'lms_algo',
        'id': 'variable_adaptive_algorithm',
        'parameters': {
            'affinity': '',
            'alias': '',
            'comment': '',
            'cons': 'hqam_const',
            'delta': '10.0',
            'ffactor': '0.99',
            'modulus': '2',
            'step_size': 'eq_gain',
            'type': 'lms'
        },
        'states': {
            'bus_sink': False,
            'bus_source': False,
            'bus_structure': None,
            'coordinate': [1060, 16.0],
            'rotation': 0,
            'state': 'enabled'
        }
    }
    rx_blocks.append(adaptive_algo_block)

    # Core RX DSP Blocks
    # USRP Source
    usrp_source = copy_block(usrp_source_sim)
    usrp_source['states']['coordinate'] = [16, 220.0]
    usrp_source['parameters']['samp_rate'] = 'samp_rate'
    usrp_source['parameters']['center_freq0'] = 'center_freq'
    usrp_source['parameters']['gain0'] = 'rx_gain'
    usrp_source['parameters']['ant0'] = '"RX2"'
    rx_blocks.append(usrp_source)

    # AGC Block
    agc_block = {
        'name': 'analog_agc_xx_0',
        'id': 'analog_agc_xx',
        'parameters': {
            'affinity': '',
            'alias': '',
            'comment': '',
            'gain': '1.0',
            'max_gain': '65536',
            'maxoutbuf': '0',
            'minoutbuf': '0',
            'rate': '1e-4',
            'reference': '1.0',
            'type': 'complex'
        },
        'states': {
            'bus_sink': False,
            'bus_source': False,
            'bus_structure': None,
            'coordinate': [200, 220.0],
            'rotation': 0,
            'state': 'enabled'
        }
    }
    rx_blocks.append(agc_block)

    # FLL Band Edge Block
    fll_block = {
        'name': 'digital_fll_band_edge_cc_0',
        'id': 'digital_fll_band_edge_cc',
        'parameters': {
            'affinity': '',
            'alias': '',
            'comment': '',
            'filter_size': '45',
            'w': '0.02',
            'maxoutbuf': '0',
            'minoutbuf': '0',
            'rolloff': 'Alpha',
            'samps_per_sym': 'sps',
            'type': 'cc'
        },
        'states': {
            'bus_sink': False,
            'bus_source': False,
            'bus_structure': None,
            'coordinate': [360, 220.0],
            'rotation': 0,
            'state': 'enabled'
        }
    }
    rx_blocks.append(fll_block)

    # NEW: Matched Filter (Root Raised Cosine Filter)
    rrc_filter_block = {
        'name': 'root_raised_cosine_filter_0',
        'id': 'root_raised_cosine_filter',
        'parameters': {
            'affinity': '',
            'alias': '',
            'alpha': 'Alpha',
            'comment': '',
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
        'states': {
            'bus_sink': False,
            'bus_source': False,
            'bus_structure': None,
            'coordinate': [560, 220.0],
            'rotation': 0,
            'state': 'enabled'
        }
    }
    rx_blocks.append(rrc_filter_block)

    # Symbol Sync (replacing PFB Clock Sync)
    symbol_sync_block = {
        'name': 'digital_symbol_sync_xx_0',
        'id': 'digital_symbol_sync_xx',
        'parameters': {
            'affinity': '',
            'alias': '',
            'comment': '',
            'constellation': 'digital.constellation_bpsk().base()',
            'damping': '1.0',
            'loop_bw': '0.03',
            'max_dev': '1.5',
            'maxoutbuf': '0',
            'minoutbuf': '0',
            'nfilters': '128',
            'osps': '1',
            'pfb_mf_taps': '[]',
            'resamp_type': 'digital.IR_MMSE_8TAP',
            'sps': 'sps',
            'ted_gain': '1.0',
            'ted_type': 'digital.TED_GARDNER', # Immune to phase rotation
            'type': 'cc'
        },
        'states': {
            'bus_sink': False,
            'bus_source': False,
            'bus_structure': None,
            'coordinate': [760, 220.0],
            'rotation': 0,
            'state': 'enabled'
        }
    }
    rx_blocks.append(symbol_sync_block)

    # Linear Equalizer (DD-LMS)
    linear_equalizer_block = {
        'name': 'digital_linear_equalizer_0',
        'id': 'digital_linear_equalizer',
        'parameters': {
            'adapt_after_training': 'True',
            'affinity': '',
            'alg': 'lms_algo',
            'alias': '',
            'comment': '',
            'maxoutbuf': '0',
            'minoutbuf': '0',
            'num_taps': '15',
            'sps': '1', # Symbol sync outputs 1 sps
            'training_sequence': '[]',
            'training_start_tag': 'corr_est'
        },
        'states': {
            'bus_sink': False,
            'bus_source': False,
            'bus_structure': None,
            'coordinate': [980, 220.0],
            'rotation': 0,
            'state': 'enabled'
        }
    }
    rx_blocks.append(linear_equalizer_block)

    # Constellation Sink (GUI) - connected to output of Linear Equalizer
    const_sink = copy_block(find_block(sim_data['blocks'], 'qtgui_const_sink_x_0'))
    const_sink['states']['coordinate'] = [1220, 140.0]
    rx_blocks.append(const_sink)

    # Decoder Blocks (No diff decoder!)
    const_dec = copy_block(find_block(sim_data['blocks'], 'digital_constellation_decoder_cb_0'))
    const_dec['states']['coordinate'] = [1220, 280.0]
    rx_blocks.append(const_dec)

    unpack_bits = copy_block(find_block(sim_data['blocks'], 'blocks_unpack_k_bits_bb_0_0_0'))
    unpack_bits['states']['coordinate'] = [1420, 280.0]
    rx_blocks.append(unpack_bits)

    char_to_float = copy_block(find_block(sim_data['blocks'], 'blocks_char_to_float_0_0'))
    char_to_float['states']['coordinate'] = [1600, 280.0]
    rx_blocks.append(char_to_float)

    # Time Sink (GUI)
    time_sink = copy_block(find_block(sim_data['blocks'], 'qtgui_time_sink_x_0_0'))
    time_sink['states']['coordinate'] = [1760, 280.0]
    time_sink['parameters']['nconnections'] = '1'
    time_sink['parameters']['name'] = '"Decoded Bits"'
    time_sink['parameters']['label1'] = 'RX Decoded Bits'
    rx_blocks.append(time_sink)

    rx_connections = [
        ['uhd_usrp_source_0', '0', 'analog_agc_xx_0', '0'],
        ['analog_agc_xx_0', '0', 'digital_fll_band_edge_cc_0', '0'],
        ['digital_fll_band_edge_cc_0', '0', 'root_raised_cosine_filter_0', '0'],
        ['root_raised_cosine_filter_0', '0', 'digital_symbol_sync_xx_0', '0'],
        ['digital_symbol_sync_xx_0', '0', 'digital_linear_equalizer_0', '0'],
        ['digital_linear_equalizer_0', '0', 'qtgui_const_sink_x_0', '0'],
        ['digital_linear_equalizer_0', '0', 'digital_constellation_decoder_cb_0', '0'],
        ['digital_constellation_decoder_cb_0', '0', 'blocks_unpack_k_bits_bb_0_0_0', '0'],
        ['blocks_unpack_k_bits_bb_0_0_0', '0', 'blocks_char_to_float_0_0', '0'],
        ['blocks_char_to_float_0_0', '0', 'qtgui_time_sink_x_0_0', '0']
    ]

    rx_grc = {
        'options': rx_options,
        'blocks': rx_blocks,
        'connections': rx_connections,
        'metadata': sim_data['metadata']
    }

    with open('hardware_test/rx_hardware.grc', 'w') as f:
        yaml.dump(rx_grc, f, default_flow_style=False)
    print("Generated rx_hardware.grc successfully!")

if __name__ == '__main__':
    generate()
