import socket
import threading
import platform  # For getting the operating system name
import subprocess  # For executing a shell command

MESSAGE_LEN = 256
PORT = 5050
PING_PORT = 5051
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
CHUNK_LEN = 1024

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

class Management:
    def __init__(self):
        self.sharing_file_list = [

        ]
        self.listening_peer_list = [

        ]

    # Dump all peer list
    def dump_peer_list(self):
        for item in self.listening_peer_list:
            print(item)

    # Dump all peer list
    def dump_file_list(self):
        for item in self.sharing_file_list:
            print(item)

management = Management()


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
    done = False
    while not done:
        data = conn.recv(1024)
        if data[-5:] == b"<END>":
            done = True
        else:
            file_bytes += data
    
    file = open(uri, "wb")
    file.write(file_bytes)

def send_message(conn, msg):
    msg = msg.encode(FORMAT)
    msg_len = len(msg)
    msg += b' ' * (MESSAGE_LEN - msg_len)
    conn.send(msg)

def recv_message(conn):
    res = conn.recv(MESSAGE_LEN).decode(FORMAT).strip()
    return res


def search_peer(conn, fname):
    for fn, socket_info in management.sharing_file_list.items():
        if fn == fname:
            send_message(conn, socket_info)
            break


def save_new_file_info(conn, req):
    cmd, fname, addr = req.split(' ')
    ip, port = addr.split(':')
    management.sharing_file_list.append({fname: f'{ip}: {port}'})
    for item in management.sharing_file_list:
        print(f"{item}")


def get_host_by_name(hostname):
    for peer_dict in management.listening_peer_list:
        for key in peer_dict.keys():
            if key == hostname:
                return peer_dict[key]


def discover(hostname):
    peer_ip, peer_port = get_host_by_name(hostname).split(':')

    peer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    peer.connect((peer_ip, int(peer_port)))

    send_message(peer, "discover")

    while True:
        data = recv_message(peer)
        if data[-5:] == "<END>":
            break
        management.sharing_file_list.append({data: f"{peer_ip}:{peer_port}"})

    peer.close()
    management.dump_file_list()

def ping(hostname):
    host, port = get_host_by_name(hostname).split(':')

    """
    Returns True if host (str) responds to a ping request.
    Remember that a host may not respond to a ping (ICMP) request even if the host name is valid.
    """
    # Option for the number of packets as a function of
    param = '-n' if platform.system().lower() == 'windows' else '-c'

    # Building the command. Ex: "ping -c 1 google.com"
    command = ['ping', param, '2', host]

    return subprocess.call(command) == 0


def ping_TCP(hostname):
    peer_ip, peer_port = get_host_by_name(hostname).split(":")

    peer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    peer.connect((peer_ip, int(peer_port)))

    send_message(peer, "ping")
    msg = recv_message(peer)
    if msg:
        print(f"[{hostname}] is online.")
    else:
        print(f"[{hostname}] is offline.")

    peer.close()





def handle_request(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    #Receive message contains info of peer
    hostname, listening_socket = recv_message(conn).split(' ')
    management.listening_peer_list.append({hostname: listening_socket})

    management.dump_peer_list()

    while True:
        req = recv_message(conn)
        print(req)
        if req[0:5] == 'fetch':
            search_peer(conn, req[6:])
        elif req[0:7] == 'publish':
            save_new_file_info(conn, req)
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
        cmd, hostname = cmd.split(' ')
        if cmd == "discover":
            discover(hostname)
        elif cmd == "ping":
            ping_TCP(hostname)
        else:
            print("WRONG CMD!!! TRY AGAIN...")


print("[Starting] server is staring...")
start()






