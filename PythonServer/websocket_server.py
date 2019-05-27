import asyncio
import websockets
import json

from command_handler import CommandHandler


class WebsocketServer:

    def __init__(self):

        self.outgoing_message_queue = asyncio.Queue()
        self.ingoing_command_queue = asyncio.Queue()
        self.connected = set()

        self.command_handler = CommandHandler(self.ingoing_command_queue, self.outgoing_message_queue)

        self.start_server()

    async def handler(self, websocket, path):
        """
        Saves and removes websocket connections
        :param websocket: A websocket that asks for a connection
        :param path:
        """

        # Register.
        self.connected.add(websocket)

        try:
            # Handle websockets.
            await asyncio.wait([self.consumer_producer_handler(ws, path) for ws in self.connected])
        finally:
            # Unregister.
            self.connected.remove(websocket)
            print('REMOVED WEBSOCKET')


    async def consumer_handler(self, websocket, path):
        """
        Is responsible for handling all incoming data/messages on the connection
        :param websocket: A connected websocket
        :param path:
        """
        try:
            async for message in websocket:
                await self.consumer(message)
        except Exception as e:
            print(f'The following exeption occured: {e}')


    async def producer_handler(self, websocket, path):
        """
        Ïs responsible for handling all outgoing data/messages on the connection
        :param websocket: A connected websocket
        :param path:
        """
        while True:
            message = await self.producer()

            await websocket.send(message)

    async def consumer(self, message):
        """
        Is responsible for handling all incoming data/messages on the connection
        :param message: The received message
        """
        print("Message: " + message)

        command = json.loads(message)
        await asyncio.ensure_future(self.ingoing_command_queue.put(command["message"]))

    async def producer(self):
        """
        Ïs responsible for handling all outgoing data/messages on the connection
        :return: Message/data to send
        """
        message = await self.outgoing_message_queue.get()

        return message

    async def consumer_producer_handler(self, websocket, path):
        """
        Is responsible for setting up the consumer and producer when a new websocket connects
        :param websocket: A connected websocket
        :param path:
        """
        consumer_task = asyncio.ensure_future(
            self.consumer_handler(websocket, path))
        producer_task = asyncio.ensure_future(
            self.producer_handler(websocket, path))
        done, pending = await asyncio.wait(
            [consumer_task, producer_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()

    def start_server(self):
        """
        Sets up the websocket server
        """
        start_server = websockets.serve(self.handler, "localhost", 8081)
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()
