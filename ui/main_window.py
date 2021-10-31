import functools
import os

from typing import List

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSlot
from PyQt5 import uic

from handtracker.hand_track_thread import HandTrackThread

form_class = uic.loadUiType(os.path.join(os.getcwd(), "assets/ui/main_window.ui"))[0]


class MainWindow(QWidget, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.hand_track_thread = HandTrackThread()
        self.hand_track_thread.send_message_about_hand_tracking.connect(self.on_recv_hand_track)
        self.hand_track_thread.start()

        self.btn_clear.clicked.connect(lambda: self.tb_data.clear())

    @pyqtSlot(dict)
    def on_recv_hand_track(self, data: dict):
        # data = {'num_of_detected_hands': num_of_detected_hands,
        #         'is_action_check_gesture': is_action_check_gesture,
        #         'direction_of_hand': direction_of_hand,
        #         'num_of_stretch_out_fingers': num_of_stretch_out_fingers
        #         }

        num_of_detected_hands = data['num_of_detected_hands']
        is_clicked = data['is_action_check_gesture']
        direction_of_hand = data['direction_of_hand']
        num_of_stretch_out_fingers = data['num_of_stretch_out_fingers']

        self.show_textBrowser(
            "num_of_detected_hands \t\t = " + str(num_of_detected_hands) + '\n' + \
            "is_clicked \t\t\t = " + str(is_clicked) + '\n' + \
            "direction_of_hand \t\t = " + str(direction_of_hand) + '\n' + \
            "num_of_stretch_out_fingers \t\t = " + str(num_of_stretch_out_fingers) + '\n' + '\n')

    def show_textBrowser(self, data):
        self.tb_data.append(data)

    def closeEvent(self, event):
        self.deleteLater()
