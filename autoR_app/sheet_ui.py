from tkinter import ttk
from tksheet import Sheet
import tkinter as tk


class DeclareFormSheet(ttk.Frame):
    def __init__(self, master, headers=[], records=[], metadata_headers=[], on_row_action_callback=None):
        super().__init__(master)

        self.records = records or []
        self.metadata_headers = metadata_headers
        self.master = master
        self.on_row_action_callback = on_row_action_callback
        self.data = []
        self.modified_datas = {}
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
            "column_width_resize",
            "row_width_resize",
            # "move_rows",
            "find",
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
            "rc_select",
            "select_all",
            # "right_click_popup_menu"
        ))

        

        self.sheet.bind("end_insert_row", self._on_cell_inserted)
        self.sheet.bind("end_delete_row", self._on_cell_deleted)

        self.sheet.extra_bindings([
            ("end_edit_cell", self._on_cell_edited),          # cell edited
            ("end_paste", self._on_cell_edited),              # paste completed
            ("end_delete_key", self._on_cell_edited),         # delete key
            ("end_cut", self._on_cell_edited),                # cut
            ("end_undo", self._on_cell_edited),               # undo
            ("end_redo", self._on_cell_edited),               # redo
            ("end_insert_rows", self._on_cell_edited),        # rows inserted
            ("end_delete_rows", self._on_cell_edited),        # rows deleted
            ("end_insert_columns", self._on_cell_edited),     # columns inserted
            ("end_delete_columns", self._on_cell_edited),     # columns deleted
            ("end_move_rows", self._on_cell_edited),          # rows moved
            ("end_move_columns", self._on_cell_edited),       # columns moved
        ])

        self.sheet.highlight_columns(
            columns=[12],
            bg="lightblue",   # background color
            fg="black",       # text color
            highlight_header=True
        )
        self.sheet.highlight_columns(
            columns=[6],
            bg="#FFEBEE",   # background color
            fg="black",       # text color
            highlight_header=True
        )
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

        self._delete_btn = ttk.Button(
            topbar,
            text="Xóa dòng đã chọn",
            command=self._delete_selected_rows  # Replace with your delete handler
        )
        self._delete_btn.pack(side="left", padx=6, pady=4)     

        # self._delete_btn = ttk.Button(
        #     topbar,
        #     text="Paste từ value",
        #     command=self._delete_selected_rows  # Replace with your delete handler
        # )
        # self._delete_btn.pack(side="left", padx=6, pady=4)      

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
        pogress_index = 6  # replace with your target column index
        route_type_index = 9
        for row in range(len(self.data)):
            # print(self.data[row][column_index])
            self.sheet.create_dropdown(
                r=row,
                c=pogress_index,   # replace with your target column index
                values=["PENDING", "DONE"],
                set_value=self.data[row][pogress_index] if self.data[row][pogress_index] else "PENDING"
            )
            self.sheet.create_dropdown(
                r=row,
                c=route_type_index,   # replace with your target column index
                values=["Xanh", "Vàng", "Đỏ"],
                set_value=self.data[row][route_type_index] if self.data[row][route_type_index] else ""
            )

        self.sheet.set_all_column_widths()    

    def _show_all_columns(self):
        self.sheet.show_columns(columns=list(range(len(self.headers))))

        # Re-hide metadata columns
        if self.metadata_headers:
            self._hide_columns()


    def _toggle_detail_columns(self):
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
        row_data = self.sheet.get_row_data(event.row)
        self.modified_datas[row_data[0]] = row_data
        self.is_modified = True

    def _on_cell_deleted(self, event):
        row_data = self.sheet.get_row_data(event.row)
        self.modified_datas[row_data[0]] = row_data
        self.is_modified = True

    def _on_cell_edited(self, event):
        # print("Event: ", event.data)
        print("Event name: ", event.eventname)
        # print("Event row: ", event)
        if event.eventname in ("end_paste", "end_ctrl_v"):
            for (row_idx, column_idx), value in event.data.items():
                print("Row:", row_idx)
                print("Column:", column_idx)
                print("New Value:", value)

                # Full row data
                row_data = self.sheet.get_row_data(row_idx)

                # Example save
                self.modified_datas[row_data[0]] = row_data
        elif event.eventname in ("end_ctrl_x", "end_cut"):
            for (row_idx, column_idx), value in event.cells["table"].items():
                # Full row data
                row_data = self.sheet.get_row_data(row_idx)

                # Example save
                self.modified_datas[row_data[0]] = row_data

                # print(f"Saved row {row_idx}: {row_data}")        
        elif event.eventname in ("end_undo"):
           datas = self.sheet.get_sheet_data()
           for data in datas:
            self.modified_datas[data[0]] = data   
        else:
            print("Cell edited at row:", event.row, "column:", event.column, " eventname:", event.eventname)
            row_data = self.sheet.get_row_data(event.row)
            self.modified_datas[row_data[0]] = row_data
        self.is_modified = True    

    def get_sheet_data(self):
        return self.sheet.get_sheet_data()
    
    def get_modified_data(self):
        return self.modified_datas
    
    def _delete_selected_rows(self):
        selected_rows = self.sheet.get_selected_rows()
        if selected_rows:
            datas  = [
                self.sheet.get_row_data(row_index)
                for row_index in selected_rows
            ]
            self.on_row_action_callback("delete", datas)


    def refresh(self, records):
        self.records = records
        self._build_data()

        self.sheet.headers(self.headers)
        self.sheet.set_sheet_data(self.data)

    def get_data(self):
        return self.sheet.get_sheet_data()

    def get_headers(self):
        return self.headers