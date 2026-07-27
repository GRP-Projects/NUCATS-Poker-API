import json
import os
import requests
import logging

logger = logging.getLogger(__name__)

def PokerInterface:
    def __init__(self, address: str, port: int = 8080, bot_name: str, passcode: str):
        
        self.address = address
        self.port = port
        self.bot_name=bot_name
        self.passcode=passcode
        self.s = requests.Session()
        self.current_game = -1

        self.login()

    def login():
       try:
            if self._ping():
                raise Exception(f"Could not access server {address}:{port}")
            data = json.dumps({"username": bot_name, "password": passcode})
            login_request = requests.Request('POST', f"{address}:{port}/bot_login", data=data).prepare()
            r = self.s.send(login_request)
            if r.status_code != 200:
                raise Exception(f"Could not authenticate with poker server: Error {r.status_code}")
        except Exception as e:
            logger.error(f"{repr(e)}")
            return
        logger.info(f"Successfully connected and authenticated with server. Logged in as {bot_name}")

    def matchmaking():
        logger.info("TBI")

    def _ping():
        if requests.get(f"{address}:{port}, timeout=5.0").status_code != 200:
            return True
        return False
