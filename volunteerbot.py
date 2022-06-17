from tracemalloc import stop
import telebot
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
import random
import datetime
import urllib.parse
import requests

password= "Pass word"

API_TOKEN = '5372774502:AAEg4cQlZGLjj8QFtwmu1NxXALEy89wbj08'
bot = telebot.TeleBot(API_TOKEN)

conn = sqlite3.connect('diploma.db', check_same_thread=False)
cursor = conn.cursor()



userInputData = {}

vol_dict = {}

order_delete_dict = {}

class Vol:
    def __init__(self, name):
        self.first_name = name
        self.last_name = None
        self.sex = None

class Order:
    def __init__(self, desc):
        self.desc = desc
        self.urgency = None
        self.region = None

def gen_order_markup():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(InlineKeyboardButton("Взяти", callback_data="order_accept"),
                InlineKeyboardButton("Далі", callback_data="order_next"),
                InlineKeyboardButton("Скарга", callback_data="order_report"),
                InlineKeyboardButton("В меню", callback_data="order_menu"))
    return markup


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "order_accept":

        bot.answer_callback_query(call.id, "order_accept")
    elif call.data == "order_next":
        bot.answer_callback_query(call.id, "order_next")
    elif call.data == "order_report":
        bot.answer_callback_query(call.id, "order_report")
    elif call.data == "order_menu":
        bot.answer_callback_query(call.id, "order_menu")


# /help
@bot.message_handler(commands=['help'])
def process_help(message):
    chat_id=message.chat.id
    bot.send_message(chat_id, '/start - почати роботу з ботом\
\n/help - переглянути список команд\
\n/register - реєстрація\
\n/orders - переглянути замовлення\
\n/my_orders - ваші активні замовлення\
\n/finished_orders - ваші завершені замовлення\
\n/close_order - завершити замовлення\
\n/remove_order - відмовитись від замовлення', reply_markup=types.ReplyKeyboardRemove())

# /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    sql = f"SELECT * FROM volunteers WHERE tg_volunteer_id = {chat_id}"
    cursor.execute(sql)
    volunteer = cursor.fetchall()
    if volunteer:
        msg = bot.reply_to(message, "Вітаємо! /start", reply_markup=types.ReplyKeyboardRemove())
    else:
        msg = bot.reply_to(message, "Це бот для волонтерів. Для продовження введіть пароль:")
        bot.register_next_step_handler(msg, process_password_step)

def process_password_step(message):
    try:
        command = check_command(message)
        if command:
            command(message)
            return
        if message.text != password:
            msg = bot.reply_to(message, "Неправильний пароль. Спробуйте ще раз:")
            bot.register_next_step_handler(msg, process_password_step)
            return
        chat_id = message.chat.id
        print(chat_id)
        cursor.execute('INSERT INTO volunteers (tg_volunteer_id, firstname, lastname, birth_date) VALUES (?, ?, ?, ?)', (chat_id, None, None, None))
        conn.commit()
        msg = bot.reply_to(message, "Доступ до боту відкритий.")
        process_help(message)
        # process_register(message)
    except Exception as e:
        print(e)
        bot.reply_to(message, "Ви не ввели пароль")

# /register
@bot.message_handler(commands=['register'])
def process_register(message):
    sql=f'SELECT firstname FROM volunteers WHERE tg_volunteer_id = {message.chat.id}'
    cursor.execute(sql)
    check_user_availability=cursor.fetchall()
    if not check_user_availability:
        send_welcome(message)
        return
    if check_user_availability[0][0]:
        bot.send_message(message.chat.id, 'Ви вже зареєстровані!', reply_markup=types.ReplyKeyboardRemove())
        return
    msg = bot.reply_to(message, "Введіть своє ім'я (без прізвища)")
    bot.register_next_step_handler(msg, process_firstname_step)


def process_firstname_step(message):
    try:
        command = check_command(message)
        if command:
            command(message)
            return
        chat_id = message.chat.id
        first_name = message.text
        user = Vol(first_name)
        vol_dict[chat_id] = user
        msg = bot.reply_to(message, "Введіть своє прізвище")
        bot.register_next_step_handler(msg, process_lastname_step)
    except Exception as e:
        bot.reply_to(message, "Ви не ввели ім'я")

def process_lastname_step(message):
    try:
        command = check_command(message)
        if command:
            command(message)
            return
        chat_id = message.chat.id
        last_name = message.text
        user = vol_dict[chat_id]
        user.last_name = last_name
        msg = bot.reply_to(message, "Введіть дату народження (у форматі dd/mm/yyyy)")
        bot.register_next_step_handler(msg, process_age_step)
    except Exception as e:
        bot.reply_to(message, "Ви не ввели прізвище")


def process_age_step(message):
    try:
        command = check_command(message)
        if command:
            command(message)
            return
        chat_id = message.chat.id
        age = message.text
        user = vol_dict[chat_id]
        user.age = age
        try:
            date_of_birth = datetime.datetime.strptime(age, "%d/%m/%Y")
            day, month, year = age.split("/")
            print(day)
            print(month)
            print(year)
            if int(year) > 2004:
                bot.send_message(chat_id, 'Ви занадто молоді для використання бота')
                return
        except:
            # print("Incorrect date!")
            bot.send_message(chat_id, 'Введіть дату в коректному форматі')
            bot.register_next_step_handler(message, process_age_step)
            return
        bot.reply_to(message, "Ви успішно зареєстровані!")
        add_user_to_table(chat_id)
    except Exception as e:
        bot.reply_to(message, 'Ви не ввели ваш вік')

def add_user_to_table(chat_id):
    try:
        user = vol_dict[chat_id]
        firstname = user.first_name
        lastname = user.last_name
        age = user.age
        bot.send_message(chat_id, "Ім'я: " + firstname + '\nПрізвище: ' + lastname + '\nДата народження: ' + age)
        db_users_insert(chat_id, firstname=firstname, lastname=lastname, age=age)
    except Exception as e:
        print(e)
        pass

def db_users_insert(chat_id, firstname: str, lastname: str, age: str):
	cursor.execute(f'UPDATE volunteers SET firstname=?, lastname=?, birth_date=? WHERE tg_volunteer_id={chat_id}' , (firstname, lastname, age))
	conn.commit()

# /orders
@bot.message_handler(commands=['orders'])
def send_order(message, id=None):
    sql=f'SELECT firstname FROM volunteers WHERE tg_volunteer_id = {message.chat.id}'
    cursor.execute(sql)
    check_user_availability=cursor.fetchall()
    print(check_user_availability)
    if not check_user_availability:
        send_welcome(message)
        return
    if check_user_availability[0][0] is None:
        bot.send_message(message.chat.id, 'Ви не зареєстровані!')
        send_welcome(message)
        return
    try:
        sql1 = f"SELECT DISTINCT orders.order_id, orders.order_desc, order_urgency.order_urgency_desc, regions.region_description, reports.volunteer_id \
            FROM orders JOIN order_urgency on orders.order_urgency_id = order_urgency.order_urgency_id \
            JOIN regions on orders.region_id = regions.region_id LEFT JOIN reports on orders.order_id = reports.order_id \
            LEFT JOIN volunteers on reports.volunteer_id = volunteers.volunteer_id \
            WHERE (volunteers.tg_volunteer_id != {message.chat.id} OR volunteers.tg_volunteer_id IS NULL) AND (orders.order_status = 'free')"
        cursor.execute(sql1)
        orders = cursor.fetchall()
        print(orders)
        l = len(orders)
        i = random.randint(0, (l-1))
        if l > 1:
            while orders[i][0] == id:
                i = random.randint(0, (l-1))
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add('Взяти', 'Далі', 'Скарга', 'В меню')
        msg = bot.reply_to(message, f'Номер замовлення: {orders[i][0]}\nТекст замовлення: {orders[i][1]}\nСтепінь терміновості: {orders[i][2]}\nРегіон замовлення: {orders[i][3]}', reply_markup=markup)
        bot.register_next_step_handler(msg, process_send_order, id=orders[i][0])
    except Exception as e:
        bot.reply_to(message, 'Вільні замовлення відсутні')
        process_help(message)


def process_send_order(message, id):
    try:
        command = check_command(message)
        if command:
            command(message)
            return
        chat_id=message.chat.id
        reply = message.text
        if reply == 'Взяти':
            bot.send_message (chat_id, 'Замовлення взяте')
            sql_volunteer_id=f'SELECT volunteer_id FROM volunteers WHERE tg_volunteer_id = {message.chat.id}'
            cursor.execute(sql_volunteer_id)
            volunteer_id=cursor.fetchall()[0][0]
            process_take_order(id=id, volunteer_id=volunteer_id)            
        elif reply == 'Далі':
            send_order(message, id)
        elif reply == 'Скарга':            
            bot.send_message(chat_id, 'Скаргу надіслано')
            sql_user_id=f'SELECT user_id FROM orders WHERE order_id={id}'
            cursor.execute(sql_user_id)
            user_id=cursor.fetchall()[0][0]
            user=int(user_id)
            sql_volunteer_id=f'SELECT volunteer_id FROM volunteers WHERE tg_volunteer_id={message.chat.id}'
            cursor.execute(sql_volunteer_id)
            volunteer_id=cursor.fetchall()[0][0]
            vol=int(volunteer_id)
            print(f'volunteer_id type: {type(volunteer_id)}')
            print(f'user_id type: {type(user_id)}')
            print(volunteer_id)
            print(user_id)
            process_report_order(id, vol=vol, user=user)
        elif reply == 'В меню':
            bot.send_message(chat_id, 'Перехід в меню', reply_markup=types.ReplyKeyboardRemove())
            process_help(message)
            return
        else:
            raise Exception("oops")
    except Exception as e:
        print(e)
        bot.reply_to(message, 'oooops')

def process_take_order(id: int, volunteer_id: int):
    try:
        sql_take=f"UPDATE orders SET order_status = 'in progress', volunteer_id={volunteer_id} WHERE order_id ={id}"
        cursor.execute(sql_take)
        conn.commit()
    except Exception:
        print("oops")

def process_report_order(id, vol: int, user: int):
    cursor.execute('INSERT INTO reports (volunteer_id, user_id, order_id) VALUES (?, ?, ?)', (vol, user, id))
    cursor.execute(f'UPDATE users SET reports = reports + 1 WHERE id={user}')
    cursor.execute(f'UPDATE orders SET reports = reports + 1 WHERE order_id={id}')
    conn.commit()

# /my_orders
@bot.message_handler(commands=['my_orders'])
def process_my_orders(message):
    select_orders=f'SELECT orders.order_id, orders.order_desc, orders.order_status, regions.region_description, order_urgency.order_urgency_desc \
    FROM orders JOIN volunteers on orders.volunteer_id = volunteers.volunteer_id JOIN regions on orders.region_id = regions.region_id \
    JOIN order_urgency on orders.order_urgency_id = order_urgency.order_urgency_id \
    WHERE volunteers.tg_volunteer_id = {message.chat.id} and orders.order_status="in progress"'
    cursor.execute(select_orders)
    user_orders=cursor.fetchall()
    if user_orders:
        for order in user_orders:
            bot.send_message(message.chat.id, f'Номер замовлення: {order[0]}\nТекст замовлення: {order[1]}\nСтатус замовлення: {order[2]}\nРегіон замовлення: {order[3]}\nТерміновість: {order[4]}', reply_markup=types.ReplyKeyboardRemove())
    else:
        bot.send_message(message.chat.id, 'У вас немає активних замовлень.', reply_markup=types.ReplyKeyboardRemove())

# /finished_orders
@bot.message_handler(commands=['finished_orders'])
def process_finished_orders(message):
    select_orders=f'SELECT orders.order_id, orders.order_desc, orders.order_status, regions.region_description, order_urgency.order_urgency_desc \
    FROM orders JOIN volunteers on orders.volunteer_id = volunteers.volunteer_id JOIN regions on orders.region_id = regions.region_id \
    JOIN order_urgency on orders.order_urgency_id = order_urgency.order_urgency_id \
    WHERE volunteers.tg_volunteer_id = {message.chat.id} and orders.order_status="finished"'
    cursor.execute(select_orders)
    user_orders=cursor.fetchall()
    if user_orders:
        for order in user_orders:
            bot.send_message(message.chat.id, f'Номер замовлення: {order[0]}\nТекст замовлення: {order[1]}\nСтатус замовлення: {order[2]}\nРегіон замовлення: {order[3]}\nТерміновість: {order[4]}', reply_markup=types.ReplyKeyboardRemove())
    else:
        bot.send_message(message.chat.id, 'У вас немає завершених замовлень.', reply_markup=types.ReplyKeyboardRemove())

# /close_order
@bot.message_handler(commands=['close_order'])
def close_order(message):
    select_orders=f"SELECT orders.order_id, orders.order_desc, orders.order_status, regions.region_description, order_urgency.order_urgency_desc \
    FROM orders JOIN volunteers on orders.volunteer_id = volunteers.volunteer_id JOIN regions on orders.region_id = regions.region_id \
    JOIN order_urgency on orders.order_urgency_id = order_urgency.order_urgency_id \
    WHERE volunteers.tg_volunteer_id = {message.chat.id} and orders.order_status='in progress'"
    cursor.execute(select_orders)
    user_orders=cursor.fetchall()
    if not user_orders:
        process_my_orders(message)
        return
    for order in user_orders:
        bot.send_message(message.chat.id, f'Номер замовлення: {order[0]}\nТекст замовлення: {order[1]}\nСтатус замовлення: {order[2]}\nРегіон замовлення: {order[3]}\nТерміновість: {order[4]}')
    msg = bot.reply_to(message, "Введіть номер замовлення, яке хочете завершити.", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, process_close_order_step)

def process_close_order_step(message):
    command = check_command(message)
    if command:
        command(message)
        return
    select_orders=f'SELECT orders.order_id, orders.order_desc, orders.order_status, regions.region_description, order_urgency.order_urgency_desc \
    FROM orders JOIN volunteers on orders.volunteer_id = volunteers.volunteer_id JOIN regions on orders.region_id = regions.region_id \
    JOIN order_urgency on orders.order_urgency_id = order_urgency.order_urgency_id \
    WHERE volunteers.tg_volunteer_id = {message.chat.id}'
    cursor.execute(select_orders)
    user_orders=cursor.fetchall()
    ids = [i[0] for i in user_orders]
    if message.text.isdigit() and int(message.text) in ids:
        order_delete_dict[message.chat.id] = int(message.text)
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add('Так', 'Ні')
        msg = bot.reply_to(message, 'Чи ви підтвержуєте завершення замовлення?', reply_markup=markup)
        bot.register_next_step_handler(msg, process_confirm_close_order_step)
    else:
        msg = bot.reply_to(message, "Введіть правильний номер замовлення.")
        bot.register_next_step_handler(msg, process_close_order_step)

def process_confirm_close_order_step(message):
    command = check_command(message)
    if command:
        command(message)
        return
    if message.text == 'Так':
        order_id = order_delete_dict[message.chat.id]
        select_user=f'SELECT users.tg_user_id FROM orders JOIN users on orders.user_id = users.id WHERE orders.order_id = {order_id} AND orders.order_status = "in progress"'
        cursor.execute(select_user)
        user=cursor.fetchall()
        print(user)
        if user:
            select_order=f'SELECT orders.order_id, orders.order_desc, regions.region_description \
            FROM orders JOIN regions on orders.region_id = regions.region_id \
            WHERE orders.order_id = {order_id}'
            cursor.execute(select_order)
            order=cursor.fetchall()
            print(order)
            user_message = f'Волонтер завершив замовлення: \n\nНомер замовлення: {order[0][0]}\nТекст замовлення: {order[0][1]}\nРегіон замовлення: {order[0][2]}'
            user_message_url = urllib.parse.quote(user_message)
            requests.get(f'https://api.telegram.org/bot5315016907:AAHzS9bOjvaJ6tGxonTCMH-i_fTaC98sBEc/sendMessage?chat_id={user[0][0]}&text={user_message_url}')
        delete_order_sql = f'UPDATE orders SET order_status="finished" WHERE order_id = {order_id}'
        cursor.execute(delete_order_sql)
        conn.commit()
        order_delete_dict.pop(message.chat.id)
        bot.reply_to(message, 'Замовлення завершене.', reply_markup=types.ReplyKeyboardRemove())

# /remove_order
@bot.message_handler(commands=['remove_order'])
def remove_order(message):
    select_orders=f"SELECT orders.order_id, orders.order_desc, orders.order_status, regions.region_description, order_urgency.order_urgency_desc \
    FROM orders JOIN volunteers on orders.volunteer_id = volunteers.volunteer_id JOIN regions on orders.region_id = regions.region_id \
    JOIN order_urgency on orders.order_urgency_id = order_urgency.order_urgency_id \
    WHERE volunteers.tg_volunteer_id = {message.chat.id} and orders.order_status='in progress'"
    cursor.execute(select_orders)
    user_orders=cursor.fetchall()
    if not user_orders:
        process_my_orders(message)
        return
    for order in user_orders:
        bot.send_message(message.chat.id, f'Номер замовлення: {order[0]}\nТекст замовлення: {order[1]}\nСтатус замовлення: {order[2]}\nРегіон замовлення: {order[3]}\nТерміновість: {order[4]}')
    msg = bot.reply_to(message, "Введіть номер замовлення, від виконання якого хочете відмовитись.", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, process_remove_order_step)

def process_remove_order_step(message):
    command = check_command(message)
    if command:
        command(message)
        return
    select_orders=f'SELECT orders.order_id, orders.order_desc, orders.order_status, regions.region_description, order_urgency.order_urgency_desc \
    FROM orders JOIN volunteers on orders.volunteer_id = volunteers.volunteer_id JOIN regions on orders.region_id = regions.region_id \
    JOIN order_urgency on orders.order_urgency_id = order_urgency.order_urgency_id \
    WHERE volunteers.tg_volunteer_id = {message.chat.id}'
    cursor.execute(select_orders)
    user_orders=cursor.fetchall()
    ids = [i[0] for i in user_orders]
    if message.text.isdigit() and int(message.text) in ids:
        order_delete_dict[message.chat.id] = int(message.text)
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add('Так', 'Ні')
        msg = bot.reply_to(message, 'Чи ви підтвержуєте відміну виконання замовлення?', reply_markup=markup)
        bot.register_next_step_handler(msg, process_confirm_remove_order_step)
    else:
        msg = bot.reply_to(message, "Введіть правильний номер замовлення.")
        bot.register_next_step_handler(msg, process_remove_order_step)

def process_confirm_remove_order_step(message):
    command = check_command(message)
    if command:
        command(message)
        return
    if message.text == 'Так':
        order_id = order_delete_dict[message.chat.id]
        select_user=f'SELECT users.tg_user_id FROM orders JOIN users on orders.user_id = users.id WHERE orders.order_id = {order_id} AND orders.order_status = "in progress"'
        cursor.execute(select_user)
        user=cursor.fetchall()
        print(user)
        if user:
            select_order=f'SELECT orders.order_id, orders.order_desc, regions.region_description \
            FROM orders JOIN regions on orders.region_id = regions.region_id \
            WHERE orders.order_id = {order_id}'
            cursor.execute(select_order)
            order=cursor.fetchall()
            print(order)
            user_message = f'Волонтер відмінив виконання замовлення: \n\nНомер замовлення: {order[0][0]}\nТекст замовлення: {order[0][1]}\nРегіон замовлення: {order[0][2]}.\nЙого зможе взяти інший волонтер.'
            user_message_url = urllib.parse.quote(user_message)
            requests.get(f'https://api.telegram.org/bot5315016907:AAHzS9bOjvaJ6tGxonTCMH-i_fTaC98sBEc/sendMessage?chat_id={user[0][0]}&text={user_message_url}')
        remove_order_sql = f'UPDATE orders SET order_status="free", volunteer_id = NULL WHERE order_id = {order_id}'
        cursor.execute(remove_order_sql)
        conn.commit()
        order_delete_dict.pop(message.chat.id)
        bot.reply_to(message, 'Замовлення завершене.', reply_markup=types.ReplyKeyboardRemove())


def check_command(message):
    try:
        command = cmd_list[message.text]
        return command
    except KeyError:
        return None

#############################################################################################################################################

 #Enable saving next step handlers to file "./.handlers-saves/step.save".
 #Delay=2 means that after any change in next step handlers (e.g. calling register_next_step_handler())
 #saving will hapen after delay 2 seconds.
bot.enable_save_next_step_handlers(delay=2)

cmd_list={'/start': send_welcome, '/help': process_help, '/register': process_register, \
    '/orders': send_order, '/my_orders': process_my_orders, '/finished_orders': process_finished_orders, \
    '/close_order': close_order, '/remove_order': remove_order}
 #Load next_step_handlers from save file (default "./.handlers-saves/step.save")
 #WARNING It will work only if enable_save_next_step_handlers was called!
 #bot.load_next_step_handlers()

if __name__ == '__main__':
    bot.polling(none_stop=True)

one_time_keyboard=True