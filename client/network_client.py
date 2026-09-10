# -*- coding: utf-8 -*-
"""
Сетевая логика клиента: чат, команды, двери, состояние, зомби, дроп, время
"""
import logging
from constants import *
from entities import Zombie
from items import DroppedItem

logger = logging.getLogger(__name__)

SERVER_CMDS = set(["op", "kick", "ban", "unban", "save", "stop",
                   "mute", "unmute", "guest", "player", "pl", "broadcast", "bc"])


class NetworkClientLogic:
    def _say(self, text):
        if self.game_mode == "client" and self.client.connected:
            self.client.send({"type": "chat", "text": text})
        else:
            self.add_chat_message("<{}> {}".format(self.nickname, text), (200, 200, 200))

    def _command(self, text):
        parts = text[1:].strip().split()
        cmd = parts[0].lower() if parts else ""
        if self.game_mode == "client" and self.client.connected and cmd in SERVER_CMDS:
            self.client.send({"type": "chat", "text": text})
        else:
            self.command_manager.execute(text, self.role)

    def _send_player_state(self):
        if self.client.connected:
            self.client.send({
                "type": "player_state",
                "hp": self.hp,
                "hunger": self.hunger,
                "hotbar": [(s.item.name if s.item else None, s.count) for s in self.hotbar],
                "inventory": [(s.item.name if s.item else None, s.count) for s in self.inventory]
            })

    def _send_door_update(self, tx, ty, open_state):
        if self.client.connected:
            self.client.send({"type": "door_update", "tx": tx, "ty": ty, "open": open_state})

    def _send_drop_item(self, item_name, count, x, y):
        if self.client.connected:
            self.client.send({"type": "drop_item", "item": item_name, "count": count, "x": x, "y": y})

    def _send_pickup(self, drop_id):
        if self.client.connected:
            self.client.send({"type": "pickup_drop", "id": drop_id})

    def _send_attack(self, zid, damage):
        if self.client.connected:
            self.client.send({"type": "attack_zombie", "id": zid, "damage": damage})

    def _send_death_drop(self, items, x, y):
        if self.client.connected:
            self.client.send({"type": "death_drop", "items": items, "x": x, "y": y})

    def _add_remote_drop(self, d):
        name = d.get("item")
        if name not in self.ALL_ITEMS:
            return
        drop = DroppedItem(d.get("x", 0), d.get("y", 0), self.ALL_ITEMS[name], d.get("count", 1))
        drop.drop_id = d.get("id")
        self.dropped_items.append(drop)

    def _process_network(self):
        for msg in self.client.get_messages():
            t = msg.get("type")
            if t == "welcome":
                self.player_id = msg.get("player_id")
                self.role = msg.get("role", "guest")
                self.was_connected = True
                spawn_x = msg.get("spawn_x")
                spawn_y = msg.get("spawn_y")
                if spawn_x is not None and spawn_y is not None:
                    self.px = spawn_x
                    self.py = spawn_y
                    logger.info("Спавн на ({:.0f}, {:.0f})".format(self.px, self.py))
                else:
                    cx, cy = MAP_W // 2, MAP_H // 2
                    self.px = cx * TILE + TILE // 2
                    self.py = cy * TILE + TILE // 2
            elif t == "world_state":
                self.world = {}
                for k, v in msg.get("tiles", {}).items():
                    tx, ty = map(int, k.split(","))
                    self.world[(tx, ty)] = v
                self.doors = {}
                for k, v in msg.get("doors", {}).items():
                    tx, ty = map(int, k.split(","))
                    self.doors[(tx, ty)] = v
                self._generate_grass_only()
                logger.info("Мир получен: {} тайлов, {} дверей".format(len(self.world), len(self.doors)))
            elif t == "player_state":
                self.hp = msg.get("hp", 100)
                self.hunger = msg.get("hunger", 100)
                for i, pair in enumerate(msg.get("hotbar", [])):
                    if i < len(self.hotbar):
                        name, count = pair[0], pair[1]
                        if name and name in self.ALL_ITEMS:
                            self.hotbar[i].item = self.ALL_ITEMS[name]
                            self.hotbar[i].count = count
                        else:
                            self.hotbar[i].item = None
                            self.hotbar[i].count = 0
                for i, pair in enumerate(msg.get("inventory", [])):
                    if i < len(self.inventory):
                        name, count = pair[0], pair[1]
                        if name and name in self.ALL_ITEMS:
                            self.inventory[i].item = self.ALL_ITEMS[name]
                            self.inventory[i].count = count
                        else:
                            self.inventory[i].item = None
                            self.inventory[i].count = 0
                logger.info("Инвентарь и состояние восстановлены с сервера")
            elif t == "players_init":
                self.other_players = {}
                for p in msg.get("players", []):
                    self.other_players[p.get("id")] = {
                        "x": p.get("x", 0), "y": p.get("y", 0), "name": p.get("nickname", "")
                    }
            elif t == "player_join":
                p = msg.get("player", {})
                self.other_players[p.get("id")] = {
                    "x": p.get("x", 0), "y": p.get("y", 0), "name": p.get("nickname", "")
                }
            elif t == "player_leave":
                self.other_players.pop(msg.get("player_id"), None)
            elif t == "player_update":
                pid = msg.get("id")
                if pid in self.other_players:
                    self.other_players[pid]["x"] = msg.get("x", 0)
                    self.other_players[pid]["y"] = msg.get("y", 0)
            elif t == "block_update":
                tx, ty = msg.get("tx"), msg.get("ty")
                b = msg.get("block", 0)
                if b == 0:
                    self.world.pop((tx, ty), None)
                else:
                    self.world[(tx, ty)] = b
            elif t == "door_update":
                tx, ty = msg.get("tx"), msg.get("ty")
                self.doors[(tx, ty)] = bool(msg.get("open"))
            elif t in ("zombies_init", "zombies_update"):
                self.zombies = []
                for z in msg.get("zombies", []):
                    zz = Zombie(z.get("x", 0), z.get("y", 0))
                    zz.zid = z.get("id")
                    zz.hp = z.get("hp", 10)
                    self.zombies.append(zz)
            elif t == "drops_init":
                self.dropped_items = []
                for d in msg.get("drops", []):
                    self._add_remote_drop(d)
            elif t == "drop_add":
                self._add_remote_drop(msg)
            elif t == "drop_remove":
                did = msg.get("id")
                self.dropped_items = [d for d in self.dropped_items
                                      if getattr(d, "drop_id", None) != did]
            elif t == "pickup_ok":
                name = msg.get("item")
                if name in self.ALL_ITEMS:
                    self._pickup(self.ALL_ITEMS[name], msg.get("count", 1))
            elif t == "damage_player":
                self.hp -= msg.get("amount", 0)
            elif t == "time_update":
                self.day_timer = msg.get("day_timer", 0)
            elif t == "chat":
                self.add_chat_message(msg.get("text", ""), tuple(msg.get("color", C_TEXT)))
            elif t == "server_stop":
                self.was_connected = False
                self.kick_message = "Сервер выключился"
                self.kick_screen = True
                self.client.disconnect()
            elif t == "kick":
                self.kick_message = msg.get("message", "Вы были отключены")
                self.kick_screen = True
            elif t == "role_update":
                self.role = msg.get("role", "guest")

    def _send_position(self):
        if self.client.connected and self.player_id:
            self.client.send({"type": "move", "x": self.px, "y": self.py})

    def _send_block_update(self, tx, ty, block):
        if self.client.connected:
            self.client.send({"type": "block_update", "tx": tx, "ty": ty, "block": block})
