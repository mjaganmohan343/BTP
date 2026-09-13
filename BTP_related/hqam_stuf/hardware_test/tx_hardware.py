#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: 16-HQAM Hardware Transmitter
# Author: pranav
# Description: 16-HexQAM simulation using native GRC blocks with custom constellation
# GNU Radio version: 3.10.12.0

from PyQt5 import Qt
from gnuradio import qtgui
from gnuradio import blocks
import numpy
from gnuradio import digital
from gnuradio import gr
from gnuradio.filter import firdes
from gnuradio.fft import window
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import uhd
import time
import threading
import tx_hardware_epy_block_0 as epy_block_0  # embedded python block



class tx_hardware(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "16-HQAM Hardware Transmitter", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("16-HQAM Hardware Transmitter")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except BaseException as exc:
            print(f"Qt GUI: Could not set Icon: {str(exc)}", file=sys.stderr)
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("gnuradio/flowgraphs", "tx_hardware")

        try:
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)
        self.flowgraph_started = threading.Event()

        ##################################################
        # Variables
        ##################################################
        self.tx_gain = tx_gain = 40
        self.sps = sps = 4
        self.seed_numpy = seed_numpy = numpy.random.seed(42)
        self.samp_rate = samp_rate = 1000000
        self.hqam_const = hqam_const = digital.constellation_calcdist([-0.3333+1.1547j, 0.3333+1.1547j, -0.6667+0.5774j, 0.0000+0.5774j, 0.6667+0.5774j, 1.3333+0.5774j, -0.3333+1e-10j, 0.3333+1e-10j, 1.0000+1e-10j, -0.6667-0.5774j, 0.0000-0.5774j, 0.6667-0.5774j, 1.3333-0.5774j, -0.3333-1.1547j, 0.3333-1.1547j, -1.0000+1e-09j], [7, 6, 5, 2, 0, 4, 3, 10, 8, 9, 11, 14, 12, 13, 15, 1],
        1, 1, digital.constellation.NO_NORMALIZATION).base()
        self.hqam_const.set_npwr(1.0)
        self.center_freq = center_freq = 2850000000
        self.Alpha = Alpha = 0.22

        ##################################################
        # Blocks
        ##################################################

        self.uhd_usrp_sink_0 = uhd.usrp_sink(
            ",".join(("", '')),
            uhd.stream_args(
                cpu_format="fc32",
                args='',
                channels=list(range(0,1)),
            ),
            "",
        )
        self.uhd_usrp_sink_0.set_samp_rate(samp_rate)
        self.uhd_usrp_sink_0.set_time_now(uhd.time_spec(time.time()), uhd.ALL_MBOARDS)

        self.uhd_usrp_sink_0.set_center_freq(center_freq, 0)
        self.uhd_usrp_sink_0.set_antenna("TX/RX", 0)
        self.uhd_usrp_sink_0.set_gain(tx_gain, 0)
        self.epy_block_0 = epy_block_0.blk(packet_len=1000)
        self.digital_constellation_modulator_0 = digital.generic_mod(
            constellation=hqam_const,
            differential=False,
            samples_per_symbol=sps,
            pre_diff_code=True,
            excess_bw=Alpha,
            verbose=False,
            log=False,
            truncate=False)
        self.analog_random_source_x_0 = blocks.vector_source_b(list(map(int, numpy.random.randint(0, 255, 10000))), True)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_random_source_x_0, 0), (self.epy_block_0, 0))
        self.connect((self.digital_constellation_modulator_0, 0), (self.uhd_usrp_sink_0, 0))
        self.connect((self.epy_block_0, 0), (self.digital_constellation_modulator_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("gnuradio/flowgraphs", "tx_hardware")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_tx_gain(self):
        return self.tx_gain

    def set_tx_gain(self, tx_gain):
        self.tx_gain = tx_gain
        self.uhd_usrp_sink_0.set_gain(self.tx_gain, 0)

    def get_sps(self):
        return self.sps

    def set_sps(self, sps):
        self.sps = sps

    def get_seed_numpy(self):
        return self.seed_numpy

    def set_seed_numpy(self, seed_numpy):
        self.seed_numpy = seed_numpy

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.uhd_usrp_sink_0.set_samp_rate(self.samp_rate)

    def get_hqam_const(self):
        return self.hqam_const

    def set_hqam_const(self, hqam_const):
        self.hqam_const = hqam_const

    def get_center_freq(self):
        return self.center_freq

    def set_center_freq(self, center_freq):
        self.center_freq = center_freq
        self.uhd_usrp_sink_0.set_center_freq(self.center_freq, 0)

    def get_Alpha(self):
        return self.Alpha

    def set_Alpha(self, Alpha):
        self.Alpha = Alpha




def main(top_block_cls=tx_hardware, options=None):

    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()

    tb.start()
    tb.flowgraph_started.set()

    tb.show()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    qapp.exec_()

if __name__ == '__main__':
    main()
