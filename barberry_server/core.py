# -*- coding: utf-8 -*-
"""
Barberry Server 2.0 — ядро
+ сервер симулирует зомби, хранит дроп, рассылает время
"""

import asyncio
import time
import json
import os
import math
import random
from world import World
from player import Player
from save import SaveManager
from network import NetworkHandler
from protocol import encode_message

BANS_FILE = "bans.json"
WHITELIST_FILE = "whitelist.json"
WORLDS_DIR = "worlds"
PLAYERS_FILE = "players_data.json"

# номера блоков из constants.py клиента (для коллизий зомби)
SOLID_STONE = 2
SOLID_WALL = 3
BLOCK_DOOR = 7

MAX_ZOMBIES = 10
ZOMBIE_SPEED = 60
ZOMBIE_DAMAGE = 5


class BarberryServer:
    def __init__(self, config):
        self.config = config
        self.world = World(size=config.get("world_size", 100))
        self.world_name = "default"
        self.players = {}
        self.next_player_id = 1
        self.save_manager = SaveManager(worlds_dir=WORLDS_DIR)
        self.network_handler = NetworkHandler(self)
        self.running = False
        self.asyncio_server = None
        self.day_timer = 0
        self.save_timer = 0
        self.entity_timer = 0
        self.zspawn_timer = 0
        self.time_broadcast_timer = 0
        self.zombies = []
        self.next_zid = 1
        self.next_did = 1
        self.player_roles = {}
        self.muted_players = set()
        self.frozen_players = set()
        self.whitelist = set()
        self.banned_players = set()
        self.banned_ips = set()
        self.banned_hashes = set()
        self.players_data = {}
        self._load_bans()
        self._load_whitelist()
        self._load_players_data()
        self._load_world(self.config.get("default_world", "default"))
        ids = [d.get("id", 0) for d in self.world.drops]
        self.next_did = (max(ids) + 1) if ids else 1

    def _load_bans(self):
        if os.path.exists(BANS_FILE):
            try:
                with open(BANS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.banned_players = set(data.get("players", []))
                self.banned_ips = set(data.get("ips", []))
                self.banned_hashes = set(data.get("hashes", []))
            except Exception as e:
                print("[Core] Ошибка загрузки банов: {}".format(e))

    def _save_bans(self):
        try:
            data = {
                "players": list(self.banned_players),
                "ips": list(self.banned_ips),
                "hashes": list(self.banned_hashes)
            }
            with open(BANS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print("[Core] Ошибка сохранения банов: {}".format(e))

    def _load_whitelist(self):
        if os.path.exists(WHITELIST_FILE):
            try:
                with open(WHITELIST_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.whitelist = set(data.get("players", []))
            except Exception as e:
                print("[Core] Ошибка загрузки вайтлиста: {}".format(e))

    def _save_whitelist(self):
        try:
            data = {"players": list(self.whitelist)}
            with open(WHITELIST_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print("[Core] Ошибка сохранения вайтлиста: {}".format(e))

    def _load_players_data(self):
        if os.path.exists(PLAYERS_FILE):
            try:
                with open(PLAYERS_FILE, 'r', encoding='utf-8') as f:
                    self.players_data = json.load(f)
                print("[Core] Загружены данные {} игроков".format(len(self.players_data)))
            except Exception as e:
                print("[Core] Ошибка загрузки данных игроков: {}".format(e))
                self.players_data = {}

    def _save_players_data(self):
        try:
            with open(PLAYERS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.players_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print("[Core] Ошибка сохранения данных игроков: {}".format(e))

    def _load_world(self, world_name):
        self.world_name = world_name
        self.world = self.save_manager.load_world(world_name)
        print("[Core] Загружен мир: {}".format(world_name))

    def _save_world(self):
        self.save_manager.save_world(self.world, self.world_name)

    def get_world_list(self):
        worlds = []
        if os.path.exists(WORLDS_DIR):
            for f in os.listdir(WORLDS_DIR):
                if f.endswith(".json"):
                    worlds.append(f[:-5])
        return worlds

    def create_world(self, world_name):
        if world_name in self.get_world_list():
            return False, "Мир уже существует"
        new_world = World(size=self.config.get("world_size", 100))
        self.save_manager.save_world(new_world, world_name)
        return True, "Мир '{}' создан".format(world_name)

    def delete_world(self, world_name):
        filepath = os.path.join(WORLDS_DIR, "{}.json".format(world_name))
        if os.path.exists(filepath):
            os.remove(filepath)
            return True, "Мир '{}' удалён".format(world_name)
        return False, "Мир не найден"

    def check_integrity(self, client_hash):
        if not self.config.get("online", False):
            return True
        expected = self.config.get("client_hash", "")
        if not expected:
            return True
        return client_hash == expected

    def get_spawn_point(self):
        cx, cy = self.world.size // 2, self.world.size // 2
        return (cx * 32 + 16, cy * 32 + 16)

    # ---------- дроп ----------
    def add_drop(self, item, count, x, y):
        d = {"id": self.next_did, "x": x, "y": y, "item": item, "count": count}
        self.next_did += 1
        self.world.drops.append(d)
        return d

    def remove_drop(self, did):
        for d in list(self.world.drops):
            if d["id"] == did:
                self.world.drops.remove(d)
                return d
        return None

    # ---------- зомби ----------
    def _solid_at(self, x, y):
        tx = int(x) // 32
        ty = int(y) // 32
        t = self.world.tiles.get((tx, ty), 0)
        if t in (SOLID_STONE, SOLID_WALL):
            return True
        if t == BLOCK_DOOR and self.world.doors.get((tx, ty), True):
            return True
        return False

    def _nearest_player(self, x, y):
        best = None
        best_d = None
        for p in self.players.values():
            d = math.hypot(p.x - x, p.y - y)
            if best_d is None or d < best_d:
                best_d = d
                best = p
        return best

    def _update_zombies(self, dt):
        cycle = self.config["day_length"] + self.config["night_length"]
        frac = (self.day_timer / cycle) if cycle else 0
        # спавн ночью
        if frac >= 0.75 and self.players and len(self.zombies) < MAX_ZOMBIES:
            self.zspawn_timer += dt
            if self.zspawn_timer >= 1.0:
                self.zspawn_timer = 0
                p = random.choice(list(self.players.values()))
                angle = random.uniform(0, math.pi * 2)
                dist = random.uniform(400, 600)
                x = min(max(p.x + math.cos(angle) * dist, 32), self.world.size * 32 - 32)
                y = min(max(p.y + math.sin(angle) * dist, 32), self.world.size * 32 - 32)
                self.zombies.append({"id": self.next_zid, "x": x, "y": y, "hp": 10, "cd": 0.0})
                self.next_zid += 1
        # поведение
        for z in list(self.zombies):
            z["cd"] = max(0.0, z["cd"] - dt)
            target = self._nearest_player(z["x"], z["y"])
            if target:
                dx = target.x - z["x"]
                dy = target.y - z["y"]
                d = math.hypot(dx, dy)
                if d > 1:
                    nx = z["x"] + (dx / d) * ZOMBIE_SPEED * dt
                    if not self._solid_at(nx, z["y"]):
                        z["x"] = nx
                    ny = z["y"] + (dy / d) * ZOMBIE_SPEED * dt
                    if not self._solid_at(z["x"], ny):
                        z["y"] = ny
                if d < 30 and z["cd"] <= 0:
                    z["cd"] = 1.0
                    target.send({"type": "damage_player", "amount": ZOMBIE_DAMAGE})
            if frac < 0.625:
                z["hp"] -= dt * 1.0
                if z["hp"] <= 0:
                    self.zombies.remove(z)

    def _broadcast_zombies(self):
        self.broadcast({
            "type": "zombies_update",
            "zombies": [{"id": z["id"], "x": z["x"], "y": z["y"], "hp": z["hp"]} for z in self.zombies]
        })

    # ---------- игроки ----------
    def add_player(self, nickname, client_hash=None, writer=None, ip=None):
        if ip and ip in self.banned_ips:
            return None, "Ваш IP забанен"
        if client_hash and client_hash in self.banned_hashes:
            return None, "Ваш клиент (CID) забанен"
        if self.config.get("online", False):
            if not self.check_integrity(client_hash):
                return None, "Проверка неприкосновенности провалена"
        if nickname in self.banned_players:
            return None, "Вы забанены"
        if self.config.get("whitelist_enabled", False) and nickname not in self.whitelist:
            return None, "Вас нет в белом списке"
        if len(self.players) >= self.config.get("max_players", 10):
            return None, "Сервер заполнен"

        spawn_x, spawn_y = self.get_spawn_point()
        player = Player(self.next_player_id, nickname, spawn_x, spawn_y, writer)
        player.ip = ip
        player.client_hash = client_hash
        self.players[player.id] = player
        self.next_player_id += 1

        if nickname not in self.player_roles:
            self.player_roles[nickname] = "guest"
        player.role = self.player_roles.get(nickname, "guest")

        saved = self.players_data.get(nickname)
        if saved and "x" in saved and "y" in saved:
            player.x = saved["x"]
            player.y = saved["y"]
            print("[Core] {} восстановлен на ({:.0f}, {:.0f})".format(nickname, player.x, player.y))

        print("[Core] + {} (ID:{}, Role:{}, IP:{})".format(nickname, player.id, player.role, ip))
        return player, None

    def remove_player(self, player):
        if player.id in self.players:
            entry = self.players_data.setdefault(player.nickname, {})
            entry["x"] = player.x
            entry["y"] = player.y
            entry["role"] = player.role
            self._save_players_data()
            del self.players[player.id]
            print("[Core] - {} (сохранён на {:.0f}, {:.0f})".format(player.nickname, player.x, player.y))
            self.broadcast({"type": "player_leave", "player_id": player.id}, exclude=player)

    def set_role(self, nickname, role):
        if role in ["guest", "player", "op"]:
            self.player_roles[nickname] = role
            for p in self.players.values():
                if p.nickname == nickname:
                    p.role = role
                    p.send({"type": "role_update", "role": role})
            return True
        return False

    def broadcast(self, message, exclude=None):
        data = encode_message(message)
        for player in self.players.values():
            if player != exclude and player.writer:
                try:
                    player.writer.write(data)
                except:
                    pass

    def request_stop(self):
        print("[Core] Остановка сервера...")
        self.running = False
        self.broadcast({"type": "server_stop"})
        for p in list(self.players.values()):
            try:
                if p.writer:
                    p.writer.close()
            except:
                pass
        self.players.clear()
        self._save_world()
        self._save_bans()
        self._save_whitelist()
        self._save_players_data()
        if self.asyncio_server is not None:
            self.asyncio_server.close()
        print("[Core] Сервер остановлен, данные сохранены")

    def execute_console_command(self, cmd_str):
        if not cmd_str.startswith("/"):
            print("[Console] {}".format(cmd_str))
            return
        parts = cmd_str[1:].strip().split()
        if not parts:
            return
        cmd = parts[0].lower()
        args = parts[1:]

        if cmd == "stop":
            self.request_stop()
        elif cmd == "deop":
            if args:
                self.set_role(args[0], "player")
        elif cmd == "op":
            if args:
                self.set_role(args[0], "op")
        elif cmd in ["player", "pl"]:
            if args:
                self.set_role(args[0], "player")
        elif cmd == "guest":
            if args:
                self.set_role(args[0], "guest")
        elif cmd == "kick":
            if args:
                for p in list(self.players.values()):
                    if p.nickname == args[0]:
                        p.send({"type": "kick", "message": "Вы были кикнуты: {}".format(" ".join(args[1:]) or "Без причины")})
                        try:
                            p.writer.close()
                        except:
                            pass
                        self.remove_player(p)
                        break
        elif cmd == "ban":
            if args:
                target = args[0]
                self.banned_players.add(target)
                for p in list(self.players.values()):
                    if p.nickname == target:
                        if getattr(p, 'ip', None):
                            self.banned_ips.add(p.ip)
                        if getattr(p, 'client_hash', None):
                            self.banned_hashes.add(p.client_hash)
                        p.send({"type": "kick", "message": "Вы забанены: {}".format(" ".join(args[1:]) or "Без причины")})
                        try:
                            p.writer.close()
                        except:
                            pass
                        self.remove_player(p)
                        break
                self._save_bans()
        elif cmd == "unban":
            if args:
                self.banned_players.discard(args[0])
                self._save_bans()
        elif cmd == "unbanall":
            self.banned_players.clear()
            self.banned_ips.clear()
            self.banned_hashes.clear()
            self._save_bans()
        elif cmd == "banlist":
            all_bans = list(self.banned_players) + list(self.banned_ips) + list(self.banned_hashes)
            for i, ban in enumerate(all_bans, 1):
                print("[Console] #{}: {}".format(i, ban))
        elif cmd == "save":
            self._save_world()
            print("[Console] Мир сохранён")
        elif cmd == "list":
            print("[Console] Игроки ({}):".format(len(self.players)))
            for p in self.players.values():
                print("  - {} (ID:{}, Role:{}, IP:{})".format(p.nickname, p.id, p.role, getattr(p, 'ip', '?')))
        elif cmd == "say":
            self.broadcast({"type": "chat", "text": "[Сервер] {}".format(" ".join(args)), "color": [255, 255, 100]})
        elif cmd == "help":
            print("[Console] Команды: /op /deop /player /guest /kick /ban /unban /unbanall /banlist /save /stop /list /say /help")
        else:
            print("[Console] Неизвестная команда: /{}".format(cmd))

    async def game_loop(self):
        tick_rate = self.config.get("tick_rate", 20)
        tick_time = 1.0 / tick_rate
        auto_save_timer = 0
        while self.running:
            start = time.time()
            self.day_timer += tick_time
            cycle = self.config["day_length"] + self.config["night_length"]
            if self.day_timer >= cycle:
                self.day_timer = 0
            self.save_timer += tick_time
            if self.save_timer >= self.config["save_interval"]:
                self.save_timer = 0
                self._save_world()
            auto_save_timer += tick_time
            if auto_save_timer >= 60:
                auto_save_timer = 0
                self._save_world()
                print("[Core] Автосохранение мира")
            # симуляция сущностей 10 раз в секунду
            self.entity_timer += tick_time
            if self.entity_timer >= 0.1:
                self.entity_timer = 0
                self._update_zombies(0.1)
                self._broadcast_zombies()
            # время всем клиентам раз в секунду
            self.time_broadcast_timer += tick_time
            if self.time_broadcast_timer >= 1.0:
                self.time_broadcast_timer = 0
                self.broadcast({"type": "time_update", "day_timer": self.day_timer})
            elapsed = time.time() - start
            if elapsed < tick_time:
                await asyncio.sleep(tick_time - elapsed)

    async def start(self):
        self.running = True
        print("=" * 50)
        print("Название: {}".format(self.config['server_name']))
        print("Адрес: {}:{}".format(self.config['host'], self.config['port']))
        print("Текущий мир: {}".format(self.world_name))
        print("Online mode: {}".format(self.config.get('online', False)))
        print("Max players: {}".format(self.config.get('max_players', 10)))
        print("=" * 50)
        self.asyncio_server = await asyncio.start_server(
            self.network_handler.handle_client,
            self.config['host'],
            self.config['port']
        )
        asyncio.create_task(self.game_loop())
        print("[Core] Сервер запущен и готов к подключениям")
        print("[Core] Введите команду (например: /help)")
        async with self.asyncio_server:
            await self.asyncio_server.serve_forever()
