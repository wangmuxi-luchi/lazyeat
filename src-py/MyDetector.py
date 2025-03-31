import threading
import time
import traceback
from typing import List

import math
import cv2
import numpy as np
import pyautogui
from pynput.keyboard import Controller as KeyboardController
from pynput.keyboard import Key
from pynput.mouse import Button, Controller
from win10toast import ToastNotifier

from HandTrackingModule import HandDetector
from HandTrackingModule import FingerStatus
from state_machine import StateMachine
import DrawInScreen

import logging
from tkinter import messagebox


screen_width, screen_height = pyautogui.size()
mouse = Controller()
keyboard = KeyboardController()
notification = ToastNotifier()

######################
wCam, hCam = 640, 480
frameR = 150  # Frame Reduction
smoothening = 7  # random value
######################

prev_loc_x, prev_loc_y = 0, 0

# 滚动屏幕的增量
scroll_increment = 1
prev_scroll_y = 0


def show_toast(title: str = '手势识别',
               msg: str = '手势识别',
               duration: int = 1):
    try:
        notification.show_toast(
            title=title,
            msg=msg,
            duration=duration,
            icon_path='icon.ico',
            threaded=True
        )
    except Exception as e:
        traceback.print_exc()


class HandState:
    # 食指举起，移动鼠标
    only_index_up = 'only_index_up'

    # 食指和中指同时竖起 - 点击模式
    index_and_middle_up = 'index_and_middle_up'

    # 三根手指同时竖起 - 滚动屏幕
    three_fingers_up = 'three_fingers_up'

    # 四根手指同时竖起 - 视频全屏
    four_fingers_up = 'four_fingers_up'

    # 五根手指同时竖起 - 暂停/开始 识别
    stop_gesture = 'stop_gesture'

    # 拇指和食指同时竖起 - 语音识别
    voice_gesture_start = 'voice_gesture_start'
    voice_gesture_stop = 'voice_gesture_stop'

    # 其他手势
    delete_gesture = 'delete_gesture'

    other = None


class MyDetector(HandDetector):
    """
    hand 为 findHands() 方法返回的字典信息
    lmList 为手部21个关键点的坐标信息, (x, y, z)
    """
    last_move_time = 0
    last_click_time = 0
    last_scroll_time = 0
    last_full_screen_time = 0
    last_change_flag_time = 0

    flag_detect = True
    voice_controller = None
    
    state_change_time = time.time()

    movestate_index_tip_pixels = []# the pixels in the start of move state
    movestate_hand_type = None # the type of hand in move state
    movestate_sensitivity = 1500# 鼠标灵敏度
    movestate_threshold = 0.02# 移动阈值
    movestate_thread = None# the thread of move state
    movestate_last_move_x = 0
    movestate_last_move_y = 0
    movestate_move_change_threshold = 0.02
    movestate_move_change_ratio = 0.2


    def __init__(self, mode=False, maxHands=2, detectionCon=0.5, minTrackCon=0.5):
        super().__init__(mode, maxHands, detectionCon, minTrackCon)

        def init_voice_controller():
            from VoiceController import VoiceController

            self.voice_controller = VoiceController()
            show_toast(
                title='语音识别模块初始化成功',
                msg='语音识别模块初始化成功',
                duration=1
            )

        thread = threading.Thread(target=init_voice_controller, daemon=True)
        thread.start()

        # 初始化状态机
        self.init_state_machine()
    def draw_mouse_move_box(self, img) -> np.ndarray:
        cv2.rectangle(img, (frameR, frameR), (wCam - frameR, hCam - frameR),
                      (255, 0, 255), 2)
        return img

    # 配置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    def process(self, all_hands: List[dict]):
        # 处理当前状态
        self.state_machine.process_current_state(all_hands)

        # current_state = self.state_machine.get[_current_state()
        # logging.info(f"当前状态: {current_state}")

        # hand_count = len(all_hands)
        # if hand_count == 0:
        #     state_msg = '未检测到手势'
        #     finger_status_list = []
        # elif hand_count == 1:
        #     right_hand = all_hands[0]
        #     finger_status_list = self.get_all_fingers_status(right_hand)
        #     state_msg = f'检测到 1 只手，手指状态列表: {finger_status_list}'
        # elif hand_count == 2:
        #     right_hand = all_hands[0]
        #     left_hand = all_hands[1]
        #     right_finger_status_list = self.get_all_fingers_status(right_hand)
        #     left_finger_status_list = self.get_all_fingers_status(left_hand)
        #     finger_status_list = [right_finger_status_list, left_finger_status_list]
        #     state_msg = f'检测到 2 只手，右手手指状态列表: {right_finger_status_list}，左手手指状态列表: {left_finger_status_list}'
        # else:
        #     return

        # 使用 logging 输出信息到控制台
        # logging.info(state_msg)

        # 使用 tkinter 消息框显示信息
        # messagebox.showinfo('手势状态', state_msg)

    def _four_fingers_up_trigger(self):
        if self.is_false_touch():
            return

        from pinia_store import PINIA_STORE

        current_time = time.time()
        if not current_time - self.last_full_screen_time > 1.5:
            return

        gesture_sender = PINIA_STORE.gesture_sender
        gesture_sender.send_four_fingers_up()
        self.last_full_screen_time = current_time

    # 防止手势误识别
    def is_false_touch(self):
        current_time = time.time()
        if current_time - self.last_move_time < 0.2:  # 防止误触, 移动鼠标后立即点击
            return True
        return False

    def init_state_machine(self):
        self.state_machine = StateMachine("normal")

        # 添加状态及处理函数
        def process_normal(all_hands):
            if all_hands:
                for hand in all_hands:
                    finger_status = self.get_all_fingers_status(hand)
                    if finger_status[1::] == [1, 1, 1, 1] or finger_status == [0, 1, 1, 1, 1] and self.detect_single_finger_state(hand["lmList"], 1) == FingerStatus.STRAIGHT_UP:
                        return "wait"
            return "normal"

        def process_move(all_hands):
            # move mouse
            if all_hands:
                for hand in all_hands:
                    if hand["type"] == self.movestate_hand_type:
                        index_tip_pixels = self.get_index_tip_pixels(hand)
                        if index_tip_pixels:
                            relative_move_x = (index_tip_pixels[0] - self.movestate_index_tip_pixels[0] - self.movestate_last_move_x)
                            relative_move_y = (index_tip_pixels[1] - self.movestate_index_tip_pixels[1] - self.movestate_last_move_y)
                            relative_move_x=math.copysign(min(abs(relative_move_x)*self.movestate_move_change_ratio,self.movestate_move_change_threshold), relative_move_x)+self.movestate_last_move_x
                            relative_move_y=math.copysign(min(abs(relative_move_y)*self.movestate_move_change_ratio,self.movestate_move_change_threshold), relative_move_y)+self.movestate_last_move_y

                            self.movestate_last_move_x = relative_move_x
                            self.movestate_last_move_y = relative_move_y
                            # 绘制圆
                            DrawInScreen.draw_cycle(True, self.movestate_threshold* self.movestate_sensitivity, -relative_move_x * self.movestate_sensitivity, relative_move_y* self.movestate_sensitivity)
                            # 判断是否超过阈值
                            relative_move_dis = (relative_move_x**2 + relative_move_y**2)**0.5
                            if relative_move_dis > self.movestate_threshold:
                                # 计算实际需要移动的距离
                                scaling = (relative_move_dis-self.movestate_threshold)**2 / relative_move_dis #非线性提速
                                move_x = relative_move_x * scaling
                                move_y = relative_move_y * scaling
                                if not hasattr(process_move, "sum_dy"):
                                    process_move.sum_dy = 0  # 初始化静态变量global sum_dx=0
                                if not hasattr(process_move, "sum_dx"):
                                    process_move.sum_dx = 0  # 初始化静态变量global sum_dx=0
                                sum_dx = process_move.sum_dx
                                sum_dy = process_move.sum_dy
                                sum_dx += -move_x * self.movestate_sensitivity
                                sum_dy += move_y * self.movestate_sensitivity
                                # 移动鼠标
                                mouse.move(math.modf(sum_dx)[1], math.modf(sum_dy)[1])
                                # 重置累积距离
                                process_move.sum_dx = math.modf(sum_dx)[0]
                                process_move.sum_dy = math.modf(sum_dy)[0]

                                # 更新起始位置
                                # self.movestate_index_tip_pixels = index_tip_pixels


                                logging.info(f"process_move : {move_x} {move_y}")

            # state change
            if all_hands:
                for hand in all_hands:
                    finger_status = self.get_all_fingers_status(hand)
                    if finger_status[1::] == [1, 1, 1, 1] or finger_status == [0, 1, 1, 1, 1] and self.detect_single_finger_state(hand["lmList"], 1) == FingerStatus.STRAIGHT_UP:
                        return "wait"
            return "move"
        def enter_move(tip_pixels, hand_type):
            self.movestate_index_tip_pixels = tip_pixels
            self.movestate_hand_type = hand_type
            self.movestate_last_move_x = 0
            self.movestate_last_move_y = 0

        def process_wait(all_hands):
            if time.time() - self.state_change_time > 5:
                return "normal"
            if all_hands:
                for hand in all_hands:
                    finger_status = self.get_all_fingers_status(hand)
                    if finger_status[1::] == [1, 0, 0, 0]and self.detect_single_finger_state(hand["lmList"], 1) == FingerStatus.STRAIGHT_UP:
                        enter_move(self.get_index_tip_pixels(hand), hand["type"])
                        logging.info(f"enter_move : {self.movestate_index_tip_pixels}")
                        return "move"
                    elif not self.is_false_touch() and finger_status[1::] == [0, 0, 0, 0]:
                        current_time = time.time()
                        if not current_time - self.last_click_time > 0.5:  # 点击间隔 0.5s
                            return "normal"

                        mouse.click(Button.left, 1)
                        # print(length)
                        self.last_click_time = current_time
            return "wait"

        def enter_wait(all_hands):
            self.state_change_time = time.time()

        
        # def enter_move(all_hands):

        self.state_machine.add_state("normal", process_normal)
        self.state_machine.add_state("move", process_move)
        self.state_machine.add_state("wait", process_wait, enter_wait)