import random
from common.constants import *
from server.board import Board
from server.player import Player

class GameState:
    def __init__(self):
        self.board = Board()
        self.players = []
        self.current_turn = 0
        self.started = False
        self.over = False
        self.doubles_count = 0
        self.chance_deck = list(CHANCE_CARDS)
        self.community_deck = list(COMMUNITY_CHEST_CARDS)
        random.shuffle(self.chance_deck)
        random.shuffle(self.community_deck)
        self.chance_index = 0
        self.community_index = 0
        self.last_dice = (0, 0)
        self.turn_phase = "roll"
        self.winner = None

    def add_player(self, pid, name):
        self.players.append(Player(pid, name))

    def remove_player(self, pid):
        self.players = [p for p in self.players if p.id != pid]

    def get_player(self, pid):
        for p in self.players:
            if p.id == pid:
                return p
        return None

    def current_player(self):
        if not self.players:
            return None
        return self.players[self.current_turn % len(self.players)]

    def next_turn(self):
        self.current_turn = (self.current_turn + 1) % len(self.players)
        while self.current_player() and self.current_player().bankrupt:
            self.current_turn = (self.current_turn + 1) % len(self.players)

    def roll_dice(self):
        d1 = random.randint(1, 6)
        d2 = random.randint(1, 6)
        self.last_dice = (d1, d2)
        return d1, d2

    def is_doubles(self):
        return self.last_dice[0] == self.last_dice[1]

    def move_player(self, player, steps):
        old_pos = player.position
        player.position = (player.position + steps) % 40
        if player.position < old_pos and old_pos + steps >= 40:
            player.money += PASS_GO_MONEY
            return True
        if steps > 0 and old_pos < 24 and player.position >= 24 and player.position < old_pos:
            pass
        return False

    def move_player_to(self, player, target):
        if target < player.position:
            player.money += PASS_GO_MONEY
        player.position = target

    def calculate_rent(self, tile_index, game_state):
        tile = self.board.get_tile(tile_index)
        owner = self.board.get_property_owner(tile_index, game_state)
        if not owner:
            return 0

        if tile["type"] == TILE_PROPERTY:
            if tile_index in owner.hotels:
                return tile["rent"][5]
            houses = owner.houses.get(tile_index, 0)
            if houses > 0:
                return tile["rent"][houses]
            group = tile["group"]
            group_tiles = PROPERTY_GROUPS[group]
            if all(t in owner.properties for t in group_tiles):
                return tile["rent"][0] * 2
            return tile["rent"][0]

        elif tile["type"] == TILE_RAILROAD:
            rr_count = sum(1 for r in RAILROADS if r in owner.properties)
            return tile["rent"][rr_count - 1] if rr_count > 0 else tile["rent"][0]

        elif tile["type"] == TILE_UTILITY:
            util_count = sum(1 for u in UTILITIES if u in owner.properties)
            d1, d2 = self.last_dice
            mult = 10 if util_count == 1 else 4
            return (d1 + d2) * mult

        return 0

    def can_build_house(self, tile_index, player):
        tile = self.board.get_tile(tile_index)
        if tile["type"] != TILE_PROPERTY:
            return False
        if tile_index not in player.properties:
            return False
        group = tile["group"]
        group_tiles = PROPERTY_GROUPS[group]
        for t in group_tiles:
            if t not in player.properties:
                return False
        if tile_index in player.hotels:
            return False
        current_houses = player.houses.get(tile_index, 0)
        if current_houses >= 4:
            return False
        for t in group_tiles:
            if t != tile_index:
                other_houses = player.houses.get(t, 0)
                other_hotel = t in player.hotels
                other_level = 5 if other_hotel else other_houses
                if other_level < current_houses:
                    return False
        cost = tile["build_cost"]
        return player.money >= cost

    def build_house(self, tile_index, player):
        tile = self.board.get_tile(tile_index)
        cost = tile["build_cost"]
        player.money -= cost
        current = player.houses.get(tile_index, 0)
        if current == 4:
            del player.houses[tile_index]
            player.hotels[tile_index] = True
        else:
            player.houses[tile_index] = current + 1

    def can_sell_house(self, tile_index, player):
        if tile_index in player.houses and player.houses[tile_index] > 0:
            return True
        if tile_index in player.hotels:
            return True
        return False

    def sell_house(self, tile_index, player):
        tile = self.board.get_tile(tile_index)
        cost = tile["build_cost"] // 2
        if tile_index in player.hotels:
            del player.hotels[tile_index]
            player.houses[tile_index] = 4
        else:
            current = player.houses.get(tile_index, 0)
            if current > 0:
                player.houses[tile_index] = current - 1
        player.money += cost

    def mortgage_property(self, tile_index, player):
        if tile_index not in player.properties:
            return False
        tile = self.board.get_tile(tile_index)
        if player.houses.get(tile_index, 0) > 0 or tile_index in player.hotels:
            return False
        value = tile.get("price", 0) // 2
        player.money += value
        return True

    def unmortgage_property(self, tile_index, player):
        if tile_index not in player.properties:
            return False
        tile = self.board.get_tile(tile_index)
        cost = tile.get("price", 0) // 2
        if player.money < cost:
            return False
        player.money -= cost
        return True

    def draw_chance(self, player):
        card = self.chance_deck.pop(0)
        self.chance_deck.append(card)
        return card

    def draw_community_chest(self, player):
        card = self.community_deck.pop(0)
        self.community_deck.append(card)
        return card

    def apply_card(self, card, player, game_state):
        result = {"card": card, "text": card["text"], "money_change": 0, "go_to_jail": False, "get_out_of_jail": False, "move_to": None, "messages": []}

        if card["type"] == "money":
            player.money += card["amount"]
            result["money_change"] = card["amount"]

        elif card["type"] == "advance_to":
            target = card["target"]
            passed_go = target < player.position
            player.position = target
            if passed_go:
                player.money += card.get("money", PASS_GO_MONEY)
                result["money_change"] = card.get("money", PASS_GO_MONEY)
            result["move_to"] = target

        elif card["type"] == "advance_railroad":
            pos = player.position
            for rr in RAILROADS:
                if rr > pos:
                    player.position = rr
                    break
            else:
                player.position = RAILROADS[0]
                player.money += PASS_GO_MONEY
                result["money_change"] = PASS_GO_MONEY
            result["move_to"] = player.position

        elif card["type"] == "move":
            player.position = (player.position + card["steps"]) % 40
            result["move_to"] = player.position

        elif card["type"] == "go_to_jail":
            player.in_jail = True
            player.jail_turns = 0
            player.position = 10
            result["go_to_jail"] = True
            result["move_to"] = 10

        elif card["type"] == "get_out_of_jail":
            player.get_out_of_jail_cards += 1
            result["get_out_of_jail"] = True

        elif card["type"] == "house_repair":
            total_houses = sum(player.houses.values())
            total_hotels = len(player.hotels)
            cost = total_houses * card["per_house"] + total_hotels * card["per_hotel"]
            player.money -= cost
            result["money_change"] = -cost

        elif card["type"] == "birthday":
            total = 0
            for p in game_state.players:
                if p and p.id != player.id and not p.bankrupt:
                    amount = min(card["amount"], p.money)
                    p.money -= amount
                    player.money += amount
                    total += amount
                    result["messages"].append(f"{p.name} 给了 ${amount}")
            result["money_change"] = total

        return result

    def check_bankruptcy(self, player):
        if player.money < 0:
            return True
        return False

    def handle_bankruptcy(self, player):
        player.bankrupt = True
        for prop in player.properties:
            pass
        player.properties = []
        player.houses = {}
        player.hotels = {}
        alive = [p for p in self.players if not p.bankrupt]
        if len(alive) == 1:
            self.over = True
            self.winner = alive[0]
