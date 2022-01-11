'''
Create game (Online, Local with bots)
Connect to game
Settings
Exit
'''

import socket
import curses

from ncursesui.Elements import Button, List, Menu, Separator, TextField, UIElement, Window
from ncursesui.Utility import draw_borders, message_box
import draft_data

from mtgsdk import Card
from Networking import receive_msg, send_msg

DEFAULT_ADDRESS = 'localhost'
DEFAULT_PORT = str(draft_data.PORT)
ADDRESS_MAX_LENGTH = 20
PORT_MAX_LENGTH = 7
CARDS_LIST_HEIGHT = 20
CARDS_LIST_WIDTH = 20

class DraftClient:
    def __init__(self) -> None:
        pass

class DraftingMenu(Menu):
    def __init__(self, parent: Window, socket: socket.socket):
        draft_info = receive_msg(socket).split(' ')
        draft_name = draft_info[0]
        super().__init__(parent, 'Draft: {}'.format(draft_name.replace('_', ' ')))
        self.socket = socket
        self.pack_n = 0
        self.cards = []
        self.pile = []
        self.initUI()
        self.notify_about_next_pack()
        self.receive_msg()

    def initUI(self):
        def cards_list_element_click(choice: int, cursor: int, option: str):
            if message_box(self.parent, f'Take {option}?', ['No', 'Yes']) == 'Yes':
                # add card to pile and send it's mid to server
                self.pile += [self.cards[choice]]
                send_msg(self.socket, self.cards[choice].multiverseid)
                self.receive_msg()
        self.cards_list = List(self, [], CARDS_LIST_HEIGHT, CARDS_LIST_WIDTH, cards_list_element_click)
        self.cards_list.scroll_down_key = curses.KEY_DOWN
        self.cards_list.scroll_up_key = curses.KEY_UP
        self.cards_list.set_pos(0, 0)
        self.cards_list.set_focused(True)
        self.add_element(self.cards_list)

    def receive_msg(self):
        msg = receive_msg(self.socket)
        message_box(self.parent, msg)
        if msg == draft_data.NEXT_PACK:
            self.notify_about_next_pack()
            self.receive_msg()
            return
        if msg == draft_data.STOP_DRAFTING:
            self.stop_drafting()
            return
        # message is a list of mids
        mids = msg.split(' ')
        self.cards = [Card.from_id(mid) for mid in mids]
        self.cards_list.set_options([card.name for card in self.cards])

    def stop_drafting(self):
        # TODO
        message_box(self.parent, 'ENDED DRAFTING')
        self.socket.close()
        pass

    def notify_about_next_pack(self):
        self.pack_n += 1
        # self.parent.draw_window_with_message(f'PACK #{self.pack_n}')

class ClientWindow(Window):
    def __init__(self, window):
        super().__init__(window)

    def initUI(self):
        main_menu = Menu(self, 'Main menu')

        altext = 'Address: '
        address_label = UIElement(self, altext)
        address_label.set_pos(0, 0)

        address_text_field = TextField(self, DEFAULT_ADDRESS, ADDRESS_MAX_LENGTH)
        address_text_field.set_pos(0, len(altext))

        pltext = 'Port: '
        port_label = UIElement(self, pltext)
        port_label.set_pos(1, 0)

        port_text_field = TextField(self, DEFAULT_PORT, PORT_MAX_LENGTH)
        port_text_field.set_pos(1, len(altext))

        def connect_button_click():
            self.draw_window_with_message('Connecting to game...')
            address = address_text_field.text
            if address == 'localhost':
                address = socket.gethostname()
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((address, int(port_text_field.text)))
                self.draw_window_with_message('Queued for the game, waiting for other players...')
                self.current_menu = DraftingMenu(self, s)
            except (ConnectionRefusedError, socket.gaierror):
                self.draw_window_with_message('Could not connect to game!')
                self.window.getch()
            except ValueError:
                self.draw_window_with_message('Port has to be a number!')
                self.window.getch()

        connect_button = Button(self, 'Connect', connect_button_click)
        connect_button.set_pos(3, 0)
        connect_button.set_focused(True)

        address_text_field.prev = connect_button
        address_text_field.next = port_text_field

        port_text_field.prev = address_text_field
        port_text_field.next = connect_button

        connect_button.prev = port_text_field
        connect_button.next = address_text_field

        main_menu.add_element(address_label)
        main_menu.add_element(address_text_field)
        main_menu.add_element(port_label)
        main_menu.add_element(port_text_field)
        main_menu.add_element(Separator(self, 2))
        main_menu.add_element(connect_button)

        self.current_menu = main_menu

    def draw_window_with_message(self, message: str):
        height = 3
        width = len(message) + 2
        y = (self.HEIGHT - height) // 2
        x = (self.WIDTH - width) // 2
        window = curses.newwin(height, width, y, x)
        draw_borders(window, 'red-black')
        window.addstr(1, 1, message)
        window.refresh()

def main(stdscr):
    curses.curs_set(0)
    window = ClientWindow(stdscr)
    window.start()

curses.wrapper(main)