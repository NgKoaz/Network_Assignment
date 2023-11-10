import socket
import threading
import shutil
import os

MESSAGE_LEN = 512
CHUNK_LEN = 1024
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"


HOST_NAME = "CLIENT"
WORKSPACE_DIR = "./client/"

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

def recv_msg(conn):
    res = conn.recv(MESSAGE_LEN).decode(FORMAT).strip()
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

def recv_file(conn, uri):
    file_bytes = b''
    while True:
        chunk = conn.recv(CHUNK_LEN)
        if chunk[-5:] == b"<END>":
            break
        file_bytes += chunk

    file = open(uri, "wb")
    file.write(file_bytes)
    file.flush()
    file.close()

def fetch(conn, req):
    send_msg(conn, req)
    addr = recv_msg(conn)
    dest_ip, dest_port = addr.split(':')

    fname = req.split(' ')[1]

    dest_peer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    dest_peer.connect((dest_ip, int(dest_port)))

    #Request to fetch file from peer
    send_msg(dest_peer, req)

    #Receive file
    recv_file(dest_peer, WORKSPACE_DIR + fname)

def publish(conn, req):
    cmd, lname, fname = req.split(' ')
    shutil.copyfile(lname, WORKSPACE_DIR + fname)

    msg = cmd + " " + fname + " " + PEER_IP + ":" + f"{PEER_PORT}"
    send_msg(conn, msg)

def discover(conn):
    file_names = os.listdir(WORKSPACE_DIR)
    for file_name in file_names:
        send_msg(conn, file_name)
    send_msg(conn, "<END>")

def ping_TCP(conn, msg):
    send_msg(conn, msg)

def handle_request(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")

    request = recv_msg(conn)

    if request[0:5] == "fetch":
        fname = request[6:]
        send_file(conn, WORKSPACE_DIR + fname)
    elif request[0:8] == "discover":
        discover(conn)
    else:
        ping_TCP(conn, request)
    conn.close()

def listening():
    peer.listen()
    print(f"[Listening] Peer is listening on {PEER_IP}")
    while True:
        conn, addr = peer.accept()
        thread = threading.Thread(target=handle_request, args={conn, addr})
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