import tkinter as tk
from tkinter import ttk, messagebox, font
import threading
import time
from datetime import datetime, timedelta
import sys


class ReminderApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("RestAlert智能休息提醒系统")
        self.root.geometry("500x400")  # 增大窗口尺寸
        self.root.resizable(False, False)
        try:
            self.root.iconbitmap('logo.ico')  # 使用相对路径
            # 或者使用绝对路径
            # self.root.iconbitmap(r'C:\path\to\app.ico')
        except:
            pass  # 如果图标加载失败则忽略

        # 自定义字体
        self.big_font = font.Font(family='Microsoft YaHei', size=24, weight='bold')
        self.medium_font = font.Font(family='Microsoft YaHei', size=14)
        self.clock_font = font.Font(family='Microsoft YaHei', size=18, weight='bold')
        self.do_font = font.Font(family='Microsoft YaHei', size=12, weight='bold')

        self.setup_ui()
        self.active = False
        self.reminder_thread = None
        self.reminder_acknowledged = False
        self.next_reminder_time = None
        self.countdown_interval = 60  # 默认60分钟

        # 启动时钟更新
        self.update_clock()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def setup_ui(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)


        # 标题
        title_label = tk.Label(main_frame,
                               text="休息提醒设置",
                               font=('Microsoft YaHei', 26, 'bold'),
                               fg='#2c3e50')
        title_label.pack(pady=(0, 5))

        # 日期时间显示框架
        datetime_frame = ttk.Frame(main_frame)
        datetime_frame.pack(fill=tk.X, pady=1)

        # 日期显示 (年月日)
        self.date_var = tk.StringVar()
        date_label = tk.Label(datetime_frame,
                              textvariable=self.date_var,
                              font=self.clock_font,
                              fg='#c0392b')
        date_label.pack(side=tk.TOP,  pady=1)

        # 当前时间显示 (时间 + 星期)
        self.current_time_var = tk.StringVar()
        time_label = tk.Label(datetime_frame,
                              textvariable=self.current_time_var,
                              font=self.clock_font,
                              fg='#c0392b')
        time_label.pack(side=tk.TOP, pady=1)
        # 时间设置框架
        time_frame = ttk.Frame(main_frame)
        time_frame.pack(fill=tk.X, pady=5)

        tk.Label(time_frame,
                 text="开始时间:",
                 font=('Microsoft YaHei', 11)).grid(row=0, column=0, padx=5, sticky='e')
        self.start_entry = ttk.Entry(time_frame, font=('Microsoft YaHei', 11), width=8)
        self.start_entry.grid(row=0, column=1, padx=5, sticky='w')
        self.start_entry.insert(0, "08:00")

        tk.Label(time_frame,
                 text="结束时间:",
                 font=('Microsoft YaHei', 11)).grid(row=0, column=2, padx=5, sticky='e')
        self.end_entry = ttk.Entry(time_frame, font=('Microsoft YaHei', 11), width=8)
        self.end_entry.grid(row=0, column=3, padx=5, sticky='w')
        self.end_entry.insert(0, "17:00")

        # 间隔设置
        interval_frame = ttk.Frame(main_frame)
        interval_frame.pack(fill=tk.X, pady=10)

        tk.Label(interval_frame,
                 text="提醒间隔:",
                 font=('Microsoft YaHei', 11)).grid(row=0, column=0, padx=5, sticky='e')
        self.interval_entry = ttk.Entry(interval_frame, font=('Microsoft YaHei', 11), width=5)
        self.interval_entry.grid(row=0, column=1, padx=5, sticky='w')
        self.interval_entry.insert(0, "60")
        tk.Label(interval_frame,
                 text="分钟",
                 font=('Microsoft YaHei', 11)).grid(row=0, column=2, padx=5, sticky='w')
        # 下次提醒倒计时
        self.countdown_var = tk.StringVar()
        self.countdown_var.set("提醒倒计时: --:--:--")
        countdown_label = tk.Label(interval_frame,
                                   textvariable=self.countdown_var,
                                   font=self.do_font,
                                   fg='#abb2b9')
        # countdown_label.pack(side=tk.RIGHT)
        countdown_label.grid(row=0, column=4, padx=5, sticky='e')
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20)

        self.start_btn = tk.Button(button_frame,
                                   text="开始提醒",
                                   font=('Microsoft YaHei', 12),
                                   bg='#27ae60', fg='white',
                                   activebackground='#2ecc71', activeforeground='white',
                                   relief='flat', padx=20,
                                   command=self.start_reminder)
        self.start_btn.pack(side=tk.LEFT, padx=10)

        self.stop_btn = tk.Button(button_frame,
                                  text="停止提醒",
                                  font=('Microsoft YaHei', 12),
                                  bg='#e67e22', fg='white',
                                  activebackground='#c0392b', activeforeground='white',
                                  relief='flat', padx=20,
                                  command=self.stop_reminder,
                                  state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=10)

        # 状态显示
        self.status_var = tk.StringVar()
        self.status_var.set("当前状态: 等待开始")
        status_label = tk.Label(main_frame,
                                textvariable=self.status_var,
                                font=('Microsoft YaHei', 11),
                                fg='#3498db')
        status_label.pack(pady=10)

        # 版权信息
        tk.Label(main_frame,
                 text="© 2025 RestAlert健康工作提醒系统 Junyong Zhao",
                 font=('Microsoft YaHei', 9),
                 fg='#7f8c8d').pack(side=tk.BOTTOM)

    def update_clock(self):
        """更新当前时间和倒计时显示"""
        now = datetime.now()
        # 更新时间显示 (时间 + 星期)
        weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        weekday = weekdays[now.weekday()]
        # 更新日期显示 (年月日)
        self.date_var.set(f"{now.year}年{now.month}月{now.day}日 {weekday} ")


        # weekday = now.strftime("%A")  # 获取完整的星期名称 (中文)
        self.current_time_var.set(f"{now.strftime('%H:%M:%S')}")
        # self.current_time_var.set(f"{now.strftime('%H:%M:%S')}")

        if self.next_reminder_time:
            remaining = self.next_reminder_time - now
            if remaining.total_seconds() > 0:
                hours, remainder = divmod(remaining.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                self.countdown_var.set(f"下次提醒: {hours:02d}:{minutes:02d}:{seconds:02d}")
            else:
                self.countdown_var.set("即将提醒...")

        self.root.after(1000, self.update_clock)  # 每秒更新一次

    def validate_time(self, time_str):
        try:
            datetime.strptime(time_str, "%H:%M")
            return True
        except ValueError:
            return False

    def start_reminder(self):
        start_time = self.start_entry.get()
        end_time = self.end_entry.get()
        interval = self.interval_entry.get()

        if not (self.validate_time(start_time) and self.validate_time(end_time)):
            messagebox.showerror("错误", "请输入正确的时间格式 (HH:MM)")
            return

        try:
            interval = int(interval)
            if interval <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("错误", "请输入有效的分钟数(大于0)")
            return

        self.start_time = datetime.strptime(start_time, "%H:%M").time()
        self.end_time = datetime.strptime(end_time, "%H:%M").time()
        self.countdown_interval = interval
        self.interval = interval * 60  # 转换为秒

        self.active = True
        self.reminder_acknowledged = False
        self.status_var.set(f"状态: 运行中 ({start_time} 至 {end_time}, 每 {interval} 分钟提醒)")

        # 计算下次提醒时间
        self.calculate_next_reminder()

        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)

        if not self.reminder_thread or not self.reminder_thread.is_alive():
            self.reminder_thread = threading.Thread(target=self.run_reminders, daemon=True)
            self.reminder_thread.start()

    def calculate_next_reminder(self):
        """计算下次提醒时间"""
        now = datetime.now()
        next_time = now + timedelta(minutes=self.countdown_interval)
        self.next_reminder_time = next_time

    def stop_reminder(self):
        self.active = False
        self.status_var.set("状态: 已停止")
        self.next_reminder_time = None
        self.countdown_var.set("提醒倒计时: --:--:--")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

    def run_reminders(self):
        while self.active:
            now = datetime.now().time()
            start_dt = datetime.combine(datetime.today(), self.start_time)
            end_dt = datetime.combine(datetime.today(), self.end_time)

            if start_dt.time() <= now <= end_dt.time():
                self.root.after(0, self.show_reminder)

                # 等待用户确认
                while self.active and not self.reminder_acknowledged:
                    time.sleep(0.1)

                # 重置标志并等待下一个间隔
                self.reminder_acknowledged = False
                self.calculate_next_reminder()  # 重新计算下次提醒时间
                time.sleep(self.interval)
            else:
                # 不在提醒时段内，每秒检查一次
                time.sleep(1)

    def show_reminder(self):
        reminder_win = tk.Toplevel(self.root)
        reminder_win.title("⚠️ 休息提醒 ⚠️")
        reminder_win.geometry("600x400")
        reminder_win.resizable(False, False)

        # 使提醒窗口保持在最前
        reminder_win.attributes('-topmost', True)

        # 主内容
        content_frame = tk.Frame(reminder_win, bg='#f8f9fa')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 醒目标题
        title_label = tk.Label(content_frame,
                               text="休息时间到！",
                               font=self.big_font,
                               bg='#f8f9fa',
                               fg='#e74c3c')
        title_label.pack(pady=(20, 10))

        # 提醒内容
        message_label = tk.Label(content_frame,
                                 text="您已经连续工作了一段时间\n\n请起身活动5-10分钟\n\n适当休息可以提高工作效率",
                                 font=self.medium_font,
                                 bg='#f8f9fa',
                                 fg='#2c3e50')
        message_label.pack(pady=10)

        # 按钮框架
        btn_frame = tk.Frame(content_frame, bg='#f8f9fa')
        btn_frame.pack(pady=10)

        # 增强的确定按钮
        confirm_btn = tk.Button(btn_frame,
                                text="我确定，我要休息！)",
                                font=('Microsoft YaHei', 12, 'bold'),
                                bg='#3498db',
                                fg='white',
                                activebackground='#2980b9',
                                activeforeground='white',
                                relief='flat',
                                padx=30,
                                pady=5,
                                command=lambda: self.on_reminder_confirm(reminder_win))
        confirm_btn.pack()

        # 居中显示
        self.center_window(reminder_win)

        # 禁用主窗口
        self.root.attributes('-disabled', True)
        reminder_win.protocol("WM_DELETE_WINDOW", lambda: None)  # 禁用关闭按钮

        # 绑定回车键到确定按钮
        reminder_win.bind('<Return>', lambda e: confirm_btn.invoke())
        confirm_btn.focus_set()

    def center_window(self, window):
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f'+{x}+{y}')

    def on_reminder_confirm(self, window):
        self.reminder_acknowledged = True
        self.root.attributes('-disabled', False)
        window.destroy()

    def on_closing(self):
        if messagebox.askokcancel("退出", "确定要退出程序吗？\n当前提醒将会停止"):
            self.active = False
            self.root.destroy()
            sys.exit(0)


if __name__ == "__main__":
    app = ReminderApp()