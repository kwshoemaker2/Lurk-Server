#!/usr/bin/python
import socket
import threading
from lurkgame import *
from sys import argv

class LurkServer:
    def __init__(self, sock):
        self.sock = sock
        self.threads = []
        self.running = False
        self.game = LurkGame()

    def run(self):
        self.running = True
        self.game.playing = True
        self.sock.listen(5)
        while self.running:
            newSock, cs = self.sock.accept()
            t = threading.Thread(None, self.game.startPlayer, None, args = (newSock,))
            self.threads.append(t)
            t.start()

        self.shutdown()

    def shutdown(self):
        self.running = False
        self.game.playing = False
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
            self.sock.close()
            for t in self.threads:
                t.join()

        except:
            pass

if __name__ == "__main__":
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    port = 9000
    if(len(argv) > 1):
        port = int(argv[1])

    s.bind(("", port))
    serv = LurkServer(s)
    try:
        serv.run()

    except:
        s.shutdown(socket.SHUT_RDWR)
        s.close()
        serv.shutdown()











































