import re

def validate_question(text: str):
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if len(lines) < 6:
        return False, "Not enough lines. Need Q, 4 options, Answer."

    if not lines[0].startswith("Q:"):
        return False, "First line must start with 'Q:'"
    question = lines[0][2:].strip()

    options = []
    for i in range(1, 5):
        if not re.match(r'^[A-D]\)', lines[i]):
            return False, f"Line {i+1} must be like 'A) ...'"
        options.append(lines[i][2:].strip())

    answer_line = lines[5]
    if not answer_line.startswith("Answer:"):
        return False, "Line 6 must start with 'Answer:'"
    answer_part = answer_line[7:].strip()
    match = re.match(r'^([A-D])$', answer_part)
    if not match:
        return False, "Answer must be a single letter A, B, C, or D"
    answer_letter = match.group(1)
    correct_index = ord(answer_letter) - ord('A')

    year = None
    if len(lines) > 6 and lines[6].startswith("Year:"):
        year_str = lines[6][5:].strip()
        if year_str.isdigit():
            year = int(year_str)

    return True, {
        "question": question,
        "options": options,
        "correct_index": correct_index,
        "year": year
    }