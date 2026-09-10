# -*- coding: utf-8 -*-
"""
Логика мира: генерация, блоки, двери, сохранения
dev-кубы (T_DEV, T_FAST_DEV) — только для роли op
"""
import os, json, random, math, logging
from constants import *
from items import Item, DroppedItem
from entities import Zombie

logger = logging.getLogger(__name__)


class WorldLogic:
    def _generate_world(self):
        random.seed(42)
        self.grass = {}
        self.world = {}
        self.doors = {}
        self.dropped_items = []
        self.zombies = []
        for ty in range(MAP_H):
            for tx in range(MAP_W):
                r = random.random()
                if r < 0.3:
                    self.grass[(tx, ty)] = C_BG_DARK
                elif r < 0.5:
                    self.grass[(tx, ty)] = C_BG_LIGHT
                else:
                    self.grass[(tx, ty)] = C_BG
                r = random.random()
                if r < 0.08:
                    self.world[(tx, ty)] = T_TREE
                elif r < 0.11:
                    self.world[(tx, ty)] = T_STONE
                elif r < 0.12:
                    self.world[(tx, ty)] = T_BERRY
        cx, cy = MAP_W // 2, MAP_H // 2
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                self.world.pop((cx + dx, cy + dy), None)
        self.world[(cx - 2, cy)] = T_DEV
        self.world[(cx + 2, cy)] = T_DEV
        self.px = cx * TILE + TILE // 2
        self.py = cy * TILE + TILE // 2

    def _generate_grass_only(self):
        random.seed(42)
        self.grass = {}
        for ty in range(MAP_H):
            for tx in range(MAP_W):
                r = random.random()
                if r < 0.3:
                    self.grass[(tx, ty)] = C_BG_DARK
                elif r < 0.5:
                    self.grass[(tx, ty)] = C_BG_LIGHT
                else:
                    self.grass[(tx, ty)] = C_BG

    def _save_world(self):
        try:
            world_data = {
                "tiles": {"{},{}".format(k[0], k[1]): v for k, v in self.world.items()},
                "doors": {"{},{}".format(k[0], k[1]): v for k, v in self.doors.items()},
                "grass": {"{},{}".format(k[0], k[1]): list(v) for k, v in self.grass.items()}
            }
            with open("world_save.json", 'w', encoding='utf-8') as f:
                json.dump(world_data, f, ensure_ascii=False)
            player_data = {
                "px": self.px, "py": self.py,
                "hp": self.hp, "hunger": self.hunger,
                "hotbar": [(s.item.name if s.item else None, s.count) for s in self.hotbar],
                "inventory": [(s.item.name if s.item else None, s.count) for s in self.inventory],
                "sel": self.sel,
                "day_timer": self.day_timer
            }
            with open("player_save.json", 'w', encoding='utf-8') as f:
                json.dump(player_data, f, ensure_ascii=False)
            drops_data = [
                {"x": d.x, "y": d.y, "item": d.item.name, "count": d.count}
                for d in self.dropped_items
            ]
            with open("drops_save.json", 'w', encoding='utf-8') as f:
                json.dump(drops_data, f, ensure_ascii=False)
            logger.info("Мир сохранён!")
        except Exception as e:
            logger.error("Ошибка сохранения: {}".format(e))

    def _load_world(self):
        try:
            if os.path.exists("world_save.json"):
                with open("world_save.json", 'r', encoding='utf-8') as f:
                    world_data = json.load(f)
                self.world = {}
                for k, v in world_data.get("tiles", {}).items():
                    tx, ty = map(int, k.split(","))
                    self.world[(tx, ty)] = v
                self.doors = {}
                for k, v in world_data.get("doors", {}).items():
                    tx, ty = map(int, k.split(","))
                    self.doors[(tx, ty)] = v
                self.grass = {}
                for k, v in world_data.get("grass", {}).items():
                    tx, ty = map(int, k.split(","))
                    self.grass[(tx, ty)] = tuple(v)
                logger.info("Мир загружен! Тайлов: {}, травы: {}".format(
                    len(self.world), len(self.grass)))
            else:
                logger.info("Сохранение не найдено")
                self._generate_world()
            if os.path.exists("player_save.json"):
                with open("player_save.json", 'r', encoding='utf-8') as f:
                    player_data = json.load(f)
                self.px = player_data.get("px", self.px)
                self.py = player_data.get("py", self.py)
                self.hp = player_data.get("hp", 100)
                self.hunger = player_data.get("hunger", 100)
                self.sel = player_data.get("sel", 0)
                self.day_timer = player_data.get("day_timer", 0)
                for i, (item_name, count) in enumerate(player_data.get("hotbar", [])):
                    if i < len(self.hotbar) and item_name and item_name in self.ALL_ITEMS:
                        self.hotbar[i].item = self.ALL_ITEMS[item_name]
                        self.hotbar[i].count = count
                for i, (item_name, count) in enumerate(player_data.get("inventory", [])):
                    if i < len(self.inventory) and item_name and item_name in self.ALL_ITEMS:
                        self.inventory[i].item = self.ALL_ITEMS[item_name]
                        self.inventory[i].count = count
                logger.info("Игрок загружен!")
            if os.path.exists("drops_save.json"):
                with open("drops_save.json", 'r', encoding='utf-8') as f:
                    drops_data = json.load(f)
                self.dropped_items = []
                for d in drops_data:
                    if d["item"] in self.ALL_ITEMS:
                        item = self.ALL_ITEMS[d["item"]]
                        self.dropped_items.append(DroppedItem(d["x"], d["y"], item, d["count"]))
                logger.info("Загружено {} выпавших предметов".format(len(self.dropped_items)))
        except Exception as e:
            logger.error("Ошибка загрузки: {}".format(e))
            self._generate_world()

    def _tile_under(self, pos):
        wx = pos[0] + self.cam_x
        wy = pos[1] + self.cam_y
        return int(wx // TILE), int(wy // TILE)

    def mine(self, pos):
        if self.drone_mode:
            return
        if not self._check_distance(pos):
            return
        tx, ty = self._tile_under(pos)
        key = (tx, ty)
        block = self.world.get(key, T_EMPTY)
        if block in (T_DEV, T_FAST_DEV) and self.role != "op":
            self.add_chat_message("Dev-кубы может брать только op!", (255, 100, 100))
            return
        if block == T_TREE:
            self.world.pop(key, None)
            self._pickup(self.ALL_ITEMS["Дерево"], 1)
            self._send_block_update(tx, ty, 0)
        elif block == T_STONE:
            self.world.pop(key, None)
            self._pickup(self.ALL_ITEMS["Камень"], 1)
            self._send_block_update(tx, ty, 0)
        elif block == T_WALL:
            self.world.pop(key, None)
            self._pickup(self.ALL_ITEMS["Стена"], 1)
            self._send_block_update(tx, ty, 0)
        elif block == T_FOUND:
            self.world.pop(key, None)
            self._pickup(self.ALL_ITEMS["Фундамент"], 1)
            self._send_block_update(tx, ty, 0)
        elif block == T_BERRY:
            self.world.pop(key, None)
            self._pickup(self.ALL_ITEMS["Ягоды"], 1)
            self._send_block_update(tx, ty, 0)
        elif block == T_FAST_DEV:
            self.world.pop(key, None)
            fast_dev_item = Item("Быстрый dev", self.sprites.fast_dev, T_FAST_DEV, True)
            self._pickup(fast_dev_item, 1)
        elif block == T_DEV:
            self.world.pop(key, None)
        elif block == T_DOOR:
            self.world.pop(key, None)
            self.doors.pop(key, None)
            self._pickup(self.ALL_ITEMS["Дверь"], 1)
            self._send_block_update(tx, ty, 0)

    def place(self, pos):
        if self.drone_mode:
            return
        if not self._check_distance(pos):
            return
        slot = self.hotbar[self.sel]
        if slot.empty() or not slot.item.is_block:
            return
        if slot.item.block_type in (T_DEV, T_FAST_DEV) and self.role != "op":
            return
        tx, ty = self._tile_under(pos)
        key = (tx, ty)
        if tx < 0 or tx >= MAP_W or ty < 0 or ty >= MAP_H:
            return
        if key in self.world:
            return
        ptx = int(self.px) // TILE
        pty = int(self.py) // TILE
        if tx == ptx and ty == pty:
            return
        block_type = slot.item.block_type
        self.world[key] = block_type
        if block_type == T_DOOR:
            self.doors[key] = True
        slot.take(1)
        self._send_block_update(tx, ty, block_type)

    def _interact_door(self, pos):
        tx, ty = self._tile_under(pos)
        key = (tx, ty)
        if self.world.get(key) == T_DOOR:
            self.doors[key] = not self.doors.get(key, True)
            self._send_door_update(tx, ty, self.doors[key])
            return True
        return False

    def _interact_dev(self, pos):
        if self.role != "op":
            return False
        tx, ty = self._tile_under(pos)
        key = (tx, ty)
        block = self.world.get(key, T_EMPTY)
        if block in (T_DEV, T_FAST_DEV):
            self.dev_menu.open_menu()
            return True
        return False

    def spawn_zombie_nearby(self):
        angle = random.uniform(0, math.pi * 2)
        dist = 10 * TILE
        x = self.px + math.cos(angle) * dist
        y = self.py + math.sin(angle) * dist
        x = max(TILE, min(MAP_W * TILE - TILE, x))
        y = max(TILE, min(MAP_H * TILE - TILE, y))
        self.zombies.append(Zombie(x, y))
