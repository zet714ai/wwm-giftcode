import re
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import pyautogui
import keyboard

class WWMApp:
    def __init__(self, root, data_manager, auto_engine, scraper_service):
        self.root = root
        self.dm = data_manager
        self.engine = auto_engine
        self.scraper = scraper_service

        self.root.title("WWM Giftcode Manager v3.0 (Multi-URL & Multi-Acc)")
        self.root.geometry("510x900")
        self.root.attributes("-topmost", True)

        self.setup_hotkeys()
        self.build_ui()
        self.load_saved_state()

    def setup_hotkeys(self):
        keyboard.add_hotkey('f7', lambda: self.root.after(0, self.capture_f7))
        keyboard.add_hotkey('f8', lambda: self.root.after(0, self.capture_f8))
        keyboard.add_hotkey('f9', lambda: self.root.after(0, self.capture_f9))
        keyboard.add_hotkey('esc', self.engine.stop)

    def build_ui(self):
        # --- PHẦN 1: QUẢN LÝ TÀI KHOẢN ---
        frame_acc = tk.LabelFrame(self.root, text="1. Chọn Tài Khoản (Tự động lọc code chưa nhập)", padx=10, pady=8)
        frame_acc.pack(fill=tk.X, padx=12, pady=5)

        row_acc = tk.Frame(frame_acc)
        row_acc.pack(fill=tk.X)

        self.acc_var = tk.StringVar()
        self.combo_acc = ttk.Combobox(row_acc, textvariable=self.acc_var, state="readonly", width=22, font=("Arial", 10, "bold"))
        self.combo_acc.pack(side=tk.LEFT, padx=(0, 8))
        self.combo_acc.bind("<<ComboboxSelected>>", self.on_account_changed)

        tk.Button(row_acc, text="+ Thêm Acc", command=self.add_account, bg="#007bff", fg="white", width=9).pack(side=tk.LEFT, padx=2)
        tk.Button(row_acc, text="Xóa Acc", command=self.delete_account, bg="#dc3545", fg="white", width=8).pack(side=tk.LEFT, padx=2)
        tk.Button(row_acc, text="Reset Lịch sử", command=self.reset_history, width=10).pack(side=tk.LEFT, padx=2)

        self.lbl_stats = tk.Label(
            frame_acc,
            text="Kho: 0 | Dùng được: 0 | Chưa thử: 0 | Lỗi/chưa rõ hạn: 0",
            fg="#333",
            font=("Arial", 9),
            wraplength=460,
            justify=tk.LEFT,
        )
        self.lbl_stats.pack(anchor="w", pady=(6, 0))

        # --- PHẦN 2: TỌA ĐỘ (LƯU VĨNH VIỄN) ---
        frame_coord = tk.LabelFrame(self.root, text="2. Tọa độ Click (Tự động lưu - Chỉ lấy lại nếu đổi độ phân giải)", padx=10, pady=6)
        frame_coord.pack(fill=tk.X, padx=12, pady=5)

        self.lbl_c1 = tk.Label(frame_coord, text="F7 - Nút mở (>>): Chưa lưu", fg="red")
        self.lbl_c1.pack(anchor="w")
        self.lbl_c2 = tk.Label(frame_coord, text="F8 - Ô nhập chữ: Chưa lưu", fg="red")
        self.lbl_c2.pack(anchor="w")
        self.lbl_c3 = tk.Label(frame_coord, text="F9 - Nút Xác nhận: Chưa lưu", fg="red")
        self.lbl_c3.pack(anchor="w")

        # --- PHẦN 3: NGUỒN CODE (THÊM TAY HOẶC CÀO WEB) ---
        frame_pool = tk.LabelFrame(self.root, text="3. Nguồn Code (quét URL hoặc nhập tay)", padx=10, pady=6)
        frame_pool.pack(fill=tk.X, padx=12, pady=5)

        btn_row = tk.Frame(frame_pool)
        btn_row.pack(fill=tk.X, pady=(0, 4))
        self.btn_scrape = tk.Button(
            btn_row,
            text="🌐 Quét URL",
            command=self.start_web_scrape,
            bg="#17a2b8",
            fg="white",
        )
        self.btn_scrape.pack(side=tk.LEFT)
        tk.Button(btn_row, text="⚙ URL nguồn", command=self.open_url_editor).pack(side=tk.LEFT, padx=4)
        tk.Button(btn_row, text="📊 Kho code", command=self.open_pool_viewer).pack(side=tk.LEFT)
        tk.Button(
            btn_row,
            text="📥 Nạp tay",
            command=self.import_manual_codes,
            bg="#6c757d",
            fg="white",
        ).pack(side=tk.RIGHT)

        import_text_frame = tk.Frame(frame_pool)
        import_text_frame.pack(fill=tk.X)
        self.txt_import = tk.Text(
            import_text_frame,
            height=8,
            font=("Consolas", 9),
            wrap=tk.WORD,
        )
        import_scrollbar = ttk.Scrollbar(
            import_text_frame,
            orient=tk.VERTICAL,
            command=self.txt_import.yview,
        )
        self.txt_import.configure(yscrollcommand=import_scrollbar.set)
        self.txt_import.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        import_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tk.Label(
            frame_pool,
            text="Dán code cách nhau bằng dòng, khoảng trắng, tab hoặc dấu câu; bấm “Nạp tay”.",
            anchor="w",
            fg="#555",
        ).pack(fill=tk.X, pady=(2, 0))

        # --- PHẦN 4: DANH SÁCH CODE CHỜ CHẠY CHO ACC HIỆN TẠI ---
        frame_run = tk.LabelFrame(self.root, text="4. Code CHƯA THỬ / chưa xác nhận cho Acc đang chọn", padx=10, pady=6)
        frame_run.pack(fill=tk.X, padx=12, pady=5)

        opt_row = tk.Frame(frame_run)
        opt_row.pack(fill=tk.X, pady=(0, 4))
        tk.Label(opt_row, text="Chờ phản hồi (giây):", font=("Arial", 9, "bold")).pack(side=tk.LEFT)
        self.entry_delay = tk.Entry(opt_row, width=5, font=("Arial", 10))
        self.entry_delay.pack(side=tk.LEFT, padx=6)

        self.txt_pending = tk.Text(frame_run, height=6, font=("Consolas", 10), bg="#fffef0")
        self.txt_pending.pack(fill=tk.X)

        self.lbl_status = tk.Label(self.root, text="Sẵn sàng. Nhấn ESC bất cứ lúc nào để dừng.", fg="blue", font=("Arial", 9, "bold"))
        self.lbl_status.pack(pady=3)

        self.btn_start = tk.Button(self.root, text="▶ BẮT ĐẦU NHẬP CHO ACC NÀY", command=self.start_auto, bg="#28a745", fg="white", font=("Arial", 11, "bold"), height=2)
        self.btn_start.pack(fill=tk.X, padx=12, pady=4)

        # --- PHẦN 5: KẾT QUẢ CHẠY ---
        self.log_area = scrolledtext.ScrolledText(self.root, height=6, font=("Consolas", 9), state=tk.DISABLED, bg="#f8f9fa")
        self.log_area.pack(fill=tk.X, padx=12, pady=(2, 10))

    # --- LOGIC GIAO DIỆN ---
    def load_saved_state(self):
        # Load tọa độ
        coords = self.dm.get_coords()
        if coords["open_btn"]:
            self.lbl_c1.config(text=f"F7 - Nút mở (>>): {coords['open_btn']} (Đã lưu)", fg="green")
        if coords["input_box"]:
            self.lbl_c2.config(text=f"F8 - Ô nhập chữ: {coords['input_box']} (Đã lưu)", fg="green")
        if coords["confirm_btn"]:
            self.lbl_c3.config(text=f"F9 - Nút Xác nhận: {coords['confirm_btn']} (Đã lưu)", fg="green")

        self.entry_delay.delete(0, tk.END)
        self.entry_delay.insert(0, str(self.dm.data.get("delay", 2.5)))

        # Load danh sách tài khoản
        accs = self.dm.get_account_names()
        self.combo_acc["values"] = accs
        last_acc = self.dm.data.get("last_account", accs[0])
        self.acc_var.set(last_acc if last_acc in accs else accs[0])
        self.refresh_pending_list()

    def refresh_pending_list(self):
        acc = self.acc_var.get()
        pool = self.dm.data["code_pool"]
        total = len(pool)
        valid = sum(1 for info in pool.values() if info.get("status") == "valid")
        never_tried = sum(
            1
            for info in pool.values()
            if info.get("status") == "new" and not info.get("account_results")
        )
        failed_unverified = sum(
            1
            for info in pool.values()
            if info.get("status") == "new"
            and any(result == "failed" for result in info.get("account_results", {}).values())
        )
        dead = sum(1 for info in pool.values() if info.get("status") == "dead")
        used = len(self.dm.data["accounts"].get(acc, {}).get("used_codes", []))
        pending = self.dm.get_pending_codes_for_account(acc)

        self.lbl_stats.config(
            text=(
                f"📦 Tổng: {total}  |  ✅ Dùng được: {valid}  |  🆕 Chưa thử: {never_tried}\n"
                f"⚠️ Lỗi/chưa rõ hạn: {failed_unverified}  |  ⛔ Hết hạn: {dead}  |  "
                f"👤 Acc đã thử: {used}  |  ⏳ Chờ: {len(pending)}"
            )
        )
        self.txt_pending.delete("1.0", tk.END)
        if pending:
            self.txt_pending.insert("1.0", "\n".join(pending))

    def on_account_changed(self, event=None):
        acc = self.acc_var.get()
        self.dm.set_last_account(acc)
        self.refresh_pending_list()

    def add_account(self):
        name = self._ask_account_name()
        if name and self.dm.add_account(name):
            self.load_saved_state()
        elif name:
            messagebox.showwarning("Lỗi", "Tên tài khoản không hợp lệ hoặc đã tồn tại!")

    def _ask_account_name(self):
        window = tk.Toplevel(self.root)
        window.title("Thêm tài khoản")
        window.transient(self.root)
        window.resizable(False, False)
        window.attributes("-topmost", True)

        tk.Label(
            window,
            text="Nhập tên gợi nhớ cho tài khoản mới:",
        ).pack(anchor="w", padx=12, pady=(12, 4))
        entry = tk.Entry(window, width=32)
        entry.pack(padx=12, pady=4)
        result = {"name": None}

        def finish():
            result["name"] = entry.get().strip()
            window.destroy()

        button_row = tk.Frame(window)
        button_row.pack(fill=tk.X, padx=12, pady=10)
        tk.Button(button_row, text="Hủy", command=window.destroy).pack(side=tk.RIGHT)
        tk.Button(
            button_row,
            text="Thêm",
            command=finish,
            default=tk.ACTIVE,
        ).pack(side=tk.RIGHT, padx=5)
        entry.bind("<Return>", lambda _event: finish())
        window.protocol("WM_DELETE_WINDOW", window.destroy)

        window.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() - window.winfo_width()) // 2
        y = self.root.winfo_rooty() + (self.root.winfo_height() - window.winfo_height()) // 2
        window.geometry(f"+{max(0, x)}+{max(0, y)}")
        window.lift()
        window.grab_set()
        entry.focus_force()
        self.root.wait_window(window)
        return result["name"]

    def delete_account(self):
        acc = self.acc_var.get()
        if messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa hồ sơ '{acc}'?"):
            if self.dm.delete_account(acc):
                self.load_saved_state()
            else:
                messagebox.showwarning("Không thể xóa", "Phải giữ lại ít nhất 1 tài khoản!")

    def reset_history(self):
        acc = self.acc_var.get()
        if messagebox.askyesno("Reset lịch sử", f"Xóa toàn bộ lịch sử đã nhập của '{acc}' để chạy lại tất cả code từ đầu?"):
            self.dm.reset_account_history(acc)
            self.refresh_pending_list()

    def import_manual_codes(self):
        raw = self.txt_import.get("1.0", tk.END).strip()
        if not raw:
            return

        codes = self._parse_manual_codes(raw)
        if not codes:
            messagebox.showwarning(
                "Không tìm thấy mã",
                "Không nhận diện được code. Hãy nhập mã gồm 4-25 chữ/số.",
            )
            return

        self.txt_import.delete("1.0", tk.END)
        self.txt_import.insert("1.0", "\n".join(codes))
        added = self.dm.add_codes_to_pool(codes, source="Nhập tay")
        self.refresh_pending_list()
        messagebox.showinfo(
            "Đã nạp vào kho",
            f"Đã nhận diện {len(codes)} mã, thêm mới {added} mã "
            f"(bỏ qua {len(codes) - added} mã đã có).",
        )

    @staticmethod
    def _parse_manual_codes(raw):
        ignored_tokens = {
            "ACTIVE",
            "AVAILABLE",
            "CODE",
            "CODES",
            "EXPIRED",
            "INACTIVE",
            "NEW",
            "STATUS",
        }
        candidates = re.findall(r"[A-Za-z0-9]{4,25}", raw)
        return list(
            dict.fromkeys(
                token.upper()
                for token in candidates
                if token.upper() not in ignored_tokens
                and any(character.isalpha() for character in token)
            )
        )

    def fetch_web_codes(self):
        self.start_web_scrape()

    def open_url_editor(self):
        window = tk.Toplevel(self.root)
        window.title("Danh sách URL nguồn (mỗi URL một dòng)")
        window.geometry("520x360")
        window.transient(self.root)

        tk.Label(
            window,
            text="Nhập các trang có danh sách giftcode; chỉ chấp nhận URL HTTP/HTTPS.",
        ).pack(anchor="w", padx=10, pady=8)
        text = tk.Text(window, height=12, font=("Consolas", 9))
        text.pack(fill=tk.BOTH, expand=True, padx=10)
        text.insert("1.0", "\n".join(self.dm.get_urls()))

        def save_urls():
            try:
                self.dm.save_urls(text.get("1.0", tk.END).splitlines())
            except ValueError as exc:
                messagebox.showwarning("URL không hợp lệ", str(exc), parent=window)
                return
            window.destroy()
            messagebox.showinfo(
                "Đã lưu",
                f"Đã lưu {len(self.dm.get_urls())} URL nguồn.",
                parent=self.root,
            )

        tk.Button(
            window,
            text="Lưu danh sách URL",
            command=save_urls,
            bg="#28a745",
            fg="white",
        ).pack(pady=8)

    def open_pool_viewer(self):
        window = tk.Toplevel(self.root)
        window.title("Kho code, nguồn và kết quả thử")
        window.geometry("820x460")
        window.transient(self.root)
        window.attributes("-topmost", True)

        controls = tk.Frame(window)
        controls.pack(fill=tk.X, padx=10, pady=(10, 4))

        tk.Label(controls, text="Tìm:").grid(row=0, column=0, sticky="w")
        search_var = tk.StringVar()
        search_entry = ttk.Entry(controls, textvariable=search_var)
        search_entry.grid(row=0, column=1, sticky="ew", padx=(4, 10))

        tk.Label(controls, text="Trạng thái:").grid(row=0, column=2, sticky="w")
        status_var = tk.StringVar(value="Tất cả")
        status_filter = ttk.Combobox(
            controls,
            textvariable=status_var,
            state="readonly",
            width=24,
            values=(
                "Tất cả",
                "Chưa thử",
                "Thử thất bại (chưa rõ hạn)",
                "Đã nhập thành công",
                "Đã đánh dấu hết hạn",
            ),
        )
        status_filter.grid(row=0, column=3, sticky="ew", padx=(4, 0))

        tk.Label(controls, text="Nguồn:").grid(row=1, column=0, sticky="w", pady=(6, 0))
        source_var = tk.StringVar(value="Tất cả")
        sources = sorted(
            {
                source
                for info in self.dm.data["code_pool"].values()
                for source in info.get("sources", [])
            },
            key=str.casefold,
        )
        source_filter = ttk.Combobox(
            controls,
            textvariable=source_var,
            state="readonly",
            values=["Tất cả", *sources],
        )
        source_filter.grid(row=1, column=1, sticky="ew", padx=(4, 10), pady=(6, 0))

        tk.Label(controls, text="Tài khoản:").grid(row=1, column=2, sticky="w", pady=(6, 0))
        account_var = tk.StringVar(value="Tất cả")
        account_filter = ttk.Combobox(
            controls,
            textvariable=account_var,
            state="readonly",
            values=["Tất cả", *self.dm.get_account_names()],
        )
        account_filter.grid(row=1, column=3, sticky="ew", padx=(4, 0), pady=(6, 0))
        controls.grid_columnconfigure(1, weight=1)
        controls.grid_columnconfigure(3, weight=1)

        table_frame = tk.Frame(window)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)
        columns = ("code", "status", "sources", "results")
        table = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="extended",
        )
        sort_state = {"column": "code", "reverse": False}

        def sort_by(column):
            if render_timer["id"] is not None:
                window.after_cancel(render_timer["id"])
                render_timer["id"] = None
            if sort_state["column"] == column:
                sort_state["reverse"] = not sort_state["reverse"]
            else:
                sort_state["column"] = column
                sort_state["reverse"] = False
            render_rows()

        table.heading("code", text="Code", command=lambda: sort_by("code"))
        table.heading("status", text="Trạng thái", command=lambda: sort_by("status"))
        table.heading("sources", text="Nguồn", command=lambda: sort_by("sources"))
        table.heading(
            "results",
            text="Kết quả theo tài khoản",
            command=lambda: sort_by("results"),
        )
        table.column("code", width=110, stretch=False)
        table.column("status", width=155, stretch=False)
        table.column("sources", width=210, stretch=True)
        table.column("results", width=285, stretch=True)
        vertical_scrollbar = ttk.Scrollbar(
            table_frame,
            orient=tk.VERTICAL,
            command=table.yview,
        )
        table.configure(yscrollcommand=vertical_scrollbar.set)
        table.grid(row=0, column=0, sticky="nsew")
        vertical_scrollbar.grid(row=0, column=1, sticky="ns")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        render_timer = {"id": None}

        def render_rows(*_args):
            query = search_var.get().strip().casefold()
            selected_status = status_var.get()
            selected_source = source_var.get()
            selected_account = account_var.get()
            filtered_rows = []

            for code, info in self.dm.data["code_pool"].items():
                status = self._code_status_label(info)
                sources = ", ".join(info.get("sources", [])) or "Không rõ"
                account_results = info.get("account_results", {})
                results = ", ".join(
                    f"{account}: {'thành công' if result == 'success' else 'thất bại'}"
                    for account, result in account_results.items()
                ) or "Chưa thử"

                if selected_status != "Tất cả" and status != selected_status:
                    continue
                if selected_source != "Tất cả" and selected_source not in info.get("sources", []):
                    continue
                if selected_account != "Tất cả" and selected_account not in account_results:
                    continue
                if query and query not in " ".join((code, status, sources, results)).casefold():
                    continue

                filtered_rows.append((code, info, status, sources, results))

            column_index = {"code": 0, "status": 2, "sources": 3, "results": 4}
            column = sort_state["column"]
            if column == "status":
                status_order = {
                    "Chưa thử": 0,
                    "Thử thất bại (chưa rõ hạn)": 1,
                    "Đã nhập thành công": 2,
                    "Đã đánh dấu hết hạn": 3,
                }
                filtered_rows.sort(
                    key=lambda row: status_order.get(row[2], 99),
                    reverse=sort_state["reverse"],
                )
            else:
                index = column_index[column]
                filtered_rows.sort(
                    key=lambda row: row[index].casefold(),
                    reverse=sort_state["reverse"],
                )

            table.delete(*table.get_children())
            for code, _info, status, sources_text, results in filtered_rows:
                table.insert(
                    "",
                    tk.END,
                    iid=code,
                    values=(code, status, sources_text, results),
                )
            count_label.config(text=f"Hiển thị {len(filtered_rows)} / {len(self.dm.data['code_pool'])} mã")

        def schedule_render(*_args):
            if render_timer["id"] is not None:
                window.after_cancel(render_timer["id"])
            render_timer["id"] = window.after(120, run_scheduled_render)

        def run_scheduled_render():
            render_timer["id"] = None
            render_rows()

        search_var.trace_add("write", schedule_render)
        status_filter.bind("<<ComboboxSelected>>", schedule_render)
        source_filter.bind("<<ComboboxSelected>>", schedule_render)
        account_filter.bind("<<ComboboxSelected>>", schedule_render)

        for column, title in (
            ("code", "Code"),
            ("status", "Trạng thái"),
            ("sources", "Nguồn"),
            ("results", "Kết quả theo tài khoản"),
        ):
            table.heading(column, text=title, command=lambda col=column: sort_by(col))

        count_label = tk.Label(window, anchor="w", fg="#555")
        count_label.pack(fill=tk.X, padx=12)
        render_rows()

        button_row = tk.Frame(window)
        button_row.pack(fill=tk.X, padx=10, pady=(4, 10))
        tk.Label(
            button_row,
            text="Bấm tiêu đề cột để sắp xếp; chọn nhiều dòng bằng Ctrl/Shift.",
            fg="#555",
        ).pack(side=tk.LEFT)
        tk.Button(
            button_row,
            text="Đánh dấu hết hạn",
            command=lambda: self._set_selected_code_status(table, "dead", render_rows),
        ).pack(side=tk.RIGHT, padx=(5, 0))
        tk.Button(
            button_row,
            text="Khôi phục về chưa xác nhận",
            command=lambda: self._set_selected_code_status(table, "new", render_rows),
        ).pack(side=tk.RIGHT)
        window.lift()
        window.focus_force()

    @staticmethod
    def _code_status_label(info):
        status = info.get("status", "new")
        if status == "valid":
            return "Đã nhập thành công"
        if status == "dead":
            return "Đã đánh dấu hết hạn"
        if any(result == "failed" for result in info.get("account_results", {}).values()):
            return "Thử thất bại (chưa rõ hạn)"
        return "Chưa thử"

    def _set_selected_code_status(self, table, status, refresh_table=None):
        selection = table.selection()
        if not selection:
            messagebox.showwarning("Chưa chọn code", "Hãy chọn một hoặc nhiều code trong bảng.")
            return
        count = len(selection)
        if status == "dead" and not messagebox.askyesno(
            "Đánh dấu hết hạn",
            f"Đánh dấu {count} code đã chọn hết hạn để ẩn khỏi danh sách của tất cả tài khoản?",
        ):
            return
        for code in selection:
            self.dm.set_code_status(code, status)
        if refresh_table:
            refresh_table()
        else:
            for code in selection:
                info = self.dm.data["code_pool"][code]
                values = list(table.item(code, "values"))
                values[1] = self._code_status_label(info)
                table.item(code, values=values)
        self.refresh_pending_list()

    def start_web_scrape(self):
        urls = self.dm.get_urls()
        if not urls:
            messagebox.showwarning(
                "Chưa có URL",
                "Hãy chọn 'Quản lý URL' và thêm ít nhất một đường dẫn.",
            )
            return
        self.btn_scrape.config(state=tk.DISABLED, text="Đang quét...")
        threading.Thread(
            target=self._run_scrape_thread,
            args=(urls,),
            daemon=True,
        ).start()

    def _run_scrape_thread(self, urls):
        try:
            success, summary = self.scraper.fetch_from_urls(urls)
        except Exception as exc:
            self.root.after(0, self._on_scrape_error, str(exc))
            return
        self.root.after(0, self._on_scrape_done, success, summary)

    def _on_scrape_done(self, success, summary):
        self.btn_scrape.config(state=tk.NORMAL, text="🌐 Quét URL")
        self.refresh_pending_list()
        dialog = messagebox.showinfo if success else messagebox.showwarning
        dialog("Kết quả quét Web", summary)

    def _on_scrape_error(self, error):
        self.btn_scrape.config(state=tk.NORMAL, text="🌐 Quét URL")
        messagebox.showerror("Lỗi quét Web", error)

    # --- LẤY TỌA ĐỘ ---
    def capture_f7(self):
        pos = pyautogui.position()
        self.dm.save_coord("open_btn", (pos.x, pos.y))
        self.lbl_c1.config(text=f"F7 - Nút mở (>>): [{pos.x}, {pos.y}] (Đã lưu)", fg="green")

    def capture_f8(self):
        pos = pyautogui.position()
        sample_y = max(0, pos.y - 50)
        color = self.engine.get_pixel_color(pos.x, sample_y)
        self.dm.save_coord("input_box", (pos.x, pos.y), color)
        self.lbl_c2.config(text=f"F8 - Ô nhập chữ: [{pos.x}, {pos.y}] (Đã lưu + Màu)", fg="green")

    def capture_f9(self):
        pos = pyautogui.position()
        self.dm.save_coord("confirm_btn", (pos.x, pos.y))
        self.lbl_c3.config(text=f"F9 - Nút Xác nhận: [{pos.x}, {pos.y}] (Đã lưu)", fg="green")

    # --- CHẠY AUTO ---
    def append_log(self, text):
        self.root.after(0, self._append_log, text)

    def _append_log(self, text):
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, text + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)

    def update_status(self, msg):
        self.root.after(0, self.lbl_status.config, {"text": msg})

    def on_run_finished(self, msg):
        self.root.after(0, self._on_run_finished, msg)

    def _on_run_finished(self, msg):
        self.lbl_status.config(text=msg)
        self.btn_start.config(state=tk.NORMAL, text="▶ BẮT ĐẦU NHẬP CHO ACC NÀY")
        self.refresh_pending_list()

    def _run_batch(self, acc_name, codes, wait_time):
        try:
            self.engine.run_batch(
                acc_name,
                codes,
                wait_time,
                self.update_status,
                self.append_log,
                self.on_run_finished,
            )
        except Exception as exc:
            self.root.after(0, self._handle_run_error, str(exc))

    def _handle_run_error(self, error):
        self.engine.stop()
        self.lbl_status.config(text="Đã xảy ra lỗi khi chạy.")
        self.btn_start.config(state=tk.NORMAL, text="▶ BẮT ĐẦU NHẬP CHO ACC NÀY")
        messagebox.showerror("Lỗi khi chạy", error)

    def start_auto(self):
        coords = self.dm.get_coords()
        if not (coords["open_btn"] and coords["input_box"] and coords["confirm_btn"]):
            messagebox.showwarning("Thiếu tọa độ", "Vui lòng lấy đủ 3 tọa độ F7, F8, F9 trước!")
            return

        raw_pending = self.txt_pending.get("1.0", tk.END).strip()
        if not raw_pending:
            messagebox.showinfo("Hoàn tất", "Tài khoản này đã nhập hết tất cả code trong kho rồi!")
            return

        codes = [line.strip() for line in raw_pending.splitlines() if line.strip()]
        try:
            wait_time = float(self.entry_delay.get())
            self.dm.save_delay(wait_time)
        except ValueError:
            wait_time = 2.5

        acc_name = self.acc_var.get()
        self.log_area.config(state=tk.NORMAL)
        self.log_area.delete("1.0", tk.END)
        self.log_area.config(state=tk.DISABLED)

        self.btn_start.config(state=tk.DISABLED, text="ĐANG CHẠY... (NHẤN ESC ĐỂ DỪNG)")

        # Đẩy tool sang phải màn hình để tránh che game
        screen_w = self.root.winfo_screenwidth()
        self.root.geometry(f"510x900+{screen_w - 530}+30")

        threading.Thread(
            target=self._run_batch,
            args=(acc_name, codes, wait_time),
            daemon=True
        ).start()