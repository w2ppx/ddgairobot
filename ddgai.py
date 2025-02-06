import requests
import json
import telebot
import random
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()
engine = create_engine('sqlite:///ddgbot.db', connect_args={'check_same_thread': False})
Session = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    model = Column(String)

Base.metadata.create_all(engine)

bot = telebot.TeleBot('YOUR_BOT_TOKEN')

models = {
    "claude-3-haiku-20240307": "Claude-3-haiku",
    "gpt-4o-mini": "GPT-4o-mini",
    "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo": "Meta-Llama-3.1",
    "mistralai/Mixtral-8x7B-Instruct-v0.1": "Mixtral"
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36",
    "Accept": "text/event-stream",
    "Referer": "https://duckduckgo.com/?q=DuckDuckGo&ia=chat",
    "Content-Type": "application/json",
    "Origin": "https://duckduckgo.com",
    "Cookie": "dcm=1; bg=-1",
    "x-vqd-accept": "1",
}

def get_random_proxy():
    response = requests.get('https://mojoproxy.com/getsocks?country=nl')
    proxies = response.text.splitlines()
    proxy = random.choice(proxies)
    try:
        requests.get('https://ipinfo.io', proxies={'https': f'socks5://{proxy}'}, timeout=3)
        return proxy
    except Exception:
        return get_random_proxy()

def get_vqd(proxy):
    response = requests.get('https://duckduckgo.com/duckchat/v1/status', headers=headers, proxies={'https': f'socks5://{proxy}'})
    return response.headers.get('x-vqd-4')

def ask_gpt_api(model, message):
    proxy = get_random_proxy()
    headers['x-vqd-4'] = get_vqd(proxy)
    json_data = {
        'model': model,
        'messages': [{'role': 'user', 'content': message}],
    }
    try:
        response = requests.post('https://duckduckgo.com/duckchat/v1/chat', headers=headers, json=json_data, proxies={'https': f'socks5://{proxy}'})
        data = response.text.split('data:')
        full_msg = ''.join(json.loads(i.split('\n\n')[0])['message'] for i in data if i and '[DONE]' not in i)
        return full_msg.encode('iso-8859-1').decode('utf-8')
    except Exception:
        return 'Error. DuckDuckGo returned bad response. Try again later.'

@bot.message_handler(commands=['start'])
def start_message(message):
    session = Session()
    user = session.query(User).filter_by(id=message.chat.id).first()
    
    if user:
        bot.reply_to(message, 'Welcome back! You can use /model command to change your model selection, or just start chatting.')
    else:
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        for model in models.values():
            markup.add(telebot.types.KeyboardButton(model))
        bot.send_message(message.chat.id, 'Welcome! Please select a model to start:', reply_markup=markup)
    session.close()

@bot.message_handler(commands=['model'])
def model_command(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for model in models.values():
        markup.add(telebot.types.KeyboardButton(model))
    bot.send_message(message.chat.id, 'Select a new model:', reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in models.values())
def set_model(message):
    session = Session()
    model = list(models.keys())[list(models.values()).index(message.text)]
    
    user = session.query(User).filter_by(id=message.chat.id).first()
    if user:
        user.model = model
    else:
        user = User(id=message.chat.id, model=model)
        session.add(user)
    
    session.commit()
    session.close()
    bot.send_message(message.chat.id, 'Model set to ' + message.text)

@bot.message_handler(func=lambda message: True)
def ask_gpt(message):
    session = Session()
    user = session.query(User).filter_by(id=message.chat.id).first()
    session.close()
    
    if user:
        msg_edit = bot.reply_to(message, 'Thinking...')
        ans = ask_gpt_api(user.model, message.text)
        bot.edit_message_text(chat_id=msg_edit.chat.id, message_id=msg_edit.message_id, text=ans, parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, 'Please select a model first using /model.')

@bot.inline_handler(lambda query: query.query)
def query_text(query):
    results = []
    for model in models:
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.add(telebot.types.InlineKeyboardButton('Wait', callback_data='wait'))
        model_num = list(models.keys()).index(model)
        results.append(telebot.types.InlineQueryResultArticle(
            title=models[model],
            id=f'm={model_num}',
            input_message_content=telebot.types.InputTextMessageContent('Loading...', parse_mode='Markdown'),
            reply_markup=keyboard
        ))
    bot.answer_inline_query(query.id, results, cache_time=0)

@bot.chosen_inline_handler(func=lambda chosen_inline_result: True)
def test_chosen(chosen_inline_result):
    bot.edit_message_reply_markup(inline_message_id=chosen_inline_result.inline_message_id, reply_markup=None)
    model = list(models.keys())[int(chosen_inline_result.result_id.split('=')[1])]
    
    ans = ask_gpt_api(model, chosen_inline_result.query)
    ans = f'<blockquote>{chosen_inline_result.query}</blockquote>\n\n{ans}'
    try:
        bot.edit_message_caption(inline_message_id=chosen_inline_result.inline_message_id, caption=ans, parse_mode='HTML')
    except Exception:
        bot.edit_message_caption(inline_message_id=chosen_inline_result.inline_message_id, caption=ans)

bot.infinity_polling()
