# -*- coding: utf-8 -*-
import telebot;
import traceback
import json

# Reading a token and launching a bot. 
try:
    token = open("token.txt", 'r').readline().replace("\n","")
    bot = telebot.TeleBot(token);
except:
    print("Error: bot doesn't started. Check token in token.txt")
    raise

# Reading an admin users (useful for debugging).
# TODO: Add debug mode.
else:
    admin = [user.replace("\n","") for user in open("admin.txt").readlines()]
    if len(admin) < 1:
        print("Error: admin users not detected. Check admin.txt")
        raise

# Reading a quest.
f = open('quest.json', 'r', encoding="utf-8")
quest = json.loads(f.read())
print(quest)
f.close()

tag = "start"

# /start message
@bot.message_handler(commands=['start'])
def hello(message):
    bot.send_message(message.from_user.id, quest["start"]["bot_answer"])

# /help message    
@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.from_user.id, quest["help"])

# Answers to questions and transitions in dialogue.
@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    global tag
    print(message)
    
    if message.text.lower() in quest[tag]["goto"]:
        tag = quest[tag]["goto"][message.text.lower()]
        bot.send_message(message.from_user.id, quest[tag]["bot_answer"])
        
    else:
        bot.send_message(message.from_user.id, quest["unidentified"])
        
if __name__ == '__main__':
    bot.polling(none_stop=True, interval=0)
    #bot.infinity_polling()