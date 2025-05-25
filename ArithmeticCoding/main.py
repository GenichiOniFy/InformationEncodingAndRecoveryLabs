import math
import os
import sys
from collections import defaultdict

PRECISION = 32  # Количество бит для целочисленного представления


def calculate_frequencies(data):
    freq = defaultdict(int)
    for byte in data:
        freq[byte] += 1
    return freq


def normalize_frequencies(freq, total):
    """Нормализует частоты для работы с целыми числами"""
    scale = (1 << PRECISION) // total
    normalized = {}
    for byte, count in freq.items():
        normalized[byte] = max(1, count * scale)
    return normalized


def build_probability_table(normalized_freq):
    """Строит таблицу вероятностей с целыми числами"""
    prob_table = []
    cumulative = 0
    for byte, weight in sorted(normalized_freq.items()):
        prob_table.append((byte, cumulative, cumulative + weight))
        cumulative += weight
    return prob_table, cumulative


def arithmetic_encode(data, prob_table, total_weight):
    """Целочисленное кодирование"""
    low = 0
    high = (1 << PRECISION) - 1

    for byte in data:
        # Находим диапазон для текущего символа
        for b, b_low, b_high in prob_table:
            if b == byte:
                break

        # Обновляем границы
        range_size = high - low + 1
        high = low + (range_size * b_high) // total_weight - 1
        low = low + (range_size * b_low) // total_weight

        # Масштабирование при переполнении
        while ((low ^ high) & (1 << (PRECISION - 1))) == 0:
            yield (low >> (PRECISION - 1)) & 1
            low = (low << 1) & ((1 << PRECISION) - 1)
            high = ((high << 1) & ((1 << PRECISION) - 1)) | 1

    # Завершающие биты
    yield (low >> (PRECISION - 1)) & 1
    for _ in range(PRECISION - 1):
        low = (low << 1) & ((1 << PRECISION) - 1)
        yield (low >> (PRECISION - 1)) & 1


def bits_to_bytes(bits):
    """Конвертирует биты в байты"""
    byte = 0
    count = 0
    for bit in bits:
        byte = (byte << 1) | bit
        count += 1
        if count == 8:
            yield byte
            byte = 0
            count = 0
    if count > 0:
        yield byte << (8 - count)


def compress(input_file, output_file):
    """Сжатие с целочисленной арифметикой"""
    with open(input_file, "rb") as f:
        data = f.read()

    freq = calculate_frequencies(data)
    total = len(data)
    normalized_freq = normalize_frequencies(freq, total)
    prob_table, total_weight = build_probability_table(normalized_freq)

    # Записываем заголовок
    with open(output_file, "wb") as f:
        # Длина данных (4 байта)
        f.write(total.to_bytes(4, "big"))
        # Количество уникальных символов (1 байт)
        f.write(len(freq).to_bytes(1, "big"))
        # Таблица частот (символ + частота, 3 байта на символ)
        for byte, count in sorted(freq.items()):
            f.write(bytes([byte]))
            f.write(count.to_bytes(2, "big"))

        # Кодируем данные
        bits = arithmetic_encode(data, prob_table, total_weight)
        bytes_data = bits_to_bytes(bits)

        # Записываем сжатые данные
        buffer = bytearray()
        for byte in bytes_data:
            buffer.append(byte)
            if len(buffer) >= 4096:
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
        total = int.from_bytes(f.read(4), "big")
        num_symbols = int.from_bytes(f.read(1), "big")

        # Восстанавливаем частоты
        freq = {}
        for _ in range(num_symbols):
            byte = ord(f.read(1))
            count = int.from_bytes(f.read(2), "big")
            freq[byte] = count

        # Читаем сжатые данные
        data = f.read()
        bit_stream = []
        for byte in data:
            for i in range(7, -1, -1):
                bit_stream.append((byte >> i) & 1)

    # Нормализуем частоты
    normalized_freq = normalize_frequencies(freq, total)
    prob_table, total_weight = build_probability_table(normalized_freq)

    # Инициализация декодера
    low = 0
    high = (1 << PRECISION) - 1
    value = 0
    for i in range(PRECISION):
        if bit_stream:
            value = (value << 1) | bit_stream.pop(0)
        else:
            value = value << 1

    # Декодирование
    with open(output_file, "wb") as f:
        for _ in range(total):
            # Находим текущий символ
            threshold = ((value - low + 1) * total_weight -
                         1) // (high - low + 1)

            for byte, b_low, b_high in prob_table:
                if b_low <= threshold < b_high:
                    f.write(bytes([byte]))
                    # Обновляем диапазон
                    range_size = high - low + 1
                    high = low + (range_size * b_high) // total_weight - 1
                    low = low + (range_size * b_low) // total_weight
                    break

            # Масштабирование
            while ((low ^ high) & (1 << (PRECISION - 1))) == 0:
                low = (low << 1) & ((1 << PRECISION) - 1)
                high = ((high << 1) & ((1 << PRECISION) - 1)) | 1
                if bit_stream:
                    value = ((value << 1) & ((1 << PRECISION) - 1)
                             ) | bit_stream.pop(0)
                else:
                    value = (value << 1) & ((1 << PRECISION) - 1)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Использование:")
        print("  Сжатие:   python arith.py compress input.txt output.bin")
        print("  Распаковка: python arith.py decompress output.bin result.txt")
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
