import tkinter as tk
from tkinter import messagebox

def check_login(username, password):
    # Đây là nơi bạn sẽ kiểm tra thông tin đăng nhập, ở đây mình để làm ví dụ
    if username == "admin" and password == "password":
        return True
    else:
        return False

def login():
    entered_username = username_entry.get()
    entered_password = password_entry.get()

    if check_login(entered_username, entered_password):
        messagebox.showinfo("Đăng nhập thành công", "Chào mừng bạn đến trang chủ!")
        open_home_window(entered_username)
        root.destroy()  # Đóng cửa sổ đăng nhập sau khi chuyển đến trang chủ
    else:
        messagebox.showerror("Lỗi đăng nhập", "Thông tin đăng nhập không đúng")

def open_home_window(username):
    home_window = tk.Tk()
    home_window.title("Trang chủ")

    # Thêm các thành phần bạn muốn vào trang chủ ở đây
    welcome_label = tk.Label(home_window, text=f"Chào mừng {username} đến trang chủ!")
    welcome_label.pack()

    # Thêm các thành phần khác tùy ý

    home_window.mainloop()

# Tạo cửa sổ đăng nhập
root = tk.Tk()
root.title("Đăng nhập")

# Tạo các label và entry cho username và password
tk.Label(root, text="Tên đăng nhập:").pack()
username_entry = tk.Entry(root)
username_entry.pack()

tk.Label(root, text="Mật khẩu:").pack()
password_entry = tk.Entry(root, show="*")
password_entry.pack()

# Tạo nút đăng nhập
login_button = tk.Button(root, text="Đăng nhập", command=login)
login_button.pack()

root.mainloop()
