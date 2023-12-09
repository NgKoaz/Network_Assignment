import socket
import time

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
from customtkinter import filedialog
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

ctk.set_appearance_mode("Light")


class MyGUI:
    def __init__(self):
        # GUI: Create root
        self.root = tk.Tk()
        self.root.geometry("500x500+500+250")
        self.root.title("File Sharing")
        self.root.tk.call('source', './Forest-ttk-theme/forest-dark.tcl')
        ttk.Style().theme_use('forest-dark')

        # Core: Create socket to listen connection from other peer.
        self.peer_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.peer_ip = socket.gethostbyname(socket.gethostname())
        self.listen_port = 9091
        self.isListened = False
        self.token = ""
        self.workspace_path = os.getenv("FOLDER_PATH")

        self.tracker_socket = None

        # GUI: Login screen
        self.login_frame = ttk.Frame(master=self.root)
        self.login_frame.pack()

        self.username_label = ttk.Label(master=self.login_frame, text="Username")
        self.username_label.pack()
        self.username_entry = ttk.Entry(master=self.login_frame)
        self.username_entry.pack()

        self.password_label = ttk.Label(master=self.login_frame, text="Password")
        self.password_label.pack()
        self.password_entry = ttk.Entry(master=self.login_frame)
        self.password_entry.pack()

        self.login_button = ttk.Button(master=self.login_frame, text="Login", command=self.handle_login)
        self.login_button.pack()

        # Add status label here

        # GUI: Main screen
        self.main_frame = ttk.Frame(master=self.root)
        # self.main_frame.pack()
        #   self.listbox = CTkListbox()

        self.label_main_frame = ttk.Label(master=self.main_frame, text="This is a main frame!")
        self.label_main_frame.pack()


        # Core:

        self.root.protocol("WM_DELETE_WINDOW", self.closing_window)
        self.root.mainloop()

    def create_folder_if_not_exists(self):
        if not os.path.exists(self.workspace_path):
            os.makedirs(self.workspace_path)

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
            self.enter_to_main_frame()
        else:
            print("Wrong password or username!")

    def declare_address(self):
        if not self.connect_to_tracker():
            print("Failed to connect to tracker!")

        # Send `address` to come into handle_address_declaration process.
        send_msg(self.tracker_socket, "address")
        # Check ACK from tracker
        if not recv_msg(self.tracker_socket) == "address":
            print("[ERROR] Wrong process!")

        # Send token for authorization
        send_msg(self.tracker_socket, f"token:{self.token}")
        res = recv_msg(self.tracker_socket)
        if res == "auth success":
            # Continue process
            pass
        elif res == "auth fail":
            print("Authorize fail")
            return
        else:
            print("Wrong process!")
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

    def enter_to_main_frame(self):
        self.login_frame.pack_forget()
        self.main_frame.pack()
        thread = threading.Thread(target=self.listening)
        thread.start()

    def handle_request(self):
        pass

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


def check_str_before_send(_str):
    pattern = re.compile(r"[:|\'\"]")
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









