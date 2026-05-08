from tkinter import ttk
from tksheet import Sheet
import tkinter as tk


class DeclareFormSheet(ttk.Frame):
    def __init__(self, master, headers=[], records=[], metadata_headers=[], on_edit_callback=None):
        super().__init__(master)

        self.records = records or []
        self.metadata_headers = metadata_headers
        self.master = master
    
        self.data = []
        self.modified_data_idx = []
        self.headers = headers
        self.is_modified = False
        self._column_vars = {}
        self._init_column_menu()
        self._build_sheet()
        

    def _build_data(self, data):
        if not data:
            self.data = []
            return

        attrs = [h for h in data[0].keys()]
        
        self.data = [
            [record[h] for h in attrs]
            for record in data
        ]

    def _build_sheet(self):

        self._build_data(self.records)
        self.sheet = Sheet(
            self,
            headers=self.headers,
            data=self.data,
            theme="light blue",
        )
        
        self._hide_columns()
        
        self.sheet.enable_bindings((
            "single_select",
            "drag_select",
            "row_select",
            "column_select",
            "edit_cell",
            "copy",
            "cut",
            "paste",
            "delete",
            "undo",
            "redo",
            "arrowkeys",
            "right_click_popup_menu",
            "rc_select",
            "select_all"
        ))

        self.sheet.extra_bindings("end_edit_cell", self._on_cell_edited)
        self.sheet.bind("end_insert_row", self._on_cell_inserted)
        self.sheet.bind("end_delete_row", self._on_cell_deleted)
        self.sheet.pack(fill="both", expand=True)


    def _hide_columns(self, hide_columns=[]):
        hide_columns = self.metadata_headers + hide_columns
        headers = self.sheet.headers()
        cols_to_hide = [
            i for i, h in enumerate(headers)
            if h in hide_columns
        ]
        print("Hiding columns:", cols_to_hide)
        self.sheet.hide_columns(cols_to_hide)

    def _init_column_menu(self) -> None:
        topbar = ttk.Frame(self)
        topbar.pack(side="top", fill="both")

        self._cols_btn = ttk.Menubutton(topbar, text="Columns")
        self._cols_btn.pack(side="left", padx=6, pady=4)
        self._cols_menu = tk.Menu(self._cols_btn, tearoff=False)
        self._cols_btn.configure(menu=self._cols_menu)

        self._cols_menu.delete(0, "end")

        # Global show/hide (NVL is always visible)
        self._cols_menu.add_command(label="<Hiện toàn bộ!!!>", command=self._show_all_columns)
        self._cols_menu.add_separator()
        for label in self.headers:
            if label == 'NVL' or label == 'Bill' or label in self.metadata_headers:
                continue
            if label == "Invoice":
                self._cols_menu.add_separator()
                # self._cols_btn.state(["!disabled"])
                self._cols_menu.add_command(label="Ẩn/Hiện các cột chi tiết lô", command=self._toggle_detail_columns)
                self._cols_menu.add_separator()
                continue

            var = tk.BooleanVar(value=True)
            self._column_vars[label] = var
            self._cols_menu.add_checkbutton(
                label=f"Ẩn: {label}",
                variable=var,
                command=lambda l=label: self._toggle_column(l),
            )    

            if label == "TMS":
                self._cols_menu.add_separator()
                self._cols_menu.add_command(label="Ẩn/Hiện các cột thời gian", command=self._toggle_time_columns)
                self._cols_menu.add_separator()  

    def _toggle_column(self, label=None):
        headers = self.sheet.headers()

        # Show all columns first
        self.sheet.show_columns(columns=list(range(len(headers))))

        hide_cols = []

        for col_label, var in self._column_vars.items():
            if col_label not in headers:
                continue

            if not var.get():   # False = hide
                hide_cols.append(headers.index(col_label))

        # Hide selected columns
        if hide_cols:
            self.sheet.hide_columns(columns=hide_cols)

        # Keep metadata columns hidden
        self._hide_columns()

    def set_sheet_data(self, data):
        self._build_data(data)
        # print ("Updating sheet with data:", self.data)
        self.sheet.set_sheet_data(self.data, reset_col_positions=True, reset_row_positions=True)
        column_index = 6  # replace with your target column index
        for row in range(len(self.data)):
            # print(self.data[row][column_index])
            self.sheet.create_dropdown(
                r=row,
                c=column_index,   # replace with your target column index
                values=["PENDING", "DONE"],
                set_value=self.data[row][column_index] if self.data[row][column_index] else "PENDING"
            )
        self.sheet.set_all_column_widths()    

    def _show_all_columns(self):
        """
        Show every column except metadata columns.
        """
        self.sheet.show_columns(columns=list(range(len(self.headers))))

        # Re-hide metadata columns
        if self.metadata_headers:
            self._hide_columns()


    def _toggle_detail_columns(self):
        """
        Hide detail columns between Invoice and TMS
        and update _column_vars to False.
        """
        headers = self.sheet.headers()

        try:
            start = headers.index("Loại hình")
            end = headers.index("TMS") + 1
        except ValueError:
            return

        for col_index in range(start, end):
            label = headers[col_index]
            # Update checkbox state
            if label in self._column_vars:
                self._column_vars[label].set(not self._column_vars[label].get())  # Toggle state

        self._toggle_column(None)  # Update column visibility based on _column_vars



    def _toggle_time_columns(self):
        """
        Show time columns after TMS until Form code.
        """
        headers = self.sheet.headers()

        try:
            start = headers.index("Giờ nhận Mail")
            end = headers.index("Giờ mail thông quan") + 1
        except ValueError:
            print("Error: 'TMS' or 'Form code' column not found in headers.")
            return

        for col_index in range(start, end):
            label = headers[col_index]
            # Update checkbox state
            if label in self._column_vars:
                self._column_vars[label].set(not self._column_vars[label].get())  # Toggle state

        self._toggle_column(None)  # Update column visibility based on _column_vars

    def _on_cell_inserted(self, event):
        self.modified_data_idx.append(event.row)
        self.is_modified = True

    def _on_cell_deleted(self, event):
        self.modified_data_idx.remove(event.row)
        self.is_modified = True

    def _on_cell_edited(self, event):
        row = event.row
        row_data = self.sheet.get_row_data(row)
        self.modified_data_idx.append(row_data[0])
        self.is_modified = True

    def get_sheet_data(self):
        return self.sheet.get_sheet_data()

    def refresh(self, records):
        self.records = records
        self._build_data()

        self.sheet.headers(self.headers)
        self.sheet.set_sheet_data(self.data)

    def get_data(self):
        return self.sheet.get_sheet_data()

    def get_headers(self):
        return self.headers