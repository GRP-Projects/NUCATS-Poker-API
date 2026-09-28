import json
import os
from time import sleep

import logging

from websockets.sync.client import connect

logger = logging.getLogger(__name__)

suit_strings = {
    0 : 'Clubs',
    1 : 'Diamonds',
    2 : 'Hearts',
    3 : 'Spades'
}

card_strings = {
    0 : 'Two',
    1 : 'Three',
    2 : 'Four',
    3 : 'Five',
    4 : 'Six',
    5 : 'Seven',
    6 : 'Eight',
    7 : 'Nine',
    8 : 'Ten',
    9 : 'Jack',
    10 : 'Queen',
    11 : 'King',
    12 : 'Ace'
}

def card_to_string(card:int = -1):
    # For disambiguation and LLM competitors
    if card==-1:
        return "Undecided"
    if card > 51:
        return "Undefined"
    return f"{card_strings[card % 13]} of {suit_strings[card // 13]}"

class PokerInterface:
    def __init__(self, api_key: str, address: str, info: bool):

        if info:
            logging.basicConfig(level=logging.INFO)
        
        if address[:5] != "ws://":
            raise Exception("Invalid address, please define ws:// preceding server URI")
        
        self.address = address
        self.api_key = api_key

        self.in_game = False
        self.turn_log = []
        self.player_status = {}

        try:
            self.s = connect(address)
        except Exception as e:
            raise Exception(f"Could not connect to poker server:\n{e}")
        logger.info("Connected to poker server successfully.")

        while not self.login():
            logger.error("Retrying in 5 seconds...")
            sleep(5)

    def login(self):
        # Attempt server sign-in
        data = json.dumps({"type": "login", "api_key": self.api_key})
        try:
            self.s.send(data)
            response = json.loads(self.s.recv())
            if response['success']:
                logger.info(f'{response['info']}')
                return True
            else:
                logger.error(f'Could not log into poker server: {response['info']}')
                return False
        except Exception as e:
            logger.error(f"Could not log into poker server:\n{e}")

    def enter_matchmaking(self):
        data = json.dumps({"type": "enter_matchmaking"})
        try:
            self.s.send(data)
            response = json.loads(self.s.recv())
            if response['success']:
                # Entered matchmaking
                logger.info(f'{response['info']}')
                # Waits for confirmation that client is in game
                response = json.loads(self.s.recv())
                if response['success'] and response['status'] == 3:
                    self.in_game = True
                    logger.info(f'{response['info']}')
                    return True
            else:
                logger.error(f'Could not enter matchmaking: {response['info']}')
                return False
        except Exception as e:
            logger.error(e)
            return False
    
    def await_turn(self):
        # Returns BOOL; BOOL [Is it your turn?; Is the game over?]
        if self.in_game:
            while True:
                message = json.loads(self.s.recv())
                if not message['success']:
                    logger.error(f"ERROR: {message['info']}")
                    return True, False
                elif message['type'] == 'game':
                    match message['status']:
                        case 3:
                            # Someone else's turn has been played; log actions.
                            played_turn = {message['player'], message['pot'], message['play'], message['current_bet']}
                            self.turn_log.append(played_turn)
                            logger.info(f"Player {message['player']} {message['play']}. Pot is {message['pot']}, and current bet is {message['current_bet']}.")
                            continue
                        case 4:
                            # Your turn: process status message and signal to parent
                            del message['type']
                            del message['status']
                            del message['success']
                            self.player_status = message

                            return False, False
                        case 5:
                            # Tidy up:
                            self.in_game = False
                            self.turn_log = []
                            self.player_status = {}

                            logger.info(f"{message['info']}")
                            return False, True
                        case _:
                            # Server wasn't expecting this.
                            logger.error("Bad response recieved from server.")
                            self.in_game = False
                            return False, True
        logger.error("You're not currently in a game.")
        return False, True
    
    def take_turn(self, play: int, raise_quantity: int = 0):
        if self.in_game:
            # play : fold = 0, call = 1, raise = 2.
            if play == 2 and raise_quantity < self.get_minimum_bet():
                raise Exception(f"Cannot raise by {raise_quantity} chips.")
            data = json.dumps({"type": "play", "play" : play, "raise_quantity" : raise_quantity})
            self.s.send(data)
        else:
            logger.info("You're not currently in a game.")
    
    # Quality of life - fold wrapper around take_turn method.
    def fold(self):
        self.take_turn(0)
    
    # Quality of life - call wrapper around take_turn method.
    def call(self):
        self.take_turn(1)
    
    # Quality of life - raise wrapper around take_turn method.
    def bump(self, raise_quantity: int):
        self.take_turn(2, raise_quantity)

    # Quality of life - gets for status attributes:
    def get_cards(self):
        if not 'cards' in self.player_status:
            return None
        return self.player_status['cards']
    
    def get_bet(self):
        if not 'bet' in self.player_status:
            return None
        return self.player_status['bet']
    
    def get_money(self):
        if not 'money' in self.player_status:
            return None
        return self.player_status['money']

    def get_folded(self):
        if not 'folded' in self.player_status:
            return None
        return self.player_status['folded']

    def get_river(self):
        if not 'river' in self.player_status:
            return None
        return self.player_status['river']

    def get_strength(self):
        if not 'hand_strength' in self.player_status:
            return None
        return self.player_status['hand_strength']
    
    def get_minimum_bet(self):
        if not 'minimum_bet' in self.player_status:
            return None
        if self.player_status['minimum_bet']==0:
            return 1
        return self.player_status['minimum_bet']
    
    def close(self):
        self.s.close()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
