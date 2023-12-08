import socket
import customtkinter as ctk
from customtkinter import filedialog
import threading
import json
import re

MESSAGE_LEN = 512
CHUNK_LEN = 1024
FORMAT = 'utf-8'

# These value can be modified.
TRACKER_IP = socket.gethostbyname(socket.gethostname())
TRACKER_PORT = 5051
TRACKER_ADDR = (TRACKER_IP, TRACKER_PORT)

ctk.set_appearance_mode("Light")

class MyGUI:
    def __init__(self):
        # GUI: Create root
        self.root = ctk.CTk()
        self.root.geometry("500x500+500+250")
        self.root.title("File Sharing")

        # Core: Create socket to listen connection from other peer.
        self.peer_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.peer_ip = socket.gethostbyname(socket.gethostname())
        self.listen_port = 9091
        self.isListened = False

        # self.tracker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.tracker_socket.connect(TRACKER_ADDR)
        # self.isConnected = True

        # GUI: Login screen
        self.login_frame = ctk.CTkFrame(master=self.root)
        self.login_frame.pack()

        self.username_label = ctk.CTkLabel(master=self.login_frame, text="Username")
        self.username_label.pack()
        self.username_entry = ctk.CTkEntry(master=self.login_frame, placeholder_text="your username")
        self.username_entry.pack()

        self.password_label = ctk.CTkLabel(master=self.login_frame, text="Password")
        self.password_label.pack()
        self.password_entry = ctk.CTkEntry(master=self.login_frame, placeholder_text="your password")
        self.password_entry.pack()

        self.login_button = ctk.CTkButton(master=self.login_frame, text="Login", command=self.login)
        self.login_button.pack()

        # GUI: Main screen
        self.main_frame = ctk.CTkFrame(master=self.root)
        # self.main_frame.pack()

        self.label_main_frame = ctk.CTkLabel(master=self.main_frame, text="This is a main frame!")
        self.label_main_frame.pack()

        # Core:

        self.root.protocol("WM_DELETE_WINDOW", self.closing_window)
        self.root.mainloop()

    def closing_window(self):
        self.root.destroy()

    def listening(self):
        self.peer_server.listen()
        while True:
            conn, addr = self.peer_server.accept()
            thread = threading.Thread(target=self.handle_request, args=(conn, addr))
            thread.start()

    def handle_request(self):
        pass

    def check_connection(self):
        return True

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not self.check_connection():
            print("Disconnect!")


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


# Run
MyGUI()









