import telebot
import sqlite3
from telebot import types

# توکن ربات تلگرام خود را اینجا قرار دهید
TOKEN = '8110388329:AAGOt7it4v07i1uJp8yBRcDdD3YVz7VH6dM'
bot = telebot.TeleBot(TOKEN)

# اتصال به دیتابیس SQLite
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()

# ایجاد جدول کاربران اگر وجود ندارد
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE,
    phone TEXT,
    first_name TEXT,
    last_name TEXT,
    province TEXT,
    city TEXT
)
''')

# ایجاد جدول ادمین‌ها اگر وجود ندارد
cursor.execute('''
CREATE TABLE IF NOT EXISTS admins (
    user_id INTEGER PRIMARY KEY
)
''')

# ایجاد جدول محتوا اگر وجود ندارد
cursor.execute('''
CREATE TABLE IF NOT EXISTS contents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT,
    type TEXT,
    content TEXT
)
''')
conn.commit()

# دیکشنری برای ذخیره اطلاعات موقت کاربران
user_data = {}

# دیکشنری برای ذخیره اطلاعات موقت ادمین‌ها
admin_data = {}

# هندلر برای دستور /start
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    # بررسی آیا کاربر ادمین است
    cursor.execute('SELECT * FROM admins WHERE user_id = ?', (user_id,))
    admin = cursor.fetchone()
    if admin:
        # کاربر ادمین است، نمایش انتخاب پنل
        show_admin_choice(message.chat.id)
        return
    # بررسی آیا کاربر قبلاً ثبت نام کرده
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    if user:
        # کاربر ثبت نام کرده، مستقیم به منوی اصلی برو
        show_main_menu(message.chat.id)
    else:
        # کاربر جدید، شروع ثبت نام
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        button = types.KeyboardButton(text="ارسال شماره تلفن", request_contact=True)
        markup.add(button)
        bot.send_message(message.chat.id, "سلام! 😊 لطفا شماره تلفن خود را ارسال کنید. 📱", reply_markup=markup)

# هندلر برای دستور /help
@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.chat.id, "تکست بخر معتبرترین پلتفرم ترانه ملودی و تنظیم آهنگسازی در ایران با سابقه کاری درخشان ۱۰ ساله و افتخار همکاری با اکثر خوانندگان مطرح کشور را داشته است")

# هندلر برای دستور /makeadmin (برای افزودن ادمین اولیه)
@bot.message_handler(commands=['makeadmin'])
def make_admin(message):
    user_id = message.from_user.id
    cursor.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (user_id,))
    conn.commit()
    bot.send_message(message.chat.id, "شما به عنوان ادمین اضافه شدید. ✅ حالا از /start استفاده کنید.")

# هندلر برای دریافت شماره تلفن
@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    if message.contact is not None:
        user_id = message.from_user.id
        phone = message.contact.phone_number
        user_data[user_id] = {'phone': phone}
        bot.send_message(message.chat.id, "شماره تلفن دریافت شد! ✅ حالا لطفا نام خود را وارد کنید. 👤")

# هندلر برای دریافت نام
@bot.message_handler(func=lambda message: message.from_user.id in user_data and 'first_name' not in user_data[message.from_user.id])
def handle_first_name(message):
    user_id = message.from_user.id
    first_name = message.text
    user_data[user_id]['first_name'] = first_name
    bot.send_message(message.chat.id, "نام دریافت شد! 👍 حالا لطفا نام خانوادگی خود را وارد کنید. 👨‍👩‍👧‍👦")

# هندلر برای دریافت نام خانوادگی
@bot.message_handler(func=lambda message: message.from_user.id in user_data and 'first_name' in user_data[message.from_user.id] and 'last_name' not in user_data[message.from_user.id])
def handle_last_name(message):
    user_id = message.from_user.id
    last_name = message.text
    user_data[user_id]['last_name'] = last_name
    # لیست استان‌ها
    provinces = ['تهران', 'اصفهان', 'خراسان رضوی', 'فارس', 'مازندران', 'گیلان', 'آذربایجان شرقی', 'آذربایجان غربی', 'کرمان', 'سیستان و بلوچستان', 'هرمزگان', 'بوشهر', 'چهارمحال و بختیاری', 'یزد', 'سمنان', 'گلستان', 'اردبیل', 'زنجان', 'قزوین', 'البرز', 'قم', 'مرکزی', 'همدان', 'کردستان', 'کرمانشاه', 'لرستان', 'ایلام', 'خوزستان', 'کهگیلویه و بویراحمد', 'ایلام']
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    for province in provinces:
        markup.add(types.KeyboardButton(province))
    bot.send_message(message.chat.id, "نام خانوادگی دریافت شد! 👏 حالا لطفا استان خود را انتخاب کنید. 🗺️", reply_markup=markup)

# هندلر برای دریافت استان
@bot.message_handler(func=lambda message: message.from_user.id in user_data and 'last_name' in user_data[message.from_user.id] and 'province' not in user_data[message.from_user.id])
def handle_province(message):
    user_id = message.from_user.id
    province = message.text
    user_data[user_id]['province'] = province
    # لیست شهرهای مرکز استان‌ها (مثال ساده)
    cities = {
        'تهران': 'تهران',
        'اصفهان': 'اصفهان',
        'خراسان رضوی': 'مشهد',
        'فارس': 'شیراز',
        'مازندران': 'ساری',
        'گیلان': 'رشت',
        'آذربایجان شرقی': 'تبریز',
        'آذربایجان غربی': 'ارومیه',
        'کرمان': 'کرمان',
        'سیستان و بلوچستان': 'زاهدان',
        'هرمزگان': 'بندرعباس',
        'بوشهر': 'بوشهر',
        'چهارمحال و بختیاری': 'شهرکرد',
        'یزد': 'یزد',
        'سمنان': 'سمنان',
        'گلستان': 'گرگان',
        'اردبیل': 'اردبیل',
        'زنجان': 'زنجان',
        'قزوین': 'قزوین',
        'البرز': 'کرج',
        'قم': 'قم',
        'مرکزی': 'اراک',
        'همدان': 'همدان',
        'کردستان': 'سنندج',
        'کرمانشاه': 'کرمانشاه',
        'لرستان': 'خرم آباد',
        'ایلام': 'ایلام',
        'خوزستان': 'اهواز',
        'کهگیلویه و بویراحمد': 'یاسوج'
    }
    city = cities.get(province, 'نامشخص')
    user_data[user_id]['city'] = city
    # ذخیره در دیتابیس
    cursor.execute('''
    INSERT INTO users (user_id, phone, first_name, last_name, province, city)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, user_data[user_id]['phone'], user_data[user_id]['first_name'], user_data[user_id]['last_name'], province, city))
    conn.commit()
    bot.send_message(message.chat.id, f"ثبت نام شما کامل شد! 🎉 اطلاعات شما:\nشماره: {user_data[user_id]['phone']} 📞\nنام: {user_data[user_id]['first_name']} 👤\nنام خانوادگی: {user_data[user_id]['last_name']} 👨‍👩‍👧‍👦\nاستان: {province} 🗺️\nشهر: {city} 🏙️")
    # پاک کردن داده‌های موقت
    del user_data[user_id]
    # نمایش منوی اصلی
    show_main_menu(message.chat.id)

# تابع نمایش انتخاب پنل برای ادمین
def show_admin_choice(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("پنل ادمین 👑"))
    markup.add(types.KeyboardButton("پنل کاربر 👤"))
    bot.send_message(chat_id, "شما ادمین هستید! لطفا پنل مورد نظر را انتخاب کنید. 👑", reply_markup=markup)

# تابع نمایش منوی اصلی
def show_main_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("پر بازدید ترین ترک ها 🔥"))
    markup.add(types.KeyboardButton("پکیج اقتصادی 💰"))
    markup.add(types.KeyboardButton("پکیج مگاهیت VIP 👑"))
    markup.add(types.KeyboardButton("ارتباط با ما 📞"))
    bot.send_message(chat_id, "تکست بخر معتبرترین پلتفرم ترانه ملودی و تنظیم آهنگسازی در ایران با سابقه کاری درخشان ۱۰ ساله و افتخار همکاری با اکثر خوانندگان مطرح کشور را داشته است\n\nبه منوی اصلی خوش آمدید! لطفا گزینه مورد نظر را انتخاب کنید. 😊", reply_markup=markup)

# هندلر برای دکمه‌های منوی اصلی
@bot.message_handler(func=lambda message: message.text == "پر بازدید ترین ترک ها 🔥")
def top_tracks(message):
    cursor.execute('SELECT content FROM contents WHERE category = ? AND type = ?', ("پر بازدید ترین ترک ها 🔥", "text"))
    texts = cursor.fetchall()
    cursor.execute('SELECT content FROM contents WHERE category = ? AND type = ?', ("پر بازدید ترین ترک ها 🔥", "music"))
    musics = cursor.fetchall()
    response = "لیست پر بازدید ترین ترک ها:\n"
    for i, (text,) in enumerate(texts):
        response += f"{i+1}. {text}\n"
    bot.send_message(message.chat.id, response)
    for music in musics:
        bot.send_document(message.chat.id, music[0])

@bot.message_handler(func=lambda message: message.text == "پکیج اقتصادی 💰")
def economic_package(message):
    cursor.execute('SELECT content FROM contents WHERE category = ? AND type = ?', ("پکیج اقتصادی 💰", "text"))
    texts = cursor.fetchall()
    cursor.execute('SELECT content FROM contents WHERE category = ? AND type = ?', ("پکیج اقتصادی 💰", "music"))
    musics = cursor.fetchall()
    response = "پکیج اقتصادی:\n"
    for i, (text,) in enumerate(texts):
        response += f"{i+1}. {text}\n"
    bot.send_message(message.chat.id, response)
    for music in musics:
        bot.send_document(message.chat.id, music[0])

@bot.message_handler(func=lambda message: message.text == "پکیج مگاهیت VIP 👑")
def vip_package(message):
    cursor.execute('SELECT content FROM contents WHERE category = ? AND type = ?', ("پکیج مگاهیت VIP 👑", "text"))
    texts = cursor.fetchall()
    cursor.execute('SELECT content FROM contents WHERE category = ? AND type = ?', ("پکیج مگاهیت VIP 👑", "music"))
    musics = cursor.fetchall()
    response = "پکیج مگاهیت VIP:\n"
    for i, (text,) in enumerate(texts):
        response += f"{i+1}. {text}\n"
    bot.send_message(message.chat.id, response)
    for music in musics:
        bot.send_document(message.chat.id, music[0])

@bot.message_handler(func=lambda message: message.text == "ارتباط با ما 📞")
def contact_us(message):
    bot.send_message(message.chat.id, "برای ارتباط با ما:\nشماره تلفن: ۰۹۱۲۳۴۵۶۷۸۹\nایمیل: info@example.com\nسایت: www.example.com")

# تابع نمایش پنل ادمین
def show_admin_panel(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("لیست کاربران 👥"))
    markup.add(types.KeyboardButton("افزودن ادمین ➕"))
    markup.add(types.KeyboardButton("افزودن موزیک به پر بازدید ترین ترک ها 🎵🔥"))
    markup.add(types.KeyboardButton("افزودن موزیک به پکیج اقتصادی 🎵💰"))
    markup.add(types.KeyboardButton("افزودن موزیک به پکیج مگاهیت VIP 🎵👑"))
    markup.add(types.KeyboardButton("افزودن متن به پر بازدید ترین ترک ها 📝🔥"))
    markup.add(types.KeyboardButton("افزودن متن به پکیج اقتصادی 📝💰"))
    markup.add(types.KeyboardButton("افزودن متن به پکیج مگاهیت VIP 📝👑"))
    markup.add(types.KeyboardButton("بازگشت به منوی اصلی 🔙"))
    bot.send_message(chat_id, "به پنل ادمین خوش آمدید! لطفا گزینه مورد نظر را انتخاب کنید. 👑", reply_markup=markup)

# هندلر برای پنل ادمین
@bot.message_handler(func=lambda message: message.text == "لیست کاربران 👥")
def list_users(message):
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    if users:
        user_list = "\n".join([f"ID: {user[1]}, نام: {user[3]} {user[4]}, استان: {user[5]}, شهر: {user[6]}" for user in users])
        bot.send_message(message.chat.id, f"لیست کاربران:\n{user_list}")
    else:
        bot.send_message(message.chat.id, "هیچ کاربری ثبت نام نکرده است.")

@bot.message_handler(func=lambda message: message.text == "افزودن ادمین ➕")
def add_admin_prompt(message):
    bot.send_message(message.chat.id, "لطفا شناسه عددی کاربر را برای افزودن به عنوان ادمین وارد کنید. 🔢")

@bot.message_handler(func=lambda message: message.text.isdigit() and message.from_user.id in [row[0] for row in cursor.execute('SELECT user_id FROM admins').fetchall()])
def handle_add_admin(message):
    admin_id = int(message.text)
    cursor.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (admin_id,))
    conn.commit()
    bot.send_message(message.chat.id, f"کاربر با شناسه {admin_id} به عنوان ادمین اضافه شد. ✅")

# هندلر برای افزودن موزیک به هر دسته‌بندی
@bot.message_handler(func=lambda message: message.text == "افزودن موزیک به پر بازدید ترین ترک ها 🎵🔥")
def add_music_top_tracks(message):
    admin_data[message.from_user.id] = {'action': 'add_music', 'category': "پر بازدید ترین ترک ها 🔥", 'step': 'music'}
    bot.send_message(message.chat.id, "لطفا فایل موزیک را ارسال کنید. 🎵")

@bot.message_handler(func=lambda message: message.text == "افزودن موزیک به پکیج اقتصادی 🎵💰")
def add_music_economic(message):
    admin_data[message.from_user.id] = {'action': 'add_music', 'category': "پکیج اقتصادی 💰", 'step': 'music'}
    bot.send_message(message.chat.id, "لطفا فایل موزیک را ارسال کنید. 🎵")

@bot.message_handler(func=lambda message: message.text == "افزودن موزیک به پکیج مگاهیت VIP 🎵👑")
def add_music_vip(message):
    admin_data[message.from_user.id] = {'action': 'add_music', 'category': "پکیج مگاهیت VIP 👑", 'step': 'music'}
    bot.send_message(message.chat.id, "لطفا فایل موزیک را ارسال کنید. 🎵")

# هندلر برای افزودن متن به هر دسته‌بندی
@bot.message_handler(func=lambda message: message.text == "افزودن متن به پر بازدید ترین ترک ها 📝🔥")
def add_text_top_tracks(message):
    admin_data[message.from_user.id] = {'action': 'add_text', 'category': "پر بازدید ترین ترک ها 🔥", 'step': 'text'}
    bot.send_message(message.chat.id, "لطفا متن اولیه را وارد کنید. 📝")

@bot.message_handler(func=lambda message: message.text == "افزودن متن به پکیج اقتصادی 📝💰")
def add_text_economic(message):
    admin_data[message.from_user.id] = {'action': 'add_text', 'category': "پکیج اقتصادی 💰", 'step': 'text'}
    bot.send_message(message.chat.id, "لطفا متن اولیه را وارد کنید. 📝")

@bot.message_handler(func=lambda message: message.text == "افزودن متن به پکیج مگاهیت VIP 📝👑")
def add_text_vip(message):
    admin_data[message.from_user.id] = {'action': 'add_text', 'category': "پکیج مگاهیت VIP 👑", 'step': 'text'}
    bot.send_message(message.chat.id, "لطفا متن اولیه را وارد کنید. 📝")

@bot.message_handler(content_types=['audio', 'document'], func=lambda message: message.from_user.id in admin_data and admin_data[message.from_user.id].get('action') == 'add_music')
def handle_add_music(message):
    user_id = message.from_user.id
    step = admin_data[user_id]['step']
    if step == 'music':
        if message.audio or message.document:
            # ذخیره فایل موزیک (در اینجا فقط پیام می‌دهیم، در واقعیت باید فایل را ذخیره کنید)
            file_id = message.audio.file_id if message.audio else message.document.file_id
            admin_data[user_id]['music'] = file_id
            admin_data[user_id]['step'] = 'text'
            bot.send_message(message.chat.id, "موزیک دریافت شد. حالا لطفا متن اولیه را وارد کنید. 📝")
        else:
            bot.send_message(message.chat.id, "لطفا فایل موزیک ارسال کنید.")

@bot.message_handler(func=lambda message: message.from_user.id in admin_data and admin_data[message.from_user.id].get('action') == 'add_music' and admin_data[message.from_user.id]['step'] == 'text')
def handle_add_text(message):
    user_id = message.from_user.id
    category = admin_data[user_id]['category']
    music = admin_data[user_id]['music']
    text = message.text
    # ذخیره در دیتابیس
    cursor.execute('INSERT INTO contents (category, type, content) VALUES (?, ?, ?)', (category, 'music', music))
    cursor.execute('INSERT INTO contents (category, type, content) VALUES (?, ?, ?)', (category, 'text', text))
    conn.commit()
    bot.send_message(message.chat.id, "موزیک و متن اولیه ذخیره شد. ✅")
    del admin_data[user_id]



@bot.message_handler(func=lambda message: message.from_user.id in admin_data and admin_data[message.from_user.id].get('action') == 'add_text' and admin_data[message.from_user.id]['step'] == 'text')
def handle_add_text_only(message):
    user_id = message.from_user.id
    category = admin_data[user_id]['category']
    text = message.text
    cursor.execute('INSERT INTO contents (category, type, content) VALUES (?, ?, ?)', (category, 'text', text))
    conn.commit()
    bot.send_message(message.chat.id, "متن اولیه ذخیره شد. ✅")
    del admin_data[user_id]

# هندلر برای انتخاب پنل ادمین یا کاربر
@bot.message_handler(func=lambda message: message.text == "پنل ادمین 👑")
def admin_panel_choice(message):
    show_admin_panel(message.chat.id)

@bot.message_handler(func=lambda message: message.text == "پنل کاربر 👤")
def user_panel_choice(message):
    show_main_menu(message.chat.id)

@bot.message_handler(func=lambda message: message.text == "بازگشت به منوی اصلی 🔙")
def back_to_main(message):
    show_main_menu(message.chat.id)

# هندلر برای پیام‌های دیگر
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "لطفا از دستور /start استفاده کنید تا ثبت نام کنید. 🤖")

if __name__ == '__main__':
    bot.polling()
