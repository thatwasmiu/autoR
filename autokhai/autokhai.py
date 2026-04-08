from pywinauto import Application

def autokhai():
    app = Application(backend="uia").connect(title_re=".*ES.*")
    dlg = app.top_window()

    btn = dlg.child_window(auto_id="btnFileDinhKem", control_type="Button")
    print(btn.exists())
    btn.click_input()


if __name__ == "__main__":
    autokhai()