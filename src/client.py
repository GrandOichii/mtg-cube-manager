import socket
import draft_data

from mtgsdk import Card
from Networking import receive_msg, send_msg

socket_host_name = socket.gethostname()
port = draft_data.PORT

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s: 
    pile = []
    pack_n = 0
    s.connect((socket_host_name, port))
    # receive draft name
    msg = receive_msg(s)
    print(f'You are queued for the <{msg}> draft!')
    # receive and send mids
    while True:
        # receive cards
        msg = receive_msg(s)
        print(msg)
        if pack_n == 0:
            pack_n += 1
            print(f'PACK #{pack_n}')
        if msg == draft_data.NEXT_PACK:
            pack_n += 1
            print(f'PACK #{pack_n}')
            continue
        if msg == draft_data.STOP_DRAFTING:
            break
        print('-' * 30)
        mids = msg.split(' ')
        cards = [Card.from_id(mid) for mid in mids]
        for card in cards:
            print(f'Name: {card.name}')
            print(f'Id: {card.multiverseid}')
            print()
        # pick card
        choice = 'err'
        while not choice in mids:
            choice = input('enter card id > ')
        # send mid of card
        send_msg(s, choice)
        # add card to pile
        for card in cards:
            if card.multiverseid == choice:
                pile += [card]
                break
    # end of draft, print out the cards
    for card in pile:
        print(card.name)
        