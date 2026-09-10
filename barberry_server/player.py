# -*- coding: utf-8 -*-
"""
Barberry Server 2.0 — класс игрока
"""

from protocol import encode_message

class Player:
    def __init__(self, player_id, nickname, x, y, writer=None):
        self.id = player_id
        self.nickname = nickname
        self.x = x
        self.y = y
        self.hp = 100
        self.hunger = 100
        self.role = "guest"
        self.writer = writer
        self.ip = None
        self.client_hash = None

    def to_dict(self):
        return {
            "id": self.id,
            "nickname": self.nickname,
            "x": self.x,
            "y": self.y,
            "hp": self.hp,
            "hunger": self.hunger,
            "role": self.role
        }

    def update_position(self, x, y):
        self.x = x
        self.y = y

    def send(self, data):
        if self.writer:
            try:
                self.writer.write(encode_message(data))
            except:
                pass
