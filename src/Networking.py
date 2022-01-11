import socket

DEFAULT_HEADER_SIZE = 10

def receive_msg(s: socket.socket, header_size: int=DEFAULT_HEADER_SIZE):
    full_msg = ''
    new_msg = True
    while True:
        msg = s.recv(16)
        if new_msg:
            full_msg = ''
            msg_len = int(msg[:header_size])
            new_msg = False
        full_msg += msg.decode('utf-8')
        if len(full_msg) - header_size == msg_len:
            return full_msg[header_size:]

def send_msg(s: socket.socket, msg: str, header_size: int=DEFAULT_HEADER_SIZE):
    msg = f'{len(msg):<{header_size}}{msg}'
    s.send(bytes(msg, 'utf-8'))

class Connection:
    def __init__(self, socket_info):
        self.socket = socket_info[0]
        self.address = socket_info[1]

    def send_msg(self, msg: str, header_size: int=DEFAULT_HEADER_SIZE):
        send_msg(self.socket, msg, header_size)

    def receive_message(self, header_size: int=DEFAULT_HEADER_SIZE):
        return receive_msg(self.socket, header_size)
