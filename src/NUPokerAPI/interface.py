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
    def __init__(self, api_key: str, address: str):

        if address[:5] != "ws://":
            raise Exception("Invalid address, please define ws:// preceding server URI")
        
        self.address = address
        self.api_key = api_key

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

    def enter_matchmaking(self, timeout: int = 30):
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
                    logger.info(f'{response['info']}')
                    return True
            else:
                logger.error(f'Could not enter matchmaking: {response['info']}')
                return False
        except Exception as e:
            logger.error(e)
            return False
    
    def close(self):
        self.s.close()
