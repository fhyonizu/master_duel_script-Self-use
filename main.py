import pyautogui
import cv2
import numpy as np
import os
import time
import keyboard
import threading
import tkinter as tk
from tkinter import messagebox

# ----------- 核心识图逻辑函数区 -----------
image_folder = "images"

def find_and_click(image_name, threshold=0.8):
    image_path = os.path.join(image_folder, image_name)
    target = cv2.imread(image_path, 0)
    if target is None:
        print(f"❌ 未找到图像：{image_name}")
        return False

    screen = pyautogui.screenshot()
    screen = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2GRAY)
    result = cv2.matchTemplate(screen, target, cv2.TM_CCOEFF_NORMED)
    loc = np.where(result >= threshold)

    for pt in zip(*loc[::-1]):
        x = pt[0] + target.shape[1] // 2
        y = pt[1] + target.shape[0] // 2
        print(f"✅ 点击 {image_name} at ({x}, {y})")
        pyautogui.click(x, y)
        return True
    return False

def find_and_offset_click(image_name, threshold=0.8, offset_y=120):
    image_path = os.path.join(image_folder, image_name)
    target = cv2.imread(image_path, 0)
    if target is None:
        print(f"❌ 未找到图像：{image_name}")
        return False

    screen = pyautogui.screenshot()
    screen = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2GRAY)
    result = cv2.matchTemplate(screen, target, cv2.TM_CCOEFF_NORMED)
    loc = np.where(result >= threshold)

    for pt in zip(*loc[::-1]):
        x = pt[0] + target.shape[1] // 2
        y = pt[1] + target.shape[0] // 2 + offset_y
        print(f"🎯 偏移点击 {image_name} → 点击下方: ({x}, {y})")

        pyautogui.click(x, y)
        return True
    return False

# ----------- 脚本运行主线程 -----------
def run_script(runtime_minutes, root_window):
    print(f"🕒 运行时长：{runtime_minutes} 分钟")
    start_time = time.time()
    image_list = [f for f in os.listdir(image_folder) if f.endswith((".png", ".jpg"))]

    try:
        while True:
            if keyboard.is_pressed('esc'):
                print("🛑 ESC 键退出")
                break

            if (time.time() - start_time) > runtime_minutes * 60:
                print("⏰ 时间到，自动退出")
                break

            clicked = False
            for img in image_list:
                if img == "qi.png":
                    if find_and_offset_click(img):
                        clicked = True
                        time.sleep(1)
                        break
                else:
                    if find_and_click(img):
                        clicked = True
                        time.sleep(1)
                        break

            if not clicked:
                time.sleep(0.3)

    except KeyboardInterrupt:
        print("⛔ 脚本被中断")

    # 关闭窗口
    root_window.quit()
    root_window.destroy()

# ----------- UI 窗口 ----------
def start_ui():
    def start():
        try:
            minutes = float(entry.get())
            start_button.config(state="disabled")
            threading.Thread(target=run_script, args=(minutes, window), daemon=True).start()
        except ValueError:
            messagebox.showerror("输入错误", "请输入有效数字")

    window = tk.Tk()
    window.title("图像识图脚本")
    window.geometry("300x150")
    window.resizable(False, False)

    label = tk.Label(window, text="请输入运行时间（分钟）：")
    label.pack(pady=10)

    entry = tk.Entry(window, justify="center")
    entry.pack(pady=5)
    entry.insert(0, "10")

    start_button = tk.Button(window, text="开始运行", command=start)
    start_button.pack(pady=10)

    window.mainloop()

# ---------- 启动程序 ----------
if __name__ == "__main__":
    if not os.path.exists(image_folder):
        print("❌ 请确保 images 文件夹与脚本同级")
        input("按回车退出")
    else:
        start_ui()
