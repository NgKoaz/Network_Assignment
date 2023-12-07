import customtkinter as ctk

class MyApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Tạo màn hình đăng nhập
        self.login_screen = ctk.CTkFrame(self)
        self.login_screen.pack(fill="both", expand=True)

        # Tạo các widget cho màn hình đăng nhập
        self.username_label = ctk.CTkLabel(self.login_screen, text="Tên người dùng")
        self.username_entry = ctk.CTkEntry(self.login_screen)
        self.password_label = ctk.CTkLabel(self.login_screen, text="Mật khẩu")
        self.password_entry = ctk.CTkEntry(self.login_screen, show="*")
        self.login_button = ctk.CTkButton(self.login_screen, text="Đăng nhập")

        # Thiết lập bố cục cho màn hình đăng nhập
        self.username_label.pack(side="left")
        self.username_entry.pack(side="left", fill="x", expand=True)
        self.password_label.pack(side="left")
        self.password_entry.pack(side="left", fill="x", expand=True)
        self.login_button.pack(side="left", fill="x", expand=True)

        # Xử lý sự kiện khi người dùng nhấp vào nút "Đăng nhập"
        self.login_button.configure(command=self.on_login_click)

    def on_login_click(self):
        # Lấy tên người dùng và mật khẩu từ người dùng
        username = self.username_entry.get()
        password = self.password_entry.get()

        # Kiểm tra xem tên người dùng và mật khẩu có hợp lệ hay không
        if username == "admin" and password == "123456":
            # Nếu hợp lệ, thì render ra màn hình mới
            self.render_home_screen()
        else:
            # Nếu không hợp lệ, thì hiển thị thông báo lỗi
            ctk.CTkLabel(self, text="Tên người dùng hoặc mật khẩu không hợp lệ").pack()

    def render_home_screen(self):
        # Xóa màn hình đăng nhập
        self.login_screen.pack_forget()

        # Tạo màn hình chính
        self.home_screen = ctk.CTkFrame(self)
        self.home_screen.pack(fill="both", expand=True)

        # Tạo các widget cho màn hình chính
        self.welcome_label = ctk.CTkLabel(self.home_screen, text="Chào mừng bạn đến với ứng dụng của chúng tôi!")

        # Thiết lập bố cục cho màn hình chính
        self.welcome_label.pack(fill="both", expand=True)

if __name__ == "__main__":
    app = MyApp()
    app.mainloop()