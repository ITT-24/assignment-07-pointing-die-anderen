import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import cv2
import time

from mediapipe import solutions
from mediapipe.framework.formats import landmark_pb2
import numpy as np

from pynput.mouse import Button, Controller
import pyautogui
import math
import sys

mouse = Controller()
screen_width, screen_height = pyautogui.size()

model_path = 'hand_landmarker.task'

BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
HandLandmarkerResult = mp.tasks.vision.HandLandmarkerResult
VisionRunningMode = mp.tasks.vision.RunningMode

CLICK_DISTANCE_THRESHOLD = 40

previous_mouse_x = 0
previous_mouse_y = 0
mouse_left_down = False

TIME_INTERVAL = 0.05
target_frame_time = 1/60

video_id = 0
if len(sys.argv) > 1:
    video_id = int(sys.argv[1]) #1 for Mac

def interpolate_positions(prev_pos, current_pos):
    elapsed_time = TIME_INTERVAL
    fraction = min(1, elapsed_time / target_frame_time)
    return prev_pos + (current_pos - prev_pos) * fraction

def get_distance(x1, y1, x2, y2):
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

def set_mouse_position(hand_landmark):
    global previous_mouse_x, previous_mouse_y
    x_mouse_current = hand_landmark.x * screen_width
    y_mouse_current = hand_landmark.y * screen_height
    x_position = interpolate_positions(previous_mouse_x, x_mouse_current)
    y_position = interpolate_positions(previous_mouse_y, y_mouse_current)
    mouse.position = (x_position, y_position)
    previous_mouse_x = x_position
    previous_mouse_y = y_position

def check_for_click(thumb_landmark, index_landmark):
    global mouse_left_down
    x_position_thumb = thumb_landmark.x * screen_width
    y_position_thumb = thumb_landmark.y * screen_height
    x_position_index = index_landmark.x * screen_width
    y_position_index = index_landmark.y * screen_height
    distance = get_distance(x_position_thumb, y_position_thumb, x_position_index, y_position_index)
    if(not mouse_left_down and distance <= CLICK_DISTANCE_THRESHOLD):
        mouse.press(Button.left)
        mouse_left_down = True
    elif mouse_left_down and distance > CLICK_DISTANCE_THRESHOLD:
        mouse.release(Button.left)
        mouse_left_down = False

def draw_landmarks_on_image(rgb_image, detection_result):
    hand_landmarks_list = detection_result.hand_landmarks
    annotated_image = np.copy(rgb_image)
    
    # Loop through the detected hands to visualize.
    for idx in range(len(hand_landmarks_list)):
        hand_landmarks = hand_landmarks_list[idx]
        
        thumb_landmark = hand_landmarks[4] #https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker/index?hl=de#models
        index_landmark = hand_landmarks[8]
        hand_landmark = hand_landmarks[9]

        set_mouse_position(hand_landmark)
        check_for_click(thumb_landmark, index_landmark)
        # Draw the hand landmarks.
        # hand_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
        # hand_landmarks_proto.landmark.extend([
        # landmark_pb2.NormalizedLandmark(x=landmark.x, y=landmark.y, z=landmark.z) for landmark in hand_landmarks
        # ])
        # solutions.drawing_utils.draw_landmarks(
        #     annotated_image,
        #     hand_landmarks_proto,
        #     solutions.hands.HAND_CONNECTIONS,
        #     solutions.drawing_styles.get_default_hand_landmarks_style())
    return annotated_image

class handDetector():
    def __init__(self):
        self.cap = cv2.VideoCapture(video_id) 
        self.running = True
        #self.dimensions = (480, 640, 3)
        self.dimensions = (screen_height, screen_width, 3) #set size to screen size to avoid mapping
        self.options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=model_path),
            running_mode=VisionRunningMode.LIVE_STREAM,
            result_callback=self.print_result)

    # Create a hand landmarker instance with the live stream mode:
    def print_result(self, result: HandLandmarkerResult, output_image: mp.Image, timestamp_ms: int):
        out = np.zeros(self.dimensions)
        #print('hand landmarker result: {}'.format(result))
        self.annotated_image = draw_landmarks_on_image(out, result) # output_image.numpy_view()

    def run(self):
        with HandLandmarker.create_from_options(self.options) as landmarker:
            while self.running:
                _, frame = self.cap.read()

                frame = cv2.flip(frame, 1)

                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
                hand_result = landmarker.detect_async(mp_image, int(time.time() * 1000))

                # try:
                #     cv2.imshow('test', self.annotated_image)
                # except:
                #     continue

                time.sleep(TIME_INTERVAL)
                # if cv2.waitKey(1) == ord('q'):
                #     self.running = False

            self.cap.release()
            #cv2.destroyAllWindows()

if __name__ == '__main__':
    detector = handDetector()
    detector.run()
