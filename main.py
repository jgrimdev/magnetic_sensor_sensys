import tkinter as tk
from gui import RealTimeGraphApp
from sensor import Sensor

if __name__ == "__main__":
    root = tk.Tk()
    app = RealTimeGraphApp(root)
    root.mainloop()
