import socket

socket_path = '/tmp/buttons'
sock = None


def connect():
    global sock
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect(socket_path)


connect()

while True:
    data = sock.recv(32)
    if data:
        print(data)
    else:
        print("Conn lost")
        connect()
