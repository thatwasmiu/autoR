import tkinter as tk
from tkinter import ttk
from .helpers import get_resource_path


class FilterForm(ttk.LabelFrame):
    def __init__(
        self,
        parent,
        title,
        keyword_options,
        people_options,
        folder_options
    ):
        super().__init__(parent, text=title, padding=10)

        # -------------------------
        # Required Keywords
        # -------------------------
        ttk.Label(self, text="Required Keywords").grid(
            row=0,
            column=0,
            sticky="w"
        )

        self.required_keywords = tk.Listbox(
            self,
            selectmode=tk.MULTIPLE,
            height=6,
            exportselection=False
        )

        for item in keyword_options:
            self.required_keywords.insert(tk.END, item)

        self.required_keywords.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=(0, 10)
        )

        # -------------------------
        # Optional Keywords
        # -------------------------
        ttk.Label(self, text="Optional Keywords (; separated)").grid(
            row=0,
            column=1,
            sticky="w"
        )

        self.optional_keywords = ttk.Entry(self, width=40)

        self.optional_keywords.grid(
            row=1,
            column=1,
            sticky="ew",
            padx=(0, 10)
        )

        # -------------------------
        # People
        # -------------------------
        ttk.Label(self, text="Sender / Receiver / CC").grid(
            row=0,
            column=2,
            sticky="w"
        )

        self.people = tk.Listbox(
            self,
            selectmode=tk.MULTIPLE,
            height=6,
            exportselection=False
        )

        for item in people_options:
            self.people.insert(tk.END, item)

        self.people.grid(
            row=1,
            column=2,
            sticky="nsew",
            padx=(0, 10)
        )

        # -------------------------
        # Folders
        # -------------------------
        ttk.Label(self, text="Folders").grid(
            row=0,
            column=3,
            sticky="w"
        )

        self.folders = tk.Listbox(
            self,
            selectmode=tk.MULTIPLE,
            height=6,
            exportselection=False
        )

        for item in folder_options:
            self.folders.insert(tk.END, item)

        self.folders.grid(
            row=1,
            column=3,
            sticky="nsew"
        )

        self.columnconfigure(1, weight=1)

    def get_data(self):
        required_keywords = [
            self.required_keywords.get(i)
            for i in self.required_keywords.curselection()
        ]

        optional_keywords = [
            x.strip()
            for x in self.optional_keywords.get().split(";")
            if x.strip()
        ]

        people = [
            self.people.get(i)
            for i in self.people.curselection()
        ]

        folders = [
            self.folders.get(i)
            for i in self.folders.curselection()
        ]

        return {
            "required_keywords": required_keywords,
            "optional_keywords": optional_keywords,
            "people": people,
            "folders": folders,
        }


# =========================================================
# Example App
# =========================================================
    
class FilterModal(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.master = master

        self.iconbitmap(get_resource_path("resources/poppo.ico"))
        self.title("Xuất báo cáo!!")
        self.geometry("900x350")
        self.transient(master)   # Keep on top of parent
        self.grab_set()          # Make modal (block parent interaction)

        descriptions = [
            "Find RSA-2103 Jira mails",
            "Find RSA-2129 deployment mails",
            "Find UAT notification mails",
        ]

        keyword_options = [
            "RSA-2103",
            "RSA-2129",
            "UAT",
            "PROD",
            "SIT",
            "Deploy",
        ]

        people_options = [
            "jira@vetc.com.vn",
            "devops@vetc.com.vn",
            "boss@vetc.com.vn",
        ]

        folder_options = [
            "Inbox",
            "Archive",
            "Projects",
            "Important",
        ]

        forms = []

        container = ttk.Frame(self, padding=10)
        container.pack(fill="both", expand=True)

        for desc in descriptions:
            form = FilterForm(
                container,
                title=desc,
                keyword_options=keyword_options,
                people_options=people_options,
                folder_options=folder_options
            )

            form.pack(
                fill="x",
                pady=10
            )

            forms.append(form)


        def submit():
            filters = []

            for form in forms:
                filters.append(form.get_data())

            print("=" * 50)

            for idx, f in enumerate(filters):
                print(f"Filter {idx + 1}")
                print(f)


        submit_btn = ttk.Button(
            self,
            text="Submit",
            command=submit
        )

        submit_btn.pack(pady=10)

        self.mainloop()