#!/usr/bin/python

class Room(object):
    def __init__(self, name, description, gold):
        self.name = name
        self.description = description
        self.gold = gold
        self.monsters = []
        self.players = {}
        self.connections = {}

    def getName(self):
        return self.name

    def getDescription(self):
        return self.description

    def getGold(self):
        return self.gold

    def messageAll(self, message):
        for name in self.players:
            p = self.players[name]
            p.sendMessage(message)

    def addPlayer(self, newPlayer):
        if(newPlayer.getName() not in self.players):
            s = str(newPlayer)
            self.messageAll("NOTIF Player %s has entered you room\n" % newPlayer.getName())
            self.messageAll("INFOM %d" % len(s))
            self.messageAll(s)

            self.players[newPlayer.getName()] = newPlayer
            if self.gold > 0:
                newPlayer.gold += self.gold
                self.gold = 0
                newPlayer.sendMessage("RESLT Enter Received %d Gold" % self.gold)

            else:
                newPlayer.sendMessage("RESLT Enter No Gold")

    def removePlayer(self, player):
        del self.players[player.getName()]

    def addMonster(self, mons):
        self.monsters.append(mons)

    def addConnection(self, room):
        self.connections[room.getName()] = room

    def removeConnection(self, room):
        del self.connections[room.getName()]

    def hasConnection(self, room):
        if type(room) == type(""):
            return room in self.connections

        else:
            return room.getName() in self.connections

    def fightPlayers(self, p1, p2):
        if (p1.getName() not in self.players or p2.getName() not in self.players):
            return False

        p1.fight(p2)
        return True

    def fightPlayerAgainstMonsters(self, player):
        if player.getName() not in self.players or self.monsters == []:
            return False

        for mons in self.monsters:
            if mons.isAlive():
                player.fight(mons)
            
            if not player.isAlive():
                break

        return True

    def playerInfo(self):
        infos = []
        for name in self.players:
            player = self.players[name]
            info = str(player)
            infos.append("INFOM %d" % len(info))
            infos.append(info)

        return infos

    def monsterInfo(self):
        infos = []
        for monster in self.monsters:
            info = str(monster)
            infos.append("INFOM %d" % len(info))
            infos.append(info)

        return infos

    def roomInfo(self):
        s = ""
        s += "Name: %s" % self.name
        s += "\nDescription: %s" % self.description
        for name in self.connections:
            s += "\nConnection:  %s" % name

        for mons in self.monsters:
            s += "\nMonster:   %s" % mons.getName()

        return s + "\n"

    def allInfos(self):
        infos = []
        me = self.roomInfo() + "\n"
        infos.append("INFOM %d" % len(me))
        infos.append(me)
        infos.extend(self.playerInfo())
        infos.extend(self.monsterInfo())
        return infos
































