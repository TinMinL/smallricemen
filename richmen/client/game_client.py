import asyncio
import json
from common.protocol import MessageType, encode, decode

class GameClient:
    def __init__(self, host="127.0.0.1", port=8765):
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None
        self.pid = None
        self.callbacks = {}

    def on(self, msg_type, callback):
        self.callbacks[msg_type] = callback

    async def connect(self):
        try:
            self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
            asyncio.create_task(self.receive_loop())
            return True
        except Exception as e:
            print(f"连接失败: {e}")
            return False

    async def send(self, msg):
        if self.writer:
            try:
                self.writer.write(encode(msg))
                await self.writer.drain()
            except Exception as e:
                print(f"发送失败: {e}")

    async def receive_loop(self):
        while True:
            try:
                data = await self.reader.readline()
                if not data:
                    break
                msg = decode(data)
                msg_type = msg.get("type")
                cb = self.callbacks.get(msg_type) or self.callbacks.get(None)
                if cb:
                    await cb(msg)
            except Exception as e:
                print(f"接收错误: {e}")
                break

    async def close(self):
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
