# -*- coding: utf-8 -*-
"""
Вся отрисовка игры
"""
import pygame, time
from constants import *


class Render:
    def _draw_game(self):
        self.screen.fill(C_BG)
        zoom = self.drone_zoom if self.drone_mode else 1.0
        if self.drone_mode:
            x0 = max(0, self.cam_x // TILE - 1)
            y0 = max(0, self.cam_y // TILE - 1)
            x1 = min(MAP_W, x0 + self.drone_tiles * 2 + 3)
            y1 = min(MAP_H, y0 + self.drone_tiles * 2 + 3)
        else:
            x0 = max(0, self.cam_x // TILE - 1)
            y0 = max(0, self.cam_y // TILE - 1)
            x1 = min(MAP_W, (self.cam_x + W) // TILE + 2)
            y1 = min(MAP_H, (self.cam_y + H) // TILE + 2)
        for ty in range(y0, y1):
            for tx in range(x0, x1):
                sx = int((tx * TILE - self.cam_x) * zoom)
                sy = int((ty * TILE - self.cam_y) * zoom)
                ts = int(TILE * zoom)
                gc = self.grass.get((tx, ty), C_BG)
                r = int(gc[0] * self.brightness)
                g = int(gc[1] * self.brightness)
                b = int(gc[2] * self.brightness)
                pygame.draw.rect(self.screen, (r, g, b), (sx, sy, ts, ts))
        current_time = time.time()
        for dropped in self.dropped_items:
            sx = int((dropped.x - self.cam_x) * zoom)
            sy = int((dropped.y - self.cam_y + dropped.get_bob_y(current_time)) * zoom)
            shadow_y = int((dropped.y - self.cam_y + 8) * zoom)
            pygame.draw.ellipse(self.screen, (40, 60, 30), (sx - 8, shadow_y, 16, 6))
            self.screen.blit(dropped.item.icon, (sx - 12, sy - 12))
            if dropped.count > 1:
                t = self.font_small.render(str(dropped.count), True, C_TEXT)
                self.screen.blit(t, (sx + 8, sy + 8))
        for ty in range(y0, y1):
            for tx in range(x0, x1):
                sx = int((tx * TILE - self.cam_x) * zoom)
                sy = int((ty * TILE - self.cam_y) * zoom)
                b = self.world.get((tx, ty), T_EMPTY)
                if b == T_TREE:
                    self.screen.blit(self.sprites.tree, (sx, sy))
                elif b == T_STONE:
                    self.screen.blit(self.sprites.stone, (sx, sy))
                elif b == T_WALL:
                    self.screen.blit(self.sprites.wall, (sx, sy))
                elif b == T_FOUND:
                    self.screen.blit(self.sprites.foundation, (sx, sy))
                elif b == T_BERRY:
                    self.screen.blit(self.sprites.berry, (sx, sy))
                elif b == T_DEV:
                    self.screen.blit(self.sprites.dev, (sx, sy))
                elif b == T_FAST_DEV:
                    self.screen.blit(self.sprites.fast_dev, (sx, sy))
                elif b == T_DOOR:
                    ds = self.sprites.door_open if self.doors.get((tx, ty), False) else self.sprites.door_closed
                    self.screen.blit(ds, (sx, sy))
        for zombie in self.zombies:
            sx = int((zombie.x - self.cam_x) * zoom)
            sy = int((zombie.y - self.cam_y) * zoom)
            self.screen.blit(self.sprites.zombie, (sx - 16, sy - 16))
            hp_ratio = max(0, zombie.hp) / 10
            pygame.draw.rect(self.screen, (100, 0, 0), (sx - 15, sy - 22, 30, 4))
            pygame.draw.rect(self.screen, (0, 200, 0), (sx - 15, sy - 22, 30 * hp_ratio, 4))
            if self.day_timer / PHASE_LENGTH < 2.5:
                pygame.draw.circle(self.screen, (255, 150, 0), (sx, sy - 18), 3)
        for pid, pd in self.other_players.items():
            sx = int((pd["x"] - self.cam_x) * zoom)
            sy = int((pd["y"] - self.cam_y) * zoom)
            self.screen.blit(self.sprites.player2[0], (sx - 16, sy - 16))
            ns = self.font_small.render(pd["name"], True, C_TEXT)
            self.screen.blit(ns, (sx - ns.get_width() // 2, sy - 25))
        px = int((self.px - self.cam_x) * zoom)
        py = int((self.py - self.cam_y) * zoom)
        if self.drone_mode:
            pygame.draw.circle(self.screen, (255, 0, 0), (px, py), 8)
            pygame.draw.circle(self.screen, (200, 0, 0), (px, py), 8, 2)
        else:
            phase = 0 if self.moving and int(self.walk_time) % 2 == 0 else 1
            self.screen.blit(self.sprites.player[phase], (px - 16, py - 16))
        self._draw_hotbar()
        self._draw_ui()
        if self.sprites_warning:
            warning_text = "Внимание! Спрайты не обнаружены!"
            warning_surface = self.font.render(warning_text, True, (255, 0, 0))
            self.screen.blit(warning_surface, (10, H - 30))
        hint = "E-инв | F-дрон | F2-спрайты | F3-debug | T-чат | Q-выброс" if not self.inv_open and not self.dev_menu.open else "E - закрыть"
        if self.drone_mode:
            hint += " [ДРОН]"
        self.screen.blit(self.font.render(hint, True, C_TEXT), (10, 10))
        if self.inv_open:
            self._draw_inventory()
            if self.drag_item:
                mx, my = pygame.mouse.get_pos()
                self.screen.blit(self.drag_item.icon, (mx - 12, my - 12))
                if self.drag_count > 1:
                    t = self.font_small.render(str(self.drag_count), True, C_TEXT)
                    self.screen.blit(t, (mx + 8, my + 8))
        if self.dev_menu.open:
            self.dev_menu.draw()
        if self.debug:
            self._draw_debug()
        self._draw_chat()
        pygame.display.flip()

    def _draw_ui(self):
        pygame.draw.rect(self.screen, (100, 0, 0), (10, 50, 100, 10))
        pygame.draw.rect(self.screen, (200, 0, 0), (10, 50, self.hp, 10))
        hp_text = self.font_small.render("HP: {}".format(int(self.hp)), True, C_TEXT)
        self.screen.blit(hp_text, (10, 40))
        pygame.draw.rect(self.screen, (100, 100, 0), (10, 70, 100, 10))
        pygame.draw.rect(self.screen, (200, 200, 0), (10, 70, self.hunger, 10))
        hunger_text = self.font_small.render("Голод: {}".format(int(self.hunger)), True, C_TEXT)
        self.screen.blit(hunger_text, (10, 60))
        phase = self.day_timer / PHASE_LENGTH
        if phase < 1:
            time_text = "Утро"
        elif phase < 2:
            time_text = "День"
        elif phase < 3:
            time_text = "Вечер"
        else:
            time_text = "Ночь"
        time_surface = self.font_small.render(time_text, True, C_TEXT)
        self.screen.blit(time_surface, (10, 90))

    def _draw_hotbar(self):
        total_w = NUM_SLOTS * (SLOT_SIZE + SLOT_PAD) - SLOT_PAD
        ox = (W - total_w) // 2
        oy = H - SLOT_SIZE - 10
        pygame.draw.rect(self.screen, C_HBAR, (ox - 5, oy - 5, total_w + 10, SLOT_SIZE + 10))
        for i in range(NUM_SLOTS):
            x = ox + i * (SLOT_SIZE + SLOT_PAD)
            y = oy
            pygame.draw.rect(self.screen, C_SLOT, (x, y, SLOT_SIZE, SLOT_SIZE))
            if i == self.sel:
                pygame.draw.rect(self.screen, C_SEL, (x, y, SLOT_SIZE, SLOT_SIZE), 3)
            slot = self.hotbar[i]
            if not slot.empty():
                self.screen.blit(slot.item.icon, (x + 10, y + 10))
                if slot.count > 1:
                    t = self.font.render(str(slot.count), True, C_TEXT)
                    self.screen.blit(t, (x + SLOT_SIZE - t.get_width() - 2, y + SLOT_SIZE - t.get_height() - 1))
            n = self.font.render(str(i + 1), True, (160, 160, 160))
            self.screen.blit(n, (x + 2, y + 1))

    def _draw_inventory(self):
        inv_width = 500
        inv_height = 350
        inv_x = (W - inv_width) // 2
        inv_y = (H - inv_height) // 2
        pygame.draw.rect(self.screen, C_INV, (inv_x, inv_y, inv_width, inv_height))
        pygame.draw.rect(self.screen, (80, 80, 80), (inv_x, inv_y, inv_width, inv_height), 2)
        self.screen.blit(self.font.render("Инвентарь", True, C_TEXT), (inv_x + 10, inv_y + 10))
        slot_size = 40
        slot_pad = 4
        start_x = inv_x + 10
        start_y = inv_y + 40
        for i in range(len(self.inventory)):
            row = i // NUM_SLOTS
            col = i % NUM_SLOTS
            x = start_x + col * (slot_size + slot_pad)
            y = start_y + row * (slot_size + slot_pad)
            pygame.draw.rect(self.screen, C_SLOT, (x, y, slot_size, slot_size))
            pygame.draw.rect(self.screen, (90, 90, 90), (x, y, slot_size, slot_size), 1)
            slot = self.inventory[i]
            if not slot.empty():
                self.screen.blit(slot.item.icon, (x + 8, y + 8))
                if slot.count > 1:
                    t = self.font_small.render(str(slot.count), True, C_TEXT)
                    self.screen.blit(t, (x + slot_size - t.get_width() - 2, y + slot_size - t.get_height() - 2))
        recipe_x = inv_x + inv_width - 200
        recipe_y = inv_y + 10
        self.screen.blit(self.font.render("Крафт", True, C_TEXT), (recipe_x, recipe_y))
        available_recipes = [r for r in self.RECIPES if self._can_craft(r)]
        for i, recipe in enumerate(available_recipes):
            self._draw_recipe_compact(recipe, i, recipe_x, recipe_y + 25)

    def _draw_recipe_compact(self, recipe, i, x, y):
        can = self._can_craft(recipe)
        bg = C_REC_OK if can else C_REC_NO
        rect = pygame.Rect(x, y + i * 45, 190, 40)
        pygame.draw.rect(self.screen, bg, rect)
        pygame.draw.rect(self.screen, (120, 120, 120), rect, 1)
        self.screen.blit(self.font_small.render(recipe["name"], True, C_TEXT), (x + 5, y + i * 45 + 3))
        ix = x + 5
        iy = y + i * 45 + 20
        for ing_name, ing_count in recipe["in"].items():
            ing_item = self.ALL_ITEMS.get(ing_name)
            if ing_item is None:
                continue
            self.screen.blit(ing_item.icon, (ix, iy))
            have = self._count_item(ing_name)
            color = (180, 255, 180) if have >= ing_count else (255, 150, 150)
            t = self.font_small.render("{}({})".format(ing_count, have), True, color)
            self.screen.blit(t, (ix + 20, iy + 4))
            ix += 60
        out_name, out_count = recipe["out"]
        out_item = self.ALL_ITEMS.get(out_name)
        if out_item:
            self.screen.blit(out_item.icon, (x + 160, y + i * 45 + 10))

    def _draw_debug(self):
        pygame.draw.rect(self.screen, (0, 0, 0, 180), (10, 10, 320, 240))
        pygame.draw.rect(self.screen, (100, 100, 100), (10, 10, 320, 240), 1)
        phase = self.day_timer / PHASE_LENGTH
        if phase < 1:
            time_text = "Утро"
        elif phase < 2:
            time_text = "День"
        elif phase < 3:
            time_text = "Вечер"
        else:
            time_text = "Ночь"
        lines = [
            "PYcraft 2.0 — Debug",
            "FPS: {}".format(self.fps),
            "Игрок: ({:.0f}, {:.0f})".format(self.px, self.py),
            "Камера: ({}, {})".format(self.cam_x, self.cam_y),
            "Мир: {} тайлов".format(len(self.world)),
            "Трава: {} тайлов".format(len(self.grass)),
            "Зомби: {}".format(len(self.zombies)),
            "Время: {} ({:.0f}с)".format(time_text, self.day_timer),
            "Яркость: {:.2f}".format(self.brightness),
            "HP: {} | Голод: {}".format(int(self.hp), int(self.hunger)),
            "Роль: {}".format(self.role),
            "Режим: {}".format(self.game_mode),
            "Дрон: {}".format('вкл' if self.drone_mode else 'выкл'),
            "Спрайты: {}".format('польз.' if self.use_custom_sprites else 'Python'),
            "Подключено: {}".format(self.client.connected),
        ]
        for i, line in enumerate(lines):
            color = (0, 255, 0) if i == 0 else (200, 200, 200)
            t = self.font_small.render(line, True, color)
            self.screen.blit(t, (15, 15 + i * 17))

    def _draw_chat(self):
        chat_x = 10
        chat_y = H - 200
        for i, msg in enumerate(self.chat_messages[-5:]):
            c = msg["color"]
            ts = self.font_small.render(msg["text"], True, c)
            self.screen.blit(ts, (chat_x, chat_y + i * 18))
        if self.chat_input_active:
            pygame.draw.rect(self.screen, (0, 0, 0, 180), (chat_x, H - 40, 400, 30))
            it = self.font_small.render(self.chat_input, True, C_TEXT)
            self.screen.blit(it, (chat_x + 5, H - 35))

    def _draw_kick_screen(self):
        self.screen.fill((80, 0, 0))
        title = self.font_big.render("Вы были отключены", True, (255, 80, 80))
        self.screen.blit(title, (W // 2 - title.get_width() // 2, 150))
        pygame.draw.line(self.screen, (150, 50, 50), (100, 220), (W - 100, 220), 2)
        reason_lines = self.kick_message.split("\n")
        y = 260
        for line in reason_lines:
            txt = self.font.render(line, True, (255, 200, 200))
            self.screen.blit(txt, (W // 2 - txt.get_width() // 2, y))
            y += 25
        pygame.draw.line(self.screen, (150, 50, 50), (100, y + 20), (W - 100, y + 20), 2)
        hint = self.font.render("Нажмите ESC или ENTER чтобы вернуться в меню", True, (200, 150, 150))
        self.screen.blit(hint, (W // 2 - hint.get_width() // 2, H - 80))
        pygame.display.flip()

    def _draw_death_screen(self, dt):
        self.death_timer -= dt
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((150, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        title = self.font_big.render("Вы умерли!", True, (255, 255, 255))
        self.screen.blit(title, (W // 2 - title.get_width() // 2, H // 2 - 60))
        death_text = self.font.render(
            "Ваши вещи остались на ({}, {})".format(self.last_death_pos[0], self.last_death_pos[1]),
            True, (255, 200, 200)
        )
        self.screen.blit(death_text, (W // 2 - death_text.get_width() // 2, H // 2))
        if self.death_timer > 0:
            timer_text = self.font.render("Возрождение через {}...".format(int(self.death_timer) + 1), True, (200, 200, 200))
            self.screen.blit(timer_text, (W // 2 - timer_text.get_width() // 2, H // 2 + 40))
        else:
            hint = self.font.render("Нажмите любую клавишу чтобы продолжить", True, (200, 200, 200))
            self.screen.blit(hint, (W // 2 - hint.get_width() // 2, H // 2 + 40))
            if self.death_timer < -2.0:
                self.death_screen = False
        pygame.display.flip()
