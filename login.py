import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import xmlrpc.client  # <-- NAZIRA'S INTEGRATION: Import RPC library

# ---------------- RPC CLIENT SETUP ----------------
# Connects to Ghaida's server. 
# Change "localhost" to her local IP address if running on different laptops.
SERVER_URL = "http://localhost:8000/"
try:
    rpc_server = xmlrpc.client.ServerProxy(SERVER_URL)
except Exception as e:
    print(f"RPC initialization error: {e}")

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
def open_dashboard(student_id):
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

    listbox = tk.Listbox(frame2, width=40, height=6)
    listbox.pack(pady=10)

    # --- NAZIRA'S INTEGRATION: Fetch courses dynamically from Ghaida's RPC server ---
    try:
        courses = rpc_server.ViewCourse()
        for c in courses:
            listbox.insert(tk.END, c)
    except Exception as e:
        messagebox.showerror("RPC Error", "Could not load course list from server.")
        # Fallback to local fake data if server isn't running yet during test
        courses = ["CND4400 - Distributed Systems", "CSC3050 - Database Systems"]
        for c in courses:
            listbox.insert(tk.END, c)

    # --- NAZIRA'S INTEGRATION: RPC Register Function ---
    def register():
        selected = listbox.get(tk.ACTIVE)
        if selected:
            try:
                # Triggers RPC to register and updates MongoDB
                status = rpc_server.RegisterCourse(selected, student_id)
                messagebox.showinfo("RPC Server Response", status)
            except Exception as e:
                messagebox.showerror("RPC Network Error", f"Failed to send register command: {e}")
        else:
            messagebox.showerror("Error", "Please select a course")

    # --- NAZIRA'S INTEGRATION: RPC Drop Function ---
    def drop():
        selected = listbox.get(tk.ACTIVE)
        if selected:
            try:
                # Triggers RPC to drop and updates MongoDB
                status = rpc_server.DropCourse(selected, student_id)
                messagebox.showinfo("RPC Server Response", status)
            except Exception as e:
                messagebox.showerror("RPC Network Error", f"Failed to send drop command: {e}")
        else:
            messagebox.showerror("Error", "Please select a course")

    tk.Button(frame2, text="Register Course", bg="#4CAF50", fg="white", command=register).pack(pady=5)
    tk.Button(frame2, text="Drop Course", bg="#f44336", fg="white", command=drop).pack(pady=5)

# ---------------- LOGIN FUNCTION ----------------
def login():
    username = username_entry.get().strip()
    password = password_entry.get().strip()

    if username == "" or password == "":
        messagebox.showerror("Error", "Please fill all fields")
        return

    # --- NAZIRA'S INTEGRATION: Verify password with Ghaida's server over RPC ---
    try:
        is_authenticated = rpc_server.verify_login(username, password)
        
        if is_authenticated:
            messagebox.showinfo("Success", "Login Successful via RPC")
            window.withdraw() # Hide the login window
            open_dashboard(username) # Launch dashboard and pass student ID
        else:
            messagebox.showerror("Error", "Invalid Username or Password")
            
    except Exception as e:
        messagebox.showerror("RPC Connection Error", f"Cannot connect to Server.\nEnsure Ghaida's script is running!\nDetails: {e}")

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