import socket
import threading

MESSAGE_LEN = 512
CHUNK_LEN = 1024
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"

SERVER = socket.gethostbyname(socket.gethostname())
PORT = 5051
ADDR = (SERVER, PORT)
file_list_dir = './sharingFileList'

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

listening_peer_list = []


# Dump all peer list
def dump_peer_list():
    for item in listening_peer_list:
        print(item)


# Dump all file in sharing file list.
def dump_file_list():
    file = open(file_list_dir, 'r')
    while True:
        line = file.readline().rstrip()
        if not line:
            break
        print(line)
    file.close()


def send_file_list(conn, uri):
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


def search_peer(conn, fname):
    file = open(file_list_dir, 'r')
    while True:
        line = file.readline().rstrip()
        if not line:
            break
        filename, addr = line.split('*')
        if filename == fname:
            send_msg(conn, addr)
            return
    send_msg(conn, "<NOT FOUND>")


def is_duplicated_file(fname):
    file = open(file_list_dir, 'r')
    while True:
        line = file.readline().rstrip()
        if not line:
            break
        filename, addr = line.split('*')
        if filename == fname:
            return True
    return False


def append_sharing_file_list(fname, ip, port):
    try:
        file = open(file_list_dir, 'a')
        file.write(f"{fname}*{ip}:{port}\n")
        print(f"{ip}:{port} are sharing {fname}")
        return True
    except:
        print("Cannot open sharing file list!")
    return False


def save_new_file_info(conn, req):
    cmd, fname, addr = req.split('*')
    ip, port = addr.split(':')

    if not is_duplicated_file(fname):
        if append_sharing_file_list(fname, ip, port):
            send_msg(conn, "publish ok")
            dump_file_list()
        else:
            send_msg(conn, "publish server error")
    else:
        send_msg(conn, "publish duplicated filename")


def get_host_by_name(hostname):
    for peer_dict in listening_peer_list:
        for key in peer_dict.keys():
            if key == hostname:
                return peer_dict[key]


def discover(hostname):
    peer_ip, peer_port = get_host_by_name(hostname).split(':')
    peer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    peer.connect((peer_ip, int(peer_port)))

    send_msg(peer, "discover")

    while True:
        fname = recv_msg(peer)
        if fname[-5:] == "<END>":
            break
        append_sharing_file_list(fname, peer_ip, peer_port)
    peer.close()
    dump_file_list()


def send_list(conn):
    file = open(file_list_dir, 'r')
    while True:
        line = file.readline().rstrip()
        if not line:
            break
        filename, addr = line.split('*')
        send_msg(conn, filename)
    send_msg(conn, "<END>")
    file.close()


def ping_TCP(hostname):
    peer_ip, peer_port = get_host_by_name(hostname).split(":")

    peer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    peer.connect((peer_ip, int(peer_port)))

    msg_send = "ping"
    send_msg(peer, msg_send)

    msg = recv_msg(peer)
    if msg:
        print(f"[{hostname}] is online.")
    else:
        print(f"[{hostname}] is offline.")

    peer.close()


def handle_request(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")

    # Receive message contains info of peer
    hostname, listening_socket = recv_msg(conn).split(' ')
    listening_peer_list.append({hostname: listening_socket})

    dump_peer_list()

    while True:
        # Wait message.
        req = recv_msg(conn)
        print(req)
        if req[0:5] == 'fetch':
            search_peer(conn, req[6:])
        elif req[0:7] == 'publish':
            save_new_file_info(conn, req)
        elif req[0:8] == 'get list':
            send_list(conn)
        else:
            break
    conn.close()


def listening():
    server.listen()
    print(f"[Listening] Server is listening on {SERVER}")
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_request, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTION] {addr}")


def start():
    thread = threading.Thread(target=listening)
    thread.start()
    while True:
        cmd = input()
        hostname = ""
        try:
            cmd, hostname = cmd.split(' ')
        except:
            print("WRONG COMMAND!!! TRY AGAIN...")
        if cmd == "discover":
            discover(hostname)
        elif cmd == "ping":
            ping_TCP(hostname)
        else:
            print("WRONG COMMAND!!! TRY AGAIN...")


print("[Starting] server is staring...")
start()






