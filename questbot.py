# -*- coding: utf-8 -*-
import telebot;
import traceback
import json
from sys import argv

print("Starting...")

try:
    quest_file = argv[1]
except Exception:
    print("Error: bot doesn't started: quest file not definited")
    raise 

# Reading a token and launching a bot. 
try:
    token = open("token.txt", 'r').readline().replace("\n","")
    bot = telebot.TeleBot(token);
except Exception:
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
f.close()

class User():
    def __init__(self, uid, tag):
        self.uid = uid
        self.tag = tag
        self.data = {}
try:        
    f = open('users.json', 'r', encoding="utf-8")
except FileNotFoundError:
    f = open('users.json', 'w', encoding="utf-8")
    f.write("{}")
    f.close()
    f = open('users.json', 'r', encoding="utf-8")
    
users_data = json.loads(f.read())
f.close()

users = {}
for user in users_data:
    users[user] = User(user, users_data[user]["tag"])

def save_data():
    f = open("users.json", 'w', encoding="utf-8")
    data = {}
    for user in users:
        data[str(user)] = {"tag" : users[user].tag}
    f.write(str(data).replace("'", '"'))    

# /start message
@bot.message_handler(commands=['start'])
def hello(message):
    global users
    uid = message.from_user.id
    
    if not uid in users:
        users[uid] = User(uid, "start")
        
    bot.send_message(message.from_user.id, quest["start"]["bot_answer"])
    users[uid].tag = "start"
    save_data()

# /help message    
@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.from_user.id, quest["help"])

# Answers to questions and transitions in dialogue.
@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    global users    
    uid = message.from_user.id
    tag = users[uid].tag
    print(uid, message.text)
    
    if uid in users and message.text.lower() in [txt.lower() for txt in quest[tag]["goto"]]:
        tag = quest[tag]["goto"][message.text.lower()]
        bot.send_message(message.from_user.id, quest[tag]["bot_answer"])
        users[uid].tag = tag
        save_data()
        
    else:
        bot.send_message(message.from_user.id, quest["unidentified"])
        
if __name__ == '__main__':
    print("Bot running...")
    bot.polling(none_stop=True, interval=0)
    #bot.infinity_polling()