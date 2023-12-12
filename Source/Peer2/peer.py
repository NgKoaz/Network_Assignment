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
        #self.root.geometry("+500+150")
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
        self.login_frame.pack(padx=50, pady=50)
        self.login_field = ttk.Frame(master=self.login_frame)
        self.login_field.pack(pady=(0, 5))
        # GUI: Login frame -> Username field
        self.username_label = ttk.Label(master=self.login_field, text="Username", width=25)
        self.username_label.grid(row=0, columnspan=2, padx=5, pady=3, sticky="W")
        self.username_entry = ttk.Entry(master=self.login_field)
        self.username_entry.grid(row=1, columnspan=2, padx=5, pady=3, sticky="WE")
        # GUI: Login frame -> Password field
        self.password_label = ttk.Label(master=self.login_field, text="Password", width=25)
        self.password_label.grid(row=2, columnspan=2, padx=5, pady=5, sticky="W")
        self.password_entry = ttk.Entry(master=self.login_field)
        self.password_entry.grid(row=3, columnspan=2, padx=5, pady=5, sticky="WE")
        # GUI: Login frame -> Login button
        self.register_button = ttk.Button(master=self.login_field,
                                          style='Accent.TButton',
                                          text="Register",
                                          command=self.handle_register)
        self.register_button.grid(row=4, column=0, padx=5, pady=8)
        self.login_button = ttk.Button(master=self.login_field,
                                       style='Accent.TButton',
                                       text="Login",
                                       command=self.handle_login)
        self.login_button.grid(row=4, column=1, padx=5, pady=8)

        # GUI: Login frame -> Status label
        self.login_status_field = ttk.Frame(master=self.login_frame)
        self.login_status_field.pack(pady=(5, 0))
        self.login_status_label = ttk.Label(master=self.login_status_field, text="", width=35)
        self.login_status_label.grid(padx=5, pady=5)

        # GUI: Main screen
        self.main_frame = ttk.Frame(master=self.root)

        # GUI: Left and right frame
        self.left_frame = ttk.Frame(master=self.main_frame)
        self.left_frame.grid(row=0, column=0, padx=2, pady=5, sticky="N")
        self.right_frame = ttk.Frame(master=self.main_frame)
        self.right_frame.grid(row=0, column=1, padx=2, pady=(20, 5), sticky="N")

        # GUI: Left frame -> Publish frame
        self.publish_frame = ttk.LabelFrame(master=self.left_frame, text="Publish File")
        self.publish_frame.grid(row=0, column=0, padx=3, pady=5)
        # GUI: Publish frame -> Filepath entry
        self.filepath_label = ttk.Label(master=self.publish_frame, text="Filepath")
        self.filepath_label.grid(row=0, columnspan=3, padx=3, pady=3, sticky="W")
        self.filepath_entry = ttk.Entry(master=self.publish_frame)
        self.filepath_entry.grid(row=1, columnspan=2, padx=3, pady=5)
        self.browse_button = ttk.Button(master=self.publish_frame,
                                        style='Accent.TButton',
                                        text="Browse...",
                                        command=self.browse_file)
        self.browse_button.grid(row=1, column=2, padx=3, pady=5)
        # GUI: Publish frame -> Filename entry
        self.filename_label = ttk.Label(master=self.publish_frame, text="Filename")
        self.filename_label.grid(row=2, columnspan=3, padx=3, pady=3, sticky="W")
        self.filename_entry = ttk.Entry(master=self.publish_frame)
        self.filename_entry.grid(row=3, columnspan=3, padx=3, pady=5, sticky="WE")
        # GUI: Publish frame -> Publish button
        self.publish_button = ttk.Button(master=self.publish_frame,
                                         style='Accent.TButton',
                                         text="Publish",
                                         command=self.handle_publish)
        self.publish_button.grid(row=4, columnspan=3, pady=5)

        # GUI: Left frame -> Fetch frame
        self.fetch_frame = ttk.LabelFrame(master=self.left_frame, text="Fetch file")
        self.fetch_frame.grid(row=1, column=0, padx=3, pady=5, sticky="WE")
        # GUI: Fetch frame -> filename entry
        self.fetch_filename_label = ttk.Label(master=self.fetch_frame, text="Filename")
        self.fetch_filename_label.pack(padx=3, pady=3, fill="x")
        self.fetch_filename_entry = ttk.Entry(master=self.fetch_frame)
        self.fetch_filename_entry.pack(padx=3, pady=3, fill="x")
        # GUI: Fetch frame -> username entry
        self.fetch_owner_label = ttk.Label(master=self.fetch_frame, text="Owner")
        self.fetch_owner_label.pack(padx=3, pady=3, fill="x")
        self.fetch_owner_entry = ttk.Entry(master=self.fetch_frame)
        self.fetch_owner_entry.pack(padx=3, pady=3, fill="x")
        # GUI: Fetch frame -> Fetch button
        self.fetch_button = ttk.Button(master=self.fetch_frame,
                                       style='Accent.TButton',
                                       text="Fetch",
                                       command=self.handle_fetch)
        self.fetch_button.pack(padx=3, pady=3)

        # GUI: Right frame -> Tree frame
        self.tree_frame = ttk.Frame(master=self.right_frame)
        self.tree_frame.grid(row=0, column=0, sticky="N")
        # GUI: Tree frame -> tree scroll
        self.tree_scroll = ttk.Scrollbar(master=self.tree_frame)
        self.tree_scroll.pack(side="right", fill="y")
        # GUI: Tree frame -> tree view
        cols = ("Filename", "Owner")
        self.tree_view = ttk.Treeview(master=self.tree_frame, show="headings",
                                      yscrollcommand=self.tree_scroll.set,
                                      columns=cols, height=14)
        self.tree_view.pack()

        self.tree_view.column("Filename", width=200)
        self.tree_view.column("Owner", width=100)
        self.tree_view.pack()
        self.tree_scroll.config(command=self.tree_view.yview)
        self.tree_view.heading("Filename", text="Filename")
        self.tree_view.heading("Owner", text="Owner")
        self.tree_view.bind("<ButtonRelease-1>", func=self.handle_tree_view_click)

        # GUI: buttons_frame
        self.buttons_frame = ttk.Frame(master=self.right_frame)
        self.buttons_frame.grid(row=1, column=0, pady=3, sticky="WES")

        self.refresh_button = ttk.Button(master=self.buttons_frame,
                                         style='Accent.TButton',
                                         text="Refresh",
                                         command=self.handle_refresh_button)
        self.refresh_button.pack(padx=3, pady=3, side="left")

        # GUI: Log frame
        self.log_frame = ttk.Frame(master=self.main_frame)
        self.log_frame.grid(row=1, columnspan=2, padx=3, pady=3, sticky="WE")

        self.log_label = ttk.Label(master=self.log_frame, text="Log")
        self.log_label.pack(padx=3, pady=2, fill='x')

        self.log_textbox = tk.Text(master=self.log_frame, height=8)
        self.log_textbox.pack(padx=3, pady=2, fill='x')

        self.clear_button = ttk.Button(master=self.log_frame,
                                       style='Accent.TButton',
                                       text="Clear",
                                       command=self.clear_log)
        self.clear_button.pack(padx=3, pady=2, side="right")

        self.logout_button = ttk.Button(master=self.log_frame,
                                        style='Accent.TButton',
                                        text="Logout",
                                        command=self.logout)
        self.logout_button.pack(padx=3, pady=3, side="left")

        # Core:
        self.root.protocol("WM_DELETE_WINDOW", self.closing_window)
        self.root.mainloop()

    def logout(self):
        self.token = ""
        self.main_frame.pack_forget()
        self.username_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)
        self.root.title(f"P2P File Sharing")
        self.login_frame.pack(padx=50, pady=50)

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
            self.fetch_owner_entry.delete(0, tk.END)
            self.fetch_filename_entry.insert(0, filename)
            self.fetch_owner_entry.insert(0, owner)

    def get_file_list(self):
        # Checking whether folder do exists
        self.create_folder_if_not_exists()
        if os.path.exists(self.workspace_path + "/" + self.file_list_json_file):
            os.remove(self.workspace_path + "/" + self.file_list_json_file)

        # Check connection, if not connect
        if not self.connect_to_tracker():
            self.print_log("[ERROR] Get file list: Cannot connect to tracker!")
            return

        # Send `file list` request to tracker
        send_msg(self.tracker_socket, "file list")
        # Receive ACK of request
        if not recv_msg(self.tracker_socket) == "file list":
            self.print_log("[ERROR] Get file list: Not received confirmation message!")
            return
        # Waiting tracker communicate with database
        time.sleep(0.15)
        recv_file(self.tracker_socket, self.workspace_path + "/" + self.file_list_json_file)
        send_msg(self.tracker_socket, "file list success")
        self.print_log("[SUCCESS] Get file list")

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
            if recv_msg(self.tracker_socket) == "ping":
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

    def print_login_error(self, err_msg):
        self.login_status_label.configure(text=err_msg, foreground="red", width=35, anchor="center")

    def print_log(self, str_log):
        self.log_textbox.insert(1.0, str_log + '\n')

    def clear_log(self):
        self.log_textbox.delete(1.0, tk.END)

    def handle_register(self):
        self.print_login_error("Register...")

        username = self.username_entry.get()
        password = self.password_entry.get()

        # Check string before send. [:,|,',"] is not allow
        if not check_str_before_send(username):
            self.print_login_error("Do not use [ : | ] for username!")
            return
        if not check_str_before_send(password):
            self.print_login_error("Don't use [ : | ] for password")
            return
        if len(username) > 100 or len(password) > 100:
            self.print_login_error("Your username or password is too long")
            return
        if len(username) < 6 or len(password) < 6:
            self.print_login_error("Your username or password is too short")
            return

        # Check connection, if not connect
        if not self.connect_to_tracker():
            self.print_login_error("Cannot connect to tracker!")
            return
        # Send `register` type request
        send_msg(self.tracker_socket, "register")
        res = recv_msg(self.tracker_socket)
        if not res == "register":
            # Wrong process, we have to reconnect later
            self.tracker_socket.close()
            return
        # Send `username`, `password` to register
        msg = f"username:{username}|password:{password}"
        send_msg(self.tracker_socket, msg)
        time.sleep(0.05)

        # Receive register response
        res = recv_msg(self.tracker_socket)
        if res == "register fail":
            self.print_login_error("Register fail!")
        elif res == "register success":
            self.print_login_error("Register success!")
        else:
            self.print_login_error("[ERROR] Wrong process!")

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
            self.token = ""
            print("[ERROR] Login: Wrong process!")
            return False

    def handle_login(self):
        self.print_login_error("Login...")

        username = self.username_entry.get()
        password = self.password_entry.get()

        # Check string before send. [:,|,',"] is not allow
        if not check_str_before_send(username):
            self.print_login_error("Do not use [ : | ] for username!")
            return
        if not check_str_before_send(password):
            self.print_login_error("Don't use [ : | ] for password")
            return
        if len(username) > 100 and len(password) > 100:
            self.print_login_error("Your username or password is too long")
            return

        # Check connection, if not connect
        if not self.connect_to_tracker():
            self.print_login_error("Cannot connect to tracker!")
            return
        # Send `login` type request
        send_msg(self.tracker_socket, "login")
        res = recv_msg(self.tracker_socket)
        if not res == "login":
            # Wrong process, we have to reconnect later
            self.tracker_socket.close()
            return

        # Send `username`, `password` to login
        msg = f"username:{username}|password:{password}"
        send_msg(self.tracker_socket, msg)
        time.sleep(0.05)

        # Receive login response
        res = recv_msg(self.tracker_socket)
        if self.handle_login_response(res):
            self.root.title(f"P2P File Sharing [username: {username}]")
            self.enter_to_main_frame()
        else:
            self.print_login_error("Wrong password or username!")

    def authentication_process(self):
        # Send token for authorization
        send_msg(self.tracker_socket, f"token:{self.token}")
        res = recv_msg(self.tracker_socket)
        if res == "auth success":
            return True
        elif res == "auth fail":
            self.print_log("[FAIL] Authenticate.")
        else:
            self.print_log("[ERROR] Authentication: Wrong process!")
        return False

    def enter_to_main_frame(self):
        self.login_frame.pack_forget()
        self.main_frame.pack()
        thread = threading.Thread(target=self.listening)
        thread.daemon = True
        thread.start()

    def declare_address(self):
        if not self.connect_to_tracker():
            self.print_log("[ERROR] Address: Failed to connect to tracker!")
            return

        # Send `address` to come into handle_address_declaration process.
        send_msg(self.tracker_socket, "address")
        # Check ACK from tracker
        if not recv_msg(self.tracker_socket) == "address":
            self.print_log("[ERROR] Wrong process!")
            return
        # Authenticate with tracker by using jwt
        if not self.authentication_process():
            self.print_log("[ERROR] Authenticate fail!")
            return

        # Send `ip`, `port` to tracker
        msg = f"{self.peer_ip}:{self.listen_port}"
        send_msg(self.tracker_socket, msg)

        # Receive login response
        res = recv_msg(self.tracker_socket)
        if res == "address success":
            self.print_log("[SUCCESS] Give address to tracker!")
        else:
            self.print_log("[FAIL] Give address to tracker!")

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
        if not filepath or not is_valid_filepath(filepath):
            self.print_log("[ERROR] Publish: Invalid filepath!")
            return
        filename = self.filename_entry.get()
        if not filename:
            self.print_log("[ERROR] Publish: Filename is empty")
            return
        if not check_str_before_send(filename):
            self.print_log("[ERROR] Publish: Your filename must not contain [:, |]")
            return

        if not self.connect_to_tracker():
            self.print_log("[ERROR] Publish: Cannot connect to tracker!")
            return

        # Request `publish` service from tracker
        send_msg(self.tracker_socket, "publish")
        if not recv_msg(self.tracker_socket) == "publish":
            self.print_log("[ERROR] Publish: Wrong process! Tracker didn't send back type of request!")
            return
        # Authentication process
        if not self.authentication_process():
            self.print_log("[ERROR] Authenticate fail!")
            return
        # Send filename to tracker
        send_msg(self.tracker_socket, filename)
        # Receive last ACK
        res = recv_msg(self.tracker_socket)
        if res == "publish success":
            self.save_publish_file_at_local_storage(filepath, filename)
            self.print_log("[SUCCESS] Publish file!")
        else:
            stt, msg = res.split('|')
            msg = msg.split(':')[1]
            self.print_log(f"[FAIL] Publish file! {msg}")

    def fetch_file_from_peer(self, addr, download_directory, filename):
        addr, ip, port = addr.split(":")
        port = int(port)
        try:
            peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer_socket.connect((ip, port))
        except:
            self.print_log(f"[ERROR] Fetch: Cannot connect to peer {addr}")
            return

        # Send `fetch` request
        send_msg(peer_socket, "fetch")
        # Receive confirm request
        if not recv_msg(peer_socket) == "fetch":
            self.print_log("[ERROR] Fetch: Wrong process!")
            return False
        # Send filename
        send_msg(peer_socket, f"filename:{filename}")
        # Receive file status
        msg = recv_msg(peer_socket)
        if msg == "file not found":
            self.print_log("[FAIL] Fetch (PEER): Peer cannot found the file!")
            return False
        if not msg == "file found":
            self.print_log("[ERROR] Fetch (PEER): Wrong process!")
            return False
        # File is found, prepare to get file
        recv_file(peer_socket, download_directory + '/' + filename)
        # Send success
        send_msg(peer_socket, "fetch success")
        self.print_log("[SUCCESS] Fetch (PEER): Get file!")
        return True

    def handle_fetch(self):
        filename = self.fetch_filename_entry.get()
        if not filename:
            self.print_log("[ERROR] Fetch: Filename is empty!")
            return
        if not check_str_before_send(filename):
            self.print_log("[ERROR] Fetch: Filename field not allow : |")
            return
        username = self.fetch_owner_entry.get()
        if not username:
            self.print_log("[ERROR] Fetch: Username is empty!")
            return
        if not check_str_before_send(username) or not username:
            self.print_log("[ERROR] Fetch: Owner field do not allow : |")
            return
        download_filepath = filedialog.askdirectory(title="Choose a directory you want to save your file")
        if not download_filepath:
            self.print_log("[NOTIFY] Fetch: Please, choose your filepath to fetch!")
            return

        if not self.connect_to_tracker():
            self.print_log("[ERROR] Fetch: Cannot connect to tracker!")
            return

        send_msg(self.tracker_socket, "fetch")
        if not recv_msg(self.tracker_socket) == "fetch":
            self.print_log("[ERROR] Fetch: Not received confirmation message")
            return
        # Send file we need to fetch
        send_msg(self.tracker_socket, f"filename:{filename}|username:{username}")
        # Last ACK from trackers
        res = recv_msg(self.tracker_socket)
        # ######### Splot
        stt, msg = res.split("|")
        if stt == "fetch fail":
            self.print_log(f"[FAIL] Fetch (tracker): {msg}")
            return
        if not stt == "fetch success":
            self.print_log("[ERROR] Fetch (tracker): Wrong process!")
            return
        if self.fetch_file_from_peer(msg, download_filepath, filename):
            self.print_log(f"[SUCCESS] Fetch: Get {filename} from {msg}.")
        else:
            self.print_log(f"[FAIL] Fetch: Get {filename} from {msg}.")

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
            self.print_log("[SUCCESS] Discover")
        elif res == "discover fail":
            self.print_log("[FAIL] Discover")
        else:
            self.print_log("[ERROR]: Wrong process!")

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
            self.print_log("[SUCCESS] Fetch file!")
        elif res == "fetch fail":
            self.print_log("[FAIL] Fetch file!")
        else:
            self.print_log("[ERROR] Wrong process!")

    def handle_request(self, conn, addr):
        self.print_log(f"{addr} connected.")
        while True:
            command = recv_msg(conn)
            if command == "discover":
                self.file_discover(conn)
            elif command == "fetch":
                self.handle_fetch_request_from_another(conn)
            elif command == "ping":
                pass
            elif command == "":
                break

    def listening(self):
        if self.isListened:
            return
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
                thread.daemon = True
                thread.start()
            except Exception as e:
                self.print_log("Socket close: Peer stopped serving!")
                return

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