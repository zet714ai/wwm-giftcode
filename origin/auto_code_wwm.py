import tkinter as tk
from tkinter import messagebox, scrolledtext
import pyautogui
import pydirectinput
import pyperclip
import time
import threading
import keyboard
from PIL import ImageGrab

is_running = False
pos_open_btn = None     # Tọa độ 1: Nút >>
pos_input_box = None    # Tọa độ 2: Ô nhập chữ
pos_confirm_btn = None  # Tọa độ 3: Nút Space Xác nhận
modal_bg_color = None   # Màu nền đặc trưng của khung Đổi phần thưởng

def get_pixel_color(x, y):
    img = ImageGrab.grab(bbox=(x, y, x + 1, y + 1))
    return img.getpixel((0, 0))

def is_same_color(c1, c2, tolerance=15):
    return all(abs(a - b) <= tolerance for a, b in zip(c1, c2))

def on_f7():
    global pos_open_btn
    pos_open_btn = pyautogui.position()
    lbl_c1.config(text=f"1. Nút mở (>>): {pos_open_btn}", fg="green")

def on_f8():
    global pos_input_box, modal_bg_color
    pos_input_box = pyautogui.position()
    # Lấy màu nền tại điểm cách ô nhập 50px lên phía trên (vùng nền tối của khung Đổi phần thưởng)
    sample_y = max(0, pos_input_box.y - 50)
    modal_bg_color = get_pixel_color(pos_input_box.x, sample_y)
    lbl_c2.config(text=f"2. Ô nhập code: {pos_input_box} (Đã lưu màu khung)", fg="green")

def on_f9():
    global pos_confirm_btn
    pos_confirm_btn = pyautogui.position()
    lbl_c3.config(text=f"3. Nút Xác nhận: {pos_confirm_btn}", fg="green")

def is_modal_still_open():
    if not pos_input_box or not modal_bg_color:
        return False
    sample_y = max(0, pos_input_box.y - 50)
    current_color = get_pixel_color(pos_input_box.x, sample_y)
    return is_same_color(current_color, modal_bg_color)

def log_result(text):
    log_area.config(state=tk.NORMAL)
    log_area.insert(tk.END, text + "\n")
    log_area.see(tk.END)
    log_area.config(state=tk.DISABLED)

def start_redeem():
    global is_running
    if not (pos_open_btn and pos_input_box and pos_confirm_btn):
        messagebox.showwarning("Thiếu tọa độ", "Vui lòng lưu đủ 3 tọa độ F7, F8, F9 trước!")
        return

    raw_text = text_area.get("1.0", tk.END).strip()
    if not raw_text:
        messagebox.showwarning("Cảnh báo", "Vui lòng dán danh sách code vào ô trống!")
        return

    try:
        wait_time = float(entry_delay.get())
    except ValueError:
        wait_time = 2.5

    codes = [line.strip() for line in raw_text.splitlines() if line.strip()]
    
    log_area.config(state=tk.NORMAL)
    log_area.delete("1.0", tk.END)
    log_area.config(state=tk.DISABLED)

    is_running = True
    btn_start.config(state=tk.DISABLED, text="Đang chạy... (Nhấn ESC để dừng)")
    
    # Tự động dạt cửa sổ tool sang góc phải màn hình để KHÔNG CHE khu vực nhập code trong game
    screen_w = root.winfo_screenwidth()
    root.geometry(f"450x640+{screen_w - 470}+50")
    
    threading.Thread(target=process_codes, args=(codes, wait_time), daemon=True).start()

def process_codes(codes, wait_time):
    global is_running
    for i in range(3, 0, -1):
        if not is_running:
            reset_ui()
            return
        lbl_status.config(text=f"Bắt đầu sau {i}s... (Nhấn ESC bất cứ lúc nào để dừng)")
        time.sleep(1)

    for index, code in enumerate(codes):
        if not is_running or keyboard.is_pressed('esc'):
            lbl_status.config(text="Đã dừng theo yêu cầu!")
            break

        lbl_status.config(text=f"Đang nhập ({index + 1}/{len(codes)}): {code}")

        # Kiểm tra thực tế tại thời điểm chuẩn bị nhập: Khung đang đóng hay mở?
        if not is_modal_still_open():
            # Khung đang ĐÓNG -> Bấm nút >> để mở
            pydirectinput.click(pos_open_btn.x, pos_open_btn.y)
            time.sleep(0.7)

        # Click vào ô nhập code
        pydirectinput.click(pos_input_box.x, pos_input_box.y)
        time.sleep(0.2)
        
        # Xóa sạch chữ cũ (nếu mã trước bị lỗi còn sót lại)
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.1)
        pyautogui.press('backspace')
        time.sleep(0.1)
        
        # Dán code mới
        pyperclip.copy(code)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.3)

        # Bấm nút Space Xác nhận
        pydirectinput.click(pos_confirm_btn.x, pos_confirm_btn.y)
        
        # Chờ game xử lý phản hồi
        time.sleep(wait_time)

        # Kiểm tra xem khung đã đóng hay vẫn mở
        if not is_modal_still_open():
            log_result(f"[THÀNH CÔNG] {code}")
        else:
            log_result(f"[THẤT BẠI / ĐÃ DÙNG] {code}")

    is_running = False
    reset_ui()
    lbl_status.config(text="Hoàn thành toàn bộ danh sách!")

def reset_ui():
    btn_start.config(state=tk.NORMAL, text="Bắt đầu tự động nhập")

def stop_hotkey():
    global is_running
    is_running = False

keyboard.add_hotkey('f7', on_f7)
keyboard.add_hotkey('f8', on_f8)
keyboard.add_hotkey('f9', on_f9)
keyboard.add_hotkey('esc', stop_hotkey)

# Giao diện GUI
root = tk.Tk()
root.title("Auto Code WWM - Chuẩn Pixel")
root.geometry("450x640")
root.attributes("-topmost", True)

frame_coord = tk.LabelFrame(root, text="Bước 1: Lấy 3 tọa độ (Kéo tool sang bên phải trước khi lấy!)", padx=10, pady=6)
frame_coord.pack(fill=tk.X, padx=15, pady=6)

lbl_c1 = tk.Label(frame_coord, text="1. Nút mở (>>): Chưa lưu (Di chuột tới >> và bấm F7)", fg="red")
lbl_c1.pack(anchor="w")
lbl_c2 = tk.Label(frame_coord, text="2. Ô nhập chữ: Chưa lưu (Mở khung, di tới ô nhập và bấm F8)", fg="red")
lbl_c2.pack(anchor="w")
lbl_c3 = tk.Label(frame_coord, text="3. Nút Xác nhận: Chưa lưu (Di tới Space Xác nhận và bấm F9)", fg="red")
lbl_c3.pack(anchor="w")

frame_opt = tk.Frame(root)
frame_opt.pack(fill=tk.X, padx=15, pady=4)
tk.Label(frame_opt, text="Thời gian chờ phản hồi (giây):", font=("Arial", 9, "bold")).pack(side=tk.LEFT)
entry_delay = tk.Entry(frame_opt, width=6, font=("Arial", 10))
entry_delay.insert(0, "2.5")
entry_delay.pack(side=tk.LEFT, padx=8)

tk.Label(root, text="Bước 2: Dán danh sách Code (mỗi code 1 dòng):", font=("Arial", 10, "bold")).pack(anchor="w", padx=15)
text_area = tk.Text(root, height=8, width=50, font=("Consolas", 10))
text_area.pack(padx=15, pady=4)

lbl_status = tk.Label(root, text="Sẵn sàng. Nhấn ESC bất cứ lúc nào để dừng.", fg="blue", font=("Arial", 9, "bold"))
lbl_status.pack(pady=3)

btn_start = tk.Button(root, text="Bắt đầu tự động nhập", command=start_redeem, bg="#28a745", fg="white", font=("Arial", 11, "bold"), height=2)
btn_start.pack(pady=5, fill=tk.X, padx=15)

tk.Label(root, text="Kết quả từng mã:", font=("Arial", 10, "bold")).pack(anchor="w", padx=15, pady=(6, 0))
log_area = scrolledtext.ScrolledText(root, height=9, width=50, font=("Consolas", 10), state=tk.DISABLED, bg="#f8f9fa")
log_area.pack(padx=15, pady=5)

root.mainloop()
