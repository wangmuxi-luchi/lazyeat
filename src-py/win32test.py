# import win32gui
# import win32con

# # 定义消息处理函数
# def WndProc(hwnd, msg, wParam, lParam):
#     if msg == win32con.WM_DESTROY:
#         win32gui.PostQuitMessage(0)
#         return True
#     return win32gui.DefWindowProc(hwnd, msg, wParam, lParam)

# # 定义窗口类
# class_name = "SimpleWindowClass"
# window_title = "Simple Window"

# # 注册窗口类
# wc = win32gui.WNDCLASS()
# wc.hbrBackground = win32gui.GetStockObject(win32con.WHITE_BRUSH)
# wc.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
# wc.hIcon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)
# wc.lpszClassName = class_name
# wc.lpfnWndProc = WndProc  # 指定消息处理函数
# class_atom = win32gui.RegisterClass(wc)

# # 创建窗口
# hwnd = win32gui.CreateWindow(
#     class_atom,
#     window_title,
#     win32con.WS_OVERLAPPEDWINDOW,
#     100, 100, 400, 300,
#     0, 0, 0, None
# )

# # 显示窗口
# win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
# win32gui.UpdateWindow(hwnd)

# # 消息循环
# win32gui.PumpMessages()

import threading
from time import sleep
import win32gui
import win32con
import win32api
from win32con import WS_EX_LAYERED,WS_EX_TRANSPARENT,GWL_EXSTYLE,WS_EX_TOOLWINDOW,HWND_TOPMOST
from win32api import SetWindowLong
# 定义消息处理函数
def WndProc(hwnd, msg, wParam, lParam):
    if msg == win32con.WM_DESTROY:
        print("WM_DESTROY")
        win32gui.PostQuitMessage(0)
        return 0
    elif msg == win32con.WM_PAINT:
        hdc, paintStruct = win32gui.BeginPaint(hwnd)
        # 绘制矩形
        win32gui.Rectangle(hdc, 50, 50, 200, 150)
        
        # 绘制圆形
        win32gui.Ellipse(hdc, 250, 50, 350, 150)
        
        win32gui.EndPaint(hwnd, paintStruct)
        
        
        return 0
    return win32gui.DefWindowProc(hwnd, msg, wParam, lParam)


class ScreenDrawer:
    def __init__(self):
        # 定义窗口和圆圈的属性
        self.big_circle_radius = 50
        self.big_circle_color = win32api.RGB(255, 0, 0)  # 红色
        self.big_window_width = self.big_circle_radius * 2 + 4
        self.big_window_height = self.big_circle_radius * 2 + 4
        self.small_circle_radius = 5
        self.small_circle_color = win32api.RGB(255, 0, 0)  # 红色
        self.small_window_width = self.small_circle_radius * 2 + 4
        self.small_window_height = self.small_circle_radius * 2 + 4
        
        # somall circle relative position to big circle center
        self.small_circle_rx = 0
        self.small_circle_ry = 0
        # 获取屏幕分辨率
        self.screen_width = win32api.GetSystemMetrics(0)
        self.screen_height = win32api.GetSystemMetrics(1)
        self.screen_center_x = self.screen_width // 2
        self.screen_center_y = self.screen_height // 2

        # hwnd
        self.big_hwnd = None
        self.small_hwnd = None
    
    def __del__(self):
        # 释放设备上下文
        # win32gui.ReleaseDC(self.hwnd, self.dc)
        # 销毁窗口
        win32gui.DestroyWindow(self.big_hwnd)
        win32gui.DestroyWindow(self.small_hwnd)
        
        
    def init_window(self):
        # 定义窗口类
        class_name = "big_circle_window"
        # 注册窗口类
        wc = win32gui.WNDCLASS()
        wc.hbrBackground = win32gui.GetStockObject(win32con.HOLLOW_BRUSH)
        wc.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
        wc.hIcon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)
        wc.lpszClassName = class_name
        wc.lpfnWndProc = self.WndProc  # 指定消息处理函数
        class_atom = win32gui.RegisterClass(wc)

        # 计算窗口左上角的坐标，使其位于屏幕中心
        center_x = self.screen_center_x - self.big_window_width // 2
        center_y = self.screen_center_y - self.big_window_height // 2

        # 创建窗口
        window_title = "Big Window"
        self.big_hwnd = win32gui.CreateWindow(
            class_atom,
            window_title,
            win32con.WS_POPUP, 
            center_x, center_y, self.big_window_width, self.big_window_height,
            0, 0, 0, None
        )
        
        # 定义窗口类
        class_name = "small_circle_window"
        # 注册窗口类
        # wc = win32gui.WNDCLASS()
        # wc.hbrBackground = win32gui.GetStockObject(win32con.WHITE_BRUSH)
        # wc.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
        # wc.hIcon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)
        # wc.lpfnWndProc = self.WndProc  # 指定消息处理函数
        wc.lpszClassName = class_name
        class_atom = win32gui.RegisterClass(wc)
        window_title = "Small Window"
        
        cx = self.screen_center_x+self.small_circle_rx - self.small_window_width // 2
        cy = self.screen_center_y+self.small_circle_ry - self.small_window_height // 2
        self.small_hwnd = win32gui.CreateWindow(
            class_atom,
            window_title,
            win32con.WS_POPUP,
            cx, cy, self.small_window_width, self.small_window_height,
            0, 0, 0, None
        )

        win32gui.SetWindowPos(
                self.big_hwnd,
                HWND_TOPMOST,  # 设置为顶层窗口 设置窗口为顶层且不显示任务栏图标
                0, 0, 0, 0,  # 不改变窗口的位置和大小
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE  # 不移动、不改变大小
        )
        win32gui.SetWindowPos(
                self.small_hwnd,
                HWND_TOPMOST,  # 设置为顶层窗口 设置窗口为顶层且不显示任务栏图标
                0, 0, 0, 0,  # 不改变窗口的位置和大小
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE  # 不移动、不改变大小
            )

        # 显示窗口
        self.show()

    def show(self):
        # 显示窗口
        for hwnd in [self.big_hwnd, self.small_hwnd]:
            if hwnd:
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                win32gui.UpdateWindow(hwnd)
        # win32gui.ShowWindow(self.big_hwnd, win32con.SW_SHOW)
        # win32gui.UpdateWindow(self.big_hwnd)
        # sleep(0.1)

        # win32gui.ShowWindow(self.small_hwnd, win32con.SW_SHOW)
        # win32gui.UpdateWindow(self.small_hwnd)

        
        self.setWinThrowON()

    def hide(self):
        # 隐藏窗口
        win32gui.ShowWindow(self.big_hwnd, win32con.SW_HIDE)
        win32gui.ShowWindow(self.small_hwnd, win32con.SW_HIDE)
        win32gui.UpdateWindow(self.big_hwnd)
        win32gui.UpdateWindow(self.small_hwnd)

    def move_small_circle(self, x, y):
        # 移动窗口中心到指定位置
        new_x = int(x - self.small_window_width // 2)
        new_y = int(y - self.small_window_height // 2)
        print(f"移动窗口: x={new_x}, y={new_y}")
        win32gui.PostMessage(self.small_hwnd, win32con.WM_MOVE, 0, (new_y << 16) | new_x)


    def close_window(self):
        # 外部调用销毁窗口
        # 检查窗口是否存在
        for hwnd in [self.big_hwnd, self.small_hwnd]:
            if hwnd and win32gui.IsWindow(hwnd):
                try:
                    # 发送 WM_CLOSE 消息
                    win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                    
                    print(f"WM_CLOSE 消息已发送到窗口句柄 {hwnd}")
                except Exception as e:
                    print(f"销毁窗口时出错: {e}")
            else:
                print("窗口不存在或已被销毁")
    # 窗口过程函数
    def WndProc(self, hwnd, msg, wParam, lParam):
        if hwnd == self.big_hwnd:
            # print("big hwnd")
            return self.big_WndProc(hwnd, msg, wParam, lParam)
        elif hwnd == self.small_hwnd:
            # print("small hwnd")
            return self.small_WndProc(hwnd, msg, wParam, lParam)
    
    def small_WndProc(self, hwnd, msg, wParam, lParam):
        if msg == win32con.WM_DESTROY:
            print("small WM_DESTROY")
            win32gui.PostQuitMessage(0)
            return 0
        elif msg == win32con.WM_PAINT:
            hdc, paintStruct = win32gui.BeginPaint(hwnd)
            paint_area = paintStruct[2]
            if paint_area[2]>self.small_circle_radius*2 and paint_area[3]>self.small_circle_radius*2:
                cx = paint_area[0]+paint_area[2]//2
                cy = paint_area[1]+paint_area[3]//2
                print(f"绘制小圆: x={cx}, y={cy}, r={self.small_circle_radius}, color={self.small_circle_color}")
                self.draw_circle(hdc, cx, cy, self.small_circle_radius, self.small_circle_color)
            else:
                print("不绘制小圆")
            win32gui.EndPaint(hwnd, paintStruct)
            
            
            return 0
        # elif msg == 20:
        #     print("拦截一条消息{}",msg)
        #     return 0
        elif msg == win32con.WM_MOVE:
            # 获取新的位置
            x = lParam & 0xFFFF  # 获取 X 坐标
            y = lParam >> 16     # 获取 Y 坐标

            # 获取窗口的当前大小
            rect = win32gui.GetWindowRect(hwnd)
            width = rect[2] - rect[0]
            height = rect[3] - rect[1]

            # 移动窗口到新的位置，保持大小不变
            win32gui.MoveWindow(hwnd, x, y, width, height, True)
            return 0
        return win32gui.DefWindowProc(hwnd, msg, wParam, lParam)

    def big_WndProc(self, hwnd, msg, wParam, lParam):
        if msg == win32con.WM_DESTROY:
            print("big WM_DESTROY")
            win32gui.PostQuitMessage(0)
            return 0
        elif msg == win32con.WM_PAINT:
            print("big WM_PAINT")
            hdc, paintStruct = win32gui.BeginPaint(hwnd)
            paint_area = paintStruct[2]
            if paint_area[2]>self.big_circle_radius*2 and paint_area[3]>self.big_circle_radius*2:
                cx = paint_area[0]+paint_area[2]//2
                cy = paint_area[1]+paint_area[3]//2
                print(f"绘制大圆: x={cx}, y={cy}, r={self.big_circle_radius}, color={self.big_circle_color}")
                self.draw_circle(hdc, cx, cy, self.big_circle_radius, self.big_circle_color)
            else:
                print("不绘制大圆")
            win32gui.EndPaint(hwnd, paintStruct)
            
            
            return 0
        # elif msg == 20:
        #     print("拦截一条消息{}",msg)
        #     return 0
        return win32gui.DefWindowProc(hwnd, msg, wParam, lParam)
    
    # 设置点击穿透
    def setWinThrowON(self):
        exStyle = WS_EX_LAYERED | WS_EX_TRANSPARENT# | WS_EX_TOOLWINDOW
        for hwnd in [self.big_hwnd, self.small_hwnd]:
            if hwnd:
                SetWindowLong(hwnd, GWL_EXSTYLE,exStyle)
        # SetWindowLong(self.big_hwnd, GWL_EXSTYLE,exStyle)
        # SetWindowLong(self.small_hwnd, GWL_EXSTYLE,exStyle)
        


    def draw_circle(self, dc, x, y, r, color):
        x0 = 0
        y0 = r
        d = 3 - 2 * r
        while x0 <= y0:
            # 计算所有 8 个对称点
            points = [
                (x + x0, y + y0),
                (x + y0, y + x0),
                (x - y0, y + x0),
                (x - x0, y + y0),
                (x - x0, y - y0),
                (x - y0, y - x0),
                (x + y0, y - x0),
                (x + x0, y - y0)
            ]
            for px, py in points:
                try:
                    # print(f"绘制像素: ({px}, {py})")
                    win32gui.SetPixel(dc, px, py, color)
                except Exception as e:
                    
                    print(f"绘制像素时出错: {e}")
                    return
                    # print(f"坐标: ({px}, {py})")
                    
            if d < 0:
                d += 4 * x0 + 6
            else:
                d += 4 * (x0 - y0) + 10
                y0 -= 1
            x0 += 1

    # def get_window_size(self,hwnd):
    #     # 获取窗口的客户区大小
    #     rect = win32gui.GetClientRect(hwnd)  # 获取窗口客户区的矩形
    #     if rect:
    #         left, top, right, bottom = rect
    #         width = right - left
    #         height = bottom - top
    #         self.window_width = width
    #         self.window_height = height
    #     else:
    #         print("无法获取窗口客户区的矩形")
    #         return False
        
    #     # 获取窗口的大小
    #     window_rect = win32gui.GetWindowRect(hwnd)  # 获取窗口的矩形
    #     if window_rect:
    #         left, top, right, bottom = window_rect
    #         width = right - left
    #         height = bottom - top
    #         self.window_width = width
    #         self.window_height = height
    #     else:
    #         print("无法获取窗口的矩形")
    #         return False
    #     return True
    # color_state = True
    # def draw_all_circle(self, dc, is_init, big_r, small_x_offset, small_y_offset, small_r=5):
    #     # 显示窗口
    #     # win32gui.ShowWindow(self.hwnd, win32con.SW_SHOW)
    #     # win32gui.UpdateWindow(self.hwnd)
    #     # # 获取窗口的设备上下文
    #     # self.dc = win32gui.GetWindowDC(self.hwnd)

    #     # 定义颜色
    #     red = win32api.RGB(255, 0, 0)  # 大圆颜色
    #     blue = win32api.RGB(0, 0, 255)  # 小圆颜色
    #     if self.color_state:
    #         color = red
    #         self.color_state = False
    #     else:
    #         color = blue
    #         self.color_state = True

    #     if is_init:
    #         # 初始化时绘制大圆
    #         center_x = self.window_width // 2
    #         center_y = self.window_height // 2
    #         print(f"绘制大圆: x={center_x}, y={center_y}, r={self.big_radius}")
    #         self.draw_circle(dc, center_x, center_y, self.big_radius, color)
    #         self.big_circle_drawn = True

    #     center_x = self.window_width // 2
    #     center_y = self.window_height // 2

    #     # 计算小圆的实际坐标
    #     scaling = self.big_radius / big_r
    #     small_x = round(center_x + small_x_offset * scaling)
    #     small_y = round(center_y + small_y_offset * scaling)
    #     small_r = int(small_r)

    #     # 绘制小圆
    #     print(f"绘制小圆: x={small_x}, y={small_y}, r={small_r}")
    #     self.draw_circle(dc, small_x, small_y, small_r, color)
     
import queue

def draw_circle(q):
    drawer = ScreenDrawer()
    drawer.init_window()
    
    q.put(drawer)
    q.put(None)
    # 消息循环
    win32gui.PumpMessages()

def init_drawcircle_thread():
    q = queue.Queue()
    # 修改部分
    draw_circle_thread = threading.Thread(target=draw_circle,args=(q,))
    # 将线程设置为守护线程
    draw_circle_thread.daemon = True
    draw_circle_thread.start()
    print("waiting for thread init...")
    drawer = None
    while True:
        tem = q.get()
        if tem is None:
            break
        drawer = tem
        q.task_done()
    if drawer:
        print("thread init success")
        return drawer, draw_circle_thread
    else:
        print("thread init failed")
        return None

# 使用示例
if __name__ == "__main__":
    # drawer = ScreenDrawer()
    # hwnd =  None
    # print(1)
    
    # drawer.show()
    # print(2)
    # # 消息循环
    # t_init = threading.Thread(target=win32gui.PumpMessages, daemon=True)
    # t_init.start()
    # q = queue.Queue()
    # # 修改部分
    # t_init = threading.Thread(target=draw_circle,args=(q,))
    # # 将线程设置为守护线程
    # t_init.daemon = True
    # t_init.start()

    # print("waiting...")
    # sleep(1)
    # while True:
    #     tem = q.get()
    #     if tem is None:
    #         break
    #     drawer = tem
    #     # print(hwnd)
    #     q.task_done()
    
    # 
    # drawer.__del__()
    # sleep(1)

    drawer, t_init = init_drawcircle_thread()
    print("show window")
    drawer.show()
    sleep(5)
    print("hide window")
    drawer.hide()
    sleep(5)
    print("show window")
    drawer.show()
    sleep(2)

    drawer.move_small_circle(100,100)
    sleep(5)
    drawer.move_small_circle(200,200)
    sleep(5)
    print("close window")
    
    drawer.close_window()

    # 等待线程结束
    print("等待线程结束")
    t_init.join()

    print("程序结束")
