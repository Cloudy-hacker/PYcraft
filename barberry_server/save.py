# -*- coding: utf-8 -*-
"""
Сохранение миров + выброшенных предметов. Пустой мир не затирает файл.
"""
import os
import json


class SaveManager:
    def __init__(self, worlds_dir="worlds"):
        self.worlds_dir = worlds_dir
        if not os.path.exists(worlds_dir):
            os.makedirs(worlds_dir)

    def save_world(self, world, name):
        if not world.tiles and not world.doors:
            print("[Save] ВНИМАНИЕ: мир '{}' пуст, сохранение ПРОПУЩЕНО (файл не затёрт)".format(name))
            return False
        path = os.path.join(self.worlds_dir, "{}.json".format(name))
        data = {
            "tiles": {"{},{}".format(k[0], k[1]): v for k, v in world.tiles.items()},
            "doors": {"{},{}".format(k[0], k[1]): v for k, v in world.doors.items()},
            "drops": world.drops,
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        print("[Save] Мир '{}' сохранён: {} (дроп: {})".format(name, path, len(world.drops)))
        return True

    def load_world(self, name):
        from world import World
        path = os.path.join(self.worlds_dir, "{}.json".format(name))
        w = World()
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for k, v in data.get("tiles", {}).items():
                    tx, ty = map(int, k.split(","))
                    w.tiles[(tx, ty)] = v
                for k, v in data.get("doors", {}).items():
                    tx, ty = map(int, k.split(","))
                    w.doors[(tx, ty)] = v
                w.drops = data.get("drops", [])
                print("[Save] Мир '{}' загружен: {} тайлов, {} дропа".format(name, len(w.tiles), len(w.drops)))
            except Exception as e:
                print("[Save] Ошибка чтения {}: {}".format(path, e))
        else:
            print("[Save] Файл мира '{}' не найден, создан пустой".format(name))
        return w
