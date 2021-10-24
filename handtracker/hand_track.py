import math
from typing import Tuple, List, NamedTuple

import cv2
import mediapipe


# return True(is not None), False(is None)
def is_not_none(obj):
    return obj is not None


class HandTrack:
    def __init__(self, frame_width, frame_height):
        self.drawing_module = mediapipe.solutions.drawing_utils
        self.hands_module = mediapipe.solutions.hands
        self.frame_width: float = frame_width
        self.frame_height: float = frame_height

        self.hands = self.hands_module.Hands(
            static_image_mode=False,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7,
            max_num_hands=2
        )

    # return : multi_hand_landmarks in frame
    def get_multi_hand_landmarks(self, frame):
        return self.hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).multi_hand_landmarks

    # return : knuckle_points about hands
    def get_knuckle_points(self, multi_hand_landmarks) -> dict:
        knuckle_points: dict = {}

        if multi_hand_landmarks is None:
            return knuckle_points

        hand_landmarks = multi_hand_landmarks[0]

        for landmark in self.hands_module.HandLandmark:
            normalized_landmark = hand_landmarks.landmark[landmark]
            pixel_coordinates_landmark: Tuple[int, int] = self.drawing_module._normalized_to_pixel_coordinates(
                normalized_landmark.x,
                normalized_landmark.y,
                int(self.frame_width),
                int(self.frame_height))

            knuckle_points[landmark] = pixel_coordinates_landmark

        return knuckle_points

    # return : num_of_detected_hands
    def get_detected_hands_count(self, multi_hand_landmarks) -> int:
        return 0 if multi_hand_landmarks is None else len(multi_hand_landmarks)

    # return: stretch_out_fingers([thumb, first, second, third, fourth])
    def get_stretch_fingers(self, knuckle_points) -> List[bool]:
        stretch_fingers: List[bool] = self.__calculate_stretch_out_fingers(knuckle_points)
        return stretch_fingers

    # return: stretch_out_fingers([thumb, first, second, third, fourth])
    def __calculate_stretch_out_fingers(self, knuckle_points: dict) -> List[bool]:
        result: List[bool] = [False] * 5

        for landmark_value in range(self.hands_module.HandLandmark.THUMB_MCP, 21, 4):
            pip, dip, tip = landmark_value, landmark_value + 1, landmark_value + 2
            result[landmark_value // 4] = self.__is_stretch_out_finger(
                pip == self.hands_module.HandLandmark.THUMB_MCP,
                knuckle_points[pip],
                knuckle_points[dip],
                knuckle_points[tip]
            )

        return result

    # return : True(stretch_out), False(not stretch out)
    def __is_stretch_out_finger(self, is_thumb: bool, finger_pip: Tuple[int], finger_dip: Tuple[int],
                                finger_tip: Tuple[int]) -> bool:
        is_valid_finger_pip: bool = is_not_none(finger_pip)
        is_valid_finger_dip: bool = is_not_none(finger_dip)
        is_valid_finger_tip: bool = is_not_none(finger_tip)

        if not is_valid_finger_pip or not is_valid_finger_dip or not is_valid_finger_tip:
            return False

        finger_pip_value: int = self.__get_value(is_thumb, finger_pip)
        finder_dip_value: int = self.__get_value(is_thumb, finger_dip)
        finger_tip_value: int = self.__get_value(is_thumb, finger_tip)

        if finder_dip_value < finger_pip_value and finger_tip_value < finger_pip_value:
            return True

        return False

    # Passing values with or without thumb
    def __get_value(self, is_thumb: bool, point: Tuple[int]) -> int:
        return point[0] if is_thumb else point[1]

    # return : True(action click gesture), False(fail detection)
    def is_action_click_gesture(self, knuckle_points) -> bool:
        thumb_tip: Tuple[int] = knuckle_points[self.hands_module.HandLandmark.THUMB_TIP]
        index_finger_tip: Tuple[int] = knuckle_points[self.hands_module.HandLandmark.INDEX_FINGER_TIP]
        middle_finger_tip: Tuple[int] = knuckle_points[self.hands_module.HandLandmark.MIDDLE_FINGER_TIP]

        distance_thumb_to_index: float = math.hypot(thumb_tip[0] - index_finger_tip[0],
                                                    thumb_tip[1] - index_finger_tip[1])
        distance_thumb_to_middle: float = math.hypot(thumb_tip[0] - middle_finger_tip[0],
                                                     thumb_tip[1] - middle_finger_tip[1])

        if distance_thumb_to_index > 80 or distance_thumb_to_middle > 80:
            return False

        return True

    # return : -1(left), 1(right), 0(fail calculate)
    def get_direction_hand(self, knuckle_points) -> int:
        index_finder_mcp: Tuple[int, int] = knuckle_points[self.hands_module.HandLandmark.INDEX_FINGER_MCP]
        index_finger_tip: Tuple[int, int] = knuckle_points[self.hands_module.HandLandmark.INDEX_FINGER_TIP]

        return self.__calculate_direction(index_finder_mcp, index_finger_tip)

    def __calculate_direction(self, first_point, second_point) -> int:
        radian = math.atan2(second_point[1] - first_point[1], first_point[0] - second_point[0])
        degree = abs(int(math.degrees(radian)))

        if degree < 45:
            return -1
        elif degree > 105:
            return 1

        return 0
