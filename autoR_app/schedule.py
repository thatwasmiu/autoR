def start_auto_sync(self, interval=10):
    print("Auto syncing...")
    self.open_sync_modal()
    self.interval = interval
    self.remaining = interval
    self.update_countdown_loop()

def update_countdown_loop(self):
    self.label.config(text=f"Auto sync in: {self.remaining}s")

    if self.remaining > 0:
        self.remaining -= 1
        self.root.after(1000, self.update_countdown_loop)
    else:
        self.label.config(text="Syncing...")
        self.run_sync_thread()
        self.remaining = self.interval
        self.root.after(1000, self.update_countdown_loop)