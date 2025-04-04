
import threading
from time import sleep
import win32gui
import win32con
import win32api
from win32con import WS_EX_LAYERED,WS_EX_TRANSPARENT,GWL_EXSTYLE,WS_EX_TOOLWINDOW,HWND_TOPMOST
from win32api import SetWindowLong
# def on_paint(hdc,paint_area,painter):
#     # 获取窗口的大小
#     width = paint_area[2]
#     height = paint_area[3]
    
#     # 创建内存设备上下文
#     mem_dc = win32gui.CreateCompatibleDC(hdc)
    
#     # 创建位图
#     bitmap = win32gui.CreateCompatibleBitmap(hdc, width, height)
    
#     # 将位图选入内存设备上下文
#     old_bitmap = win32gui.SelectObject(mem_dc, bitmap)
#     # # 设置位图为透明
#     # # 创建一个蓝色的画刷
#     # blue_brush = win32gui.GetStockObject(win32con.NULL_BRUSH)
#     blue_brush = win32gui.CreateSolidBrush(win32api.RGB(97, 175, 239))
#     # 将蓝色画刷选入设备上下文
#     # old_brush = win32gui.SelectObject(mem_dc, blue_brush)

#     # # 绘制椭圆
#     print("paint ellipse",paint_area)
#     win32gui.FillRect(mem_dc, paint_area, blue_brush)
#     # win32gui.Ellipse(mem_dc, paint_area[0]+4, paint_area[1]+4, paint_area[2]-4, paint_area[3]-4)
#     # 恢复原来的画刷
#     # win32gui.SelectObject(mem_dc, old_brush)
#     # 删除创建的画刷
#     win32gui.DeleteObject(blue_brush)
#     # Background = win32gui.GetStockObject(win32con.HOLLOW_BRUSH)
#     # old_brush = win32gui.SelectObject(mem_dc, Background)
#     # # win32gui.Rectangle(mem_dc, paint_area[3], paint_area[1], paint_area[2], paint_area[3])
#     # win32gui.Ellipse(mem_dc, paint_area[3], paint_area[1], paint_area[2], paint_area[3])
#     # win32gui.SelectObject(mem_dc, old_brush)
#     # win32gui.FillRect(mem_dc, (0, 0, width, height), Background)
#     # # 使用 win32con.BKMODE_TRANSPARENT 设置背景模式为透明
#     # win32gui.SetBkMode(mem_dc, win32con.BKMODE_TRANSPARENT)
#     # # 使用 win32con.PATCOPY 模式填充位图，使其完全透明
#     # win32gui.BitBlt(mem_dc, 0, 0, width, height, None, 0, 0, win32con.PATCOPY) 
    
#     # 在内存设备上下文中绘图
#     # 示例：绘制一个矩形
#     # win32gui.Rectangle(mem_dc, 1, 1, width - 1, height - 1)
#     painter.draw(mem_dc,paint_area)
    
#     # 将内存设备上下文的内容复制到屏幕
#     win32gui.BitBlt(hdc, 0, 0, width, height, mem_dc, 0, 0, win32con.SRCCOPY)
    
#     # 恢复旧位图
#     win32gui.SelectObject(mem_dc, old_bitmap)
    
#     # 删除位图和内存设备上下文
#     win32gui.DeleteObject(bitmap)
#     win32gui.DeleteDC(mem_dc)   

class ScreenDrawer:
    def __init__(self):
        # 定义窗口和圆圈的属性
        self.big_circle_radius = 50
        self.big_circle_color = win32api.RGB(255, 0, 0)  # 红色
        self.big_window_width = self.big_circle_radius * 2 + 4
        self.big_window_height = self.big_circle_radius * 2 + 4
        self.small_circle_radius = 15
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

        # 扩展样式
        self.circle2_circle_radius = 20
        self.circle2_circle_color = win32api.RGB(97, 175, 239)  # 蓝色
        self.circle2_window_width = self.circle2_circle_radius * 2 + 4
        self.circle2_window_height = self.circle2_circle_radius * 2 + 4

        self.circle2_mode = False
        self.draw_small_circle_2 = False
        self.small_circle_2_color = win32api.RGB(0, 255, 0)  # 蓝色
        self.small_circle_2_radius = 5
    
    def __del__(self):
        # 释放设备上下文
        # win32gui.ReleaseDC(self.hwnd, self.dc)
        # 销毁窗口
        win32gui.DestroyWindow(self.big_hwnd)
        win32gui.DestroyWindow(self.small_hwnd)
        
    def set_circle_2(self,is_draw = True,color = win32api.RGB(0, 255, 0),radius = 50):
        self.circle2_mode = is_draw
        self.small_circle_2_color = color
        if is_draw:
            win32gui.ShowWindow(self.circle2_hwnd, win32con.SW_SHOW)
        else:
            win32gui.ShowWindow(self.circle2_hwnd, win32con.SW_HIDE)
        # self.small_circle_2_radius = radius
        
    def init_window(self):
        # 定义窗口类
        class_name = "small_circle_window"
        # 注册窗口类
        wc = win32gui.WNDCLASS()
        wc.hbrBackground = win32gui.GetStockObject(win32con.HOLLOW_BRUSH)
        wc.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
        wc.hIcon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)
        wc.lpszClassName = class_name
        wc.lpfnWndProc = self.WndProc  # 指定消息处理函数
        class_atom = win32gui.RegisterClass(wc)

        cx = self.screen_center_x+self.small_circle_rx - self.small_window_width // 2
        cy = self.screen_center_y+self.small_circle_ry - self.small_window_height // 2
        
        window_title = "Small Window"
        self.small_hwnd = win32gui.CreateWindow(
            class_atom,
            window_title,
            win32con.WS_POPUP,
            cx, cy, self.small_window_width, self.small_window_height,
            0, 0, 0, None
        )

        # 定义窗口类
        class_name = "big_circle_window"
        # 注册窗口类
        # wc = win32gui.WNDCLASS()
        # wc.hbrBackground = win32gui.GetStockObject(win32con.WHITE_BRUSH)
        # wc.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
        # wc.hIcon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)
        # wc.lpfnWndProc = self.WndProc  # 指定消息处理函数
        wc.lpszClassName = class_name
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
        class_name = "circle2_window"
        wc.lpszClassName = class_name
        class_atom = win32gui.RegisterClass(wc)
        
        # 计算窗口左上角的坐标，使其位于屏幕中心
        center_x = self.screen_center_x - self.big_window_width // 2
        center_y = self.screen_center_y - self.big_window_height // 2

        # 创建窗口
        window_title = "circle2 Window"
        self.circle2_hwnd = win32gui.CreateWindow(
            class_atom,
            window_title,
            win32con.WS_POPUP, 
            center_x, center_y, self.circle2_window_width, self.circle2_window_height,
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
        win32gui.SetWindowPos(
                self.circle2_hwnd,
                HWND_TOPMOST,  # 设置为顶层窗口 设置窗口为顶层且不显示任务栏图标
                0, 0, 0, 0,  # 不改变窗口的位置和大小
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE  # 不移动、不改变大小
        )

        # 初始化窗口
        for hwnd in [self.big_hwnd, self.small_hwnd, self.circle2_hwnd]:
            if hwnd:
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
        self.setWinThrowON()
        self.hide()



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

        
        # self.setWinThrowON()

    def hide(self):
        # 隐藏窗口
        for hwnd in [self.big_hwnd, self.small_hwnd, self.circle2_hwnd]:
            if hwnd:
                win32gui.ShowWindow(hwnd, win32con.SW_HIDE)
                win32gui.UpdateWindow(hwnd)

    def move_circles(self, relative_x, relative_y):
        mouse = win32api.GetCursorPos()
        self.screen_center_x = mouse[0]
        self.screen_center_y = mouse[1]
        self.move_big_circle(0, 0)
        self.move_small_circle(relative_x, relative_y)

    def move_big_circle(self, relative_x, relative_y):
        # 计算窗口左上角的坐标，使其位于屏幕中心
        left = self.screen_center_x - self.big_window_width // 2
        top = self.screen_center_y - self.big_window_height // 2
        win32gui.PostMessage(self.big_hwnd, win32con.WM_MOVE, 0, (top << 16) | left)

    def move_small_circle(self, relative_x, relative_y):
        
        # 归一化坐标转窗口中心像素坐标，relative_x为1时大圆小圆刚好相切
        scale = self.big_circle_radius - self.small_circle_radius
        cx = relative_x*scale + self.screen_center_x
        cy = relative_y*scale + self.screen_center_y

        # 计算窗口左上角的坐标
        new_x = int(cx - self.small_window_width // 2)
        new_y = int(cy - self.small_window_height // 2)
        # print(f"移动窗口: x={new_x}, y={new_y}")
        win32gui.PostMessage(self.small_hwnd, win32con.WM_MOVE, 0, (new_y << 16) | new_x)

    def move_circle2(self, relative_poision):
        # 归一化坐标转窗口中心像素坐标，relative_poision为1时圆刚好相切
        cx = self.screen_center_x - (self.big_circle_radius+self.circle2_circle_radius) * relative_poision
        cy = self.screen_center_y
        cx = int(cx)
        cy = int(cy)
        left = cx - self.circle2_window_width // 2
        top = cy - self.circle2_window_height // 2
        # print(f"移动窗口: x={left}, y={top}")
        win32gui.PostMessage(self.circle2_hwnd, win32con.WM_MOVE, 0, (top << 16) | left)

    def update_circle2(self, relative_radius):
        if not self.circle2_mode:
            return
        if abs(relative_radius)<=1:
            win32gui.ShowWindow(self.circle2_hwnd, win32con.SW_HIDE)

            if self.draw_small_circle_2:
                self.draw_small_circle_2 = False
            else:
                return
        else:
            win32gui.ShowWindow(self.circle2_hwnd, win32con.SW_SHOW)
            self.draw_small_circle_2 = True
            # self.small_circle_2_radius = relative_radius*self.small_circle_radius
        self.move_circle2(relative_radius)
        # win32gui.PostMessage(self.small_hwnd, win32con.WM_PAINT, self.small_window_width, self.small_window_height)
            # 使窗口无效，触发 WM_PAINT 消息
        # win32gui.InvalidateRect(self.small_hwnd, None, True)
        
        # 强制窗口立即处理 WM_PAINT 消息
        # win32gui.UpdateWindow(self.small_hwnd)

    def close_window(self):
        # 外部调用销毁窗口
        # 检查窗口是否存在
        for hwnd in [self.big_hwnd, self.small_hwnd]:
            if hwnd and win32gui.IsWindow(hwnd):
                try:
                    # 发送 WM_CLOSE 消息
                    win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                    # 等待窗口关闭，最多5秒
                    import time
                    start_time = time.time()
                    while win32gui.IsWindow(hwnd):
                        if time.time() - start_time > 5:
                            raise TimeoutError(f"窗口 {hwnd} 在 5 秒内未关闭")
                        time.sleep(0.1)

                except Exception as e:
                    # print(f"销毁窗口时出错: {e}")
                    pass
            else:
                # print("窗口不存在或已被销毁")
                pass

    # 窗口过程函数
    def WndProc(self, hwnd, msg, wParam, lParam):
        if hwnd == self.big_hwnd:
            # # print("big hwnd")
            return self.big_WndProc(hwnd, msg, wParam, lParam)
        elif hwnd == self.small_hwnd:
            # # print("small hwnd")
            return self.small_WndProc(hwnd, msg, wParam, lParam)
        elif hwnd == self.circle2_hwnd:
            # # print("small hwnd")
            return self.circle2_WndProc(hwnd, msg, wParam, lParam)
    
    def small_WndProc(self, hwnd, msg, wParam, lParam):
        if msg == win32con.WM_DESTROY:
            # print("small WM_DESTROY")
            win32gui.PostQuitMessage(0)
            return 0
        elif msg == win32con.WM_PAINT:
            hdc, paintStruct = win32gui.BeginPaint(hwnd)
            paint_area = paintStruct[2]
            if paint_area[2]>self.small_circle_radius*2 and paint_area[3]>self.small_circle_radius*2:
                # on_paint(hdc,paint_area,self)
                cx = paint_area[0]+paint_area[2]//2
                cy = paint_area[1]+paint_area[3]//2
                # print(f"绘制小圆: x={cx}, y={cy}, r={self.small_circle_radius}, color={self.small_circle_color}")
                self.draw_circle(hdc, cx, cy, self.small_circle_radius, self.small_circle_color)
                # if self.draw_circle2:
                #     print(f"绘制小圆2: x={cx}, y={cy}, r={self.small_circle_2_radius}, color={self.small_circle_2_color}")
                #     self.draw_circle(hdc, cx, cy, self.small_circle_2_radius, self.small_circle_color)
            else:
                # print("不绘制小圆,paint_area{ paint_area[2]},{paint_area[3]}")
                pass
            win32gui.EndPaint(hwnd, paintStruct)
            
            
            return win32gui.DefWindowProc(hwnd, msg, wParam, lParam)
            return 0
        # elif msg == 20:
        #     # print("拦截一条消息{}",msg)
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

    # def draw(self,hdc,paint_area):
    #     cx = paint_area[0]+paint_area[2]//2
    #     cy = paint_area[1]+paint_area[3]//2
    #     print(f"绘制小圆: x={cx}, y={cy}, r={self.small_circle_radius}, color={self.small_circle_color}")
    #     self.draw_circle(hdc, cx, cy, self.small_circle_radius, self.small_circle_color)
    #     if self.draw_small_circle_2:
    #         print(f"绘制小圆2: x={cx}, y={cy}, r={self.small_circle_2_radius}, color={self.small_circle_2_color}")
    #         self.draw_circle(hdc, cx, cy, self.small_circle_2_radius, self.small_circle_color)
            
    def big_WndProc(self, hwnd, msg, wParam, lParam):
        if msg == win32con.WM_DESTROY:
            # print("big WM_DESTROY")
            win32gui.PostQuitMessage(0)
            return 0
        elif msg == win32con.WM_PAINT:
            # print("big WM_PAINT")
            hdc, paintStruct = win32gui.BeginPaint(hwnd)
            paint_area = paintStruct[2]
            # print(f"big WM_PAINT: paint_area{paint_area[0]},{paint_area[1]},{paint_area[2]},{paint_area[3]}")
            if paint_area[2]>self.big_circle_radius*2 and paint_area[3]>self.big_circle_radius*2:
                cx = paint_area[0]+paint_area[2]//2
                cy = paint_area[1]+paint_area[3]//2
                # print(f"绘制大圆: x={cx}, y={cy}, r={self.big_circle_radius}, color={self.big_circle_color}")
                self.draw_circle(hdc, cx, cy, self.big_circle_radius, self.big_circle_color)
            else:
                # print("不绘制大圆")
                pass
            win32gui.EndPaint(hwnd, paintStruct)
            
            
            return 0
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
        # elif msg == 20:
        #     # print("拦截一条消息{}",msg)
        #     return 0
        # print("big_WndProc {}",msg)
        return win32gui.DefWindowProc(hwnd, msg, wParam, lParam)
    
    def circle2_WndProc(self, hwnd, msg, wParam, lParam):
        # print("circle2_WndProc")
        if msg == win32con.WM_DESTROY:
            win32gui.PostQuitMessage(0)
            return 0
        elif msg == win32con.WM_PAINT:
            hdc, paintStruct = win32gui.BeginPaint(hwnd)
            paint_area = paintStruct[2]
            if paint_area[2]>self.circle2_circle_radius*2 and paint_area[3]>self.circle2_circle_radius*2:
                cx = paint_area[0]+paint_area[2]//2
                cy = paint_area[1]+paint_area[3]//2
                self.draw_circle(hdc, cx, cy, self.circle2_circle_radius, self.circle2_circle_color)
            else:
                pass
            win32gui.EndPaint(hwnd, paintStruct)
            
            
            return 0
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

    # 设置点击穿透，不显示任务栏图标
    def setWinThrowON(self):
        exStyle = WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW
        for hwnd in [self.big_hwnd, self.small_hwnd, self.circle2_hwnd]:
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
                px = int(px)
                py = int(py)
                try:
                    # print(f"绘制像素: ({px}, {py})")
                    win32gui.SetPixel(dc, px, py, color)
                except Exception as e:
                    
                    # print(f"绘制像素时出错: {e}")
                    return
                    # print(f"坐标: ({px}, {py})")
                    
            if d < 0:
                d += 4 * x0 + 6
            else:
                d += 4 * (x0 - y0) + 10
                y0 -= 1
            x0 += 1


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
    # print("waiting for thread init...")
    drawer = None
    while True:
        tem = q.get()
        if tem is None:
            break
        drawer = tem
        q.task_done()
    if drawer:
        # print("thread init success")
        return drawer, draw_circle_thread
    else:
        # print("thread init failed")
        return None
    
if __name__ == "__main__":
    drawer, draw_circle_thread = init_drawcircle_thread()
    # sleep(10)
    drawer.show()
    drawer.move_small_circle(0.5,0.5)
    sleep(4)
    drawer.set_circle_2()
    drawer.update_circle2(1.8)
    sleep(4)
    drawer.move_small_circle(-0.5,-0.5)
    drawer.update_circle2(1.5)
    sleep(4)
    drawer.update_circle2(0.5)
    sleep(4)
    drawer.close_window()

    sleep(10)