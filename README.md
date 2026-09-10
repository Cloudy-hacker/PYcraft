Русский ниже
# 🍒 PYcraft 2.0 (Barberry)

2D sandbox with survival, crafting, and multiplayer elements. Built with Python + Pygame.
The main goal of this project is to create a game that runs **even on a calculator**:
full support for 32-bit systems, old Linux distributions, and weak laptops from the 2010s.

> **Developers:** Клауди (Cloudy) and AI co-author Нексус (Nexus)
> **Engine:** Python 3.5+ / Pygame
> **Status:** Pre-Alpha / Beta

---

## 🚀 How to Run

### Client (Game)
1. Install Python 3.5 or newer.
2. Install Pygame library: `pip install pygame`
3. Run `main.py` (or use `loader.py` for auto-installation).
4. In the menu, select "Single Player" or "Multiplayer".

### Server (Barberry Server)
1. Go to the `barberry_server` folder.
2. Run `server.py`.
3. In the game, enter the server IP (default `127.0.0.1` if playing on the same PC).

---

## 🎮 Controls
- **WASD / Arrow Keys** — movement
- **LMB** — break blocks / attack
- **RMB** — place blocks / eat / open doors
- **E** — inventory / close Dev menu
- **F** — drone mode (free camera)
- **F2** — toggle sprites
- **F3** — debug info (FPS, coordinates)
- **T** — chat
- **Q** — drop item (Ctrl+Q — drop entire stack)
- **ESC** — exit / menu

---

## ✅ What Works in v0.2
- ✅ Stable multiplayer (movement, blocks, doors synchronized)
- ✅ World, position, and inventory saving on server
- ✅ Server-side zombie simulation (spawn at night, burn during day, attack players)
- ✅ Global chat and server commands (`/op`, `/kick`, `/ban`, `/save`, `/stop`)
- ✅ Dev cubes available only to operators (dupe protection)
- ✅ Proper client disconnection when server shuts down

## 🐛 Known Issues
- Whitelist currently works only through manual config editing (commands in development).
- Zombies and dropped items are synchronized, but there may be slight delays on weak internet.
- The game is in active development, bugs are possible.

---

## 📜 License
The project is distributed under the MIT License. See [LICENSE](LICENSE) file for details.

---

---

# 🍒 PYcraft 2.0 (Barberry)

2D-песочница с элементами выживания, крафта и мультиплеера. Написана на Python + Pygame.
Главная цель проекта — сделать игру, которая запустится **даже на калькуляторе**:
полная поддержка 32-битных систем, старых Linux и слабых ноутбуков из 2010-х.

> **Разработчики:** Клауди (Cloudy) и ИИ-соавтор Нексус (Nexus)
> **Движок:** Python 3.5+ / Pygame
> **Статус:** Pre-Alpha / Beta

---

## 🚀 Как запустить

### Клиент (Игра)
1. Установи Python 3.5 или новее.
2. Установи библиотеку Pygame: `pip install pygame`
3. Запусти `main.py` (или используй `loader.py` для автоустановки).
4. В меню выбери "Одиночная игра" или "Мультиплеер".

### Сервер (Barberry Server)
1. Перейди в папку `barberry_server`.
2. Запусти `server.py`.
3. В игре введи IP сервера (по умолчанию `127.0.0.1`, если играешь на том же ПК).

---

## 🎮 Управление
- **WASD / Стрелки** — движение
- **ЛКМ** — ломать блоки / атаковать
- **ПКМ** — ставить блоки / есть / открывать двери
- **E** — инвентарь / закрыть Dev-меню
- **F** — режим дрона (свободная камера)
- **F2** — переключить спрайты
- **F3** — отладочная информация (FPS, координаты)
- **T** — чат
- **Q** — выбросить предмет (Ctrl+Q — весь стак)
- **ESC** — выход / меню

---

## ✅ Что работает в v0.2
- ✅ Стабильный мультиплеер (движение, блоки, двери синхронизированы)
- ✅ Сохранение мира, позиций и инвентаря на сервере
- ✅ Серверный симулятор зомби (спавнятся ночью, горят днём, атакуют игроков)
- ✅ Общий чат и серверные команды (`/op`, `/kick`, `/ban`, `/save`, `/stop`)
- ✅ Dev-кубы доступны только операторам (защита от дюпа)
- ✅ Корректное отключение клиентов при выключении сервера

## 🐛 Известные проблемы
- Whitelist (белый список) пока работает только через ручное редактирование конфигов (команды в разработке).
- Зомби и выброшенные предметы синхронизируются, но могут быть небольшие задержки на слабом интернете.
- Игра находится в активной разработке, возможны баги.

---

## 📜 Лицензия
Проект распространяется под лицензией MIT. См. файл [LICENSE](LICENSE) для подробностей.
