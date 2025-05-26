#!/bin/python3

import numpy as np

# Генераторная матрица G для кода (5,2)
G = np.array([[1, 0, 1, 0, 1], [0, 1, 0, 1, 1]], dtype=int)

# Проверочная матрица H
H = np.array([[1, 0, 1, 0, 0], [0, 1, 0, 1, 0], [1, 1, 0, 0, 1]], dtype=int)

# Таблица синдромов и соответствующих лидеров смежных классов
syndrome_table = {
    (0, 0, 0): np.array([0, 0, 0, 0, 0], dtype=int),  # Нет ошибок
    (1, 0, 1): np.array([1, 0, 0, 0, 0], dtype=int),  # Ошибка в 1-м бите
    (0, 1, 1): np.array([0, 1, 0, 0, 0], dtype=int),  # Ошибка во 2-м бите
    (1, 0, 0): np.array([0, 0, 1, 0, 0], dtype=int),  # Ошибка в 3-м бите
    (0, 1, 0): np.array([0, 0, 0, 1, 0], dtype=int),  # Ошибка в 4-м бите
    (1, 1, 1): np.array([0, 0, 0, 0, 1], dtype=int),  # Ошибка в 5-м бите
    (1, 1, 0): np.array([1, 0, 0, 0, 1], dtype=int),  # Другие возможные ошибки
    (0, 0, 1): np.array([1, 1, 0, 0, 0], dtype=int),  # Другие возможные ошибки
}


def encode(message):
    """Кодирование сообщения с использованием линейного кода (5,2)"""
    if len(message) != 2:
        raise ValueError("Длина сообщения должна быть 2 бита")
    return np.dot(message, G) % 2


def introduce_error(codeword, error_position):
    """Внесение ошибки в кодовое слово"""
    if error_position < 0 or error_position >= len(codeword):
        raise ValueError("Недопустимая позиция ошибки")
    error = np.zeros(5, dtype=int)
    error[error_position] = 1
    return (codeword + error) % 2


def compute_syndrome(received):
    """Вычисление синдрома для полученного вектора"""
    return tuple(np.dot(H, received) % 2)  # Преобразуем в кортеж обычных int


def correct_error(received):
    """Коррекция ошибки на основе синдрома"""
    syndrome = compute_syndrome(received)
    if syndrome in syndrome_table:
        error_vector = syndrome_table[syndrome]
        corrected = (received + error_vector) % 2
        return corrected, syndrome, error_vector
    else:
        return received, syndrome, np.zeros(5, dtype=int)


def decode(codeword):
    """Декодирование кодового слова обратно в сообщение"""
    return codeword[:2]  # Для кода (5,2) информационные биты - первые два


def main():
    print("Линейный код (5,2) с исправлением одиночных ошибок")
    print("Генераторная матрица G:")
    print(G)
    print("\nПроверочная матрица H:")
    print(H)

    # Ввод сообщения
    while True:
        message = input("\nВведите 2-битное сообщение (например, '10'): ")
        if len(message) == 2 and all(c in "01" for c in message):
            break
        print("Ошибка: введите ровно 2 бита (0 или 1)")

    message = np.array([int(bit) for bit in message], dtype=int)

    # Кодирование
    codeword = encode(message)
    print(f"\nЗакодированное сообщение: {''.join(map(str, codeword))}")

    # Ввод ошибки
    while True:
        error_input = input(
            "Введите позицию для ошибки (0-4, -1 для отсутствия ошибки): "
        )
        try:
            error_pos = int(error_input)
            if error_pos == -1 or 0 <= error_pos <= 4:
                break
        except ValueError:
            pass
        print("Ошибка: введите число от 0 до 4 или -1")

    if error_pos != -1:
        received = introduce_error(codeword, error_pos)
        print(f"\nПринятое сообщение с ошибкой: {''.join(map(str, received))}")
    else:
        received = codeword.copy()
        print("\nОшибка не вносилась")

    # Коррекция ошибки
    corrected, syndrome, error_vector = correct_error(received)
    # Теперь выводится как обычный кортеж (1, 0, 0)
    print(f"\nСиндром: {[int(x) for x in syndrome]}")
    print(f"Вектор ошибки: {''.join(map(str, error_vector))}")

    if np.array_equal(corrected, codeword):
        print("\nОшибка успешно исправлена!")
        print(f"Исправленное кодовое слово: {''.join(map(str, corrected))}")
    else:
        print("\nНе удалось исправить ошибку (возможно, двойная ошибка)")

    # Декодирование
    decoded = decode(corrected)
    print(f"\nДекодированное сообщение: {''.join(map(str, decoded))}")


if __name__ == "__main__":
    main()
