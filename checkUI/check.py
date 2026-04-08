import tkinter as tk
from tkinter import scrolledtext, messagebox
from pywinauto import Application
import sys
import threading


class TextRedirector:
    def __init__(self, widget):
        self.widget = widget

    def write(self, text):
        self.widget.after(0, self._append, text)

    def _append(self, text):
        self.widget.insert("end", text)
        self.widget.see("end")

    def flush(self):
        pass


def load_controls():
    try:
        app_name = entry.get().strip()
        if not app_name:
            raise Exception("Please enter app name")

        print(f"Connecting to: {app_name}")
        app = Application(backend="uia").connect(title_re=f"(?i).*{app_name}.*")
        dlg = app.top_window()

        print("Window found:", dlg)
        print("Printing controls...\n")

        dlg.print_control_identifiers()

        print("\nDone.")

    except Exception as e:
        print("ERROR:", e)


def start_load():
    threading.Thread(target=load_controls, daemon=True).start()


# -------------------------------
# UI
# -------------------------------
root = tk.Tk()
root.title("UI Inspector")
root.geometry("900x600")

# input frame
frame = tk.Frame(root)
frame.pack(pady=5)

tk.Label(frame, text="App name:").pack(side="left")

entry = tk.Entry(frame, width=30)
entry.pack(side="left", padx=5)
entry.insert(0, "ThaiSon")

btn = tk.Button(root, text="Load Controls", command=start_load)
btn.pack(pady=10)

text_box = scrolledtext.ScrolledText(root, wrap=tk.WORD)
text_box.pack(expand=True, fill="both", padx=10, pady=10)

# redirect console to UI
sys.stdout = TextRedirector(text_box)
sys.stderr = TextRedirector(text_box)

root.mainloop()