# -*- coding: utf-8 -*-
"""
Barberry Server 2.0 — сетевой обработчик
+ атака по зомби, дроп, пикап, смерть-дроп, dev-блоки только для op
"""

import asyncio
import math
import random
from protocol import decode_message, encode_message

# номера dev-блоков из constants.py клиента: T_DEV=4, T_FAST_DEV=5
DEV_IDS = (4, 5)

class NetworkHandler:
    def __init__(self, server):
        self.server = server

    async def handle_client(self, reader, writer):
        addr = writer.get_extra_info('peername')
        print("[Network] + {}".format(addr))
        player = None
        try:
            while self.server.running:
                line = await reader.readline()
                if not line:
                    break
                line = line.strip()
                if not line:
                    continue
                data = decode_message(line)
                player = await self.process(data, player, writer)
        except asyncio.IncompleteReadError:
            print("[Network] Клиент {} оборвал поток".format(addr))
        except ConnectionResetError:
            print("[Network] Клиент {} сбросил соединение".format(addr))
        except Exception as e:
            print("[Network] Error: {} ({})".format(e, addr))
        finally:
            if player:
                self.server.remove_player(player)
            try:
                writer.close()
            except Exception:
                pass
            print("[Network] - {}".format(addr))

    async def process(self, data, player, writer):
        t = data.get("type")
        if t != "move":
            print("[Network] <- '{}' от {}".format(t, player.nickname if player else "?"))

        if t == "connect":
            nickname = data.get("nickname", "Player")
            client_hash = data.get("client_hash")
            requested_world = data.get("world", "default")
            ip = writer.get_extra_info('peername')[0] if writer else None

            for old in list(self.server.players.values()):
                if old.nickname == nickname:
                    print("[Network] убираю старую сессию игрока {}".format(nickname))
                    self.server.remove_player(old)
                    try:
                        if old.writer:
                            old.writer.close()
                    except Exception:
                        pass

            if requested_world not in self.server.get_world_list():
                self.server.create_world(requested_world)

            p, err = self.server.add_player(nickname, client_hash, writer, ip)
            if p is None:
                writer.write(encode_message({"type": "kick", "message": err}))
                await writer.drain()
                writer.close()
                return None
            player = p
            player.writer = writer

            writer.write(encode_message({
                "type": "welcome",
                "player_id": player.id,
                "role": player.role,
                "world": requested_world,
                "spawn_x": player.x,
                "spawn_y": player.y
            }))
            writer.write(encode_message({
                "type": "world_state",
                "tiles": {"{},{}".format(k[0], k[1]): v for k, v in self.server.world.tiles.items()},
                "doors": {"{},{}".format(k[0], k[1]): v for k, v in self.server.world.doors.items()}
            }))
            writer.write(encode_message({
                "type": "time_update",
                "day_timer": self.server.day_timer
            }))
            others = [pl.to_dict() for pl in self.server.players.values() if pl != player]
            writer.write(encode_message({"type": "players_init", "players": others}))
            writer.write(encode_message({"type": "drops_init", "drops": self.server.world.drops}))
            writer.write(encode_message({
                "type": "zombies_init",
                "zombies": [{"id": z["id"], "x": z["x"], "y": z["y"], "hp": z["hp"]} for z in self.server.zombies]
            }))
            saved = self.server.players_data.get(nickname)
            if saved:
                writer.write(encode_message({
                    "type": "player_state",
                    "hp": saved.get("hp", 100),
                    "hunger": saved.get("hunger", 100),
                    "hotbar": saved.get("hotbar", []),
                    "inventory": saved.get("inventory", [])
                }))
            self.server.broadcast({
                "type": "player_join",
                "player": player.to_dict()
            }, exclude=player)
            await writer.drain()
            print("[Network] {} подключился на ({:.0f}, {:.0f}), игроков: {}".format(
                nickname, player.x, player.y, len(self.server.players)))

        elif t == "move" and player:
            player.update_position(data["x"], data["y"])
            self.server.broadcast({
                "type": "player_update",
                "id": player.id,
                "x": player.x,
                "y": player.y
            }, exclude=player)

        elif t == "block_update" and player:
            tx = data.get("tx")
            ty = data.get("ty")
            block = data.get("block", 0)
            if tx is not None and ty is not None:
                old = self.server.world.tiles.get((tx, ty), 0)
                if (old in DEV_IDS or block in DEV_IDS) and player.role != "op":
                    print("[Network] {} не op — dev-блок запрещён".format(player.nickname))
                    return player
                if block == 0:
                    self.server.world.tiles.pop((tx, ty), None)
                else:
                    self.server.world.tiles[(tx, ty)] = block
                self.server.broadcast(data, exclude=player)
                print("[Network] {} изменил блок ({}, {}) на {}".format(
                    player.nickname, tx, ty, block))

        elif t == "door_update" and player:
            tx = data.get("tx")
            ty = data.get("ty")
            open_state = bool(data.get("open"))
            if tx is not None and ty is not None:
                self.server.world.doors[(tx, ty)] = open_state
                self.server.broadcast(data, exclude=player)
                print("[Network] {} {} дверь ({}, {})".format(
                    player.nickname, "Закрыл" if open_state else "Открыл", tx, ty))

        elif t == "attack_zombie" and player:
            zid = data.get("id")
            dmg = data.get("damage", 1)
            for z in list(self.server.zombies):
                if z["id"] == zid:
                    d = math.hypot(z["x"] - player.x, z["y"] - player.y)
                    if d <= 120:
                        z["hp"] -= dmg
                        print("[Network] {} бьёт зомби {} на {} (hp: {})".format(
                            player.nickname, zid, dmg, z["hp"]))
                        if z["hp"] <= 0:
                            self.server.zombies.remove(z)
                            self.server._broadcast_zombies()
                    break

        elif t == "drop_item" and player:
            d = self.server.add_drop(
                data.get("item"), data.get("count", 1),
                data.get("x", player.x), data.get("y", player.y))
            self.server.broadcast({
                "type": "drop_add", "id": d["id"], "x": d["x"], "y": d["y"],
                "item": d["item"], "count": d["count"]})

        elif t == "pickup_drop" and player:
            did = data.get("id")
            target = None
            for d in self.server.world.drops:
                if d["id"] == did:
                    target = d
                    break
            if target:
                dist = math.hypot(target["x"] - player.x, target["y"] - player.y)
                if dist <= 60:
                    self.server.remove_drop(did)
                    self.server.broadcast({"type": "drop_remove", "id": did})
                    player.send({"type": "pickup_ok", "item": target["item"], "count": target["count"]})

        elif t == "death_drop" and player:
            x = data.get("x", player.x)
            y = data.get("y", player.y)
            for pair in data.get("items", []):
                name = pair[0]
                count = pair[1]
                dx = x + random.uniform(-40, 40)
                dy = y + random.uniform(-40, 40)
                d = self.server.add_drop(name, count, dx, dy)
                self.server.broadcast({
                    "type": "drop_add", "id": d["id"], "x": d["x"], "y": d["y"],
                    "item": d["item"], "count": d["count"]})
            print("[Network] {} умер, вещей выброшено: {}".format(player.nickname, len(data.get("items", []))))

        elif t == "player_state" and player:
            entry = self.server.players_data.setdefault(player.nickname, {})
            entry["x"] = player.x
            entry["y"] = player.y
            entry["role"] = player.role
            entry["hp"] = data.get("hp", 100)
            entry["hunger"] = data.get("hunger", 100)
            entry["hotbar"] = data.get("hotbar", [])
            entry["inventory"] = data.get("inventory", [])
            self.server._save_players_data()
            print("[Network] состояние игрока {} сохранено".format(player.nickname))

        elif t == "chat" and player:
            if player.nickname in self.server.muted_players:
                player.send({"type": "chat", "text": "Вы замучены!", "color": [255, 100, 100]})
                return player
            text = data.get("text", "")
            if text.startswith("/"):
                self._handle_command(player, text)
            else:
                self.server.broadcast({
                    "type": "chat",
                    "text": "<{}> {}".format(player.nickname, text),
                    "color": [200, 200, 200]
                })

        elif t == "disconnect":
            print("[Network] игрок {} вышел корректно (esc/закрытие)".format(
                player.nickname if player else "?"))
            writer.close()

        elif t == "command" and player and player.role == "op":
            self._handle_command(player, "/" + data.get("cmd", "") + " " + " ".join(data.get("args", [])))

        return player

    def _handle_command(self, player, cmd_str):
        parts = cmd_str[1:].strip().split()
        if not parts:
            return
        cmd = parts[0].lower()
        args = parts[1:]
        if cmd == "op" and args:
            self.server.set_role(args[0], "op")
        elif cmd == "kick" and args:
            for p in list(self.server.players.values()):
                if p.nickname == args[0]:
                    p.send({"type": "kick", "message": "Вы были кикнуты: {}".format(" ".join(args[1:]) or "Без причины")})
                    try:
                        p.writer.close()
                    except:
                        pass
                    self.server.remove_player(p)
                    self.server.broadcast({"type": "chat", "text": "{} кикнут".format(args[0]), "color": [255, 100, 100]})
                    break
        elif cmd == "ban" and args:
            target = args[0]
            reason = " ".join(args[1:]) or "Без причины"
            self.server.banned_players.add(target)
            for p in list(self.server.players.values()):
                if p.nickname == target:
                    if getattr(p, 'ip', None):
                        self.server.banned_ips.add(p.ip)
                    if getattr(p, 'client_hash', None):
                        self.server.banned_hashes.add(p.client_hash)
                    p.send({"type": "kick", "message": "Вы забанены: {}".format(reason)})
                    try:
                        p.writer.close()
                    except:
                        pass
                    self.server.remove_player(p)
                    break
            self.server._save_bans()
            self.server.broadcast({"type": "chat", "text": "{} забанен: {}".format(target, reason), "color": [255, 100, 100]})
        elif cmd == "unban" and args:
            self.server.banned_players.discard(args[0])
            self.server._save_bans()
            self.server.broadcast({"type": "chat", "text": "{} разбанен".format(args[0]), "color": [100, 255, 100]})
        elif cmd == "save":
            self.server._save_world()
            self.server.broadcast({"type": "chat", "text": "Мир сохранён!", "color": [100, 255, 100]})
        elif cmd == "stop":
            self.server.request_stop()
        elif cmd in ["broadcast", "bc"] and args:
            msg = " ".join(args)
            self.server.broadcast({"type": "chat", "text": "[ОБЪЯВЛЕНИЕ] {}".format(msg), "color": [255, 255, 0]})
        elif cmd == "mute" and args:
            self.server.muted_players.add(args[0])
            self.server.broadcast({"type": "chat", "text": "{} замучен".format(args[0]), "color": [255, 200, 100]})
        elif cmd == "unmute" and args:
            self.server.muted_players.discard(args[0])
            self.server.broadcast({"type": "chat", "text": "{} размучен".format(args[0]), "color": [100, 255, 100]})
        elif cmd == "guest" and args:
            self.server.set_role(args[0], "guest")
            self.server.broadcast({"type": "chat", "text": "{} теперь гость".format(args[0]), "color": [200, 200, 200]})
        elif cmd in ["player", "pl"] and args:
            self.server.set_role(args[0], "player")
            self.server.broadcast({"type": "chat", "text": "{} теперь обычный игрок".format(args[0]), "color": [100, 255, 100]})
