from alpha_rptr.src.config import config as conf

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters



class TelegramBot:

    def __init__(self, token):
        self.updater = Updater(token, use_context=True)

        dp = self.updater.dispatcher
        dp.add_handler(CommandHandler("start", self.start_command_handler))
        dp.add_handler(MessageHandler(Filters.text, self.message_command_handler))
        dp.add_error_handler(self.error_handler)
        
        self.update=None
    
    def attach(self, observer):
        self.observers.append(observer)

    def run_bot(self):
        self.updater.start_polling()

    def start_command_handler(self, update, context):
        self.update=update
        print(update)
        print(type(update))
        self.send_message('Start Command Received')

    def message_command_handler(self, update, context):
        text=update.message.text
        self.send_message(f'I received {text}')
        
    def error_handler(self, update, context):
        error=context.error

    def send_message(self, msg):
        if self.update:
            self.update.message.reply_text(msg)


telegram_bot=TelegramBot(conf['telegram_apikey']['API_KEY'])
telegram_bot.run_bot()

def main():
    tg=TelegramBot(conf['telegram_apikey']['API_KEY'])
    tg.run_bot()
    while True:
        pass

if __name__ == '__main__':
    main()