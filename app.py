import telebot
from PIL import Image, ImageDraw, ImageFont
import os
from telebot import types
import time

BOT_TOKEN = '7666674896:AAHKXKmag-XlJMOM4iPKZsIHJDZDwTgO4VY'
bot = telebot.TeleBot(BOT_TOKEN)

TEMPLATE_FOLDER = 'templates'
user_data = {}

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
    bot.send_message(call.message.chat.id, "✏️ Напиши текст: верх | низ (например: привет | пока)")
    bot.register_next_step_handler(call.message, handle_text_input)

def handle_text_input(message):
    if '|' not in message.text:
        bot.reply_to(message, "⚠️ Неправильный формат! Используй: верх | низ")
        return

    user_data[message.chat.id]['text'] = message.text
    generate_meme(message)

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

        # 📐 Автоматическая настройка размера шрифта под изображение
        font_percent = 0.06 if width > 800 else 0.08

        # Используем стандартный шрифт (работает на всех системах)
        try:
            font = ImageFont.truetype('fonts/Arial.ttf', int(min(width, height) * font_percent))  # Укажите правильный путь
        except IOError:
            font = ImageFont.load_default()  # Стандартный шрифт, если не удалось загрузить Arial

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
            draw_text(top_text, 5, -55, 2)
            draw_text(bottom_text, height - 50, 65, 10)
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

# Запуск бота
def start_polling():
    print("Бот запущен. Ожидаем сообщений...")
    while True:
        try:
            # Запускаем polling для получения новых сообщений
            bot.polling(non_stop=True, interval=1, timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Возникла ошибка: {e}. Переподключение через 15 секунд...")
            time.sleep(15)

if __name__ == '__main__':
    start_polling()
