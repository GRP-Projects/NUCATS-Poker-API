import json
import os
import requests
import logging

from time import sleep

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
    def __init__(self, bot_name: str, passcode: str, address: str, port: int = 8080):

        if not ((address[:7] != "http://") ^ (address[:8] != "https://")):
            raise Exception("Invalid address, please define https:// or http://")
        
        self.address = address
        self.port = port
        self.bot_name=bot_name
        self.passcode=passcode
        self.s = requests.Session()

        while not self.login():
            logger.error("Could not login, retrying in 5...")
            sleep(5)

    def login(self):
        # Attempt server sign-in
        try:
            if self._ping():
                raise Exception(f"Could not access server {self.address}:{self.port}")
            data = json.dumps({"username": self.bot_name, "password": self.passcode})
            login_request = requests.Request('POST', f"{self.address}:{self.port}/bot_login", data=data)
            login_request.headers['Content-Type'] = 'application/json'
            login_request = self.s.prepare_request(login_request)
            r = self.s.send(login_request, timeout=5)
            if r.status_code != 200:
                raise Exception(f"Could not authenticate with poker server: Error {r.status_code}.")
        except Exception as e:
            logger.error(e)
            return False
        logger.info(f"Successfully connected and authenticated with server. Logged in as {self.bot_name}.")
        return True

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
