## README

This repository contains the code for a Telegram bot implemented in Python. The main file is `bot.py`.

### Prerequisites

- Python 3.9 or higher
- Telegram API token

### Usage

1. Create a `.env` file and set the Telegram API token in the `.env` file:

   ```env
   TOKEN = "TELEGRAM_BOT_TOKEN"
   USERNAME="TELEGRAM_USER_TO_SEND_TO"
   SQLALCHEMY_DATABASE_URI="sqlite:///db/database.db"
   ```

2. Run the bot:

   To run the bot you'll need to use the following command to build the container:

   ``` bash
    docker buildx build -t order_book_bot .
   ```
   Run the following to run the container with persistent volumes `/db` and `.env`

   ``` bash
   docker run -v $(pwd)/db:/app/db -v $(pwd)/.env:/app/.env -d --name order_book_bot order_book_bot:latest
   ```

### Features

- Prompt user to share location and contact information
- Send user location and contact details to a specified user
- Send map and user details to a specified user


### License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
