def calculate_length_points(length: int) -> int:
    if length <= 0:
        return 0
    if length == 1:
        return 1
    if length == 2:
        return 3
    return 3 + (3 * (length - 2))


def calculate_word_points(*, ordinal: int, word_length: int) -> dict[str, int]:
    length_points = calculate_length_points(word_length)
    index_points = ordinal
    total = index_points + length_points
    return {
        "index_points": index_points,
        "length_points": length_points,
        "total": total,
    }


def calculate_time_bonus(time_left_ms: int) -> int:
    if time_left_ms <= 0:
        return 0
    return (time_left_ms // 100) * 5
