import telebot
from PIL import Image, ImageDraw, ImageFont
import os
from telebot import types
from flask import Flask, request
import threading

app = Flask(__name__)

BOT_TOKEN = '7666674896:AAHKXKmag-XlJMOM4iPKZsIHJDZDwTgO4VY'
bot = telebot.TeleBot(BOT_TOKEN)

TEMPLATE_FOLDER = 'templates'
user_data = {}

@app.route('/webhook', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return 'OK', 200

@app.route('/')
def home():
    return "Telegram Bot is running!"

def start_polling():
    """Функция для запуска бота на сервере с Flask"""
    bot.remove_webhook()
    bot.set_webhook(url="https://<YOUR_RAILWAY_PROJECT>.railway.app/webhook")  # Укажи ссылку на свой проект на Railway
    print("Бот запущен и ожидает вебхуков...")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    keyboard = types.InlineKeyboardMarkup()
    templates = os.listdir(TEMPLATE_FOLDER)
    for template in templates:
        keyboard.add(types.InlineKeyboardButton(template, callback_data=template))
    bot.reply_to(message, "Выбери шаблон:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: True)
def handle_template_selection(call):
    user_data[call.message.chat.id] = {'template': call.data}
    bot.send_message(call.message.chat.id, "✏️ Напиши текст: верх | низ (не более 6 символов в строке на размере текста 5.9 или >)")
    bot.register_next_step_handler(call.message, handle_text_input)

def handle_text_input(message):
    if '|' not in message.text:
        bot.reply_to(message, "⚠️ Неправильный формат! Используй: верх | низ")
        return

    user_data[message.chat.id]['text'] = message.text
    bot.send_message(message.chat.id, "🔠 Теперь введи размер шрифта в процентах (например, 5 или 6.5):")
    bot.register_next_step_handler(message, handle_font_size_input)

def handle_font_size_input(message):
    try:
        font_percent = float(message.text.strip())
        if not (1 <= font_percent <= 20):
            raise ValueError("Недопустимое значение")
        user_data[message.chat.id]['font_percent'] = font_percent
        generate_meme(message)
    except Exception:
        bot.reply_to(message, "⚠️ Введи число от 1 до 20 — это процент от ширины/высоты картинки.")

def generate_meme(message):
    try:
        data = user_data.get(message.chat.id)
        if not data:
            bot.reply_to(message, "Что-то пошло не так. Попробуй снова.")
            return

        top_text, bottom_text = data['text'].split('|')
        template_path = os.path.join(TEMPLATE_FOLDER, data['template'])

        img = Image.open(template_path).convert("RGB")
        draw = ImageDraw.Draw(img)
        width, height = img.size

        font_percent = 0.06 if width > 800 else 0.08

        def get_font():
            return ImageFont.truetype('/Library/Fonts/Arial.ttf', int(min(width, height) * font_percent))

        font = get_font()

        def draw_text(text, y, shift_x=0, shift_y=0):
            text = text.upper().strip()
            bbox = draw.textbbox((0, 0), text, font=font)
            x = (width - (bbox[2] - bbox[0])) / 2 + shift_x
            y += shift_y
            for dx in [-2, -1, 0, 1, 2]:
                for dy in [-2, -1, 0, 1, 2]:
                    draw.text((x + dx, y + dy), text, font=font, fill='black')
            draw.text((x, y), text, font=font, fill='white')

        if "nye-da.jpg" in template_path:
            draw_text(top_text, 5, -20, 20)
            draw_text(bottom_text, height - 90, 20, 45)
        elif "doge.jpg" in template_path:
            draw_text(top_text, int(height * 0.05))      # Над первой собакой
            draw_text(bottom_text, int(height * 0.88))   # Под второй собакой
        else:
            draw_text(top_text, 10, -20, 20)
            draw_text(bottom_text, height - 20, 20, 45)

        output_path = f"meme_{message.chat.id}.jpg"
        img.save(output_path, format='JPEG', quality=95)
        with open(output_path, 'rb') as photo:
            bot.send_photo(message.chat.id, photo)
        os.remove(output_path)
        user_data.pop(message.chat.id, None)
    except Exception as e:
        bot.reply_to(message, f"Ошибка при создании мема: {e}")

if __name__ == '__main__':
    threading.Thread(target=start_polling).start()  # запуск бота в отдельном потоке
    app.run(debug=True, host='0.0.0.0', port=5000)  # Запуск Flask-приложения
