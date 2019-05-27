import serial
import serial.tools.list_ports
import asyncio
import json
import struct


class SerialPortController:

    def __init__(self):
        self.ports = []
        self.arduino_port = serial.Serial()

    def find_arduino(self, outgoing):
        self.find_all_ports()
        self.open_all_ports(self.ports, outgoing)

    def find_all_ports(self):
        """
        Gets all non-empty ports
        """
        self.ports = serial.tools.list_ports.comports()

        for port, desc, hwid in sorted(self.ports):
            print("{}: {} [{}]".format(port, desc, hwid))

    def open_all_ports(self, ports, outgoing):
        """
        Opens all ports and searches for a specific byte
        :param ports: All non-empty ports
        """
        connected_ports = []
        recived_byte = bytes()
        handshake_byte = bytes('y', 'utf-8')
        expected_byte = bytes('R', 'utf-8')

        if self.arduino_port.is_open:
            self.arduino_port.close()

        for port, desc, hwid in sorted(ports):
            try:
                connected_ports.append(serial.Serial(port, 250000, timeout=1))

            except Exception as e:
                print(f"An exception occurred: {e}")

        for port in connected_ports:
            while not recived_byte:
                port.write(handshake_byte)
                recived_byte = self.read_byte(port, handshake_byte)

            if recived_byte == expected_byte:
                self.arduino_port = port
                #self.arduino_port.write(handshake_byte)

                self.send_command('connected', outgoing)
                #break
            else:
                port.close()
            
            # while not recived_byte:
            #     port.write(handshake_byte)
            #     print(handshake_byte)
            #     recived_byte = self.read_byte(port, handshake_byte)
            #     print(recived_byte)
            #
            # if recived_byte != bytes([0]):
            #     self.arduino_port = port
            #     self.send_command('connected', outgoing)
            #     port.flush()
            # else:
            #     port.close()

            recived_byte = bytes()

        if not self.arduino_port.is_open:
            self.send_command('not_connected', outgoing)

    def read_byte(self, port, handshake_byte):
        """
        Reads a byte from the serial port connection and returns bytes([0]) if it can't read a byte
        :param port: The current port we read from
        :return: The received byte or bytes([0])
        """
        try_counter = 0
        condition = True

        received_byte = bytes()

        while condition:
            port.write(handshake_byte)
            ch = port.read()
            #print(ch.decode('utf-8'))
            received_byte = ch

            if self.if_byte_empty(ch):
                condition = False
            elif try_counter is 2:
                received_byte = bytes([0])
                condition = False
            else:
                try_counter += 1

        return received_byte

    def if_byte_empty(self, byte):
        """
        Checks if the received byte is empty
        :param byte: The receved byte
        :return: Boolean
        """

        if not byte:
            return False
        else:
            return True

    def collect_data(self):
        """
        Reads bytes for the continuous data gathering
        :return: Received byte
        """

        data_to_send = self.arduino_port.read()
        print(data_to_send)
        data = int.from_bytes(data_to_send, byteorder='big', signed=True)

        return data

    def collect(self):
        data_object = []
        data_list = []
        sensor_counter = 0

        self.arduino_port.write(bytes('y', 'utf-8'))
        self.arduino_port.flushInput()
        self.arduino_port.write(bytes('S', 'utf-8'))

        while len(data_object) < 7:
            if sensor_counter <= 17:
                arduino_data = self.arduino_port.read()
                data = int.from_bytes(arduino_data, byteorder='big', signed=True)
                data_list.append(data)
                #print(arduino_data)
                sensor_counter += 1
                #i += 1
            else:
                sensor_counter = 0
                data_object.append(data_list)
                data_list = []

        #self.arduino_port.flushInput()

        return data_object

    def send_command(self, command, outgoing):
        json_to_send = json.dumps({"command": command})
        asyncio.ensure_future(outgoing.put(json_to_send))



