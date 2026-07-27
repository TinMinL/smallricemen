#!/usr/bin/env python3
import asyncio
import sys
sys.path.insert(0, ".")
from server.game_server import GameServer

async def main():
    host = sys.argv[1] if len(sys.argv) > 1 else "0.0.0.0"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8765
    server = GameServer(host, port)
    await server.start()

if __name__ == "__main__":
    asyncio.run(main())
