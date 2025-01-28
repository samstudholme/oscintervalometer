import time
import threading
import json
import os
import sys
import socket
from datetime import datetime
from tkinter import Tk, Label, Entry, Button, Canvas, OptionMenu, StringVar, filedialog, Toplevel, Text, Scrollbar, VERTICAL, RIGHT, Y, END, BOTH, messagebox
from pythonosc import udp_client, dispatcher, osc_server
import platform

# Global variable to control the sending thread
stop_event = threading.Event()
osc_server_instance = None

# Predefined OSC commands
osc_commands = {
    "QLab - Go": "/cue/1/start",
    "QLab - Stop": "/cue/1/stop",
    "ETC EOS - Go": "/eos/key/go_0",
    "ETC EOS - Stop": "/eos/key/stop_0",
    "ETC EOS - Back": "/eos/key/back_0",
    "ETC EOS - Fire": "/eos/cue/1/1/fire",
    "Cuepoints - Play": "/CuePoints,s,Play",
    "Cuepoints - Pause": "/CuePoints,s,Pause",
    "Custom": ""
}

# OSC sender commands
osc_sender_commands = {
    "Start Sending": "/oscint/start",
    "Stop Sending": "/oscint/stop",
    "Test OSC": "/oscint/test"
}

# Path to settings file
settings_dir = os.path.join(os.path.expanduser("~"), "Documents", "OSC Intervalometer")
settings_file = os.path.join(settings_dir, "settings.json")

# Function to update the address entry based on the selected command
def update_address_entry(*args):
    selected_command = command_var.get()
    address_entry.delete(0, "end")
    address_entry.insert(0, osc_commands[selected_command])

# Function to send OSC message
def send_osc_message(ip, port, address, interval_seconds):
    client = udp_client.SimpleUDPClient(ip, port)
    while not stop_event.is_set():
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] Sent OSC message to {address} (IP: {ip}, Port: {port})")
        client.send_message(address, "")
        update_status_icon("green")
        time.sleep(interval_seconds)
    update_status_icon("red")

# Function to start sending OSC messages
def start_sending():
    print("start_sending called")  # Debug print statement
    global stop_event
    stop_event.clear()
    ip = ip_entry.get()
    port = port_entry.get()
    address = address_entry.get()
    interval_minutes = interval_minutes_entry.get()
    interval_seconds = interval_seconds_entry.get()

    if not ip or not port or not address or not interval_minutes or not interval_seconds:
        messagebox.showerror("Error", "All fields must be filled out")
        return

    port = int(port)
    interval_minutes = int(interval_minutes)
    interval_seconds = int(interval_seconds)
    total_interval_seconds = interval_minutes * 60 + interval_seconds

    # Start a new thread to send OSC messages
    threading.Thread(target=send_osc_message, args=(ip, port, address, total_interval_seconds), daemon=True).start()

# Function to stop sending OSC messages
def stop_sending():
    stop_event.set()
    update_status_icon("red")

# Function to test sending a single OSC message
def test_osc_message():
    ip = ip_entry.get()
    port = port_entry.get()
    address = address_entry.get()

    if not ip or not port or not address:
        messagebox.showerror("Error", "IP, Port, and Address fields must be filled out")
        return

    port = int(port)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] Test OSC message sent to {address} (IP: {ip}, Port: {port})")
    client = udp_client.SimpleUDPClient(ip, port)
    client.send_message(address, "")

# Function to update the status icon color
def update_status_icon(color):
    canvas.itemconfig(status_icon, fill=color)

# Function to update the OSC server status icon color
def update_osc_status_icon(color):
    canvas.itemconfig(osc_status_icon, fill=color)

# Function to save settings to a JSON file
def save_settings():
    settings = {
        "ip": ip_entry.get(),
        "port": port_entry.get(),
        "command": command_var.get(),
        "address": address_entry.get(),
        "interval_minutes": interval_minutes_entry.get(),
        "interval_seconds": interval_seconds_entry.get(),
        "osc_interface": interface_var.get()
    }
    os.makedirs(settings_dir, exist_ok=True)
    with open(settings_file, "w") as f:
        json.dump(settings, f)

# Function to load settings from a JSON file
def load_settings():
    os.makedirs(settings_dir, exist_ok=True)  # Ensure the folder is created
    if os.path.exists(settings_file):
        with open(settings_file, "r") as f:
            settings = json.load(f)
            required_keys = ["ip", "port", "command", "address", "interval_minutes", "interval_seconds", "osc_interface"]
            if all(key in settings for key in required_keys):
                ip_entry.delete(0, "end")
                ip_entry.insert(0, settings.get("ip", ""))
                port_entry.delete(0, "end")
                port_entry.insert(0, settings.get("port", ""))
                command_var.set(settings.get("command", "Custom"))
                address_entry.delete(0, "end")
                address_entry.insert(0, settings.get("address", ""))
                interval_minutes_entry.delete(0, "end")
                interval_minutes_entry.insert(0, settings.get("interval_minutes", ""))
                interval_seconds_entry.delete(0, "end")
                interval_seconds_entry.insert(0, settings.get("interval_seconds", ""))
                interface_var.set(settings.get("osc_interface", interfaces[0]))
            else:
                save_settings()  # Save default settings if any key is missing

# Function to save settings to a text file
def save_settings_as_txt():
    settings = {
        "ip": ip_entry.get(),
        "port": port_entry.get(),
        "command": command_var.get(),
        "address": address_entry.get(),
        "interval_minutes": interval_minutes_entry.get(),
        "interval_seconds": interval_seconds_entry.get(),
        "osc_interface": interface_var.get()
    }
    file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
    if file_path:
        with open(file_path, "w") as f:
            json.dump(settings, f)

# Function to open settings from a text file
def open_settings_from_txt():
    file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    if file_path:
        with open(file_path, "r") as f:
            settings = json.load(f)
            required_keys = ["ip", "port", "command", "address", "interval_minutes", "interval_seconds", "osc_interface"]
            if all(key in settings for key in required_keys):
                ip_entry.delete(0, "end")
                ip_entry.insert(0, settings.get("ip", ""))
                port_entry.delete(0, "end")
                port_entry.insert(0, settings.get("port", ""))
                command_var.set(settings.get("command", "Custom"))
                address_entry.delete(0, "end")
                address_entry.insert(0, settings.get("address", ""))
                interval_minutes_entry.delete(0, "end")
                interval_minutes_entry.insert(0, settings.get("interval_minutes", ""))
                interval_seconds_entry.delete(0, "end")
                interval_seconds_entry.insert(0, settings.get("interval_seconds", ""))
                interface_var.set(settings.get("osc_interface", interfaces[0]))
            else:
                save_settings()  # Save default settings if any key is missing

# Function to open a debug window
def open_debug_window():
    debug_window = Toplevel(root)
    debug_window.title("Debug Window")
    debug_window.geometry("600x400")

    debug_text = Text(debug_window, wrap="word", spacing1=1, spacing3=1)
    debug_text.pack(expand=True, fill="both")

    scrollbar = Scrollbar(debug_text, orient=VERTICAL, command=debug_text.yview)
    scrollbar.pack(side=RIGHT, fill=Y)
    debug_text.config(yscrollcommand=scrollbar.set)

    def write_to_debug(message):
        debug_text.insert(END, message + "\n")
        debug_text.see(END)

    # Redirect print statements to the debug window
    class PrintRedirector:
        def __init__(self, func):
            self.func = func

        def write(self, message):
            self.func(message)

        def flush(self):
            pass

    sys.stdout = PrintRedirector(write_to_debug)
    sys.stderr = PrintRedirector(write_to_debug)

# Function to start the OSC server
def start_osc_server():
    global osc_server_instance
    if osc_server_instance:
        osc_server_instance.shutdown()
    selected_interface = interface_var.get()
    print(f"Starting OSC server on interface: {selected_interface}")
    dispatcher_instance = dispatcher.Dispatcher()
    dispatcher_instance.map("/oscint/start", lambda addr, *args: (print(f"OSC command received: /oscint/start"), start_sending()))
    dispatcher_instance.map("/oscint/stop", lambda addr, *args: (print(f"OSC command received: /oscint/stop"), stop_sending()))
    dispatcher_instance.map("/oscint/test", lambda addr, *args: (print(f"OSC command received: /oscint/test"), test_osc_message()))
    osc_server_instance = osc_server.ThreadingOSCUDPServer((selected_interface, 3001), dispatcher_instance)
    threading.Thread(target=osc_server_instance.serve_forever, daemon=True).start()
    print(f"OSC server started on {selected_interface}:3001")
    update_osc_status_icon("green")

# Function to open OSC settings window
def open_osc_settings_window():
    osc_window = Toplevel(root)
    osc_window.title("OSC Settings")
    osc_window.geometry("400x300")

    Label(osc_window, text="OSC Settings", font=("Helvetica", 14)).pack(pady=10)

    Label(osc_window, text="Network Interface:").pack(pady=5)
    interfaces = [i[4][0] for i in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)]
    interface_var.set(interfaces[0])
    interface_menu = OptionMenu(osc_window, interface_var, *interfaces)
    interface_menu.pack(pady=5)

    ip_label = Label(osc_window, text=f"Current IP: {interfaces[0]}")
    ip_label.pack(pady=5)

    def update_ip_label(*args):
        ip_label.config(text=f"Current IP: {interface_var.get()}")
        start_osc_server()

    interface_var.trace("w", update_ip_label)

    Label(osc_window, text="OSC Port: 3001").pack(pady=5)

    Label(osc_window, text="Available OSC Commands:").pack(pady=5)
    commands_text = Text(osc_window, height=10, wrap="word")
    commands_text.pack(expand=True, fill="both", padx=10, pady=5)
    commands_text.insert(END, "\n".join([f"{key}: {value}" for key, value in osc_sender_commands.items()]))
    commands_text.config(state="disabled")

    Button(osc_window, text="Start OSC Server", command=start_osc_server).pack(pady=10)

# Function to detect system theme
def detect_system_theme():
    if platform.system() == "Windows":
        import winreg
        try:
            registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
            key = winreg.OpenKey(registry, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return "light" if value == 1 else "dark"
        except Exception as e:
            print(f"Error detecting Windows theme: {e}")
            return "light"
    elif platform.system() == "Darwin":
        try:
            from subprocess import Popen, PIPE
            p = Popen(["defaults", "read", "-g", "AppleInterfaceStyle"], stdout=PIPE, stderr=PIPE)
            output, _ = p.communicate()
            return "dark" if b"Dark" in output else "light"
        except Exception as e:
            print(f"Error detecting macOS theme: {e}")
            return "light"
    else:
        return "light"

# Function to apply theme
def apply_theme(theme):
    if theme == "dark":
        root.tk_setPalette(background="#2e2e2e", foreground="#ffffff", activeBackground="#4e4e4e", activeForeground="#ffffff")
        for widget in root.winfo_children():
            widget.configure(bg="#2e2e2e", fg="#ffffff")
    else:
        root.tk_setPalette(background="#ffffff", foreground="#000000", activeBackground="#e0e0e0", activeForeground="#000000")
        for widget in root.winfo_children():
            widget.configure(bg="#ffffff", fg="#000000")

# Create the GUI
root = Tk()
root.title("OSC Intervalometer V1.0")  # Updated window title

# Detect and apply system theme
system_theme = detect_system_theme()
apply_theme(system_theme)

Label(root, text="OSC Intervalometer", font=("Helvetica", 16)).grid(row=0, columnspan=2, padx=10, pady=10)  # Added title label

Label(root, text="OSC Server Status:").grid(row=1, column=0, padx=10, pady=5)  # Moved OSC Server Status label
osc_status_canvas = Canvas(root, width=20, height=20)
osc_status_canvas.grid(row=2, column=1, pady=5)
osc_status_icon = osc_status_canvas.create_oval(5, 5, 15, 15, fill="red")

Label(root, text="Intervalometer Status:").grid(row=2, column=0, padx=10, pady=5)  # Moved Active Status label
canvas = Canvas(root, width=20, height=20)
canvas.grid(row=1, column=1, pady=5)
status_icon = canvas.create_oval(5, 5, 15, 15, fill="red")

start_button = Button(root, text="Start Sending", command=start_sending)
start_button.grid(row=3, column=0, padx=10, pady=10)

stop_button = Button(root, text="Stop Sending", command=stop_sending)
stop_button.grid(row=3, column=1, padx=10, pady=10)

Label(root, text="Target IP:").grid(row=4, column=0, padx=10, pady=5)
ip_entry = Entry(root)
ip_entry.grid(row=4, column=1, padx=10, pady=5)

Label(root, text="Port:").grid(row=5, column=0, padx=10, pady=5)
port_entry = Entry(root)
port_entry.grid(row=5, column=1, padx=10, pady=5)

Label(root, text="Command:").grid(row=6, column=0, padx=10, pady=5)
command_var = StringVar(root)
command_var.set("Custom")
command_var.trace("w", update_address_entry)
command_menu = OptionMenu(root, command_var, *osc_commands.keys())
command_menu.grid(row=6, column=1, padx=10, pady=5)

Label(root, text="OSC Message:").grid(row=7, column=0, padx=10, pady=5)
address_entry = Entry(root)
address_entry.grid(row=7, column=1, padx=10, pady=5)

Label(root, text="Interval (minutes):").grid(row=8, column=0, padx=10, pady=5)
interval_minutes_entry = Entry(root)
interval_minutes_entry.grid(row=8, column=1, padx=10, pady=5)

Label(root, text="Interval (seconds):").grid(row=9, column=0, padx=10, pady=5)
interval_seconds_entry = Entry(root)
interval_seconds_entry.grid(row=9, column=1, padx=10, pady=5)

test_button = Button(root, text="Test OSC", command=test_osc_message)
test_button.grid(row=10, column=0, padx=10, pady=10)

save_button = Button(root, text="Save Setup File", command=save_settings_as_txt)
save_button.grid(row=11, column=0, padx=10, pady=10)

open_button = Button(root, text="Open Setup File", command=open_settings_from_txt)
open_button.grid(row=11, column=1, padx=10, pady=10)

debug_button = Button(root, text="Open Debug Window", command=open_debug_window)
debug_button.grid(row=12, column=0, padx=10, pady=10)  # Added debug button

osc_button = Button(root, text="OSC Settings", command=open_osc_settings_window)
osc_button.grid(row=12, column=1, padx=10, pady=10)  # Added OSC settings button

# Load settings when the application starts
interfaces = [i[4][0] for i in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)]
interface_var = StringVar(root)
load_settings()

# Start OSC server on startup
start_osc_server()

# Save settings when the application closes
root.protocol("WM_DELETE_WINDOW", lambda: (save_settings(), root.destroy()))

root.mainloop()