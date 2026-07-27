TILE_GO = 0
TILE_PROPERTY = 1
TILE_COMMUNITY_CHEST = 2
TILE_TAX = 3
TILE_RAILROAD = 4
TILE_CHANCE = 5
TILE_JAIL = 6
TILE_UTILITY = 7
TILE_FREE_PARKING = 8
TILE_GO_TO_JAIL = 9

COLORS = {
    "brown": (139, 69, 19),
    "lightblue": (100, 181, 246),
    "pink": (233, 30, 99),
    "orange": (255, 128, 0),
    "red": (211, 47, 47),
    "yellow": (253, 216, 53),
    "green": (46, 125, 50),
    "darkblue": (13, 71, 161),
}

BOARD_TILES = [
    {"index": 0, "name": "GO", "type": TILE_GO},
    {"index": 1, "name": "地中海大道", "type": TILE_PROPERTY, "group": "brown", "price": 60, "rent": [2, 10, 30, 90, 160, 250], "build_cost": 50},
    {"index": 2, "name": "公益金", "type": TILE_COMMUNITY_CHEST},
    {"index": 3, "name": "波罗的海大道", "type": TILE_PROPERTY, "group": "brown", "price": 60, "rent": [4, 20, 60, 180, 320, 450], "build_cost": 50},
    {"index": 4, "name": "所得税", "type": TILE_TAX, "amount": 200},
    {"index": 5, "name": "皇家铁路", "type": TILE_RAILROAD, "price": 200, "rent": [25, 50, 100, 200]},
    {"index": 6, "name": "东方大道", "type": TILE_PROPERTY, "group": "lightblue", "price": 100, "rent": [6, 30, 90, 270, 400, 550], "build_cost": 50},
    {"index": 7, "name": "机会", "type": TILE_CHANCE},
    {"index": 8, "name": "佛蒙特大道", "type": TILE_PROPERTY, "group": "lightblue", "price": 100, "rent": [6, 30, 90, 270, 400, 550], "build_cost": 50},
    {"index": 9, "name": "康涅狄格大道", "type": TILE_PROPERTY, "group": "lightblue", "price": 120, "rent": [8, 40, 100, 300, 450, 600], "build_cost": 50},
    {"index": 10, "name": "监狱/探视", "type": TILE_JAIL},
    {"index": 11, "name": "圣查尔斯广场", "type": TILE_PROPERTY, "group": "pink", "price": 140, "rent": [10, 50, 150, 450, 625, 750], "build_cost": 100},
    {"index": 12, "name": "电力公司", "type": TILE_UTILITY, "price": 150},
    {"index": 13, "name": "州大道", "type": TILE_PROPERTY, "group": "pink", "price": 140, "rent": [10, 50, 150, 450, 625, 750], "build_cost": 100},
    {"index": 14, "name": "弗吉尼亚大道", "type": TILE_PROPERTY, "group": "pink", "price": 160, "rent": [12, 60, 180, 500, 700, 900], "build_cost": 100},
    {"index": 15, "name": "宾夕法尼亚铁路", "type": TILE_RAILROAD, "price": 200, "rent": [25, 50, 100, 200]},
    {"index": 16, "name": "圣詹姆斯广场", "type": TILE_PROPERTY, "group": "orange", "price": 180, "rent": [14, 70, 200, 550, 750, 950], "build_cost": 100},
    {"index": 17, "name": "公益金", "type": TILE_COMMUNITY_CHEST},
    {"index": 18, "name": "田纳西大道", "type": TILE_PROPERTY, "group": "orange", "price": 180, "rent": [14, 70, 200, 550, 750, 950], "build_cost": 100},
    {"index": 19, "name": "纽约大道", "type": TILE_PROPERTY, "group": "orange", "price": 200, "rent": [16, 80, 220, 600, 800, 1000], "build_cost": 100},
    {"index": 20, "name": "免费停车", "type": TILE_FREE_PARKING},
    {"index": 21, "name": "肯塔基大道", "type": TILE_PROPERTY, "group": "red", "price": 220, "rent": [18, 90, 250, 700, 875, 1050], "build_cost": 150},
    {"index": 22, "name": "机会", "type": TILE_CHANCE},
    {"index": 23, "name": "印第安纳大道", "type": TILE_PROPERTY, "group": "red", "price": 220, "rent": [18, 90, 250, 700, 875, 1050], "build_cost": 150},
    {"index": 24, "name": "伊利诺伊大道", "type": TILE_PROPERTY, "group": "red", "price": 240, "rent": [20, 100, 300, 750, 925, 1100], "build_cost": 150},
    {"index": 25, "name": "B&O铁路", "type": TILE_RAILROAD, "price": 200, "rent": [25, 50, 100, 200]},
    {"index": 26, "name": "大西洋大道", "type": TILE_PROPERTY, "group": "yellow", "price": 260, "rent": [22, 110, 330, 800, 975, 1150], "build_cost": 150},
    {"index": 27, "name": "文特诺大道", "type": TILE_PROPERTY, "group": "yellow", "price": 260, "rent": [22, 110, 330, 800, 975, 1150], "build_cost": 150},
    {"index": 28, "name": "自来水公司", "type": TILE_UTILITY, "price": 150},
    {"index": 29, "name": "马文花园", "type": TILE_PROPERTY, "group": "yellow", "price": 280, "rent": [24, 120, 360, 850, 1025, 1200], "build_cost": 150},
    {"index": 30, "name": "去监狱", "type": TILE_GO_TO_JAIL},
    {"index": 31, "name": "太平洋大道", "type": TILE_PROPERTY, "group": "green", "price": 300, "rent": [26, 130, 390, 900, 1100, 1275], "build_cost": 200},
    {"index": 32, "name": "北卡罗来纳大道", "type": TILE_PROPERTY, "group": "green", "price": 300, "rent": [26, 130, 390, 900, 1100, 1275], "build_cost": 200},
    {"index": 33, "name": "公益金", "type": TILE_COMMUNITY_CHEST},
    {"index": 34, "name": "宾夕法尼亚大道", "type": TILE_PROPERTY, "group": "green", "price": 320, "rent": [28, 150, 450, 1000, 1200, 1400], "build_cost": 200},
    {"index": 35, "name": "短途铁路", "type": TILE_RAILROAD, "price": 200, "rent": [25, 50, 100, 200]},
    {"index": 36, "name": "机会", "type": TILE_CHANCE},
    {"index": 37, "name": "公园广场", "type": TILE_PROPERTY, "group": "darkblue", "price": 350, "rent": [35, 175, 500, 1100, 1300, 1500], "build_cost": 200},
    {"index": 38, "name": "奢侈品税", "type": TILE_TAX, "amount": 100},
    {"index": 39, "name": "滨海大道", "type": TILE_PROPERTY, "group": "darkblue", "price": 400, "rent": [50, 200, 600, 1400, 1700, 2000], "build_cost": 200},
]

PROPERTY_GROUPS = {
    "brown": [1, 3],
    "lightblue": [6, 8, 9],
    "pink": [11, 13, 14],
    "orange": [16, 18, 19],
    "red": [21, 23, 24],
    "yellow": [26, 27, 29],
    "green": [31, 32, 34],
    "darkblue": [37, 39],
}

RAILROADS = [5, 15, 25, 35]
UTILITIES = [12, 28]

CHANCE_CARDS = [
    {"text": "向前走到GO", "type": "advance_to", "target": 0, "money": 200},
    {"text": "去伊利诺伊大道", "type": "advance_to", "target": 24},
    {"text": "去圣查尔斯广场", "type": "advance_to", "target": 11},
    {"text": "银行付你红利 $50", "type": "money", "amount": 50},
    {"text": "缴纳罚款 $15", "type": "money", "amount": -15},
    {"text": "向前走到最近铁路", "type": "advance_railroad"},
    {"text": "向后走3步", "type": "move", "steps": -3},
    {"text": "出狱免费卡", "type": "get_out_of_jail"},
    {"text": "去监狱", "type": "go_to_jail"},
    {"text": "房屋修缮费 $25/房 $100/酒店", "type": "house_repair", "per_house": 25, "per_hotel": 100},
    {"text": "你中奖了 $100", "type": "money", "amount": 100},
    {"text": "你的建筑贷款到期 $150", "type": "money", "amount": -150},
    {"text": "向前走到太平洋大道", "type": "advance_to", "target": 31},
    {"text": "回到GO", "type": "advance_to", "target": 0, "money": 200},
    {"text": "向前走到最近铁路", "type": "advance_railroad"},
    {"text": "生日快乐！每人给你 $10", "type": "birthday", "amount": 10},
]

COMMUNITY_CHEST_CARDS = [
    {"text": "银行错误，你多得 $200", "type": "money", "amount": 200},
    {"text": "人寿保险到期 $100", "type": "money", "amount": 100},
    {"text": "医疗费用 $50", "type": "money", "amount": -50},
    {"text": "学费 $50", "type": "money", "amount": -50},
    {"text": "出狱免费卡", "type": "get_out_of_jail"},
    {"text": "去监狱", "type": "go_to_jail"},
    {"text": "股票分红 $50", "type": "money", "amount": 50},
    {"text": "退税 $20", "type": "money", "amount": 20},
    {"text": "生日快乐！每人给你 $10", "type": "birthday", "amount": 10},
    {"text": "咨询费 $25", "type": "money", "amount": 25},
    {"text": "房屋修缮费 $40/房 $115/酒店", "type": "house_repair", "per_house": 40, "per_hotel": 115},
    {"text": "你继承 $100", "type": "money", "amount": 100},
    {"text": "圣诞基金 $100", "type": "money", "amount": 100},
    {"text": "缴纳罚款 $10", "type": "money", "amount": -10},
    {"text": "向前走到GO", "type": "advance_to", "target": 0, "money": 200},
    {"text": "医院费用 $100", "type": "money", "amount": -100},
]

START_MONEY = 1500
MAX_PLAYERS = 8
PASS_GO_MONEY = 200
JAIL_FINE = 50
MAX_DOUBLES = 3
JAIL_TURNS = 3
AUCTION_TIME = 15
