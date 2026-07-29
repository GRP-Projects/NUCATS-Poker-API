# NUCATS AI POKER API

This Poker API is meant for use in the NuCats autonomous poker exercise / competition. The AI Poker competition involves individuals
or teams creating AI poker bots, either using traditional game theoretical methods or AI models, to play against other AI poker bots
in a free-for-all no holds barred poker tournament.

This poker API provides a standard mode of interface for such poker bots to compete against eachother on a centralised server, which
controls a poker game. This README.md will outline the standard use of this poker library for such a purpose.

## Installing the Package

This poker API requires Python 3.12.0 or higher.

Firstly, clone or download the repository, and run ``pip install .`` from inside the directory, either from a system python install or
(recommended) a sourced python virtual environment.

## Registering with the Poker Server

In order to access the poker server, you must first register a profile for your poker bot, once you have done this, initialise the
poker API using the address of the server, port, and the bot username and password.

## API Usage

Interactions with the server are encapsulated within an API object under the class PokerInterface, so importing should look like
``from NUPokerAPI import PokerInterface``, and creating an object should look like
``Poker = PokerInterface(bot_name = bot_name, passcode = passcode, address = address, port = port)`` for a given
registered bot name and passcode registered with the poker server.

For a PokerInterface object, the following methods:

|Method|Parameters|Returns|Description|
|------|----------|-------|-----------|
|init|bot_name: str, passcode: str, address: str, port: int (default: 8080)|None.|Initiates the Poker API by logging into and creating a session with the poker API server.|
|login|None (uses credentials passed at object initialisation)|True if successful login, False if not.| Used during object initialisation, but can be reinvoked if the session is disrupted.|
|enter_matchmaking|timeout: int (default: 30)|Match / Game ID (int) if successful in joining match, None if not.|Attempts to enter matchmaking queue, if successful, wait until timeout for confirmation of start of game, querying every second.|
|check_matchmaking|None|True, Game ID if in match. False, 0 if not in match. None, None if Exception.|Queries with poker server whether the bot is currently in a poker match.|

Packaged also are some useful functions which can be imported alongside the PokerInterface class for additional functionality:

|Function|Parameters|Returns|Description|
|--------|----------|-------|-----------|
|card_to_string|card: int (default: -1)|String representation of the card number (-1 to 51).|For disambiguation and ease of integration for LLM competitors. Converts a card integer into its corresponding string representation according to the API card format (see below).|

## Card Format

Cards are represented by intagers between -1 and 51, where -1 is reserved for undefined cards (cards on the river which have not yet been flipped).

The remaining 0 to 51 cards are reserved for the 52 playing cards in a game of poker arranged ascending in order of strength (Two to Ace) * (Clubs, Diamonds, Hearts, Spades), 13x4.

- 0 is the Two of Clubs
- 11 is the King of Clubs
- 51 is the Ace of Spaces
- etc...

Anything above 51 is considered Undefined, and is returned as such.
