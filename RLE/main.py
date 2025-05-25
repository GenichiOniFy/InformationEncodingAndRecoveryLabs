#!/bin/python3
import heapq
import sys


def ReadText(file_name):
    try:
        with open(file_name, "rb") as file:
            return file.read()
    except FileNotFoundError:
        print("Файл не найден")
        exit(0)


def compress(index, bwt):
    print(bwt)
    rle_encoded = []
    count = 1
    for i in range(1, len(bwt)):
        if bwt[i] == bwt[i - 1]:
            count += 1
        else:
            rle_encoded.append((bwt[i - 1], count))
            count = 1
    if (rle_encoded[-1][0]!=bwt[-1]):
        rle_encoded.append((bwt[-1], count))

    # index  colvoBitForLen
    # 1byte     1Byte
    print(rle_encoded)
    try:
        with open(sys.argv[3], "wb") as file:
            file.write(index.to_bytes(1, "big"))
            colvoBitForLen = len(bin(max([x for _, x in rle_encoded]))) - 2
            print(colvoBitForLen)
            file.write(colvoBitForLen.to_bytes(1, "big"))
            data = ""
            for byte, _len in rle_encoded:
                data += bin(byte)[2:].zfill(8)
                data += bin(_len)[2:].zfill(colvoBitForLen)
            if len(data) % 8 != 0:
                data += "0" * (8 - len(data) % 8)
            for i in range(0, len(data), 8):
                file.write(int(data[i : i + 8], 2).to_bytes(1, "big"))
    except:
        print("Что-то не так")

    # print(rle_encoded)


def decompress(text):
    bwt = []
    index = text[0]
    colvoBitForLen = text[1]
    text = "".join([bin(x)[2:].zfill(8) for x in text[2:]])
    while len(text) > 0:
        try:
            symbol = int(text[:8], 2)
            text = text[8:]
            _len = int(text[:colvoBitForLen], 2)
            text = text[colvoBitForLen:]
            for i in range(_len):
                bwt.append(symbol)
        except:
            break
    print(bwt, index)

    matrix = [b""] * len(bwt)
    for j in range(len(bwt) - 1, -1, -1):
        for i in range(len(bwt)):
            matrix[i] = bwt[i].to_bytes(1, "big") + matrix[i]
        matrix = sorted(matrix)
    print(matrix)
    original = matrix[index-1]
    with open(sys.argv[3], "wb") as file:
        for byte in original:
            file.write(byte.to_bytes(1, "big"))


def generate_cyclic_matrix(text):
    n = len(text)
    return [text[i:] + text[:i] for i in range(n)]


if __name__ == "__main__":
    text = list(ReadText(sys.argv[2]))
    if sys.argv[1] == "decompress":
        decompress(text)
        exit(0)
    elif sys.argv[1] == "compress":
        matrix = generate_cyclic_matrix(text)

        # Создаем список кортежей (строка, исходный индекс)
        indexed_matrix = [(row, i) for i, row in enumerate(matrix)]

        # Сортируем лексикографически
        sorted_matrix = sorted(indexed_matrix, key=lambda x: x[0])

        # Находим индекс исходной строки в отсортированном списке
        original_index = None
        for idx, (row, original_pos) in enumerate(sorted_matrix, 1):
            if original_pos == 0:  # Исходная строка имеет исходный индекс 0
                original_index = idx

        # Выводим отсортированную матрицу с нумерацией
        print("[")
        for idx, (row, original_pos) in enumerate(sorted_matrix, 1):
            print(f"{idx:2d} {row}")
        print("]")

        print(
            f"Исходная строка находится на позиции: {
                original_index}"
        )

        compress(original_index, [row[-1] for row, _ in sorted_matrix])
    else:
        print("Не известная команда")
