import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import time
import csv
from datetime import datetime
import os
from collections import defaultdict

DATA_FILE = 'task_log.csv'

def save_session(task, comment, duration_sec):
    date = datetime.now().strftime("%Y-%m-%d")
    time_str = datetime.now().strftime("%H:%M:%S")
    with open(DATA_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([date, time_str, task, comment, duration_sec])

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

def get_recent_tasks(n=3):
    history = read_task_history()
    sorted_tasks = sorted(history.items(), key=lambda item: max(
        [datetime.strptime(d + " " + t, "%Y-%m-%d %H:%M:%S") for d, t, _, _ in item[1]]
    ), reverse=True)
    return sorted_tasks[:n]

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

class AllTasksWindow:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("All Tasks")
        self.history = read_task_history()

        self.tree = ttk.Treeview(self.window, columns=("Total Time"), show="tree")
        self.tree.pack(fill="both", expand=True)

        for task, sessions in self.history.items():
            total_sec = sum([s[3] for s in sessions])
            parent_id = self.tree.insert("", "end", text=f"{task} ({total_sec//60} min)", open=False)
            for date, time_str, comment, duration in sessions:
                self.tree.insert(parent_id, "end", text=f"{date} {time_str} - {duration//60} min - {comment}")

        self.rename_btn = tk.Button(self.window, text="Rename Task", command=self.rename_task)
        self.rename_btn.pack(pady=5)

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

class TaskTimerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Task Timer v4")

        self.task_var = tk.StringVar()
        self.comment_var = tk.StringVar()
        self.start_time = None
        self.running = False
        self.selected_task = None

        # Recent tasks block
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

        # Manual entry
        tk.Label(root, text="Or enter new task name:").pack()
        self.task_entry = tk.Entry(root, textvariable=self.task_var)
        self.task_entry.pack()
        self.task_entry.bind("<KeyRelease>", lambda _: self.set_selected_task())

        # Comment
        tk.Label(root, text="Comment:").pack()
        tk.Entry(root, textvariable=self.comment_var).pack()

        # Timer
        self.timer_label = tk.Label(root, text="Timer: 00:00:00", font=("Courier", 16))
        self.timer_label.pack(pady=10)

        self.start_button = tk.Button(root, text="Start", command=self.start_timer, state="disabled")
        self.start_button.pack()

        self.stop_button = tk.Button(root, text="Stop", command=self.stop_timer)
        self.stop_button.pack()

        self.all_tasks_button = tk.Button(root, text="All tasks", command=self.show_all_tasks)
        self.all_tasks_button.pack(pady=5)

    def set_selected_task(self):
        self.selected_task = self.task_var.get().strip()
        self.update_start_button()

    def update_start_button(self):
        self.start_button.config(state="normal" if self.selected_task else "disabled")

    def select_task(self, name):
        self.selected_task = name
        self.task_var.set(name)
        self.update_start_button()

    def update_timer(self):
        if self.running:
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
        self.update_timer()

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

# Run the app
root = tk.Tk()
app = TaskTimerApp(root)
root.mainloop()
