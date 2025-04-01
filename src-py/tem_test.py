
        def process_scroll(all_hands):
            # scroll mouse
            if len(all_hands) > 0:
                for hand in all_hands:
                    if hand["type"] == self.state_hand_type:
                        index_tip_pixels = self.get_pixels(hand, 8) # 食指指尖
                        if index_tip_pixels:
                            scroll_x,scroll_y = self.mouse_joystick.calculate_scrollment(index_tip_pixels[0], index_tip_pixels[1])
                            # 计算相对位置
                            mouse.scroll(scroll_x,scroll_y)
                            logging.info(f"process_scroll : {scroll_x} {scroll_y}")
                    elif len(all_hands) == 1:
                        self.wrong_hand_count += 1
                        if self.wrong_hand_count > 10:
                            self.wrong_hand_count = 0
                            self.state_hand_type = hand["type"]
                            logging.info(f"process_scroll : change state_hand_type to {self.state_hand_type}")

            # state change
            if all_hands:
                for hand in all_hands:
                    finger_status = self.get_all_fingers_status(hand)
                    if finger_status[1::] == [1, 1, 1, 1] or finger_status == [0, 1, 1, 1, 1] and self.detect_single_finger_state(hand["lmList"], 1) == FingerStatus.STRAIGHT_UP:
                        return "wait",(hand["type"],)
            return "scroll"
        def enter_scroll(tip_pixels=None, hand_type=None, base_finger=1):
            # 显示摇杆
            self.mouse_joystick.show()
            if tip_pixels is None:
                return

            self.wrong_hand_count = 0
            self.mouse_joystick.set_top(tip_pixels[0], tip_pixels[1])
            self.state_hand_type = hand_type
            # self.scrollstate_base_finger = base_finger
            # self.scrollstate_start_center = (tip_pixels[0], tip_pixels[1]+self.scrollstate_threshold)
            # (self.scrollstate_dyn_cx, self.scrollstate_dyn_cy) = self.scrollstate_start_center
            # self.scrollstate_last_relative_px = 0
            # self.scrollstate_last_relative_py = 0
            # # DrawInScreen.draw_cycle(T输入是我要输入一些身边
            f