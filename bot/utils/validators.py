import re

def validate_question(text: str):
    """
    Validate and parse a question in the format:
    
    Q: Question text
    A) Option 1
    B) Option 2
    C) Option 3
    D) Option 4
    Answer: A
    Year: 2024 (optional)
    
    Supports: A) Option, A. Option, A - Option, A:Option, A)Option (with/without space)
    Handles special characters like ², (), /, etc.
    """
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    
    if len(lines) < 6:
        return False, f"❌ Need at least 6 lines. Found {len(lines)} lines.\n\n" \
                      "Format:\nQ: Question text\nA) Option 1\nB) Option 2\nC) Option 3\nD) Option 4\nAnswer: A"

    # Check first line: must start with Q:
    if not lines[0].lower().startswith("q:"):
        return False, "❌ First line must start with 'Q:'"
    
    question = lines[0][2:].strip()
    if not question:
        return False, "❌ Question text cannot be empty."

    # Parse options (lines 2-5)
    options = []
    option_letters = ['A', 'B', 'C', 'D']
    
    for i in range(1, 5):
        if i >= len(lines):
            return False, f"❌ Missing option {option_letters[i-1]}."
        
        line = lines[i]
        # Support: A), A. , A - , A: , A)Option, etc.
        match = re.match(r'^([A-D])[\)\.\:\-\s]+(.*)$', line)
        if not match:
            return False, f"❌ Line {i+1} must start with '{option_letters[i-1]})', '{option_letters[i-1]}.', or '{option_letters[i-1]} - '"
        
        letter = match.group(1)
        option_text = match.group(2).strip()
        
        if letter != option_letters[i-1]:
            return False, f"❌ Expected option {option_letters[i-1]} but found {letter}."
        
        if not option_text:
            return False, f"❌ Option {letter} text cannot be empty."
        
        options.append(option_text)
    
    # Find Answer line (can be anywhere after options)
    answer_line = None
    answer_index = -1
    for i in range(5, len(lines)):
        if lines[i].lower().startswith("answer:"):
            answer_line = lines[i]
            answer_index = i
            break
    
    if not answer_line:
        return False, "❌ Answer line not found. Add 'Answer: A' (or B, C, D)."
    
    answer_part = answer_line[7:].strip().upper()
    match = re.match(r'^([A-D])$', answer_part)
    if not match:
        return False, "❌ Answer must be a single letter A, B, C, or D."
    
    correct_index = ord(match.group(1)) - ord('A')
    
    # Parse Year (optional)
    year = None
    for i in range(answer_index + 1, len(lines)):
        if lines[i].lower().startswith("year:"):
            year_str = lines[i][5:].strip()
            if year_str.isdigit():
                year = int(year_str)
            break
    
    return True, {
        "question": question,
        "options": options,
        "correct_index": correct_index,
        "year": year
    }
