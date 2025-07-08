import tkinter as tk
from tkinter import messagebox
import time
import csv
from datetime import datetime
import os

DATA_FILE = 'task_log.csv'

def save_session(task, comment, duration_sec):
    date = datetime.now().strftime("%Y-%m-%d")
    time_str = datetime.now().strftime("%H:%M:%S")
    with open(DATA_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([date, time_str, task, comment, duration_sec])

def summarize_time():
    if not os.path.exists(DATA_FILE):
        return "No records yet."
    summary = {}
    with open(DATA_FILE, newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            date, _, _, _, duration = row
            duration = int(duration)
            summary[date] = summary.get(date, 0) + duration
    result = "Total time by date:\n"
    for date, total_sec in summary.items():
        mins = total_sec // 60
        result += f"{date}: {mins} minutes\n"
    return result

class TaskTimerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Task Timer")

        self.task_var = tk.StringVar()
        self.comment_var = tk.StringVar()
        self.start_time = None

        tk.Label(root, text="Task Name:").pack()
        tk.Entry(root, textvariable=self.task_var).pack()

        tk.Label(root, text="Comment:").pack()
        tk.Entry(root, textvariable=self.comment_var).pack()

        self.timer_label = tk.Label(root, text="Timer: 0 seconds")
        self.timer_label.pack()

        self.start_button = tk.Button(root, text="Start", command=self.start_timer)
        self.start_button.pack()

        self.stop_button = tk.Button(root, text="Stop", command=self.stop_timer)
        self.stop_button.pack()

        self.summary_label = tk.Label(root, text=summarize_time())
        self.summary_label.pack()

    def start_timer(self):
        self.start_time = time.time()
        self.timer_label.config(text="Timer started...")

    def stop_timer(self):
        if not self.start_time:
            messagebox.showwarning("Warning", "Timer not started.")
            return
        duration = int(time.time() - self.start_time)
        task = self.task_var.get()
        comment = self.comment_var.get()
        save_session(task, comment, duration)
        self.start_time = None
        self.timer_label.config(text=f"Session lasted {duration} seconds.")
        self.summary_label.config(text=summarize_time())

root = tk.Tk()
app = TaskTimerApp(root)
root.mainloop()
