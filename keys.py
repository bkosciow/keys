import RPi.GPIO as GPIO
import time
import os
import socket
import configparser
import sys


ini_file = "/etc/keys/keys.ini"
service_file = "/lib/systemd/system/keys.service"
app_file = "/usr/local/bin/keys.py"


def install():
    import shutil
    import subprocess
    print("""Copy keys.ini to %s""" % ini_file)
    os.makedirs(os.path.dirname(ini_file), exist_ok=True)
    shutil.copy("keys.ini", ini_file)
    print("""Copy keys.service to %s """ % service_file)
    shutil.copy("keys.service", service_file)
    print("""Copy self to %s """ % app_file)
    shutil.copy("keys.py", app_file)
    print("Stopping service")
    result = subprocess.run(["systemctl", "stop", "keys.service"], capture_output=True)
    print("Starting service")
    result = subprocess.run(["systemctl", "start", "keys.service"], capture_output=True)
    if "systemctl daemon-reload" in result.stderr.decode('utf8'):
        subprocess.run(["systemctl", "daemon-reload"])
        result = subprocess.run(["systemctl", "start", "keys.service"], capture_output=True)
    print(result)
    print("Enable start on boot")
    result = subprocess.run(["systemctl", "enable", "keys.service"], capture_output=True)
    print(result)


if len(sys.argv) == 2 and sys.argv[1] == 'install':
    print("Installing...")
    install()
    print("Done")
    print("Type")
    print("systemctl status keys.service")
    print("to check if all is ok")
    exit(0)
elif len(sys.argv) != 1:
    print("Unknown parameters, use `install` to install")
    exit(1)


GPIO.setmode(GPIO.BCM)

config = configparser.ConfigParser()
config.read(ini_file)

any_actions = False
for pin in config['actions']:
    any_actions = True
    if not pin.isnumeric():
        print("""Value `%s` is not a valid pin""" % (pin))
        exit(1)
    if config['actions'][pin] == '':
        print("""Name for pin `%s` is empty""" % (pin))
        exit(1)

if not any_actions:
    print("No actions set")
    exit(1)


socket_path = config['general']['socket']
max_clients = config['general']['clients']
bounce = config['general']['bounce']

if socket_path == '':
    print("Set `socket` in config file as writable path with file! (/tmp/socket)")
    exit(1)

if max_clients == '' or not max_clients.isnumeric():
    print("Set `clients` in config file as number! (10)")
    exit(1)

if bounce == '' or not bounce.isnumeric():
    print("Set `bounce` in config file as number! (700)")
    exit(1)


try:
    os.unlink(socket_path)
except OSError:
    if os.path.exists(socket_path):
        raise


class Buttons:
    def __init__(self, bounce):
        self.btns = {}
        self.bounce = int(bounce)

    def add(self, pin, name):
        self.btns[pin] = {
            'name': name,
        }
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(pin, GPIO.RISING, callback=self.action, bouncetime=self.bounce)

    def action(self, gpio):
        send_all(self.btns[gpio]['name'].encode("utf8"))


clients = []
socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
socket.bind(socket_path)
socket.listen(int(max_clients))


def send_all(content):
    global clients
    for idx, s in enumerate(clients.copy()):
        try:
            s.send(content)
        except BrokenPipeError:
            del clients[idx]


BTNS = Buttons(bounce)

for pin in config['actions']:
    BTNS.add(int(pin), config['actions'][pin])

while True:
    client_socket, addr = socket.accept()
    clients.append(client_socket)
    time.sleep(0.2)
