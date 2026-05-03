from __future__ import annotations

import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import re
from .daily_invoice import get_data

def open_sync_modal(self) -> None:
        modal = tk.Toplevel(self.master)
        modal.title("Sync from folder")
        modal.geometry("900x260")
        modal.transient(self.master)
        modal.grab_set()

        tk.Label(modal, text="Selected Folder:").pack(pady=6)

        folder_entry = tk.Entry(modal, width=90)
        folder_entry.pack(pady=5)

        def choose_folder() -> None:
            folder = filedialog.askdirectory(parent=modal)
            if folder:
                folder_entry.delete(0, tk.END)
                folder_entry.insert(0, folder)

        tk.Button(modal, text="Browse", command=choose_folder).pack(pady=5)

        status_label = tk.Label(modal, text="Status: Idle", fg="blue")
        status_label.pack(pady=10)

        run_button = tk.Button(modal, text="Sync")
        run_button.pack(pady=10)

        ignore_folders = {"xml", "__pycache__"}

        def folder_sort_key(name: str) -> int:
            m = re.match(r"\d+", name)
            return int(m.group(0)) if m else 10**9

        def task(folder_path: str) -> None:
            print("folder path: ", folder_path)
            datas = []
            try:
                root = Path(folder_path)
                if not root.exists():
                    status_label.config(text="Folder not found", fg="red")
                    return

                folders = [p for p in root.iterdir()
                            if p.is_dir()
                            and not any(ignore.lower() in p.name.lower() for ignore in ignore_folders)]
                folders = sorted(folders, key=lambda p: folder_sort_key(p.name))
                status_label.config(text=f"Found {len(folders)} folders", fg="blue")
                status_label.update_idletasks()

                for i, folder in enumerate(folders):
                    # print(f"Processing folder: {folder}")
                    status_label.config(text=f"Processing ({i+1}/{len(folders)}): {folder.name}", fg="blue")
                    status_label.update_idletasks()

                    data = get_data(folder)
                    datas.append(data)
                self.sync_folder(folder_path, datas)
                # status_label.config(text="✅ Sync done", fg="green")
            except Exception as e:
                status_label.config(text=str(e), fg="red")
            finally:
                # self._resync()
                run_button.config(state="normal")

        def run_tasks(folder_paths: list[str]) -> None:
            """
            Run task processing in background thread.
            """
            try:
                for folder in folder_paths:
                    task(folder)

                status_label.after(
                    0,
                    lambda: status_label.config(
                        text="Sync completed successfully!",
                        fg="green"
                    )
                )

            except Exception as e:
                status_label.after(
                    0,
                    lambda: status_label.config(
                        text=f"Error: {str(e)}",
                        fg="red"
                    )
                )

            finally:
                run_button.after(
                    0,
                    lambda: run_button.config(state="normal")
                )

        def is_data_folder(folder: Path) -> bool:
            """
            Check if folder name matches dd.MM format.
            Example: 01.05, 25.12
            """
            return folder.is_dir() and re.fullmatch(r"\d{2}\.\d{2}", folder.name) is not None

        def start_sync() -> None:
            folder_path = folder_entry.get().strip()

            if not folder_path:
                status_label.config(text="Please select a folder!", fg="red")
                return

            selected_path = Path(folder_path)

            if not selected_path.exists():
                status_label.config(text="Folder not found!", fg="red")
                return

            folder_paths = []

            # Exact data folder selected
            if is_data_folder(selected_path):
                folder_paths.append(str(selected_path))

            # Container folder selected
            elif selected_path.is_dir():
                data_folders = sorted(
                    [p for p in selected_path.iterdir() if is_data_folder(p)],
                    key=lambda p: folder_sort_key(p.name)
                )

                if not data_folders:
                    messagebox.showerror(
                        "No Data Folders Found",
                        "Selected folder does not contain any valid data folders (dd.MM)."
                    )
                    status_label.config(text="No valid data folders found!", fg="red")
                    return

                folder_paths.extend(str(folder) for folder in data_folders)

            else:
                status_label.config(text="Invalid folder selected!", fg="red")
                return

            run_button.config(state="disabled")
            status_label.config(text="Starting sync...", fg="blue")

            # Run in background thread
            threading.Thread(
                target=run_tasks,
                args=(folder_paths,),
                daemon=True
            ).start()

        run_button.config(command=start_sync)