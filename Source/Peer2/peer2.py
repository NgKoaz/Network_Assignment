import socket
import time
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import threading
import json
import os
from dotenv import load_dotenv
import re


MESSAGE_LEN = 512
CHUNK_LEN = 1024
FORMAT = 'utf-8'


load_dotenv()
TRACKER_IP = os.getenv("TRACKER_IP")
TRACKER_PORT = int(os.getenv("TRACKER_PORT"))
TRACKER_ADDR = (TRACKER_IP, TRACKER_PORT)


class MyGUI:
    def __init__(self):
        # GUI: Create root
        self.root = tk.Tk()
        self.root.geometry("+500+150")
        self.root.title("P2P File Sharing")
        self.root.tk.call('source', './Forest-ttk-theme/forest-light.tcl')
        ttk.Style().theme_use('forest-light')

        # Core: Create socket to listen connection from other peer.
        self.peer_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.peer_ip = socket.gethostbyname(socket.gethostname())
        self.listen_port = 9092
        self.isListened = False
        self.token = ""
        self.workspace_path = os.getenv("WORKSPACE_PATH")
        self.data_json_file = "data.json"
        self.file_list_json_file = "file-list.json"

        self.tracker_socket = None

        # GUI: Login screen
        self.login_frame = ttk.Frame(master=self.root)
        self.login_frame.pack()
        # GUI: Username field
        self.username_label = ttk.Label(master=self.login_frame, text="Username")
        self.username_label.pack()
        self.username_entry = ttk.Entry(master=self.login_frame)
        self.username_entry.pack()
        # GUI: Password field
        self.password_label = ttk.Label(master=self.login_frame, text="Password")
        self.password_label.pack()
        self.password_entry = ttk.Entry(master=self.login_frame)
        self.password_entry.pack()
        # GUI: Login butotn
        self.login_button = ttk.Button(master=self.login_frame, text="Login", command=self.handle_login)
        self.login_button.pack()
        # GUI: Status label
        # Add status label here (TO DO)

        # GUI: Main screen
        self.main_frame = ttk.Frame(master=self.root)

        # GUI: Main -> Publish frame
        self.publish_frame = ttk.Frame(master=self.main_frame)
        self.publish_frame.grid(row=0, column=0, padx=5, pady=5)
        # GUI: Publish frame -> Filepath entry
        self.filepath_entry = ttk.Entry(master=self.publish_frame)
        self.filepath_entry.pack()
        self.browse_button = ttk.Button(master=self.publish_frame, text="Browse...", command=self.browse_file)
        self.browse_button.pack()
        # GUI: Publish frame -> Filename entry
        self.filename_entry = ttk.Entry(master=self.publish_frame)
        self.filename_entry.pack()
        # GUI: Publish frame -> Publish button
        self.publish_button = ttk.Button(master=self.publish_frame, text="Publish", command=self.handle_publish)
        self.publish_button.pack()

        # GUI: Main -> Fetch frame
        self.fetch_frame = ttk.Frame(master=self.main_frame)
        self.fetch_frame.grid(row=0, column=1, padx=5, pady=5)
        # GUI: Fetch frame -> Tree frame
        self.tree_frame = ttk.Frame(master=self.fetch_frame)
        self.tree_frame.pack()
        # GUI: Tree frame -> tree scroll
        self.tree_scroll = ttk.Scrollbar(master=self.tree_frame)
        self.tree_scroll.pack(side="right", fill="y")
        # GUI: Tree frame -> tree view
        cols = ("Filename", "Owner")
        self.tree_view = ttk.Treeview(master=self.tree_frame, show="headings",
                                      yscrollcommand=self.tree_scroll.set,
                                      columns=cols, height=13)
        self.tree_view.pack()

        self.tree_view.column("Filename", width=200)
        self.tree_view.column("Owner", width=100)
        self.tree_view.pack()
        self.tree_scroll.config(command=self.tree_view.yview)
        self.tree_view.heading("Filename", text="Filename")
        self.tree_view.heading("Owner", text="Owner")
        self.tree_view.bind("<ButtonRelease-1>", func=self.handle_tree_view_click)
        self.refresh_button = ttk.Button(master=self.tree_frame, text="Refresh", command=self.handle_refresh_button)
        self.refresh_button.pack()

        # GUI: Fetch frame -> filename entry
        self.fetch_filename_entry = ttk.Entry(master=self.fetch_frame)
        self.fetch_filename_entry.pack()
        # GUI: Fetch frame -> username entry
        self.fetch_username_entry = ttk.Entry(master=self.fetch_frame)
        self.fetch_username_entry.pack()
        # GUI: Fetch frame -> Fetch button
        self.fetch_button = ttk.Button(master=self.fetch_frame, text="Fetch", command=self.handle_fetch)
        self.fetch_button.pack()

        # Core:
        self.root.protocol("WM_DELETE_WINDOW", self.closing_window)
        self.root.mainloop()

    def refresh_tree_view_data(self):
        # Clear all old data.
        for item in self.tree_view.get_children():
            self.tree_view.delete(item)
        # Load new data
        with open("./data/file-list.json", "r") as file:
            js_data = json.load(file)
            for data in list(js_data):
                self.tree_view.insert("", tk.END, values=(data['filename'], data['username']))

    def handle_refresh_button(self):
        self.get_file_list()
        self.refresh_tree_view_data()

    def handle_tree_view_click(self, event):
        # Get the selected item
        selected_item = self.tree_view.selection()
        if selected_item:
            filename, owner = self.tree_view.item(selected_item, "values")
            self.fetch_filename_entry.delete(0, tk.END)
            self.fetch_username_entry.delete(0, tk.END)
            self.fetch_filename_entry.insert(0, filename)
            self.fetch_username_entry.insert(0, owner)

    def get_file_list(self):
        # Checking whether folder do exists
        self.create_folder_if_not_exists()
        if os.path.exists(self.workspace_path + "/" + self.file_list_json_file):
            os.remove(self.workspace_path + "/" + self.file_list_json_file)
        # Send `file list` request to tracker
        send_msg(self.tracker_socket, "file list")
        # Receive ACK of request
        if not recv_msg(self.tracker_socket) == "file list":
            print("Not received confirmation message from tracker")
            return
        # Waiting tracker communicate with database
        time.sleep(0.15)
        recv_file(self.tracker_socket, self.workspace_path + "/" + self.file_list_json_file)
        send_msg(self.tracker_socket, "file list success")

    def browse_file(self):
        filepath = filedialog.askopenfilename(title="Choose a file you want to publish")
        self.filepath_entry.delete(0, tk.END)
        self.filepath_entry.insert(0, filepath)
        self.filename_entry.delete(0, tk.END)
        self.filename_entry.insert(0, filepath.split('/').pop())

    def create_folder_if_not_exists(self):
        if not os.path.exists(self.workspace_path):
            os.makedirs(self.workspace_path)

    def create_json_file_if_not_exists(self, filename):
        uri = self.workspace_path + "/" + filename
        file = open(uri, "r")
        js_data = file.read(512)
        if js_data:
            return
        file.close()
        # Create a new form for json
        file = open(uri, "w")
        str_data = '''
        []
        '''
        js_data = json.loads(str_data)
        json.dump(js_data, file)
        file.close()

    def check_connection(self):
        if not self.tracker_socket:
            return False
        # Send ping to check whether this connection is alive.
        try:
            send_msg(self.tracker_socket, "ping")
            if recv_msg(self.tracker_socket) == "pong":
                return True
        except Exception as e:
            print(e)
        return False

    def connect_to_tracker(self):
        if self.check_connection():
            return True
        # Create new connection, when we have no connection before.
        try:
            self.tracker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tracker_socket.connect(TRACKER_ADDR)
        except Exception as e:
            print(e)
            return False
        return True

    def handle_login_response(self, res):
        # Pattern of response is "msg|token:<value>"
        msg, token = res.split("|")
        if msg == "login fail":
            self.token = ""
            return False
        elif msg == "login success":
            self.token = token.split(":")[1]
            return True
        else:
            print("[LOGIN ERROR] ERROR FROM PROGRAM! WRONG PROCESS PROTOCOL")
            return False

    def handle_login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        # Check string before send. [:,|,',"] is not allow
        if not check_str_before_send(username):
            print("Don't use : and | \' \" for username")
        if not check_str_before_send(password):
            print("Don't use : and | \' \" for password")

        # Check connection, if not connect
        if not self.connect_to_tracker():
            print("Cannot connect to tracker!")
            return
        # Send `login` type request
        send_msg(self.tracker_socket, "login")
        res = recv_msg(self.tracker_socket)
        if not res == "login":
            # Wrong process, we have to reconnect later
            self.tracker_socket.close()

        # Send `username`, `password` to login
        msg = f"username:{username}|password:{password}"
        if len(msg) > 1024:
            print("ERROR OUT OF LENGTH")
            return
        send_msg(self.tracker_socket, msg)
        time.sleep(0.05)

        # Receive login response
        res = recv_msg(self.tracker_socket)
        if self.handle_login_response(res):
            print("Login success")
            self.root.title(f"P2P File Sharing [username: {username}]")
            self.enter_to_main_frame()
        else:
            print("Wrong password or username!")

    def authentication_process(self):
        # Send token for authorization
        send_msg(self.tracker_socket, f"token:{self.token}")
        res = recv_msg(self.tracker_socket)
        if res == "auth success":
            return True
        elif res == "auth fail":
            print("Authorize fail")
        else:
            print("Wrong process!")
        return False

    def enter_to_main_frame(self):
        self.login_frame.pack_forget()
        self.main_frame.pack()
        thread = threading.Thread(target=self.listening)
        thread.start()

    def declare_address(self):
        if not self.connect_to_tracker():
            print("Failed to connect to tracker!")

        # Send `address` to come into handle_address_declaration process.
        send_msg(self.tracker_socket, "address")
        # Check ACK from tracker
        if not recv_msg(self.tracker_socket) == "address":
            print("[ERROR] Wrong process!")
        # Authenticate with tracker by using jwt
        if not self.authentication_process():
            return

        # Send `ip`, `port` to tracker
        msg = f"{self.peer_ip}:{self.listen_port}"
        send_msg(self.tracker_socket, msg)

        # Receive login response
        res = recv_msg(self.tracker_socket)
        if res == "address success":
            print(res)
        else:
            print(res)

    def save_publish_file_at_local_storage(self, filepath, filename):
        # Saving into file
        self.create_folder_if_not_exists()
        self.create_json_file_if_not_exists(self.data_json_file)
        file = open(self.workspace_path + "/data.json", "r")
        js_data = json.load(file)
        file.close()

        file = open(self.workspace_path + "/data.json", "w")
        js_data.append({"filepath": filepath, "filename": filename})
        json.dump(js_data, file, indent=4)
        file.close()

    def handle_publish(self):
        # Checking filepath and filename
        filepath = self.filepath_entry.get()
        if not is_valid_filepath(filepath):
            print("Invalid filepath!!!")
        filename = self.filename_entry.get()
        if not check_str_before_send(filename):
            print("Your filename must not contain [:, |]")

        # Request `publish` service from tracker
        send_msg(self.tracker_socket, "publish")
        if not recv_msg(self.tracker_socket) == "publish":
            print("WRONG PROCESS!")
            return
        # Authentication process
        self.authentication_process()
        # Send filename to tracker
        send_msg(self.tracker_socket, filename)
        # Receive last ACK
        res = recv_msg(self.tracker_socket)
        if res == "publish success":
            self.save_publish_file_at_local_storage(filepath, filename)
            print(res)
        elif res == "publish fail":
            stt, msg = res.split('|')
            msg = msg.split(':')[1]
            print(msg)
        else:
            print("WRONG LAST ACK")

    def fetch_file_from_peer(self, addr, download_directory, filename):
        addr, ip, port = addr.split(":")
        port = int(port)
        peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        peer_socket.connect((ip, port))
        # Send `fetch` request
        send_msg(peer_socket, "fetch")
        # Receive confirm request
        if not recv_msg(peer_socket) == "fetch":
            print("Cannot get confirmation from another peer")
            return
        # Send filename
        send_msg(peer_socket, f"filename:{filename}")
        # Receive file status
        msg = recv_msg(peer_socket)
        if msg == "file not found":
            print("This file may be deleted from this peer!")
            return
        if not msg == "file found":
            print("WRONG PROCESS!!!!")
            return
        # File is found, prepare to get file
        recv_file(peer_socket, download_directory + '/' + filename)
        # Send success
        send_msg(peer_socket, "fetch success")

    def handle_fetch(self):
        filename = self.fetch_filename_entry.get()
        if not check_str_before_send(filename):
            print("Filename not allow : |")
            return
        username = self.fetch_username_entry.get()
        if not check_str_before_send(username):
            print("Username not allow : |")
            return
        download_filepath = filedialog.askdirectory(title="Choose a directory you want to save your file")
        if not download_filepath:
            print("Please, choose your filepath to fetch!")

        send_msg(self.tracker_socket, "fetch")
        if not recv_msg(self.tracker_socket) == "fetch":
            print("WRONG PROCESS")
            return
        # Send file we need to fetch
        send_msg(self.tracker_socket, f"filename:{filename}|username:{username}")
        # Last ACK from trackers
        res = recv_msg(self.tracker_socket)
        # ######### Splot
        stt, msg = res.split("|")
        if stt == "fetch fail":
            print(msg)
            return
        if not stt == "fetch success":
            print("WRONG FETCH PROCESS")
            return

        if self.fetch_file_from_peer(msg, download_filepath, filename):
            print(f"FETCH {filename} from {msg} SUCCESS")
        else:
            print(f"FETCH FAIL!!!")

    def file_discover(self, conn):
        # Make sure the uri is an existed json file
        self.create_folder_if_not_exists()
        # self.create_json_file_if_not_exists()
        uri = self.workspace_path + '/data.json'
        # Send back to confirm `discover` request
        send_msg(conn, "discover")
        send_file(conn, uri)
        res = recv_msg(conn)
        if res == "discover success":
            print(res)
        elif res == "discover fail":
            print(res)
        else:
            print("NOT SYNC")

    def handle_fetch_request_from_another(self, conn):
        # Send back `fetch` to confirm.
        send_msg(conn, "fetch")
        # Receive filename from another peer
        filename = recv_msg(conn).split(":")[1]
        filepath = ""

        # Look up filename
        file = open(self.workspace_path + "/data.json", "r")
        data_js = json.load(file)
        for f in data_js:
            print(f)
            if f['filename'] == filename:
                filepath = f['filepath']
                break
        # If file is found, tell that peer prepare to recv_file
        if not filepath:
            send_msg(conn, "file not found")
            return
        send_msg(conn, "file found")
        send_file(conn, filepath)

        res = recv_msg(conn)
        if res == "fetch success":
            print("FETCH OK")
        elif res == "fetch fail":
            print("Fetch fail")
        else:
            print("WRONG FETCH PROCESS!!")

    def handle_request(self, conn, addr):
        print(f"{addr} connected.")
        while True:
            command = recv_msg(conn)
            if command == "discover":
                self.file_discover(conn)
            elif command == "fetch":
                self.handle_fetch_request_from_another(conn)
            elif command == "":
                break

    def listening(self):
        self.peer_server.bind((self.peer_ip, self.listen_port))
        self.peer_server.listen()
        self.isListened = True
        # Inform to tracker
        self.declare_address()

        # Accept and handle connection
        while True:
            try:
                conn, addr = self.peer_server.accept()
                thread = threading.Thread(target=self.handle_request, args=(conn, addr))
                thread.start()
            except Exception as e:
                print("Socket close: Peer stopped serving!")
                break

    def closing_window(self):
        try:
            self.tracker_socket.close()
        except Exception as e:
            print(e)
        if self.isListened:
            self.peer_server.close()
        self.root.destroy()


def is_valid_filepath(filepath):
    return os.path.exists(filepath)


def check_str_before_send(_str):
    pattern = re.compile(r"[:|]")
    return not bool(pattern.search(_str))


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


def send_file(conn, filepath):
    file = open(filepath, "rb")
    while True:
        data = file.read(CHUNK_LEN)
        if not data:
            break
        conn.send(data)
    conn.send(b"<END>")
    file.close()


def recv_file(conn, filepath):
    file = open(filepath, "ab")
    while True:
        chunk = conn.recv(CHUNK_LEN)
        if chunk[-5:] == b"<END>":
            break
        file.write(chunk)
    file.close()


# Run
MyGUI()
