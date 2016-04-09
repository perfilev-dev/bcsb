from telegram import Bot
from utils.config import configure_from_file


if __name__ == '__main__':
    config = configure_from_file('default.cfg')
    bot = Bot(token=config['telegram']['token'])

    print bot.getMe()
