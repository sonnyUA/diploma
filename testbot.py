import urllib.parse
import requests
import telebot
from telebot import types
import sqlite3
import datetime

API_TOKEN = '5315016907:AAHzS9bOjvaJ6tGxonTCMH-i_fTaC98sBEc'
bot = telebot.TeleBot(API_TOKEN)

conn = sqlite3.connect('diploma.db', check_same_thread=False)
cursor = conn.cursor()



userInputData = {}

user_dict = {}

order_dict = {}

order_delete_dict = {}

class Order:
    def __init__(self, desc):
        self.desc = desc
        self.urgency = None
        self.region = None

class User:
    def __init__(self, name):
        self.first_name = name
        self.last_name = None
        self.sex = None


# Handle '/start' and '/help'
@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    chat_id = message.chat.id
    # try:
    #     u = user_dict[chat_id]
    #     bot.reply_to(message, "Вже зареєстрований")
    # except KeyError:
    msg = bot.reply_to(message, "За командою /register ви можете зареєструватися.\nЗа командою /account ви можете переглянути ваші дані.\n\
За командою /order ви можете створити замовлення.\nЗа командою /my_orders ви можете переглянути свої замовлення.\n\
За командою /delete_order ви можете видалити ваше замовлення.")


# /register
@bot.message_handler(commands=['register'])
def send_register(message):
    sql=f'SELECT id FROM users WHERE tg_user_id = {message.chat.id}'
    cursor.execute(sql)
    check_user_availability=cursor.fetchall()
    # check_user_availability=cursor.fetchall()[0][0]
    if check_user_availability:
        bot.send_message(message.chat.id, 'Ви вже зареєстровані!')
        return
    msg = bot.reply_to(message, "Введіть своє ім'я (без прізвища)")
    bot.register_next_step_handler(msg, process_firstname_step)


def process_firstname_step(message):
    try:
        chat_id = message.chat.id
        first_name = message.text
        user = User(first_name)
        user_dict[chat_id] = user
        msg = bot.reply_to(message, "Введіть своє прізвище")
        bot.register_next_step_handler(msg, process_lastname_step)
    except Exception as e:
        bot.reply_to(message, "Ви не ввели ім'я")


def process_lastname_step(message):
    try:
        chat_id = message.chat.id
        last_name = message.text
        user = user_dict[chat_id]
        user.last_name = last_name
        msg = bot.reply_to(message, "Введіть дату народження (у форматі dd/mm/yyyy)")
        bot.register_next_step_handler(msg, process_age_step)
    except Exception as e:
        bot.reply_to(message, "Ви не ввели прізвище")


def process_age_step(message):
    try:
        chat_id = message.chat.id
        age = message.text
        user = user_dict[chat_id]
        user.age = age
        print(message.text)
        print(type(message.text))
        try:
            date_of_birth = datetime.datetime.strptime(age, "%d/%m/%Y")
            day, month, year = age.split("/")
            print(day)
            print(month)
            print(year)
            if int(year) > 2006:
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
        user = user_dict[chat_id]
        print(user_dict)
        firstname = user.first_name
        lastname = user.last_name
        age = user.age
        # tg_user_id=user.chat_id
        #print(user_dict)
        bot.send_message(chat_id, "Ім'я: " + firstname + '\n Прізвище: ' + lastname + '\n Дата народження: ' + age)
        db_users_insert(tg_user_id=chat_id, firstname=firstname, lastname=lastname, age=age)
    except Exception as e:
        print(e)
        pass

def db_users_insert(tg_user_id: int, firstname: str, lastname: str, age: str):
	cursor.execute('INSERT INTO users (tg_user_id, firstname, lastname, birth_date) VALUES (?, ?, ?, ?)', (tg_user_id, firstname, lastname, age))
	conn.commit()

# /account
@bot.message_handler(commands=['account'])
def send_account(message):
    sql=f'SELECT id FROM users WHERE tg_user_id = {message.chat.id}'
    cursor.execute(sql)
    check_user_availability=cursor.fetchall()
    # check_user_availability=cursor.fetchall()[0][0]
    if not check_user_availability:
        bot.send_message(message.chat.id, 'Ви ще не зареєстровані!')
        send_welcome(message)
        return
    sql = f"SELECT firstname, lastname, birth_date FROM users WHERE tg_user_id = {message.chat.id}"
    cursor.execute(sql)
    user = cursor.fetchall()
    reply = f"Ім'я: {user[0][0]} \nПрізвище: {user[0][1]} \nДата народження: {user[0][2]}"
    msg = bot.reply_to(message, reply)
    
# /order
@bot.message_handler(commands=['order'])
def start_order(message):
    sql=f'SELECT id FROM users WHERE tg_user_id = {message.chat.id}'
    cursor.execute(sql)
    check_user_availability=cursor.fetchall()
    # check_user_availability=cursor.fetchall()[0][0]
    if not check_user_availability:
        bot.send_message(message.chat.id, 'Ви ще не зареєстровані!')
        send_welcome(message)
        return
    cursor.execute(f'SELECT reports FROM users WHERE tg_user_id={message.chat.id} ')
    reports=cursor.fetchall()
    if reports>9:
        bot.send_message(message.chat.id, 'Через велику кількість скарг на ваші замовлення ви не маєте доступу до створення нових замовлень')
        send_welcome(message)
        return
    msg = bot.reply_to(message, "Стисло вкажіть, чого ви потребуєте. Рекомендуємо робити роздільні замовлення для окремих типів речей.\
        Наприклад: в окремому замовленні вкажіть усі ліки, в іншому замовленні вкажіть їжу якої потребуєте, \
        в третьому замовленні вкажіть одяг, якого вам не вистачає.")
    bot.register_next_step_handler(msg, process_urgency_order_step)

def process_urgency_order_step(message):
    try:
        chat_id = message.chat.id
        order_dict[chat_id] = Order(message.text)
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add('Термінове', 'Нетермінове')
        msg = bot.reply_to(message, 'Чи термінове ваше замовлення', reply_markup=markup)
        bot.register_next_step_handler(msg, process_next_order_step)
    except Exception as e:
        bot.reply_to(message, 'oooops')


def process_next_order_step(message):
    try:
        chat_id = message.chat.id
        order_urg = message.text
        order = order_dict[chat_id]
        if (order_urg == 'Термінове'):
            order.urgency = 1
        elif (order_urg == 'Нетермінове'):
            order.urgency = 2
        else:
            msg=bot.send_message(message,'Оберіть степінь терміновості замовлення')
            bot.register_next_step_handler(msg, process_next_order_step)
            return
        sql=f'SELECT * FROM regions'
        cursor.execute(sql)
        regions_ids=cursor.fetchall()
        regions_ids_str = ''
        for i in regions_ids:
            regions_ids_str += f'{i[0]} - {i[1]}\n'
        msg= bot.reply_to(message, f'{regions_ids_str} \nВведіть номер регіону зі списку, що відображено вище, в який треба буде доставити замовлення.', reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, process_order_region_step)
    except Exception as e:
        bot.reply_to(message, 'oooops')

def process_order_region_step(message):
    try:
        chat_id = message.chat.id
        sql=f'SELECT region_id FROM regions'
        cursor.execute(sql)
        regions_ids=cursor.fetchall()
        ids = [i[0] for i in regions_ids]
        if not int(message.text) in ids:
            raise Exception
        order_region = int(message.text)
        order = order_dict[chat_id]
        order.region = order_region
        bot.reply_to(message, 'Замовлення успішно створено')
        add_order_to_table(message)
    except Exception as e:
        bot.reply_to(message, 'you oooops')


def add_order_to_table(message):
    try:
        chat_id = message.chat.id
        order = order_dict[chat_id]
        order_desc = order.desc
        order_urgency_id = order.urgency
        region_id=order.region
        sql2=f'SELECT region_description FROM regions WHERE region_id = {region_id}'
        cursor.execute(sql2)
        region_desc=cursor.fetchall()[0][0]
        sql1=f'SELECT id FROM users WHERE tg_user_id = {message.chat.id}'
        cursor.execute(sql1)
        user_id=cursor.fetchall()[0][0]
        bot.send_message(chat_id, f'Ваше замовлення: {order_desc} \nРегіон замовлення: {region_desc}')
        db_orders_insert(chat_id = chat_id, user_id=user_id, order_desc=order_desc, order_urgency_id=order_urgency_id, region_id=region_id)
    except Exception as e:
        print(e)
        pass

def db_orders_insert(chat_id: int, user_id: int, order_desc: str, order_urgency_id: int, region_id: int):
    try:
        cursor.execute('INSERT INTO orders (order_desc, order_status, user_id, volunteer_id, order_urgency_id, region_id) VALUES (?, ?, ?, ?, ?, ?)', (order_desc, 'free', user_id, None, order_urgency_id, region_id))
        conn.commit()
        order_dict.pop(chat_id)
    except Exception as e:
        print(e)

# /my_orders
@bot.message_handler(commands=['my_orders'])
def my_orders(message):
    sql=f'SELECT id FROM users WHERE tg_user_id = {message.chat.id}'
    cursor.execute(sql)
    check_user_availability=cursor.fetchall()
    # check_user_availability=cursor.fetchall()[0][0]
    if not check_user_availability:
        bot.send_message(message.chat.id, 'Ви ще не зареєстровані!')
        send_welcome(message)
        return
    select_orders=f'SELECT orders.order_id, orders.order_desc, orders.order_status, regions.region_description, order_urgency.odred_urgency_desc \
    FROM orders join users on orders.user_id = users.id join regions on orders.region_id = regions.region_id \
    join order_urgency on orders.order_urgency_id = order_urgency.order_urgency_id WHERE users.tg_user_id = {message.chat.id}'
    cursor.execute(select_orders)
    user_orders=cursor.fetchall()
    for order in user_orders:
        bot.send_message(message.chat.id, f'Номер замовлення: {order[0]}\nТекст замовлення: {order[1]}\nСтатус замовлення: {order[2]}\nРегіон замовлення: {order[3]}\nТерміновість: {order[4]}')

# /delete_order
@bot.message_handler(commands=['delete_order'])
def delete_order(message):
    sql=f'SELECT id FROM users WHERE tg_user_id = {message.chat.id}'
    cursor.execute(sql)
    check_user_availability=cursor.fetchall()
    # check_user_availability=cursor.fetchall()[0][0]
    if not check_user_availability:
        bot.send_message(message.chat.id, 'Ви ще не зареєстровані!')
        send_welcome(message)
        return
    select_orders=f'SELECT orders.order_id, orders.order_desc, orders.order_status, regions.region_description, order_urgency.odred_urgency_desc \
    FROM orders join users on orders.user_id = users.id join regions on orders.region_id = regions.region_id \
    join order_urgency on orders.order_urgency_id = order_urgency.order_urgency_id \
    WHERE users.tg_user_id = {message.chat.id}'
    cursor.execute(select_orders)
    user_orders=cursor.fetchall()
    for order in user_orders:
        bot.send_message(message.chat.id, f'Номер замовлення: {order[0]}\nТекст замовлення: {order[1]}\nСтатус замовлення: {order[2]}\nРегіон замовлення: {order[3]}\nТерміновість: {order[4]}')
    msg = bot.reply_to(message, "Введіть номер замовлення, яке хочете видалити.")
    bot.register_next_step_handler(msg, process_delete_order_step)

def process_delete_order_step(message):
    select_orders=f'SELECT orders.order_id, orders.order_desc, orders.order_status, regions.region_description, order_urgency.odred_urgency_desc \
    FROM orders join users on orders.user_id = users.id join regions on orders.region_id = regions.region_id \
    join order_urgency on orders.order_urgency_id = order_urgency.order_urgency_id WHERE users.tg_user_id = {message.chat.id}'
    cursor.execute(select_orders)
    user_orders=cursor.fetchall()
    ids = [i[0] for i in user_orders]
    if message.text.isdigit() and int(message.text) in ids:
        order_delete_dict[message.chat.id] = int(message.text)
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add('Так', 'Ні')
        msg = bot.reply_to(message, 'Чи ви підтвержуєте видалення замовлення?', reply_markup=markup)
        bot.register_next_step_handler(msg, process_confirm_delete_order_step)
    else:
        msg = bot.reply_to(message, "Введіть правильний номер замовлення.")
        bot.register_next_step_handler(msg, process_delete_order_step)

def process_confirm_delete_order_step(message):
    if message.text == 'Так':
        order_id = order_delete_dict[message.chat.id]
        select_volunteer=f'SELECT volunteers.tg_volunteer_id \
            FROM orders JOIN volunteers on orders.volunteer_id = volunteers.volunteer_id \
            WHERE orders.order_id = {order_id} AND orders.order_status = "progress"'
        cursor.execute(select_volunteer)
        volunteer=cursor.fetchall()
        if volunteer:
            select_order=f'SELECT orders.order_id, orders.order_desc, regions.region_description \
            FROM orders JOIN regions on orders.region_id = regions.region_id WHERE orders.order_id = {order_id}'
            cursor.execute(select_order)
            order=cursor.fetchall()
            volunteer_message = f'Замовник видалив замовлення: \n\nНомер замовлення: {order[0][0]}\nТекст замовлення: {order[0][1]}\nРегіон замовлення: {order[0][2]}'
            volunteer_message_url = urllib.parse.quote(volunteer_message)
            requests.get(f'https://api.telegram.org/bot5372774502:AAEg4cQlZGLjj8QFtwmu1NxXALEy89wbj08/sendMessage?chat_id={volunteer[0][0]}&text={volunteer_message_url}')
        delete_order_sql = f'DELETE FROM orders WHERE order_id = {order_id}'
        cursor.execute(delete_order_sql)
        conn.commit()
        order_delete_dict.pop(message.chat.id)
        bot.reply_to(message, 'Замовлення видалено.')
       


 #Enable saving next step handlers to file "./.handlers-saves/step.save".
 #Delay=2 means that after any change in next step handlers (e.g. calling register_next_step_handler())
 #saving will hapen after delay 2 seconds.
bot.enable_save_next_step_handlers(delay=2)


 #Load next_step_handlers from save file (default "./.handlers-saves/step.save")
 #WARNING It will work only if enable_save_next_step_handlers was called!
 #bot.load_next_step_handlers()

if __name__ == '__main__':
    bot.polling(none_stop=True)

one_time_keyboard=True