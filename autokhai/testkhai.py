from pywinauto import Application

app = Application(backend="uia").connect(title_re=".*Zalo.*")
dlg = app.top_window()


listbox = dlg.descendants(control_type="List")[0]
item = listbox.children(control_type="ListItem")[1]

rect = item.rectangle()
item.click_input(coords=(rect.width()//2, rect.height()//2))


# .click()          # click button
# .double_click()   # double click
# .type_keys()      # send keyboard
# .set_text()       # set text
# .get_value()      # read text
# .select()         # select item