#!/usr/bin/env python3
import asyncio
import os
import sys
base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base)
from server.game_server import GameServer

async def main():
    host = sys.argv[1] if len(sys.argv) > 1 else "0.0.0.0"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8765
    server = GameServer(host, port)
    await server.start()

if __name__ == "__main__":
    asyncio.run(main())
