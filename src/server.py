# import cursesui
import socket

from mtgsdk import Card, Cube
from cursesui.Networking import Connection, PORT

HEADER_SIZE = 10
NUMBER_OF_PLAYERS = 2
DEFAULT_PORT = PORT
DEFAULT_NAME_OF_DRAFT = 'Awesome draft'
NUMBER_OF_PACKS = 2

def draft_pack(pack: list[Card], drafters: list[Connection]):
    pass

# entering data
cube_name = 'new cards'
# while cube_name == '':
#     print('Enter the name of the cube: ', end='')
#     s = input()
#     if s != '':
#         cube_name = s
print(f'Enter the name of draft (Default: {DEFAULT_NAME_OF_DRAFT}): ', end='')
draft_name = DEFAULT_NAME_OF_DRAFT
entered_name = input()
if entered_name != '':
    draft_name = entered_name
print(f'Enter the port to host on (Default: {DEFAULT_PORT}): ', end='')
port_s = input()
port = DEFAULT_PORT
if not port_s == '':
    port = int(port_s)

print('Loading cube...')
cube = Cube.load(f'cubes/{cube_name}.cube')
print('Cube loaded!')

server_host_address = socket.gethostname()
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((server_host_address, port))
    s.listen(5)

    drafters = []

    print(f'Hosting <{draft_name}> draft...')

    while True:
        if len(drafters) == NUMBER_OF_PLAYERS:
            break
        drafter = Connection(s.accept())
        drafters += [drafter]
        print(f'Queued drafter at {drafter.address}')
        drafter.send_msg(f'You are queued for the <{draft_name}> draft!')

    # all players connected
    packs = cube.generate_packs(NUMBER_OF_PACKS)
    for pack in packs:
        for card in pack:
            print(card.name)
        print('-' * 20)
        # draft_pack(pack)