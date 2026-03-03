📄 File: README.md

```markdown
# 🧪 NEET Quiz Bot

A production‑ready Telegram bot that automatically sends NEET quiz polls in a group every 20 minutes, with subject rotation (Physics, Chemistry, Biology) and a sleep mode at night. Users can submit their own questions via a private chat, which go through an admin approval process before entering the quiz pool. The bot tracks scores (+1 for correct, -1 for wrong) and provides leaderboards (daily/weekly/all‑time) and chapter‑wise accuracy.

---

## ✨ Features

- ✅ **Automatic daily quizzes** – Scheduled by time blocks:
  - 6 AM – 12 PM: Physics
  - 12 PM – 6 PM: Chemistry
  - 6 PM – 12 AM: Biology
  - 12 AM – 6 AM: Sleep mode (no polls)
- ✅ **Quiz every 20 minutes** – Each poll is a non‑anonymous quiz with the correct option pre‑set.
- ✅ **Scoring system** – Users get +1 for a correct answer, –1 for a wrong answer. Real‑time feedback in the group.
- ✅ **Leaderboard** – `/leaderboard` in the group shows top 10 users; can be filtered by daily, weekly, or all‑time.
- ✅ **Private start menu** – In private chat, `/start` shows a professional welcome with buttons for Help, Add Question, Developer, and Support Channel.
- ✅ **Multi‑step question submission** – Users select subject, class, chapter, then send the question in a strict format:
```

Q: Question text
A) Option 1
B) Option 2
C) Option 3
D) Option 4
Answer: A
Year: 2024 (optional)

```
- ✅ **Batch question mode** – After each question, the bot asks “Next question?” with `/next` and `/done` (via inline buttons).
- ✅ **Admin approval system** – Submitted batches are sent to an admin with inline buttons to **Accept**, **Reject**, or **Delete** each question. Only accepted questions go into the main quiz pool.
- ✅ **MongoDB storage** – Collections: `users`, `questions`, `pending_batches`, `poll_logs`, `answers`.
- ✅ **Chapter‑wise accuracy tracking** – The bot stores correct/wrong counts per chapter for each user.
- ✅ **Command restrictions** – Leaderboard is group‑only, question submission is private‑only, admin commands are admin‑only.
- ✅ **Clean, modular async architecture** – Uses `python-telegram-bot` v20+, `APScheduler`, `motor` (async MongoDB driver), and environment variables for configuration.
- ✅ **Production‑ready** – Error handling, logging, and easy deployment on Railway.

---

## 🛠️ Tech Stack

- Python 3.11
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) (v20+)
- [APScheduler](https://github.com/agronholm/apscheduler) – for scheduling quizzes
- [MongoDB](https://www.mongodb.com/) – with [Motor](https://github.com/mongodb/motor) async driver
- [pytz](https://pythonhosted.org/pytz/) – timezone handling
- [python-dotenv](https://github.com/theskumar/python-dotenv) – environment variables

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- MongoDB instance (local or [Atlas](https://www.mongodb.com/cloud/atlas))
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- A Telegram group where the bot will send quizzes (make the bot an admin to send polls)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/neet-quiz-bot.git
   cd neet-quiz-bot
```

1. Create a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```
2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables
      Create a .env file in the project root with the following content:
   ```env
   BOT_TOKEN=your_telegram_bot_token
   MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/neetquiz
   ADMIN_ID=your_telegram_user_id
   GROUP_ID=-1001234567890
   SUPPORT_CHANNEL=@your_channel   # optional
   DEVELOPER_USERNAME=yourusername  # optional
   ```
   · ADMIN_ID: Your personal Telegram user ID (to receive approval requests).
   · GROUP_ID: ID of the group where quizzes will be sent (must start with -100 for supergroups).
   · To get your user ID, talk to @userinfobot.
   · To get the group ID, add the bot to the group and send a message; then check https://api.telegram.org/bot<BOT_TOKEN>/getUpdates.
4. Prepare MongoDB indexes (recommended for performance)
      Connect to your MongoDB and run:
   ```javascript
   db.users.createIndex({ user_id: 1 }, { unique: true })
   db.questions.createIndex({ subject: 1, chapter: 1, approved: 1 })
   db.pending_batches.createIndex({ user_id: 1, status: 1 })
   db.poll_logs.createIndex({ poll_id: 1 })
   db.answers.createIndex({ user_id: 1, timestamp: -1 })
   ```
5. Fill in chapter lists
      Open bot/config.py and replace the placeholder CHAPTERS dictionary with the actual NEET syllabus chapters for Physics, Chemistry, and Biology (classes 11 and 12).
6. Run the bot locally
   ```bash
   python -m bot.main
   ```

---

☁️ Deploy on Railway

1. Push your code to a GitHub repository.
2. Go to Railway and create a new project from your GitHub repo.
3. Add all the environment variables from your .env file in the Railway dashboard.
4. Ensure the start command is set to: python -m bot.main.
5. Railway will automatically install dependencies and run the bot.

Note: Make sure the bot is added to your group and promoted to admin before quizzes start.

---

📖 Usage

In the group

· The bot automatically sends quiz polls every 20 minutes (only during active time blocks).
· Users answer the poll; the bot replies immediately with their updated score.
· Use /leaderboard to see the top 10 users (you can choose daily, weekly, or all‑time).

In private chat with the bot

· /start – Shows the welcome menu with buttons:
  · Help – Explains the bot’s schedule, scoring, and question format.
  · Add Question – Starts the multi‑step question submission process.
  · Developer – Link to the developer’s Telegram.
  · Support Channel – Link to the channel for updates/help.
· Add Question flow:
  1. Select subject (Physics, Chemistry, Biology).
  2. Select class (11 or 12).
  3. Select chapter (from the hardcoded list).
  4. Send the question in the required strict format.
  5. After each question, choose Next Question or Done.
  6. When done, the batch is sent to the admin for review.
· You will be notified when your questions are accepted/rejected.

---

🤖 Commands

Command Where Description
/start Private Shows welcome menu and buttons.
/leaderboard Group Displays top 10 users with period selection.
/addquestion Private Starts the question submission process (also available via button).
/cancel Private Cancels an ongoing question submission.

Note: There is no /help command because help is integrated into the start menu button.

---

📁 Project Structure

```
neet-quiz-bot/
├── bot/
│   ├── __init__.py
│   ├── main.py                 # Entry point
│   ├── config.py               # Environment & constants
│   ├── scheduler.py            # APScheduler & quiz dispatcher
│   ├── database/
│   │   ├── __init__.py
│   │   ├── db.py               # MongoDB connection
│   │   └── models.py           # All database operations
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── start.py             # /start, help callback
│   │   ├── leaderboard.py       # /leaderboard command & callbacks
│   │   ├── poll_answer.py       # Scoring and feedback
│   │   ├── question_submission.py # Conversation for adding questions
│   │   ├── admin.py             # Admin approval interface
│   │   └── error.py             # Global error handler
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── helpers.py           # Utility functions
│   │   ├── validators.py        # Question format validation
│   │   └── decorators.py        # @group_only, @private_only, @admin_only
│   └── logs/                    # Optional log files
├── .env                          # Environment variables
├── requirements.txt
└── README.md
```

---

🧪 Testing

· Sleep mode: After 12 AM IST, no quizzes should be sent until 6 AM.
· Subject rotation: Verify that at 6 AM, 12 PM, and 6 PM the subject changes correctly.
· Scoring: Answer a poll correctly and incorrectly, check the instant feedback and total points.
· Leaderboard: Use /leaderboard in the group and try the three filters.
· Question submission: Go through the full flow, deliberately enter a wrong format to see the error message.
· Admin approval: As admin, accept/reject questions and ensure the user gets notified.

---

🤝 Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

1. Fork the repository.
2. Create a feature branch: git checkout -b feature/my-feature
3. Commit your changes: git commit -am 'Add some feature'
4. Push to the branch: git push origin feature/my-feature
5. Open a pull request.

---

📄 License

This project is licensed under the MIT License – see the LICENSE file for details.

---

🙏 Acknowledgements

· python-telegram-bot for the excellent library.
· All contributors and testers.

---

Happy Quizzing! 🧪📚

```