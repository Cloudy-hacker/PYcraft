# -*- coding: utf-8 -*-
import time, random, math

class Item:
    def __init__(self, name, icon, block_type=0, is_block=False, is_food=False, food_value=0):
        self.name = name
        self.icon = icon
        self.block_type = block_type
        self.is_block = is_block
        self.is_food = is_food
        self.food_value = food_value

class Slot:
    def __init__(self):
        self.item = None
        self.count = 0
    def empty(self):
        return self.item is None or self.count <= 0
    def add(self, item, amount=1):
        if self.empty():
            take = min(amount, 64)
            self.item = item
            self.count = take
            return amount - take
        if self.item.name == item.name:
            space = 64 - self.count
            take = min(amount, space)
            self.count += take
            return amount - take
        return amount
    def take(self, amount=1):
        self.count -= amount
        if self.count <= 0:
            self.item = None
            self.count = 0

class DroppedItem:
    def __init__(self, x, y, item, count):
        self.x = x
        self.y = y
        self.item = item
        self.count = count
        self.spawn_time = time.time()
        self.bob_offset = random.uniform(0, math.pi * 2)
    def get_bob_y(self, current_time):
        return math.sin(current_time * 2 + self.bob_offset) * 3
    def is_expired(self, current_time, total_dropped):
        age = current_time - self.spawn_time
        limit = 300 if total_dropped > 150 else 1200
        return age > limit
