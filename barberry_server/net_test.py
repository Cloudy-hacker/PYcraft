# -*- coding: utf-8 -*-
"""
Самодиагностика сети PYcraft.
Консоль 1:  python net_test.py server
Консоль 2:  python net_test.py client
"""
import sys, socket, threading, json, time, asyncio

PORT = 54321

def encode(data):
    return json.dumps(data, ensure_ascii=False).encode('utf-8') + b"\n"

def decode(line):
    return json.loads(line.decode('utf-8'))

# ---------------- СЕРВЕР ----------------
async def handle(reader, writer):
    addr = writer.get_extra_info('peername')
    print("[test-server] подключился {}".format(addr))
    try:
        while True:
            line = await reader.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue
            msg = decode(line)
            print("[test-server] ПОЛУЧИЛ: {}".format(msg))
            if msg.get("type") == "move":
                writer.write(encode({"type": "player_update", "id": msg.get("id"), "x": msg.get("x"), "y": msg.get("y")}))
                await writer.drain()
                print("[test-server] отправил player_update обратно")
    except Exception as e:
        print("[test-server] ошибка: {}".format(e))
    print("[test-server] отключился {}".format(addr))

async def server_main():
    srv = await asyncio.start_server(handle, '0.0.0.0', PORT)
    print("[test-server] СЛУШАЮ ПОРТ {}".format(PORT))
    async with srv:
        await srv.serve_forever()

# ---------------- КЛИЕНТ ----------------
def client_main():
    s = socket.create_connection(('127.0.0.1', PORT), timeout=5)
    s.settimeout(0.2)
    f = s.makefile('rb')

    def recv_loop():
        while True:
            try:
                line = f.readline()
            except socket.timeout:
                continue
            except Exception as e:
                print("[test-client] ошибка приёма: {}".format(e))
                break
            if not line:
                print("[test-client] сервер закрыл соединение")
                break
            print("[test-client] ПОЛУЧИЛ: {}".format(decode(line.strip())))

    threading.Thread(target=recv_loop, daemon=True).start()
    s.sendall(encode({"type": "connect", "nickname": "Test"}))
    for i in range(10):
        time.sleep(0.5)
        s.sendall(encode({"type": "move", "id": 1, "x": 100 + i, "y": 200 + i}))
        print("[test-client] отправил move #{}".format(i))
    time.sleep(1)
    s.close()
    print("[test-client] готово, закрываюсь")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        loop = asyncio.get_event_loop()
        loop.run_until_complete(server_main())
    else:
        client_main()
