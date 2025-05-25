#!/bin/python3
import sys
import os
import math
import struct

def ReadText(file_name):
    try:
        with open(file_name, "rb") as file:
            return file.read()
    except FileNotFoundError:
        print("Файл не найден")
        exit(0)


def compress(data, search_buffer_size=4096, lookahead_buffer_size=64):
    compressed = bytearray()
    search_buffer = bytearray()
    data = bytearray(data)
    tokens = []

    while len(data) > 0:
        lookahead_buffer = data[:lookahead_buffer_size]
        best_offset = 0
        best_length = 0
        best_char = lookahead_buffer[0] if len(lookahead_buffer) > 0 else 0

        # Поиск наилучшего совпадения в буфере поиска
        for offset in range(1, min(len(search_buffer), search_buffer_size) + 1):
            length = 0
            while (
                length < len(lookahead_buffer)
                and length < lookahead_buffer_size
                and offset + length <= len(search_buffer)
                and search_buffer[-offset + length] == lookahead_buffer[length]
            ):
                length += 1

            if length > best_length or (length == best_length and offset < best_offset):
                best_length = length
                best_offset = offset
                if length < len(lookahead_buffer):
                    best_char = lookahead_buffer[length]
                else:
                    best_char = 0

        # Сохраняем токен (offset, length, char)
        if best_length >= 3:
            tokens.append((best_offset, best_length, best_char))
            move_length = best_length + 1
        else:
            tokens.append((0, 0, lookahead_buffer[0]))
            move_length = 1

        # Обновляем буферы
        search_buffer.extend(lookahead_buffer[:move_length])
        if len(search_buffer) > search_buffer_size:
            search_buffer = search_buffer[-search_buffer_size:]
        data = data[move_length:]

    # Определяем минимальное количество бит для чисел
    max_offset = max(t[0] for t in tokens)
    max_length = max(t[1] for t in tokens)

    offset_bits = max(1, math.ceil(math.log2(max_offset + 1))
                      ) if max_offset > 0 else 1
    length_bits = max(1, math.ceil(math.log2(max_length + 1))
                      ) if max_length > 0 else 1

    # Записываем заголовок (биты для offset и length)
    compressed.append(offset_bits)
    compressed.append(length_bits)

    # Кодируем токены
    bit_buffer = []
    for offset, length, char in tokens:
        # Кодируем offset
        if offset_bits > 0:
            bits = bin(offset)[2:].zfill(offset_bits)
            bit_buffer.extend([int(b) for b in bits])

        # Кодируем length
        if length_bits > 0:
            bits = bin(length)[2:].zfill(length_bits)
            bit_buffer.extend([int(b) for b in bits])

        # Кодируем char (8 бит)
        bits = bin(char)[2:].zfill(8)
        bit_buffer.extend([int(b) for b in bits])

    # Упаковываем биты в байты
    for i in range(0, len(bit_buffer), 8):
        byte_bits = bit_buffer[i: i + 8]
        byte_str = "".join(map(str, byte_bits))
        byte = int(byte_str, 2)
        compressed.append(byte)

    return compressed


def decompress(compressed_data):
    if len(compressed_data) < 2:
        return bytearray()

    # Читаем заголовок
    offset_bits = compressed_data[0]
    length_bits = compressed_data[1]
    data = compressed_data[2:]

    # Преобразуем байты в биты
    bit_buffer = []
    for byte in data:
        bits = bin(byte)[2:].zfill(8)
        bit_buffer.extend([int(b) for b in bits])

    # Читаем токены
    tokens = []
    token_size = offset_bits + length_bits + 8
    i = 0
    while i + token_size <= len(bit_buffer):
        # Читаем offset
        offset_bits_part = bit_buffer[i: i + offset_bits]
        offset = int("".join(map(str, offset_bits_part)),
                     2) if offset_bits > 0 else 0
        i += offset_bits

        # Читаем length
        length_bits_part = bit_buffer[i: i + length_bits]
        length = int("".join(map(str, length_bits_part)),
                     2) if length_bits > 0 else 0
        i += length_bits

        # Читаем char
        char_bits_part = bit_buffer[i: i + 8]
        char = int("".join(map(str, char_bits_part)), 2)
        i += 8

        tokens.append((offset, length, char))

    # Восстанавливаем данные
    decompressed = bytearray()
    for offset, length, char in tokens:
        if offset == 0 and length == 0:
            decompressed.append(char)
        else:
            start = len(decompressed) - offset
            for j in range(length):
                if start + j >= 0 and start + j < len(decompressed):
                    decompressed.append(decompressed[start + j])
                else:
                    decompressed.append(32)  # Запасной вариант (пробел)
            decompressed.append(char)

    return decompressed


if __name__ == "__main__":
    text = list(ReadText(sys.argv[2]))
    if sys.argv[1] == "decompress":
        with open(sys.argv[3], "wb") as decompressFile:
            decompressFile.write(decompress(text))
    elif sys.argv[1] == "compress":
        with open(sys.argv[3], "wb") as compressFile:
            compressFile.write(compress(text))
    else:
        print("Не известная команда")
