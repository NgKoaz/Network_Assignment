import socket
import threading
import shutil
import os

MESSAGE_LEN = 512
CHUNK_LEN = 1024
HOST_NAME = "CLIENT"
PORT = 5050
FORMAT = 'utf-8'
PEER_SERVER = socket.gethostbyname(socket.gethostname()) 
PEER_PORT = 9996
PING_PORT = 9997
DISCONNECT_MESSAGE = "!DISCONNECT"
SERVER = socket.gethostbyname(socket.gethostname()) #Change when ...
WORKSPACE_DIR = "./client/"

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((SERVER, PORT))

peer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
peer.bind((PEER_SERVER, PEER_PORT))

def send_message(conn, msg):
    msg = msg.encode(FORMAT)
    msg_len = len(msg)
    msg += b' ' * (MESSAGE_LEN - msg_len)
    conn.send(msg)

def recv_message(conn):
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
    send_message(conn, req)
    addr = recv_message(conn)
    dest_ip, dest_port = addr.split(':')

    fname = req.split(' ')[1]

    dest_peer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    dest_peer.connect((dest_ip, int(dest_port)))

    #Request to fetch file from peer
    send_message(dest_peer, req)

    #Receive file
    recv_file(dest_peer, WORKSPACE_DIR + fname)

def publish(conn, req):
    cmd, lname, fname = req.split(' ')
    shutil.copyfile(lname, WORKSPACE_DIR + fname)

    msg = cmd + " " + fname + " " + PEER_SERVER + ":" + f"{PEER_PORT}"
    send_message(conn, msg)
    addr = recv_message(conn)

def discover(conn):
    file_names = os.listdir(WORKSPACE_DIR)
    for file_name in file_names:
        send_message(conn, file_name)
    send_message(conn, "<END>")

def ping_TCP(conn, msg):
    send_message(conn, msg)

def handle_request(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")

    request = recv_message(conn)

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
    print(f"[Listening] Peer is listening on {PEER_SERVER}")
    while True:
        conn, addr = peer.accept()
        thread = threading.Thread(target=handle_request, args={conn, addr})
        thread.start()

def start():
    thread = threading.Thread(target=listening)
    thread.start()

    msg = f"{HOST_NAME} {PEER_SERVER}:{PEER_PORT}"
    send_message(client, msg)

    command = input().strip()

    if command[0:5] == 'fetch':
        fetch(client, command)

    elif command[0:7] == 'publish':
        publish(client, command)

    else:
        print('CANNOT RECOGNIZE COMMAND!!!')

start()