# -*- coding: utf-8 -*-
import math

class Zombie:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.hp = 10
        self.speed = 60
        self.attack_cooldown = 0
        self.damage = 10
        self.burn_timer = 0.0

    def update(self, dt, player_x, player_y, game):
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        if dist > 0:
            dir_x = dx / dist
            dir_y = dy / dist
            directions = [(dir_x, dir_y), (dir_x + dir_y, dir_y - dir_x), 
                          (dir_x - dir_y, dir_y + dir_x), (-dir_x, dir_y), (dir_x, -dir_y)]
            best_dir = None
            best_score = float('inf')
            for test_dx, test_dy in directions:
                length = math.sqrt(test_dx*test_dx + test_dy*test_dy)
                if length == 0: continue
                test_dx /= length
                test_dy /= length
                test_x = self.x + test_dx * self.speed * dt
                test_y = self.y + test_dy * self.speed * dt
                if not game._check_zombie_collision(test_x, test_y):
                    score = math.sqrt((test_x - player_x)**2 + (test_y - player_y)**2)
                    if score < best_score:
                        best_score = score
                        best_dir = (test_dx, test_dy)
            if best_dir:
                self.x += best_dir[0] * self.speed * dt
                self.y += best_dir[1] * self.speed * dt
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt

    def take_damage(self, amount):
        self.hp -= amount
        return self.hp <= 0
