 Storage_test

A Telegram bot for warehouse inventory management.



## Features

- Add products
- Write off product quantities
- View current stock
- Search for products
- Delete products with confirmation
- View operation history
- Russian and English language support
- Access restriction by Telegram User ID
- Data storage using SQLite
- Cancel current operations using the /cancel command



## Technologies

- Python 3.12
- aiogram 3
- SQLite
- aiosqlite
- python-dotenv



## Installation

Clone the repository and open the project directory.

Install dependencies using pip install -r requirements.txt.



## Configuration

Create a .env file in the project root directory.

Add the following variables:

BOT_TOKEN=YOUR_BOT_TOKEN

ALLOWED_USERS=YOUR_TELEGRAM_USER_ID

Replace the placeholder values with your Telegram bot token and Telegram user ID.



## Running the Bot

Run the application using python main.py.



## Database

The bot uses SQLite for data storage.

The database file is created automatically when the bot starts for the first time.

Products and operation history are preserved after restarting the bot.



## Security

Access is restricted to Telegram user IDs specified in the ALLOWED_USERS environment variable.

The .env file contains sensitive information and must not be uploaded to GitHub.

The SQLite database file should also be excluded from version control.