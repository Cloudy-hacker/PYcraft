# -*- coding: utf-8 -*-
import pygame, sys, threading, random, math
from constants import *
from items import Item
from sprites import Sprites
from network import discover_servers
from entities import Zombie

class MainMenu:
    def __init__(self, game):
        self.game = game
        self.nickname = "Player"
        self.input_active = False
        self.menu_state = "main"
        self.buttons = {}
        self.ip_input = "127.0.0.1"
        self.ip_input_active = False
        self.discovered_servers = []
        self.status_message = ""
        self.status_timer = 0
    
    def draw(self):
        self.game.screen.fill(C_MENU_BG)
        if self.menu_state == "main": self._draw_main()
        elif self.menu_state == "multiplayer": self._draw_multi()
        elif self.menu_state == "join": self._draw_join()
        if self.status_timer > 0:
            self.status_timer -= 1/30
            s = self.game.font.render(self.status_message, True, (255,200,100))
            self.game.screen.blit(s, (W//2-s.get_width()//2, H-50))
        pygame.display.flip()
    
    def _draw_main(self):
        t = self.game.font_big.render("PYcraft 2.0", True, C_TEXT)
        self.game.screen.blit(t, (W//2-t.get_width()//2, 80))
        sub = self.game.font.render("Barberry Client", True, (150,150,150))
        self.game.screen.blit(sub, (W//2-sub.get_width()//2, 110))
        nick_label = self.game.font.render("Никнейм:", True, C_TEXT)
        self.game.screen.blit(nick_label, (W//2-200, 160))
        nick_box = pygame.Rect(W//2-100, 160, 200, 30)
        pygame.draw.rect(self.game.screen, C_SLOT, nick_box)
        if self.input_active:
            pygame.draw.rect(self.game.screen, C_SEL, nick_box, 2)
        self.game.screen.blit(self.game.font.render(self.nickname, True, C_TEXT), (nick_box.x+5, nick_box.y+5))
        single = pygame.Rect(W//2-120, 230, 240, 45)
        multi = pygame.Rect(W//2-120, 290, 240, 45)
        quit_btn = pygame.Rect(W//2-120, 350, 240, 45)
        self._btn(single, "Одиночная игра")
        self._btn(multi, "Мультиплеер")
        self._btn(quit_btn, "Выход")
        self.buttons = {"single":single,"multi":multi,"quit":quit_btn,"nick":nick_box}
    
    def _draw_multi(self):
        t = self.game.font_big.render("Мультиплеер", True, C_TEXT)
        self.game.screen.blit(t, (W//2-t.get_width()//2, 60))
        create = pygame.Rect(W//2-120, 130, 240, 45)
        join = pygame.Rect(W//2-120, 190, 240, 45)
        back = pygame.Rect(W//2-120, 450, 240, 45)
        self._btn(create, "Создать мир (хост)")
        self._btn(join, "Подключиться")
        self._btn(back, "Назад")
        lt = self.game.font.render("Серверы в локальной сети:", True, C_TEXT)
        self.game.screen.blit(lt, (W//2-120, 260))
        if not self.discovered_servers:
            ns = self.game.font_small.render("Поиск...", True, (150,150,150))
            self.game.screen.blit(ns, (W//2-120, 290))
        else:
            for i,srv in enumerate(self.discovered_servers[:5]):
                st = self.game.font.render(srv['info'], True, C_TEXT)
                ip = self.game.font_small.render(srv['ip'], True, (150,150,150))
                y = 290+i*35
                self.game.screen.blit(st, (W//2-120, y))
                self.game.screen.blit(ip, (W//2-120, y+18))
        self.buttons = {"create":create,"join":join,"back":back}
    
    def _draw_join(self):
        t = self.game.font_big.render("Подключиться", True, C_TEXT)
        self.game.screen.blit(t, (W//2-t.get_width()//2, 60))
        ip_label = self.game.font.render("IP сервера:", True, C_TEXT)
        self.game.screen.blit(ip_label, (W//2-200, 140))
        ip_box = pygame.Rect(W//2-100, 140, 200, 30)
        pygame.draw.rect(self.game.screen, C_SLOT, ip_box)
        if self.ip_input_active:
            pygame.draw.rect(self.game.screen, C_SEL, ip_box, 2)
        self.game.screen.blit(self.game.font.render(self.ip_input, True, C_TEXT), (ip_box.x+5, ip_box.y+5))
        connect = pygame.Rect(W//2-120, 200, 240, 45)
        back = pygame.Rect(W//2-120, 450, 240, 45)
        self._btn(connect, "Подключиться")
        self._btn(back, "Назад")
        self.buttons = {"connect":connect,"back":back,"ip":ip_box}
    
    def _btn(self, rect, text):
        pygame.draw.rect(self.game.screen, C_MENU_BTN, rect)
        pygame.draw.rect(self.game.screen, C_MENU_BTN_HOVER, rect, 2)
        bt = self.game.font.render(text, True, C_TEXT)
        self.game.screen.blit(bt, bt.get_rect(center=rect.center))
    
    def show_status(self, msg):
        self.status_message = msg
        self.status_timer = 3.0
    
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if self.input_active:
                if event.key == pygame.K_RETURN: self.input_active = False
                elif event.key == pygame.K_BACKSPACE: self.nickname = self.nickname[:-1]
                elif len(self.nickname)<20: self.nickname += event.unicode
            elif self.ip_input_active:
                if event.key == pygame.K_RETURN: self.ip_input_active = False
                elif event.key == pygame.K_BACKSPACE: self.ip_input = self.ip_input[:-1]
                else: self.ip_input += event.unicode
        if event.type == pygame.MOUSEBUTTONDOWN:
            for key,rect in self.buttons.items():
                if rect.collidepoint(event.pos):
                    if key=="single": self.game.start_singleplayer(self.nickname)
                    elif key=="multi":
                        self.menu_state = "multiplayer"
                        self.discovered_servers = []
                        threading.Thread(target=self._discover, daemon=True).start()
                    elif key=="quit": pygame.quit(); sys.exit()
                    elif key=="nick": self.input_active = True; self.ip_input_active = False
                    elif key=="create":
                        self.show_status("Запуск хоста...")
                        self.game.start_host(self.nickname)
                    elif key=="join": self.menu_state = "join"
                    elif key=="back": self.menu_state = "main"
                    elif key=="connect":
                        self.show_status("Подключение к {}...".format(self.ip_input))
                        self.game.start_client(self.nickname, self.ip_input)
                    elif key=="ip": self.ip_input_active = True
    
    def _discover(self):
        self.discovered_servers = discover_servers(timeout=2.0)


class DevMenu:
    def __init__(self, game):
        self.game = game
        self.open = False
        self.items_per_row = 6
        self.slot_size = 50
        self.padding = 5
        self.time_buttons = []
    
    def open_menu(self):
        self.open = True
    
    def close_menu(self):
        self.open = False
    
    def draw(self):
        if not self.open: return
        pygame.draw.rect(self.game.screen, (20, 20, 20, 200), (50, 50, W-100, H-100))
        pygame.draw.rect(self.game.screen, (100, 100, 100), (50, 50, W-100, H-100), 2)
        title = self.game.font.render("Меню разработчика (E - закрыть)", True, C_TEXT)
        self.game.screen.blit(title, (70, 60))
        time_y = 90
        self.time_buttons = []
        time_labels = [("Утро", 0), ("День", 1), ("Вечер", 2), ("Ночь", 3)]
        btn_w, btn_h = 80, 30
        btn_spacing = 10
        for i, (label, phase) in enumerate(time_labels):
            btn_x = 70 + i * (btn_w + btn_spacing)
            rect = pygame.Rect(btn_x, time_y, btn_w, btn_h)
            self.time_buttons.append((rect, "time_{}".format(phase)))
            pygame.draw.rect(self.game.screen, C_SLOT, rect)
            pygame.draw.rect(self.game.screen, C_SEL, rect, 2)
            text = self.game.font_small.render(label, True, C_TEXT)
            text_rect = text.get_rect(center=rect.center)
            self.game.screen.blit(text, text_rect)
        spawn_btn = pygame.Rect(70, time_y + 40, 160, 30)
        self.time_buttons.append((spawn_btn, "spawn_zombie"))
        pygame.draw.rect(self.game.screen, (150, 50, 50), spawn_btn)
        pygame.draw.rect(self.game.screen, C_SEL, spawn_btn, 2)
        spawn_text = self.game.font_small.render("Зомби рядом (10 блоков)", True, C_TEXT)
        self.game.screen.blit(spawn_text, spawn_text.get_rect(center=spawn_btn.center))
        all_items = list(self.game.ALL_ITEMS.items())
        fast_dev_item = Item("Быстрый dev", self.game.sprites.fast_dev, T_FAST_DEV, True)
        all_items.append(("Быстрый dev", fast_dev_item))
        door_item = Item("Дверь", self.game.sprites.door_i, T_DOOR, True)
        all_items.append(("Дверь", door_item))
        x_start = 70
        y_start = 180
        for i, (name, item) in enumerate(all_items):
            row = i // self.items_per_row
            col = i % self.items_per_row
            x = x_start + col * (self.slot_size + self.padding)
            y = y_start + row * (self.slot_size + self.padding)
            pygame.draw.rect(self.game.screen, C_SLOT, (x, y, self.slot_size, self.slot_size))
            pygame.draw.rect(self.game.screen, (90, 90, 90), (x, y, self.slot_size, self.slot_size), 1)
            icon_size = 32
            icon_x = x + (self.slot_size - icon_size) // 2
            icon_y = y + (self.slot_size - icon_size) // 2
            self.game.screen.blit(item.icon, (icon_x, icon_y))
            name_text = self.game.font_small.render(name, True, C_TEXT)
            self.game.screen.blit(name_text, (x + 5, y + self.slot_size - 12))
    
    def handle_click(self, pos):
        if not self.open: return False
        mx, my = pos
        if mx < 50 or mx > W-50 or my < 50 or my > H-50:
            self.close_menu()
            return True
        for rect, action in self.time_buttons:
            if rect.collidepoint(pos):
                if action.startswith("time_"):
                    phase = int(action.split("_")[1])
                    self.game.set_time_phase(phase)
                elif action == "spawn_zombie":
                    self.game.spawn_zombie_nearby()
                return True
        all_items = list(self.game.ALL_ITEMS.items())
        fast_dev_item = Item("Быстрый dev", self.game.sprites.fast_dev, T_FAST_DEV, True)
        all_items.append(("Быстрый dev", fast_dev_item))
        door_item = Item("Дверь", self.game.sprites.door_i, T_DOOR, True)
        all_items.append(("Дверь", door_item))
        x_start = 70
        y_start = 180
        for i, (name, item) in enumerate(all_items):
            row = i // self.items_per_row
            col = i % self.items_per_row
            x = x_start + col * (self.slot_size + self.padding)
            y = y_start + row * (self.slot_size + self.padding)
            if x <= mx <= x + self.slot_size and y <= my <= y + self.slot_size:
                self.game._pickup(item, 10)
                return True
        return False


class CommandManager:
    def __init__(self, game):
        self.game = game
        self.commands = {}
        self._register()
    
    def _register(self):
        self.commands["help"] = self.cmd_help
        self.commands["tp"] = self.cmd_tp
        self.commands["heal"] = self.cmd_heal
        self.commands["feed"] = self.cmd_feed
        self.commands["kill"] = self.cmd_kill
        self.commands["give"] = self.cmd_give
        self.commands["clear"] = self.cmd_clear
        self.commands["time"] = self.cmd_time
        self.commands["day"] = lambda a: self.cmd_time(["set","day"])
        self.commands["night"] = lambda a: self.cmd_time(["set","night"])
        self.commands["spawn"] = self.cmd_spawn
        self.commands["say"] = self.cmd_say
        self.commands["stats"] = self.cmd_stats
        self.commands["list"] = self.cmd_list
        self.commands["op"] = self.cmd_op
        self.commands["kick"] = self.cmd_kick
        self.commands["ban"] = self.cmd_ban
        self.commands["unban"] = self.cmd_unban
        self.commands["god"] = self.cmd_god
        self.commands["save"] = self.cmd_save
    
    def execute(self, cmd_str, role="guest"):
        if not cmd_str.startswith("/"): return False
        parts = cmd_str[1:].strip().split()
        if not parts: return False
        cmd_name = parts[0].lower()
        args = parts[1:]
        if cmd_name not in self.commands:
            self.game.add_chat_message("Неизвестная команда: /{}".format(cmd_name), (255,100,100))
            return False
        server_cmds = ["op","kick","ban","unban","god"]
        if cmd_name in server_cmds and role != "op":
            self.game.add_chat_message("У вас нет прав!", (255,100,100))
            return False
        try:
            self.commands[cmd_name](args)
            return True
        except Exception as e:
            self.game.add_chat_message("Ошибка: {}".format(e), (255,100,100))
            return False
    
    def cmd_help(self, args):
        self.game.add_chat_message("Доступные команды:", (100,255,100))
        for cmd in sorted(self.commands.keys()):
            self.game.add_chat_message("  /{}".format(cmd), (200,200,200))
    
    def cmd_tp(self, args):
        if len(args)<2:
            self.game.add_chat_message("/tp <x> <y>", (255,200,100)); return
        try:
            self.game.px = float(args[0]); self.game.py = float(args[1])
            self.game.add_chat_message("Телепортация: ({:.0f}, {:.0f})".format(self.game.px, self.game.py), (100,255,100))
        except:
            self.game.add_chat_message("Неверные координаты!", (255,100,100))
    
    def cmd_heal(self, args):
        self.game.hp = 100
        self.game.add_chat_message("HP восстановлено!", (100,255,100))
    
    def cmd_feed(self, args):
        self.game.hunger = 100
        self.game.add_chat_message("Голод восстановлен!", (100,255,100))
    
    def cmd_kill(self, args):
        self.game.hp = 0
        self.game.add_chat_message("Вы умерли!", (255,100,100))
    
    def cmd_give(self, args):
        if len(args)<1:
            self.game.add_chat_message("/give <item> [count]", (255,200,100)); return
        name = args[0]; count = int(args[1]) if len(args)>1 else 1
        if name in self.game.ALL_ITEMS:
            self.game._pickup(self.game.ALL_ITEMS[name], count)
            self.game.add_chat_message("Выдано: {} x{}".format(name, count), (100,255,100))
        else:
            self.game.add_chat_message("Неизвестный предмет: {}".format(name), (255,100,100))
    
    def cmd_clear(self, args):
        for s in self.game.hotbar+self.game.inventory:
            s.item=None; s.count=0
        self.game.add_chat_message("Инвентарь очищен!", (100,255,100))
    
    def cmd_time(self, args):
        if len(args)<2 or args[0]!="set":
            self.game.add_chat_message("/time set <day|night>", (255,200,100)); return
        phases = {"day":1,"night":3}
        if args[1] in phases:
            self.game.day_timer = phases[args[1]]*PHASE_LENGTH
            self.game.add_chat_message("Время: {}".format(args[1]), (100,255,100))
    
    def cmd_spawn(self, args):
        angle = random.uniform(0, math.pi*2)
        dist = 10*TILE
        x = self.game.px + math.cos(angle)*dist
        y = self.game.py + math.sin(angle)*dist
        self.game.zombies.append(Zombie(x,y))
        self.game.add_chat_message("Зомби заспавнен!", (100,255,100))
    
    def cmd_say(self, args):
        self.game.add_chat_message("[Сервер] {}".format(' '.join(args)), (255,255,100))
    
    def cmd_stats(self, args):
        self.game.add_chat_message("HP: {:.0f}/100".format(self.game.hp), (200,200,200))
        self.game.add_chat_message("Голод: {:.0f}/100".format(self.game.hunger), (200,200,200))
    
    def cmd_list(self, args):
        self.game.add_chat_message("Игроки: {} (вы)".format(self.game.nickname), (200,200,200))
    
    def cmd_op(self, args):
        if not args:
            self.game.add_chat_message("/op <player>", (255,200,100)); return
        self.game.add_chat_message("{} теперь оператор!".format(args[0]), (255,215,0))
    
    def cmd_kick(self, args):
        if not args:
            self.game.add_chat_message("/kick <player>", (255,200,100)); return
        self.game.add_chat_message("{} кикнут".format(args[0]), (255,100,100))
    
    def cmd_ban(self, args):
        if not args:
            self.game.add_chat_message("/ban <player>", (255,200,100)); return
        self.game.add_chat_message("{} забанен".format(args[0]), (255,100,100))
    
    def cmd_unban(self, args):
        if not args:
            self.game.add_chat_message("/unban <player>", (255,200,100)); return
        self.game.add_chat_message("{} разбанен".format(args[0]), (100,255,100))
    
    def cmd_god(self, args):
        self.game.hp = 999999
        self.game.add_chat_message("Режим бога!", (255,215,0))
    
    def cmd_save(self, args):
        self.game._save_world()
        self.game.add_chat_message("Мир сохранён вручную!", (100,255,100))
