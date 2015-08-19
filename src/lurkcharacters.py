#!/usr/bin/python

import socket
import random

class LurkCharacter(object):
    def __init__(self, name, atk, defns, regen, health, gold, description):
        self.name = name
        self.attack = atk
        self.defense = defns
        self.regen = regen
        self.health = health
        self.maxHealth = health
        self.gold = gold
        self.description = description
        self.alive = True

    def getName(self):
        return self.name

    def getAttack(self):
        return self.attack

    def getDefense(self):
        return self.defense

    def getRegen(self):
        return self.regen

    def getHealth(self):
        return self.health

    def getGold(self):
        return self.gold

    def getDescription(self):
        return self.description

    def isAlive(self):
        return self.alive

    def updateHealth(self, amt):
        if self.health + amt < 0:
            self.health = 0
            self.alive = False

        elif self.health + amt > self.maxHealth:
            self.health = self.maxHealth

        else:
            self.health += amt

    def regenerate(self):
        if self.health > 0:
            self.updateHealth(self.regen)

    def fight(self, other):
        myDmg = self.__calculate_damage(self.defense, other.attack)
        theirDmg = self.__calculate_damage(other.defense, self.attack)
        self.updateHealth(-myDmg)
        other.updateHealth(-theirDmg)


    def __str__(self):
        s = ""
        s += "Name: %s" % self.name
        s += "\nDescription: %s" % self.description
        s += "\nGold: %s" % self.gold
        s += "\nAttack: %s" % self.attack
        s += "\nDefense: %s" % self.defense
        s += "\nRegen: %s" % self.regen
        return s

    def __calculate_damage(self, defense, attack):
        dmg = 0
        if attack == 0:
            return 0

        elif defense == 0:
            return random.randint(1, attack)

        elif attack <= defense:
            dmg = random.randint(1, attack) - (defense // attack)

        else:
            dmg = random.randint(1, attack) - (attack // defense)

        if dmg < 0: 
            return 0
        return dmg

class Player(LurkCharacter):
    def __init__(self, sock, name, atk, defns, regen, health, gold, description):
        super(Player, self).__init__(name, atk, defns, regen, health, gold, description)
        self.sock = sock
        self.room = None
        self.playing = False

    def setRoom(self, r):
        self.room = r

    def setPlaying(self, play):
        self.playing = play

    def isPlaying(self):
        return self.playing

    def changeLocation(self, newLoc):
        if type(newLoc) == type(""):
            raise ValueError("NOT CORRECT!!!")
        self.room = newLoc

    def getLocation(self):
        return self.room

    def sendMessage(self, message):
        try:
            self.sock.send(message)

        except:
            return False

        return True

    def recvMessage(self, size):
        try:
            recvd = self.sock.recv(size)
            return recvd
        except:
            return ""

    def login(self, sock):
        self.sock = sock
        self.playing = True

    def logout(self):
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
            self.sock.close()
        except:
            pass

        finally:
            self.playing = False
            self.sock = None


    def __str__(self):
        s = super(Player, self).__str__()
        if(self.isAlive()):
            s += "\nStatus: %s" % "ALIVE"
        else:
            s += "\nStatus: %s" % "DEAD"

        s += "\nLocation: %s" % self.room.getName()
        s += "\nHealth: %s"  % self.getHealth()
        s += "\nStarted: %s" % "YES"
        s += "\nJoin Battle: %s" % "YES"

        return s + "\n"


class Monster(LurkCharacter):
    def __init__(self, name, atk, defns, regen, health, gold, description):
        super(Monster, self).__init__(name, atk, defns, regen, health, gold, description)

    def __str__(self):
        s = super(Monster, self).__str__()
        s += "\nMonster"
        s += "\nHealth: %s" % self.health
        return s + "\n"









































































