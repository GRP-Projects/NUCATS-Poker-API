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
    def __init__(self, bot_name: str, passcode: str, address: str):

        if address[:5] != "ws://":
            raise Exception("Invalid address, please define ws:// preceding server URI")
        
        self.address = address
        self.bot_name = bot_name
        self.passcode = passcode

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
        data = json.dumps({"username": self.bot_name, "password": self.passcode})
        try:
            self.s.send(data)
            response = json.loads(self.s.recv())
            if response['login']:
                return True
            else:
                logger.error(f'Could not log into poker server: {response['info']}')
                return False
        except Exception as e:
            logger.error(f"Could not log into poker server:\n{e}")

    def enter_matchmaking(self, timeout: int = 30):
        # Tries to enter matchmaking queue, if successful, query for confirmation of game entry until timeout.
        try:
            if not self._matchmaking_request():
                raise Exception(f"Could not enter matchmaking queue.")
            logger.info("Queued for match.")
            for i in range(0, timeout):
                queued, match = self.check_matchmaking()
                if queued:
                    logger.info(f"Match found! Match ID: {match}.")
                    return match
                sleep(1)
            raise Exception(f"Timeout after {timeout} seconds.")
        except Exception as e:
            logger.error(e)
            return None

    def _matchmaking_request(self):
        # Attempts to enter matchmaking queue, if successful, return True. Else, return False.
        try:
            queue_request = requests.Request('POST', f"{self.address}:{self.port}/enter_queue")
            queue_request = self.s.prepare_request(queue_request)
            r = self.s.send(queue_request, timeout=5)
            if r.status_code == 200:
                return True
            return False
        except Exception as e:
            logger.error(e)
            return False

    def check_matchmaking(self):
        # Checks to see whether match making has placed bot in match.
        try:
            check_request = requests.Request("GET", f"{self.address}:{self.port}/query_queue")
            check_request.headers['Content-Type'] = 'application/json'
            check_request = self.s.prepare_request(check_request)
            r = self.s.send(check_request, timeout=5)
            if r.status_code != 200:
                raise Exception(f"Contacted server, could not check matchmaking. Error: {r.status_code}")
            status = json.loads(r.text)
            if status["queued"]:
                return True, status["match"]
            return False, 0
        except Exception as e:
            logger.error(e)
            return None, None

    def _ping(self):
        if requests.get(f"{self.address}:{self.port}", timeout=5).status_code != 200:
            return True
        return False
