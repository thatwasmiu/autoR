import tkinter as tk

def option1_action():
    print("Option 1 selected!")

def option2_action():
    print("Option 2 selected!")

def option3_action():
    print("Option 3 selected!")

def option4_action():
    print("Option 4 selected!")

def ask_four_options(title, message, actions):
    """
    Show a dialog with 4 buttons, each calling a specific function.
    actions: dict mapping button text -> function
    """
    # Create hidden root
    root = tk.Tk()
    root.withdraw()

    # Create top-level dialog
    dialog = tk.Toplevel(root)
    dialog.title(title)
    dialog.resizable(False, False)
    dialog.grab_set()  # modal
    dialog.focus_force()

    # Message label
    tk.Label(dialog, text=message, padx=20, pady=10).pack()

    # Buttons frame
    frame = tk.Frame(dialog, pady=10)
    frame.pack()

    for btn_text, func in actions.items():
        tk.Button(frame, text=btn_text, width=12, command=lambda f=func, d=dialog: [f(), d.destroy()]).pack(side="left", padx=5)

    # Center dialog
    dialog.update_idletasks()
    w, h = dialog.winfo_width(), dialog.winfo_height()
    ws, hs = dialog.winfo_screenwidth(), dialog.winfo_screenheight()
    x, y = (ws-w)//2, (hs-h)//2
    dialog.geometry(f"{w}x{h}+{x}+{y}")

    # Wait until user clicks
    root.wait_window(dialog)
    root.destroy()

# Example usage
ask_four_options(
    "Select an Action",
    "Choose what you want to do:",
    {
        "Option 1": option1_action,
        "Option 2": option2_action,
        "Option 3": option3_action,
        "Option 4": option4_action,
    }
)