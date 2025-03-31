import cv2
import mediapipe as mp
import math
import logging
from enum import Enum

# 定义手指状态的枚举
class FingerStatus(Enum):
    STRAIGHT_UP = 2  # 手指伸直且指向上方
    STRAIGHT = 1     # 手指伸直
    BENT = 0         # 手指弯曲
    OTHER = -1       # 其他状态

class HandDetector:
    """
    利用mediapipe寻找手， 得到手部关键点坐标. 能够检测出多少只手指是伸张的
    以及两个手指指尖的距离 ，对检测到的手计算它的锚框.
    """
    # 配置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    img_width = 0
    img_height = 0
    
    def __init__(self, mode=False, maxHands=2, detectionCon=0.5, minTrackCon=0.5):
        """
        :param mode: 在静态模式会对没一张图片进行检测：比较慢
        :param maxHands: 检测到手的最大个数
        :param detectionCon: 最小检测阈值
        :param minTrackCon: 最小追踪阈值
        """
        self.mode = mode
        self.maxHands = maxHands
        self.detectionCon = detectionCon
        self.minTrackCon = minTrackCon

        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(static_image_mode=self.mode, max_num_hands=self.maxHands,
                                        min_detection_confidence=self.detectionCon,
                                        min_tracking_confidence=self.minTrackCon)
        self.mpDraw = mp.solutions.drawing_utils
        self.tipIds = [4, 8, 12, 16, 20]  # 从大拇指开始，依次为每个手指指尖
        self.fingers = []
        self.lmList = []

    def findPosition(self, img, handNo=0, draw=True):
        xList = []
        yList = []
        bbox = []
        self.lmList = []
        if self.results.multi_hand_landmarks:
            myHand = self.results.multi_hand_landmarks[handNo]
            for id, lm in enumerate(myHand.landmark):
                # print(id, lm)
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                xList.append(cx)
                yList.append(cy)
                # print(id, cx, cy)
                self.lmList.append([id, cx, cy])
                if draw:
                    cv2.circle(img, (cx, cy), 5, (255, 0, 255), cv2.FILLED)

            xmin, xmax = min(xList), max(xList)
            ymin, ymax = min(yList), max(yList)
            bbox = xmin, ymin, xmax, ymax

            if draw:
                cv2.rectangle(img, (xmin - 20, ymin - 20), (xmax + 20, ymax + 20),
                              (0, 255, 0), 2)

        return self.lmList, bbox

    def findHands(self, img, draw=True, flipType=True):
        """
        Finds hands in a BGR image.
        :param img: Image to find the hands in.
        :param draw: Flag to draw the output on the image.
        :return: Image with or without drawings
        """
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)

        allHands = []
        h, w, c = img.shape
        (self.img_height, self.img_width, _) = img.shape
        # print("multi_hand_landmarks")
        # print(self.results.multi_hand_landmarks)
        # print("self.results.multi_handedness")
        # print(self.results.multi_handedness)
        # self.results.multi_hand_landmarks为21个landmark,21个关键点信息
        # landmark
        # {
        #     x: 0.08329735696315765
        #     y: 0.861643373966217
        #     z: 8.069470709415327e-07
        # }

        # self.results.multi_handedness"
        # [classification {
        #     index: 0   代表手的索引号，第几个手掌
        #     score: 0.5836966037750244
        #     label: "Left"
        # }
        #  ]


        if self.results.multi_hand_landmarks:
            for handType, handLms in zip(self.results.multi_handedness, self.results.multi_hand_landmarks):
                myHand = {}
                ## lmList
                mylmList = []
                xList = []
                yList = []
                for id, lm in enumerate(handLms.landmark):
                    px, py, pz = int(lm.x * w), int(lm.y * h), int(lm.z * w)
                    mylmList.append([px, py, pz])
                    xList.append(px)
                    yList.append(py)

                ## bbox
                xmin, xmax = min(xList), max(xList)  # 取最大数值
                ymin, ymax = min(yList), max(yList)
                boxW, boxH = xmax - xmin, ymax - ymin
                bbox = xmin, ymin, boxW, boxH
                cx, cy = bbox[0] + (bbox[2] // 2), \
                         bbox[1] + (bbox[3] // 2)

                myHand["lmList"] = mylmList
                myHand["bbox"] = bbox
                myHand["center"] = (cx, cy)

                if flipType:
                    if handType.classification[0].label == "Right":
                        myHand["type"] = "Left"
                    else:
                        myHand["type"] = "Right"
                else:
                    myHand["type"] = handType.classification[0].label
                allHands.append(myHand)

                ## draw
                if draw:
                    self.mpDraw.draw_landmarks(img, handLms,
                                               self.mpHands.HAND_CONNECTIONS)
                    cv2.rectangle(img, (bbox[0] - 20, bbox[1] - 20),
                                  (bbox[0] + bbox[2] + 20, bbox[1] + bbox[3] + 20),
                                  (255, 0, 255), 2)  #红蓝为 紫色
                    cv2.putText(img, myHand["type"], (bbox[0] - 30, bbox[1] - 30), cv2.FONT_HERSHEY_PLAIN,
                                2, (255, 0, 255), 2)
        if draw:
            return allHands, img
        else:
            return allHands

    def fingersUp(self, myHand):
        """
        Finds how many fingers are open and returns in a list.
        Considers left and right hands separately
        :return: List of which fingers are up
        """
        myHandType = myHand["type"]
        myLmList = myHand["lmList"]
        if self.results.multi_hand_landmarks:
            fingers = []
            # Thumb
            if myHandType == "Right":

                if myLmList[self.tipIds[0]][0] < myLmList[self.tipIds[0] - 1][0]:
                    fingers.append(0)
                else:
                    fingers.append(1)
            else:
                if myLmList[self.tipIds[0]][0] > myLmList[self.tipIds[0] - 1][0]:
                    fingers.append(0)
                else:
                    fingers.append(1)

            # 4 Fingers
            for id in range(1, 5):
                # 其他手指指尖的y坐标小于次指尖的点的坐标，则为竖直
                if myLmList[self.tipIds[id]][1] < myLmList[self.tipIds[id] - 2][1]:
                    fingers.append(1)
                else:
                    fingers.append(0)
        return fingers

    def findDistance(self, p1, p2, img=None):
        """
        计算指尖距离
        :param p1: Point1
        :param p2: Point2
        :param img: 要绘制的图
        :param draw: 标志变量
        :return: 返回指尖距离，和绘制好的图
        """

        x1, y1 = p1
        x2, y2 = p2
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        length = math.hypot(x2 - x1, y2 - y1)
        info = (x1, y1, x2, y2, cx, cy)
        if img is not None:
            cv2.circle(img, (x1, y1), 15, (255, 0, 255), cv2.FILLED)   # 食指尖画紫圈
            cv2.circle(img, (x2, y2), 15, (255, 0, 255), cv2.FILLED)   # 中指尖画紫圈
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
            cv2.circle(img, (cx, cy), 15, (255, 0, 255), cv2.FILLED)   # 两指中间画紫圈
            return length, info, img
        else:
            return length, info

    def get_finger_status(self, myLmList, finger_id):
        """
        根据手指第一节骨头和最后一节骨头的角度判断手指是伸直还是弯曲。

        :param myLmList: 手部关键点坐标列表
        :param finger_id: 手指的 ID（0 为大拇指，1 为食指，依此类推）
        :return: 手指状态，伸直为 1，弯曲为 0
        """
        # 获取手指相关的关键点索引
        tip_id = self.tipIds[finger_id]
        if finger_id == 0:  # 大拇指
            joint1_point1 = myLmList[0][:2]
            joint1_point2 = myLmList[tip_id - 3][:2]
            joint2_point1 = myLmList[tip_id - 1][:2]
            joint2_point2 = myLmList[tip_id][:2]
            # base_id = tip_id - 2
            # mid_id = tip_id - 1
        else:
            joint1_point1 = myLmList[0][:2]
            joint1_point2 = myLmList[tip_id - 3][:2]
            joint2_point1 = myLmList[tip_id - 3][:2]
            joint2_point2 = myLmList[tip_id - 2][:2]
            # base_id = 0
            # root_id = tip_id - 3
            # base_id = tip_id - 3
            # mid_id = tip_id - 2

        # 获取关键点的坐标
        # tip_point = myLmList[tip_id][:2]
        # base_point = myLmList[base_id][:2]
        # mid_point = myLmList[mid_id][:2]

        # 计算向量
        vector1 = (joint1_point2[0] - joint1_point1[0], joint1_point2[1] - joint1_point1[1])
        vector2 = (joint2_point2[0] - joint2_point1[0], joint2_point2[1] - joint2_point1[1])
        # vector1 = (tip_point[0] - mid_point[0], tip_point[1] - mid_point[1])
        # vector2 = (base_point[0] - mid_point[0], base_point[1] - mid_point[1])

        # 计算向量的点积
        dot_product = vector1[0] * vector2[0] + vector1[1] * vector2[1]

        # 计算向量的模
        magnitude1 = math.sqrt(vector1[0] ** 2 + vector1[1] ** 2)
        magnitude2 = math.sqrt(vector2[0] ** 2 + vector2[1] ** 2)

        # 检查是否存在零向量
        if magnitude1 * magnitude2 == 0:
            cos_angle = 0
        else:
            # 计算夹角的余弦值
            cos_angle = dot_product / (magnitude1 * magnitude2)

        # 确保 cos_angle 在 [-1, 1] 范围内
        cos_angle = max(-1, min(1, cos_angle))

        # 计算夹角（弧度）
        angle = math.acos(cos_angle)

        # 将弧度转换为角度
        angle_degrees = math.degrees(angle)

        # 根据角度判断手指状态
        # return angle_degrees
        if angle_degrees < 25:  # 可根据实际情况调整阈值
            return 1  # 手指伸直
        else:
            return 0  # 手指弯曲

    def get_all_fingers_status(self, myHand):
        """
        调用 get_finger_status 方法获取五根手指的状态，并返回一个列表。

        :param myHand: 包含手部信息的字典，如关键点坐标、手部类型等
        :return: 包含五根手指状态的列表，伸直为 1，弯曲为 0
        """
        myLmList = myHand["lmList"]
        fingers_status = []

        # 处理大拇指
        thumb_status = self.get_finger_status(myLmList, 0)
        fingers_status.append(thumb_status)

        # 处理其他四根手指
        for finger_id in range(1, 5):
            finger_status = self.get_finger_status(myLmList, finger_id)
            fingers_status.append(finger_status)

        # finger_status = self.get_finger_status(myLmList, 1)
        # fingers_status.append(finger_status)

        return fingers_status


    def get_index_tip_pixels(self, myHand):
        """
        获取食指指尖的像素坐标归一化。
        :param myHand: 包含手部信息的字典，如关键点坐标、手部类型等
        :return: 食指指尖的像素坐标归一化 (x, y)
        """
        myLmList = myHand["lmList"]
        index_tip_id = self.tipIds[1]  # 食指指尖的关键点索引
        index_tip_pixels = myLmList[index_tip_id][:2]  # 获取前两个元素，即 x 和 y 坐标

        # 归一化
        normalized_x = index_tip_pixels[0] / self.img_width
        normalized_y = index_tip_pixels[1] / self.img_height
        return normalized_x, normalized_y
    
    def detect_single_finger_state(self, myLmList, finger_id):
        """
        检测单个手指的状态。

        :param myLmList: 手部关键点坐标列表
        :param finger_id: 手指的 ID（0 为大拇指，1 为食指，依此类推）
        :return: 手指的状态，使用 FingerStatus 枚举表示
        """
        # 获取手指相关的关键点索引
        tip_id = self.tipIds[finger_id]
        if finger_id == 0:  # 大拇指
            base_id = tip_id - 1
            mid_id = tip_id - 2
        else:
            base_id = tip_id - 3
            mid_id = tip_id - 2

        # 获取关键点的坐标
        tip_point = myLmList[tip_id][:2]
        base_point = myLmList[base_id][:2]
        mid_point = myLmList[mid_id][:2]

        # 计算向量
        vector1 = (tip_point[0] - mid_point[0], tip_point[1] - mid_point[1])
        vector2 = (mid_point[0] - base_point[0] , mid_point[1] - base_point[1] )

        # 计算向量的点积
        dot_product = vector1[0] * vector2[0] + vector1[1] * vector2[1]

        # 计算向量的模
        magnitude1 = math.sqrt(vector1[0] ** 2 + vector1[1] ** 2)
        magnitude2 = math.sqrt(vector2[0] ** 2 + vector2[1] ** 2)

        # 检查是否存在零向量
        if magnitude1 * magnitude2 == 0:
            cos_angle = 0
        else:
            # 计算夹角的余弦值
            cos_angle = dot_product / (magnitude1 * magnitude2)

        # 确保 cos_angle 在 [-1, 1] 范围内
        cos_angle = max(-1, min(1, cos_angle))

        # 计算夹角（弧度）
        angle = math.acos(cos_angle)

        # 将弧度转换为角度
        angle_degrees = math.degrees(angle)

        # 计算手指向量与垂直方向的夹角
        finger_vector = (tip_point[0] - base_point[0], tip_point[1] - base_point[1])
        vertical_vector = (0, -1)  # 垂直向上的向量
        dot_product_vertical = finger_vector[0] * vertical_vector[0] + finger_vector[1] * vertical_vector[1]
        magnitude_finger = math.sqrt(finger_vector[0] ** 2 + finger_vector[1] ** 2)
        magnitude_vertical = math.sqrt(vertical_vector[0] ** 2 + vertical_vector[1] ** 2)
        if magnitude_finger * magnitude_vertical == 0:
            cos_angle_vertical = 0
        else:
            cos_angle_vertical = dot_product_vertical / (magnitude_finger * magnitude_vertical)
        cos_angle_vertical = max(-1, min(1, cos_angle_vertical))
        angle_vertical = math.degrees(math.acos(cos_angle_vertical))

        logging.info(f"当前状态: {angle_degrees};{angle_vertical}")
        # 根据角度判断手指状态
        if angle_degrees < 25:  # 可根据实际情况调整阈值
            if angle_vertical < 25:  # 判断手指是否几乎垂直，可根据实际情况调整阈值
                return FingerStatus.STRAIGHT_UP
            else:
                return FingerStatus.STRAIGHT
        elif angle_degrees > 90:  # 可根据实际情况调整阈值
            return FingerStatus.BENT
        else:
            return FingerStatus.OTHER

def main():
    cap = cv2.VideoCapture(0)
    detector = HandDetector(detectionCon=0.8, maxHands=2)
    while True:
        # Get image frame
        success, img = cap.read()
        # Find the hand and its landmarks
        hands, img = detector.findHands(img)  # with draw
        # hands = detector.findHands(img, draw=False)  # without draw

        if hands:
            # Hand 1
            hand1 = hands[0]
            lmList1 = hand1["lmList"]  # List of 21 Landmark points
            bbox1 = hand1["bbox"]  # Bounding box info x,y,w,h
            centerPoint1 = hand1['center']  # center of the hand cx,cy
            handType1 = hand1["type"]  # Handtype Left or Right

            fingers1 = detector.fingersUp(hand1)

            if len(hands) == 2:
                # Hand 2
                hand2 = hands[1]
                lmList2 = hand2["lmList"]  # List of 21 Landmark points
                bbox2 = hand2["bbox"]  # Bounding box info x,y,w,h
                centerPoint2 = hand2['center']  # center of the hand cx,cy
                handType2 = hand2["type"]  # Hand Type "Left" or "Right"

                fingers2 = detector.fingersUp(hand2)

                # Find Distance between two Landmarks. Could be same hand or different hands
                length, info, img = detector.findDistance(lmList1[8][0:2], lmList2[8][0:2], img)  # with draw
                # length, info = detector.findDistance(lmList1[8], lmList2[8])  # with draw
        # Display
        cv2.imshow("Image", img)
        cv2.waitKey(1)


if __name__ == "__main__":
    main()
