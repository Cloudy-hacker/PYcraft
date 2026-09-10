# -*- coding: utf-8 -*-
import pygame, os
from constants import *

def load_sprite(name, size=32):
    path = os.path.join("sprites", name)
    if os.path.exists(path):
        try:
            img = pygame.image.load(path).convert_alpha()
            return pygame.transform.scale(img, (size, size))
        except Exception:
            pass
    return None

def check_custom_sprites():
    for f in ["tree.png", "stone.png", "wall.png", "player.png"]:
        if os.path.exists(os.path.join("sprites", f)):
            return True
    return False

def invert_surface(surface):
    inverted = surface.copy()
    inverted.fill((255, 255, 255, 255), None, pygame.BLEND_RGB_SUB)
    return inverted

def draw_player_sprite(phase=0, color=C_PLAYER, color_dark=C_PLAYER_DARK):
    s = pygame.Surface((32,32), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (40,60,30), (8,26,16,6))
    if phase==0:
        pygame.draw.rect(s, color_dark, (10,20,4,8))
        pygame.draw.rect(s, color_dark, (18,22,4,6))
    else:
        pygame.draw.rect(s, color_dark, (10,22,4,6))
        pygame.draw.rect(s, color_dark, (18,20,4,8))
    pygame.draw.rect(s, color, (8,10,16,14))
    pygame.draw.rect(s, color_dark, (8,10,4,14))
    pygame.draw.circle(s, (220,180,150), (16,10), 6)
    pygame.draw.circle(s, (0,0,0), (18,9), 1)
    return s

def draw_tree():
    s = pygame.Surface((32,32), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (40,60,30), (4,24,24,8))
    pygame.draw.rect(s, C_TRUNK, (12,14,8,12))
    pygame.draw.rect(s, C_TRUNK_DARK, (12,14,2,12))
    pygame.draw.circle(s, C_TREE_DARK, (16,14), 11)
    pygame.draw.circle(s, C_TREE, (14,12), 9)
    pygame.draw.circle(s, C_TREE_LIGHT, (18,10), 7)
    return s

def draw_stone():
    s = pygame.Surface((32,32), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (40,60,30), (2,26,28,6))
    pygame.draw.polygon(s, C_STONE, [(4,24),(10,6),(26,8),(28,22),(14,28)])
    pygame.draw.polygon(s, C_STONE_LIGHT, [(10,6),(26,8),(20,16),(12,14)])
    pygame.draw.polygon(s, C_STONE_DARK, [(4,24),(14,28),(28,22),(20,16)])
    return s

def draw_wall():
    s = pygame.Surface((32,32), pygame.SRCALPHA)
    pygame.draw.rect(s, C_WALL, (1,1,30,30))
    for i in range(3):
        y = 8+i*8
        pygame.draw.line(s, C_WALL_DARK, (2,y), (29,y), 1)
        pygame.draw.circle(s, (80,60,40), (6,y), 1)
        pygame.draw.circle(s, (80,60,40), (25,y), 1)
    pygame.draw.rect(s, C_WALL_DARK, (1,1,30,30), 2)
    return s

def draw_foundation():
    s = pygame.Surface((32,32), pygame.SRCALPHA)
    pygame.draw.rect(s, C_FOUND, (1,1,30,30))
    pygame.draw.line(s, C_FOUND_DARK, (5,5), (15,15), 1)
    pygame.draw.line(s, C_FOUND_DARK, (20,10), (25,20), 1)
    pygame.draw.circle(s, (100,100,110), (8,22), 2)
    pygame.draw.circle(s, (100,100,110), (22,8), 2)
    pygame.draw.rect(s, C_FOUND_DARK, (1,1,30,30), 2)
    return s

def draw_dev():
    s = pygame.Surface((32,32), pygame.SRCALPHA)
    for i in range(10):
        c = (255-i*5, 100+i*10, 255-i*5)
        pygame.draw.rect(s, c, (2+i,2+i,28-i*2,28-i*2))
    pygame.draw.rect(s, C_DEV_DARK, (2,2,28,28), 2)
    f = pygame.font.Font(None, 14)
    s.blit(f.render("DEV", True, (255,255,0)), (6,10))
    return s

def draw_fast_dev():
    return invert_surface(draw_dev())

def draw_zombie():
    s = pygame.Surface((32,32), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (30,50,30), (8,26,16,6))
    pygame.draw.rect(s, C_ZOMBIE_DARK, (10,20,4,8))
    pygame.draw.rect(s, C_ZOMBIE_DARK, (18,20,4,8))
    pygame.draw.rect(s, C_ZOMBIE, (8,10,16,14))
    pygame.draw.circle(s, C_ZOMBIE_DARK, (16,10), 6)
    pygame.draw.circle(s, (0,0,0), (14,9), 1)
    pygame.draw.circle(s, (0,0,0), (18,9), 1)
    return s

def draw_berry():
    s = pygame.Surface((32,32), pygame.SRCALPHA)
    pygame.draw.circle(s, C_BERRY, (12,16), 4)
    pygame.draw.circle(s, C_BERRY, (20,16), 4)
    pygame.draw.circle(s, C_BERRY, (16,12), 4)
    pygame.draw.circle(s, (150,30,30), (16,16), 6, 1)
    return s

def draw_door(closed=True):
    s = pygame.Surface((32,32), pygame.SRCALPHA)
    if closed:
        pygame.draw.rect(s, C_DOOR, (12, 2, 8, 28))
        pygame.draw.rect(s, C_DOOR_DARK, (12, 2, 2, 28))
        pygame.draw.circle(s, (200,180,100), (18, 16), 2)
    else:
        pygame.draw.rect(s, C_DOOR, (2, 12, 28, 8))
        pygame.draw.rect(s, C_DOOR_DARK, (2, 12, 28, 2))
        pygame.draw.circle(s, (200,180,100), (16, 18), 2)
    return s

def draw_wood_icon():
    s = pygame.Surface((24,24), pygame.SRCALPHA)
    pygame.draw.rect(s, C_TRUNK, (3,7,18,10))
    pygame.draw.circle(s, C_TRUNK_DARK, (6,12), 4)
    pygame.draw.circle(s, C_TRUNK_DARK, (18,12), 4)
    return s

def draw_stone_icon():
    s = pygame.Surface((24,24), pygame.SRCALPHA)
    pygame.draw.polygon(s, C_STONE, [(4,18),(8,6),(18,8),(20,16),(10,20)])
    pygame.draw.polygon(s, C_STONE_LIGHT, [(8,6),(18,8),(14,12),(10,10)])
    return s

def draw_wall_icon():
    s = pygame.Surface((24,24), pygame.SRCALPHA)
    pygame.draw.rect(s, C_WALL, (2,2,20,20))
    for i in range(2):
        y = 7+i*6
        pygame.draw.line(s, C_WALL_DARK, (3,y), (21,y), 1)
    return s

def draw_foundation_icon():
    s = pygame.Surface((24,24), pygame.SRCALPHA)
    pygame.draw.rect(s, C_FOUND, (2,2,20,20))
    pygame.draw.line(s, C_FOUND_DARK, (4,4), (10,10), 1)
    pygame.draw.line(s, C_FOUND_DARK, (14,8), (18,14), 1)
    return s

def draw_sword_icon():
    s = pygame.Surface((24,24), pygame.SRCALPHA)
    pygame.draw.line(s, (200,200,220), (12,4), (12,18), 3)
    pygame.draw.line(s, (150,150,170), (8,18), (16,18), 3)
    pygame.draw.rect(s, (100,80,60), (10,18,4,4))
    return s

def draw_axe_icon():
    s = pygame.Surface((24,24), pygame.SRCALPHA)
    pygame.draw.line(s, (120,80,40), (12,4), (12,20), 2)
    pygame.draw.polygon(s, (180,80,40), [(12,6),(18,8),(18,14),(12,12)])
    return s

def draw_pickaxe_icon():
    s = pygame.Surface((24,24), pygame.SRCALPHA)
    pygame.draw.line(s, (120,80,40), (6,18), (18,6), 2)
    pygame.draw.polygon(s, (100,100,180), [(6,6),(10,4),(12,8),(8,10)])
    return s

def draw_berry_icon():
    s = pygame.Surface((24,24), pygame.SRCALPHA)
    pygame.draw.circle(s, C_BERRY, (8,12), 4)
    pygame.draw.circle(s, C_BERRY, (16,12), 4)
    pygame.draw.circle(s, (150,30,30), (12,12), 6, 1)
    return s

def draw_door_icon():
    s = pygame.Surface((24,24), pygame.SRCALPHA)
    pygame.draw.rect(s, C_DOOR, (8, 2, 8, 20))
    pygame.draw.circle(s, (200,180,100), (14, 12), 1)
    return s

class Sprites:
    def __init__(self, use_custom=False):
        if use_custom:
            self.tree = load_sprite("tree.png") or draw_tree()
            self.stone = load_sprite("stone.png") or draw_stone()
            self.wall = load_sprite("wall.png") or draw_wall()
            self.foundation = load_sprite("foundation.png") or draw_foundation()
            self.dev = load_sprite("dev_cube.png") or draw_dev()
            self.fast_dev = load_sprite("fast_dev.png") or draw_fast_dev()
            self.zombie = load_sprite("zombie.png") or draw_zombie()
            self.berry = load_sprite("berry.png") or draw_berry()
            self.door_closed = load_sprite("door_closed.png") or draw_door(True)
            self.door_open = load_sprite("door_open.png") or draw_door(False)
            self.player = [load_sprite("player.png") or draw_player_sprite(0), load_sprite("player.png") or draw_player_sprite(1)]
            self.player2 = [load_sprite("player2.png") or draw_player_sprite(0, C_PLAYER2, C_PLAYER2_DARK), load_sprite("player2.png") or draw_player_sprite(1, C_PLAYER2, C_PLAYER2_DARK)]
        else:
            self.tree = draw_tree()
            self.stone = draw_stone()
            self.wall = draw_wall()
            self.foundation = draw_foundation()
            self.dev = draw_dev()
            self.fast_dev = draw_fast_dev()
            self.zombie = draw_zombie()
            self.berry = draw_berry()
            self.door_closed = draw_door(True)
            self.door_open = draw_door(False)
            self.player = [draw_player_sprite(0), draw_player_sprite(1)]
            self.player2 = [draw_player_sprite(0, C_PLAYER2, C_PLAYER2_DARK), draw_player_sprite(1, C_PLAYER2, C_PLAYER2_DARK)]
        
        self.wood = load_sprite("wood_icon.png", 24) or draw_wood_icon()
        self.stone_i = load_sprite("stone_icon.png", 24) or draw_stone_icon()
        self.wall_i = load_sprite("wall_icon.png", 24) or draw_wall_icon()
        self.found_i = load_sprite("foundation_icon.png", 24) or draw_foundation_icon()
        self.sword = load_sprite("sword.png", 24) or draw_sword_icon()
        self.axe = load_sprite("axe.png", 24) or draw_axe_icon()
        self.pick = load_sprite("pickaxe.png", 24) or draw_pickaxe_icon()
        self.berry_i = load_sprite("berry_icon.png", 24) or draw_berry_icon()
        self.door_i = load_sprite("door_icon.png", 24) or draw_door_icon()
