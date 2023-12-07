import tkinter as tk

root = tk.Tk()
root.geometry("400x400")
root.title("My first")

label = tk.Label(root, text="Hello World!", font=("Arial", 16))
label.pack(padx=20, pady=20)

textBox = tk.Text(root, height=3, font=("Arial", 16))
textBox.pack(padx=10)

buttonFrame = tk.Frame(root)
buttonFrame.columnconfigure(0, weight=1)
buttonFrame.columnconfigure(1, weight=1)
buttonFrame.columnconfigure(2, weight=1)


btn1 = tk.Button(buttonFrame, text="1", font=('Arial', 16))
btn1.grid(row=0, column=0, sticky=tk.W+tk.E)
btn1 = tk.Button(buttonFrame, text="2", font=('Arial', 16))
btn1.grid(row=0, column=1, sticky=tk.W+tk.E)
btn1 = tk.Button(buttonFrame, text="3", font=('Arial', 16))
btn1.grid(row=0, column=2, sticky=tk.W+tk.E)

buttonFrame.pack(fill="x")

anotherbtn = tk.Button(root, text="TEST")
anotherbtn.place(x=200, y=200, height=100, width=100)

root.mainloop()
