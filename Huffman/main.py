#!/bin/python3
import heapq
import sys

from Node import *


def ReadText(file_name):
    try:
        with open(file_name, "rb") as file:
            return file.read()
    except:
        print("Файл не найден")
        exit(0)


def buildHuffmanTree(frequencyDict):
    heap = [Node(char, freq) for char, freq in frequencyDict.items()]
    heapq.heapify(heap)

    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)

        newNode = Node("", left.Freq + right.Freq, left, right)
        heapq.heappush(heap, newNode)
    return heap[0]


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
        fr += f"{char:08b}"  # add sumbol
        fr += bin(len(value))[2:].zfill(colvoBitForLen)  # len
        fr += value

    data = fr + compr
    if len(data) % 8 != 0:
        data += "0" * (8 - len(data) % 8)
    try:
        with open(sys.argv[3], "wb") as file:
            file.write(len(frequencyDict).to_bytes(1, "big"))
            file.write(colvoBitForLen.to_bytes(1, "big"))
            for i in range(0, len(data), 8):
                file.write(int(data[i : i + 8], 2).to_bytes(1, "big"))
    except:
        print("Что-то не так")

def decompress(text):
    lenDict = text[0]
    colvoBitLenCode = text[1]
    text = "".join([bin(x)[2:].zfill(8) for x in text[2:]])
    dic = dict()
    for _ in range(lenDict):
        key = int(text[:8], 2)
        lenCode = int(text[8 : 8 + colvoBitLenCode],2)
        value = text[8 + colvoBitLenCode : 8 + colvoBitLenCode + lenCode]
        text = text[8 + colvoBitLenCode + lenCode :]
        dic[value] = key
    try:
        with open(sys.argv[3], 'wb') as file:
            while len(text)>0:
                code=''
                while code not in dic.keys():
                    code+=text[0]
                    text=text[1:]
                file.write(dic[code].to_bytes(1,"big"))
    except:
        exit(0)


# struct=[len_dict, colvo_bit_len_code, (value, len_code, code)*len_dict, compress_text]
#           8               8             8     cblc      lc


if __name__=='__main__':
    text = ReadText(sys.argv[2])
    if sys.argv[1]=='decompress':
        decompress(text)
    elif sys.argv[1]=='compress':
        frequencyDict = {char: text.count(char) for char in set(text)}  # Frequency analysis
        head = buildHuffmanTree(frequencyDict)
        getCodes(head)
        compress(frequencyDict, text)
    else:
        print("Не известная команда")
