import asyncio
import json
import time
from common.protocol import MessageType, encode, decode
from server.game_logic import GameState

class GameServer:
    def __init__(self, host="0.0.0.0", port=8765):
        self.host = host
        self.port = port
        self.clients = {}
        self.player_ids = {}
        self.game = GameState()
        self.lock = asyncio.Lock()
        self.pending_decisions = {}
        self.auction_state = None

    async def handle_client(self, reader, writer):
        addr = writer.get_extra_info("peername")
        print(f"新连接: {addr}")
        pid = id(writer)
        self.clients[pid] = writer
        self.player_ids[writer] = pid

        try:
            while True:
                data = await reader.readline()
                if not data:
                    break
                msg = decode(data)
                await self.handle_message(pid, msg)
        except (ConnectionResetError, asyncio.IncompleteReadError, json.JSONDecodeError) as e:
            print(f"连接断开 {addr}: {e}")
        finally:
            await self.disconnect(pid)

    async def handle_message(self, pid, msg):
        async with self.lock:
            msg_type = msg.get("type")
            print(f"收到消息: {msg_type} 来自 {pid}")

            if msg_type == MessageType.JOIN_GAME:
                await self.handle_join(pid, msg)
            elif msg_type == MessageType.ROLL_DICE:
                await self.handle_roll_dice(pid)
            elif msg_type == MessageType.BUY_PROPERTY:
                await self.handle_buy_property(pid)
            elif msg_type == MessageType.AUCTION_BID:
                await self.handle_auction_bid(pid, msg)
            elif msg_type == MessageType.BUILD_HOUSE:
                await self.handle_build_house(pid, msg)
            elif msg_type == MessageType.SELL_HOUSE:
                await self.handle_sell_house(pid, msg)
            elif msg_type == MessageType.MORTGAGE:
                await self.handle_mortgage(pid, msg)
            elif msg_type == MessageType.UNMORTGAGE:
                await self.handle_unmortgage(pid, msg)
            elif msg_type == MessageType.TRADE_OFFER:
                await self.handle_trade_offer(pid, msg)
            elif msg_type == MessageType.TRADE_RESPONSE:
                await self.handle_trade_response(pid, msg)
            elif msg_type == MessageType.PAY_JAIL_FINE:
                await self.handle_pay_jail_fine(pid)
            elif msg_type == MessageType.USE_GET_OUT_OF_JAIL:
                await self.handle_use_get_out_of_jail(pid)
            elif msg_type == MessageType.END_TURN:
                await self.handle_end_turn(pid)
            elif msg_type == MessageType.CHAT:
                await self.handle_chat(pid, msg)
            elif msg_type == MessageType.DECISION_RESPONSE:
                await self.handle_decision_response(pid, msg)
            elif msg_type == "start_game":
                await self.handle_start_game(pid)

    async def handle_start_game(self, pid):
        if self.game.started:
            await self.send_to(pid, {"type": MessageType.ERROR, "message": "游戏已开始"})
            return
        if len(self.game.players) < 2:
            await self.send_to(pid, {"type": MessageType.ERROR, "message": "至少需要2名玩家"})
            return
        await self.start_game()

    async def handle_join(self, pid, msg):
        name = msg.get("name", f"玩家{pid % 100}")
        if self.game.started:
            await self.send_to(pid, {"type": MessageType.ERROR, "message": "游戏已开始"})
            return
        if any(p.id == pid for p in self.game.players):
            await self.send_to(pid, {"type": MessageType.ERROR, "message": "已加入"})
            return
        self.game.add_player(pid, name)
        await self.send_to(pid, {"type": MessageType.JOIN_GAME, "pid": pid, "name": name})
        await self.broadcast({"type": MessageType.PLAYER_JOINED, "pid": pid, "name": name, "players": [p.to_dict() for p in self.game.players]})

        if len(self.game.players) >= 2:
            await self.send_to(pid, {"type": "prompt_start", "message": "至少2名玩家，输入 /start 开始游戏"})

    async def handle_roll_dice(self, pid):
        player = self.game.get_player(pid)
        if not player or self.game.current_player().id != pid or player.bankrupt:
            return

        if player.in_jail:
            d1, d2 = self.game.roll_dice()
            rolled_doubles = d1 == d2
            player.jail_turns += 1
            if rolled_doubles:
                player.in_jail = False
                player.jail_turns = 0
                self.game.move_player(player, d1 + d2)
                await self.broadcast({"type": MessageType.DICE_RESULT, "pid": pid, "dice": [d1, d2], "doubles": True, "position": player.position, "text": f"{player.name} 掷出 {d1}+{d2}，出狱了！"})
                await self.handle_landing(pid, player)
            elif player.jail_turns >= JAIL_TURNS:
                player.money -= JAIL_FINE
                player.in_jail = False
                player.jail_turns = 0
                self.game.move_player(player, d1 + d2)
                await self.broadcast({"type": MessageType.DICE_RESULT, "pid": pid, "dice": [d1, d2], "position": player.position, "text": f"{player.name} 掷出 {d1}+{d2}，交罚款出狱"})
                await self.handle_landing(pid, player)
            else:
                await self.broadcast({"type": MessageType.DICE_RESULT, "pid": pid, "dice": [d1, d2], "jail_turns": player.jail_turns, "text": f"{player.name} 在监狱中，掷出 {d1}+{d2}"})
                self.game.turn_phase = "end"
                await self.send_turn_options(pid)
            return

        d1, d2 = self.game.roll_dice()
        steps = d1 + d2
        passed_go = self.game.move_player(player, steps)
        is_doubles = self.game.is_doubles()

        msg = {"type": MessageType.DICE_RESULT, "pid": pid, "dice": [d1, d2], "position": player.position, "text": f"{player.name} 掷出 {d1}+{d2}，走到 {self.game.board.get_tile(player.position)['name']}"}
        if passed_go:
            msg["passed_go"] = True
            msg["text"] += f"，经过GO获得${PASS_GO_MONEY}"
        if is_doubles:
            self.game.doubles_count += 1
            msg["doubles"] = True
            if self.game.doubles_count >= MAX_DOUBLES:
                player.in_jail = True
                player.position = 10
                msg["text"] = f"{player.name} 连续3次掷出双数，去监狱！"
                msg["go_to_jail"] = True
                msg["position"] = 10

        await self.broadcast(msg)

        if not player.in_jail:
            await self.handle_landing(pid, player)

    async def handle_landing(self, pid, player):
        index = player.position
        tile = self.game.board.get_tile(index)

        if tile["type"] == TILE_CHANCE:
            card = self.game.draw_chance(player)
            result = self.game.apply_card(card, player, self.game)
            await self.broadcast({"type": "card_drawn", "pid": pid, "card": result["card"], "text": result["text"], "money_change": result["money_change"], "go_to_jail": result["go_to_jail"], "move_to": result["move_to"]})
            if result["messages"]:
                for m in result["messages"]:
                    await self.broadcast({"type": "system_message", "text": m})
            if result["go_to_jail"]:
                await self.broadcast({"type": "system_message", "text": f"{player.name} 去监狱了！"})
                self.game.turn_phase = "end"
                await self.broadcast(self._state_update())
                await self.send_turn_options(pid)
                return

        elif tile["type"] == TILE_COMMUNITY_CHEST:
            card = self.game.draw_community_chest(player)
            result = self.game.apply_card(card, player, self.game)
            await self.broadcast({"type": "card_drawn", "pid": pid, "card": result["card"], "text": result["text"], "money_change": result["money_change"], "go_to_jail": result["go_to_jail"], "move_to": result["move_to"]})
            if result["messages"]:
                for m in result["messages"]:
                    await self.broadcast({"type": "system_message", "text": m})
            if result["go_to_jail"]:
                await self.broadcast({"type": "system_message", "text": f"{player.name} 去监狱了！"})
                self.game.turn_phase = "end"
                await self.broadcast(self._state_update())
                await self.send_turn_options(pid)
                return

        elif tile["type"] == TILE_TAX:
            player.money -= tile["amount"]
            await self.broadcast({"type": "system_message", "text": f"{player.name} 缴税 ${tile['amount']}"})

        elif tile["type"] == TILE_GO_TO_JAIL:
            player.in_jail = True
            player.jail_turns = 0
            player.position = 10
            await self.broadcast({"type": "system_message", "text": f"{player.name} 去了监狱！"})
            self.game.turn_phase = "end"
            await self.broadcast(self._state_update())
            await self.send_turn_options(pid)
            return

        elif tile["type"] in (TILE_PROPERTY, TILE_RAILROAD, TILE_UTILITY):
            owner = self.game.board.get_property_owner(index, self.game)
            if owner and owner.id != pid and not owner.bankrupt:
                rent = self.game.calculate_rent(index, self.game)
                player.money -= rent
                owner.money += rent
                await self.broadcast({"type": "system_message", "text": f"{player.name} 支付 ${rent} 租金给 {owner.name}"})
                if player.money < 0:
                    await self.broadcast(self._state_update())
                    await self.handle_bankruptcy_check(pid)
                    return
            elif owner is None:
                self.game.turn_phase = "buy_decision"
                await self.broadcast(self._state_update())
                await self.send_to(pid, {"type": MessageType.PROMPT_DECISION, "decision": "buy_property", "tile_index": index, "tile_name": tile["name"], "price": tile.get("price", 0), "message": f"要购买 {tile['name']} 吗？价格 ${tile.get('price', 0)}"})
                return

        await self.broadcast(self._state_update())
        self.game.turn_phase = "end"
        await self.send_turn_options(pid)

    async def handle_buy_property(self, pid):
        player = self.game.get_player(pid)
        if not player:
            return
        index = player.position
        tile = self.game.board.get_tile(index)
        if tile["type"] not in (TILE_PROPERTY, TILE_RAILROAD, TILE_UTILITY):
            return
        if self.game.board.get_property_owner(index, self.game):
            return
        price = tile.get("price", 0)
        if player.money >= price:
            player.money -= price
            player.properties.append(index)
            await self.broadcast({"type": "system_message", "text": f"{player.name} 购买了 {tile['name']}"})
        await self.broadcast(self._state_update())
        self.game.turn_phase = "end"
        await self.send_turn_options(pid)

    async def handle_auction_bid(self, pid, msg):
        if not self.auction_state:
            return
        bid = msg.get("bid", 0)
        player = self.game.get_player(pid)
        if not player or player.bankrupt:
            return
        if self.auction_state["current_bidder"] == pid:
            await self.send_to(pid, {"type": "system_message", "text": "你已经是最高出价者"})
            return
        if bid <= self.auction_state["current_bid"]:
            await self.send_to(pid, {"type": "system_message", "text": "出价必须高于当前出价"})
            return
        if player.money < bid:
            await self.send_to(pid, {"type": "system_message", "text": "资金不足"})
            return
        self.auction_state["current_bid"] = bid
        self.auction_state["current_bidder"] = pid
        self.auction_state["last_bid_time"] = time.time()
        self.auction_state["bidder_name"] = player.name
        await self.broadcast({"type": "auction_update", "bid": bid, "bidder": pid, "bidder_name": player.name})

    async def handle_build_house(self, pid, msg):
        player = self.game.get_player(pid)
        if not player:
            return
        tile_index = msg.get("tile_index")
        if self.game.can_build_house(tile_index, player):
            self.game.build_house(tile_index, player)
            tile = self.game.board.get_tile(tile_index)
            await self.broadcast({"type": "system_message", "text": f"{player.name} 在 {tile['name']} 建造了房屋"})
        await self.broadcast(self._state_update())

    async def handle_sell_house(self, pid, msg):
        player = self.game.get_player(pid)
        if not player:
            return
        tile_index = msg.get("tile_index")
        if self.game.can_sell_house(tile_index, player):
            self.game.sell_house(tile_index, player)
            tile = self.game.board.get_tile(tile_index)
            await self.broadcast({"type": "system_message", "text": f"{player.name} 出售了 {tile['name']} 上的房屋"})
        await self.broadcast(self._state_update())

    async def handle_mortgage(self, pid, msg):
        player = self.game.get_player(pid)
        if not player:
            return
        tile_index = msg.get("tile_index")
        if self.game.mortgage_property(tile_index, player):
            tile = self.game.board.get_tile(tile_index)
            await self.broadcast({"type": "system_message", "text": f"{player.name} 抵押了 {tile['name']}"})
        await self.broadcast(self._state_update())

    async def handle_unmortgage(self, pid, msg):
        player = self.game.get_player(pid)
        if not player:
            return
        tile_index = msg.get("tile_index")
        if self.game.unmortgage_property(tile_index, player):
            tile = self.game.board.get_tile(tile_index)
            await self.broadcast({"type": "system_message", "text": f"{player.name} 赎回了 {tile['name']}"})
        await self.broadcast(self._state_update())

    async def handle_trade_offer(self, pid, msg):
        player = self.game.get_player(pid)
        if not player:
            return
        target_pid = msg.get("target_pid")
        offer_props = msg.get("offer_properties", [])
        request_props = msg.get("request_properties", [])
        offer_money = msg.get("offer_money", 0)
        request_money = msg.get("request_money", 0)
        target = self.game.get_player(target_pid)
        if not target or target.bankrupt:
            return
        await self.send_to(target_pid, {"type": "trade_request", "from_pid": pid, "from_name": player.name, "offer_properties": offer_props, "request_properties": request_props, "offer_money": offer_money, "request_money": request_money})

    async def handle_trade_response(self, pid, msg):
        pass

    async def handle_pay_jail_fine(self, pid):
        player = self.game.get_player(pid)
        if not player or not player.in_jail:
            return
        if player.money >= JAIL_FINE:
            player.money -= JAIL_FINE
            player.in_jail = False
            player.jail_turns = 0
            await self.broadcast({"type": "system_message", "text": f"{player.name} 交了 ${JAIL_FINE} 罚款出狱"})
        await self.broadcast(self._state_update())

    async def handle_use_get_out_of_jail(self, pid):
        player = self.game.get_player(pid)
        if not player or not player.in_jail or player.get_out_of_jail_cards <= 0:
            return
        player.get_out_of_jail_cards -= 1
        player.in_jail = False
        player.jail_turns = 0
        await self.broadcast({"type": "system_message", "text": f"{player.name} 使用了出狱卡！"})
        await self.broadcast(self._state_update())

    async def handle_end_turn(self, pid):
        player = self.game.get_player(pid)
        if not player or self.game.current_player().id != pid:
            return
        if self.game.is_doubles() and self.game.doubles_count < MAX_DOUBLES and not player.in_jail:
            pass
        else:
            self.game.doubles_count = 0
            self.game.next_turn()
        self.game.turn_phase = "roll"
        await self.broadcast(self._state_update())
        next_p = self.game.current_player()
        if next_p and not next_p.bankrupt:
            if next_p.in_jail:
                await self.send_to(next_p.id, {"type": MessageType.YOUR_TURN, "in_jail": True, "jail_turns": next_p.jail_turns, "can_pay": next_p.money >= JAIL_FINE, "has_card": next_p.get_out_of_jail_cards > 0})
            else:
                await self.send_to(next_p.id, {"type": MessageType.YOUR_TURN, "in_jail": False})

    async def handle_chat(self, pid, msg):
        player = self.game.get_player(pid)
        name = player.name if player else f"玩家{pid}"
        await self.broadcast({"type": "chat", "pid": pid, "name": name, "text": msg.get("text", "")})

    async def handle_decision_response(self, pid, msg):
        decision = msg.get("decision")
        if decision == "buy_property":
            if msg.get("accepted"):
                await self.handle_buy_property(pid)
            else:
                player = self.game.get_player(pid)
                if player:
                    index = player.position
                    self.start_auction(index)

    async def handle_bankruptcy_check(self, pid):
        player = self.game.get_player(pid)
        if not player:
            return
        await self.send_to(pid, {"type": "prompt_bankruptcy", "message": "你负债了！需要变卖资产或宣告破产"})
        self.game.turn_phase = "bankrupt"

    def start_auction(self, tile_index):
        tile = self.game.board.get_tile(tile_index)
        self.auction_state = {"tile_index": tile_index, "tile_name": tile["name"], "current_bid": 0, "current_bidder": None, "bidder_name": None, "last_bid_time": time.time()}
        asyncio.create_task(self.run_auction())

    async def run_auction(self):
        delay = 10
        await asyncio.sleep(delay)
        async with self.lock:
            if self.auction_state and self.auction_state["current_bidder"]:
                winner = self.game.get_player(self.auction_state["current_bidder"])
                if winner:
                    tile = self.game.board.get_tile(self.auction_state["tile_index"])
                    winner.money -= self.auction_state["current_bid"]
                    winner.properties.append(self.auction_state["tile_index"])
                    await self.broadcast({"type": "system_message", "text": f"{winner.name} 以 ${self.auction_state['current_bid']} 拍得 {tile['name']}"})
                    await self.broadcast(self._state_update())
                self.auction_state = None
            else:
                await self.broadcast({"type": "system_message", "text": "拍卖流拍"})
                self.auction_state = None

    async def send_turn_options(self, pid):
        player = self.game.get_player(pid)
        if not player:
            return
        options = []
        if self.game.turn_phase == "end":
            options.append({"action": "end_turn", "label": "结束回合"})
        await self.send_to(pid, {"type": "turn_options", "options": options})

    def _state_update(self):
        return {"type": MessageType.STATE_UPDATE, "players": [p.to_dict() for p in self.game.players], "current_turn": self.game.current_turn % len(self.game.players) if self.game.players else 0, "turn_phase": self.game.turn_phase}

    async def start_game(self):
        self.game.started = True
        await self.broadcast({"type": MessageType.GAME_START, "players": [p.to_dict() for p in self.game.players]})
        await self.broadcast(self._state_update())
        first = self.game.current_player()
        if first:
            await self.send_to(first.id, {"type": MessageType.YOUR_TURN, "in_jail": False})

    async def send_to(self, pid, msg):
        writer = self.clients.get(pid)
        if writer:
            try:
                writer.write(encode(msg))
                await writer.drain()
            except:
                pass

    async def broadcast(self, msg):
        for pid in list(self.clients.keys()):
            await self.send_to(pid, msg)

    async def disconnect(self, pid):
        if pid in self.clients:
            del self.clients[pid]
        self.game.remove_player(pid)
        await self.broadcast({"type": MessageType.PLAYER_DISCONNECTED, "pid": pid})

    async def start(self):
        server = await asyncio.start_server(self.handle_client, self.host, self.port)
        print(f"服务器启动在 {self.host}:{self.port}")
        async with server:
            await server.serve_forever()
