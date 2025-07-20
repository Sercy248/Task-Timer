# Bản merge
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import time
import csv
from datetime import datetime, timedelta
import os
from collections import defaultdict

DATA_FILE = 'task_log.csv'

# Save a session log, Hiển thị All Tasks (session log tốt hơn)
def save_session(task, comment, duration_sec):
    date = datetime.now().strftime("%Y-%m-%d")
    time_str = datetime.now().strftime("%H:%M:%S")
    with open(DATA_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([date, time_str, task, comment, duration_sec])



# Read all task history
def read_task_history():
    history = defaultdict(list)
    if not os.path.exists(DATA_FILE):
        return history
    with open(DATA_FILE, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) != 5:
                continue
            date, time_str, task, comment, duration = row
            try:
                duration = int(duration)
                history[task].append((date, time_str, comment, duration))
            except:
                continue
    return history

# Get recent tasks for suggestion
def get_recent_tasks(n=3):
    history = read_task_history()
    sorted_tasks = sorted(history.items(), key=lambda item: max(
        [datetime.strptime(d + " " + t, "%Y-%m-%d %H:%M:%S") for d, t, _, _ in item[1]]
    ), reverse=True)
    return sorted_tasks[:n]

# Rename a task in the CSV file
def rename_task_in_file(old_name, new_name):
    if not os.path.exists(DATA_FILE):
        return
    rows = []
    with open(DATA_FILE, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) == 5 and row[2] == old_name:
                row[2] = new_name
            rows.append(row)
    with open(DATA_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(rows)

# Session Log window (Group by Task)
class AllTasksWindow:
    def __init__(self, parent):
        self.filter_var = tk.StringVar()
        self.filter_var.trace_add("write", lambda *args: self.update_tree())

        self.filter_note_var = tk.BooleanVar()
        self.filter_note_var.trace_add("write", lambda *args: self.update_tree())
        self.window = tk.Toplevel(parent)
        self.window.title("All Tasks")
        self.history = read_task_history()
        self.original_history = self.history.copy()

        self.tree = ttk.Treeview(self.window, columns=("Date", "Start Time", "End Time", "Duration (min)", "Comment", "Note"), show="tree headings")
        for col in ("Date", "Start Time", "End Time", "Duration (min)", "Comment", "Note"):
            self.tree.heading(col, text=col)
            self.tree.column(col, stretch=True)
        self.tree.pack(fill="both", expand=True)

        h_scrollbar = ttk.Scrollbar(self.window, orient="horizontal", command=self.tree.xview)
        h_scrollbar.pack(side="bottom", fill="x")
        self.tree.configure(xscrollcommand=h_scrollbar.set)

        # self.tree.tag_configure("highlight", background="yellow")  # Highlighting disabled

        self.populate_tree()

        tk.Label(self.window, text="Filter by task:").pack(pady=(5, 0))
        tk.Entry(self.window, textvariable=self.filter_var).pack(padx=10, fill="x")
        tk.Checkbutton(self.window, text="Only show non-continuous sessions", variable=self.filter_note_var).pack(pady=2)

        self.rename_btn = tk.Button(self.window, text="Rename Task", command=self.rename_task)
        self.rename_btn.pack(pady=5)

    def populate_tree(self):
        self.tree.delete(*self.tree.get_children())
        for task, sessions in self.history.items():
            total_sec = sum([s[3] for s in sessions])
            parent_id = self.tree.insert("", "end", text=f"{task} ({total_sec//60} min)", open=False)
            for date, time_str, comment, duration in sessions:
                end_dt = datetime.strptime(f"{date} {time_str}", "%Y-%m-%d %H:%M:%S") + timedelta(seconds=duration)
                end_time = end_dt.strftime("%H:%M:%S")
                actual_duration = int((end_dt - datetime.strptime(time_str, "%H:%M:%S")).total_seconds()) // 60
                note = "non-continuous session" if actual_duration != duration // 60 else ""
                tag = ""  # No highlighting
                self.tree.insert(parent_id, "end", text="", values=(date, time_str, end_time, duration // 60, comment, note), tags=(tag,))

    def update_tree(self):
        filter_text = self.filter_var.get().lower()
        note_filter = self.filter_note_var.get()

        if not filter_text:
            filtered = self.original_history.copy()
        else:
            filtered = {task: sess for task, sess in self.original_history.items() if filter_text in task.lower()}

        if note_filter:
            for task in list(filtered.keys()):
                filtered[task] = [s for s in filtered[task] if (datetime.strptime(s[1], "%H:%M:%S") + timedelta(seconds=s[3])).strftime("%H:%M:%S") != (datetime.strptime(s[1], "%H:%M:%S") + timedelta(minutes=s[3]//60)).strftime("%H:%M:%S")]
                if not filtered[task]:
                    del filtered[task]

        self.history = filtered
        self.populate_tree()

    def rename_task(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a task to rename.")
            return
        task_text = self.tree.item(selected[0], "text")
        old_name = task_text.split(" (")[0]
        new_name = simpledialog.askstring("Rename Task", f"Enter new name for '{old_name}':")
        if new_name:
            rename_task_in_file(old_name, new_name)
            messagebox.showinfo("Renamed", f"'{old_name}' renamed to '{new_name}'. Please reopen the window.")
            self.window.destroy()

# Main Task Timer App
class TaskTimerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Task Timer v5")
        self.task_var = tk.StringVar()
        self.comment_var = tk.StringVar()
        self.start_time = None
        self.running = False
        self.paused = False
        self.elapsed_before_pause = 0
        self.selected_task = None

		# Prevent closing window if task is running
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Always on top
        self.root.wm_attributes("-topmost", 1)

        # Task selection area
        tk.Label(root, text="Choose recent task or enter new one:", font=("Arial", 12, "bold")).pack()
        self.task_frame = tk.Frame(root)
        self.task_frame.pack(pady=5)
        self.task_buttons = []

        for task_name, sessions in get_recent_tasks():
            total_time = sum([s[3] for s in sessions])
            last_comment = sessions[-1][2] if sessions else ""
            btn = tk.Button(self.task_frame, text=f"{task_name:<20} {total_time//60} min",
                            command=lambda name=task_name: self.select_task(name),
                            anchor='w', width=40)
            btn.pack(anchor="w", padx=10)
            label = tk.Label(self.task_frame, text=f"  ↪ {last_comment}", fg="gray", font=("Arial", 9), anchor="w")
            label.pack(anchor="w", padx=20)
            self.task_buttons.append(btn)

        tk.Label(root, text="Or enter new task name:").pack()
        self.task_entry = tk.Entry(root, textvariable=self.task_var)
        self.task_entry.pack()
        self.task_entry.bind("<KeyRelease>", lambda _: self.set_selected_task())

        tk.Label(root, text="Comment:").pack()
        tk.Entry(root, textvariable=self.comment_var).pack()

        self.timer_label = tk.Label(root, text="Timer: 00:00:00", font=("Courier", 16))
        self.timer_label.pack(pady=10)

        btn_row = tk.Frame(root)
        btn_row.pack(pady=5)
        self.start_button = tk.Button(btn_row, text="Start", command=self.start_timer, state="disabled")
        self.start_button.pack(side="left", padx=5)

        self.pause_button = tk.Button(btn_row, text="Pause", command=self.pause_timer)
        self.pause_button.pack(side="left", padx=5)
        
        self.stop_button = tk.Button(btn_row, text="Stop", command=self.stop_timer)
        self.stop_button.pack(side="left", padx=5)
   
        # Bottom buttons: All tasks and Minimize
        bottom_frame = tk.Frame(root)
        bottom_frame.pack(fill="x", side="bottom")
        self.all_tasks_button = tk.Button(root, text="All tasks", command=self.show_all_tasks)
        self.all_tasks_button.pack(side="left", padx=5, pady=5)
        self.minimize_button = tk.Button(bottom_frame, text="Minimize", command=self.minimize_view)
        self.minimize_button.pack(side="right", padx=5, pady=5)

    def set_selected_task(self):
        self.selected_task = self.task_var.get().strip()
        self.update_start_button()

    def update_start_button(self):
        task_filled = self.task_var.get().strip() != ""
        self.start_button.config(state="normal" if task_filled else "disabled")
        self.pause_button.config(state="normal" if task_filled else "disabled")

    def select_task(self, name):
        self.selected_task = name
        self.task_var.set(name)
        self.update_start_button()

    def update_timer(self):
        if self.running and not self.paused:
            elapsed = int(time.time() - self.start_time)
            hrs = elapsed // 3600
            mins = (elapsed % 3600) // 60
            secs = elapsed % 60
            self.timer_label.config(text=f"Timer: {hrs:02}:{mins:02}:{secs:02}")
            self.root.after(1000, self.update_timer)

    def start_timer(self):
        if not self.selected_task:
            messagebox.showwarning("Warning", "Please select or enter a task first.")
            return
        self.start_time = time.time()
        self.running = True
        self.paused = False
            
    def pause_timer(self):
        if not self.running:
            messagebox.showwarning("Warning", "Timer is not running.")
            return
        if not self.paused:
            self.paused = True
            self.elapsed_before_pause = int(time.time() - self.start_time)
            self.pause_button.config(text="Resume")
        else:
            self.paused = False
            self.start_time = time.time() - self.elapsed_before_pause
            self.pause_button.config(text="Pause")
            # self.update_timer()
    def stop_timer(self):
        if not self.running:
            messagebox.showwarning("Warning", "Timer not running.")
            return
        self.running = False
        duration = int(time.time() - self.start_time)
        task = self.selected_task
        comment = self.comment_var.get().strip()
        save_session(task, comment, duration)
        self.timer_label.config(text=f"Last session: {duration} sec")
        messagebox.showinfo("Saved", f"Task '{task}' saved with {duration} sec.")

    def show_all_tasks(self):
        AllTasksWindow(self.root)

    def minimize_view(self):
        self.root.geometry("360x60")
        self.root.overrideredirect(True)
        self.root.configure(highlightbackground="cyan", highlightthickness=3)
        self.root.attributes("-topmost", True)
        
        # Cho phép kéo cửa sổ thu nhỏ
        def start_move(event):
            self._x = event.x
            self._y = event.y

        def do_move(event):
            x = self.root.winfo_pointerx() - self._x
            y = self.root.winfo_pointery() - self._y
            self.root.geometry(f"+{x}+{y}")

        self.root.bind('<Button-1>', start_move)
        self.root.bind('<B1-Motion>', do_move)

        for widget in self.root.winfo_children():
            widget.pack_forget()

        info_frame = tk.Frame(self.root)
        info_frame.pack()
        tk.Label(info_frame, text=self.selected_task, font=("Arial", 10, "bold"), anchor="w").pack(side="left", padx=5)
        self.timer_label = tk.Label(info_frame, text="Timer: 00:00:00", font=("Courier", 10))
        self.timer_label.pack(side="right", padx=5)

        btn_frame = tk.Frame(self.root)
        btn_frame.pack()
        tk.Button(btn_frame, text="Start", command=self.start_timer).pack(side="left", padx=2)
        tk.Button(btn_frame, text="Pause", command=self.pause_timer).pack(side="left", padx=2)
        tk.Button(btn_frame, text="Stop", command=self.stop_timer).pack(side="left", padx=2)
        tk.Button(btn_frame, text="Expand", command=self.expand_view).pack(side="left", padx=2)

    def expand_view(self):
        self.root.overrideredirect(False)
        self.root.geometry("600x400") # Phóng to như khi khởi động app
        
            # Khôi phục toàn bộ giao diện không mất session đang chạy
        for widget in self.root.winfo_children():
            widget.destroy()

        # Lưu trạng thái session cũ
        old_state = {
            'selected_task': self.selected_task,
            'comment': self.comment_var.get(),
            'running': self.running,
            'paused': self.paused,
            'start_time': self.start_time
        }

            
        self.__init__(self.root)

        # Phục hồi session đang chạy (nếu có)
        self.selected_task = old_state['selected_task']
        self.task_var.set(old_state['selected_task'])
        self.comment_var.set(old_state['comment'])
        self.running = old_state['running']
        self.paused = old_state['paused']
        self.start_time = old_state['start_time']

        if self.running:
            self.update_timer()
            self.timer_label.config(text="Resumed...")

    def select_task_and_enable(self, name):
        self.selected_task = name
        self.task_var.set(name)
        self.update_start_button()

    def on_close(self):
        if self.running:
            messagebox.showwarning("Stop Timer", "Please stop the timer before closing the app.")
        else:
            self.root.destroy()
        
# Run the app
root = tk.Tk()
app = TaskTimerApp(root)
root.mainloop()


