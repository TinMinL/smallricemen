import asyncio
import random
from common.constants import *

BOT_DELAY_MIN = 0.5
BOT_DELAY_MAX = 2.0

class BotAI:
    def __init__(self, server, player_id, difficulty="normal"):
        self.server = server
        self.pid = player_id
        self.difficulty = difficulty

    async def delay(self):
        await asyncio.sleep(random.uniform(BOT_DELAY_MIN, BOT_DELAY_MAX))

    def player(self):
        return self.server.game.get_player(self.pid)

    def should_buy(self, price, tile_index):
        p = self.player()
        if not p:
            return False
        reserve = 300 if self.difficulty == "easy" else 100
        return p.money >= price + reserve

    def max_bid(self, tile_index):
        tile = next((t for t in BOARD_TILES if t["index"] == tile_index), None)
        if not tile:
            return 0
        p = self.player()
        if not p:
            return 0
        max_price = tile.get("price", 0)
        if self.difficulty == "easy":
            return int(max_price * 0.5)
        elif self.difficulty == "hard":
            return int(max_price * 0.9)
        return int(max_price * 0.7)

    def should_build(self):
        p = self.player()
        if not p or p.money < 200:
            return None
        for group, indices in PROPERTY_GROUPS.items():
            if not all(i in p.properties for i in indices):
                continue
            for i in indices:
                if p.money < 200:
                    return None
                if self.server.game.can_build_house(i, p):
                    return i
        return None

    def should_sell_for_cash(self, needed):
        p = self.player()
        if not p:
            return []
        actions = []
        for prop in list(p.properties):
            if p.money >= needed:
                break
            tile = next((t for t in BOARD_TILES if t["index"] == prop), None)
            if not tile:
                continue
            if p.houses.get(prop, 0) > 0 or prop in p.hotels:
                if self.server.game.can_sell_house(prop, p):
                    actions.append(("sell_house", prop))
            elif p.money < needed:
                actions.append(("mortgage", prop))
        return actions

    async def handle_turn(self):
        await self.delay()
        p = self.player()
        if not p or p.bankrupt:
            return

        if p.in_jail:
            if p.get_out_of_jail_cards > 0:
                await self.server.handle_use_get_out_of_jail(self.pid)
                await self.delay()
            elif p.money >= 50 and self.difficulty != "hard":
                await self.server.handle_pay_jail_fine(self.pid)
                await self.delay()
            await self.server.handle_roll_dice(self.pid)
        else:
            build = self.should_build()
            if build is not None:
                await self.server.handle_build_house(self.pid, {"tile_index": build})
                await self.delay()
            await self.server.handle_roll_dice(self.pid)

    async def handle_buy_decision(self, msg):
        await self.delay()
        tile_index = msg.get("tile_index")
        price = msg.get("price", 0)
        if self.should_buy(price, tile_index):
            await self.server.handle_buy_property(self.pid)
        else:
            await self.server.handle_decision_response(self.pid, {"decision": "buy_property", "accepted": False})

    async def handle_end_turn(self):
        await self.delay()
        await self.server.handle_end_turn(self.pid)

    async def handle_bankruptcy(self):
        p = self.player()
        if not p:
            return
        actions = self.should_sell_for_cash(0)
        for action, prop in actions:
            if p.money >= 0:
                break
            if action == "sell_house":
                await self.server.handle_sell_house(self.pid, {"tile_index": prop})
                await self.delay()
            elif action == "mortgage":
                await self.server.handle_mortgage(self.pid, {"tile_index": prop})
                await self.delay()
        if p.money < 0:
            p.bankrupt = True

    @staticmethod
    def bot_name(pid, index):
        names = ["电脑小智", "电脑阿福", "电脑大亨", "电脑财运", "电脑金库", "电脑富豪", "电脑赢家"]
        return names[(index - 1) % len(names)]
