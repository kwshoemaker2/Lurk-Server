#!/usr/bin/python
import socket
import threading
from lurkcharacters import *
from room import *

def toInt(s):
    try:
        return int(s)

    except:
        return None

class LurkGame(object):
    def __init__(self):
        self.playing = False
        self.rooms = {}
        self.players = {}
        self.description = ""
        self.headers = ["CNNCT", "ATTCK", "REGEN", "DEFNS", "DESCR", "ACTON", "LVLUP", "LEAVE", "QUERY" ]
        self.initial = None
        self.lock = threading.RLock()
        self.buildGame()

    def startPlayer(self, sock):
        name = ""
        while self.playing and name == "":
            resp = ""
            try:
                resp = sock.recv(1024 * 1024)

            except:
                pass

            if len(resp) == 0: 
                sock.close()
                return
            
            elif resp[-1] == "\n":
                resp = resp[:-1]

            head = resp[:5]
            
            if head == "QUERY":
                s = self.baseQuery()
                infom = "INFOM %d" % len(s)
                try:
                    sock.send(infom)
                    sock.send(s)

                except:
                    pass

            elif head == "CNNCT":
                name = resp[6:].strip()

            elif head == "LEAVE":
                try:
                    sock.send("ACEPT Fine")
                    sock.shutdown(socket.SHUT_RDWR)
                    sock.close()

                except:
                    pass

                return

            elif head in self.headers:
                sock.send("REJEC Incorrect State")

            if name != "":
                if name not in self.players:
                    sock.send("ACEPT New Player")
                    self.registerPlayer(sock, name)
                    return
                
                elif self.players[name] != None and not self.players[name].isPlaying():
                    with self.lock:
                        sock.send("ACEPT Reprising player")
                        player = self.players[name]
                        player.login(sock)
                    self.playGame(player)
                    return

                else:
                    sock.send("REJEC Name taken")
                    name = ""


    def playGame(self, player):
        print("Playing with player:\n" + str(player))
        with self.lock:
            self.messageAll("NOTIF %s begins breathing and comes alive!" % player.getName())
            r = player.getLocation()
            r.addPlayer(player)
            self.sendRoomInfo(player)

        while self.playing and player.isPlaying() and player.isAlive():
            resp = player.recvMessage(1024 * 1024)
            if(resp) == "":
                print("Player connection died it looks like")
                self.logoutPlayer(player)
                return

            if resp[-1] == "\n":
                resp = resp[:-1]

            head = resp[:5]
            if head == "ACTON":
                head = resp[6:].strip()[0:5]


            if head in self.headers and not player.isAlive():
                with self.lock:
                    player.sendMessage("REJEC Incorrect State")
                self.killPlayer(player)
                return

            elif head == "LEAVE":
                with self.lock:
                    player.sendMessage("ACEPT Your lifeless corpse hits the floor")
                self.logoutPlayer(player)
                return

            elif head == "QUERY":
                self.sendQuery(player)

            elif head == "SHOUT":
                parts = resp.split(' ', 2)
                msg = ""
                if len(parts) > 2:
                    msg =  parts[2]
                
                with self.lock:
                    r = player.getLocation()
                    r.messageAll("MESSG %s shouts %s" % (player.getName(), msg))

            elif head == "MESSG":
                parts = resp.split(' ', 3)
                name, msg = "", ""
                if len(parts) >= 3:
                    name = parts[2]

                if len(parts) >= 4:
                    msg = parts[3]
                
                with self.lock:
                    if name not in self.players or self.players[name] == None or not self.players[name].isPlaying():
                        player.sendMessage("REJEC Can't send message")

                    else:
                        self.message(player, self.players[name], msg)
                        player.sendMessage("ACEPT Fine")
                

            elif head == "CHROM":
                parts = resp.split(' ', 2)
                roomname = ""
                if len(parts) >= 3:
                    roomname = parts[2]
                with self.lock:
                    r = player.getLocation()
                    print("Player %s asked to move to %s" % (player.getName(), roomname))
                    if r.hasConnection(roomname):
                        self.movePlayer(player, self.rooms[roomname])

                    else:
                        player.sendMessage("REJEC No Connection")

            elif head == "FIGHT":
                parts = resp.split(' ', 3)
                fought = False
                with self.lock:
                    if len(parts) < 3:
                        print("Player %s is fighting a bunch of monsters!" % player.getName())
                        fought = player.getLocation().fightPlayerAgainstMonsters(player)

                    else:
                        name = parts[2]
                        if name in self.players and self.players[name] != None and self.players[name].isPlaying():
                            who = self.players[name]
                            fought = player.getLocation().fightPlayers(player, who)

                    if fought:
                        player.sendMessage("ACEPT Fine")
                        self.sendRoomInfo(player)

                    else:
                        player.sendMessage("REJEC Cannot set up fight")

                if not player.isAlive():
                    self.killPlayer(player)
                    return

            elif head == "LVLUP":
                stat = ""
                parts = resp.split(' ', 2)

                if player.getGold() < 50:
                    with self.lock:
                        player.sendMessage("REJEC Need 50 gold or more")
                    continue
                elif len(parts) >= 3:
                    stat = parts[2]

                self.levelUp(player, stat)

            elif head == "JOINB":
                with self.lock:
                    player.sendMessage("ACEPT Fine")


    def killPlayer(self, player):
        with self.lock:
            player.sendMessage("NOTIF Death")
            self.players[player.getName()] = None
            player.getLocation().removePlayer(player)
        head = player.recvMessage(1024 * 1024)[:5]
        while head != "LEAVE":
            with self.lock:
                if head in self.headers:
                    player.sendMessage("REJEC Incorrect State")
            head = player.recvMessage(1024 * 1024)[:5]

        with self.lock:
            player.sendMessage("ACEPT Fine")
            player.logout()


    def logoutPlayer(self, player):
        with self.lock:
            player.logout()
            r = player.getLocation()
            r.removePlayer(player)


    def levelUp(self, player, stat):
        with self.lock:
            if stat.lower() == "attack":
                player.attack += 10

            elif stat.lower() == "defense":
                player.defense += 10

            elif stat.lower() == "regen":
                player.regen += 10

            elif stat.lower() == "health":
                player.health += 50
                player.maxHealth += 50

            else:
                player.sendMessage("REJEC No valid stat sent (send attack, defense, regen, or health")
                return

            player.gold -= 50
            player.sendMessage("ACEPT Succsefully updated")

    def messageAll(self, message):
        with self.lock:
            for name in self.players:
                p = self.players[name]
                if p != None and p.isPlaying():
                    p.sendMessage(message)


    def registerPlayer(self, sock, name):
        attack = None
        defens = None
        regen = None
        descr = None
        started = False
        statTotal = 0
        while ((attack == None or defens == None or regen == None or 
                descr == None or not started) and self.playing):

            resp = sock.recv(1024 * 1024)
            if len(resp) == 0:
                sock.close()
                return

            if resp[-1] == "\n":
                resp = resp[:-1]

            head = resp[:5]
            if head == "DESCR":
                descr = resp[6:]
                sock.send("ACEPT Fine")

            elif head == "ATTCK":
                attack = toInt(resp[6:].strip())
                if attack == None:
                    attack = 1
                
                sock.send("ACEPT Fine")

            elif head == "DEFNS":
                defens = toInt(resp[6:].strip())
                if defens == None:
                    defens = 1

                sock.send("ACEPT Fine")


            elif head == "REGEN":
                regen = toInt(resp[6:].strip())
                if regen == None:
                    regen = 1
                
                sock.send("ACEPT Fine")


            elif head == "START":
                if (attack == None or defens == None or regen == None or descr == None):
                    print(attack, defens, regen, descr)
                    sock.send("REJEC Incorrect state")

                else:
                    started = True
                    sock.send("ACEPT Fine")

            elif head == "QUERY":
                s = self.baseQuery()
                infom = "INFOM %d" % len(s)
                try:
                    sock.send(infom)
                    sock.send(s)

                except:
                    pass


            elif head == "LEAVE":
                try:
                    sock.send("ACEPT Not Started")
                    sock.shutdown(socket.SHUT_RDWR)
                    sock.close()

                except:
                    pass

                return None
        
        with self.lock:
            player = Player(sock, name, attack, defens, regen, 100, 0, descr)
            player.setRoom(self.initial)
            player.setPlaying(True)
            self.players[name] = player
        self.playGame(player)

    def baseQuery(self):
        s = ""
        s += "GameDescription: " + self.description
        s += "\n\nExtension: SHOUT"
        s += "\nNiceName: shout"
        s += "\nType: ACTON"
        s += "\nDescription: Talk to everyone in the room"
        s += "\nParameter: message"
 
        s += "\n\nExtension: LVLUP"
        s += "\nNiceName: lvlup"
        s += "\nType: MESSAGE"
        s += "\nDescription: Spend gold to level up one of your stats"
        s += "\nParameter: Stat\n\n"

        return s

    def sendQuery(self, player):
        with self.lock:
            s = self.baseQuery()
            s += str(player)

            for name in self.players:
                p = self.players[name]
                if p != None and p.isPlaying() and p.getName() != player.getName():
                    s += "\nPlayer: " + p.getName()

            infom = "INFOM %d" % len(s)
            player.sendMessage(infom)
            player.sendMessage(s)


    def message(self, p1, p2, message):
        with self.lock:
            if p2 != None and p2.isPlaying():
                p2.sendMessage("ACTON MESSG %s says to you: %s" % (p1.getName(), message))

            else:
                p1.sendMessage("REJEC Unable to message")

    def movePlayer(self, player, room):
        with self.lock:
            r = player.getLocation()
            r.removePlayer(player)
            room.addPlayer(player)
            player.changeLocation(room)
            self.sendRoomInfo(player)
            player.regenerate()


    def sendRoomInfo(self, player):
        with self.lock:
            r = player.getLocation()
            s = str(player)
            infos = ["INFOM %d" % len(s), s]
            infos.extend(r.allInfos())
            for info in infos:
                player.sendMessage(info)


    def buildGame(self):
        self.description = """You are a crewmember on a starship travelling through space. You wake up to discover that a bunch of zombie-like aliens called the Zorthons have taken over the ship and begun zombifying crew members! After equipping yourself with 100 points of attack, defense, and regen, you venture out to save your ship
        """
        crew_lounge = Room("Crew Lounge", "Used to be a relaxing place", 10)
        bridge = Room("Bridge", "Former command center. Now overrun with Zorthon zombies", 20)
        captain_quart = Room("Captain's Quarters", "The captain is still here, though not quite the same...", 50)
        holodeck = Room("Holodeck", "Currently shut off. This is no time for relaxation or enjoyment!", 0)
        sickbay = Room("Sickbay", "Not currently operational. So don't get hurt!", 0)
        elevator = Room("Elevator", "Will lead you to many different rooms", 0)
        crew_quart = Room("Crew Quarters", "Living quarters for the crew. Now dead quarters for the crew", 30)
        transport = Room("Transporter Room", "Will take you to the Zorthon ship", 0)
        hallway = Room("Hallway", "A long hallway on the Zorthon ship. Filled with tubes...", 50)
        assim = Room("Assimilation Chamber", "Where the Zorthons assimilate their victims!", 100)
        hive = Room("Hive Central", "The queen is here! Destroy her!", 500)
        for room in [crew_lounge, bridge, captain_quart, holodeck, sickbay, elevator, crew_quart, transport,
                     hallway, assim, hive]:
            self.rooms[room.getName()] = room

        # add monsters
        bridge.addMonster(Monster("Zorthon Drone", 40, 40, 10, 150, 70, "Basic Drone of the Zorthon Empire"))
        bridge.addMonster(Monster("Zorthon Drone", 40, 40, 10, 150, 70, "Basic Drone of the Zorthon Empire"))

        captain_quart.addMonster(Monster("Zorthonized Captain", 80, 80, 15, 300, 500, "Your captain as a Zorthon!"))

        holodeck.addMonster(Monster("Riker", 500, 0, 0, 5, 100, "Commander of some star ship somewhere. Very deadly in the holodeck"))

        sickbay.addMonster(Monster("Zorthonized Doctor", 5, 100, 10, 30, 50, "Can't see you right now. She's a Zorthon!"))

        crew_quart.addMonster(Monster("Zorthon Drone", 40, 40, 10, 150, 70, "Basic Drone of the Zorthon Empire"))
        crew_quart.addMonster(Monster("Zorthon Drone", 40, 40, 10, 150, 70, "Basic Drone of the Zorthon Empire"))

        transport.addMonster(Monster("Zorthon Drone", 40, 40, 10, 150, 70, "Basic Drone of the Zorthon Empire"))
        transport.addMonster(Monster("Zorthon Drone", 40, 40, 10, 150, 70, "Basic Drone of the Zorthon Empire"))
        transport.addMonster(Monster("Zorthon Drone", 40, 40, 10, 150, 70, "Basic Drone of the Zorthon Empire"))
        
        hallway.addMonster(Monster("Zorthon Drone", 40, 40, 10, 150, 70, "Basic Drone of the Zorthon Empire"))
        hallway.addMonster(Monster("Zorthon Drone", 40, 40, 10, 150, 70, "Basic Drone of the Zorthon Empire"))
        hallway.addMonster(Monster("Zorthon Drone", 40, 40, 10, 150, 70, "Basic Drone of the Zorthon Empire"))

        hive.addMonster(Monster("Zorthon Queen", 500, 500, 50, 2000, 2000, "The queen! Destroy her!"))

        # add connections
        crew_lounge.addConnection(holodeck)
        crew_lounge.addConnection(crew_quart)
        crew_lounge.addConnection(elevator)

        bridge.addConnection(elevator)
        bridge.addConnection(captain_quart)
        
        captain_quart.addConnection(bridge)

        holodeck.addConnection(crew_lounge)

        sickbay.addConnection(elevator)

        elevator.addConnection(crew_lounge)
        elevator.addConnection(bridge)
        elevator.addConnection(sickbay)
        elevator.addConnection(transport)
        elevator.addConnection(crew_quart)

        crew_quart.addConnection(elevator)
        crew_quart.addConnection(crew_lounge)

        transport.addConnection(elevator)
        transport.addConnection(hallway)

        hallway.addConnection(assim)
        hallway.addConnection(hive)

        assim.addConnection(hallway)

        hive.addConnection(hallway)

        self.initial = crew_lounge


































