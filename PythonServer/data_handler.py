from serial_port import SerialPortController
import json
import time
import csv

import asyncio

class DataHandler:
    def __init__(self):
        self.SPC = SerialPortController()

    def connect_arduino(self, outgoing):
        self.SPC.find_arduino(outgoing)

    async def start_stop_data_collection(self, ingoing, outgoing):
        """
        Responsible for starting/stopping the data gathering
        :param ingoing: ingoing_command_queue from websocket_server
        :param outgoing: outgoing_message_queue from websocket_server
        """
        active = True
        end_time = time.time() + 5
        byte_counter = 0

        json_to_send = {}



        while active:

            if ingoing.qsize() == 0 and time.time() < end_time:
                try:
                    await self.get_5000_datapoints(ingoing, outgoing)
                except Exception as e:
                    print(f'Could not read data. The following exception occurred {e}')
                    active = False
                    command = 'disconnected'

                    await self.send_data('command', command, outgoing)
            elif time.time() > end_time:
                active = False
                command = 'stop'
                await self.send_data('command', command, outgoing)
            else:
                await ingoing.get()
                active = False

        #self.write_to_csv()


    async def get_5000_datapoints(self, ingoing, outgoing):
        byte_counter = 0

        data = []

        while byte_counter < 5000:
            if ingoing.qsize() == 0:
                try:
                    data_to_send = self.SPC.collect()
                    print(data_to_send)
                    byte_counter += 126
                    print(byte_counter/18)

                    await self.send_data('data', data_to_send, outgoing)
                except Exception as e:
                    print(f'Could not read data. The following exception occurred {e}')
                    command = 'disconnected'

                    await self.send_data('command', command, outgoing)

                    break
            else:
                 break


    async def send_data(self, command_data_flag, data, outgoing):
        json_to_send = {
            command_data_flag: data
        }

        #print(data)
        json_to_send = json.dumps(json_to_send)

        # Add functionality for sending data to UI
        await asyncio.ensure_future(outgoing.put(json_to_send))

    def write_to_csv(self):
        i = 0
        string_floats = []
        floats = []

        with open('collection_data.csv', 'r') as ingoing, open('collection_data_floats.csv', 'w+', newline='') as out:
            writer = csv.writer(out)
            reader = csv.reader(ingoing)

            for row in reader:
                for char in row:
                    string_float = f'{char[i]}.{char[i+1]}'
                    i += 2
                i = 0



        out.close()

