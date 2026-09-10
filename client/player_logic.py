# -*- coding: utf-8 -*-
"""
Логика игрока: движение, коллизии, смерть, голод
Смерть в мультиплеере: вещи уходят дропом на сервер
"""
import pygame, random, math
from constants import *
from items import DroppedItem
from entities import Zombie


class PlayerLogic:
    def _check_collision(self, px, py):
        half = TILE // 2
        player_tx = int(px) // TILE
        player_ty = int(py) // TILE
        for ty_check in range(player_ty - 1, player_ty + 2):
            for tx_check in range(player_tx - 1, player_tx + 2):
                if self._is_solid(tx_check, ty_check):
                    tile_rect = pygame.Rect(tx_check * TILE, ty_check * TILE, TILE, TILE)
                    player_rect = pygame.Rect(px - half, py - half, TILE - 4, TILE - 4)
                    if tile_rect.colliderect(player_rect):
                        return True
        return False

    def _check_zombie_collision(self, x, y):
        zombie_size = 20
        half = zombie_size // 2
        zombie_tx = int(x) // TILE
        zombie_ty = int(y) // TILE
        for ty_check in range(zombie_ty - 1, zombie_ty + 2):
            for tx_check in range(zombie_tx - 1, zombie_tx + 2):
                if self._is_solid(tx_check, ty_check):
                    tile_rect = pygame.Rect(tx_check * TILE, ty_check * TILE, TILE, TILE)
                    zombie_rect = pygame.Rect(x - half, y - half, zombie_size, zombie_size)
                    if tile_rect.colliderect(zombie_rect):
                        return True
        return False

    def _check_distance(self, pos):
        wx = pos[0] + self.cam_x
        wy = pos[1] + self.cam_y
        dist = math.sqrt((wx - self.px) ** 2 + (wy - self.py) ** 2)
        return dist <= INTERACTION_DISTANCE

    def _is_solid(self, tx, ty):
        block = self.world.get((tx, ty), T_EMPTY)
        if block in (T_WALL, T_STONE):
            return True
        if block == T_DOOR and self.doors.get((tx, ty), True):
            return True
        return False

    def _on_death(self):
        death_x = self.px
        death_y = self.py
        self.last_death_pos = (int(death_x), int(death_y))
        all_slots = list(self.hotbar) + list(self.inventory)
        if self.game_mode == "client" and self.client.connected:
            items = [[s.item.name, s.count] for s in all_slots if not s.empty()]
            self._send_death_drop(items, death_x, death_y)
            dropped_count = sum(c for _, c in items)
        else:
            dropped_count = 0
            for slot in all_slots:
                if not slot.empty():
                    drop_x = death_x + random.uniform(-40, 40)
                    drop_y = death_y + random.uniform(-40, 40)
                    self.dropped_items.append(DroppedItem(drop_x, drop_y, slot.item, slot.count))
                    dropped_count += slot.count
        for slot in all_slots:
            slot.item = None
            slot.count = 0
        self.add_chat_message("Вы умерли!", (255, 80, 80))
        self.add_chat_message("Ваши вещи ({} шт.) остались на месте смерти.".format(dropped_count), (255, 200, 100))
        self.hp = 100
        self.hunger = 100
        cx, cy = MAP_W // 2, MAP_H // 2
        self.px = cx * TILE + TILE // 2
        self.py = cy * TILE + TILE // 2
        self.inv_open = False
        self.dev_menu.close_menu()
        self.drag_item = None
        self.drag_count = 0
        self.q_held = False
        self.q_timer = 0.0
        self.death_screen = True
        self.death_timer = 3.0

    def _update_player(self, dt, keys):
        running = keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]
        hunger_rate = 1.5 if running else 1.0
        self.hunger_timer += dt
        if self.hunger_timer >= 10:
            self.hunger_timer = 0
            self.hunger = max(0, self.hunger - hunger_rate)
        if self.hunger <= 0:
            self.hp = max(0, self.hp - 1)
        if self.hunger >= 60 and self.hp < 100:
            self.regen_timer += dt
            if self.regen_timer >= 1.0:
                self.regen_timer = 0.0
                heal_amount = min(5, 100 - self.hp)
                self.hp += heal_amount
        if self.hp <= 0:
            self._on_death()
            return False

        if self.q_held and not self.inv_open and not self.dev_menu.open and not self.drone_mode:
            ctrl_held = keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]
            if not ctrl_held:
                self.q_timer += dt
                if self.q_timer >= Q_DROP_INTERVAL:
                    self.q_timer = 0.0
                    self._drop_one()

        if not self.drone_mode:
            dx = dy = 0
            current_speed = self.speed * 2 if running else self.speed
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                dy -= 1
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                dy += 1
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                dx -= 1
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                dx += 1
            self.moving = (dx != 0 or dy != 0)
            if self.moving:
                self.walk_time += dt * 8
            if dx != 0 and dy != 0:
                dx *= 0.707
                dy *= 0.707
            new_px = self.px + dx * current_speed * dt
            new_py = self.py + dy * current_speed * dt
            if not self._check_collision(new_px, self.py):
                self.px = new_px
            if not self._check_collision(self.px, new_py):
                self.py = new_py
            half = TILE // 2
            self.px = max(half, min(MAP_W * TILE - half, self.px))
            self.py = max(half, min(MAP_H * TILE - half, self.py))
            dist_moved = math.sqrt((self.px - self.last_debug_x) ** 2 + (self.py - self.last_debug_y) ** 2)
            if dist_moved >= 10 * TILE:
                self.last_debug_x = self.px
                self.last_debug_y = self.py
        else:
            world_view = self.drone_tiles * TILE * 2
            base_cam_x = int(self.px - world_view / 2)
            base_cam_y = int(self.py - world_view / 2)
            self.cam_x = base_cam_x - self.drone_cam_offset[0]
            self.cam_y = base_cam_y - self.drone_cam_offset[1]
            self.drone_zoom = min(W / world_view, H / world_view)
        return True
