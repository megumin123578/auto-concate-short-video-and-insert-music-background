import os
import threading
import queue
import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkcalendar import DateEntry
from ffmpeg_helper import auto_concat 
import shutil
from module import (
    ROOT_DIR,
    SAVE_FOLDER,
    get_today_date_str,
    list_all_mp4_files,
    get_all_random_video_groups,
    list_all_mp3_files,
    mix_audio_with_bgm_ffmpeg,
    get_next_output_filename

)
import random

IS_WINDOWS = (os.name == 'nt')
mp3_list = list_all_mp3_files(r"\\192.168.1.92\Ổ Sever Mới\Định\Satisfy ASMR\SHORT AI\render nhac")

def os_join(*parts: str) -> str:
    return os.path.join(*parts)

def get_random_mp3_from_list(mp3_list):
    return random.choice(mp3_list) if mp3_list else None

class ConcatApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Ghép Short")
        self.minsize(800, 200)
        
        style = ttk.Style()
        style.theme_use("clam")

        # State
        today_str = str(get_today_date_str())
        self.dt_var = tk.StringVar(value=today_str)
        self.use_dt_path_var = tk.BooleanVar(value=True)
        self.input_folder_var = tk.StringVar(value=os_join(ROOT_DIR, today_str))
        self.save_folder_var = tk.StringVar(value=SAVE_FOLDER)

        self.total_mp4_var = tk.StringVar(value="0")
        self.num_groups_var = tk.StringVar(value="0")
        self.groups_done_var = tk.StringVar(value="0")
        

        self.groups: list[list[str]] = []
        self.stop_flag = threading.Event()
        self.worker: threading.Thread | None = None
        self.log_q: queue.Queue[str] = queue.Queue()

        self._build_ui()
        self._layout()
        self.load_state() 
        self.reload_groups()

    def _build_ui(self):
        self.frm_top = ttk.Frame(self)

        self.dt_label = ttk.Label(self.frm_top, text="Chọn ngày")
        self.dt_picker = DateEntry(
            self.frm_top, width=12, background='darkblue',
            foreground='white', borderwidth=2, date_pattern='dd.MM.yy'
        )
        self.dt_picker.bind("<<DateEntrySelected>>", lambda e: self.reload_groups())

        # Tùy chọn xuất
        self.frm_opts = ttk.LabelFrame(self, text="Tuỳ chọn xuất")
        self.btn_concat = ttk.Button(self.frm_opts, text="▶ Bắt đầu ghép", command=self.start_concat)
        self.btn_stop = ttk.Button(self.frm_opts, text="■ Dừng", command=self.stop_concat, state=tk.DISABLED)
        self.btn_resume = ttk.Button(self.frm_opts, text="|>>| Tiếp tục chạy", command=self.resume_concat, state=tk.DISABLED)
        self.btn_open_out = ttk.Button(self.frm_opts, text="📂 Mở thư mục lưu", command=self.open_output_folder)

        # Thống kê + tiến trình
        self.frm_stats = ttk.LabelFrame(self, text="Thống kê")
        self.lbl_total_mp4 = ttk.Label(self.frm_stats, text="Tổng file MP4:")
        self.val_total_mp4 = ttk.Label(self.frm_stats, textvariable=self.total_mp4_var)
        self.lbl_num_groups = ttk.Label(self.frm_stats, text="Số nhóm:")
        self.val_num_groups = ttk.Label(self.frm_stats, textvariable=self.num_groups_var)
        self.lbl_group_size = ttk.Label(self.frm_stats, text="Số lượng nhóm đã chạy:")
        self.val_group_size = ttk.Label(self.frm_stats, textvariable=self.groups_done_var)

        self.progress = ttk.Progressbar(self.frm_stats, orient=tk.HORIZONTAL, mode='determinate')
        self.status_var = tk.StringVar(value="0%")
        self.status_lbl = ttk.Label(self.frm_stats, textvariable=self.status_var)

    def _layout(self):
        pad = dict(padx=6, pady=4)

        self.frm_top.pack(fill=tk.X, **pad)
        self.dt_label.grid(row=0, column=0, sticky='e', **pad)
        self.dt_picker.grid(row=0, column=1, sticky='w', **pad)
        self.frm_top.columnconfigure(2, weight=1)

        self.frm_opts.pack(fill=tk.X, **pad)
        self.btn_concat.grid(row=0, column=0, sticky='w', **pad)
        self.btn_stop.grid(row=0, column=1, sticky='w', **pad)
        self.btn_resume.grid(row=0, column=2, sticky='w', **pad)
        self.btn_open_out.grid(row=0, column=3, sticky='w', **pad)  # CHỈ CẦN ĐỔI lại row=0

        self.frm_stats.pack(fill=tk.X, **pad)
        self.lbl_total_mp4.grid(row=0, column=0, sticky='e', **pad)
        self.val_total_mp4.grid(row=0, column=1, sticky='w', **pad)
        self.lbl_num_groups.grid(row=0, column=2, sticky='e', **pad)
        self.val_num_groups.grid(row=0, column=3, sticky='w', **pad)
        self.lbl_group_size.grid(row=0, column=4, sticky='e', **pad)
        self.val_group_size.grid(row=0, column=5, sticky='w', **pad)

        self.progress.grid(row=1, column=0, columnspan=6, sticky='we', **pad)
        self.status_lbl.grid(row=2, column=0, columnspan=6, sticky='w', **pad)
        self.frm_stats.columnconfigure(5, weight=1)



    def reload_groups(self):
        dt = self.dt_picker.get().strip()
        if not dt:
            messagebox.showwarning("Thiếu ngày", "Hãy nhập ngày (vd: 29.09.25)")
            return

        folder = os_join(ROOT_DIR, dt)
        out_folder = SAVE_FOLDER   # luôn lưu ở SAVE_FOLDER

        self.input_folder_var.set(folder)
        self.save_folder_var.set(out_folder)

        if not os.path.isdir(folder):
            messagebox.showerror("Sai đường dẫn", f"Thư mục không tồn tại:\n{folder}")
            return

        try:
            all_videos = list_all_mp4_files(folder)
            groups = get_all_random_video_groups(folder)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi khi đọc video/nhóm:\n{e}")
            return

        self.groups = groups or []
        total_mp4 = len(all_videos)
        num_groups = len(self.groups)

        self.total_mp4_var.set(str(total_mp4))
        self.num_groups_var.set(str(num_groups))
        self.groups_done_var.set("0")
        self.progress['value'] = 0



    def start_concat(self):
        self.groups_done_var.set("0")
        if self.worker and self.worker.is_alive():
            messagebox.showinfo("Đang chạy", "Tiến trình đang chạy, hãy dừng trước khi chạy lại.")
            return
        if not self.groups:
            messagebox.showwarning("Chưa có nhóm", "Hãy Reload nhóm trước.")
            return

        out_dir = self.save_folder_var.get().strip()
        if not out_dir:
            messagebox.showwarning("Thiếu thư mục lưu", "Hãy chọn thư mục lưu")
            return
        try:
            os.makedirs(out_dir, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tạo thư mục lưu:\n{e}")
            return

        self.stop_flag.clear()
        self.btn_concat.configure(state=tk.DISABLED)
        self.btn_stop.configure(state=tk.NORMAL)
        self.status_var.set("Đang ghép...")
        self.progress['value'] = 0
        self.progress['maximum'] = len(self.groups)

        args = (self.groups, out_dir)
        self.worker = threading.Thread(target=self._do_concat_worker, args=args, daemon=True)
        self.worker.start()
        self.after(150, self._poll_worker)

    def stop_concat(self):
        if self.worker and self.worker.is_alive():
            self.stop_flag.set()
            self.btn_resume.configure(state=tk.NORMAL)

    def resume_concat(self):
        try:
        
            already_done = int(self.groups_done_var.get())
        except ValueError:
            already_done = 0

        total_groups = len(self.groups)

        # Đảm bảo không vượt quá số nhóm
        if already_done >= total_groups:
            messagebox.showinfo("Không còn nhóm nào", "Tất cả nhóm đã được xử lý.")
            return

        # Cập nhật lại progress bar nếu cần (phòng trường hợp mất đồng bộ)
        self.progress['value'] = already_done
        self.progress['maximum'] = total_groups

        # Lấy danh sách nhóm còn lại
        todo_remaining = self.groups[already_done:]

        if not todo_remaining:
            messagebox.showinfo("Không còn nhóm nào", "Không có nhóm nào còn lại để chạy.")
            return

        out_dir = self.save_folder_var.get().strip()
        if not out_dir:
            messagebox.showwarning("Thiếu thư mục lưu", "Hãy chọn thư mục lưu")
            return

        self.stop_flag.clear()
        self.btn_concat.configure(state=tk.DISABLED)
        self.btn_resume.configure(state=tk.DISABLED)
        self.btn_stop.configure(state=tk.NORMAL)
        self.status_var.set(f"Tiếp tục từ nhóm {already_done + 1}...")

        # Bắt đầu worker với phần còn lại
        args = (todo_remaining, out_dir)
        self.worker = threading.Thread(target=self._do_concat_worker, args=args, daemon=True)
        self.worker.start()
        self.after(150, self._poll_worker)


    def _do_concat_worker(self, todo: list[list[str]], out_dir: str):
        log_dir = os.path.abspath("log")
        os.makedirs(log_dir, exist_ok=True)
        date_str = self.dt_picker.get().strip().replace("/", ".")
        log_path = os.path.join(log_dir, f"{date_str}.txt")

        script_dir = os.getcwd()

        try:
            with open(log_path, "a", encoding="utf-8") as f_log:
                for i, group in enumerate(todo):
                    if self.stop_flag.is_set():
                        break

                    temp_concat_path = os.path.join(script_dir, "temp.mp4")  # luôn tạm

                    try:
                        # 1. Ghép video nhóm thành file tạm
                        auto_concat(group, temp_concat_path)
                        relative_paths = [os.path.relpath(p, start=ROOT_DIR) for p in group]

                        # 2. Chọn nhạc nền
                        bg_audio = get_random_mp3_from_list(mp3_list)
                        if bg_audio and os.path.isfile(bg_audio):
                            try:
                                # mix_audio_with_bgm_ffmpeg đã tự tính số thứ tự và trả về path thực tế
                                output_video = mix_audio_with_bgm_ffmpeg(
                                    input_video=temp_concat_path,
                                    bgm_audio=bg_audio,
                                    output_dir=SAVE_FOLDER,
                                    bgm_volume=0.9
                                )
                                log_line = f"{os.path.basename(output_video)}: {', '.join(relative_paths)} + BGM: {os.path.basename(bg_audio)}"
                            except Exception as music_err:
                                log_line = f"ERROR chèn nhạc ({music_err}) | Files: {', '.join(relative_paths)}"
                                output_video = None
                        else:
                            # Không có nhạc nền → copy ra file kế tiếp
                            output_video = get_next_output_filename(SAVE_FOLDER)
                            shutil.copy2(temp_concat_path, output_video)
                            log_line = f"{os.path.basename(output_video)}: {', '.join(relative_paths)} | Không có nhạc nền → chỉ copy"

                    except Exception as e:
                        log_line = f"ERROR ghép video ({e}) | Files: {', '.join(group)}"
                        output_video = None

                    finally:
                        # 3. Xoá file tạm
                        if os.path.exists(temp_concat_path):
                            try:
                                os.remove(temp_concat_path)
                            except Exception as rm_err:
                                log_line += f" | Lỗi xoá file tạm: {rm_err}"

                    # 4. Ghi log
                    f_log.write(log_line + "\n")
                    f_log.flush()
                    self._enqueue(lambda: self._inc_progress())

        finally:
            self._enqueue(self._on_worker_done)





    def _inc_progress(self):
        self.progress['value'] = min(self.progress['maximum'], self.progress['value'] + 1)
        percent = (self.progress['value'] / self.progress['maximum']) * 100
        self.status_var.set(f"{percent:.1f}%")
        self.groups_done_var.set(str(int(self.groups_done_var.get()) + 1))
        self.save_state() 


    def _on_worker_done(self):
        self.btn_concat.configure(state=tk.NORMAL)
        self.btn_stop.configure(state=tk.DISABLED)
        # self.status_var.set("100.0%")
        self.btn_resume.configure(state=tk.DISABLED)


    def _poll_worker(self):
        if self.worker and self.worker.is_alive():
            self.after(200, self._poll_worker)

    def _enqueue(self, fn):
        self.after(0, fn)

    def open_output_folder(self):
        path = self.save_folder_var.get().strip()
        if not path or not os.path.isdir(path):
            messagebox.showwarning("Không tìm thấy", "Thư mục lưu chưa tồn tại.")
            return
        os.startfile(path)

    def save_state(self):
        dt = self.dt_picker.get().strip()
        path = f"state_{dt}.txt"
        with open(path, "w") as f:
            f.write(self.groups_done_var.get())

    def load_state(self):
        dt = self.dt_picker.get().strip()
        path = f"state_{dt}.txt"
        if os.path.exists(path):
            with open(path, "r") as f:
                val = f.read().strip()
                if val.isdigit():
                    self.groups_done_var.set(val)



if __name__ == '__main__':
    app = ConcatApp()
    app.mainloop()
