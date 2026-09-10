# -*- coding: utf-8 -*-
"""
Barberry Server 2.0 — точка входа с цветным ASCII-артом ягоды
"""

import asyncio
import json
import os
import hashlib
import sys
import time
from concurrent.futures import ThreadPoolExecutor

RED = "\033[91m"
DARK_RED = "\033[31m"
ORANGE = "\033[33m"
GREEN = "\033[92m"
DARK_GREEN = "\033[32m"
YELLOW = "\033[93m"
WHITE = "\033[97m"
BROWN = "\033[33m"
RESET = "\033[0m"
BOLD = "\033[1m"

BARBERRY_ART = f"""
{DARK_GREEN}          \\  |  /{RESET}
{DARK_GREEN}           \\ | /{RESET}
{GREEN}            \\|/{RESET}
{GREEN}             |{RESET}
{GREEN}            /|\\{RESET}
{RED}           ╭───╮{RESET}
{RED}          ╭┤{ORANGE}●{RED} ├╮{RESET}
{RED}         ╭┤{ORANGE}●●{RED} ├╮{RESET}
{RED}        ╭┤{ORANGE}●●●{RED} ├╮{RESET}
{RED}         ╰┤{ORANGE}●●{RED} ├╯{RESET}
{RED}          ┤{ORANGE}●{RED} ├╯{RESET}
{RED}           ╰───╯{RESET}
{DARK_RED}             |{RESET}
{DARK_RED}            /|\\{RESET}
{DARK_GREEN}           / | \\{RESET}
"""

BARBERRY_ART_SIMPLE = r"""
          \  |  /
           \ | /
            \|/
             |
            /|\
           ╭───╮
          ╭┤● ├╮
         ╭┤●● ├╮
        ╭┤●●● ├╮
         ╰┤●● ├╯
          ╰┤● ├╯
           ╰───╯
             |
            /|\
           / | \
"""

def get_art():
    try:
        import colorama
        colorama.init()
        return BARBERRY_ART
    except ImportError:
        if sys.platform == "win32":
            try:
                os.system('')
                return BARBERRY_ART
            except:
                return BARBERRY_ART_SIMPLE
        return BARBERRY_ART

def calculate_file_hash(filepath):
    try:
        with open(filepath, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    except:
        return None

def load_config():
    path = "config.json"
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "server_name": "Barberry local Server",
        "host": "0.0.0.0",
        "port": 54321,
        "max_players": 10,
        "world_size": 100,
        "tick_rate": 20,
        "save_interval": 120,
        "day_length": 420,
        "night_length": 420,
        "zombie_spawn_rate": 0.5,
        "max_zombies": 10,
        "online": False,
        "client_hash": ""
    }

def save_config(config):
    with open("config.json", 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

async def read_console_input(loop, executor):
    try:
        cmd = await loop.run_in_executor(executor, input, f"{YELLOW}[Console]{RESET} > ")
        return cmd
    except EOFError:
        return None
    except Exception as e:
        print(f"{RED}[Console Error] {e}{RESET}")
        return ""

async def console_loop(server, loop, executor):
    print(f"\n{GREEN}[Console] Готово к вводу команд. Введите /help для списка.{RESET}")
    while server.running:
        try:
            cmd = await read_console_input(loop, executor)
            if cmd is None:
                break
            cmd = cmd.strip()
            if cmd:
                server.execute_console_command(cmd)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"{RED}[Console Error] {e}{RESET}")
    print(f"\n{YELLOW}[Console] Консоль закрыта{RESET}")

async def main():
    if sys.platform == "win32":
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        except:
            pass
    
    print(get_art())
    print(f"{BOLD}{WHITE}Barberry Server v2.0{RESET}")
    print(f"{DARK_GREEN}Ягодное ядро для PYcraft{RESET}")
    print()
    print(f"{YELLOW}Загрузка конфигурации...{RESET}")
    config = load_config()
    
    if config.get("online", False) and not config.get("client_hash", ""):
        client_path = os.path.join("..", "game.py")
        if os.path.exists(client_path):
            h = calculate_file_hash(client_path)
            if h:
                config["client_hash"] = h
                save_config(config)
                print(f"{GREEN}[Config] client_hash автозаполнен: {h[:16]}...{RESET}")
        else:
            print(f"{ORANGE}[Config] WARNING: game.py не найден в папке выше{RESET}")
    
    from core import BarberryServer
    server = BarberryServer(config)
    
    loop = asyncio.get_event_loop()
    executor = ThreadPoolExecutor(max_workers=1)
    
    srv = await asyncio.start_server(
        server.network_handler.handle_client,
        config['host'],
        config['port']
    )
    server.running = True
    
    game_task = asyncio.create_task(server.game_loop())
    console_task = asyncio.create_task(console_loop(server, loop, executor))
    
    print(f"{WHITE}{'='*50}{RESET}")
    print(f"{GREEN}Название:{RESET} {config['server_name']}")
    print(f"{GREEN}Адрес:{RESET} {config['host']}:{config['port']}")
    print(f"{GREEN}Online mode:{RESET} {config.get('online', False)}")
    print(f"{GREEN}Max players:{RESET} {config.get('max_players', 10)}")
    print(f"{WHITE}{'='*50}{RESET}")
    print(f"{GREEN}[Core] Сервер запущен и готов к подключениям{RESET}")
    print(f"{YELLOW}[Core] Введите команду (например: /help){RESET}")
    
    try:
        await console_task
    except KeyboardInterrupt:
        print(f"\n{RED}[Server] Ctrl+C — остановка...{RESET}")
    finally:
        server.stop()
        executor.shutdown(wait=False)
        srv.close()
        await srv.wait_closed()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{RED}[Server] Завершение работы...{RESET}")
        sys.exit(0)
