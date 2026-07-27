import tkinter as tk
from tkinter import font as tkfont
import asyncio
import threading
from common.constants import *

TILE_SIZE = 65
SIDE_TILES = 11
BOARD_SIZE = TILE_SIZE * SIDE_TILES
INFO_WIDTH = 280
PAD = 10

PLAYER_COLORS = ["#ff3232", "#3232ff", "#32c832", "#ffc800", "#ff00ff", "#00ffff", "#ff9600", "#800080"]

BOARD_COORDS = {}
for tile in BOARD_TILES:
    i = tile["index"]
    if i == 0:
        BOARD_COORDS[i] = (TILE_SIZE * (SIDE_TILES - 1), TILE_SIZE * (SIDE_TILES - 1))
    elif 1 <= i <= 9:
        BOARD_COORDS[i] = (TILE_SIZE * (SIDE_TILES - 1 - i), TILE_SIZE * (SIDE_TILES - 1))
    elif i == 10:
        BOARD_COORDS[i] = (0, TILE_SIZE * (SIDE_TILES - 1))
    elif 11 <= i <= 19:
        BOARD_COORDS[i] = (0, TILE_SIZE * (SIDE_TILES - 1 - (i - 10)))
    elif i == 20:
        BOARD_COORDS[i] = (0, 0)
    elif 21 <= i <= 29:
        BOARD_COORDS[i] = (TILE_SIZE * (i - 20), 0)
    elif i == 30:
        BOARD_COORDS[i] = (TILE_SIZE * (SIDE_TILES - 1), 0)
    elif 31 <= i <= 39:
        BOARD_COORDS[i] = (TILE_SIZE * (SIDE_TILES - 1), TILE_SIZE * (i - 30))

class MonopolyGUI:
    def __init__(self, client):
        self.client = client
        self.root = tk.Tk()
        self.root.title("大富翁 - RichMen")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.resizable(False, False)

        self.my_pid = None
        self.my_name = "玩家"
        self.game_state = None
        self.in_lobby = True
        self.lobby_players = []
        self.messages = []
        self.pending_decision = None
        self.card_animation = None
        self.toast_text = ""
        self.toast_id = None

        self.root.bind("<Key>", self.on_key)

        total_w = BOARD_SIZE + INFO_WIDTH + PAD * 3
        total_h = BOARD_SIZE + PAD * 2
        self.root.geometry(f"{total_w}x{total_h}")

        self.font_sm = tkfont.Font(size=8)
        self.font_md = tkfont.Font(size=10)
        self.font_lg = tkfont.Font(size=14, weight="bold")
        self.font_xl = tkfont.Font(size=18, weight="bold")

        self.frame = tk.Frame(self.root)
        self.frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(self.frame, width=BOARD_SIZE, height=BOARD_SIZE,
                                 bg="#c8e6c8", highlightthickness=0)
        self.canvas.place(x=PAD, y=PAD)
        self.canvas.bind("<Button-1>", self.on_click)

        self.info_frame = tk.Frame(self.frame, width=INFO_WIDTH, bg="#f0f0f0",
                                    highlightbackground="#ccc", highlightthickness=1)
        self.info_frame.place(x=PAD * 2 + BOARD_SIZE, y=PAD, width=INFO_WIDTH, height=BOARD_SIZE)
        self.info_frame.pack_propagate(False)

        self.players_canvas = tk.Canvas(self.info_frame, bg="#f0f0f0",
                                         highlightthickness=0, height=350)
        self.players_canvas.pack(fill="x", padx=5, pady=5)

        self.chat_label = tk.Label(self.info_frame, text="聊天", font=self.font_sm,
                                    bg="#f0f0f0", fg="#888")
        self.chat_label.pack(anchor="w", padx=8)

        self.chat_frame = tk.Frame(self.info_frame, bg="white",
                                    highlightbackground="#ddd", highlightthickness=1)
        self.chat_frame.pack(fill="both", expand=True, padx=5, pady=(0, 5))

        self.chat_text = tk.Text(self.chat_frame, font=self.font_sm, bg="white",
                                  fg="#333", wrap="word", state="disabled",
                                  highlightthickness=0, borderwidth=0)
        self.chat_text.pack(fill="both", expand=True, padx=2, pady=2)

        self.input_var = tk.StringVar()
        self.input_entry = tk.Entry(self.info_frame, textvariable=self.input_var,
                                     font=self.font_md, bg="white", fg="#333")
        self.input_entry.pack(fill="x", padx=5, pady=(0, 5))
        self.input_entry.bind("<Return>", self.on_chat_submit)
        self.input_entry.bind("<Escape>", lambda e: self.root.focus_set())
        self.input_entry.bind("<FocusIn>", lambda e: self.root.after(50, self.check_input_focus))

        self.input_active = False

        self.root.after(100, self.render_loop)

    def check_input_focus(self):
        pass

    def on_chat_submit(self, event):
        text = self.input_var.get().strip()
        if not text:
            return
        if text.startswith("/"):
            cmd = text[1:].strip().lower()
            if cmd == "start":
                asyncio.run_coroutine_threadsafe(
                    self.client.send({"type": "start_game"}), asyncio.get_event_loop())
            elif cmd in ("dice", "roll"):
                asyncio.run_coroutine_threadsafe(
                    self.client.send({"type": "roll_dice"}), asyncio.get_event_loop())
            elif cmd == "end":
                asyncio.run_coroutine_threadsafe(
                    self.client.send({"type": "end_turn"}), asyncio.get_event_loop())
            elif cmd.startswith("bid "):
                try:
                    bid = int(cmd.split()[1])
                    asyncio.run_coroutine_threadsafe(
                        self.client.send({"type": "auction_bid", "bid": bid}), asyncio.get_event_loop())
                except:
                    self.add_message("用法: /bid <金额>")
            elif cmd == "buy":
                asyncio.run_coroutine_threadsafe(
                    self.client.send({"type": "decision_response", "decision": "buy_property", "accepted": True}), asyncio.get_event_loop())
                self.pending_decision = None
            elif cmd == "skip":
                asyncio.run_coroutine_threadsafe(
                    self.client.send({"type": "decision_response", "decision": "buy_property", "accepted": False}), asyncio.get_event_loop())
                self.pending_decision = None
            else:
                self.add_message(f"未知命令: /{cmd}")
        else:
            asyncio.run_coroutine_threadsafe(
                self.client.send({"type": "chat", "text": text}), asyncio.get_event_loop())
        self.input_var.set("")

    def on_key(self, event):
        if self.input_entry.focus_get() is self.input_entry:
            return
        if event.char == "d" or event.char == "D":
            asyncio.run_coroutine_threadsafe(
                self.client.send({"type": "roll_dice"}), asyncio.get_event_loop())
        elif event.char == "e" or event.char == "E":
            asyncio.run_coroutine_threadsafe(
                self.client.send({"type": "end_turn"}), asyncio.get_event_loop())
        elif event.char == "b" or event.char == "B":
            if self.pending_decision and self.pending_decision.get("decision") == "buy_property":
                asyncio.run_coroutine_threadsafe(
                    self.client.send({"type": "decision_response", "decision": "buy_property", "accepted": True}), asyncio.get_event_loop())
                self.pending_decision = None
        elif event.char == "n" or event.char == "N":
            if self.pending_decision and self.pending_decision.get("decision") == "buy_property":
                asyncio.run_coroutine_threadsafe(
                    self.client.send({"type": "decision_response", "decision": "buy_property", "accepted": False}), asyncio.get_event_loop())
                self.pending_decision = None
        elif event.char == "p" or event.char == "P":
            asyncio.run_coroutine_threadsafe(
                self.client.send({"type": "pay_jail_fine"}), asyncio.get_event_loop())
        elif event.char == "c" or event.char == "C":
            asyncio.run_coroutine_threadsafe(
                self.client.send({"type": "use_get_out_of_jail"}), asyncio.get_event_loop())
        elif event.keysym == "Escape":
            self.card_animation = None

    def on_click(self, event):
        if self.card_animation:
            self.card_animation = None
            return
        x, y = event.x, event.y
        if self.pending_decision:
            dec = self.pending_decision
            if dec.get("decision") == "buy_property":
                cx = self.root.winfo_width() // 2
                cy = self.root.winfo_height() // 2
                if cx - 120 <= x <= cx - 20 and cy <= y <= cy + 40:
                    asyncio.run_coroutine_threadsafe(
                        self.client.send({"type": "decision_response", "decision": "buy_property", "accepted": True}), asyncio.get_event_loop())
                    self.pending_decision = None
                elif cx + 20 <= x <= cx + 120 and cy <= y <= cy + 40:
                    asyncio.run_coroutine_threadsafe(
                        self.client.send({"type": "decision_response", "decision": "buy_property", "accepted": False}), asyncio.get_event_loop())
                    self.pending_decision = None

    def on_close(self):
        self.root.destroy()

    def add_message(self, text):
        self.messages.append(text)
        if len(self.messages) > 100:
            self.messages = self.messages[-100:]
        self.chat_text.config(state="normal")
        self.chat_text.insert("end", text + "\n")
        self.chat_text.see("end")
        self.chat_text.config(state="disabled")

    def show_toast(self, text):
        self.toast_text = text
        if self.toast_id:
            self.root.after_cancel(self.toast_id)
        self.toast_id = self.root.after(4000, self.clear_toast)

    def clear_toast(self):
        self.toast_text = ""
        self.toast_id = None
        self.render_loop()

    def render_loop(self):
        if not self.root.winfo_exists():
            return

        self.canvas.delete("all")
        self.players_canvas.delete("all")

        if self.in_lobby:
            self.render_lobby()
        else:
            self.render_board()
            self.render_players()
            self.render_info()

        self.render_toast()
        self.render_decision()
        self.render_card()

        self.root.after(50, self.render_loop)

    def render_lobby(self):
        self.canvas.create_text(BOARD_SIZE // 2, 80, text="🎲 大富翁", font=self.font_xl, fill="white")
        self.canvas.create_text(BOARD_SIZE // 2, 110, text="RichMen", font=self.font_md, fill="#ccffcc")
        self.canvas.create_text(BOARD_SIZE // 2, 150, text="等待玩家加入...", font=self.font_md, fill="#ccffcc")
        y = 200
        for p in self.lobby_players:
            self.canvas.create_text(BOARD_SIZE // 2, y, text=f"  {p.get('name', '未知')}",
                                     font=self.font_md, fill="white", anchor="w")
            y += 30
        self.canvas.create_text(BOARD_SIZE // 2, BOARD_SIZE - 60, text="/start 开始游戏（至少2人）",
                                 font=self.font_sm, fill="#aaffaa")

    def render_board(self):
        self.canvas.create_rectangle(0, 0, BOARD_SIZE, BOARD_SIZE, fill="#c8e6c8")
        for tile in BOARD_TILES:
            self.render_tile(tile)

        cx, cy = BOARD_SIZE // 2, BOARD_SIZE // 2
        self.canvas.create_text(cx, cy - 20, text="大富翁", font=self.font_lg, fill="#2d5a2d")
        self.canvas.create_text(cx, cy + 5, text="RichMen", font=self.font_sm, fill="#555")

    def render_tile(self, tile):
        i = tile["index"]
        x, y = BOARD_COORDS[i]
        w, h = TILE_SIZE, TILE_SIZE
        is_corner = i in (0, 10, 20, 30)

        color_strip = 12

        if is_corner:
            self.canvas.create_rectangle(x, y, x + w, y + h, fill="#ffffd0", outline="#333")
            name = tile["name"]
            self.canvas.create_text(x + w // 2, y + h // 2, text=name, font=self.font_sm, fill="#333")
            return

        tile_type = tile.get("type")
        if tile_type == TILE_PROPERTY:
            group = tile.get("group", "brown")
            c = COLORS.get(group, (200, 200, 200))
            hex_c = f"#{c[0]:02x}{c[1]:02x}{c[2]:02x}"
        elif tile_type == TILE_RAILROAD:
            hex_c = "#888"
        elif tile_type == TILE_UTILITY:
            hex_c = "#96c8ff"
        elif tile_type == TILE_CHANCE:
            hex_c = "#ffc864"
        elif tile_type == TILE_COMMUNITY_CHEST:
            hex_c = "#ff9696"
        elif tile_type == TILE_TAX:
            hex_c = "#ccc"
        else:
            hex_c = "#ccc"

        self.canvas.create_rectangle(x, y, x + w, y + h, fill="#fff", outline="#333")
        self.canvas.create_rectangle(x, y, x + w, y + color_strip, fill=hex_c, outline="")

        is_h = 1 <= i <= 9 or 21 <= i <= 29
        name = tile["name"]
        if len(name) > 6:
            name = name[:6]

        if is_h:
            self.canvas.create_text(x + w // 2, y + color_strip + 8, text=name,
                                     font=self.font_sm, fill="#333")
        else:
            self.canvas.create_text(x + 4, y + color_strip + 8, text=name,
                                     font=self.font_sm, fill="#333", anchor="nw")

        price = tile.get("price", 0)
        if price:
            self.canvas.create_text(x + w // 2, y + h - 4, text=f"${price}",
                                     font=self.font_sm, fill="#070", anchor="s")

        game_state = self.game_state
        if game_state:
            players = game_state.get("players", [])
            for pi, p in enumerate(players):
                if p.get("bankrupt"):
                    continue
                if p.get("position") == i:
                    dx = x + 3 + (pi % 4) * (w // 4)
                    dy = y + h - 10 - (pi // 4) * 10
                    pc = PLAYER_COLORS[pi % len(PLAYER_COLORS)]
                    self.canvas.create_oval(dx, dy, dx + 8, dy + 8, fill=pc, outline="#333")

    def render_players(self):
        if not self.game_state:
            return
        players = self.game_state.get("players", [])
        ct = self.game_state.get("current_turn", 0)
        y = 10
        for idx, p in enumerate(players):
            if p.get("bankrupt"):
                continue
            is_current = idx == ct
            is_me = p.get("id") == self.my_pid
            bg = "#d4fcd4" if is_current else "#f0f0f0"
            self.players_canvas.create_rectangle(0, y, INFO_WIDTH - 10, y + 75,
                                                   fill=bg, outline="")
            c = PLAYER_COLORS[idx % len(PLAYER_COLORS)]
            self.players_canvas.create_oval(10, y + 8, 26, y + 24, fill=c, outline="#333")
            name = p.get("name", f"玩家{idx}")
            if is_me:
                name += " (你)"
            self.players_canvas.create_text(32, y + 6, text=name, font=self.font_md, fill="#000", anchor="nw")
            self.players_canvas.create_text(32, y + 22, text=f"\U0001f4b0 ${p.get('money', 0)}",
                                             font=self.font_sm, fill="#070", anchor="nw")
            props = p.get("properties", [])
            self.players_canvas.create_text(32, y + 38, text=f"\U0001f3e0 {len(props)}块地",
                                             font=self.font_sm, fill="#888", anchor="nw")
            if p.get("in_jail"):
                self.players_canvas.create_text(INFO_WIDTH - 30, y + 10, text="\U0001f512",
                                                 font=self.font_md, fill="#c00")
            y += 80

    def render_info(self):
        pass

    def render_toast(self):
        if self.toast_text:
            x = BOARD_SIZE // 2
            y = BOARD_SIZE - 40
            tw = len(self.toast_text) * 8 + 20
            self.canvas.create_rectangle(x - tw // 2, y - 15, x + tw // 2, y + 15,
                                           fill="#333", outline="")
            self.canvas.create_text(x, y, text=self.toast_text, font=self.font_md, fill="white")

    def render_decision(self):
        if not self.pending_decision:
            return
        dec = self.pending_decision
        if dec.get("decision") == "buy_property":
            x = BOARD_SIZE // 2
            y = BOARD_SIZE // 2
            self.canvas.create_rectangle(x - 180, y - 50, x + 180, y + 60,
                                           fill="white", outline="#333", width=2)
            msg = dec.get("message", "")
            self.canvas.create_text(x, y - 30, text=msg, font=self.font_sm, fill="#333")
            self.canvas.create_rectangle(x - 100, y + 5, x - 10, y + 40,
                                           fill="#4caf50", outline="")
            self.canvas.create_text(x - 55, y + 22, text="购买 [B]", font=self.font_sm, fill="white")
            self.canvas.create_rectangle(x + 10, y + 5, x + 100, y + 40,
                                           fill="#f44336", outline="")
            self.canvas.create_text(x + 55, y + 22, text="跳过 [N]", font=self.font_sm, fill="white")

    def render_card(self):
        if not self.card_animation:
            return
        card = self.card_animation
        x = BOARD_SIZE // 2
        y = BOARD_SIZE // 2
        self.canvas.create_rectangle(x - 170, y - 80, x + 170, y + 50,
                                       fill="#1a1a2e", outline="#e94560", width=2)
        text = card.get("text", "")
        lines = []
        while text:
            if len(text) > 20:
                idx = text.rfind(" ", 0, 21)
                if idx == -1:
                    idx = 20
                lines.append(text[:idx])
                text = text[idx:].strip()
            else:
                lines.append(text)
                break
        ty = y - 50
        for line in lines:
            self.canvas.create_text(x, ty, text=line, font=self.font_sm, fill="white")
            ty += 20
        self.canvas.create_text(x, y + 30, text="点击关闭", font=self.font_sm, fill="#888")

    def handle_message(self, msg):
        t = msg.get("type")
        if t == "join_game":
            self.my_pid = msg.get("pid")
            self.add_message(f"已加入游戏，ID: {self.my_pid}")

        elif t == "player_joined":
            self.lobby_players = msg.get("players", [])
            self.add_message(f"{msg.get('name')} 加入了游戏")

        elif t == "game_start":
            self.in_lobby = False
            self.game_state = {"players": msg.get("players", []),
                                "current_turn": 0, "turn_phase": "playing"}
            self.add_message("游戏开始！")

        elif t == "state_update":
            self.game_state = msg

        elif t == "your_turn":
            self.show_toast("轮到你了！按 D 掷骰子")
            if msg.get("in_jail"):
                jail_msgs = []
                if msg.get("can_pay"):
                    jail_msgs.append("P=交$50")
                if msg.get("has_card"):
                    jail_msgs.append("C=出狱卡")
                extra = " | ".join(jail_msgs)
                self.show_toast(f"你在监狱中！D=掷骰子 | {extra}")

        elif t == "dice_result":
            dice = msg.get("dice", [0, 0])
            self.add_message(msg.get("text", f"掷出 {dice[0]}+{dice[1]}"))

        elif t == "system_message":
            self.add_message(msg.get("text", ""))

        elif t == "chat":
            self.add_message(f"{msg.get('name')}: {msg.get('text')}")

        elif t == "card_drawn":
            self.card_animation = msg
            self.add_message(msg.get("text", "抽到卡片"))

        elif t == "prompt_decision":
            if msg.get("decision") == "buy_property":
                self.pending_decision = msg
                self.show_toast("按 B 购买 | 按 N 跳过")

        elif t == "prompt_start":
            self.add_message("输入 /start 开始游戏")

        elif t == "error":
            self.add_message(f"错误: {msg.get('message')}")

        elif t == "auction_update":
            self.add_message(f"拍卖: {msg.get('bidder_name')} 出价 ${msg.get('bid')}")

        elif t == "go_to_jail":
            self.add_message(msg.get("text", "去了监狱！"))

        elif t == "game_over":
            self.add_message(f"游戏结束！胜者: {msg.get('winner_name')}")
            self.show_toast(f"游戏结束！{msg.get('winner_name')} 获胜！")

        elif t == "turn_options":
            pass

    def run(self):
        self.root.mainloop()
