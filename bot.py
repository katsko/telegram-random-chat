#!/usr/bin/env python
from config import token
from collections import defaultdict
from telegram import ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
"""
users - карта пользователей: статусы и кто с кем связан
Структура:
{
    '<user_id>': {'status': 'free/busy', 'interlocutor': '<interlocutor_id>',
    '<user_id>': ...,
}

user_id и interlocutor_id - это номер чатов (update.message.chat_id)
"""
users = defaultdict(dict)


def scan(current):
    """
    Поиск свободных собеседников для пользователя current
    """
    for key, value in users.items():
        if key != current and value.get('status') == 'free':
            return key
    return None


def connect(user, interlocutor):
    """
    Соединение двух пользователей.
    Установка статусов "занят" и взаимная привязка.
    """
    users[user]['status'] = 'busy'
    users[user]['interlocutor'] = interlocutor
    users[interlocutor]['status'] = 'busy'
    users[interlocutor]['interlocutor'] = user


def find(bot, update):
    """
    Выставление статуса "свободен", запуск поиска и подключение,
    если собеседник найден
    """
    user = update.message.chat_id
    bot.sendMessage(user, text='Find...')
    interlocutor = users[user].get('interlocutor')
    if interlocutor:
        bot.sendMessage(interlocutor, text='Disconnect')
        users[interlocutor]['interlocutor'] = None
        users[user]['interlocutor'] = None
    interlocutor = scan(user)
    if interlocutor:
        connect(user, interlocutor)
        bot.sendMessage(user, text='Connect success')
        bot.sendMessage(interlocutor, text='Connect success')
    else:
        users[user]['status'] = 'free'


def disconnect(bot, update):
    """
    Отключение от чата с сохранением статуса "занят",
    чтобы не принимать новых сбеседников
    """
    user = update.message.chat_id
    bot.sendMessage(user, text='Disconnect')
    users[user]['status'] = 'busy'
    interlocutor = users[user].get('interlocutor')
    if interlocutor:
        bot.sendMessage(interlocutor, text='Disconnect')
        users[interlocutor]['interlocutor'] = None
        users[user]['interlocutor'] = None


def send(bot, update):
    """
    Пересылка сообщения, если у пользователя был собеседник
    """
    user = update.message.chat_id
    interlocutor = users[user].get('interlocutor')
    if not interlocutor:
        bot.sendMessage(user, text="You haven't connect. Enter /find")
    else:
        bot.sendMessage(interlocutor, text=update.message.text)


def start(bot, update):
    reply_markup = ReplyKeyboardMarkup(
        [[KeyboardButton('/find')]], resize_keyboard=True)
    bot.sendMessage(update.message.chat_id,
                    text='Welcome to chat. Enter /find',
                    reply_markup=reply_markup)


def help(bot, update):
    bot.sendMessage(update.message.chat_id, text='Enter /find to connect')


def main():
    updater = Updater(token)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('help', help))
    dp.add_handler(CommandHandler('find', find))
    dp.add_handler(CommandHandler('disconnect', disconnect))
    dp.add_handler(MessageHandler([Filters.text], send))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
