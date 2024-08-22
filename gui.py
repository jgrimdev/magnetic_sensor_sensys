import csv, os, serial.tools.list_ports, time
import tkinter as tk
import customtkinter as ctk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
from matplotlib.figure import Figure
import threading
import queue  # For inter-thread communication

from PIL import Image, ImageTk
from sensor import Sensor


class RealTimeGraphApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Magnetic sensor FGM3D/100")
        self.root.configure(background='white')
        # self.sensor = Sensor(port='COM4')

        script_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(script_dir, "img/magnet.ico")
        self.root.iconbitmap(icon_path)

        # Selecting color mode and theme-blue, green, dark-blue
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        # self.csv_filename = "data"
        self.create_widgets()
        self.create_plot()
        # self.loading_screen(duration=1400) # Kdyby náhodou
        self.data_x1, self.data_y1 = [], []
        self.data_x2, self.data_y2 = [], []
        self.data_x3, self.data_y3 = [], []
        self.is_logging_to_csv = False
        self.start_time = time.time()
        self.ani = animation.FuncAnimation(self.fig, self.update_plot, interval=50)
        self.data_queue = queue.Queue()

        self.last_com_port = self.load_last_com_port()  # Load the last chosen COM port
        self.available_com_ports = self.get_available_com_ports()  # Populate the dropdown menu with available COM ports
        self.com_port_var.set(
            self.last_com_port if self.last_com_port in self.available_com_ports else self.available_com_ports[0])

        # self.start_sensor_communication()

        # Bind the on_closing method to the window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    # GUI
    def create_widgets(self):
        # Create a frame for upper buttons
        self.button_frame = ctk.CTkFrame(self.root)
        self.button_frame.grid(row=0, column=0, columnspan=4, sticky='ew', padx=1, pady=1)
        # Create a frame for settings
        self.control_frame = ctk.CTkFrame(self.root)
        self.control_frame.grid(row=1, column=0, columnspan=4, sticky='ew', padx=1, pady=1)
        # Create a frame for info
        self.info_frame = ctk.CTkFrame(self.root)
        self.info_frame.grid(row=2, column=0, columnspan=4, sticky='ew', padx=1, pady=1)

        # Configure column weights to distribute space
        # self.button_frame.columnconfigure(0, weight=1)
        # self.button_frame.columnconfigure(1, weight=1)
        # self.button_frame.columnconfigure(2, weight=1)

        # --- Line 0 ---
        self.clear_button = ctk.CTkButton(self.button_frame, text="Clear Graph", command=self.clear_graph)
        self.clear_button.grid(row=0, column=0, padx=5, pady=5, sticky='w')

        # self.end_button = ctk.CTkButton(self.button_frame, text="End", command=self.end_application)
        # self.end_button.grid(row=0, column=2, padx=5, pady=5, sticky='e')

        # --- Line 1 ---
        # Checkboxes
        self.show_graph1_var = tk.IntVar(value=1)
        self.show_graph1_checkbox = ctk.CTkCheckBox(self.control_frame, text="Show Axis 1",
                                                    variable=self.show_graph1_var,
                                                    command=self.update_visibility)
        self.show_graph1_checkbox.grid(row=1, column=0, padx=5, pady=5, sticky='w')

        self.show_graph2_var = tk.IntVar(value=1)
        self.show_graph2_checkbox = ctk.CTkCheckBox(self.control_frame, text="Show Axis 2",
                                                    variable=self.show_graph2_var,
                                                    command=self.update_visibility)
        self.show_graph2_checkbox.grid(row=1, column=1, padx=5, pady=5, sticky='w')

        self.show_graph3_var = tk.IntVar(value=1)
        self.show_graph3_checkbox = ctk.CTkCheckBox(self.control_frame, text="Show Axis 3",
                                                    variable=self.show_graph3_var,
                                                    command=self.update_visibility)
        self.show_graph3_checkbox.grid(row=1, column=2, padx=5, pady=5, sticky='w')

        # --- Line 2 ---
        # Create label and text entry for CSV filename
        ctk.CTkLabel(self.control_frame, text="CSV Filename: ").grid(row=2, column=0, padx=5, pady=5, sticky='e')
        self.csv_filename_entry = ctk.CTkEntry(self.control_frame)
        self.csv_filename_entry.grid(row=2, column=1, padx=5, pady=5, sticky='w')
        self.csv_filename_entry.insert(0, "default.csv")  # Set default value

        # Create checkbox for logging to CSV
        self.log_to_csv_var = tk.IntVar(value=0)
        self.log_to_csv_checkbox = ctk.CTkCheckBox(self.control_frame, text="Log to CSV", variable=self.log_to_csv_var,
                                                   command=self.toggle_csv_logging)
        self.log_to_csv_checkbox.grid(row=2, column=2, padx=5, pady=5, sticky='w')

        # --- Line 3 ---
        # Create label and dropdownmenu for COM port
        ctk.CTkLabel(self.control_frame, text="COM Port: ").grid(row=3, column=0, padx=5, pady=5, sticky='e')
        self.com_port_var = tk.StringVar()
        self.com_port_combobox = ctk.CTkComboBox(self.control_frame, variable=self.com_port_var,
                                                 values=self.get_available_com_ports())
        self.com_port_combobox.grid(row=3, column=1, padx=5, pady=5, sticky='w')
        # Create status bar - little broken - fix it
        self.connection_label = ctk.CTkLabel(self.control_frame, text="Connection")
        self.connection_label.grid(row=3, column=4, padx=10, pady=5, sticky='e')
        # Start/stop buttons
        self.start_button = ctk.CTkButton(self.control_frame, text="Start", command=self.start_sensor_communication)
        self.start_button.grid(row=3, column=2, padx=5, pady=5, sticky='w')
        self.stop_button = ctk.CTkButton(self.control_frame, text="Stop", command=self.stop_sensor_communication)
        self.stop_button.grid(row=3, column=3, padx=5, pady=5, sticky='w')

        # --- Line 4 ---
        # only info about B field
        self.magnetic_field_label = ctk.CTkLabel(self.info_frame, text="Magnetic Field Size: 0.00000 G")
        self.magnetic_field_label.grid(row=0, column=0, padx=10, pady=5, sticky='w')

        self.value_label = ctk.CTkLabel(self.info_frame, text="Graph Values: x=0.00, y=0.00")
        self.value_label.grid(row=0, column=1, padx=10, pady=5, sticky='e')

    # region Start/stop and communication with sensor
    def stop_sensor_communication(self):
        if self.sensor_thread.is_alive():
            self.sensor.stop_serial_communication()
            self.sensor_thread.join()
        self.connection_label.configure(text="Communication stopped")

    def start_sensor_communication(self):
        try:
            # Read COM port from dropdown menu
            com_port = self.com_port_var.get()
            # Initialize the sensor with user-defined settings
            self.sensor = Sensor(port=com_port)
            # Start the sensor communication thread
            self.sensor_thread = threading.Thread(target=self.sensor.start_serial_communication,
                                                  args=(self.update_sensor_data,))
            self.sensor_thread.start()

            # Save the selected COM port
            self.save_last_com_port()
            self.connection_label.configure(text="Connection not found")
        except:
            self.connection_label.configure(text="Connection not found")
            pass

    def get_available_com_ports(self):
        ports = [f"COM{i}" for i in range(1, 256)]
        available_ports = []
        for port in ports:
            try:
                s = serial.Serial(port)
                s.close()
                available_ports.append(port)
            except (OSError, serial.SerialException):
                pass
        return available_ports

    def load_last_com_port(self):
        try:
            with open("config.txt", "r") as file:
                return file.read().strip()
        except FileNotFoundError:
            return "COM4"

    def save_last_com_port(self):
        with open("config.txt", "w") as file:
            file.write(self.com_port_var.get())

    # endregion

    # region GUI - plot logic
    def update_visibility(self):
        # Update plot based on checkbox state
        self.canvas.draw_idle()

    def create_plot(self):
        # Create a Matplotlib figure
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().grid(row=3, column=0, columnspan=4, sticky='nsew')
        self.canvas.mpl_connect("motion_notify_event", self.on_plot_hover)

        # Make the plot area expandable
        self.root.grid_rowconfigure(3, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_columnconfigure(2, weight=1)
        self.root.grid_columnconfigure(3, weight=1)

    def update_plot(self, frame):

        # if self.is_running:
        self.ax.clear()
        # Plot the data for each measurement
        if self.show_graph1_var.get():
            self.ax.plot(self.data_x1, self.data_y1, label="Axis 1")
        if self.show_graph2_var.get():
            self.ax.plot(self.data_x2, self.data_y2, label="Axis 2")
        if self.show_graph3_var.get():
            self.ax.plot(self.data_x3, self.data_y3, label="Axis 3")

        self.ax.legend()
        self.ax.set_xlabel('Time')
        self.ax.set_ylabel('Magnetic field (T)')
        self.ax.set_title('Real-time Data Plot')

        combined_size = 10000 * np.sqrt(
            np.mean(np.array(self.data_y1) ** 2 + np.array(self.data_y2) ** 2 + np.array(self.data_y3) ** 2))
        self.magnetic_field_label.configure(text=f"Magnetic Field Size: {combined_size:.5f} G")

        # Draw the canvas
        self.canvas.draw()

        # Check if logging to CSV is enabled and log data if so
        if self.is_logging_to_csv:
            self.csv_filename = self.csv_filename_entry.get()
            self.write_to_csv()

    def clear_graph(self):
        # Clear all datasets
        self.data_x1.clear()
        self.data_y1.clear()
        self.data_x2.clear()
        self.data_y2.clear()
        self.data_x3.clear()
        self.data_y3.clear()

        # Clear the plot
        self.ax.clear()
        self.canvas.draw()

        # Reset the value label
        self.value_label.configure(text="Graph Values: ")

    def on_plot_hover(self, event):
        x = event.xdata
        y = event.ydata

        if x is not None and y is not None:
            self.value_label.configure(text=f"Graph Values: x={x:.2f}, y={y * 1e5:.2f}")

    # endregion

    # region Handle data and write data to file
    def update_sensor_data(self, values):
        # Update data arrays with new sensor values
        self.data_x1.append(time.time() - self.start_time)
        self.data_y1.append(values[0])
        self.data_x2.append(time.time() - self.start_time)
        self.data_y2.append(values[1])
        self.data_x3.append(time.time() - self.start_time)
        self.data_y3.append(values[2])

        # Keep only the last 100 data points for each dataset
        self.data_x1 = self.data_x1[-100:]
        self.data_y1 = self.data_y1[-100:]
        self.data_x2 = self.data_x2[-100:]
        self.data_y2 = self.data_y2[-100:]
        self.data_x3 = self.data_x3[-100:]
        self.data_y3 = self.data_y3[-100:]

    def write_to_csv(self):
        filename = f"{self.csv_filename}.csv"
        # filename = f"data.csv"
        with open(filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Time', 'Measurement 1', 'Measurement 2', 'Measurement 3'])
            for i in range(len(self.data_x1)):
                writer.writerow([self.data_x1[i], self.data_y1[i], self.data_y2[i], self.data_y3[i]])

    def toggle_csv_logging(self):
        if self.log_to_csv_var.get() == 1:
            self.is_logging_to_csv = True
        else:
            self.is_logging_to_csv = False

    # endregion

    # region Load gif for loading screen - no use for now
    def loading_screen(self, duration=3000):
        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Construct the full path to the GIF file
        gif_path = os.path.join(script_dir, "history/1.0/img/giphy.gif")
        # Load the animated GIF
        self.load_gif(gif_path)
        # Create a label for the GIF overlay
        self.gif_label = tk.Label(self.root, image=self.gif_frames[0], bg='white')
        self.gif_label.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.gif_label.lift()  # Bring to front
        # Start the animation
        self.animate(0, interval=50)
        # Schedule the destruction of the GIF label after 3000 milliseconds (3 seconds)
        self.root.after(duration, self.destroy_gif_label)

    def load_gif(self, filename):
        self.gif_frames = []
        self.gif_index = 0
        # Open the GIF file
        gif = Image.open(filename)
        # Extract each frame
        try:
            while True:
                self.gif_frames.append(ImageTk.PhotoImage(gif.copy()))
                gif.seek(gif.tell() + 1)
        except EOFError:
            pass

    def animate(self, frame, interval=100):
        self.gif_label.configure(image=self.gif_frames[frame])
        # Increase the frame index
        frame = (frame + 1) % len(self.gif_frames)
        # Schedule the next animation frame with reduced interval for faster playback
        self.root.after(interval, lambda: self.animate(frame, interval))

    def destroy_gif_label(self):
        # Destroy the GIF label
        self.gif_label.destroy()

    # endregion

    # region Closing app
    def end_application(self):
        # Stop the sensor thread
        try:
            if self.sensor_thread.is_alive():
                self.sensor.stop_serial_communication()
                self.sensor_thread.join()
        except:
            pass
        self.root.quit()
        self.root.destroy()

    def on_closing(self):
        self.save_last_com_port()
        self.end_application()
    # endregion


if __name__ == "__main__":
    root = tk.Tk()
    # root=ctk.CTk()
    app = RealTimeGraphApp(root)
    root.mainloop()
