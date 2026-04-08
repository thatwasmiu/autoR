from pywinauto import Application
from pywinauto.timings import wait_until_passes
from pywinauto.keyboard import send_keys

app = Application(backend="uia").connect(title_re="Your App")
dlg = app.top_window()

menu_item = dlg.child_window(
    title="Danh sách tờ khai nhập khẩu",
    control_type="MenuItem"
)

# Expand parent menu first (if needed)
menu_item.parent().expand()  # optional, only if parent menu is collapsed

menu_item.click_input()

# 1. click main button
dlg.child_window(title="Delete", control_type="Button").click_input()

# 2. wait for popup
popup = app.window(auto_id="frmKB_GiayPhep", control_type="Window")

popup.wait("exists enabled visible ready", timeout=10)

# 3. click button inside popup
btnFileDinhKem = popup.child_window(auto_id="btnFileDinhKem", control_type="Button")
btnFileDinhKem.click()

# connect to file dialog
# file_dlg = app.window(title_re=".*Open.*|.*Mở.*")
file_dlg = app.window(class_name="#32770")

file_dlg.wait("visible", timeout=10)

# type full file path
send_keys(r"C:\temp\test.pdf")

# press Open
send_keys("{ENTER}") 