#!/usr/bin/env python3
import asyncio
import sys
import random
import threading
sys.path.insert(0, ".")
from client.game_client import GameClient
from client.gui import MonopolyGUI

def main():
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8765

    loop = asyncio.new_event_loop()
    client = GameClient(host, port)
    gui = MonopolyGUI(client)

    async def on_message(msg):
        gui.root.after(0, gui.handle_message, msg)

    client.on(None, on_message)

    async def connect_and_join():
        connected = await client.connect()
        if connected:
            name = sys.argv[3] if len(sys.argv) > 3 else f"Player_{random.randint(100, 999)}"
            gui.root.after(0, lambda: setattr(gui, "my_name", name))
            await client.send({"type": "join_game", "name": name})
        else:
            print(f"无法连接到服务器 {host}:{port}")

    def run_loop():
        asyncio.set_event_loop(loop)
        loop.run_until_complete(connect_and_join())
        loop.run_forever()

    threading.Thread(target=run_loop, daemon=True).start()
    gui.run()
    loop.call_soon_threadsafe(loop.stop)

if __name__ == "__main__":
    main()
