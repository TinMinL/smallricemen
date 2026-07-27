from common.constants import BOARD_TILES, TILE_PROPERTY, TILE_RAILROAD, TILE_UTILITY

class Board:
    def __init__(self):
        self.tiles = BOARD_TILES

    def get_tile(self, index):
        return self.tiles[index % 40]

    def is_property(self, index):
        t = self.get_tile(index)
        return t["type"] in (TILE_PROPERTY, TILE_RAILROAD, TILE_UTILITY)

    def is_owned(self, index, game_state):
        for p in game_state.players:
            if p and index in p.properties:
                return p
        return None

    def get_property_owner(self, index, game_state):
        for p in game_state.players:
            if p and index in p.properties:
                return p
        return None
