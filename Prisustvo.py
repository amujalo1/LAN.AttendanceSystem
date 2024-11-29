import network
import machine
import time
import socket
import ure
import json
import os

button_start_pin = machine.Pin(0, machine.Pin.IN, machine.Pin.PULL_DOWN)
button_stop_pin = machine.Pin(1, machine.Pin.IN, machine.Pin.PULL_DOWN)
timer = machine.Timer()

red_led_pin = machine.Pin(14, machine.Pin.OUT)
green_led_pin = machine.Pin(12, machine.Pin.OUT)
blue_led_pin = machine.Pin(13, machine.Pin.OUT)

ssid = 'PRISUSTVO'
password = '123456789'

connected_clients = set()
stop_time = False
start_time = None
elapsed_time = 0
timer_running = False

users = {
    "20230001": {"ime": "Marko", "prezime": "Marković", "lozinka": "pass123", "index": "20230001", "ip_adresa": None, "prisustvo": False, "vrijeme_osluskivanja": None, "ukupno_vrijeme_osluskivanja": None},
    "20230002": {"ime": "Ana", "prezime": "Anić", "lozinka": "pass456", "index": "20230002", "ip_adresa": None, "prisustvo": False, "vrijeme_osluskivanja": None, "ukupno_vrijeme_osluskivanja": None},
    "20230003": {"ime": "Ivan", "prezime": "Ivanović", "lozinka": "pass789", "index": "20230003", "ip_adresa": None, "prisustvo": False, "vrijeme_osluskivanja": None, "ukupno_vrijeme_osluskivanja": None},
    "20230004": {"ime": "Petar", "prezime": "Petrović", "lozinka": "pass101112", "index": "20230004", "ip_adresa": None, "prisustvo": False, "vrijeme_osluskivanja": None, "ukupno_vrijeme_osluskivanja": None},
    "20230005": {"ime": "Jelena", "prezime": "Jelenić", "lozinka": "pass131415", "index": "20230005", "ip_adresa": None, "prisustvo": False, "vrijeme_osluskivanja": None, "ukupno_vrijeme_osluskivanja": None},
    "20230006": {"ime": "Milan", "prezime": "Milanović", "lozinka": "pass161718", "index": "20230006", "ip_adresa": None, "prisustvo": False, "vrijeme_osluskivanja": None, "ukupno_vrijeme_osluskivanja": None},
    "20230007": {"ime": "Nikola", "prezime": "Nikolić", "lozinka": "pass192021", "index": "20230007", "ip_adresa": None, "prisustvo": False, "vrijeme_osluskivanja": None, "ukupno_vrijeme_osluskivanja": None},
    "20230008": {"ime": "Lana", "prezime": "Lanić", "lozinka": "pass222324", "index": "20230008", "ip_adresa": None, "prisustvo": False, "vrijeme_osluskivanja": None, "ukupno_vrijeme_osluskivanja": None},
    "20230009": {"ime": "Sara", "prezime": "Sarić", "lozinka": "pass252627", "index": "20230009", "ip_adresa": None, "prisustvo": False, "vrijeme_osluskivanja": None, "ukupno_vrijeme_osluskivanja": None},
    "20230010": {"ime": "Stefan", "prezime": "Stefanović", "lozinka": "pass282930", "index": "20230010", "ip_adresa": None, "prisustvo": False, "vrijeme_osluskivanja": None, "ukupno_vrijeme_osluskivanja": None},
}

def update_leds():
    global timer_running
    global stop_time
    global users
   
    if not timer_running:
        red_led_pin.on()
        green_led_pin.off()
        blue_led_pin.off()
    elif timer_running and not stop_time:
        red_led_pin.off()
        green_led_pin.on()
        blue_led_pin.off()
    elif timer_running and stop_time:
        red_led_pin.on()
        green_led_pin.on()
        blue_led_pin.off()


ap = network.WLAN(network.AP_IF)
ap.config(essid=ssid, password=password)
ap.active(True)

wait_counter = 0
while not ap.active():
    print("waiting " + str(wait_counter))
    time.sleep(0.5)
    wait_counter += 1

print('WiFi active')
print(ap.ifconfig())
update_leds()
def timer_callback(timer):
    global elapsed_time
    elapsed_time += 1
   
def button_start_handler(pin):
    global timer_running
    global start_time
    global stop_time
   
    if not timer_running:
        timer_running = True
        start_time = time.time()
        timer.init(freq=1, mode=machine.Timer.PERIODIC, callback=timer_callback)
    elif not stop_time:
        stop_time = True
        timer.deinit()
    elif timer_running:
        stop_time = False
        start_time = time.time()
        timer.init(freq=1, mode=machine.Timer.PERIODIC, callback=timer_callback)
    update_leds()
       

def button_stop_handler(pin):
    global timer_running
    global elapsed_time
    global users
    update_leds()

    for user_id in users:
        if users[user_id]["prisustvo"]:
            user_time = users[user_id]["vrijeme_osluskivanja"]
            if user_time is not None:
                time_diff = int(elapsed_time) - int(user_time)
                diff_hours = time_diff // 3600
                diff_minutes = (time_diff % 3600) // 60
                diff_secs = time_diff % 60
                users[user_id]["ukupno_vrijeme_osluskivanja"] = "{:02d}:{:02d}:{:02d}".format(diff_hours, diff_minutes, diff_secs)
            else:
                users[user_id]["ukupno_vrijeme_osluskivanja"] = "N/A"
   
   
    timestamp = time.time()
    json_filename = "users_" + str(int(timestamp)) + ".json"
   

    json_data = json.dumps(users)
   
    formatted_json_data = json_data.replace(',', ',\n').replace('{', '{\n').replace('}', '\n}')
   
    with open(json_filename, 'w') as json_file:
        json_file.write(formatted_json_data)
   
    for user_id in users:
        users[user_id]["ip_adresa"] = None
        users[user_id]["prisustvo"] = False
        users[user_id]["vrijeme_osluskivanja"] = None
        users[user_id]["ukupno_vrijeme_osluskivanja"] = None
    timer_running = False
    timer.deinit()
    elapsed_time = 0
   
button_start_pin.irq(trigger=machine.Pin.IRQ_RISING, handler=button_start_handler)
button_stop_pin.irq(trigger=machine.Pin.IRQ_RISING, handler=button_stop_handler)


def generate_html():
    global timer_running
    global start_time
    global stop_time
    global elapsed_time
   
    current_time = elapsed_time

    # Pretvaranje vremena u format "HH:MM:SS"
    hours = int(current_time) // 3600
    minutes = (int(current_time) % 3600) // 60
    secs = int(current_time) % 60
    time_str = "{:02d}:{:02d}:{:02d}".format(hours, minutes, secs)
   
    if stop_time:
        time_str = time_str + " (Pauza)"
   
    # Generisanje HTML-a
    client_list = "<ul>"
    for index, user in users.items():
        if user["prisustvo"]:
            user_time = user["vrijeme_osluskivanja"]
            if user_time is not None:
                time_diff = int(current_time) - int(user_time)
                diff_hours = time_diff // 3600
                diff_minutes = (time_diff % 3600) // 60
                diff_secs = time_diff % 60
                time_diff_str = "{:02d}:{:02d}:{:02d}".format(diff_hours, diff_minutes, diff_secs)
            else:
                time_diff_str = "N/A"
            client_list += f"<li>{user['ime']} {user['prezime']} ({user['ip_adresa']}) - Vrijeme osluškivanja: {time_diff_str}</li>"
    client_list += "</ul>"

    html_content = f"""<!DOCTYPE html>
    <html>
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Prisustvo</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f4f4f9;
        }}
        .container {{
            width: 80%;
            margin: auto;
            overflow: hidden;
        }}
        header {{
            background: #50b3a2;
            color: #fff;
            padding-top: 30px;
            min-height: 70px;
            border-bottom: #2980b9 3px solid;
        }}
        header h1 {{
            text-align: center;
            text-transform: uppercase;
            margin: 0;
            font-size: 24px;
        }}
        ul {{
            list-style: none;
            padding: 0;
        }}
        ul li {{
            background: #fff;
            color: #333;
            padding: 10px;
            margin-bottom: 5px;
            border-radius: 5px;
        }}
        form {{
            background: #fff;
            padding: 20px;
            border-radius: 5px;
            margin-top: 20px;
        }}
        form label {{
            display: block;
            margin-bottom: 5px;
        }}
        form input[type="text"],
        form input[type="password"] {{
            width: 100%;
            padding: 10px;
            margin-bottom: 10px;
            border: 1px solid #ccc;
            border-radius: 5px;
        }}
        form input[type="submit"] {{
            background: #50b3a2;
            color: #fff;
            border: 0;
            padding: 10px 15px;
            cursor: pointer;
            border-radius: 5px;
        }}
    </style>
    </head>
    <body>
    <header>
        <div class="container">
            <h1>Prisustvo</h1>
        </div>
    </header>
    <div class="container">
        <h2>Prisutni studenti:</h2>
        {client_list}
        <h2>Tajmer:</h2>
        <p>Trenutno proteklo vreme: {time_str}</p>
        <h2>Unesite svoj index i lozinku</h2>
        <form action="/" method="POST">
            <label for="index">Index:</label>
            <input type="text" id="index" name="index">
            <label for="password">Lozinka:</label>
            <input type="password" id="password" name="password">
            <input type="submit" value="Submit">
        </form>
       
        <h2>Dodaj novog korisnika:</h2>
        <form action="/add_user" method="POST">
            <label for="sifa_unosa_studenta">Sifra za pristup unosa studenta:</label>
            <input type="text" id="sifa_unosa_studenta" name="sifa_unosa_studenta">
            <label for="new_name">Ime:</label>
            <input type="text" id="new_name" name="new_name">
            <label for="new_last_name">Prezime:</label>
            <input type="text" id="new_last_name" name="new_last_name">
            <label for="new_index">Indeks:</label>
            <input type="text" id="new_index" name="new_index">
            <label for="new_password">Lozinka:</label>
            <input type="password" id="new_password" name="new_password">
            <input type="submit" value="Dodaj">
        </form>
       
        <h2>Izbrisi/Izbaci studenta:</h2>
        <form action="/errase_user" method="POST">
            <label for="sifa_brisanja_studenta">Sifra za pristup brisanja studenta:</label>
            <input type="text" id="sifa_brisanja_studenta" name="sifa_brisanja_studenta">            
            <label for="errase_index">Indeks:</label>
            <input type="text" id="errase_index" name="errase_index">
            <input type="submit" value="Izbrisi">
        </form>
    </div>
    </body>
    </html>"""
   
    return html_content
# Funkcija za parsiranje POST zahtjeva za dodavanje novih korisnika
def parse_new_user_request(request):
    match = ure.search(r"sifa_unosa_studenta=([^&]*)&new_name=([^&]*)&new_last_name=([^&]*)&new_index=([^&]*)&new_password=([^&]*)", request)
    if match:
        return match.group(1), match.group(2), match.group(3), match.group(4), match.group(5)
    return None, None, None, None, None

def parse_errase_user_request(request):
    match = ure.search(r"sifa_brisanja_studenta=([^&]*)&errase_index=([^&]*)", request)
    if match:
        return match.group(1), match.group(2)
    return None, None


# Postavljanje adrese i porta za socket
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]

# Kreiranje socket-a
s = socket.socket()
s.bind(addr)
s.listen(1)

print('listening on', addr)

# Funkcija za parsiranje POST zahteva
def parse_request(request):
    match = ure.search(r"index=([^&]*)&password=([^&]*)", request)
    if match:
        return match.group(1), match.group(2)
    return None, None

def is_ip_in_use(ip):
    for index, user in users.items():
        if user["ip_adresa"] == ip:
            return True
    return False


# Slušanje zahteva na socket-u
while True:
    try:
        cl, addr = s.accept()
        print('client connected from', addr)
        request = cl.recv(1024).decode('utf-8')
        print(request)
       
        if "POST" in request:
            if "new_name" in request:
                sifa_unosa_studenta, new_name, new_last_name, new_index, new_password = parse_new_user_request(request)
                if new_name and new_last_name and new_index and new_password and sifa_unosa_studenta == "1234":
                    users[new_index] = {"ime": new_name, "prezime": new_last_name, "lozinka": new_password,
                                        "index": new_index, "ip_adresa": None, "prisustvo": False,
                                        "vrijeme_osluskivanja": None, "ukupno_vrijeme_osluskivanja": None}
                                       
            if "sifa_brisanja_studenta" in request:
                sifa_brisanja_studenta,  errase_index = parse_errase_user_request(request)
                if errase_index and sifa_brisanja_studenta == "1234":
                    if errase_index in users:
                        del users[errase_index]
                        print(f"korisnik sa indexom {errase_index} je uspjesno obrisan")
                    else:
                        print(f"korisnik sa indexom {errase_index} ne postoji")
                   
                   
            index, password = parse_request(request)
            if index and password and index in users:
                user = users[index]
                if user["lozinka"] == password and not is_ip_in_use(addr[0]):
                    user["prisustvo"] = True
                    user["ip_adresa"] = addr[0]
                    user["vrijeme_osluskivanja"] = elapsed_time  # Postavljanje vremena osluškivanja
                    connected_clients.add(addr[0])

        cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
        cl.send(generate_html())
        cl.close()
    except OSError as e:
        cl.close()
        print('connection closed')