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

    
    current_hand_state = HandState.other
    previous_hand_state = HandState.other

    mouse_left_button_down = False

    movestate_start_center = []# the pixels in the start of move state
    movestate_dyn_cx = 0 # the x coordinate of the center of the hand in move state
    movestate_dyn_cy = 0 # the y coordinate of the center of the hand in move state
    movestate_hand_type = None # the type of hand in move state
    movestate_sensitivity = 1500# 鼠标灵敏度
    movestate_move_v = 0 # 鼠标动态移动速度
    movestate_threshold = 0.15 # 摇杆移动阈值
    movestate_base_finger = 1 # 移动基于哪根手指指尖，1代表食指，2代表中指，3代表无名指，4代表小拇指
    movestate_thread = None# the thread of move state
    movestate_last_relative_px = 0
    movestate_last_relative_py = 0
    movestate_move_change_threshold = 0.02
    movestate_move_change_ratio = 0.2

    drawer = None
    draw_circle_thread = None


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


    def get_hand_state(self, hand):
        fingers = self.fingersUp(hand)
        # print(fingers)

        # 0,1,2,3,4 分别代表 大拇指，食指，中指，无名指，小拇指
        if fingers == [0, 1, 0, 0, 0]:
            return HandState.only_index_up
        elif fingers == [0, 1, 1, 0, 0]:
            return HandState.index_and_middle_up
        elif fingers == [0, 1, 1, 1, 0]:
            return HandState.three_fingers_up
        elif fingers == [0, 1, 1, 1, 1]:
            return HandState.four_fingers_up
        elif fingers == [1, 1, 1, 1, 1]:
            return HandState.stop_gesture
        elif fingers == [1, 0, 0, 0, 1]:
            return HandState.voice_gesture_start
        elif fingers == [0, 0, 0, 0, 0]:
            return HandState.voice_gesture_stop
        # 拇指在左边，其他全收起 手势判断
        elif (hand['lmList'][4][0] > (hand['lmList'][8][0] + 20)
              and hand['lmList'][4][0] > (hand['lmList'][12][0] + 20)
              and hand['lmList'][4][0] > (hand['lmList'][16][0] + 20)
              and hand['lmList'][4][0] > (hand['lmList'][20][0] + 20)
              and fingers == [1, 0, 0, 0, 0]):
            return HandState.delete_gesture
        else:
            return HandState.other

    def draw_mouse_move_box(self, img) -> np.ndarray:
        cv2.rectangle(img, (frameR, frameR), (wCam - frameR, hCam - frameR),
                      (255, 0, 255), 2)
        return img

    # 配置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    def process(self, all_hands: List[dict]):
        # 处理当前状态
        self.current_hand_state
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
                    # hand_state = self.get_hand_state(hand)
                    
                    # logging.info(f"process_normal hand_state: {hand_state}")
                    # continue
                    finger_status = self.get_all_fingers_status(hand)
                    if finger_status[1::] == [1, 1, 1, 1] or finger_status == [0, 1, 1, 1, 1] and self.detect_single_finger_state(hand["lmList"], 1) == FingerStatus.STRAIGHT_UP:
                        return "wait"
            return "normal"

        def process_move(all_hands):
            # move mouse
            if all_hands:
                for hand in all_hands:
                    if hand["type"] == self.movestate_hand_type:
                        # finger_status = self.get_all_fingers_status(hand)
                        # x2, y2, z2 = self.get_pixels(hand, 12, False, True) # 中指指尖
                        # x1, y1, z1 = self.get_pixels(hand, 8 , False, True) # 食指指尖
                        
                        # if self.is_false_touch():
                        #     return

                        # length  = self.cal_3Ddistance((x1, y1, z1), (x2, y2, z2))
                        # logging.info(f"process_move two fingers dis: {length}")

                        # if length < 30 and not self.mouse_left_button_down:
                        #     self.mouse_left_button_down = True
                        #     mouse.press(Button.left)
                        # if length > 40 and self.mouse_left_button_down:
                        #     self.mouse_left_button_down = False
                        #     mouse.release(Button.left)

                        # if length < 80:
                        #     continue



                            # current_time = time.time()
                            # if not current_time - self.last_click_time > 0.5:  # 点击间隔 0.5s
                            #     return

                            # mouse.click(Button.left, 1)
                            # print(length)
                            # self.last_click_time = current_time
                        # continue


                        # if self.movestate_base_finger == 1:
                        #     index_tip_pixels = self.get_pixels(hand, 8) # 食指指尖
                        # elif self.movestate_base_finger == 2:
                        #     index_tip_pixels = self.get_pixels(hand, 12) # 中指指尖
                        index_tip_pixels = self.get_pixels(hand, 8) # 食指指尖
                        # if length > 40 and self.movestate_base_finger == 2:
                        #     # 重新设置当前坐标
                        #     self.movestate_base_finger = 1
                        #     enter_move((index_tip_pixels[0]-self.movestate_last_relative_px,index_tip_pixels[1]-self.movestate_last_relative_py), self.movestate_hand_type,1)
                        # elif length < 40:
                        #     if self.movestate_base_finger == 1:
                        #         self.movestate_base_finger = 2
                        
                        #     continue

                        if index_tip_pixels:
                            # 计算相对于移动中心的坐标
                            relative_pixelx = index_tip_pixels[0] - self.movestate_start_center[0]
                            relative_pixely = index_tip_pixels[1] - self.movestate_start_center[1]
                            # 对坐标进行滤波
                            if not hasattr(process_move, "rpx"):
                                process_move.rpx = relative_pixelx  
                                process_move.rpy = relative_pixely                            
                            update_ratio = 0.2
                            process_move.rpx = process_move.rpx * (1-update_ratio) + relative_pixelx * update_ratio
                            process_move.rpy = process_move.rpy * (1-update_ratio) + relative_pixely * update_ratio

                            # 计算坐标变化量
                            relative_move_x = (process_move.rpx - self.movestate_last_relative_px)
                            relative_move_y = (process_move.rpy - self.movestate_last_relative_py)
                            self.movestate_last_relative_px = process_move.rpx
                            self.movestate_last_relative_py = process_move.rpy
                            # 更新移动速度                            
                            if not hasattr(process_move, "last_time_v"):
                                process_move.last_time_v = time.time()  # 初始化静态变量global sum_dx=0
                                dt = 0
                            elif process_move.last_time_v < time.time()-1:
                                process_move.last_time_v = time.time()
                                dt = 0
                            else:
                                dt = time.time() - process_move.last_time_v
                                process_move.last_time_v = time.time()
                            if dt == 0:
                                continue                            
                            relative_move_dis = (relative_move_x**2 + relative_move_y**2)**0.5
                            relative_move_v = relative_move_dis / dt
                            update_ratio = 0.2
                            if relative_move_v < self.movestate_move_v:
                                update_ratio = 1-update_ratio
                            self.movestate_move_v = self.movestate_move_v * (1-update_ratio) + relative_move_v * update_ratio
                            if relative_move_v < 0.0001:
                                continue
                            
                            # 计算直接鼠标移动的距离
                            move_dis = dt*self.movestate_move_v
                            scaling = min(move_dis, relative_move_dis)/relative_move_dis
                            move_x = relative_move_x * scaling
                            move_y = relative_move_y * scaling
                            # low pass filter
                            if not hasattr(process_move, "dx"):
                                process_move.dx = 0  # 初始化静态变量global sum_dx=0
                            if not hasattr(process_move, "dy"):
                                process_move.dy = 0  # 初始化静态变量global sum_dx=0
                            update_ratio = 0.2
                            process_move.dx = process_move.dx * (1-update_ratio) + move_x * update_ratio
                            process_move.dy = process_move.dy * (1-update_ratio) + move_y * update_ratio
                            if not hasattr(process_move, "sum_dy"):
                                process_move.sum_dy = 0  # 初始化静态变量global sum_dx=0
                            if not hasattr(process_move, "sum_dx"):
                                process_move.sum_dx = 0  # 初始化静态变量global sum_dx=0
                            sum_dx = process_move.sum_dx
                            sum_dy = process_move.sum_dy
                            sum_dx += -process_move.dx * self.movestate_sensitivity
                            sum_dy += process_move.dy * self.movestate_sensitivity

                            ## 计算摇杆移动鼠标的距离
                            # 绘制摇杆圆
                            self.drawer.move_small_circle(-process_move.rpx/self.movestate_threshold, process_move.rpy/self.movestate_threshold)
                            # DrawInScreen.draw_cycle(False, self.movestate_threshold, -process_move.rpx, process_move.rpy)
                            # 判断是否超过阈值
                            relative_move_dis = (process_move.rpx**2 + process_move.rpy**2)**0.5
                            relative_move_dis = min(relative_move_dis, 2*self.movestate_threshold)
                            if relative_move_dis > self.movestate_threshold:
                                # 计算实际需要移动的距离
                                scaling = 10*(relative_move_dis-self.movestate_threshold)**2 / relative_move_dis #非线性提速
                                move_x = process_move.rpx * scaling
                                move_y = process_move.rpy * scaling

                                sum_dx += -move_x * self.movestate_sensitivity
                                sum_dy += move_y * self.movestate_sensitivity

                            # 移动鼠标
                            mouse.move(math.modf(sum_dx)[1], math.modf(sum_dy)[1])
                            # 重置累积距离
                            process_move.sum_dx = math.modf(sum_dx)[0]
                            process_move.sum_dy = math.modf(sum_dy)[0]
                            logging.info(f"process_move : {math.modf(sum_dx)[1]} {math.modf(sum_dy)[1]}")



            # state change
            if all_hands:
                for hand in all_hands:
                    finger_status = self.get_all_fingers_status(hand)
                    if finger_status[1::] == [1, 1, 1, 1] or finger_status == [0, 1, 1, 1, 1] and self.detect_single_finger_state(hand["lmList"], 1) == FingerStatus.STRAIGHT_UP:
                        return "wait"
            return "move"
        def enter_move(tip_pixels, hand_type, base_finger=1):
            self.movestate_start_center = (tip_pixels[0], tip_pixels[1]+self.movestate_threshold)
            (self.movestate_dyn_cx, self.movestate_dyn_cy) = self.movestate_start_center
            self.movestate_hand_type = hand_type
            self.movestate_last_relative_px = 0
            self.movestate_last_relative_py = 0
            self.movestate_base_finger = base_finger
            # DrawInScreen.draw_cycle(True, self.movestate_threshold, 0,0)

            process_move.rpx = 0  
            process_move.rpy = -self.movestate_threshold

            if self.drawer is not None and self.draw_circle_thread is not None and self.draw_circle_thread.is_alive():
                self.drawer.show()
            else:
                self.drawer, self.draw_circle_thread = DrawInScreen.init_drawcircle_thread()
                self.drawer.show()
        
        def exit_move():
            self.drawer.hide()

        def process_wait(all_hands):
            if time.time() - self.state_change_time > 5:
                return "normal"
            if all_hands:
                for hand in all_hands:
                    finger_status = self.get_all_fingers_status(hand)
                    if finger_status[1::] == [1, 0, 0, 0]and self.detect_single_finger_state(hand["lmList"], 1) == FingerStatus.STRAIGHT_UP:
                        enter_move(self.get_pixels(hand), hand["type"])
                        logging.info(f"enter_move : {self.movestate_start_center}")
                        return "move"
                    elif not self.is_false_touch() and finger_status[1::] == [0, 0, 0, 0]:
                        return "press"
                        # current_time = time.time()
                        # if not current_time - self.last_click_time > 0.5:  # 点击间隔 0.5s
                        #     return "normal"

                        # mouse.click(Button.left, 1)
                        # # print(length)
                        # self.last_click_time = current_time
            return "wait"

        def enter_wait(all_hands):
            self.state_change_time = time.time()

        def process_press(all_hands):
            # mouse.release(Button.left)
            # current_time = time.time()
            # if not current_time - self.last_click_time > 0.5:  # 点击间隔 0.5s
            #     return "normal"

            # mouse.click(Button.left, 1)
            # # print(length)
            # self.last_click_time = current_time
            if time.time() - self.state_change_time > 0.5:
                mouse.click(Button.left, 1)
                return "normal"
            if all_hands:
                for hand in all_hands:
                    finger_status = self.get_all_fingers_status(hand)
                    if finger_status[1::] == [1, 0, 0, 0] and self.detect_single_finger_state(hand["lmList"], 1) == FingerStatus.STRAIGHT_UP:
                        mouse.press(Button.left)
                        return "move"
                    elif finger_status[1::] == [1, 1, 1, 1] and self.detect_single_finger_state(hand["lmList"], 1) == FingerStatus.STRAIGHT_UP:
                        mouse.click(Button.left, 2)
                        return "wait"
            return "press"
                    
        def enter_press(all_hands):
            self.state_change_time = time.time()
        
        # def enter_move(all_hands):

        self.state_machine.add_state("normal", process_normal)
        self.state_machine.add_state("move", process_move, None, exit_move)
        self.state_machine.add_state("wait", process_wait, enter_wait)
        self.state_machine.add_state("press", process_press, enter_press)