# -*- coding: utf-8 -*-
"""
Инвентарь, крафт, дроп, еда, атака
В мультиплеере дроп и атака уходят на сервер
"""
import pygame, random, math
from constants import *
from items import DroppedItem


class Inventory:
    def _all_slots(self):
        for s in self.hotbar:
            yield s
        for s in self.inventory:
            yield s

    def _count_item(self, name):
        return sum(s.count for s in self._all_slots() if not s.empty() and s.item.name == name)

    def _pickup(self, item, amount):
        left = amount
        for s in self.hotbar:
            if left <= 0:
                break
            if not s.empty() and s.item.name == item.name:
                left = s.add(item, left)
        for s in self.inventory:
            if left <= 0:
                break
            if not s.empty() and s.item.name == item.name:
                left = s.add(item, left)
        for s in self.hotbar:
            if left <= 0:
                break
            if s.empty():
                left = s.add(item, left)
        for s in self.inventory:
            if left <= 0:
                break
            if s.empty():
                left = s.add(item, left)

    def _drop_one(self):
        slot = self.hotbar[self.sel]
        if slot.empty():
            return
        if self.game_mode == "client" and self.client.connected:
            self._send_drop_item(slot.item.name, 1,
                                 self.px + random.uniform(-20, 20),
                                 self.py + random.uniform(-20, 20))
            slot.take(1)
            return
        drop_x = self.px + random.uniform(-20, 20)
        drop_y = self.py + random.uniform(-20, 20)
        self.dropped_items.append(DroppedItem(drop_x, drop_y, slot.item, 1))
        slot.take(1)

    def _drop_full_stack(self):
        slot = self.hotbar[self.sel]
        if slot.empty():
            return
        if self.game_mode == "client" and self.client.connected:
            self._send_drop_item(slot.item.name, slot.count,
                                 self.px + random.uniform(-20, 20),
                                 self.py + random.uniform(-20, 20))
            slot.item = None
            slot.count = 0
            return
        drop_x = self.px + random.uniform(-20, 20)
        drop_y = self.py + random.uniform(-20, 20)
        self.dropped_items.append(DroppedItem(drop_x, drop_y, slot.item, slot.count))
        slot.item = None
        slot.count = 0

    def _click_dropped_item(self, pos):
        wx = pos[0] + self.cam_x
        wy = pos[1] + self.cam_y
        for i, dropped in enumerate(self.dropped_items):
            dist = math.sqrt((wx - dropped.x) ** 2 + (wy - dropped.y) ** 2)
            if dist < 40:
                if self.game_mode == "client" and self.client.connected:
                    did = getattr(dropped, "drop_id", None)
                    if did is not None:
                        self._send_pickup(did)
                        return True
                self._pickup(dropped.item, dropped.count)
                self.dropped_items.pop(i)
                return True
        return False

    def _eat_food(self):
        slot = self.hotbar[self.sel]
        if slot.empty() or not slot.item.is_food:
            return False
        food_val = slot.item.food_value
        self.hunger = min(100, self.hunger + food_val)
        slot.take(1)
        return True

    def _attack_zombie(self, pos):
        if self.drone_mode:
            return False
        if not self._check_distance(pos):
            return False
        wx = pos[0] + self.cam_x
        wy = pos[1] + self.cam_y
        slot = self.hotbar[self.sel]
        damage = 2 if (not slot.empty() and slot.item.name == "Меч") else 1
        for i, zombie in enumerate(self.zombies):
            dist = math.sqrt((wx - zombie.x) ** 2 + (wy - zombie.y) ** 2)
            if dist < 40:
                if self.game_mode == "client" and self.client.connected:
                    self._send_attack(getattr(zombie, "zid", None), damage)
                    return True
                if zombie.take_damage(damage):
                    self.zombies.pop(i)
                return True
        return False

    def _can_craft(self, recipe):
        for name, need in recipe["in"].items():
            if self._count_item(name) < need:
                return False
        return True

    def _do_craft(self, recipe):
        for name, need in recipe["in"].items():
            left = need
            for s in self._all_slots():
                if left <= 0:
                    break
                if not s.empty() and s.item.name == name:
                    take = min(left, s.count)
                    s.count -= take
                    left -= take
                    if s.count <= 0:
                        s.item = None
                        s.count = 0
        out_name, out_count = recipe["out"]
        out_item = self.ALL_ITEMS.get(out_name)
        if out_item is None:
            return
        self._pickup(out_item, out_count)

    def _hotbar_rect(self, i):
        total_w = NUM_SLOTS * (SLOT_SIZE + SLOT_PAD) - SLOT_PAD
        ox = (W - total_w) // 2
        oy = H - SLOT_SIZE - 10
        return pygame.Rect(ox + i * (SLOT_SIZE + SLOT_PAD), oy, SLOT_SIZE, SLOT_SIZE)

    def _inv_rect(self, idx):
        slot_size = 40
        slot_pad = 4
        inv_width = 500
        inv_height = 350
        inv_x = (W - inv_width) // 2
        inv_y = (H - inv_height) // 2
        start_x = inv_x + 10
        start_y = inv_y + 40
        row = idx // NUM_SLOTS
        col = idx % NUM_SLOTS
        x = start_x + col * (slot_size + slot_pad)
        y = start_y + row * (slot_size + slot_pad)
        return pygame.Rect(x, y, slot_size, slot_size)

    def _handle_inv_click(self, pos, button, shift):
        if button != 1:
            return
        for i in range(len(self.inventory)):
            if self._inv_rect(i).collidepoint(pos):
                self._slot_click(self.inventory[i], self.inventory, shift)
                return
        for i in range(NUM_SLOTS):
            if self._hotbar_rect(i).collidepoint(pos):
                self._slot_click(self.hotbar[i], self.hotbar, shift)
                return
        inv_width = 500
        inv_height = 350
        inv_x = (W - inv_width) // 2
        inv_y = (H - inv_height) // 2
        recipe_x = inv_x + inv_width - 200
        recipe_y = inv_y + 35
        available_recipes = [r for r in self.RECIPES if self._can_craft(r)]
        for i, recipe in enumerate(available_recipes):
            recipe_rect = pygame.Rect(recipe_x, recipe_y + i * 45, 190, 40)
            if recipe_rect.collidepoint(pos):
                if self._can_craft(recipe):
                    self._do_craft(recipe)
                return

    def _slot_click(self, slot, owner, shift):
        if shift:
            target = self.inventory if owner is self.hotbar else self.hotbar
            if slot.empty():
                return
            for s in target:
                if not s.empty() and s.item.name == slot.item.name and s.count < 64:
                    space = 64 - s.count
                    take = min(slot.count, space)
                    s.count += take
                    slot.count -= take
                    if slot.count <= 0:
                        slot.item = None
                        slot.count = 0
                    return
            for s in target:
                if s.empty():
                    s.item = slot.item
                    s.count = slot.count
                    slot.item = None
                    slot.count = 0
                    return
        else:
            if self.drag_item is None:
                if not slot.empty():
                    self.drag_item = slot.item
                    self.drag_count = slot.count
                    slot.item = None
                    slot.count = 0
            else:
                if slot.empty():
                    slot.item = self.drag_item
                    slot.count = self.drag_count
                    self.drag_item = None
                    self.drag_count = 0
                elif slot.item.name == self.drag_item.name:
                    space = 64 - slot.count
                    take = min(self.drag_count, space)
                    slot.count += take
                    self.drag_count -= take
                    if self.drag_count <= 0:
                        self.drag_item = None
                        self.drag_count = 0
                else:
                    old_item, old_count = slot.item, slot.count
                    slot.item = self.drag_item
                    slot.count = self.drag_count
                    self.drag_item = old_item
                    self.drag_count = old_count
