#!/bin/python3


def encode_hamming(data):
    # Вычисляем количество контрольных битов
    m = len(data)
    r = 0
    while 2**r < m + r + 1:
        r += 1

    # Создаем закодированное сообщение с пустыми контрольными битами
    encoded = [0] * (m + r)
    j = 0
    for i in range(1, m + r + 1):
        if (i & (i - 1)) == 0:  # Если позиция - степень двойки
            encoded[i - 1] = 0  # Пока ставим 0, потом вычислим
        else:
            encoded[i - 1] = int(data[j])
            j += 1

    # Вычисляем контрольные биты
    for i in range(r):
        pos = 2**i - 1  # Позиции контрольных битов (0-based)
        parity = 0
        # Проходим по всем битам, которые включают этот контрольный бит
        for j in range(pos, len(encoded), 2 * (pos + 1)):
            for k in range(j, min(j + (pos + 1), len(encoded))):
                if k != pos:  # Сам контрольный бит не учитываем
                    parity ^= encoded[k]
        encoded[pos] = parity

    return "".join(map(str, encoded))


def introduce_error(encoded):
    print(f"Закодированное сообщение: {encoded}")
    while True:
        try:
            pos = (
                int(
                    input(
                        "Введите позицию для внесения ошибки (1..{}): ".format(
                            len(encoded)
                        )
                    )
                )
                - 1
            )
            if 0 <= pos < len(encoded):
                break
            print("Позиция вне диапазона!")
        except ValueError:
            print("Введите число!")

    encoded_list = list(encoded)
    encoded_list[pos] = "1" if encoded_list[pos] == "0" else "0"
    return "".join(encoded_list)


def correct_hamming(encoded):
    encoded_list = list(map(int, encoded))
    r = 0
    while 2**r <= len(encoded_list):
        r += 1

    error_pos = 0
    for i in range(r):
        pos = 2**i - 1
        if pos >= len(encoded_list):
            continue
        parity = 0
        # Вычисляем контрольную сумму
        for j in range(pos, len(encoded_list), 2 * (pos + 1)):
            for k in range(j, min(j + (pos + 1), len(encoded_list))):
                if k != pos:  # Исключаем сам контрольный бит
                    parity ^= encoded_list[k]
        # Сравниваем с текущим значением контрольного бита
        if parity != encoded_list[pos]:
            error_pos += pos + 1  # +1 потому что контрольные биты на позициях 2^i

    if error_pos == 0:
        print("Ошибок не обнаружено")
    else:
        # Корректируем ошибку
        error_index = error_pos - 1  # Переводим в 0-based индекс
        if error_index < len(encoded_list):
            print(f"Обнаружена ошибка в позиции {error_pos}")
            encoded_list[error_index] ^= 1
            print(f"Исправленное сообщение: {''.join(map(str, encoded_list))}")
        else:
            print("Ошибка в несуществующей позиции")

    # Извлекаем исходные данные (удаляем контрольные биты)
    original_data = []
    power_of_two = 1
    for i in range(len(encoded_list)):
        if i + 1 == power_of_two:
            power_of_two *= 2
        else:
            original_data.append(str(encoded_list[i]))

    print(f"Исходное сообщение: {''.join(original_data)}")
    return "".join(map(str, encoded_list))


def main():
    data = input("Введите двоичную последовательность: ")

    if not all(c in "01" for c in data):
        print("Ошибка: введите только 0 и 1!")
        return

    encoded = encode_hamming(data)

    corrupted = introduce_error(encoded)
    print(f"Сообщение с ошибкой: {corrupted}")

    correct_hamming(corrupted)


if __name__ == "__main__":
    main()
