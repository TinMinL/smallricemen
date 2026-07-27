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
    def __init__(self, client, loop=None):
        self.client = client
        self.loop = loop or asyncio.get_event_loop()
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

        self.root.configure(bg="#1a1a2e")
        self.frame = tk.Frame(self.root, bg="#1a1a2e")
        self.frame.pack(fill="both", expand=True)

        board_container = tk.Frame(self.frame, bg="#1a1a2e", highlightbackground="#16213e",
                                    highlightthickness=3, padx=4, pady=4)
        board_container.place(x=PAD, y=PAD)

        self.canvas = tk.Canvas(board_container, width=BOARD_SIZE, height=BOARD_SIZE,
                                 bg="#1b5e20", highlightthickness=0)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.on_click)

        info_border = tk.Frame(self.frame, bg="#1a1a2e", highlightbackground="#0f3460",
                                highlightthickness=3, padx=3, pady=3)
        info_border.place(x=PAD * 2 + BOARD_SIZE, y=PAD, width=INFO_WIDTH + 6, height=BOARD_SIZE + 6)

        self.info_frame = tk.Frame(info_border, width=INFO_WIDTH, bg="#e8ddd0")
        self.info_frame.pack(fill="both", expand=True)
        self.info_frame.pack_propagate(False)

        header = tk.Frame(self.info_frame, bg="#3d2b1f", height=32)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="🎲 大富翁", font=self.font_md,
                 bg="#3d2b1f", fg="#f5e6d0").pack(side="left", padx=8, pady=4)

        self.toolbar = tk.Frame(self.info_frame, bg="#3d2b1f", height=36)
        self.toolbar.pack(fill="x")
        self.toolbar.pack_propagate(False)

        self.btn_style = {"font": self.font_sm, "bd": 0, "relief": "flat",
                          "activeforeground": "white", "padx": 6, "pady": 4,
                          "cursor": "hand2"}

        self.btn_roll = tk.Button(self.toolbar, text="🎲 掷骰子", command=self.cmd_roll,
                                   bg="#2e7d32", fg="white", activebackground="#388e3c", **self.btn_style)
        self.btn_end = tk.Button(self.toolbar, text="⏹ 结束", command=self.cmd_end_turn,
                                  bg="#e65100", fg="white", activebackground="#ef6c00", **self.btn_style)
        self.btn_buy = tk.Button(self.toolbar, text="💰 购买", command=self.cmd_buy,
                                  bg="#2e7d32", fg="white", activebackground="#388e3c", **self.btn_style)
        self.btn_skip = tk.Button(self.toolbar, text="⏭ 跳过", command=self.cmd_skip,
                                   bg="#c62828", fg="white", activebackground="#d32f2f", **self.btn_style)
        self.btn_addbot = tk.Button(self.toolbar, text="🤖 +电脑", command=self.cmd_addbot,
                                     bg="#4527a0", fg="white", activebackground="#512da8", **self.btn_style)
        self.btn_start = tk.Button(self.toolbar, text="▶ 开始", command=self.cmd_start,
                                    bg="#1565c0", fg="white", activebackground="#1976d2", **self.btn_style)

        self.players_canvas = tk.Canvas(self.info_frame, bg="#f5efe6",
                                         highlightthickness=0, height=320)
        self.players_canvas.pack(fill="x", padx=5, pady=5)
        self.players_canvas.bind("<Button-1>", self.on_players_click)

        sep = tk.Frame(self.info_frame, bg="#c0b090", height=1)
        sep.pack(fill="x", padx=8)

        chat_header = tk.Label(self.info_frame, text="💬 聊天", font=self.font_sm,
                                bg="#e8ddd0", fg="#5d4037")
        chat_header.pack(anchor="w", padx=8, pady=(4, 0))

        self.chat_frame = tk.Frame(self.info_frame, bg="#faf6f0",
                                    highlightbackground="#d7ccc8", highlightthickness=1)
        self.chat_frame.pack(fill="both", expand=True, padx=5, pady=(2, 3))

        self.chat_text = tk.Text(self.chat_frame, font=self.font_sm, bg="#faf6f0",
                                  fg="#3e2723", wrap="word", state="disabled",
                                  highlightthickness=0, borderwidth=0)
        self.chat_text.pack(fill="both", expand=True, padx=3, pady=3)

        self.input_var = tk.StringVar()
        input_frame = tk.Frame(self.info_frame, bg="#e8ddd0")
        input_frame.pack(fill="x", padx=5, pady=(0, 5))
        self.input_entry = tk.Entry(input_frame, textvariable=self.input_var,
                                     font=self.font_md, bg="#faf6f0", fg="#3e2723",
                                     highlightbackground="#a1887f", highlightthickness=1,
                                     relief="flat")
        self.input_entry.pack(fill="x", ipady=2)
        self.input_entry.bind("<Return>", self.on_chat_submit)
        self.input_entry.bind("<Escape>", lambda e: self.root.focus_set())
        self.input_entry.bind("<FocusIn>", lambda e: self.root.after(50, self.check_input_focus))

        self.input_active = False

        self.root.after(100, self.render_loop)

    def check_input_focus(self):
        pass

    def cmd_addbot(self):
        asyncio.run_coroutine_threadsafe(
            self.client.send({"type": "add_bot", "count": 1}), self.loop)
        self.add_message("添加 1 个电脑玩家")

    def cmd_start(self):
        asyncio.run_coroutine_threadsafe(
            self.client.send({"type": "start_game"}), self.loop)

    def update_buttons(self):
        for b in (self.btn_roll, self.btn_end, self.btn_buy, self.btn_skip,
                  self.btn_addbot, self.btn_start):
            b.pack_forget()
        if hasattr(self, 'btn_pay'):
            self.btn_pay.pack_forget()
            self.btn_card.pack_forget()

        if self.in_lobby or not self.game_state:
            self.btn_addbot.pack(side="left", padx=2, pady=3)
            has_humans = self.my_pid is not None
            player_count = len(self.lobby_players) if self.lobby_players else 0
            if has_humans and player_count >= 2:
                self.btn_start.pack(side="left", padx=2, pady=3)
            return

        turn_phase = self.game_state.get("turn_phase", "")
        players = self.game_state.get("players", [])
        ct = self.game_state.get("current_turn", 0)
        is_my_turn = False
        my_player = None
        for idx, p in enumerate(players):
            if p.get("id") == self.my_pid and not p.get("bankrupt"):
                is_my_turn = idx == ct
                my_player = p
                break

        if not is_my_turn:
            return

        if turn_phase == "roll":
            if my_player and my_player.get("in_jail"):
                self.btn_roll.pack(side="left", padx=2, pady=3)
                if not hasattr(self, 'btn_pay'):
                    self.btn_pay = tk.Button(self.toolbar, text="🔓 交$50", command=self.cmd_pay_jail, **self.btn_style)
                    self.btn_card = tk.Button(self.toolbar, text="🃏 出狱卡", command=self.cmd_use_card, **self.btn_style)
                if my_player.get("money", 0) >= 50:
                    self.btn_pay.pack(side="left", padx=2, pady=3)
                if my_player.get("get_out_of_jail_cards", 0) > 0:
                    self.btn_card.pack(side="left", padx=2, pady=3)
            else:
                self.btn_roll.pack(side="left", padx=2, pady=3)

        elif turn_phase == "buy_decision" or self.pending_decision:
            self.btn_buy.pack(side="left", padx=2, pady=3)
            self.btn_skip.pack(side="left", padx=2, pady=3)

        elif turn_phase == "end":
            self.btn_end.pack(side="left", padx=2, pady=3)

    def cmd_roll(self):
        if not self.input_entry.focus_get() is self.input_entry:
            asyncio.run_coroutine_threadsafe(
                self.client.send({"type": "roll_dice"}), self.loop)

    def cmd_end_turn(self):
        if not self.input_entry.focus_get() is self.input_entry:
            asyncio.run_coroutine_threadsafe(
                self.client.send({"type": "end_turn"}), self.loop)

    def cmd_buy(self):
        if self.pending_decision and self.pending_decision.get("decision") == "buy_property":
            asyncio.run_coroutine_threadsafe(
                self.client.send({"type": "decision_response", "decision": "buy_property", "accepted": True}), self.loop)
            self.pending_decision = None

    def cmd_skip(self):
        if self.pending_decision and self.pending_decision.get("decision") == "buy_property":
            asyncio.run_coroutine_threadsafe(
                self.client.send({"type": "decision_response", "decision": "buy_property", "accepted": False}), self.loop)
            self.pending_decision = None

    def cmd_pay_jail(self):
        asyncio.run_coroutine_threadsafe(
            self.client.send({"type": "pay_jail_fine"}), self.loop)

    def cmd_use_card(self):
        asyncio.run_coroutine_threadsafe(
            self.client.send({"type": "use_get_out_of_jail"}), self.loop)

    def on_players_click(self, event):
        if self.card_animation:
            self.card_animation = None
            return
        x, y = event.x, event.y
        if not self.game_state:
            return
        players = self.game_state.get("players", [])
        row = y // 80
        if 0 <= row < len(players):
            p = players[row]
            if p.get("bankrupt"):
                return
            props = p.get("properties", [])
            names = []
            for pi in props:
                tile = next((t for t in BOARD_TILES if t["index"] == pi), None)
                if tile:
                    names.append(tile["name"])
            info = f"{p.get('name')} | 💰 ${p.get('money')} | 🏠 {len(props)}块地"
            if names:
                info += "\n" + " ".join(names)
            self.show_toast(info)

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
                    self.cmd_buy()
                elif cx + 20 <= x <= cx + 120 and cy <= y <= cy + 40:
                    self.cmd_skip()

    def on_chat_submit(self, event):
        text = self.input_var.get().strip()
        if not text:
            return
        if text.startswith("/"):
            cmd = text[1:].strip().lower()
            if cmd == "start":
                asyncio.run_coroutine_threadsafe(
                    self.client.send({"type": "start_game"}), self.loop)
            elif cmd in ("dice", "roll"):
                asyncio.run_coroutine_threadsafe(
                    self.client.send({"type": "roll_dice"}), self.loop)
            elif cmd == "end":
                asyncio.run_coroutine_threadsafe(
                    self.client.send({"type": "end_turn"}), self.loop)
            elif cmd.startswith("bid "):
                try:
                    bid = int(cmd.split()[1])
                    asyncio.run_coroutine_threadsafe(
                        self.client.send({"type": "auction_bid", "bid": bid}), self.loop)
                except:
                    self.add_message("用法: /bid <金额>")
            elif cmd == "buy":
                asyncio.run_coroutine_threadsafe(
                    self.client.send({"type": "decision_response", "decision": "buy_property", "accepted": True}), self.loop)
                self.pending_decision = None
            elif cmd == "skip":
                asyncio.run_coroutine_threadsafe(
                    self.client.send({"type": "decision_response", "decision": "buy_property", "accepted": False}), self.loop)
                self.pending_decision = None
            elif cmd.startswith("addbot") or cmd.startswith("bot"):
                try:
                    count = int(cmd.split()[1]) if len(cmd.split()) > 1 else 1
                    asyncio.run_coroutine_threadsafe(
                        self.client.send({"type": "add_bot", "count": count}), self.loop)
                    self.add_message(f"添加 {count} 个电脑玩家")
                except:
                    self.add_message(f"用法: /bot <数量>")
            else:
                self.add_message(f"未知命令: /{cmd}")
        else:
            asyncio.run_coroutine_threadsafe(
                self.client.send({"type": "chat", "text": text}), self.loop)
        self.input_var.set("")

    def on_key(self, event):
        if self.input_entry.focus_get() is self.input_entry:
            return
        if event.char in ("d", "D"):
            self.cmd_roll()
        elif event.char in ("e", "E"):
            self.cmd_end_turn()
        elif event.char in ("b", "B"):
            self.cmd_buy()
        elif event.char in ("n", "N"):
            self.cmd_skip()
        elif event.char in ("p", "P"):
            self.cmd_pay_jail()
        elif event.char in ("c", "C"):
            self.cmd_use_card()
        elif event.keysym == "Escape":
            self.card_animation = None

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
        self.update_buttons()

        self.root.after(50, self.render_loop)

    def render_lobby(self):
        self.canvas.create_rectangle(0, 0, BOARD_SIZE, BOARD_SIZE, fill="#16213e")
        self.canvas.create_oval(BOARD_SIZE // 2 - 100, BOARD_SIZE // 2 - 120,
                                 BOARD_SIZE // 2 + 100, BOARD_SIZE // 2 + 20,
                                 fill="#1a1a2e", outline="#0f3460", width=3)
        self.canvas.create_text(BOARD_SIZE // 2, BOARD_SIZE // 2 - 80,
                                 text="🎲 大富翁", font=self.font_xl, fill="#e94560")
        self.canvas.create_text(BOARD_SIZE // 2, BOARD_SIZE // 2 - 55,
                                 text="RichMen", font=self.font_md, fill="#a5d6a7")
        self.canvas.create_text(BOARD_SIZE // 2, BOARD_SIZE // 2 - 25,
                                 text="等待玩家加入...", font=self.font_md, fill="#888")
        y = BOARD_SIZE // 2 + 10
        for p in self.lobby_players:
            is_bot = p.get("is_bot", False)
            icon = "🤖" if is_bot else "👤"
            name = p.get('name', '未知')
            self.canvas.create_text(BOARD_SIZE // 2 - 60, y, text=f"{icon} {name}",
                                     font=self.font_md, fill="white", anchor="w")
            y += 28
        self.canvas.create_text(BOARD_SIZE // 2, BOARD_SIZE - 30,
                                 text="点击按钮或输入 /start 开始",
                                 font=self.font_sm, fill="#555")

    def render_board(self):
        self.canvas.create_rectangle(0, 0, BOARD_SIZE, BOARD_SIZE, fill="#1b5e20")
        self.canvas.create_rectangle(2, 2, BOARD_SIZE - 2, BOARD_SIZE - 2, fill="#2e7d32", outline="#4caf50", width=1)
        for tile in BOARD_TILES:
            self.render_tile(tile)

        cx, cy = BOARD_SIZE // 2, BOARD_SIZE // 2
        self.canvas.create_oval(cx - 80, cy - 80, cx + 80, cy + 80, fill="#1b5e20", outline="#4caf50", width=4)
        self.canvas.create_oval(cx - 72, cy - 72, cx + 72, cy + 72, fill="#1b5e20", outline="#388e3c", width=1)
        self.canvas.create_text(cx, cy - 18, text="大富翁", font=self.font_lg, fill="#ffffff")
        self.canvas.create_text(cx, cy + 8, text="RichMen", font=self.font_sm, fill="#a5d6a7")
        self.canvas.create_text(cx, cy + 28, text="▼", font=("", 6), fill="#4caf50")

    def render_tile(self, tile):
        i = tile["index"]
        x, y = BOARD_COORDS[i]
        w, h = TILE_SIZE, TILE_SIZE
        is_corner = i in (0, 10, 20, 30)
        strip_h = 14
        inner = 1

        if is_corner:
            self.canvas.create_rectangle(x, y, x + w, y + h, fill="#f5deb3", outline="#555", width=2)
            cx, cy = x + w // 2, y + h // 2
            self.canvas.create_oval(cx - 18, cy - 18, cx + 18, cy + 18, fill="#e8c896", outline="#b8956a", width=1)
            name = tile["name"]
            nf = self.font_sm if len(name) <= 4 else tkfont.Font(size=7)
            self.canvas.create_text(cx, cy, text=name, font=nf, fill="#5d4037")
        else:
            tile_type = tile.get("type")
            if tile_type == TILE_PROPERTY:
                group = tile.get("group", "brown")
                c = COLORS.get(group, (200, 200, 200))
                hex_c = f"#{c[0]:02x}{c[1]:02x}{c[2]:02x}"
            elif tile_type == TILE_RAILROAD:
                hex_c = "#78909c"
            elif tile_type == TILE_UTILITY:
                hex_c = "#64b5f6"
            elif tile_type == TILE_CHANCE:
                hex_c = "#ffb74d"
            elif tile_type == TILE_COMMUNITY_CHEST:
                hex_c = "#ef9a9a"
            elif tile_type == TILE_TAX:
                hex_c = "#bdbdbd"
            else:
                hex_c = "#bdbdbd"

            self.canvas.create_rectangle(x + inner, y + inner, x + w - inner, y + h - inner,
                                          fill="#faf8f2", outline="#bbb", width=1)
            self.canvas.create_rectangle(x + inner, y + inner, x + w - inner, y + strip_h,
                                          fill=hex_c, outline="")

            is_h = 1 <= i <= 9 or 21 <= i <= 29
            name = tile["name"]
            if len(name) > 6:
                name = name[:5] + "."

            if is_h:
                self.canvas.create_text(x + w // 2, y + strip_h + 7, text=name,
                                         font=tkfont.Font(size=7), fill="#444")
            else:
                self.canvas.create_text(x + 3, y + strip_h + 6, text=name,
                                         font=tkfont.Font(size=7), fill="#444", anchor="nw")

            price = tile.get("price", 0)
            if price:
                self.canvas.create_text(x + w // 2, y + h - 4, text=f"${price}",
                                         font=tkfont.Font(size=7), fill="#2e7d32", anchor="s")

        game_state = self.game_state
        if game_state:
            players = game_state.get("players", [])
            r = 9
            for pi, p in enumerate(players):
                if p.get("bankrupt"):
                    continue
                if p.get("position") == i:
                    if is_corner:
                        dx = x + 3 + (pi % 3) * (r * 2 + 3)
                        dy = y + h - r * 2 - 3 - (pi // 3) * (r * 2 + 3)
                    else:
                        dx = x + 2 + (pi % 4) * (w // 4)
                        dy = y + h - 14 - (pi // 4) * 16
                    pc = PLAYER_COLORS[pi % len(PLAYER_COLORS)]
                    self.canvas.create_oval(dx, dy, dx + r * 2, dy + r * 2, fill=pc, outline="white", width=2)
                    self.canvas.create_text(dx + r, dy + r, text=str(pi + 1),
                                             font=tkfont.Font(size=8, weight="bold"), fill="white")

    def render_players(self):
        if not self.game_state:
            return
        players = self.game_state.get("players", [])
        ct = self.game_state.get("current_turn", 0)
        y = 6
        for idx, p in enumerate(players):
            if p.get("bankrupt"):
                continue
            is_current = idx == ct
            is_me = p.get("id") == self.my_pid
            h = 62

            if is_current:
                self.players_canvas.create_rectangle(2, y, INFO_WIDTH - 14, y + h,
                                                      fill="#c8e6c9", outline="#66bb6a", width=2)
            else:
                self.players_canvas.create_rectangle(2, y, INFO_WIDTH - 14, y + h,
                                                      fill="#faf6f0", outline="#e0d5c5", width=1)

            c = PLAYER_COLORS[idx % len(PLAYER_COLORS)]
            self.players_canvas.create_oval(10, y + 8, 28, y + 26, fill=c, outline="white", width=2)
            self.players_canvas.create_text(19, y + 17, text=str(idx + 1),
                                             font=tkfont.Font(size=8, weight="bold"), fill="white")

            name = p.get("name", f"玩家{idx}")
            if is_me:
                name += " (你)"
            self.players_canvas.create_text(34, y + 5, text=name, font=self.font_md, fill="#3e2723", anchor="nw")

            money = p.get('money', 0)
            color_money = "#2e7d32" if money >= 0 else "#c62828"
            self.players_canvas.create_text(34, y + 22, text=f"💰 ${money}",
                                             font=self.font_sm, fill=color_money, anchor="nw")

            props = p.get("properties", [])
            houses = sum(p.get("houses", {}).values())
            hotels = len(p.get("hotels", {}))
            prop_info = f"🏠 {len(props)}块地"
            if houses:
                prop_info += f" 🏗{houses}"
            if hotels:
                prop_info += f" 🏨{hotels}"
            self.players_canvas.create_text(34, y + 38, text=prop_info,
                                             font=tkfont.Font(size=7), fill="#8d6e63", anchor="nw")

            jail_icon = "🔒" if p.get("in_jail") else ""
            if jail_icon:
                self.players_canvas.create_text(INFO_WIDTH - 30, y + 10, text=jail_icon,
                                                 font=self.font_md)
            if is_current:
                self.players_canvas.create_text(INFO_WIDTH - 30, y + h - 14, text="◀",
                                                 font=tkfont.Font(size=10), fill="#2e7d32")

            y += h + 4

    def render_info(self):
        pass

    def render_toast(self):
        if self.toast_text:
            x = BOARD_SIZE // 2
            y = BOARD_SIZE - 40
            tw = len(self.toast_text) * 7 + 30
            self.canvas.create_rectangle(x - tw // 2, y - 16, x + tw // 2, y + 16,
                                           fill="#263238", outline="#4caf50", width=2)
            self.canvas.create_text(x, y, text=self.toast_text, font=self.font_md, fill="#a5d6a7")

    def render_decision(self):
        if not self.pending_decision:
            return
        dec = self.pending_decision
        if dec.get("decision") == "buy_property":
            x = BOARD_SIZE // 2
            y = BOARD_SIZE // 2
            self.canvas.create_rectangle(x - 185, y - 55, x + 185, y + 65,
                                           fill="#faf6f0", outline="#5d4037", width=2)
            self.canvas.create_rectangle(x - 183, y - 53, x + 183, y + 63,
                                           fill="#faf6f0", outline="")
            msg = dec.get("message", "")
            self.canvas.create_text(x, y - 35, text=msg, font=self.font_sm, fill="#3e2723")

            self.canvas.create_rectangle(x - 100, y + 5, x - 10, y + 40,
                                           fill="#2e7d32", outline="")
            self.canvas.create_text(x - 55, y + 22, text="💰 购买", font=self.font_sm,
                                     fill="white")
            self.canvas.create_rectangle(x + 10, y + 5, x + 100, y + 40,
                                           fill="#c62828", outline="")
            self.canvas.create_text(x + 55, y + 22, text="⏭ 跳过", font=self.font_sm,
                                     fill="white")

    def render_card(self):
        if not self.card_animation:
            return
        card = self.card_animation
        x = BOARD_SIZE // 2
        y = BOARD_SIZE // 2
        is_chance = "机会" in card.get("text", "")
        border = "#ffb74d" if is_chance else "#ef9a9a"
        self.canvas.create_rectangle(x - 175, y - 85, x + 175, y + 55,
                                       fill="#1a1a2e", outline=border, width=3)
        self.canvas.create_rectangle(x - 172, y - 82, x + 172, y + 52,
                                       fill="#1a1a2e", outline=border, width=1)
        icon = "❓" if is_chance else "🏦"
        self.canvas.create_text(x, y - 65, text=icon, font=tkfont.Font(size=20))
        text = card.get("text", "")
        lines = []
        while text:
            if len(text) > 18:
                idx = text.rfind(" ", 0, 19)
                if idx == -1:
                    idx = 18
                lines.append(text[:idx])
                text = text[idx:].strip()
            else:
                lines.append(text)
                break
        ty = y - 30
        for line in lines:
            self.canvas.create_text(x, ty, text=line, font=self.font_md, fill="white")
            ty += 22
        self.canvas.create_text(x, y + 38, text="点击关闭", font=tkfont.Font(size=8), fill="#666")

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
            pid = msg.get("pid")
            pos = msg.get("position")
            if self.game_state and pid is not None and pos is not None:
                for p in self.game_state.get("players", []):
                    if p.get("id") == pid:
                        p["position"] = pos

        elif t == "system_message":
            self.add_message(msg.get("text", ""))

        elif t == "chat":
            self.add_message(f"{msg.get('name')}: {msg.get('text')}")

        elif t == "card_drawn":
            self.card_animation = msg
            self.add_message(msg.get("text", "抽到卡片"))
            pid = msg.get("pid")
            move_to = msg.get("move_to")
            if self.game_state and pid is not None and move_to is not None:
                for p in self.game_state.get("players", []):
                    if p.get("id") == pid:
                        p["position"] = move_to

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
