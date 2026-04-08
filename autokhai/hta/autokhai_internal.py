from pywinauto import Application

app = Application(backend="uia").connect(title_re=".*Zalo.*")
dlg = app.top_window()

box = dlg.child_window(auto_id="richInput", control_type="Group")
box.click_input()
box.type_keys("Hello", with_spaces=True)