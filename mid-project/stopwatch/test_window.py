"""Exercise actual Tk buttons and refresh callbacks, then close the window."""
import time
import tkinter as tk
from tkinter import ttk
from unittest.mock import patch

import simulator


def check_window(root):
    errors = []
    root.report_callback_exception = lambda kind, value, trace: errors.append(value)

    def descendants(widget):
        for child in widget.winfo_children():
            yield child
            yield from descendants(child)

    def wait(seconds=0.15):
        end = time.perf_counter() + seconds
        while time.perf_counter() < end:
            root.update()
            time.sleep(0.005)
        assert not errors, errors

    try:
        root.update()
        widgets = list(descendants(root))
        buttons = {str(w.cget("text")): w for w in widgets if isinstance(w, ttk.Button)}
        table = next(w for w in widgets if isinstance(w, ttk.Treeview))
        clock = next(w for w in widgets if isinstance(w, ttk.Label) and w.cget("text") == "00:00.00")
        wait()
        buttons["Start / Pause [S]"].invoke()
        wait()
        assert clock.cget("text") != "00:00.00"
        buttons["Save lap [L]"].invoke()
        wait()
        assert len(table.get_children()) == 1
        buttons["Start / Pause [S]"].invoke()
        wait()
        paused = clock.cget("text")
        wait()
        assert clock.cget("text") == paused
        buttons["Reset [R]"].invoke()
        wait()
        assert clock.cget("text") == "00:00.00"
        assert not table.get_children()
        for widget in widgets:
            assert widget.winfo_rooty() + widget.winfo_height() <= root.winfo_rooty() + root.winfo_height(), "Widget clipped vertically"
        print("Window verified: start, live refresh, lap table, pause, reset, and vertical layout.")
    finally:
        root.destroy()


if __name__ == "__main__":
    with patch.object(tk.Tk, "mainloop", check_window):
        simulator.main()
