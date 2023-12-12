import socket
import threading
import os
import jwt
import json
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


def register(username, password):
    result = database.users.find_one({"username": username})
    if not result:
        database.users.insert_one({"username": username, "password": password})
        return True
    # register fail
    return False


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


def handle_register_request(conn):
    # Send back to confirm request for peer
    send_msg(conn, "register")
    # Receive username and password from peer
    msg = recv_msg(conn)
    username, password = handle_login_info(msg)
    # Check username, password
    if register(username, password):
        # Send empty token
        msg = f"register success"
    else:
        msg = f"register fail"
    send_msg(conn, msg)


def handle_token_msg(token):
    token = token.split(":")[1]
    return jwt.decode(token, KEY, algorithms=['HS256'])


def handle_address_info(msg):
    pass


def authenticate_peer(conn):
    token = recv_msg(conn)
    payload = handle_token_msg(token)
    user_id = payload['_id']
    if user_id:
        send_msg(conn, "auth success")
        return user_id
    else:
        send_msg(conn, "auth fail")
        return ""


def handle_address_declaration(conn):
    # Send back to confirm request for peer
    send_msg(conn, "address")
    # Authentication process
    user_id = authenticate_peer(conn)
    if not user_id:
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


def handle_publish_request(conn):
    # Send back to confirm going to publish process.
    send_msg(conn, "publish")
    # Authenticate peer
    user_id = authenticate_peer(conn)
    if not user_id:
        return
    # Receive filname from peer
    filename = recv_msg(conn)

    # Update database
    # Check whether filename is empty.
    if not filename:
        send_msg(conn, "publish fail|msg: Your filename is empty!")
        return
    # Check whether filename is duplicated.
    result = database.files.find_one(
        {"filename": filename, "user_id": user_id}
    )
    if result:
        send_msg(conn, "publish fail|msg: Your filename is duplicated with a file you upload before!")
        return
    # No duplicate, insert into `files` collection.
    database.files.insert_one({
        "user_id": user_id,
        "filename": filename
    })
    send_msg(conn, "publish success")


def handle_no_publish_request(conn):
    # Send `no publish` back
    send_msg("no publish")
    # Authentication process
    user_id = authenticate_peer(conn)
    if not user_id:
        return
    # get filename
    msg = recv_msg(conn)
    filename = msg.split(":")[1]
    database.files.delete_one({"user_id": user_id, "filename": filename})


def handle_fetch_request(conn):
    # Send back to confirm `fetch` request from user
    send_msg(conn, "fetch")
    # Receive `filename` and `username` from peer
    req = recv_msg(conn)
    # Split
    filename, username = req.split("|")
    filename = filename.split(":")[1]
    username = username.split(":")[1]

    # Send last ACK
    # Checking whether username does exist
    result = database.users.find_one({"username": username})
    if not result:
        send_msg(conn, "fetch fail|msg: Username you provided is not found!")
        return
    user_id = str(result["_id"])
    user_addr = str(result["address"])
    if not user_addr:
        send_msg(conn, "fetch fail|msg: Username is not online!")
        return
    # Checking whether filename belongs to that user
    result = database.files.find_one({"user_id": ObjectId(user_id), "filename": filename})
    if not result:
        send_msg(conn, "fetch fail|msg: This username don't have this file!")
        return
    # Fetch success
    send_msg(conn, f"fetch success|address:{user_addr}")


def handle_get_file_list(conn):
    # Send back `file list` to confirm
    send_msg(conn, "file list")
    # Get file list from data base then save in the file
    data = database.files.aggregate([
        {
            "$lookup": {
                "from": "users",
                "localField": "user_id",
                "foreignField": "_id",
                "as": "user"
            }
        },
        {
            "$project": {
                "_id": 0,
                "user_id": 1,
                "filename": 1,
                "user.username": 1
            }
        }
    ])
    str_data = '''
    []
    '''
    js_data = json.loads(str_data)

    for d in list(data):
        if d["user"]:
            js_data.append(
                {"filename": d["filename"], "username": d["user"][0]["username"]}
            )
        else:
            print(d["filename"])

    with open("./data/file-list.json", "w") as file:
        json.dump(js_data, file, indent=4)

    send_file(conn, "./data/file-list.json")
    if not recv_msg(conn) == "file list success":
        print("Peer cannot get file!")
    print("Peer get file-list file success!")


def handle_request(conn, addr):
    print(f"{addr} connected.")
    while True:
        command = recv_msg(conn)
        if command == "login":
            handle_login_request(conn)
        elif command == "register":
            handle_register_request(conn)
        elif command == "address":
            handle_address_declaration(conn)
        elif command == "publish":
            handle_publish_request(conn)
        elif command == "no publish":
            handle_no_publish_request(conn)
        elif command == "fetch":
            handle_fetch_request(conn)
        elif command == "file list":
            handle_get_file_list(conn)
            pass
        elif command == "ping":
            send_msg(conn, "ping")
        elif command == "":
            break


def cml_user_list():
    result = database.users.find()
    print("-------------- USER LIST -------------")
    for user in result:
        print(f"username={user['username']}")
    print("-------------- END USER LIST -------------")


def cml_discover():
    pass


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
        thread.daemon = True
        thread.start()


def main():
    thread = threading.Thread(target=listening)
    thread.daemon = True
    thread.start()
    while True:
        cmd = input()
        if cmd == "user list":
            cml_user_list()
        elif cmd == "discover":
            cml_discover()
        elif cmd == "exit":
            break


if __name__ == "__main__":
    main()















