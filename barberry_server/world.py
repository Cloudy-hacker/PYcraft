# -*- coding: utf-8 -*-
import random, json

T_EMPTY=0; T_TREE=1; T_STONE=2; T_WALL=3; T_DEV=4; T_FOUND=5; T_BERRY=6; T_FAST_DEV=7; T_DOOR=8

class World:
    def __init__(self, size=100, seed=42):
        self.size = size; self.seed = seed
        self.tiles = {}; self.doors = {}
        self.generate()
    
    def generate(self):
        random.seed(self.seed)
        for ty in range(self.size):
            for tx in range(self.size):
                r = random.random()
                if r<0.08: self.tiles[(tx,ty)] = T_TREE
                elif r<0.11: self.tiles[(tx,ty)] = T_STONE
                elif r<0.12: self.tiles[(tx,ty)] = T_BERRY
        cx,cy = self.size//2, self.size//2
        for dy in range(-3,4):
            for dx in range(-3,4):
                self.tiles.pop((cx+dx,cy+dy), None)
        self.tiles[(cx-2,cy)] = T_DEV
        self.tiles[(cx+2,cy)] = T_DEV
    
    def get_tile(self, tx, ty):
        return self.tiles.get((tx,ty), T_EMPTY)
    
    def set_tile(self, tx, ty, block_type):
        if 0<=tx<self.size and 0<=ty<self.size:
            if block_type == T_EMPTY:
                self.tiles.pop((tx,ty), None)
            else:
                self.tiles[(tx,ty)] = block_type
    
    def get_spawn_point(self):
        cx,cy = self.size//2, self.size//2
        return (cx*32+16, cy*32+16)
    
    def to_dict(self):
        return {
            "size": self.size, "seed": self.seed,
            "tiles": {f"{k[0]},{k[1]}":v for k,v in self.tiles.items()},
            "doors": {f"{k[0]},{k[1]}":v for k,v in self.doors.items()}
        }
    
    @classmethod
    def from_dict(cls, data):
        w = cls(size=data["size"], seed=data["seed"])
        w.tiles = {}
        for k,v in data["tiles"].items():
            tx,ty = map(int,k.split(","))
            w.tiles[(tx,ty)] = v
        w.doors = {}
        for k,v in data.get("doors",{}).items():
            tx,ty = map(int,k.split(","))
            w.doors[(tx,ty)] = v
        return w
# -*- coding: utf-8 -*-
"""
Мир сервера: тайлы, двери, выброшенные предметы
"""

class World:
    def __init__(self, size=100):
        self.size = size
        self.tiles = {}
        self.doors = {}
        self.drops = []   # список словарей {id, x, y, item, count}
