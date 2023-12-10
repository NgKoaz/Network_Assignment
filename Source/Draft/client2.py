import tkinter as tk

def resize_frame():
    new_width = int(entry_width.get())
    new_height = int(entry_height.get())
    frame.config(width=new_width, height=new_height)

# Tạo cửa sổ
root = tk.Tk()
root.title("Thay đổi kích thước frame")

# Tạo frame
frame = tk.Frame(root, width=100, height=100)
frame.pack(padx=10, pady=10)

# Tạo entry và button để nhập và thay đổi kích thước
label_width = tk.Label(root, text="Width:")
label_width.pack()
entry_width = tk.Entry(root)
entry_width.pack()

label_height = tk.Label(root, text="Height:")
label_height.pack()
entry_height = tk.Entry(root)
entry_height.pack()

resize_button = tk.Button(root, text="Thay đổi kích thước", command=resize_frame)
resize_button.pack()

# Main loop
root.mainloop()