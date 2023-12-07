import socket
import customtkinter as ctk
from customtkinter import filedialog
import threading
import os

MESSAGE_LEN = 512
CHUNK_LEN = 1024
FORMAT = 'utf-8'

ctk.set_appearance_mode("Light")

class MyGUI:
    def __init__(self):
        # GUI: Create root
        self.root = ctk.CTk()
        # self.root.geometry("500x500+200+100")
        self.root.title("File Sharing")

        # Core: Create ip, port to listen connection from other peer.
        self.peer_ip = socket.gethostbyname(socket.gethostname())
        self.listen_port = 9092
        self.peerServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.isConnected = False
        self.isListened = False
        self.file_list = []
        self.repository = './publish_file_list2'

        # GUI + Core: Create tracker ip, port to connect Tracker in P2P network
        self.tracker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # GUI: Create entities to connect to the tracker
        self.mainFrame = ctk.CTkFrame(master=self.root)
        self.mainFrame.pack(padx=10, pady=10)

        self.connectionFrame = ctk.CTkFrame(master=self.mainFrame)
        self.connectionFrame.grid(row=0, column=0, padx=10, pady=10)

        self.hostname_label = ctk.CTkLabel(master=self.connectionFrame, text="Your hostname")
        self.hostname_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.hostname_entry = ctk.CTkEntry(master=self.connectionFrame)
        self.hostname_entry.grid(row=1, column=0, padx=5)

        self.tracker_ip_label = ctk.CTkLabel(master=self.connectionFrame, text="Tracker IP")
        self.tracker_ip_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.tracker_ip_entry = ctk.CTkEntry(master=self.connectionFrame)
        self.tracker_ip_entry.grid(row=1, column=1, padx=5)

        self.tracker_port_label = ctk.CTkLabel(master=self.connectionFrame, text="Tracker port")
        self.tracker_port_label.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.tracker_port_entry = ctk.CTkEntry(master=self.connectionFrame)
        self.tracker_port_entry.grid(row=1, column=2, padx=5)

        self.button1 = ctk.CTkButton(master=self.connectionFrame,
                                     text="Click here to connect!",
                                     command=self.connect_to_tracker)
        self.button1.grid(row=2, columnspan=3, pady=5)

        # GUI: Create GUI to find and fetch file.
        self.fetchFrame = ctk.CTkFrame(master=self.mainFrame)
        self.fetchFrame.grid(row=1, column=0, padx=10, pady=10)

        self.fetchLabel = ctk.CTkLabel(master=self.fetchFrame,
                                       text="Fetch file")
        self.fetchLabel.grid(row=0, column=0, pady=2, columnspan=2)

        self.refreshButton = ctk.CTkButton(master=self.fetchFrame,
                                           text="Refresh",
                                           command=self.handle_refresh_button)
        self.refreshButton.grid(row=1, column=0, pady=3, sticky="w")

        self.text_combobox = ctk.StringVar()
        self.files_combobox = ctk.CTkComboBox(master=self.fetchFrame,
                                              height=30,
                                              width=300,
                                              values=self.file_list,
                                              variable=self.text_combobox)
        self.files_combobox.grid(row=2, column=0, padx=2, pady=3)

        self.fetchButton = ctk.CTkButton(master=self.fetchFrame,
                                         text="Fetch",
                                         command=self.handle_fetch_button)
        self.fetchButton.grid(row=2, column=1, padx=2)

        # GUI: Create GUI to publish file
        self.publishFrame = ctk.CTkFrame(master=self.mainFrame)
        self.publishFrame.grid(row=2, column=0)

        #   Row 0
        self.labelPublish = ctk.CTkLabel(master=self.publishFrame,
                                         text="Publish file")
        self.labelPublish.grid(row=0, columnspan=2)
        #   Row 1
        self.dirEntry = ctk.CTkEntry(master=self.publishFrame,
                                     width=300,
                                     height=30)
        self.dirEntry.grid(row=1, column=0, padx=2)

        self.importButton = ctk.CTkButton(master=self.publishFrame,
                                          text="Browse...",
                                          command=self.browse_file)
        self.importButton.grid(row=1, column=1, padx=2)
        #   Row 2
        self.newNameLabel = ctk.CTkLabel(master=self.publishFrame, text="Create a new name")
        self.newNameLabel.grid(row=2, columnspan=2, sticky="w", padx=2, pady=5)
        #   Row 3
        self.newNameEntry = ctk.CTkEntry(master=self.publishFrame,
                                         height=30,
                                         placeholder_text="Enter new file name")
        self.newNameEntry.grid(row=3, columnspan=2, sticky="ew", padx=2)
        #   Row 4
        self.importButton = ctk.CTkButton(master=self.publishFrame,
                                          text="Publish",
                                          command=self.handle_publish_button)
        self.importButton.grid(row=4, columnspan=2, pady=10)

        # GUI: Console frame
        self.consoleFrame = ctk.CTkFrame(master=self.mainFrame)
        self.consoleFrame.grid(row=3, column=0, padx=10, pady=20, sticky='ew')

        #   GUI: Create Input
        # self.inputFrame = ctk.CTkFrame(master=self.consoleFrame)
        # self.inputFrame.pack()

        # self.inputEntry = ctk.CTkEntry(master=self.inputFrame,
        #                               height=30,
        #                               width=300,
        #                               placeholder_text="Write your command")
        # self.inputEntry.grid(row=0, column=0, padx=2)

        # self.enterButton = ctk.CTkButton(master=self.inputFrame, text="Enter")
        # self.enterButton.grid(row=0, column=1, padx=2)

        #   GUI: Create output
        self.outputFrame = ctk.CTkFrame(master=self.consoleFrame)
        self.outputFrame.pack(fill="x")

        self.consoleLabel = ctk.CTkLabel(master=self.outputFrame, text="Output log")
        self.consoleLabel.pack(pady=1, anchor="nw")

        self.consoleTextbox = ctk.CTkTextbox(master=self.outputFrame, height=150)
        self.consoleTextbox.pack(fill="x")

        thread = threading.Thread(target=self.listening)
        thread.start()

        self.root.protocol("WM_DELETE_WINDOW", self.closing)
        self.root.mainloop()

    def closing(self):
        self.isListened = False
        self.tracker_socket.close()
        self.peerServer.close()
        self.root.destroy()

    def listening(self):
        if self.isListened:
            return
        self.isListened = True
        self.peerServer.bind((self.peer_ip, self.listen_port))

        self.write_log(f"Peer is listening on {self.peer_ip}:{self.listen_port}")

        self.peerServer.listen()
        while self.isListened:
            conn, addr = self.peerServer.accept()
            thread = threading.Thread(target=self.handle_request, args=(conn, addr))
            thread.start()

    def handle_request(self, conn, addr):
        self.write_log(f"Connection from {addr}")
        try:
            msg = recv_msg(conn)
            if msg[0:5] == "fetch":
                self.handle_fetch_request(conn, msg[6:])
            elif msg == "discover":
                self.send_file_list(conn)
            elif msg == "ping":
                self.ping_reaction(conn)
            else:
                pass
        except:
            self.write_log(f"{addr} was disconnected!")

    def send_file_list(self, conn):
        file = open(self.repository, "r")
        while True:
            line = file.readline().rstrip()
            if not line:
                break
            filename = line.split('*')[0]
            send_msg(conn, filename)
        send_msg("<END>")
        file.close()

    def ping_reaction(self, conn):
        send_msg(conn, "pong")

    def handle_fetch_request(self, conn, filename):
        l_dir = self.find_local_dir(filename)
        if not l_dir:
            self.write_log("Handle fetch request: Cannot find local directory")
        else:
            self.write_log(l_dir)
            send_file(conn, l_dir)

    def find_local_dir(self, filename):
        file = open(self.repository, "r")
        while True:
            line = file.readline().rstrip()
            if not line:
                break
            f_name, local_directory = line.split('*')
            if f_name == filename:
                return local_directory
        return ""

    def connect_to_tracker(self):
        if self.isConnected:
            return
        new_log = ""
        try:
            self.tracker_socket.connect((self.tracker_ip_entry.get(), int(self.tracker_port_entry.get())))
            send_msg(self.tracker_socket, f"{self.hostname_entry.get()} {self.peer_ip}:{self.listen_port}")
            new_log = f"Connected to {self.tracker_ip_entry.get(), self.tracker_port_entry.get()}"
            self.isConnected = True
        except:
            new_log = f"Cannot connect to {self.tracker_ip_entry.get(), self.tracker_port_entry.get()}"
        finally:
            self.write_log(new_log)

    def write_log(self, str_log):
        self.consoleTextbox.insert(ctk.END, str_log + "\n")

    def browse_file(self):
        filepath = filedialog.askopenfilename()
        if not filepath:
            return
        self.dirEntry.delete(0, ctk.END)
        self.dirEntry.insert(0, filepath)

        filename = filepath.split('/').pop()
        self.newNameEntry.delete(0, ctk.END)
        self.newNameEntry.insert(0, filename)

        self.write_log(f"Browse: {filepath}")

    def handle_publish_button(self):
        if not self.isConnected:
            self.write_log("Publish: Connect to tracker first!")
            return
        local_directory = self.dirEntry.get()
        newname = self.newNameEntry.get()
        if not local_directory:
            self.write_log("Publish: No chosen file!")
            return
        elif not newname:
            self.write_log("Publish: Cannot get file name!")
            return
        self.publish_file(newname, local_directory)

    def publish_file(self, filename, local_directory):
        send_msg(self.tracker_socket, f"publish*{filename}*{self.peer_ip}:{self.listen_port}")
        try:
            res = recv_msg(self.tracker_socket)
            self.write_log("RECEIVE:" + res)
        except:
            self.write_log(f"Publish: No ack from tracker!")
            return

        if res == "publish ok":
            self.write_log(f"Publish: Successful! Filename: {filename}")
            try:
                file = open(self.repository, "a")
                file.write(f"{filename}*{local_directory}\n")
                file.close()
            except:
                self.write_log(f"Publish: Cannot open file!")
        elif res == "publish duplicated filename":
            self.write_log(f"Publish: Duplicated filename in tracker's file list. Please change other filename!!")
        else:
            self.write_log(f"Publish: Tracker haven't received message!")

    def handle_fetch_button(self):
        if not self.isConnected:
            self.write_log("Fetch: Connect to tracker first!")
            return
        filename = self.text_combobox.get()
        self.fetch_file(filename)

    def get_peer_hold_file(self, filename):
        send_msg(self.tracker_socket, f"fetch*{filename}")
        res = ""
        try:
            res = recv_msg(self.tracker_socket)
        except:
            self.write_log(f"Fetch: Cannot get IP, Port of neighbor peers")
        return res

    def fetch_file(self, filename):
        addr = self.get_peer_hold_file(filename)
        if addr == "<NOT FOUND>":
            self.write_log("Fetch: File is not found!")
            return
        ip, port = addr.split(":")
        port = int(port)

        neighbor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        save_folder = filedialog.askdirectory()
        if not save_folder:
            self.write_log("Fetch: Please choose folder to save file")
            return

        save_file_dir = save_folder + "/" + filename
        self.write_log(f"Set directory: {save_file_dir}")

        try:
            neighbor_socket.connect((ip, port))
            self.write_log(f"Connection: Connected to {ip}:{port}")
        except:
            self.write_log(f"Fetch: Cannot connect to {addr})")
            return

        send_msg(neighbor_socket, f"fetch {filename}")

        try:
            recv_file(neighbor_socket, save_file_dir)
            self.write_log(f"Fetch: Successful! Filename: {filename}")
        except:
            self.write_log(f"Fetch: Cannot receive full file from {addr}")
            return

        self.publish_file(filename, save_file_dir)

    def handle_refresh_button(self):
        if not self.isConnected:
            self.write_log("Fetch: Connect to tracker first!")
            return
        self.file_list.clear()
        self.get_list()

    def get_list(self):
        send_msg(self.tracker_socket, "get list")
        try:
            while True:
                filename = recv_msg(self.tracker_socket)
                if filename[-5:] == "<END>":
                    break
                self.file_list.append(filename)
            self.write_log("Get list: Successful!")
        except:
            self.write_log("Get list: Not fully success!")

        self.files_combobox.configure(values=self.file_list)


def send_msg(conn, msg):
    msg = msg.encode(FORMAT)
    msg_len = len(msg)
    msg += b' ' * (MESSAGE_LEN - msg_len)
    conn.send(msg)


def recv_msg(conn):
    return conn.recv(MESSAGE_LEN).decode(FORMAT).strip()


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


MyGUI()
