import socket
import threading

MESSAGE_LEN = 512
CHUNK_LEN = 1024
FORMAT = 'utf-8'


################ THIS PROJECT IN PROGRESS

class Tracker:
    def __init__(self):
        #Create socket and bind ip, port
        self.tracker_ip = socket.gethostbyname(socket.gethostname())
        self.tracker_port = 5051
        self.tracker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #Bind socket
        self.binding()

    def binding(self):
        try:
            self.tracker_socket.bind((self.tracker_ip, self.tracker_port))
        except:
            print("Port have been used! Changing your listening port!")

    def listening(self):
        self.tracker_socket.listen()
        print(f"Tracker is listening on {self.tracker_ip, self.tracker_port}")
        while True:
            conn, addr = self.tracker_socket.accept()
            thread = threading.thread(target=self.handle_request, args=(conn, addr))

    def handle_request(self, conn, addr):
        print(f"Connection from {addr}")
        hostname, listening_addr = recv_msg(conn).split(' ')
        #while True:



def send_msg(conn, msg):
    msg = msg.encode(FORMAT)
    msg += b' ' * (MESSAGE_LEN - len(msg))
    conn.send(msg)


def recv_msg(conn):
    return conn.recv(MESSAGE_LEN).decode(FORMAT).strip()


def send_file(conn, uri):
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
    while True:
        data = conn.recv(CHUNK_LEN)
        if data[-5:0] == b"<END>":
            break
        file.write(data)
    file.close()


Tracker()