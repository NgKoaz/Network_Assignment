import socket
import threading
import os
import jwt
from dotenv import load_dotenv
from pymongo import MongoClient
from bson.objectid import ObjectId

MESSAGE_LEN = 512
CHUNK_LEN = 1024
FORMAT = 'utf-8'
UNKNOWN_MESSAGE = "<UNKNOWN>"

load_dotenv()
SERVER = socket.gethostbyname(socket.gethostname())
PORT = 5051
ADDR = (SERVER, PORT)

KEY = os.getenv("KEY")

database = MongoClient(os.getenv("MONGO_URL")).p2pFileSharing

tracker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


def handle_login_info(msg):
    username, password = msg.split("|")
    username = username.split(":")[1]
    password = password.split(":")[1]
    return username, password


def login(username, password):
    result = database.users.find_one({"username": username, "password": password})
    if result:
        # login success
        return str(result['_id'])
    # Login fail
    return ""


def handle_login_request(conn):
    # Send back to confirm request for peer
    send_msg(conn, "login")
    # Receive username and password from peer
    msg = recv_msg(conn)
    username, password = handle_login_info(msg)
    # Check username, password
    user_id = login(username, password)
    if not user_id:
        # Send empty token
        msg = f"login fail|token:"
    else:
        payload_data = {
            "_id": user_id
        }
        token = jwt.encode(
            payload=payload_data,
            key=KEY
        )
        msg = f"login success|token:{token}"
    send_msg(conn, msg)


def handle_token_msg(token):
    token = token.split(":")[1]
    return jwt.decode(token, KEY, algorithms=['HS256'])


def handle_address_info(msg):
    pass


def handle_address_declaration(conn):
    # Send back to confirm request for peer
    send_msg(conn, "address")
    # Receive token to identify user
    token = recv_msg(conn)
    payload = handle_token_msg(token)
    user_id = payload['_id']
    if user_id:
        send_msg(conn, "auth success")
    else:
        send_msg(conn, "auth fail")
        return

    # Receive `ip, port` from peer
    msg = recv_msg(conn)
    # Checking port (TO DO)
    # checking_port()
    # Send ACK
    send_msg(conn, "address success")

    # Saving port
    database.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"address": msg}}
    )


def handle_request(conn, addr):
    print(f"{addr} connected.")
    while True:
        command = recv_msg(conn)
        if command == "login":
            handle_login_request(conn)
        elif command == "address":
            handle_address_declaration(conn)
        elif command == "ping":
            send_msg(conn, "pong")
        elif command == "":
            break


def send_msg(conn, msg):
    msg = msg.encode(FORMAT)
    msg_len = len(msg)
    msg += b' ' * (MESSAGE_LEN - msg_len)
    conn.send(msg)
    print(f"SEND: {msg}")


def recv_msg(conn):
    res = conn.recv(MESSAGE_LEN).decode(FORMAT).strip()
    print(f"RECEIVE: {res}")
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


def listening():
    tracker_socket.bind(ADDR)
    tracker_socket.listen()
    print(f"Tracker is listening on {ADDR}")
    while True:
        conn, addr = tracker_socket.accept()
        thread = threading.Thread(target=handle_request, args=(conn, addr))
        thread.start()


def main():
    thread = threading.Thread(target=listening)
    thread.start()


if __name__ == "__main__":
    main()















