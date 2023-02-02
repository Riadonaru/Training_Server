import math
import numpy as np
import signal
import socket
import os
import threading
from typing import List

from client import Client
import globals
from message import Message


class Server():

    # ============================Start=of=Commands======================== #

    def help(self, args: str):
        with open(globals.PATH + "HELP.md") as f:
            print(f.read())

    def switch(self, args: str):
        try:
            new_id = int(args)
            if new_id >= len(self.clients) or self.clients[new_id] == None:
                print("switch: client id must be in %s" % [
                      id for id in range(len(self.clients)) if self.clients[id] != None])
            else:
                self.target_client_id = new_id
        except ValueError:
            print("switch: client id must be a number!")

    def shutdown(self, args: str):
        if args[:3] == "-a":
            for client in self.clients:
                if client != None:
                    msg = Message("shutdown", client.id, client.socket)
                    msg.send()
        os.kill(os.getpid(), signal.SIGTERM)

    def client_command(self, command: str):
        if len(self.clients) > 0:
            target_client = self.clients[self.target_client_id]
            if target_client != None:
                msg = Message(command, self.target_client_id,
                              target_client.socket)
                msg.send()
            else:
                print("Client %i is no longer connected!" %
                      self.target_client_id)
        else:
            print("No client is connected...")

    # ============================End=of=Commands======================== #

    def __init__(self) -> None:
        self.socket = socket.socket()
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        for i in range(globals.MAX_RETRIES):
            try:
                self.socket.bind((globals.HOST, globals.PORT))
                break
            except socket.error as e:
                if i >= globals.MAX_RETRIES - 1:
                    raise socket.error(e)
        self.clients: List[Client] = []
        self.inp_thread = threading.Thread(target=self.usr_inpt)
        self.thread = threading.Thread(target=self.run)
        self.target_client_id = 0
        self.commands = {
            "help": self.help,
            "switch": self.switch,
            "shutdown": self.shutdown,
        }
        print('Listening for incoming connections...')
        self.socket.listen(globals.MAX_CONNECTIONS)

    def next_client_id(self):
        for i, client in enumerate(self.clients):
            if not client:
                del self.clients[i]
                return i

        return len(self.clients)

    def usr_inpt(self):
        while True:
            inpt = input()
            if inpt:
                splinpt = inpt.split(maxsplit=1)
                if splinpt in self.commands.keys():
                    self.commands[splinpt[0]]("" if len(splinpt) <= 1 else splinpt[1])
                    continue
                self.client_command(inpt)

    def output(self, client: Client):
        get = False
        while True:
            msg = Message.decipher(client.socket.recv(globals.MAX_MSG_LEN))
            if msg == None:
                self.clients[client.id] = None
                print("Client %i disconnected" % client.id)
                break
            if get:
                get = False
                num_arr = msg.get_content().split()
                sqr_edge = int(math.sqrt(len(num_arr)))
                data = np.reshape(num_arr, (sqr_edge, sqr_edge))
                for list in data:
                    for num in list:
                        num = str(num)
                        if len(num) == 1:
                            num = " " + num
                        print(num, end=" ")
                    print()
            else:
                msg.print_content()

            if msg.get_content().split(maxsplit=1)[0] == "get":
                get = True

    def run(self):
        if not self.inp_thread.is_alive():
            self.inp_thread.start()

        with self.socket:
            while True:
                try:
                    sock, address = self.socket.accept()
                except socket.error:
                    print("\nStopped listening to incoming connections")
                    break
                print('Connected to: ' + address[0] + ':' + str(address[1]))
                next_id = self.next_client_id()
                self.clients.insert(next_id, Client(
                    next_id, sock, self.output))
