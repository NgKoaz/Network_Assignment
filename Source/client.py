import socket
import threading
import shutil
import os

MESSAGE_LEN = 512
CHUNK_LEN = 1024
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"

HOST_NAME = "CLIENT"
WORKSPACE_DIR = "./repos_client/"

PEER_IP = socket.gethostbyname(socket.gethostname())
PEER_PORT = 9996
PEER_ADDR = (PEER_IP, PEER_PORT)

SERVER_PORT = 5050
SERVER_HOST = socket.gethostbyname(socket.gethostname()) #Change when ...
SERVER_ADDR = (SERVER_HOST, SERVER_PORT)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(SERVER_ADDR)

peer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
peer.bind(PEER_ADDR)

def send_msg(conn, msg):
    msg = msg.encode(FORMAT)
    msg_len = len(msg)
    msg += b' ' * (MESSAGE_LEN - msg_len)
    conn.send(msg)
    print(f"[SENT] Message: {msg.decode(FORMAT)}")

def recv_msg(conn):
    res = conn.recv(MESSAGE_LEN).decode(FORMAT).strip()
    print(f"[RECEIVED] Message: {res}")
    return res

def send_file(conn, uri):
    file = open(uri, "rb")
    while True:
        data = file.read(CHUNK_LEN)
        if not data:
            break
        conn.send(data)

    conn.send(b"<END>")
    file.close()
    print(f"[SENT FILE] Filename: {uri}")

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
    print(f"[RECEIVED FILE] Filename: {uri}")


def fetch(conn, req):
    send_msg(conn, req)
    addr = recv_msg(conn)
    print("Peer's address contain that file: " + addr)
    dest_ip, dest_port = addr.split(':')

    fname = req.split(' ')[1]

    dest_peer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    dest_peer.connect((dest_ip, int(dest_port)))

    #Request to fetch file from peer
    send_msg(dest_peer, req)

    #Receive file
    recv_file(dest_peer, WORKSPACE_DIR + fname)

def publish(conn, req):
    #publishC:\\User\\File.txt.txt`
    cmd, lname, fname = req.split(' ')
    #source uri, destination uri
    shutil.copyfile(lname, WORKSPACE_DIR + fname)

    msg = cmd + " " + fname + " " + PEER_IP + ":" + f"{PEER_PORT}"
    send_msg(conn, msg)

def discover(conn):
    #discover client's local repository
    file_names = os.listdir(WORKSPACE_DIR)
    for file_name in file_names:
        send_msg(conn, file_name)
    send_msg(conn, "<END>")


def handle_request(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")

    while True:
        request = recv_msg(conn)
        if request[0:5] == "fetch":
            fname = request[6:]
            send_file(conn, WORKSPACE_DIR + fname)
        elif request[0:8] == "discover":
            discover(conn)
        elif request[0:4] == "ping":
            send_msg(conn, "pong")
        else:
            break

    conn.close()

def listening():
    peer.listen()
    print(f"[Listening] Peer is listening on {PEER_IP}")
    while True:
        conn, addr = peer.accept()
        thread = threading.Thread(target=handle_request, args=(conn, addr))
        thread.start()

def start():
    thread = threading.Thread(target=listening)
    thread.start()

    msg = f"{HOST_NAME} {PEER_IP}:{PEER_PORT}"
    send_msg(client, msg)

    while True:
        command = input().strip()
        if command[0:5] == 'fetch':
            fetch(client, command)
        elif command[0:7] == 'publish':
            publish(client, command)
        else:
            print('CANNOT RECOGNIZE COMMAND!!!')

start()