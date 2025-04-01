import math
import time
import DrawInScreen


class JoystickController:
    """
    摇杆控制类，用于处理摇杆输入并生成相应的移动距离。
    """

    # 摇杆绘制器，用于绘制摇杆
    drawer = None
    # 绘制摇杆的线程
    draw_circle_thread = None
    def __init__(self, sensitivity=1.0, threshold=10, center_x=0, center_y=0):
        """
        初始化摇杆控制类。

        :param sensitivity: 灵敏度，控制移动的缩放比例，默认为 1.0
        :param threshold: 阈值，用于判断是否忽略小幅度的移动，默认为 10
        :param center_x: 中心点的 x 坐标，默认为 0
        :param center_y: 中心点的 y 坐标，默认为 0
        """
        self.sensitivity = sensitivity
        self.threshold = threshold
        self.center_x = center_x
        self.center_y = center_y
        self.move_v = 0  # 鼠标移动速度

        self.lrpx = None  # last_relative_pixelx,used for filter
        self.lrpy = None  # last_relative_pixely,used for filter
        self.last_time = None  # last time of movement,used for filter
        self.sum_dy = 0  # sum of dy,prevent decimal truncation
        self.sum_dx = 0  # sum of dx,prevent decimal truncation

        if self.drawer is not None and self.draw_circle_thread is not None and self.draw_circle_thread.is_alive():
            # self.drawer.hide()
            pass
        else:
            self.drawer, self.draw_circle_thread = DrawInScreen.init_drawcircle_thread()
            # self.drawer.hide()

    def set(self, sensitivity=1.0, threshold=10, center_x=0, center_y=0):
        """
        设置摇杆控制类的参数。

        :param sensitivity: 灵敏度，控制移动的缩放比例，默认为 1.0
        :param threshold: 阈值，用于判断是否忽略小幅度的移动，默认为 10
        :param center_x: 中心点的 x 坐标，默认为 0
        :param center_y: 中心点的 y 坐标，默认为 0
        """
        self.sensitivity = sensitivity
        self.threshold = threshold
        self.center_x = center_x
        self.center_y = center_y

    def show(self):
        """
        显示摇杆。
        """
        if self.drawer is not None and self.draw_circle_thread is not None and self.draw_circle_thread.is_alive():
            self.drawer.show()
        else:
            self.drawer, self.draw_circle_thread = DrawInScreen.init_drawcircle_thread()
            self.drawer.show()

    def hide(self):
        """
        隐藏摇杆。
        """
        if self.drawer is not None and self.draw_circle_thread is not None and self.draw_circle_thread.is_alive():
            self.drawer.hide()
        else:
            self.drawer, self.draw_circle_thread = DrawInScreen.init_drawcircle_thread()
            self.drawer.hide()

    def set_sensitivity(self, sensitivity):
        """
        设置灵敏度。

        :param sensitivity: 新的灵敏度值
        """
        self.sensitivity = sensitivity

    def set_threshold(self, threshold):
        """
        设置阈值。

        :param threshold: 新的阈值
        """
        self.threshold = threshold

    def set_top(self, top_x, top_y):
        """
        设置摇杆的顶部位置。

        :param top_x: 新的顶部 x 坐标
        :param top_y: 新的顶部 y 坐标
        """
        self.center_x = top_x
        self.center_y = top_y + self.threshold

    def set_center(self, center_x, center_y):
        """
        设置中心点。

        :param center_x: 新的中心点 x 坐标
        :param center_y: 新的中心点 y 坐标
        """
        self.center_x = center_x
        self.center_y = center_y

    def calculate_movement(self, x, y):
        """
        根据输入的坐标计算移动距离。

        :param x: 输入的 x 坐标
        :param y: 输入的 y 坐标
        :return: 移动距离 (dx, dy)
        """
        # 计算相对于移动中心的坐标
        relative_pixelx = x - self.center_x
        relative_pixely = y - self.center_y
        # 对坐标进行滤波
        update_ratio = 0.2
        
        relative_move_x = lowpass_filter.filter_retdx("relative_pixelx", relative_pixelx, update_ratio)
        relative_move_y = lowpass_filter.filter_retdx("relative_pixely", relative_pixely, update_ratio)
        rpx = lowpass_filter.get_last_value("relative_pixelx")
        rpy = lowpass_filter.get_last_value("relative_pixely")
        # 绘制摇杆圆
        self.drawer.move_small_circle(-rpx/self.threshold, rpy/self.threshold)
        
        # 重置累积距离的整数部分，因为上一次返回时已经移动过了
        self.sum_dx = math.modf(self.sum_dx)[0]
        self.sum_dy = math.modf(self.sum_dy)[0]

        if self.last_time is None:# 初始化
            self.last_time = time.time()
            dt = 0
        elif self.last_time < time.time()-1:# 超过1s,重置
            self.last_time = time.time()
            dt = 0
        else:# 计算dt
            dt = time.time() - self.last_time
            self.last_time = time.time()
        if dt == 0:
            return 0, 0

        # 判断是否超过触发摇杆阈值
        relative_move_dis = (rpx**2 + rpy**2)**0.5
        relative_move_dis = min(relative_move_dis, 2*self.threshold)
        if relative_move_dis > self.threshold:
            ## 计算摇杆移动鼠标的距离
            # 计算实际需要移动的距离
            scaling = 10*dt*(relative_move_dis-self.threshold) / relative_move_dis #非线性提速
            move_x = rpx * scaling
            move_y = rpy * scaling

            self.sum_dx += -move_x * self.sensitivity
            self.sum_dy += move_y * self.sensitivity

            return math.modf(self.sum_dx)[1], math.modf(self.sum_dy)[1]
        
        # 如果没有触发摇杆，则直接滑动

        # 更新移动速度                  
        relative_move_dis = (relative_move_x**2 + relative_move_y**2)**0.5 # 计算直接移动的距离
        finger_move_v = relative_move_dis / dt # 计算指尖移动速度
        update_ratio = 0.2
        if finger_move_v < self.move_v:
            update_ratio = 1-update_ratio
        self.move_v = self.move_v * (1-update_ratio) + finger_move_v * update_ratio
        if finger_move_v < 0.0001:
            return 0, 0
        
        # 获取鼠标直接跟随手指移动的距离
        move_dis = dt*self.move_v
        scaling = min(move_dis, relative_move_dis)/relative_move_dis
        move_x = relative_move_x * scaling * self.sensitivity
        move_y = relative_move_y * scaling * self.sensitivity


        # 累加防止小数被截断
        self.sum_dx += -move_x
        self.sum_dy += move_y 
        return math.modf(self.sum_dx)[1], math.modf(self.sum_dy)[1]


class lowpass_filter:
    """
    低通滤波器类，用于对输入信号进行低通滤波。
    """
    filters = {}  # 存储滤波器的字典，键为滤波器名称，值为滤波器实例

    @classmethod
    def filter(cls,name, input_value, update_ratio=0.5):
        """
        调用指定名称的低通滤波器进行滤波。
        :param name: 滤波器名称
        :param input_value: 输入信号的值
        :return: 滤波后的信号值
        """
        if name not in cls.filters:  # 如果滤波器不存在，则创建一个新的滤波器实例
            cls.filters[name] = cls(name, update_ratio)  # 假设默认的更新比率为0.5
        return cls.filters[name].filter(input_value)  # 调用滤波器的filter方法进行滤波
    
    @classmethod
    def filter_retdx(cls,name, input_value, update_ratio=0.5):
        """
        调用指定名称的低通滤波器进行滤波。
        :param name: 滤波器名称
        :param input_value: 输入信号的值
        :return: 信号与上一次相比的的变化量
        """
        if name not in cls.filters:  # 如果滤波器不存在，则创建一个新的滤波器实例
            cls.filters[name] = cls(name, input_value,update_ratio)  # 假设默认的更新比率为0.5
        last_value = cls.filters[name].last_value  # 调用滤波器的filter方法进行滤波
        # 调用滤波器的filter方法进行滤波
        if last_value is None:  # 如果上一次的输出值为None，则直接返回输入值
            last_value = input_value
        return cls.filters[name].filter(input_value) - last_value
            
    @classmethod
    def get_last_value(cls,name):
        """
        调用指定名称的低通滤波器进行滤波。
        :param name: 滤波器名称
        :param input_value: 输入信号的值
        :return: 滤波后的信号值
        """
        if name not in cls.filters:  # 如果滤波器不存在
            return None
        return cls.filters[name].last_value
    

    def __init__(self, name, input_value,update_ratio):
        """
        初始化低通滤波器类。
        :param name: 滤波器名称，用于区分不同的滤波器
        :param update_ratio: 滤波器的更新比率，用于控制滤波的速度
        """
        self.name = name  # 滤波器名称
        self.update_ratio = update_ratio  # 滤波器的更新比率
        self.last_value = input_value  # 上一次的滤波器输出值
        self.filters[name] = self  # 将滤波器实例添加到字典中

    def filter(self, input_value):
        """
        对输入信号进行低通滤波。
        :param input_value: 输入信号的值
        :return: 滤波后的信号值
        """
        if self.last_value is None:  # 如果上一次的输出值为None，则直接返回输入值
            self.last_value = input_value
        self.last_value =  self.update_ratio * input_value + (1 - self.update_ratio) * self.last_value
        return self.last_value
    


if __name__ == "__main__":
    # 创建一个低通滤波器实例
    filter = lowpass_filter("my_filter", 1,0.5)  # 假设默认的更新比率为0.5

    # 模拟输入信号
    input_values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    # 对输入信号进行滤波
    for input_value in input_values:
        filtered_value = filter.filter(input_value)  # 调用滤波器的filter方法进行滤波
        print(f"Input: {input_value}, Filtered: {filtered_value}")

    for input_value in input_values:
        filtered_value = lowpass_filter.filter_retdx("my_filter2", input_value, 0.5)  # 调用滤波器的filter方法进行滤波
        print(f"Input: {input_value}, Filtered: {filtered_value}")