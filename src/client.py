import socket
from cursesui.Networking import receive_msg, PORT

socket_host_name = socket.gethostname()
port = PORT

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s: 
    s.connect((socket_host_name, port))

    while True:
        msg = receive_msg(s)
        print(msg)