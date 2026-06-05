import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

# ---------------- MAIN WINDOW ----------------
window = tk.Tk()
window.title("University Course Registration System")
window.geometry("450x500")
window.configure(bg="#0b3d91")  # university blue

# ---------------- LOGIN FRAME ----------------
frame = tk.Frame(window, bg="white", padx=25, pady=25)
frame.place(relx=0.5, rely=0.5, anchor="center")

# ---------------- LOGO ----------------
try:
    img = Image.open("upm.png")
    img = img.resize((80, 80))
    logo = ImageTk.PhotoImage(img)

    tk.Label(frame, image=logo, bg="white").pack(pady=10)
except:
    tk.Label(frame, text="UNIVERSITY LOGO", bg="white").pack(pady=10)

# ---------------- TITLE ----------------
tk.Label(
    frame,
    text="COURSE REGISTRATION SYSTEM",
    font=("Arial", 12, "bold"),
    bg="white",
    fg="#0b3d91"
).pack(pady=5)

tk.Label(
    frame,
    text="Student Login",
    font=("Arial", 10),
    bg="white",
    fg="gray"
).pack(pady=5)

# ---------------- INPUT FIELDS ----------------
tk.Label(frame, text="Username", bg="white").pack(anchor="w")
username_entry = tk.Entry(frame, width=30)
username_entry.pack(pady=5)

tk.Label(frame, text="Password", bg="white").pack(anchor="w")
password_entry = tk.Entry(frame, show="*", width=30)
password_entry.pack(pady=5)

# ---------------- DASHBOARD ----------------
def open_dashboard():
    dashboard = tk.Toplevel()
    dashboard.title("Student Dashboard")
    dashboard.geometry("500x400")
    dashboard.configure(bg="#f2f2f2")

    frame2 = tk.Frame(dashboard, bg="white", padx=20, pady=20)
    frame2.place(relx=0.5, rely=0.5, anchor="center")

    tk.Label(
        frame2,
        text="AVAILABLE COURSES",
        font=("Arial", 14, "bold"),
        bg="white"
    ).pack(pady=10)

    # FAKE COURSE DATA
    courses = [
        "CND4400 - Distributed Systems",
        "CSC3050 - Database Systems",
        "CSC3100 - Artificial Intelligence",
        "CSC3020 - Networking"
    ]

    listbox = tk.Listbox(frame2, width=40, height=6)
    listbox.pack(pady=10)

    for c in courses:
        listbox.insert(tk.END, c)

    # REGISTER
    def register():
        selected = listbox.get(tk.ACTIVE)
        if selected:
            messagebox.showinfo("Success", f"Registered: {selected}")
        else:
            messagebox.showerror("Error", "Please select a course")

    # DROP
    def drop():
        selected = listbox.get(tk.ACTIVE)
        if selected:
            messagebox.showinfo("Success", f"Dropped: {selected}")
        else:
            messagebox.showerror("Error", "Please select a course")

    tk.Button(frame2, text="Register Course", bg="#4CAF50", fg="white", command=register).pack(pady=5)
    tk.Button(frame2, text="Drop Course", bg="#f44336", fg="white", command=drop).pack(pady=5)

# ---------------- LOGIN FUNCTION ----------------
def login():
    username = username_entry.get()
    password = password_entry.get()

    if username == "" or password == "":
        messagebox.showerror("Error", "Please fill all fields")

    elif username == "student" and password == "1234":
        messagebox.showinfo("Success", "Login Successful")
        open_dashboard()

    else:
        messagebox.showerror("Error", "Invalid Username or Password")

# ---------------- LOGIN BUTTON ----------------
tk.Button(
    frame,
    text="LOGIN",
    bg="#0b3d91",
    fg="white",
    width=20,
    command=login
).pack(pady=15)

window.mainloop()