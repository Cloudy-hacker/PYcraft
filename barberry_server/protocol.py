# -*- coding: utf-8 -*-
"""
Протокол: одно сообщение = одна JSON-строка, завершённая \n
"""
import json

def encode_message(data):
    return json.dumps(data, ensure_ascii=False).encode('utf-8') + b"\n"

def decode_message(line):
    return json.loads(line.decode('utf-8'))
