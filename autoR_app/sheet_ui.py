from tkinter import ttk
from tksheet import Sheet


class DeclareFormSheet(ttk.Frame):
    def __init__(self, master, headers=[], records=None, skip_headers=None, on_edit_callback=None):
        super().__init__(master)

        self.records = records or []
        self.skip_headers = set(skip_headers or [])

        self.headers = headers
        self.data = []

        self._build_data(self.records)
        self._build_sheet()

    def _build_data(self, data):
        if not data:
            self.data = []
            return

        attrs = [
            h for h in data[0].keys()
            if h not in self.skip_headers
        ]

        self.data = [
            [record[h] for h in attrs]
            for record in data
        ]

    def _build_sheet(self):
        self.sheet = Sheet(
            self,
            headers=self.headers,
            data=self.data,
            theme="light blue",
        )

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

        self.sheet.pack(fill="both", expand=True)

    def set_sheet_data(self, data):
        self._build_data(data)
        # print ("Updating sheet with data:", self.data)
        self.sheet.set_sheet_data(self.data, reset_col_positions=True, reset_row_positions=True)
        column_index = 11  # replace with your target column index
        for row in range(len(self.data)):
            self.sheet.create_dropdown(
                r=row,
                c=column_index,   # replace with your target column index
                values=["PENDING", "DONE"],
                # set_value=self.data[row][column_index] if self.data[row][column_index] else "PENDING"
            )


    def _on_cell_edited(self, event):
        row = event.row
        column = event.column
        value = event.value

        # Trigger parent callback
        if self.on_edit_callback:
            self.on_edit_callback(
                row=row,
                column=column,
                value=value,
                headers=self.headers,
                records=self.records,
            )

    def refresh(self, records):
        self.records = records
        self._build_data()

        self.sheet.headers(self.headers)
        self.sheet.set_sheet_data(self.data)

    def get_data(self):
        return self.sheet.get_sheet_data()

    def get_headers(self):
        return self.headers