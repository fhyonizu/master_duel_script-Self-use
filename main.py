import pyautogui
import cv2
import numpy as np
import os
import time
import keyboard
import threading
import tkinter as tk
from tkinter import messagebox

# ----------- 配置 -----------
IMAGE_FOLDER = "images"
DEFAULT_THRESHOLD = 0.8
CLICK_DELAY = 1.0
IDLE_DELAY = 0.3

# 需要偏移点击的图像及其偏移量 {文件名: offset_y}
OFFSET_CLICK_MAP = {
    "qi.png": 120,
}

# ----------- 图像缓存 -----------
_image_cache: dict[str, np.ndarray] = {}

def _load_image(image_name: str) -> np.ndarray | None:
    if image_name not in _image_cache:
        path = os.path.join(IMAGE_FOLDER, image_name)
        img = cv2.imread(path, 0)
        if img is None:
            print(f"❌ 未找到图像：{image_name}")
            return None
        _image_cache[image_name] = img
    return _image_cache[image_name]

# ----------- 核心识图逻辑 -----------
def _match_image(screen_gray: np.ndarray, image_name: str, threshold: float = DEFAULT_THRESHOLD):
    """在屏幕截图中匹配目标图像，返回匹配中心坐标，未找到返回 None。"""
    target = _load_image(image_name)
    if target is None:
        return None

    result = cv2.matchTemplate(screen_gray, target, cv2.TM_CCOEFF_NORMED)
    loc = np.where(result >= threshold)

    for pt in zip(*loc[::-1]):
        x = pt[0] + target.shape[1] // 2
        y = pt[1] + target.shape[0] // 2
        return x, y
    return None

def _take_screenshot() -> np.ndarray:
    screen = pyautogui.screenshot()
    return cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2GRAY)

def find_and_click(screen_gray: np.ndarray, image_name: str, threshold: float = DEFAULT_THRESHOLD) -> bool:
    pos = _match_image(screen_gray, image_name, threshold)
    if pos:
        x, y = pos
        print(f"✅ 点击 {image_name} at ({x}, {y})")
        pyautogui.click(x, y)
        return True
    return False

def find_and_offset_click(screen_gray: np.ndarray, image_name: str, threshold: float = DEFAULT_THRESHOLD, offset_y: int = 120) -> bool:
    pos = _match_image(screen_gray, image_name, threshold)
    if pos:
        x, y = pos[0], pos[1] + offset_y
        print(f"🎯 偏移点击 {image_name} → ({x}, {y})")
        pyautogui.click(x, y)
        return True
    return False

# ----------- 脚本运行主线程 -----------
def run_script(runtime_minutes: float, root_window: tk.Tk, status_var: tk.StringVar, stop_event: threading.Event):
    print(f"🕒 运行时长：{runtime_minutes} 分钟")
    start_time = time.time()
    image_list = sorted(f for f in os.listdir(IMAGE_FOLDER) if f.endswith((".png", ".jpg")))

    # 预加载所有图像
    for img in image_list:
        _load_image(img)

    try:
        while not stop_event.is_set():
            if keyboard.is_pressed('esc'):
                print("🛑 ESC 键退出")
                break

            elapsed = time.time() - start_time
            if elapsed > runtime_minutes * 60:
                print("⏰ 时间到，自动退出")
                break

            remaining = int(runtime_minutes * 60 - elapsed)
            status_var.set(f"运行中... 剩余 {remaining // 60:02d}:{remaining % 60:02d}")

            screen_gray = _take_screenshot()
            clicked = False

            for img in image_list:
                offset_y = OFFSET_CLICK_MAP.get(img)
                if offset_y is not None:
                    if find_and_offset_click(screen_gray, img, offset_y=offset_y):
                        clicked = True
                        time.sleep(CLICK_DELAY)
                        break
                else:
                    if find_and_click(screen_gray, img):
                        clicked = True
                        time.sleep(CLICK_DELAY)
                        break

            if not clicked:
                time.sleep(IDLE_DELAY)

    except KeyboardInterrupt:
        print("⛔ 脚本被中断")

    status_var.set("已停止")
    root_window.quit()
    root_window.destroy()

# ----------- UI 窗口 -----------
def start_ui():
    stop_event = threading.Event()

    def start():
        try:
            minutes = float(entry.get())
            start_button.config(state="disabled")
            stop_button.config(state="normal")
            status_var.set("启动中...")
            threading.Thread(
                target=run_script,
                args=(minutes, window, status_var, stop_event),
                daemon=True
            ).start()
        except ValueError:
            messagebox.showerror("输入错误", "请输入有效数字")

    def stop():
        stop_event.set()
        stop_button.config(state="disabled")
        status_var.set("正在停止...")

    window = tk.Tk()
    window.title("Master Duel 自动脚本")
    window.geometry("300x200")
    window.resizable(False, False)

    tk.Label(window, text="请输入运行时间（分钟）：").pack(pady=10)

    entry = tk.Entry(window, justify="center")
    entry.pack(pady=5)
    entry.insert(0, "10")

    btn_frame = tk.Frame(window)
    btn_frame.pack(pady=10)

    start_button = tk.Button(btn_frame, text="开始运行", width=10, command=start)
    start_button.pack(side="left", padx=5)

    stop_button = tk.Button(btn_frame, text="停止", width=10, state="disabled", command=stop)
    stop_button.pack(side="left", padx=5)

    status_var = tk.StringVar(value="等待启动")
    tk.Label(window, textvariable=status_var, fg="gray").pack(pady=5)

    window.mainloop()

# ---------- 启动程序 ----------
if __name__ == "__main__":
    if not os.path.exists(IMAGE_FOLDER):
        print("❌ 请确保 images 文件夹与脚本同级")
        input("按回车退出")
    else:
        start_ui()
