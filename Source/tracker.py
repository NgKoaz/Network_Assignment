import socket
import threading

MESSAGE_LEN = 512
CHUNK_LEN = 1024
FORMAT = 'utf-8'
UNKNOWN_MESSAGE = "<UNKNOWN>"

SERVER = socket.gethostbyname(socket.gethostname())
PORT = 5051
ADDR = (SERVER, PORT)
file_list_dir = './sharingFileList'

listening_peer_list = []

class Tracker:
    def __init__(self):
        try:
            self.tracker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tracker.bind(ADDR)
        except Exception as e:
            print(e)
            return

    def listening(self):
        self.tracker.listen()
        print(f"Tracker is listening on {ADDR}")
        while True:
            conn, addr = self.tracker.accept()
            thread = threading.Thread(target=self.handle_request, args=(conn, addr))
            thread.start()

    def handle_request(self, conn, addr):
        print(f"{addr} connected.")

        while True:
            msg = recv_msg(conn)



def send_msg(conn, msg):
    msg = msg.encode(FORMAT)
    msg_len = len(msg)
    msg += b' ' * (MESSAGE_LEN - msg_len)
    conn.send(msg)


def recv_msg(conn):
    res = conn.recv(MESSAGE_LEN).decode(FORMAT).strip()
    return res


def send_file_list(conn, uri):
    file = open(uri, "rb")
    while True:
        data = file.read(CHUNK_LEN)
        if not data:
            break
        conn.send(data)

    conn.send(b"<END>")
    file.close()


def recv_file(conn, uri):
    file = open(uri, "ab")
    file_bytes = b''
    done = False
    while not done:
        data = conn.recv(1024)
        if data[-5:] == b"<END>":
            done = True
        else:
            file.write(data)
    file.close()


Tracker()















