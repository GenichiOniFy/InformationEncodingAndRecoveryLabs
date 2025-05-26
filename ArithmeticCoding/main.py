#!/bin/python3

import os
import sys
from collections import defaultdict

# Количество бит для целочисленного представления (для работы с целыми числами вместо дробных)
PRECISION = 32


def calculate_frequencies(data):
    """Вычисление частот символов в данных (вероятностная модель)"""
    freq = defaultdict(int)
    for byte in data:
        freq[byte] += 1
    return freq


def normalize_frequencies(freq, total):
    """Нормализует частоты для работы с целыми числами (масштабирует к заданной точности)"""
    scale = (1 << PRECISION) // total  # Вычисляем масштабный коэффициент
    normalized = {}
    for byte, count in freq.items():
        # Гарантируем, что каждый символ имеет ненулевую частоту
        normalized[byte] = max(1, count * scale)
    return normalized


def build_probability_table(normalized_freq):
    """Строит таблицу вероятностей с целыми числами (разбивает интервал на подынтервалы)"""
    prob_table = []
    cumulative = 0
    # Сортируем символы и создаем таблицу с накопленными вероятностями
    for byte, weight in sorted(normalized_freq.items()):
        # (символ, нижняя граница, верхняя граница)
        prob_table.append((byte, cumulative, cumulative + weight))
        cumulative += weight
    # Возвращаем таблицу и общий вес (аналог суммы вероятностей)
    return prob_table, cumulative


def arithmetic_encode(data, prob_table, total_weight):
    """Целочисленное кодирование (реализация алгоритма арифметического кодирования)"""
    low = 0  # Нижняя граница интервала
    # Верхняя граница интервала (максимальное 32-битное число)
    high = (1 << PRECISION) - 1

    for byte in data:
        # Находим диапазон для текущего символа в таблице вероятностей
        b_high = 0
        b_low = 0
        for b, b_low, b_high in prob_table:
            if b == byte:
                break

        # Обновляем границы интервала (сужаем его)
        range_size = high - low + 1
        high = low + (range_size * b_high) // total_weight - 1
        low = low + (range_size * b_low) // total_weight

        # Масштабирование при переполнении (когда старшие биты low и high совпадают)
        while ((low ^ high) & (1 << (PRECISION - 1))) == 0:
            # Выводим старший бит (бит, который уже определился)
            yield (low >> (PRECISION - 1)) & 1
            # Сдвигаем границы (эквивалентно умножению на 2)
            low = (low << 1) & ((1 << PRECISION) - 1)
            high = ((high << 1) & ((1 << PRECISION) - 1)) | 1

    # Завершающие биты (выводим оставшиеся биты из low)
    yield (low >> (PRECISION - 1)) & 1
    for _ in range(PRECISION - 1):
        low = (low << 1) & ((1 << PRECISION) - 1)
        yield (low >> (PRECISION - 1)) & 1


def bits_to_bytes(bits):
    """Конвертирует биты в байты (упаковывает биты в байты для записи в файл)"""
    byte = 0
    count = 0
    for bit in bits:
        byte = (byte << 1) | bit
        count += 1
        if count == 8:
            yield byte
            byte = 0
            count = 0
    if count > 0:  # Дописываем оставшиеся биты
        yield byte << (8 - count)


def compress(input_file, output_file):
    """Сжатие с целочисленной арифметикой"""
    with open(input_file, "rb") as f:
        data = f.read()

    # 1. Строим вероятностную модель (частоты символов)
    freq = calculate_frequencies(data)
    total = len(data)

    # 2. Нормализуем частоты для работы с целыми числами
    normalized_freq = normalize_frequencies(freq, total)

    # 3. Строим таблицу вероятностей (разбиваем интервал на подынтервалы)
    prob_table, total_weight = build_probability_table(normalized_freq)

    # Записываем заголовок сжатого файла
    with open(output_file, "wb") as f:
        # Длина исходных данных (4 байта)
        f.write(total.to_bytes(4, "big"))
        # Количество уникальных символов (1 байт)
        f.write(len(freq).to_bytes(1, "big"))
        # Таблица частот (символ + частота, 3 байта на символ)
        for byte, count in sorted(freq.items()):
            f.write(bytes([byte]))
            f.write(count.to_bytes(2, "big"))

        # 4. Кодируем данные с помощью арифметического кодирования
        bits = arithmetic_encode(data, prob_table, total_weight)
        bytes_data = bits_to_bytes(bits)

        # Записываем сжатые данные
        buffer = bytearray()
        for byte in bytes_data:
            buffer.append(byte)
            if len(buffer) >= 4096:  # Буферизация для эффективной записи
                f.write(buffer)
                buffer.clear()
        if buffer:
            f.write(buffer)

    # Вычисляем степень сжатия
    orig_size = os.path.getsize(input_file)
    comp_size = os.path.getsize(output_file)
    print(f"Степень сжатия: {orig_size/comp_size:.2f}")


def arithmetic_decode(input_file, output_file):
    """Декодирование с целочисленной арифметикой"""
    with open(input_file, "rb") as f:
        # Читаем заголовок
        total = int.from_bytes(f.read(4), "big")  # Длина исходных данных
        # Количество уникальных символов
        num_symbols = int.from_bytes(f.read(1), "big")

        # Восстанавливаем частоты символов
        freq = {}
        for _ in range(num_symbols):
            byte = ord(f.read(1))  # Символ
            count = int.from_bytes(f.read(2), "big")  # Его частота
            freq[byte] = count

        # Читаем сжатые данные и преобразуем в поток битов
        data = f.read()
        bit_stream = []
        for byte in data:
            for i in range(7, -1, -1):  # Разбираем каждый бит
                bit_stream.append((byte >> i) & 1)

    # Нормализуем частоты (как при кодировании)
    normalized_freq = normalize_frequencies(freq, total)
    prob_table, total_weight = build_probability_table(normalized_freq)

    # Инициализация декодера (аналогично кодировщику)
    low = 0
    high = (1 << PRECISION) - 1
    value = 0  # Здесь будем накапливать декодируемое значение

    # Читаем первые PRECISION бит для инициализации value
    for i in range(PRECISION):
        if bit_stream:
            value = (value << 1) | bit_stream.pop(0)
        else:
            value = value << 1

    # Декодирование
    with open(output_file, "wb") as f:
        for _ in range(total):  # Декодируем все символы
            # Находим текущий символ по положению value в интервале
            threshold = ((value - low + 1) * total_weight - 1) // (high - low + 1)

            # Ищем символ, чей интервал содержит threshold
            for byte, b_low, b_high in prob_table:
                if b_low <= threshold < b_high:
                    f.write(bytes([byte]))  # Записываем декодированный символ
                    # Обновляем диапазон (как при кодировании)
                    range_size = high - low + 1
                    high = low + (range_size * b_high) // total_weight - 1
                    low = low + (range_size * b_low) // total_weight
                    break

            # Масштабирование (аналогично кодировщику)
            while ((low ^ high) & (1 << (PRECISION - 1))) == 0:
                low = (low << 1) & ((1 << PRECISION) - 1)
                high = ((high << 1) & ((1 << PRECISION) - 1)) | 1
                # Читаем следующий бит в младший разряд value
                if bit_stream:
                    value = ((value << 1) & ((1 << PRECISION) - 1)) | bit_stream.pop(0)
                else:
                    value = (value << 1) & ((1 << PRECISION) - 1)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Использование:")
        print("  Сжатие:   python main.py compress input.txt output.bin")
        print("  Распаковка: python main.py decompress output.bin result.txt")
        sys.exit(1)

    command = sys.argv[1]
    input_file = sys.argv[2]
    output_file = sys.argv[3]

    if command == "compress":
        compress(input_file, output_file)
    elif command == "decompress":
        arithmetic_decode(input_file, output_file)
    else:
        print("Ошибка: используйте 'compress' или 'decompress'")
