import logging
from datetime import datetime
from typing import Optional, Dict, Any
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger(__name__)

def format_user_mention(user_id: int, username: Optional[str] = None, first_name: Optional[str] = None) -> str:
    """
    Format user mention for display in messages.
    Returns @username if available, otherwise first name or 'User'
    """
    if username:
        return f"@{username}"
    elif first_name:
        return first_name
    else:
        return f"User(ID: {user_id})"

def parse_time_string(time_str: str) -> Optional[datetime]:
    """
    Parse time string in various formats.
    Returns datetime object or None if invalid.
    """
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%d/%m/%Y %H:%M",
        "%H:%M",
        "%I:%M %p"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(time_str, fmt)
        except ValueError:
            continue
    return None

def get_subject_emoji(subject: str) -> str:
    """Return appropriate emoji for subject"""
    emojis = {
        "Physics": "⚛️",
        "Chemistry": "🧪",
        "Biology": "🧬"
    }
    return emojis.get(subject, "📚")

def create_confirmation_keyboard(data: Dict[str, str]) -> InlineKeyboardMarkup:
    """
    Create yes/no confirmation keyboard with callback data
    """
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes", callback_data=data.get("yes", "confirm_yes")),
            InlineKeyboardButton("❌ No", callback_data=data.get("no", "confirm_no"))
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def safe_int(value: Any, default: int = 0) -> int:
    """
    Safely convert value to int, return default if fails
    """
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to max_length and add suffix if needed
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def format_score_message(correct: int, wrong: int, total: int) -> str:
    """
    Format user score for display
    """
    accuracy = (correct / (correct + wrong) * 100) if (correct + wrong) > 0 else 0
    return (
        f"📊 Your Stats:\n"
        f"✅ Correct: {correct}\n"
        f"❌ Wrong: {wrong}\n"
        f"📈 Total Points: {total}\n"
        f"🎯 Accuracy: {accuracy:.1f}%"
    )

def get_time_remaining(target_hour: int, target_minute: int = 0) -> str:
    """
    Calculate time remaining until target time
    """
    now = datetime.now()
    target = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
    
    if target < now:
        target = target.replace(day=target.day + 1)
    
    diff = target - now
    hours = diff.seconds // 3600
    minutes = (diff.seconds % 3600) // 60
    
    if hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"

def is_valid_indian_mobile(number: str) -> bool:
    """
    Validate Indian mobile number
    """
    import re
    pattern = r'^[6-9]\d{9}$'
    return bool(re.match(pattern, number))

def create_pagination_buttons(base_callback: str, current_page: int, total_pages: int) -> list:
    """
    Create pagination inline keyboard buttons
    """
    buttons = []
    row = []
    
    if current_page > 0:
        row.append(InlineKeyboardButton("◀️ Prev", callback_data=f"{base_callback}_page_{current_page-1}"))
    
    row.append(InlineKeyboardButton(f"{current_page+1}/{total_pages}", callback_data="noop"))
    
    if current_page < total_pages - 1:
        row.append(InlineKeyboardButton("Next ▶️", callback_data=f"{base_callback}_page_{current_page+1}"))
    
    if row:
        buttons.append(row)
    
    return buttons

def log_user_action(user_id: int, action: str, details: Optional[Dict] = None):
    """
    Log user actions for monitoring
    """
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "action": action,
        "details": details or {}
    }
    logger.info(f"User Action: {log_data}")
    # Can also write to a separate log file or database

def format_question_preview(question_data: Dict) -> str:
    """
    Format question for preview display
    """
    options_text = "\n".join([
        f"{chr(65+i)}) {opt}" 
        for i, opt in enumerate(question_data.get("options", []))
    ])
    
    return (
        f"📝 Question: {question_data.get('question', 'N/A')}\n\n"
        f"{options_text}\n\n"
        f"✅ Correct: {chr(65 + question_data.get('correct_index', 0))}\n"
        f"📚 Subject: {question_data.get('subject', 'N/A')}\n"
        f"📖 Chapter: {question_data.get('chapter', 'N/A')}\n"
        f"📅 Year: {question_data.get('year', 'N/A')}"
    )

def calculate_accuracy(correct: int, total: int) -> float:
    """
    Calculate accuracy percentage
    """
    if total == 0:
        return 0.0
    return (correct / total) * 100

def split_list_into_chunks(lst: list, chunk_size: int):
    """
    Split a list into smaller chunks
    """
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]