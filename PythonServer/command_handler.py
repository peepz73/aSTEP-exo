import json
import asyncio

from data_handler import DataHandler


class CommandHandler:

    def __init__(self, ingoing, outgoing):

        self.data_handler = DataHandler()
        self.ingoing = ingoing
        self.outgoing = outgoing

        self.command_dictionary = \
            {
                "connect": self.data_handler.connect_arduino,
                "start": self.data_handler.start_stop_data_collection,
                "flaots": self.data_handler.write_to_csv
            }

        asyncio.ensure_future(self.get_ingoing_commands())


    async def get_ingoing_commands(self):
        """
        Waits for ingoing commands
        """
        while True:
            command = await self.ingoing.get()
            print("command" + command)
            await self.decide_command(command, self.ingoing, self.outgoing)

    async def decide_command(self, command, ingoing, outgoing):
        """
        Handles ingoing commands
        :param command: The command (a string)
        :param ingoing: ingoing_command_queue from websocket_server
        :param outgoing: outgoing_message_queue from websocket_server
        """
        if command == 'connect':
            self.command_dictionary[command](outgoing)
        elif command == 'start':
            await self.command_dictionary[command](ingoing, outgoing)
        elif command[0] == 'floats':

            self.command_dictionary[command[0]](command[1])
        else:
            raise Exception('Invalid command. The received command was: ' + command)

