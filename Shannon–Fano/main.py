#!/bin/python3
import sys

from Node import Node


def ReadText(file_name):
    try:
        with open(file_name, "rb") as file:
            return file.read()
    except FileNotFoundError:
        print("Файл не найден")
        exit(0)


def buildShannonFanoTree(frequencyDict):
    # Сортируем символы по убыванию частоты
    sorted_symbols = sorted(frequencyDict.items(), key=lambda x: -x[1])

    # Рекурсивно строим дерево
    def buildTree(symbols):
        if len(symbols) == 1:
            return Node(symbols[0][0], symbols[0][1])

        # Находим место для разделения
        total = sum(freq for _, freq in symbols)
        half = total / 2
        sum_freq = 0
        split_index = 0

        for i, (_, freq) in enumerate(symbols):
            sum_freq += freq
            if sum_freq >= half:
                split_index = i
                # Выбираем лучшее разделение - ближе к середине
                if i > 0 and abs(sum_freq - freq - half) < abs(sum_freq - half):
                    split_index = i - 1
                break

        # Разделяем на две части
        left_part = symbols[: split_index + 1]
        right_part = symbols[split_index + 1 :]

        # Создаем узел
        node = Node("", total)
        node.Left = buildTree(left_part)
        node.Right = buildTree(right_part)

        return node

    return buildTree(sorted_symbols)


def getCodes(node):
    global frequencyDict
    left = node.Left
    right = node.Right
    code_left = node.Value + "0"
    code_right = node.Value + "1"
    if left.Value != "":
        frequencyDict[left.Value] = code_left
    else:
        left.Value = code_left
        getCodes(left)
    if right.Value != "":
        frequencyDict[right.Value] = code_right
    else:
        right.Value = code_right
        getCodes(right)


def compress(frequencyDict, text):
    compr = ""
    for char in text:
        compr += frequencyDict[char]
    fr = ""
    maxLen = len(max(frequencyDict.values(), key=len))  # max_len_code
    colvoBitForLen = len(bin(maxLen)) - 2
    for char, value in frequencyDict.items():
        fr += f"{char:08b}"  # add symbol
        fr += bin(len(value))[2:].zfill(colvoBitForLen)  # len
        fr += value

    data = fr + compr
    if len(data) % 8 != 0:
        data += "0" * (8 - len(data) % 8)

    original_size = len(text)
    # +2 for lenDict and colvoBitForLen bytes
    compressed_size = len(data) // 8 + 2

    try:
        with open(sys.argv[3], "wb") as file:
            file.write(len(frequencyDict).to_bytes(1, "big"))
            file.write(colvoBitForLen.to_bytes(1, "big"))
            for i in range(0, len(data), 8):
                file.write(int(data[i : i + 8], 2).to_bytes(1, "big"))

        # Выводим статистику сжатия
        print(f"Размер исходного файла: {original_size} байт")
        print(f"Размер сжатого файла: {compressed_size} байт")
        if compressed_size > 0:
            compression_ratio = original_size / compressed_size
            print(f"Степень сжатия: {compression_ratio:.2f}")

        else:
            print("Невозможно вычислить степень сжатия (размер сжатого файла 0)")

    except Exception as e:
        print(f"Ошибка при сжатии: {e}")


def decompress(text):
    lenDict = text[0]
    colvoBitLenCode = text[1]
    text = "".join([bin(x)[2:].zfill(8) for x in text[2:]])
    dic = dict()
    for _ in range(lenDict):
        key = int(text[:8], 2)
        lenCode = int(text[8 : 8 + colvoBitLenCode], 2)
        value = text[8 + colvoBitLenCode : 8 + colvoBitLenCode + lenCode]
        text = text[8 + colvoBitLenCode + lenCode :]
        dic[value] = key
    try:
        with open(sys.argv[3], "wb") as file:
            while len(text) > 0:
                code = ""
                while code not in dic.keys():
                    code += text[0]
                    text = text[1:]
                file.write(dic[code].to_bytes(1, "big"))
    except Exception as e:
        print(f"Ошибка при распаковке: {e}")
        exit(0)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(
            "Использование: python main.py compress/decompress input_file output_file"
        )
        exit(1)

    text = ReadText(sys.argv[2])
    if sys.argv[1] == "decompress":
        decompress(text)
    elif sys.argv[1] == "compress":
        frequencyDict = {char: text.count(char) for char in set(text)}
        head = buildShannonFanoTree(frequencyDict)
        getCodes(head)
        compress(frequencyDict, text)
    else:
        print("Неизвестная команда. Используйте 'compress' или 'decompress'")
