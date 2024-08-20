# Alert Ready

Alert Ready is a Discord bot designed to monitor and alert users about weather updates. It connects to a TCP stream to receive weather alerts and sends them to designated channels in Discord servers.

## Features

- **Automatic Channel Setup**: Automatically creates and sets up `heartbeat` and `alerts` channels in new guilds.
- **Weather Alerts**: Parses XML data from a TCP stream and sends alerts to the appropriate channels.
- **Custom Help Command**: Provides a custom help command for users.
- **Status Loop**: Updates the bot's status to show the number of servers it is monitoring.
- **Test Alerts**: Allows the bot owner to send test alerts to all `alerts` channels.
- **Direct Message Logging**: Logs direct messages and forwards them to the bot owner.
- **View Conversations**: Allows the bot owner to view saved conversations.

## Setup

### Prerequisites

- Python 3.8+
- `py-cord` library
- `xml.etree.ElementTree` for XML parsing
- `socket` for TCP connection
- `json` for data storage
- `logging` for logging
- `threading` for running the TCP stream in a separate thread
- `asyncio` for asynchronous operations

### Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/shibakek2/alert-ready-discord-bot.git
    cd alert-ready-discord-bot
    ```

2. Install the required packages:
    ```sh
    pip install py-cord
    ```

3. Set up your bot token:
    - Replace `'put token here'` in the `bot_token` variable with your actual Discord bot token.

4. Run the bot:
    ```sh
    python alert-ready.py
    ```

## Usage

### Commands

- `!setup`: Sets up the `heartbeat` and `alerts` channels in the server.
- `!customhelp`: Displays a custom help message.
- `!test_alert <message>`: Sends a test alert to all `alerts` channels (Owner only).
- `!test_single_alert <message>`: Sends a test alert to a specific test channel.
- `!view_conversations`: Displays saved conversations (Owner only).

### Events

- `on_guild_join`: Triggered when the bot joins a new guild. Sets up the necessary channels.
- `on_ready`: Triggered when the bot is ready. Starts the TCP stream thread and status loop.
- `on_message`: Handles direct messages and logs them.
- `on_message_edit`: Forwards edited direct messages to the original sender.
- `on_command_error`: Handles errors that occur during command execution.

## Data Storage

- `dms.json`: Stores direct messages.
- `servers.json`: Stores server-specific data, including channel IDs for `heartbeat` and `alerts`.

## Logging

The bot uses Python's built-in `logging` module to log important events and errors. Logs are displayed in the console.

## Contributing

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Make your changes.
4. Commit your changes (`git commit -am 'Add new feature'`).
5. Push to the branch (`git push origin feature-branch`).
6. Create a new Pull Request.

## License

This project is licensed under the MIT License.

## Contact

For questions or support, join our Discord server: [discord.gg/EB694pE2ht](https://discord.gg/EB694pE2ht)

---
