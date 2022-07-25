from actions import say_save
import socket
say_save(socket.gethostbyname(socket.gethostname()))
