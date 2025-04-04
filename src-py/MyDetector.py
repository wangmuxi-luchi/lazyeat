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
from Joystick import JoystickController

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

    # 拇指和小指同时竖起 - 语音识别
    six_gesture = 'six_gesture'  #wait模式下，开始语音识别
    fist_gesture = 'fist_gesture' # 结束语音识别，在wait模式下点击鼠标

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

    
    cur_left_hand_state = None
    cur_right_hand_state = None
    pre_left_hand_state = None
    pre_right_hand_state = None

    mouse_joystick = JoystickController()

    wrong_hand_count = 0

    last_left_state_change_time = 0
    last_right_state_change_time = 0
    # movestate_start_center = []# the pixels in the start of move state
    # movestate_dyn_cx = 0 # the x coordinate of the center of the hand in move state
    # movestate_dyn_cy = 0 # the y coordinate of the center of the hand in move state
    state_hand_type = None # the type of hand in move state
    move_sensitivity = 150# 鼠标灵敏度
    scroll_sensitivity = 3# 滚动灵敏度
    move_threshold = 0.5 # 摇杆移动阈值
    scroll_threshold = 0.5 # 摇杆移动阈值

    mouse_left_button_down = False
    mouse_right_button_down = False
    pressed_button = None

    # 滞回比较器控制点击阈值
    click_threshold_min = 0.33 # 点击阈值
    click_threshold_max = 0.38 # 点击阈值

    # tipdis_threshold = 100 # 指尖距离阈值，超过这个距离就不移动

    movestate_base_finger = 1 # 移动基于哪根手指指尖，1代表食指，2代表中指，3代表无名指，4代表小拇指



    # movestate_move_change_threshold = 0.02
    # movestate_move_change_ratio = 0.2
    # movestate_move_v = 0 # 鼠标动态移动速度
    # movestate_thread = None# the thread of move state
    # movestate_last_relative_px = 0
    # movestate_last_relative_py = 0


    def __init__(self, mode=False, maxHands=2, detectionCon=0.5, minTrackCon=0.5):
        super().__init__(mode, maxHands, detectionCon, minTrackCon)
        logging.info('MyDetector init')

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
        logging.info('MyDetector init state machine')
        self.init_state_machine()
        # 初始化摇杆
        logging.info('MyDetector init joystick')
        self.mouse_joystick.set(self.move_sensitivity, self.move_threshold)

    def shutdown(self):
        self.mouse_joystick.shutdown()

    def get_hand_state(self, hand):
        fingers = self.get_all_fingers_status(hand)
        second_finger_pos = self.get_pixels(hand, 1, 3)
        last_finger_pos = self.get_pixels(hand, 4, 3)
        delt_x = second_finger_pos[0] - last_finger_pos[0]
        if hand['type'] == 'Left' and delt_x > -0.6:
            # logging.info(f"left hand delt_x: {delt_x}")
            return HandState.other
        if hand['type'] == 'Right' and delt_x < 0.6:
            # logging.info(f"right hand delt_x: {delt_x}")
            return HandState.other

        # 0,1,2,3,4 分别代表 大拇指，食指，中指，无名指，小拇指
        if fingers[1::] == [1, 0, 0, 0]:
            return HandState.only_index_up
        elif fingers[1::] == [1, 1, 0, 0]:
            return HandState.index_and_middle_up
        elif fingers[1::] == [1, 1, 1, 0]:
            return HandState.three_fingers_up
        elif fingers == [0, 0, 0, 0, 0]:
            return HandState.fist_gesture
        elif fingers == [0, 1, 1, 1, 1]:
            return HandState.four_fingers_up
        elif fingers == [1, 1, 1, 1, 1]:
            return HandState.stop_gesture
        elif fingers == [1, 0, 0, 0, 1]:
            return HandState.six_gesture
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

    
    def process(self, all_hands: List[dict]):
        # 没有手
        if len(all_hands) <= 0:
            return
        # 处理当前状态
        self.pre_left_hand_state = self.cur_left_hand_state
        self.pre_right_hand_state = self.cur_right_hand_state
        self.cur_left_hand_state = None
        self.cur_right_hand_state = None
        for hand in all_hands:
            hand_state = self.get_hand_state(hand)
            if hand['type'] == 'Left':
                self.cur_left_hand_state = hand_state
                if self.cur_left_hand_state != self.pre_left_hand_state:
                    self.last_change_flag_time = time.time()

                # second_finger_pos = self.get_pixels(hand, 1, 0, is_3D=True)
                # first_finger_pos = self.get_pixels(hand, 0, 0, is_3D=True)
                # delt_x = second_finger_pos[0] - first_finger_pos[0]
                # delt_y = second_finger_pos[1] - first_finger_pos[1]
                # delt_z = second_finger_pos[2] - first_finger_pos[2]
                # dis = math.sqrt(delt_x**2 + delt_y**2 + delt_z**2)
                # # logging.info(f"左手状态: {hand_state} 第二根手指位置: {second_finger_pos} 第五根手指位置: {last_finger_pos}")
                # logging.info(f"左手状态: {hand_state} 距离: {dis}")
            else:
                self.cur_right_hand_state = hand_state
                if self.cur_right_hand_state!= self.pre_right_hand_state:
                    self.last_right_state_change_time = time.time()


                # second_finger_pos = self.get_pixels(hand, 1, 0, is_3D=True)
                # first_finger_pos = self.get_pixels(hand, 0, 0, is_3D=True)
                # delt_x = second_finger_pos[0] - first_finger_pos[0]
                # delt_y = second_finger_pos[1] - first_finger_pos[1]
                # delt_z = second_finger_pos[2] - first_finger_pos[2]
                # dis = math.sqrt(delt_x**2 + delt_y**2 + delt_z**2)
                # logging.info(f"左手状态: {hand_state} 第二根手指位置: {second_finger_pos} 第五根手指位置: {last_finger_pos}")
                # logging.info(f"右手状态: {hand_state} 距离:{self.cal_palm_width(hand)} {self.cal_point_dis(hand, 5,17)}")
                # logging.info(f"右手状态: {hand_state} 距离:{self.cal_finger_tip_dis(hand,0,1)} ")
                
        # return
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

    def mouse_button_press(self, button):
        if button == Button.left and not self.mouse_left_button_down:
            self.mouse_left_button_down = True
            mouse.press(Button.left)
        elif button == Button.right and not self.mouse_right_button_down:
            self.mouse_right_button_down = True
            mouse.press(Button.right)

    def mouse_button_release(self, button):
        if button == Button.left and self.mouse_left_button_down:
            self.mouse_left_button_down = False
            mouse.release(Button.left)
        elif button == Button.right and self.mouse_right_button_down:
            self.mouse_right_button_down = False
            mouse.release(Button.right)
    
    def mouse_button_clear(self):
        for button in [Button.left, Button.right]:
            self.mouse_button_release(button)

    def init_state_machine(self):
        self.state_machine = StateMachine("normal")

        # 添加状态及处理函数
        def process_normal(all_hands):
            # 暂停识别
            if len(all_hands) == 2:
                right_hand = all_hands[0]
                left_hand = all_hands[1]

                # 两只手的类型相同, 不处理
                if right_hand['type'] == left_hand['type']:
                    return "normal"

                right_hand_state = self.get_hand_state(right_hand)
                left_hand_state = self.get_hand_state(left_hand)

                # 暂停/开始 识别
                if right_hand_state == HandState.stop_gesture and left_hand_state == HandState.stop_gesture:
                    current_time = time.time()
                    if current_time - self.last_change_flag_time > 1.5:
                        return "pause"

            elif len(all_hands) >= 1:
                for hand in all_hands:
                    hand_state = self.get_hand_state(hand)
                    if hand_state == HandState.stop_gesture:
                        return "wait", (hand["type"],)
                        pass
                
                    # logging.info(f"process_normal hand_state: {hand_state}")
                # return "normal"
                # finger_status = self.get_all_fingers_status(hand)
                # if finger_status[1::] == [1, 1, 1, 1] or finger_status == [0, 1, 1, 1, 1] and self.detect_single_finger_state(hand["lmList"], 1) == FingerStatus.STRAIGHT_UP:
                #     return "wait"
            return "normal"

        def process_pause(all_hands):
            if len(all_hands) == 2:
                right_hand = all_hands[0]
                left_hand = all_hands[1]

                # 两只手的类型相同, 不处理
                if right_hand['type'] == left_hand['type']:
                    return "pause"

                right_hand_state = self.get_hand_state(right_hand)
                left_hand_state = self.get_hand_state(left_hand)

                # 暂停/开始 识别
                if right_hand_state == HandState.stop_gesture and left_hand_state == HandState.stop_gesture:
                    current_time = time.time()
                    if current_time - self.last_change_flag_time > 1.5:
                        return "normal"
            return "pause"
        
        def toggle_pause():
            show_toast(
                msg='继续手势识别' if self.flag_detect else '暂停手势识别',
                duration=1
            )
            self.last_change_flag_time = time.time()

        def process_move(all_hands):
            # move mouse
            if len(all_hands) > 0:
                for hand in all_hands:
                    if hand["type"] == self.state_hand_type:
                        index_tip_pixels = self.get_pixels(hand, 1) # 食指指尖
                        if index_tip_pixels:
                            # move_x,move_y = self.mouse_joystick.calculate_movement(index_tip_pixels[0], index_tip_pixels[1])
                            
                            dis02 = self.cal_finger_tip_dis(hand,0,2)# 计算拇指到中指的距离
                            dis03 = self.cal_finger_tip_dis(hand,0,3)# 计算拇指到无名指的距离
                            
                            tem_button = None
                            if self.pressed_button is None:
                                button_control_dis = min(dis02,dis03)
                                if dis02 > dis03:
                                    sign_dis = -button_control_dis
                                    tem_button = Button.right
                                else:
                                    sign_dis = button_control_dis
                                    tem_button = Button.left
                            elif self.pressed_button == Button.right:
                                button_control_dis = dis03
                                sign_dis = -button_control_dis
                            elif self.pressed_button == Button.left:
                                button_control_dis = dis02
                                sign_dis = button_control_dis
                            else:
                                button_control_dis = min(dis02,dis03)
                                if dis02 > dis03:
                                    sign_dis = -button_control_dis
                                    tem_button = Button.right
                                else:
                                    sign_dis = button_control_dis
                                    tem_button = Button.left
                                self.pressed_button = None
                            


                            if button_control_dis < self.click_threshold_min and self.pressed_button is None:
                                self.pressed_button = tem_button
                                self.mouse_button_press(self.pressed_button)
                                self.mouse_joystick.set_control_threshold(self.click_threshold_max)
                                # logging.info(f"process_move : {dis02} {dis03}")
                                # time.sleep(0.25)
                            if button_control_dis > self.click_threshold_max :
                                if self.pressed_button is not None and self.pressed_button in [Button.left,Button.right]:
                                    self.mouse_button_release(self.pressed_button)
                                self.mouse_joystick.set_control_threshold(self.click_threshold_min)
                                self.pressed_button = None
                            

                            move_x,move_y = self.mouse_joystick.calculate_movement(index_tip_pixels[0], index_tip_pixels[1],sign_dis)
                            # 计算相对位置
                            mouse.move(move_x,move_y)

                            # 扩展快捷点击
                            # logging.info(f"process_move : {move_x} {move_y}")
                    elif len(all_hands) == 1:
                        self.wrong_hand_count += 1
                        if self.wrong_hand_count > 10:
                            self.wrong_hand_count = 0
                            self.state_hand_type = hand["type"]
                            logging.info(f"process_move : change state_hand_type to {self.state_hand_type}")

            # state change
            if all_hands:
                for hand in all_hands:
                    finger_status = self.get_all_fingers_status(hand)
                    if finger_status[1::] == [1, 1, 1, 1] or finger_status == [0, 1, 1, 1, 1] and self.detect_single_finger_state(hand, 1) == FingerStatus.STRAIGHT_UP:
                        return "wait",(hand["type"],)
            return "move"
        def enter_move(tip_pixels=None, hand_type=None, base_finger=1):
            # 显示摇杆
            self.mouse_joystick.show()
            if tip_pixels is None:
                return False

            self.wrong_hand_count = 0
            self.mouse_joystick.set_top(tip_pixels[0], tip_pixels[1])
            self.mouse_joystick.set_sensitivity(self.move_sensitivity)
            self.mouse_joystick.set_threshold(self.move_threshold)
            self.mouse_joystick.set_control_mode(2, self.click_threshold_min)
            self.state_hand_type = hand_type

            self.mouse_button_clear()
            return True
            # self.movestate_base_finger = base_finger
            # self.movestate_start_center = (tip_pixels[0], tip_pixels[1]+self.movestate_threshold)
            # (self.movestate_dyn_cx, self.movestate_dyn_cy) = self.movestate_start_center
            # self.movestate_last_relative_px = 0
            # self.movestate_last_relative_py = 0
            # # DrawInScreen.draw_cycle(True, self.movestate_threshold, 0,0)

            # process_move.rpx = 0  
            # process_move.rpy = -self.movestate_threshold

        
        def exit_move():
            self.mouse_button_clear()
            self.mouse_joystick.hide()
        

        def process_scroll(all_hands):
            # scroll mouse
            if len(all_hands) > 0:
                for hand in all_hands:
                    if hand["type"] == self.state_hand_type:
                        index_tip_pixels = self.get_pixels(hand, 1) # 指尖
                        if index_tip_pixels:
                            scroll_x,scroll_y = self.mouse_joystick.calculate_movement(index_tip_pixels[0], index_tip_pixels[1],self.cal_finger_tip_dis(hand,0,2))
                            # 计算相对位置
                            mouse.scroll(scroll_x,scroll_y)
                            # logging.info(f"process_scroll : {scroll_x} {scroll_y}")
                    elif len(all_hands) == 1:
                        self.wrong_hand_count += 1
                        if self.wrong_hand_count > 10:
                            self.wrong_hand_count = 0
                            self.state_hand_type = hand["type"]
                            logging.info(f"process_scroll : change state_hand_type to {self.state_hand_type}")

            # state change
            if all_hands:
                for hand in all_hands:
                    if hand["type"] != self.state_hand_type:
                        continue

                    hand_state = self.get_hand_state(hand)
                    if hand_state == HandState.stop_gesture:
                        return "wait",(hand["type"],)
                        
            return "scroll"
        
        def enter_scroll(tip_pixels=None, hand_type=None, base_finger=1):
            # 显示摇杆
            self.mouse_joystick.show()
            if tip_pixels is None:
                return False

            self.wrong_hand_count = 0
            self.mouse_joystick.set_top(tip_pixels[0], tip_pixels[1])
            self.mouse_joystick.set_sensitivity(self.scroll_sensitivity)
            self.mouse_joystick.set_threshold(self.scroll_threshold)
            self.mouse_joystick.set_control_mode(1)
            self.state_hand_type = hand_type
            return True

        def exit_scroll():
            self.mouse_joystick.hide()  

        def process_wait(all_hands):
            if time.time() - self.state_change_time > 5:
                return "normal"
            if all_hands:
                for hand in all_hands:
                    if hand['type'] == 'Left':
                        hand_state = self.cur_left_hand_state
                        pre_hand_state = self.pre_left_hand_state
                        last_state_change_time = self.last_left_state_change_time
                    else:
                        hand_state = self.cur_right_hand_state
                        pre_hand_state = self.pre_right_hand_state
                        last_state_change_time = self.last_right_state_change_time

                    if hand_state == HandState.only_index_up:
                        if time.time() - last_state_change_time > 0.1:
                            return "move",(self.get_pixels(hand),hand["type"])
                    elif hand_state == HandState.three_fingers_up:
                        if time.time() - last_state_change_time > 0.1:
                            return "scroll",(self.get_pixels(hand,1),hand["type"])
                    # elif hand_state == HandState.fist_gesture:
                    #     if time.time() - last_state_change_time > 0.1:
                    #         return "press"
                    elif hand_state == HandState.six_gesture:
                        if time.time() - last_state_change_time > 0.1:
                            return "voice",(hand["type"],)
                    elif hand_state == HandState.delete_gesture:
                        if time.time() - last_state_change_time > 0.1:
                            keyboard.tap(Key.backspace)
                    elif hand_state == HandState.four_fingers_up:
                        if time.time() - last_state_change_time > 0.1:
                            self._four_fingers_up_trigger()
                
            return "wait"

        def enter_wait(hand_type):
            self.state_hand_type = hand_type
            self.state_change_time = time.time()
            return True

        def process_press(all_hands):
            # mouse.release(Button.left)
            # current_time = time.time()
            # if not current_time - self.last_click_time > 0.5:  # 点击间隔 0.5s
            #     return "normal"

            # mouse.click(Button.left, 1)
            # self.last_click_time = current_time
            if time.time() - self.state_change_time > 0.5:
                mouse.click(Button.left, 1)
                return "normal"
            if all_hands:
                for hand in all_hands:
                    finger_status = self.get_all_fingers_status(hand)
                    # if finger_status[1::] == [1, 0, 0, 0] and self.detect_single_finger_state(hand["lmList"], 1) == FingerStatus.STRAIGHT_UP:
                    #     mouse.press(Button.left)
                    #     return "move"
                    # el
                    if finger_status[1::] == [1, 1, 1, 1] and self.detect_single_finger_state(hand, 1) == FingerStatus.STRAIGHT_UP:
                        mouse.click(Button.left, 2)
                        return "wait",(hand["type"],)
            return "press"
                    
        def enter_press():
            self.state_change_time = time.time()
            return True
        
        def process_voice(all_handsf):
            # if not self.voice_controller:
            #     return "normal"
            for state in [self.cur_left_hand_state,self.cur_right_hand_state]:
                if state == None:
                    continue
                if state == HandState.stop_gesture:
                    return "normal"
            return "voice"

        def enter_voice(hand_type=None):
            if not self.voice_controller or hand_type == None:
                return False
            self.voice_controller.start_record_thread()
            show_toast(
                title='开始语音识别',
                msg='开始语音识别',
                duration=1
            )
            self.state_hand_type = hand_type
            return True

        def exit_voice():
            self.voice_controller.stop_record()
            show_toast(
                title='结束语音识别',
                msg='结束语音识别',
                duration=1
            )

            text = self.voice_controller.transcribe_audio()
            # 将文本输入到当前焦点的应用程序
            if text:
                keyboard.type(text)
                keyboard.tap(Key.enter)


        
        # def enter_move(all_hands):

        self.state_machine.add_state("normal", process_normal)
        self.state_machine.add_state("move", process_move, enter_move, exit_move)
        self.state_machine.add_state("wait", process_wait, enter_wait)
        self.state_machine.add_state("press", process_press, enter_press)
        self.state_machine.add_state("pause", process_pause, toggle_pause, toggle_pause)
        self.state_machine.add_state("scroll", process_scroll, enter_scroll, exit_scroll)
        self.state_machine.add_state("voice", process_voice, enter_voice, exit_voice)