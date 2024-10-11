# Libraries
import logging
from logging.handlers import RotatingFileHandler
import socket
import paramiko 
import threading

# Constraints
logging_format = logging.Formatter('%(message)s')
SSH_BANNER = ""

# host_key = "server.key"
host_key = paramiko.RSAKey(filename='Server.key')

# Loggers and Logging Files
funnel_logger = logging.getLogger("FunnelLogger") # This are going to capture those username, IP, and pswd

# ----- There are log levels - We are going with Info one 
funnel_logger.setLevel(logging.INFO)
funnel_handler = RotatingFileHandler("audits.log", maxBytes=2000, backupCount=5)
funnel_handler.setFormatter(logging_format)
funnel_logger.addHandler(funnel_handler) # Added those handler in this

creds_logger = logging.getLogger("credsLogger")
creds_logger.setLevel(logging.INFO)
creds_handler = RotatingFileHandler("cmd_audits.log", maxBytes=2000, backupCount=5)
creds_handler.setFormatter(logging_format)
creds_logger.addHandler(creds_handler) 

# Emulated Shells 
def emulated_shell(channel, client_ip):
    channel.send(b'corporate-jumpbos2$ ')
    command = b"" # listening user inputs 
    while True:
        char = channel.recv(1) # listening
        channel.send(char) # Sending that heard stuff
        if not char:
            channel.close()

        command += char 

        if char == b'\r':
            if command.strip() == b'exit':
                response = b'\n GoodBye\n'
                channel.close()
            elif command.strip() == b'pwd':
                response = b'\\usr\local' + b'\r\n'
                creds_logger.info(f"Command {command.strip()}" + "executed by" + f"{client_ip}")
            elif command.strip() == b'whoami':
                response = b"\n" + b"corpuser1" + b"\r\n"
                creds_logger.info(f"Command {command.strip()}" + "executed by" + f"{client_ip}")
            elif command.strip() == b'ls':
                response = b'\n' + b"jumpbox1.conf" + b"\r\n"
                creds_logger.info(f"Command {command.strip()}" + "executed by" + f"{client_ip}")
            elif command.strip() == b'cat jumpbox1.conf':
                response = b"\n" + b"Go to deeboodah.com." + b"\r\n"
                creds_logger.info(f"Command {command.strip()}" + "executed by" + f"{client_ip}")
            else:
                response = b'\n' + bytes(command.strip()) + b'\r\n'
                creds_logger.info(f"Command {command.strip()}" + "executed by" + f"{client_ip}")

        channel.send(response)
        channel.send(b'corpoaret-jumpbox2$ ')
        command = b""


# SSh Server + Sockets
class Server(paramiko.ServerInterface):
    
    def __init__(self, client_ip, input_username=None, input_password=None):
        self.event = threading.Event()
        self.client_ip = client_ip
        self.input_username = input_username
        self.input_password = input_password

    def check_channel_request(self, kind: str, chanid: int) -> int:
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        
    def get_allowed_auths(self):
        return "password"

    def check_auth_password(self, username, password):
        funnel_logger.info(f"Client {self.client_ip} attempted connection with " + f"username {username}, " + f"password {password}")
        creds_logger.info(f'{self.client_ip}, {username}, {password}')
        if self.input_username is not None and self.input_password is not None:
            if username == self.input_username and password == self.input_password:
                return paramiko.AUTH_SUCCESSFULL
            else:
                return paramiko.AUTH_FAILED
        else:
            return paramiko.AUTH_SUCCESSFUL
            
    def check_channel_shell_request(self, channel):
        self.event.set()
        return True
    
    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        return True
    
    def check_channel_exec_request(self, channel, command):
        command = str(command)
        return True
    
def client_handle(client, addr, username, password):
    client_ip = addr[0]
    print(f"{client_ip} has connected to the server")
    try:
        transport = paramiko.Transport(client)    # pass
        transport.local_version = SSH_BANNER
        server = Server(client_ip=client_ip, input_username=username, input_password=password)

        transport.add_server_key(host_key)

        transport.start_server(server=server)

        channel = transport.accept(100) # waits for the client to open a channel
        if channel is None:
            print("No channel is open")

        standard_banner = "Welcome to ubuntu 22.04 LTS (Jammy Jellyfish)! \r\n\r\n"
        channel.send(standard_banner)
        emulated_shell(channel, client_ip=client_ip)

    except Exception as error:
        print(error) # pass
        print("!!!! ERROR !!!!")

    finally:
        try:         # pass
            transport.close()
        except Exception as error:
                print(error)
                print("!!!! ERROR !!!!")
        client.close()


# Provision SSH-Based Honeypot

def honeypot(address, port, username, password):
    socks = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # AF_INET - IPv4 address we are going to listening... Stream one - listening through TCP port
    socks.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # 1 enables these two options here...
    socks.bind((address, port))

    socks.listen(100)
    print(f"SSH server is listening on port {port}")

    while True:
        try:
            client, addr = socks.accept()
            ssh_honeypot_thread = threading.Thread(target=client_handle, args=(client, addr, username, password))
            ssh_honeypot_thread.start()
            

        except Exception as error:
            print(error)

        
honeypot('127.0.0.1', 2223, username=None, password=None)