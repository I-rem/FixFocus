import tkinter as tk
from tkinter import messagebox
import subprocess
import os

def run_app():
    try:
        subprocess.run(["python", "student_focus.py"])
    except Exception as e:
        messagebox.showerror("Error", f"Failed to run App:\n{str(e)}")

def open_log():
    if os.path.exists("distraction_log.csv"):
        os.startfile("distraction_log.csv")
    else:
        messagebox.showinfo("Info", "No log file found yet.")

app = tk.Tk()
app.title("FixFocus")
app.geometry("350x200")
app.resizable(False, False)

tk.Label(app, text="🎯 FixFocus - Student Attention Tracker", font=("Arial", 14)).pack(pady=10)

tk.Button(app, text="▶ Start Session", font=("Arial", 12), width=20, command=run_app).pack(pady=10)
tk.Button(app, text="📁 Open Distraction Log", font=("Arial", 12), width=20, command=open_log).pack(pady=5)
tk.Button(app, text="❌ Exit", font=("Arial", 12), width=20, command=app.quit).pack(pady=5)

app.mainloop()

