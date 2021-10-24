import time
from typing import List

import cv2
from PyQt5.QtCore import QThread, pyqtSignal

from handtracker.hand_track import HandTrack


class HandTrackThread(QThread):
    send_message_about_hand_tracking = pyqtSignal(dict)

    def __init__(self):
        super(HandTrackThread, self).__init__()
        self.capture = cv2.VideoCapture(0)

    def run(self):
        hand_track = HandTrack(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH), self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

        prev_data = {'num_of_detected_hands': 0,
                     'is_action_check_gesture': False,
                     'direction_of_hand': 0,
                     'num_of_stretch_out_fingers': 0}
        prev_time = 0
        is_send = False
        while True:
            try:
                ret, frame = self.capture.read()
            except KeyboardInterrupt:
                print('read error')
                break

            if not ret:
                continue

            frame = cv2.flip(frame, 1)
            current_time = time.time()

            # processing
            multi_hand_landmarks = hand_track.get_multi_hand_landmarks(frame)
            knuckle_points: dict = hand_track.get_knuckle_points(multi_hand_landmarks)

            if not knuckle_points:
                cv2.waitKey(33)
                continue

            # num of hand
            num_of_detected_hands: int = hand_track.get_detected_hands_count(multi_hand_landmarks)

            # count stretched finger num
            stretch_fingers: List[bool] = hand_track.get_stretch_fingers(knuckle_points)
            num_of_stretch_out_fingers = stretch_fingers.count(True)

            # init or not
            is_valid = num_of_stretch_out_fingers != 5

            # click or not
            is_action_check_gesture: bool = True if num_of_stretch_out_fingers == 0 and num_of_detected_hands == 1 and hand_track.is_action_click_gesture(
                knuckle_points) else False

            # hand direction
            direction_of_hand: int = hand_track.get_direction_hand(knuckle_points)

            data = {'num_of_detected_hands': num_of_detected_hands,
                    'is_action_check_gesture': is_action_check_gesture,
                    'direction_of_hand': direction_of_hand,
                    'num_of_stretch_out_fingers': num_of_stretch_out_fingers
                    }

            # If the same operation is maintained for 1 second after initialization, a signal is sent.
            if is_send and prev_data == data and is_valid:
                print(data)
                if current_time - prev_time >= 1:
                    self.send_message_about_hand_tracking.emit(data)
                    is_send = False
                continue

            prev_data, prev_time = data, current_time

            # 초기화 인식
            if not is_valid:
                is_send = True

            if cv2.waitKey(33) == 27:
                break

        # cv2.destroyAllWindows()
        self.capture.release()
