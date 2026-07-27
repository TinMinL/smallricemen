import json

class MessageType:
    JOIN_GAME = "join_game"
    PLAYER_JOINED = "player_joined"
    GAME_START = "game_start"
    STATE_UPDATE = "state_update"
    ROLL_DICE = "roll_dice"
    DICE_RESULT = "dice_result"
    BUY_PROPERTY = "buy_property"
    AUCTION_PROPERTY = "auction_property"
    AUCTION_BID = "auction_bid"
    AUCTION_RESULT = "auction_result"
    BUILD_HOUSE = "build_house"
    SELL_HOUSE = "sell_house"
    MORTGAGE = "mortgage"
    UNMORTGAGE = "unmortgage"
    TRADE_OFFER = "trade_offer"
    TRADE_RESPONSE = "trade_response"
    PAY_JAIL_FINE = "pay_jail_fine"
    USE_GET_OUT_OF_JAIL = "use_get_out_of_jail"
    END_TURN = "end_turn"
    DECLARE_BANKRUPTCY = "declare_bankruptcy"
    CHAT = "chat"
    PLAYER_DISCONNECTED = "player_disconnected"
    ERROR = "error"
    YOUR_TURN = "your_turn"
    GAME_OVER = "game_over"
    ROLLED_DOUBLES = "rolled_doubles"
    PROMPT_DECISION = "prompt_decision"
    DECISION_RESPONSE = "decision_response"

def encode(msg):
    return json.dumps(msg).encode() + b"\n"

def decode(data):
    return json.loads(data.decode())
