import time
import pyautogui
import pydirectinput
import pyperclip
import keyboard
from PIL import ImageGrab

class AutoEngine:
    def __init__(self, data_manager):
        self.dm = data_manager
        self.is_running = False

    @staticmethod
    def get_pixel_color(x, y):
        img = ImageGrab.grab(bbox=(x, y, x + 1, y + 1))
        return img.getpixel((0, 0))

    @staticmethod
    def is_same_color(c1, c2, tolerance=15):
        return all(abs(a - b) <= tolerance for a, b in zip(c1, c2))

    def is_modal_still_open(self):
        coords = self.dm.get_coords()
        input_box = coords.get("input_box")
        modal_color = coords.get("modal_color")
        if not input_box or not modal_color:
            return False
        sample_y = max(0, input_box[1] - 50)
        current_color = self.get_pixel_color(input_box[0], sample_y)
        return self.is_same_color(current_color, modal_color)

    def stop(self):
        self.is_running = False

    def run_batch(self, account_name, codes, wait_time, on_status, on_log, on_finish):
        self.is_running = True
        try:
            coords = self.dm.get_coords()
            open_btn = coords["open_btn"]
            input_box = coords["input_box"]
            confirm_btn = coords["confirm_btn"]

            for i in range(3, 0, -1):
                if not self.is_running:
                    on_finish("Đã hủy trước khi chạy.")
                    return
                on_status(f"[{account_name}] Chuẩn bị sau {i}s... (Nhấn ESC để dừng)")
                time.sleep(1)

            for index, code in enumerate(codes):
                if not self.is_running or keyboard.is_pressed('esc'):
                    on_status("Đã dừng theo yêu cầu!")
                    break

                on_status(f"[{account_name}] Đang nhập ({index + 1}/{len(codes)}): {code}")

                if not self.is_modal_still_open():
                    pydirectinput.click(open_btn[0], open_btn[1])
                    time.sleep(0.7)

                pydirectinput.click(input_box[0], input_box[1])
                time.sleep(0.2)
                pyautogui.hotkey('ctrl', 'a')
                time.sleep(0.1)
                pyautogui.press('backspace')
                time.sleep(0.1)

                pyperclip.copy(code)
                pyautogui.hotkey('ctrl', 'v')
                time.sleep(0.3)

                pydirectinput.click(confirm_btn[0], confirm_btn[1])
                time.sleep(wait_time)

                is_success = not self.is_modal_still_open()
                if is_success:
                    on_log(f"[THÀNH CÔNG] {code}")
                else:
                    on_log(f"[THẤT BẠI / ĐÃ DÙNG] {code}")

                self.dm.update_code_result(account_name, code, is_success)

            on_finish(f"Hoàn thành phiên nhập cho {account_name}!")
        finally:
            self.is_running = False
