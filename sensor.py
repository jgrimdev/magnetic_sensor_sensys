import serial


class Sensor:
    def __init__(self, port='COM4', baud_rate=115200, timeout=1):
        self.port = port
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.running = False
        self.ser = None
        self.status="Connection"

    def process_magnetic_field_values(self, values):
        values = [float(value) for value in values]
        return values

    def start_serial_communication(self, callback):

        try:
            self.status = "Connection works"
            self.ser = serial.Serial(self.port, self.baud_rate, timeout=self.timeout)
            if self.ser.is_open:
                print(f"Serial port {self.port} opened successfully.")
                self.ser.write(b'START\r\n')
                self.ser.write(b'SENSYSDATA\r\n')
                # Skip initial responses
                for _ in range(6):
                    self.ser.readline()

                self.running = True
                while self.running:
                    response = self.ser.readline().strip().decode()
                    if response.startswith('$PSEND'):
                        parts = response.split(',')
                        magnetic_values = parts[4:7]  # Extract values from index 4 to 6 (inclusive)
                        last_value = magnetic_values[-1].split('*')[0]  # Remove checksum
                        magnetic_values[-1] = last_value
                        # Call function to process the magnetic field values
                        processed_values = self.process_magnetic_field_values(magnetic_values)
                        # Pass the processed values to the callback function
                        callback(processed_values)

                # Send stop command and close serial port
                self.ser.write(b'STOP\r\n')
                self.ser.close()
                print(f"Serial port {self.port} closed.")
                self.status = "Connection works"
            else:
                print(f"Failed to open serial port {self.port}.")

        except Exception as e:
            self.status = "PORT not found"
            print(f"An error occurred: {str(e)}")


    def stop_serial_communication(self):
        self.running = False
        print("Ending communication.")
        self.status = "Connection lost"


if __name__ == "__main__":
    # Example usage: pass a callback function that processes received values
    def callback(values):
        # Example: Print received values
        # print("Received values:", values)
        pass


    # Create a Sensor instance and start serial communication with the callback function
    sensor = Sensor()
    sensor.start_serial_communication(callback)
