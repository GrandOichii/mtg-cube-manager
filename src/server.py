# import cursesui
import socket
import logging

from mtgsdk import Card, Cube
from Networking import Connection
import draft_data

logging.basicConfig(filename='serverlogs.log', encoding='utf-8', level=logging.DEBUG)

HEADER_SIZE = 10
NUMBER_OF_PLAYERS = 2
DEFAULT_PORT = draft_data.PORT
DEFAULT_NAME_OF_DRAFT = 'Awesome draft'
NUMBER_OF_PACKS = 2

'''
when connecting user, send to each user word MARKO
should expect POLO from all users
if didn't receive POLO, user is disconnected -> remove him from drafters list
'''

def divide_into_clusters(packs: list[list[Card]], number_of_players: int):
    if len(packs) % number_of_players != 0:
        raise Exception(f'ERR: number of packs in not equally divisible by number of players(packs: {len(packs)}, players: {number_of_players})')
    result = []
    for i in range(number_of_players):
        result += [[]]
    for i in range(len(packs)):
        ind = i % number_of_players
        result[ind] += [packs[i]]
    return result

def pack_to_mids(pack: list[Card]):
    return [card.multiverseid for card in pack]

def draft_packs(packs: list[list[Card]], drafters: list[Connection]):
    logging.info('Generated packs, contents:')
    for pack in packs:
        for card in pack:
            logging.info(card.multiverseid)
        logging.info('-' * 20)
    shift = 0
    while True:
        # send mids to each player
        for i in range(len(drafters)):
            mids = pack_to_mids(packs[(i + shift) % len(packs)])
            logging.info(f'Sending {mids} to drafter {drafters[i].address}')
            drafters[i].send_msg(' '.join(mids))
        # receive mid from each player and remove the cards
        for i in range(len(drafters)):
            drafter = drafters[i]
            mid = drafter.receive_message()
            logging.info(f'Drafter at {drafter.address} chose {mid}')
            pack = packs[(i + shift) % len(packs)]
            for card in pack:
                if card.multiverseid == mid:
                    pack.remove(card)
        # check if no cards left
        if len(packs[0]) == 0:
            break
        # shift
        shift += 1
        if shift >= len(packs):
            logging.info(f'Shifting order, new order: {shift}')
            shift = 0
    for drafter in drafters:
        drafter.send_msg(draft_data.NEXT_PACK)

cube_name = 'draft test cube'
logging.info(f'Enter the name of draft (Default: {DEFAULT_NAME_OF_DRAFT}): ', end='')
draft_name = DEFAULT_NAME_OF_DRAFT
entered_name = input()
if entered_name != '':
    draft_name = entered_name
logging.info(f'Enter the port to host on (Default: {DEFAULT_PORT}): ', end='')
port_s = input()
port = DEFAULT_PORT
if not port_s == '':
    port = int(port_s)

logging.info('Loading cube...')
cube = Cube.load(f'cubes/{cube_name}.cube')
logging.info('Cube loaded!')

server_host_address = socket.gethostname()
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((server_host_address, port))
    s.listen(5)

    drafters = []

    logging.info(f'Hosting <{draft_name}> draft (waiting for {NUMBER_OF_PLAYERS} players)...')

    while True:
        if len(drafters) == NUMBER_OF_PLAYERS:
            break
        drafter = Connection(s.accept())
        drafters += [drafter]
        logging.info(f'Queued drafter at {drafter.address}')
        drafter.send_msg(draft_name)

    # all players connected
    packs = cube.generate_packs(NUMBER_OF_PACKS * NUMBER_OF_PLAYERS)
    logging.info(f'Number of players: {NUMBER_OF_PLAYERS}')
    logging.info(f'Number of packs: {NUMBER_OF_PACKS}')
    logging.info(f'Total number of packs: {len(packs)}')
    logging.info(f'Amount of cards in a pack: {len(packs[-1])}')
    clusters = divide_into_clusters(packs, len(drafters))
    # draft the packs
    for cluster in clusters:
        draft_packs(cluster, drafters)
    # tell the players that the draft is over
    for drafter in drafters:
        # logging.info(f'Telling {drafter.address} to stop drafting')
        drafter.send_msg(draft_data.STOP_DRAFTING)


# packs = cube.generate_packs(NUMBER_OF_PACKS * NUMBER_OF_PLAYERS)