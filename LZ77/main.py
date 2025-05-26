#!/bin/python3
import math
import os
import sys

# Функция для чтения текста из файла


def ReadText(file_name):
    try:
        with open(file_name, "rb") as file:
            return file.read()
    except FileNotFoundError:
        print("Файл не найден")
        exit(0)


# Функция сжатия данных по алгоритму LZ77


def compress(data, search_buffer_size=4096, lookahead_buffer_size=64):
    compressed = bytearray()  # Сжатые данные
    search_buffer = bytearray()  # Буфер поиска (уже обработанные данные)
    data = bytearray(data)  # Входные данные
    tokens = []  # Список токенов (смещение, длина, следующий символ)

    while len(data) > 0:
        # Берем часть данных для поиска совпадений (упреждающий буфер)
        lookahead_buffer = data[:lookahead_buffer_size]
        best_offset = 0  # Лучшее найденное смещение
        best_length = 0  # Максимальная длина совпадения
        best_char = (
            lookahead_buffer[0] if len(lookahead_buffer) > 0 else 0
        )  # Следующий символ

        # Поиск наилучшего совпадения в буфере поиска
        for offset in range(1, min(len(search_buffer), search_buffer_size) + 1):
            length = 0
            # Проверяем совпадения символов
            while (
                length < len(lookahead_buffer)
                and length < lookahead_buffer_size
                and offset + length <= len(search_buffer)
                and search_buffer[-offset + length] == lookahead_buffer[length]
            ):
                length += 1

            # Обновляем лучший результат, если нашли более длинное совпадение
            # или такое же, но с меньшим смещением
            if length > best_length or (length == best_length and offset < best_offset):
                best_length = length
                best_offset = offset
                if length < len(lookahead_buffer):
                    best_char = lookahead_buffer[length]
                else:
                    best_char = 0

        # Формируем токен (смещение, длина, следующий символ)
        if best_length >= 3:  # Если совпадение достаточно длинное
            tokens.append((best_offset, best_length, best_char))
            move_length = (
                best_length + 1
            )  # Сдвигаем окно на длину совпадения + 1 символ
        else:  # Если совпадений нет
            tokens.append((0, 0, lookahead_buffer[0]))
            move_length = 1  # Сдвигаем окно на 1 символ

        # Обновляем буферы
        search_buffer.extend(lookahead_buffer[:move_length])
        if len(search_buffer) > search_buffer_size:
            # Поддерживаем размер буфера
            search_buffer = search_buffer[-search_buffer_size:]
        data = data[move_length:]  # Удаляем обработанные данные

    # Определяем минимальное количество бит для чисел
    max_offset = max(t[0] for t in tokens)
    max_length = max(t[1] for t in tokens)

    # Вычисляем необходимое количество бит для хранения смещения и длины
    offset_bits = max(1, math.ceil(math.log2(max_offset + 1))) if max_offset > 0 else 1
    length_bits = max(1, math.ceil(math.log2(max_length + 1))) if max_length > 0 else 1

    # Записываем заголовок (биты для offset и length)
    compressed.append(offset_bits)
    compressed.append(length_bits)

    # Кодируем токены в биты
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

        # Кодируем char (всегда 8 бит)
        bits = bin(char)[2:].zfill(8)
        bit_buffer.extend([int(b) for b in bits])

    # Упаковываем биты в байты
    for i in range(0, len(bit_buffer), 8):
        byte_bits = bit_buffer[i : i + 8]
        byte_str = "".join(map(str, byte_bits))
        byte = int(byte_str, 2)
        compressed.append(byte)

    return compressed


# Функция распаковки данных


def decompress(compressed_data):
    if len(compressed_data) < 2:
        return bytearray()

    # Читаем заголовок (количество бит для смещения и длины)
    offset_bits = compressed_data[0]
    length_bits = compressed_data[1]
    data = compressed_data[2:]  # Остальные данные

    # Преобразуем байты в биты
    bit_buffer = []
    for byte in data:
        bits = bin(byte)[2:].zfill(8)
        bit_buffer.extend([int(b) for b in bits])

    # Читаем токены
    tokens = []
    token_size = offset_bits + length_bits + 8  # Размер одного токена в битах
    i = 0
    while i + token_size <= len(bit_buffer):
        # Читаем смещение
        offset_bits_part = bit_buffer[i : i + offset_bits]
        offset = int("".join(map(str, offset_bits_part)), 2) if offset_bits > 0 else 0
        i += offset_bits

        # Читаем длину
        length_bits_part = bit_buffer[i : i + length_bits]
        length = int("".join(map(str, length_bits_part)), 2) if length_bits > 0 else 0
        i += length_bits

        # Читаем символ
        char_bits_part = bit_buffer[i : i + 8]
        char = int("".join(map(str, char_bits_part)), 2)
        i += 8

        tokens.append((offset, length, char))

    # Восстанавливаем оригинальные данные
    decompressed = bytearray()
    for offset, length, char in tokens:
        if offset == 0 and length == 0:  # Если совпадений не было
            decompressed.append(char)
        else:
            start = len(decompressed) - offset  # Начало совпадения
            for j in range(length):  # Копируем совпадающие символы
                if start + j >= 0 and start + j < len(decompressed):
                    decompressed.append(decompressed[start + j])
                else:
                    decompressed.append(32)  # Запасной вариант (пробел)
            decompressed.append(char)  # Добавляем следующий символ

    return decompressed


# Основная часть программы
if __name__ == "__main__":
    text = list(ReadText(sys.argv[2]))  # Читаем входной файл
    if sys.argv[1] == "decompress":  # Режим распаковки
        with open(sys.argv[3], "wb") as decompressFile:
            decompressFile.write(decompress(text))
    elif sys.argv[1] == "compress":  # Режим сжатия
        with open(sys.argv[3], "wb") as compressFile:
            compressFile.write(compress(text))
        print(
            "Степень сжатия:",
            os.path.getsize(sys.argv[2]) / os.path.getsize(sys.argv[3]),
        )
    else:
        print("Не известная команда")
