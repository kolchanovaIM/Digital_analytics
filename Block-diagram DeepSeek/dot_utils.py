def escape_dot_label(text: str) -> str:
    """Экранирует спецсимволы и переносит длинные строки."""
    # Заменяем двойные кавычки на обратный слеш + кавычка
    text = text.replace('"', '\\"')
    # Если строка длиннее 30 символов, вставляем перенос строки
    if len(text) > 30:
        words = text.split()
        new_text = ''
        line = ''
        for w in words:
            if len(line) + len(w) < 30:
                line += w + ' '
            else:
                new_text += line.strip() + '\\n'
                line = w + ' '
        new_text += line.strip()
        return new_text
    return text

def shape_for_type(node_type: str) -> str:
    shapes = {
        'start': 'ellipse',
        'end': 'ellipse',
        'process': 'box',
        'decision': 'diamond',
        'io': 'parallelogram',
        'loop': 'hexagon',
        'function': 'component',
    }
    return shapes.get(node_type, 'box')