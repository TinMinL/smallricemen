#!/usr/bin/env python3
import asyncio
import sys
sys.path.insert(0, ".")
from client.game_client import GameClient
from client.gui import MonopolyGUI

async def main():
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8765

    client = GameClient(host, port)
    gui = MonopolyGUI(client)
    client.gui = gui

    async def on_message(msg):
        t = msg.get("type")
        print(f"收到: {t}")

        if t == "join_game":
            gui.my_pid = msg.get("pid")
            gui.add_message(f"已加入游戏，ID: {gui.my_pid}")
            gui.connected = True

        elif t == "player_joined":
            gui.lobby_players = msg.get("players", [])
            gui.add_message(f"{msg.get('name')} 加入了游戏")

        elif t == "game_start":
            gui.in_lobby = False
            gui.game_state = {"players": msg.get("players", []), "current_turn": 0, "turn_phase": "playing"}
            gui.add_message("游戏开始！")

        elif t == "state_update":
            gui.game_state = msg

        elif t == "your_turn":
            gui.show_toast("轮到你了！按 D 掷骰子")
            if msg.get("in_jail"):
                m = "你在监狱中！按 D 掷骰子"
                if msg.get("can_pay"):
                    m += " | 按 P 交$50罚款"
                if msg.get("has_card"):
                    m += " | 按 C 使用出狱卡"
                gui.show_toast(m)

        elif t == "dice_result":
            dice = msg.get("dice", [0, 0])
            gui.add_message(msg.get("text", f"掷出 {dice[0]}+{dice[1]}"))

        elif t == "system_message":
            gui.add_message(msg.get("text", ""))

        elif t == "chat":
            gui.add_message(f"{msg.get('name')}: {msg.get('text')}")

        elif t == "card_drawn":
            gui.card_animation = msg
            gui.add_message(msg.get("text", "抽到卡片"))

        elif t == "prompt_decision":
            if msg.get("decision") == "buy_property":
                gui.pending_decision = msg
                gui.show_toast("按 B 购买 | 按 N 跳过")

        elif t == "turn_options":
            pass

        elif t == "prompt_start":
            gui.add_message("输入 /start 开始游戏")

        elif t == "error":
            gui.add_message(f"错误: {msg.get('message')}")

        elif t == "auction_update":
            gui.add_message(f"拍卖: {msg.get('bidder_name')} 出价 ${msg.get('bid')}")

        elif t == "game_over":
            gui.add_message(f"游戏结束！胜者: {msg.get('winner_name')}")
            gui.show_toast(f"游戏结束！{msg.get('winner_name')} 获胜！")

    client.on(None, on_message)

    connected = await client.connect()
    if connected:
        name = sys.argv[3] if len(sys.argv) > 3 else f"Player_{random.randint(100, 999)}"
        gui.my_name = name
        await client.send({"type": "join_game", "name": name})
        await gui.run()
    else:
        print(f"无法连接到服务器 {host}:{port}")

if __name__ == "__main__":
    import random
    asyncio.run(main())
