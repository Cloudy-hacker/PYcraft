# -*- coding: utf-8 -*-
"""
PYcraft 2.0 — основной файл игры (оркестратор)
"""

import pygame, random, sys, math, os, time, logging
from constants import *
from items import Item, Slot
from entities import Zombie
from network import NetworkClient
from sprites import Sprites, check_custom_sprites
from ui import MainMenu, DevMenu, CommandManager
from player_logic import PlayerLogic
from world_logic import WorldLogic
from inventory import Inventory
from render import Render
from network_client import NetworkClientLogic

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


class Game(PlayerLogic, WorldLogic, Inventory, Render, NetworkClientLogic):
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption("PYcraft 2.0")
        self.clock = pygame.time.Clock()

        # === ЗАГРУЗКА ШРИФТОВ ===
        try:
            from fonts_config import FONTS, FONTS_DIR, FALLBACK_FONT
            self.font_small = self._load_font("small")
            self.font = self._load_font("normal")
            self.font_big = self._load_font("big")
            logger.info("Шрифты загружены из конфигурации")
        except Exception as e:
            logger.warning("Не удалось загрузить шрифты: {}".format(e))
            fallback = "arial"
            try:
                from fonts_config import FALLBACK_FONT as FB
                fallback = FB
            except:
                pass
            self.font_small = pygame.font.SysFont(fallback, 10)
            self.font = pygame.font.SysFont(fallback, 14)
            self.font_big = pygame.font.SysFont(fallback, 24)

        self.custom_sprites_available = check_custom_sprites()
        self.use_custom_sprites = False
        self.sprites_warning = not self.custom_sprites_available
        self.sprites = Sprites(use_custom=False)

        self.main_menu = MainMenu(self)
        self.game_mode = "menu"
        self.client = NetworkClient()
        self.nickname = "Player"
        self.player_id = None
        self.role = "guest"
        self.px = 0
        self.py = 0
        self.speed = 150
        self.cam_x = 0
        self.cam_y = 0
        self.world = {}
        self.doors = {}
        self.grass = {}
        self.hotbar = [Slot() for _ in range(NUM_SLOTS)]
        self.inventory = [Slot() for _ in range(NUM_SLOTS * INV_ROWS)]
        self.sel = 0
        self.inv_open = False
        self.drag_item = None
        self.drag_count = 0
        self.hp = 100
        self.hunger = 100
        self.hunger_timer = 0
        self.regen_timer = 0.0
        self.zombies = []
        self.zombie_spawn_timer = 0.0
        self.dropped_items = []
        self.day_timer = 0
        self.brightness = 1.0
        self.moving = False
        self.walk_time = 0.0
        self.other_players = {}
        self.network_send_timer = 0.0
        self.q_held = False
        self.q_timer = 0.0
        self.drone_mode = False
        self.drone_zoom = 1.0
        self.drone_tiles = 25
        self.drone_dragging = False
        self.drone_drag_start = (0, 0)
        self.drone_cam_offset = (0, 0)
        self.was_connected = False
        self.ALL_ITEMS = {}
        self.RECIPES = []
        self._init_items()
        self.command_manager = CommandManager(self)
        self.chat_messages = []
        self.chat_input = ""
        self.chat_input_active = False
        self.debug = False
        self.kick_screen = False
        self.kick_message = ""
        self.death_screen = False
        self.death_timer = 0.0
        self.last_death_pos = (0, 0)
        self.tooltip_text = ""
        self.tooltip_timer = 0
        self.fps = 0
        self.frame_count = 0
        self.fps_time = 0
        self.last_debug_x = 0
        self.last_debug_y = 0
        self.dev_menu = DevMenu(self)
        logger.info("PYcraft 2.0 запущен")
        if self.sprites_warning:
            logger.warning("Внимание! Спрайты не обнаружены!")

    def _load_font(self, font_key):
        try:
            from fonts_config import FONTS, FONTS_DIR
            if font_key not in FONTS:
                raise KeyError("Шрифт '{}' не найден".format(font_key))
            font_file, font_size = FONTS[font_key]
            font_path = os.path.join(FONTS_DIR, font_file)
            if os.path.exists(font_path):
                return pygame.font.Font(font_path, font_size)
            else:
                logger.warning("Файл шрифта не найден: {}".format(font_path))
                raise FileNotFoundError(font_path)
        except Exception as e:
            from fonts_config import FALLBACK_FONT
            sizes = {"small": 10, "normal": 14, "big": 24}
            return pygame.font.SysFont(FALLBACK_FONT, sizes.get(font_key, 14))

    def _init_items(self):
        self.ALL_ITEMS = {
            "Дерево": Item("Дерево", self.sprites.wood, T_TREE, True),
            "Камень": Item("Камень", self.sprites.stone_i, T_STONE, True),
            "Стена": Item("Стена", self.sprites.wall_i, T_WALL, True),
            "Фундамент": Item("Фундамент", self.sprites.found_i, T_FOUND, True),
            "Топор": Item("Топор", self.sprites.axe),
            "Кирка": Item("Кирка", self.sprites.pick),
            "Меч": Item("Меч", self.sprites.sword),
            "Ягоды": Item("Ягоды", self.sprites.berry_i, is_food=True, food_value=20),
            "Дверь": Item("Дверь", self.sprites.door_i, T_DOOR, True),
        }
        self.RECIPES = [
            {"name": "Топор", "in": {"Дерево": 3, "Камень": 2}, "out": ("Топор", 1)},
            {"name": "Кирка", "in": {"Камень": 3, "Дерево": 2}, "out": ("Кирка", 1)},
            {"name": "Меч", "in": {"Камень": 2, "Дерево": 1}, "out": ("Меч", 1)},
            {"name": "Стена x4", "in": {"Дерево": 2}, "out": ("Стена", 4)},
            {"name": "Фундамент", "in": {"Камень": 8}, "out": ("Фундамент", 1)},
            {"name": "Дверь", "in": {"Дерево": 6}, "out": ("Дверь", 1)},
        ]

    def toggle_sprites(self):
        if self.use_custom_sprites:
            self.use_custom_sprites = False
            self.sprites = Sprites(use_custom=False)
        else:
            if self.custom_sprites_available:
                self.use_custom_sprites = True
                self.sprites = Sprites(use_custom=True)
            else:
                logger.warning("Пользовательские спрайты не найдены!")
        for name, item in self.ALL_ITEMS.items():
            sprite_map = {
                "Дерево": self.sprites.wood, "Камень": self.sprites.stone_i,
                "Стена": self.sprites.wall_i, "Фундамент": self.sprites.found_i,
                "Топор": self.sprites.axe, "Кирка": self.sprites.pick,
                "Меч": self.sprites.sword, "Ягоды": self.sprites.berry_i,
                "Дверь": self.sprites.door_i
            }
            if name in sprite_map:
                item.icon = sprite_map[name]

    def set_time_phase(self, phase):
        self.day_timer = phase * PHASE_LENGTH

    def start_singleplayer(self, nickname):
        self.nickname = nickname
        self.game_mode = "single"
        self.role = "op"
        self._reset_game()
        self._load_world()

    def start_host(self, nickname):
        self.nickname = nickname
        self.game_mode = "host"
        self.role = "op"
        self._reset_game()
        self.main_menu.show_status("Хост запущен")

    def start_client(self, nickname, ip):
        if self.client.connect(ip):
            self.nickname = nickname
            self.game_mode = "client"
            self._reset_game()
            self.client.send({"type": "connect", "nickname": nickname})
        else:
            self.main_menu.show_status("Не удалось подключиться!")

    def _reset_game(self):
        self.hp = 100
        self.hunger = 100
        self.hunger_timer = 0
        self.regen_timer = 0.0
        self.px = 0
        self.py = 0
        self.cam_x = 0
        self.cam_y = 0
        self.world = {}
        self.doors = {}
        self.grass = {}
        self.hotbar = [Slot() for _ in range(NUM_SLOTS)]
        self.inventory = [Slot() for _ in range(NUM_SLOTS * INV_ROWS)]
        self.sel = 0
        self.inv_open = False
        self.drag_item = None
        self.drag_count = 0
        self.zombies = []
        self.zombie_spawn_timer = 0.0
        self.dropped_items = []
        self.day_timer = 0
        self.brightness = 1.0
        self.moving = False
        self.walk_time = 0.0
        self.other_players = {}
        self.network_send_timer = 0.0
        self.q_held = False
        self.q_timer = 0.0
        self.drone_mode = False
        self.drone_cam_offset = (0, 0)
        self.was_connected = False
        self.chat_messages = []
        self.chat_input = ""
        self.chat_input_active = False
        self.debug = False
        self.kick_screen = False
        self.kick_message = ""
        self.death_screen = False
        self.death_timer = 0.0
        self.dev_menu.close_menu()

    def add_chat_message(self, text, color=C_TEXT):
        self.chat_messages.append({"text": text, "color": color, "time": time.time()})
        if len(self.chat_messages) > 10:
            self.chat_messages.pop(0)

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    if self.game_mode == "single":
                        self._save_world()
                    if self.client.connected:
                        self._send_player_state()
                        self.client.send({"type": "disconnect"})
                        time.sleep(0.1)
                    self.client.disconnect()
                    pygame.quit()
                    sys.exit()
                if self.kick_screen:
                    if event.type == pygame.KEYDOWN:
                        if event.key in [pygame.K_ESCAPE, pygame.K_RETURN]:
                            self.kick_screen = False
                            self.kick_message = ""
                            if self.client.connected:
                                self.client.disconnect()
                            self.game_mode = "menu"
                            self.other_players.clear()
                    continue
                if self.death_screen:
                    if event.type == pygame.KEYDOWN:
                        self.death_screen = False
                    continue
                if self.game_mode == "menu":
                    self.main_menu.handle_event(event)
                elif self.game_mode in ["single", "host", "client"]:
                    self._handle_game_event(event)
            if self.kick_screen:
                self._draw_kick_screen()
            elif self.death_screen:
                self._draw_death_screen(dt)
            elif self.game_mode == "menu":
                self.main_menu.draw()
            elif self.game_mode in ["single", "host", "client"]:
                if self.game_mode == "client":
                    self._process_network()
                    if self.was_connected and not self.client.connected and not self.kick_screen:
                        self.kick_message = "Соединение с сервером потеряно"
                        self.kick_screen = True
                self._update_game(dt)
                self._draw_game()

    def _handle_game_event(self, event):
        if event.type == pygame.KEYDOWN:
            if self.chat_input_active:
                if event.key == pygame.K_RETURN:
                    if self.chat_input.startswith("/"):
                        self._command(self.chat_input)
                    elif self.chat_input:
                        self._say(self.chat_input)
                    self.chat_input = ""
                    self.chat_input_active = False
                elif event.key == pygame.K_ESCAPE:
                    self.chat_input_active = False
                    self.chat_input = ""
                elif event.key == pygame.K_BACKSPACE:
                    self.chat_input = self.chat_input[:-1]
                elif len(self.chat_input) < 100 and event.unicode.isprintable():
                    self.chat_input += event.unicode
                return
            if event.key == pygame.K_F3:
                self.debug = not self.debug
                return
            if event.key == pygame.K_t:
                self.chat_input_active = True
                return
            if event.key == pygame.K_F2:
                self.toggle_sprites()
                return
            if event.key == pygame.K_f and not self.inv_open and not self.dev_menu.open:
                self.drone_mode = not self.drone_mode
                self.drone_cam_offset = (0, 0)
                return
            if event.key == pygame.K_e:
                if self.dev_menu.open:
                    self.dev_menu.close_menu()
                else:
                    self.inv_open = not self.inv_open
                    if not self.inv_open and self.drag_item:
                        self._pickup(self.drag_item, self.drag_count)
                        self.drag_item = None
                        self.drag_count = 0
                return
            if event.key == pygame.K_q and not self.inv_open and not self.dev_menu.open and not self.drone_mode:
                self.q_held = True
                self.q_timer = 0.0
                keys = pygame.key.get_pressed()
                if keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]:
                    self._drop_full_stack()
                else:
                    self._drop_one()
                return
            if not self.inv_open and not self.dev_menu.open:
                if pygame.K_1 <= event.key <= pygame.K_9:
                    self.sel = event.key - pygame.K_1
                    return
            if event.key == pygame.K_ESCAPE:
                if self.game_mode == "single":
                    self._save_world()
                if self.client.connected:
                    self._send_player_state()
                    self.client.send({"type": "disconnect"})
                    time.sleep(0.1)
                    self.client.disconnect()
                self.game_mode = "menu"
                self.other_players.clear()
                self.inv_open = False
                self.dev_menu.close_menu()
                self.drone_mode = False
                return
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_q:
                self.q_held = False
                self.q_timer = 0.0
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.dev_menu.open:
                self.dev_menu.handle_click(event.pos)
            elif self.inv_open:
                shift = bool(pygame.key.get_mods() & pygame.KMOD_SHIFT)
                self._handle_inv_click(event.pos, event.button, shift)
            elif self.drone_mode:
                if event.button == 1:
                    self.drone_dragging = True
                    self.drone_drag_start = event.pos
            else:
                if event.button == 4:
                    self.sel = (self.sel - 1) % NUM_SLOTS
                elif event.button == 5:
                    self.sel = (self.sel + 1) % NUM_SLOTS
                elif event.button == 1:
                    if not self._click_dropped_item(event.pos):
                        if not self._attack_zombie(event.pos):
                            self.mine(event.pos)
                elif event.button == 3:
                    if not self._eat_food():
                        if not self._interact_door(event.pos):
                            if not self._interact_dev(event.pos):
                                self.place(event.pos)
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.drone_dragging:
                self.drone_dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.drone_dragging:
                dx = event.pos[0] - self.drone_drag_start[0]
                dy = event.pos[1] - self.drone_drag_start[1]
                self.drone_cam_offset = (
                    self.drone_cam_offset[0] + dx,
                    self.drone_cam_offset[1] + dy
                )
                self.drone_drag_start = event.pos

    def _update_game(self, dt):
        self.frame_count += 1
        self.fps_time += dt
        if self.fps_time >= 1.0:
            self.fps = self.frame_count
            self.frame_count = 0
            self.fps_time = 0
        self.day_timer += dt
        cycle = PHASE_LENGTH * 4
        if self.day_timer >= cycle:
            self.day_timer = 0
        phase = self.day_timer / PHASE_LENGTH
        if phase < 1:
            self.brightness = 0.3 + 0.7 * (phase / 1.0)
        elif phase < 2:
            self.brightness = 1.0
        elif phase < 3:
            self.brightness = 1.0 - 0.7 * ((phase - 2) / 1.0)
        else:
            self.brightness = 0.3
        if self.game_mode != "client":
            is_night = phase >= 3
            if is_night and len(self.zombies) < MAX_ZOMBIES:
                self.zombie_spawn_timer += dt
                if self.zombie_spawn_timer >= 1.0 / ZOMBIE_SPAWN_RATE:
                    self.zombie_spawn_timer = 0
                    angle = random.uniform(0, math.pi * 2)
                    dist = random.uniform(400, 600)
                    x = self.px + math.cos(angle) * dist
                    y = self.py + math.sin(angle) * dist
                    x = max(TILE, min(MAP_W * TILE - TILE, x))
                    y = max(TILE, min(MAP_H * TILE - TILE, y))
                    self.zombies.append(Zombie(x, y))
            for zombie in self.zombies:
                zombie.update(dt, self.px, self.py, self)
                dist = math.sqrt((zombie.x - self.px) ** 2 + (zombie.y - self.py) ** 2)
                if dist < 30 and zombie.attack_cooldown <= 0:
                    self.hp -= zombie.damage
                    zombie.attack_cooldown = 1.0
                if phase < 2.5:
                    zombie.burn_timer += dt
                    if zombie.burn_timer >= 1.5:
                        zombie.burn_timer = 0.0
                        zombie.hp -= 1.5
                        if zombie.hp <= 0:
                            if zombie in self.zombies:
                                self.zombies.remove(zombie)
                else:
                    zombie.burn_timer = 0.0
        keys = pygame.key.get_pressed()
        if self.inv_open or self.dev_menu.open:
            return
        if not self._update_player(dt, keys):
            return
        if not self.drone_mode:
            self.cam_x = int(self.px - W // 2)
            self.cam_y = int(self.py - H // 2)
            self.drone_zoom = 1.0
        if self.game_mode == "client":
            self.network_send_timer += dt
            if self.network_send_timer >= 0.02:
                self.network_send_timer = 0
                self._send_position()


if __name__ == "__main__":
    Game().run()
