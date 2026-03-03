import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
SUPPORT_CHANNEL = os.getenv("SUPPORT_CHANNEL", "")
DEVELOPER_USERNAME = os.getenv("DEVELOPER_USERNAME", "")
GROUP_ID = int(os.getenv("GROUP_ID", 0))

TIMEZONE = "Asia/Kolkata"
QUIZ_INTERVAL_MINUTES = 20

SCHEDULE = [
    {"start": 6, "end": 12, "subject": "Physics"},
    {"start": 12, "end": 18, "subject": "Chemistry"},
    {"start": 18, "end": 24, "subject": "Biology"},
]

# 🔴 Fill in your chapter lists below (NEET syllabus)
CHAPTERS = {
    "Physics": {
        11: ["Physical World", "Units and Measurements", "Motion in a Straight Line"],
        12: ["Electric Charges and Fields", "Electrostatic Potential", "Current Electricity"]
    },
    "Chemistry": {
        11: ["Some Basic Concepts", "Structure of Atom", "Classification of Elements"],
        12: ["Solid State", "Solutions", "Electrochemistry"]
    },
    "Biology": {
        11: ["The Living World", "Biological Classification", "Plant Kingdom"],
        12: ["Reproduction", "Genetics and Evolution", "Biology in Human Welfare"]
    }
}