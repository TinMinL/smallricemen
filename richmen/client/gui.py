import pygame
import asyncio
import random
from common.constants import *

TILE_SIZE = 70
BOARD_PADDING = 10
INFO_WIDTH = 300
SIDE_TILES = 11
BOARD_SIZE = TILE_SIZE * SIDE_TILES
SCREEN_WIDTH = BOARD_SIZE + INFO_WIDTH + BOARD_PADDING * 3
SCREEN_HEIGHT = BOARD_SIZE + BOARD_PADDING * 2

PLAYER_COLORS = [(255, 50, 50), (50, 50, 255), (50, 200, 50), (255, 200, 0), (255, 0, 255), (0, 255, 255), (255, 150, 0), (128, 0, 128)]

class MonopolyGUI:
    def __init__(self, client):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("大富翁 - RichMen")
        self.font = pygame.font.SysFont("simhei", 12)
        self.font_small = pygame.font.SysFont("simhei", 10)
        self.font_title = pygame.font.SysFont("simhei", 16)
        self.font_large = pygame.font.SysFont("simhei", 20)
        self.clock = pygame.time.Clock()
        self.client = client
        self.game_state = None
        self.my_pid = None
        self.my_name = "玩家"
        self.messages = []
        self.input_text = ""
        self.show_input = False
        self.pending_decision = None
        self.auction_bid = 0
        self.connected = False
        self.in_lobby = True
        self.lobby_players = []
        self.card_animation = None
        self.toast_message = None
        self.toast_timer = 0
        self.player_tokens = {}
        self.offset_x = BOARD_PADDING
        self.offset_y = BOARD_PADDING

    def get_tile_pos(self, index):
        if index == 0:
            return (self.offset_x + TILE_SIZE * (SIDE_TILES - 1), self.offset_y + TILE_SIZE * (SIDE_TILES - 1))
        if 1 <= index <= 9:
            return (self.offset_x + TILE_SIZE * (SIDE_TILES - 1 - index), self.offset_y + TILE_SIZE * (SIDE_TILES - 1))
        if index == 10:
            return (self.offset_x, self.offset_y + TILE_SIZE * (SIDE_TILES - 1))
        if 11 <= index <= 19:
            return (self.offset_x, self.offset_y + TILE_SIZE * (SIDE_TILES - 1 - (index - 10)))
        if index == 20:
            return (self.offset_x, self.offset_y)
        if 21 <= index <= 29:
            return (self.offset_x + TILE_SIZE * (index - 20), self.offset_y)
        if index == 30:
            return (self.offset_x + TILE_SIZE * (SIDE_TILES - 1), self.offset_y)
        if 31 <= index <= 39:
            return (self.offset_x + TILE_SIZE * (SIDE_TILES - 1), self.offset_y + TILE_SIZE * (index - 30))
        return (0, 0)

    def draw_board(self):
        pygame.draw.rect(self.screen, (34, 139, 34), (self.offset_x - 2, self.offset_y - 2, BOARD_SIZE + 4, BOARD_SIZE + 4))
        pygame.draw.rect(self.screen, (200, 230, 200), (self.offset_x, self.offset_y, BOARD_SIZE, BOARD_SIZE))

        for tile in BOARD_TILES:
            self.draw_tile(tile)

        center_x = self.offset_x + BOARD_SIZE // 2
        center_y = self.offset_y + BOARD_SIZE // 2
        title = self.font_large.render("大富翁", True, (0, 0, 0))
        sub = self.font.render("RichMen", True, (100, 100, 100))
        self.screen.blit(title, (center_x - title.get_width() // 2, center_y - 30))
        self.screen.blit(sub, (center_x - sub.get_width() // 2, center_y))

    def draw_tile(self, tile):
        i = tile["index"]
        x, y = self.get_tile_pos(i)
        w, h = TILE_SIZE, TILE_SIZE

        is_corner = i in (0, 10, 20, 30)
        is_bottom = 1 <= i <= 9
        is_left = 11 <= i <= 19
        is_top = 21 <= i <= 29
        is_right = 31 <= i <= 39

        if is_corner:
            tw, th = w, h
            tx, ty = x, y
        elif is_bottom:
            tw, th = w, h
            tx, ty = x, y
        elif is_left:
            tw, th = w, h
            tx, ty = x, y
        elif is_top:
            tw, th = w, h
            tx, ty = x, y
        else:
            tw, th = w, h
            tx, ty = x, y

        rect = pygame.Rect(tx, ty, tw, th)

        if is_corner:
            pygame.draw.rect(self.screen, (255, 255, 200), rect)
            pygame.draw.rect(self.screen, (0, 0, 0), rect, 1)
            label = tile["name"]
            if len(label) > 4:
                label = label[:4]
            text = self.font_small.render(label, True, (0, 0, 0))
            self.screen.blit(text, (tx + tw // 2 - text.get_width() // 2, ty + th // 2 - text.get_height() // 2))
        else:
            color_strip_h = 15
            tile_type = tile.get("type")
            if tile_type == TILE_PROPERTY:
                group = tile.get("group", "brown")
                color = COLORS.get(group, (200, 200, 200))
                pygame.draw.rect(self.screen, color, (tx, ty, tw, color_strip_h))
            elif tile_type == TILE_RAILROAD:
                pygame.draw.rect(self.screen, (100, 100, 100), (tx, ty, tw, color_strip_h))
            elif tile_type == TILE_UTILITY:
                pygame.draw.rect(self.screen, (150, 200, 255), (tx, ty, tw, color_strip_h))
            elif tile_type == TILE_CHANCE:
                pygame.draw.rect(self.screen, (255, 200, 100), (tx, ty, tw, color_strip_h))
            elif tile_type == TILE_COMMUNITY_CHEST:
                pygame.draw.rect(self.screen, (255, 150, 150), (tx, ty, tw, color_strip_h))
            elif tile_type == TILE_TAX:
                pygame.draw.rect(self.screen, (200, 200, 200), (tx, ty, tw, color_strip_h))
            else:
                pygame.draw.rect(self.screen, (200, 200, 200), (tx, ty, tw, color_strip_h))

            pygame.draw.rect(self.screen, (0, 0, 0), rect, 1)

            name = tile["name"]
            if len(name) > 6:
                name = name[:6]
            text = self.font_small.render(name, True, (0, 0, 0))
            if is_bottom or is_top:
                self.screen.blit(text, (tx + tw // 2 - text.get_width() // 2, ty + color_strip_h + 2))
            else:
                self.screen.blit(text, (tx + 2, ty + color_strip_h + 2))

            if tile_type in (TILE_PROPERTY, TILE_RAILROAD, TILE_UTILITY):
                price = tile.get("price", 0)
                price_text = self.font_small.render(f"${price}", True, (0, 100, 0))
                if is_bottom or is_top:
                    self.screen.blit(price_text, (tx + tw // 2 - price_text.get_width() // 2, ty + th - 12))
                else:
                    self.screen.blit(price_text, (tx + 2, ty + th - 12))

    def draw_players(self):
        if not self.game_state:
            return
        players = self.game_state.get("players", [])
        for idx, p in enumerate(players):
            if p.get("bankrupt"):
                continue
            pos = p.get("position", 0)
            px, py = self.get_tile_pos(pos)
            tile = BOARD_TILES[pos]
            is_corner = pos in (0, 10, 20, 30)
            is_bottom = 1 <= pos <= 9
            is_left = 11 <= pos <= 19
            is_top = 21 <= pos <= 29

            if is_bottom:
                dx = px + 10 + (idx % 4) * 15
                dy = py + TILE_SIZE - 20 - (idx // 4) * 15
            elif is_left:
                dx = px + 5 + (idx // 4) * 15
                dy = py + 10 + (idx % 4) * 15
            elif is_top:
                dx = px + 5 + (idx % 4) * 15
                dy = py + 10 + (idx // 4) * 15
            elif is_right:
                dx = px + TILE_SIZE - 20 - (idx // 4) * 15
                dy = py + 10 + (idx % 4) * 15
            else:
                dx = px + 10 + (idx % 4) * 15
                dy = py + 10 + (idx // 4) * 15

            color = PLAYER_COLORS[idx % len(PLAYER_COLORS)]
            pygame.draw.circle(self.screen, color, (dx + 5, dy + 5), 7)
            pygame.draw.circle(self.screen, (0, 0, 0), (dx + 5, dy + 5), 7, 1)

            if self.my_pid == p.get("id"):
                pygame.draw.circle(self.screen, (255, 255, 255), (dx + 5, dy + 5), 3)

    def draw_info_panel(self):
        ix = self.offset_x + BOARD_SIZE + BOARD_PADDING
        iy = self.offset_y
        iw = INFO_WIDTH
        ih = BOARD_SIZE

        pygame.draw.rect(self.screen, (240, 240, 240), (ix, iy, iw, ih))
        pygame.draw.rect(self.screen, (0, 0, 0), (ix, iy, iw, ih), 2)

        if not self.game_state:
            return

        players = self.game_state.get("players", [])
        ct = self.game_state.get("current_turn", 0)

        y = iy + 10
        for idx, p in enumerate(players):
            if p.get("bankrupt"):
                continue
            color = PLAYER_COLORS[idx % len(PLAYER_COLORS)]
            is_current = idx == ct and self.game_state.get("turn_phase") != "waiting"
            is_me = p.get("id") == self.my_pid

            if is_current:
                pygame.draw.rect(self.screen, (200, 255, 200), (ix + 2, y, iw - 4, 80))

            pygame.draw.circle(self.screen, color, (ix + 15, y + 15), 8)
            name = p.get("name", f"玩家{idx}")
            if is_me:
                name += " (你)"
            name_text = self.font.render(name, True, (0, 0, 0))
            self.screen.blit(name_text, (ix + 30, y + 5))

            money_text = self.font.render(f"💰 ${p.get('money', 0)}", True, (0, 100, 0))
            self.screen.blit(money_text, (ix + 30, y + 22))

            props = p.get("properties", [])
            prop_text = self.font_small.render(f"🏠 {len(props)}块地", True, (100, 100, 100))
            self.screen.blit(prop_text, (ix + 30, y + 38))

            jail_icon = "🔒" if p.get("in_jail") else ""
            jail_text = self.font.render(jail_icon, True, (0, 0, 0))
            self.screen.blit(jail_text, (ix + iw - 30, y + 5))

            y += 85

        y += 10
        chat_y = iy + ih - 200
        pygame.draw.rect(self.screen, (255, 255, 255), (ix + 5, chat_y, iw - 10, 195))
        pygame.draw.rect(self.screen, (200, 200, 200), (ix + 5, chat_y, iw - 10, 195), 1)

        chat_label = self.font_small.render("聊天", True, (100, 100, 100))
        self.screen.blit(chat_label, (ix + 10, chat_y + 2))

        msgs = self.messages[-6:]
        my = chat_y + 18
        for m in msgs:
            text = self.font_small.render(m, True, (0, 0, 0))
            self.screen.blit(text, (ix + 10, my))
            my += 16

        if self.show_input:
            input_box = pygame.Rect(ix + 5, iy + ih - 28, iw - 10, 24)
            pygame.draw.rect(self.screen, (255, 255, 255), input_box)
            pygame.draw.rect(self.screen, (100, 100, 255), input_box, 2)
            input_render = self.font.render(self.input_text + "|", True, (0, 0, 0))
            self.screen.blit(input_render, (ix + 8, iy + ih - 24))

    def draw_toast(self):
        if self.toast_message and self.toast_timer > 0:
            alpha = min(255, self.toast_timer * 2)
            text = self.font_large.render(self.toast_message, True, (255, 255, 255))
            bg = pygame.Surface((text.get_width() + 20, text.get_height() + 10))
            bg.set_alpha(200)
            bg.fill((0, 0, 0))
            bx = SCREEN_WIDTH // 2 - bg.get_width() // 2
            by = SCREEN_HEIGHT // 2 - 50
            self.screen.blit(bg, (bx, by))
            self.screen.blit(text, (bx + 10, by + 5))
            self.toast_timer -= 1

    def show_toast(self, msg):
        self.toast_message = msg
        self.toast_timer = 120

    def draw_lobby(self):
        self.screen.fill((34, 139, 34))
        title = self.font_large.render("大富翁 - RichMen", True, (255, 255, 255))
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))

        sub = self.font.render("等待玩家加入...", True, (200, 255, 200))
        self.screen.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 90))

        y = 150
        for p in self.lobby_players:
            text = self.font.render(f"  {p.get('name', '未知')}", True, (255, 255, 255))
            self.screen.blit(text, (SCREEN_WIDTH // 2 - 100, y))
            y += 30

        if self.connected:
            hint = self.font.render("输入 /start 开始游戏 (至少2人) | Enter 聊天", True, (200, 255, 200))
            self.screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT - 100))

        if self.show_input:
            input_box = pygame.Rect(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT - 60, 300, 30)
            pygame.draw.rect(self.screen, (255, 255, 255), input_box)
            input_render = self.font.render(self.input_text + "|", True, (0, 0, 0))
            self.screen.blit(input_render, (input_box.x + 5, input_box.y + 5))

    def draw_decision(self):
        if not self.pending_decision:
            return
        dec = self.pending_decision
        if dec.get("decision") == "buy_property":
            s = pygame.Surface((400, 200), pygame.SRCALPHA)
            s.fill((0, 0, 0, 200))
            self.screen.blit(s, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 100))

            text = self.font_large.render(dec.get("message", ""), True, (255, 255, 255))
            self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2 - 70))

            buy_btn = pygame.Rect(SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT // 2, 100, 40)
            skip_btn = pygame.Rect(SCREEN_WIDTH // 2 + 20, SCREEN_HEIGHT // 2, 100, 40)
            pygame.draw.rect(self.screen, (0, 200, 0), buy_btn)
            pygame.draw.rect(self.screen, (200, 0, 0), skip_btn)

            buy_text = self.font.render("购买", True, (255, 255, 255))
            skip_text = self.font.render("跳过", True, (255, 255, 255))
            self.screen.blit(buy_text, (buy_btn.x + 50 - buy_text.get_width() // 2, buy_btn.y + 20 - buy_text.get_height() // 2))
            self.screen.blit(skip_text, (skip_btn.x + 50 - skip_text.get_width() // 2, skip_btn.y + 20 - skip_text.get_height() // 2))

            return buy_btn, skip_btn
        return None, None

    def draw_card_animation(self):
        if not self.card_animation:
            return
        card = self.card_animation
        s = pygame.Surface((350, 250), pygame.SRCALPHA)
        s.fill((0, 0, 0, 220))
        self.screen.blit(s, (SCREEN_WIDTH // 2 - 175, SCREEN_HEIGHT // 2 - 125))

        text = self.font_large.render(card.get("text", ""), True, (255, 255, 255))
        self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2 - 40))

        close_text = self.font.render("点击任意键关闭", True, (200, 200, 200))
        self.screen.blit(close_text, (SCREEN_WIDTH // 2 - close_text.get_width() // 2, SCREEN_HEIGHT // 2 + 40))

    def render(self):
        if self.in_lobby:
            self.draw_lobby()
        else:
            self.draw_board()
            self.draw_players()
            self.draw_info_panel()

        btns = self.draw_decision()
        self.draw_card_animation()
        self.draw_toast()
        self.clock.tick(30)

    def add_message(self, text):
        self.messages.append(text)
        if len(self.messages) > 50:
            self.messages = self.messages[-50:]

    async def handle_click(self, pos):
        if self.pending_decision:
            dec = self.pending_decision
            if dec.get("decision") == "buy_property":
                buy_btn = pygame.Rect(SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT // 2, 100, 40)
                skip_btn = pygame.Rect(SCREEN_WIDTH // 2 + 20, SCREEN_HEIGHT // 2, 100, 40)
                if buy_btn.collidepoint(pos):
                    await self.client.send({"type": "decision_response", "decision": "buy_property", "accepted": True})
                    self.pending_decision = None
                elif skip_btn.collidepoint(pos):
                    await self.client.send({"type": "decision_response", "decision": "buy_property", "accepted": False})
                    self.pending_decision = None

    async def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if self.show_input:
                            if self.input_text.startswith("/"):
                                cmd = self.input_text[1:].strip().lower()
                                if cmd == "start":
                                    await self.client.send({"type": "start_game"})
                                elif cmd == "dice" or cmd == "roll":
                                    await self.client.send({"type": MessageType.ROLL_DICE})
                                elif cmd == "end":
                                    await self.client.send({"type": MessageType.END_TURN})
                                elif cmd.startswith("bid "):
                                    try:
                                        bid = int(cmd.split()[1])
                                        await self.client.send({"type": MessageType.AUCTION_BID, "bid": bid})
                                    except:
                                        pass
                            elif self.input_text:
                                await self.client.send({"type": MessageType.CHAT, "text": self.input_text})
                            self.input_text = ""
                            self.show_input = False
                        else:
                            self.show_input = True
                    elif event.key == pygame.K_ESCAPE:
                        self.show_input = False
                        self.card_animation = None
                        self.input_text = ""
                    elif self.show_input:
                        if event.key == pygame.K_BACKSPACE:
                            self.input_text = self.input_text[:-1]
                        else:
                            if len(self.input_text) < 30:
                                self.input_text += event.unicode
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.card_animation:
                        self.card_animation = None
                    elif not self.show_input:
                        await self.handle_click(event.pos)

                if not self.show_input and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_d:
                        await self.client.send({"type": MessageType.ROLL_DICE})
                    elif event.key == pygame.K_e:
                        await self.client.send({"type": MessageType.END_TURN})
                    elif event.key == pygame.K_b and self.pending_decision:
                        dec = self.pending_decision
                        if dec.get("decision") == "buy_property":
                            await self.client.send({"type": "decision_response", "decision": "buy_property", "accepted": True})
                            self.pending_decision = None
                    elif event.key == pygame.K_n and self.pending_decision:
                        dec = self.pending_decision
                        if dec.get("decision") == "buy_property":
                            await self.client.send({"type": "decision_response", "decision": "buy_property", "accepted": False})
                            self.pending_decision = None

            self.render()
            pygame.display.flip()
            await asyncio.sleep(0)

        pygame.quit()
