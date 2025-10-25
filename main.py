#!/usr/bin/env python3
"""
TextBekharBot Startup Script
Professional Telegram Bot for TextBekhar Platform
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    """Main entry point"""
    try:
        # Import and run the bot
        from bot import TextBekharBot

        # Check if bot token is provided
        bot_token = os.getenv('BOT_TOKEN')
        if not bot_token:
            print("Error: BOT_TOKEN environment variable is required!")
            print("Please set your bot token in .env file or environment variables.")
            sys.exit(1)

        print("Starting TextBekharBot...")
        print("Press Ctrl+C to stop the bot")

        # Create and run bot
        bot = TextBekharBot(bot_token)
        bot.run()

    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
