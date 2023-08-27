import random
import socket
import threading
import time

import globals
from message import Message


class Client():
    
    def __init__(self, id: int, socket: socket.socket, action: callable) -> None:
        self.id = id
        self.type = None # TODO Snake/Minesweeper/PacMan, etc...
        self.socket = socket
        self.thread = threading.Thread(target=action, args=(self,))
        self.thread.start()
        message = Message("Connection successful!", self.id, self.socket)
        message.send()
        self.nn = None # TODO make a way for each client to access the population

    def solve(self):
        msg = Message("size", self.id, self.socket)
        msg.send()
        msg = Message.decipher(self.socket.recv(globals.MAX_MSG_LEN))
        msg = Message.decipher(self.socket.recv(globals.MAX_MSG_LEN))
        g_width, g_height = [int(coord) - 1 for coord in msg.get_content().split(",")]
        print("Grid size:\nWidth: %i\nHeight: %i" % (g_width + 1, g_height + 1))
        solved = False
        while not solved:
            x_rand, y_rand = random.randint(0, g_width), random.randint(0, g_height)
            Message("reveal %i %i" % (x_rand, y_rand), self.id, self.socket).send()
            msg = Message.decipher(self.socket.recv(globals.MAX_MSG_LEN))
            if "mine" in msg.get_content():
                input("Lost. Press Any key to retry")
                Message("reset", self.id, self.socket).send()
            time.sleep(0.5)

    
    def ping(self):
        i = 0
        while True:
            msg = Message("\nPinging... %i" % i, self.id, self.socket)
            msg.send()
            i += 1
            time.sleep(1)

