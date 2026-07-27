class Player:
    def __init__(self, pid, name):
        self.id = pid
        self.name = name
        self.position = 0
        self.money = 1500
        self.properties = []
        self.in_jail = False
        self.jail_turns = 0
        self.bankrupt = False
        self.get_out_of_jail_cards = 0
        self.houses = {}
        self.hotels = {}

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "position": self.position,
            "money": self.money,
            "properties": self.properties,
            "in_jail": self.in_jail,
            "jail_turns": self.jail_turns,
            "bankrupt": self.bankrupt,
            "get_out_of_jail_cards": self.get_out_of_jail_cards,
            "houses": self.houses,
            "hotels": self.hotels,
        }

    def net_worth(self):
        return self.money + len(self.properties) * 50
