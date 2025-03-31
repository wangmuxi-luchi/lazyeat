import win32gui, win32ui, win32api, win32con
from win32api import GetSystemMetrics

def draw_test():
    # 获取桌面窗口的设备上下文
    hwnd = win32gui.GetDesktopWindow()
    dc = win32gui.GetWindowDC(hwnd)
    dcObj = win32ui.CreateDCFromHandle(dc)
    hwnd = win32gui.WindowFromPoint((0, 0))
    monitor = (0, 0, GetSystemMetrics(0), GetSystemMetrics(1))
    screen_width = GetSystemMetrics(0)
    screen_height = GetSystemMetrics(1)

    red = win32api.RGB(255, 0, 0)  # Red
    past_coordinates = monitor
    m = win32gui.GetCursorPos()

    rect = win32gui.CreateRoundRectRgn(*past_coordinates, 2, 2)
    # 刷新部分区域的内容
    win32gui.RedrawWindow(hwnd, past_coordinates, rect, win32con.RDW_INVALIDATE)

    # 绘制指定像素点
    for x in range(10):
        # 计算绘制像素的 x 坐标，并限制在屏幕范围内
        draw_x1 = max(0, min(screen_width - 1, m[0] + x))
        draw_x2 = max(0, min(screen_width - 1, m[0] + x))
        draw_y1 = max(0, min(screen_height - 1, m[1]))
        draw_y2 = max(0, min(screen_height - 1, m[1] + 10))
        win32gui.SetPixel(dc, draw_x1, draw_y1, red)
        win32gui.SetPixel(dc, draw_x2, draw_y2, red)

        for y in range(10):
            # 计算绘制像素的 y 坐标，并限制在屏幕范围内
            draw_x3 = max(0, min(screen_width - 1, m[0]))
            draw_x4 = max(0, min(screen_width - 1, m[0] + 10))
            draw_y3 = max(0, min(screen_height - 1, m[1] + y))
            draw_y4 = max(0, min(screen_height - 1, m[1] + y))
            win32gui.SetPixel(dc, draw_x3, draw_y3, red)
            win32gui.SetPixel(dc, draw_x4, draw_y4, red)

    # 记录待刷新区域
    past_coordinates = (m[0] - 20, m[1] - 20, m[0] + 20, m[1] + 20)

    # 释放设备上下文
    win32gui.ReleaseDC(hwnd, dc)

# 全局变量，用于存储大圆的信息
big_circle_drawn = False
big_radius = 50

def draw_cycle(is_init, big_r, small_x_offset, small_y_offset, small_r=5):
    global big_circle_drawn, big_radius
    # 获取桌面窗口的设备上下文
    hwnd = win32gui.GetDesktopWindow()
    dc = win32gui.GetWindowDC(hwnd)
    dcObj = win32ui.CreateDCFromHandle(dc)
    hwnd = win32gui.WindowFromPoint((0, 0))
    monitor = (0, 0, GetSystemMetrics(0), GetSystemMetrics(1))
    screen_width = GetSystemMetrics(0)
    screen_height = GetSystemMetrics(1)

    # 定义颜色
    red = win32api.RGB(255, 0, 0)  # 大圆颜色
    blue = win32api.RGB(0, 0, 255)  # 小圆颜色
  
    if is_init:
        # 初始化时绘制大圆
        center_x = screen_width // 2
        center_y = screen_height // 2
        # big_radius = int(big_r)  
        draw_circle(dc,center_x, center_y, big_radius, red)
        # 确保大圆不会超出屏幕范围
        # left = max(0, center_x - big_r)
        # top = max(0, center_y - big_r)
        # right = min(screen_width, center_x + big_r)
        # bottom = min(screen_height, center_y + big_r)
        # win32gui.Ellipse(dc, left, top, right, bottom)
        big_circle_drawn = True
    else:
        center_x = screen_width // 2
        center_y = screen_height // 2

    # 计算小圆的实际坐标
    scaling = big_radius / big_r
    small_x = round(center_x + small_x_offset*scaling)
    small_y = round(center_y + small_y_offset*scaling)
    small_r = int(small_r)

    # 确保小圆不会超出屏幕范围
    small_left = max(0, small_x - small_r)
    small_top = max(0, small_y - small_r)
    small_right = min(screen_width, small_x + small_r)
    small_bottom = min(screen_height, small_y + small_r)

    # 绘制小圆
    draw_circle(dc, small_x, small_y, small_r, red)
    # win32gui.Ellipse(dc, small_left, small_top, small_right, small_bottom)

    # 释放设备上下文
    win32gui.ReleaseDC(hwnd, dc)


def draw_circle(dc, x, y, r, color):
    screen_width = GetSystemMetrics(0)
    screen_height = GetSystemMetrics(1)
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
            # 确保坐标在屏幕范围内
            if 0 <= px < screen_width and 0 <= py < screen_height:
                win32gui.SetPixel(dc, px, py, color)
        if d < 0:
            d += 4 * x0 + 6
        else:
            d += 4 * (x0 - y0) + 10
            y0 -= 1
        x0 += 1