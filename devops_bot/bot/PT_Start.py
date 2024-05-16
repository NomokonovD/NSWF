
import logging
import re
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
import paramiko
import os
from dotenv import load_dotenv,find_dotenv
import psycopg2
from psycopg2 import Error
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CallbackQueryHandler
from datetime import datetime

find_dotenv()
load_dotenv()

TOKEN = os.getenv('TOKEN')
host = os.getenv('RM_HOST')
port = os.getenv('RM_PORT')
username = os.getenv('RM_USER')
password = os.getenv('RM_PASSWORD')

# Подключаем логирование
logging.basicConfig(
    filename='logfile.txt', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

# Функция для SSH-соединения и выполнения команд
def execute_ssh_command(command: str):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command(command)
    data = stdout.read() + stderr.read()
    client.close()
    return data.decode('utf-8')


def get_repl_logs(update: Update, context):
    data = execute_ssh_command('docker compose logs db | tail -n 10 | grep repl')
    update.message.reply_text(data)

# Команды мониторинга
def get_release(update: Update, context):
    data = execute_ssh_command('cat /etc/os-release')
    update.message.reply_text(data)

def get_uname(update: Update, context):
    data = execute_ssh_command('uname -a')
    update.message.reply_text(data)

def get_uptime(update: Update, context):
    data = execute_ssh_command('uptime -p')
    update.message.reply_text(data)

def get_df(update: Update, context):
    data = execute_ssh_command('df -h')
    update.message.reply_text(data)

def get_free(update: Update, context):
    data = execute_ssh_command('free -h')
    update.message.reply_text(data)

def get_mpstat(update: Update, context):
    data = execute_ssh_command('mpstat')
    update.message.reply_text(data)

def get_w(update: Update, context):
    data = execute_ssh_command('w')
    update.message.reply_text(data)

def get_auths(update: Update, context):
    data = execute_ssh_command('last -n 10')
    update.message.reply_text(data)

def get_critical(update: Update, context):
    data = execute_ssh_command("journalctl -p crit --since yesterday | tail -n 5")
    update.message.reply_text(data)

def get_ps(update: Update, context):
    data = execute_ssh_command('ps aux --sort=-%cpu')
    update.message.reply_text(data)

def get_ss(update: Update, context):
    data = execute_ssh_command('ss -tuln')
    update.message.reply_text(data)


def get_apt_listCommand(update: Update, context):
    update.message.reply_text('Введите all, если хотите вывести список всех установленных пакетов (выведет первые 100). \n\nВведите название пакета, для которого требуется вывести информацию')

    return 'get_apt_list'

def get_apt_list(update: Update, context):

    user_input = update.message.text  # Получаем текст, содержащий номера телефонов
    print(user_input)


    if user_input.lower() == "all":
        # Выводим весь список установленных пакетов
        command = "dpkg -l | grep '^ii' | awk '{print $2}' | head -n 100"
        data = execute_ssh_command(command)
    else:
        # Ищем конкретный пакет
        command = f"apt show {user_input.lower()}"
        data = execute_ssh_command(command)

        # Проверяем, найден ли пакет
        if not data.strip():
            data = f"Пакет с именем '{user_input.lower()}' не найден."

    # Отправляем ответ пользователю
    update.message.reply_text(data)
    return ConversationHandler.END  # Завершаем работу обработчика диалога


def start(update: Update, context):
    start_msg = '''
Я - бот, вот список команд, которые я могу выполнить:

1. Поиск информации в тексте.
    Поиск email-адресов:
    - Команда: /find_email
    Поиск номеров телефонов:
    - Команда: /find_phone_number

2. Проверка сложности пароля. Определите надежность вашего пароля с помощью регулярных выражений.
    Проверка сложности пароля:
    - Команда: /verify_password
    - Требования: не менее 8 символов, с верхним и нижним регистром, цифрами и специальными символами.

3. Мониторинг Linux-системы. Получайте метрики с удаленного сервера, используя SSH-подключение.
    Информация о системе:
    - О релизе: /get_release
    - Об архитектуре процессора, имени хоста и версии ядра: /get_uname
    - О времени работы: /get_uptime

    Состояние системы:
    - Файловая система: /get_df
    - Оперативная память: /get_free
    - Производительность: /get_mpstat
    - Активные пользователи: /get_w

    Логи системы:
    - Последние 10 входов в систему: /get_auths
    - Последние 5 критических событий: /get_critical

    Информация о процессах и сетевых портах:
    - Запущенные процессы: /get_ps
    - Используемые порты: /get_ss

    Установленные пакеты и сервисы:
    - Все установленные пакеты: /get_apt_list
    - Запущенные сервисы: /get_services

4. Правила бойцовского клуба.
    - Список правил: /club_rules
'''
    user = update.effective_user
    update.message.reply_text(f'Привет {user.full_name}! '+ start_msg)


def helpCommand(update: Update, context):
    update.message.reply_text('Help!')

def set_database_data(command: str):
    logging.basicConfig(filename='logfile.txt', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO, encoding="utf-8")
    connection = None
    try:
        find_dotenv()
        load_dotenv()
        connection = psycopg2.connect(user=os.getenv('DB_USER'), password=os.getenv('DB_PASSWORD'), host=os.getenv('DB_HOST'), port=os.getenv('DB_PORT'), database=os.getenv('DB_DATABASE'))
        cursor = connection.cursor()
        cursor.execute(command)
        connection.commit()
        logging.info("Команда успешно выполнена")
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()


def get_database_data(command: str):
    logging.basicConfig(
    filename='logfile.txt', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO, encoding="utf-8"
)
    connection = None
    try:
        find_dotenv()
        load_dotenv()
        connection = psycopg2.connect(user=os.getenv('DB_USER'), password=os.getenv('DB_PASSWORD'), host=os.getenv('DB_HOST'), port=os.getenv('DB_PORT'), database=os.getenv('DB_DATABASE'))
        cursor = connection.cursor()
        cursor.execute(command)
        data = cursor.fetchall()
        result_string = ""

        for row in data:
            if result_string:  # Проверяем, не пуста ли строка, чтобы не добавить лишний перенос в начало
                result_string += "\n"
            result_string += f"{row[0]}. {row[1]}"

        logging.info("Команда успешно выполнена")
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
    return result_string


def get_emails(update: Update, context):
    data = get_database_data('SELECT * FROM email_addresses;')
    update.message.reply_text(data)

def get_phone_numbers(update: Update, context):
    data = get_database_data('SELECT * FROM phone_numbers;')
    update.message.reply_text(data)

def club_rules(update: Update, context):
    image_path = '.\\Fight_club.jpg'

    msg_rules='''
Первое правило бойцовского клуба: не упоминать о бойцовском клубе.
Второе правило бойцовского клуба: не упоминать нигде о бойцовском клубе.
Третье правило бойцовского клуба: боец крикнул: "стоп", выдохся, отключился - бой окончен.
Четвертое правило бойцовского клуба: в бою участвуют лишь двое.
Пятое правило бойцовского клуба: бои идут один за другим.
Шестое правило бойцовского клуба: снимать обувь и рубашку.
Седьмое правило бойцовского клуба : бой продолжается столько, сколько нужно.
Восьмое и последнее правило бойцовского клуба : тот, кто впервые пришел в клуб, примет бой.'''

    with open(image_path, 'rb') as photo:
        update.message.reply_photo(photo=photo, caption=msg_rules)


def find_phone_numberCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска телефонных номеров: ')

    return 'find_phone_number'


def find_phone_number(update: Update, context):
    user_input = update.message.text  # Получаем текст, содержащий номера телефонов
    phone_num_regex = re.compile(r'(\+7|8)[\-\s]?(\(?\d{3}\)?)[\-\s]?\d{3}[\-\s]?\d{2}[\-\s]?\d{2}')

    # Используем finditer для поиска всех номеров в тексте
    matches = phone_num_regex.finditer(user_input)
    phone_numbers = ''
    for i, match in enumerate(matches, start=1):
        phone_numbers += f'{i}. {match.group()}\n'  # Сохраняем полный текст совпадения

    # Проверяем, есть ли совпадения в тексте
    if not phone_numbers:
        update.message.reply_text('Телефонные номера не найдены')
        return ConversationHandler.END  # Завершаем работу обработчика диалога

    else:
        context.user_data['phone_numbers'] = phone_numbers  # Сохраняем номера в контекст
        # Создаем кнопку
        keyboard = [[InlineKeyboardButton("Добавить номер(а) в базу данных", callback_data='add_phone')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(phone_numbers, reply_markup=reply_markup)

    return ConversationHandler.END  # Завершаем работу обработчика диалога



def find_emailCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска email адресов: ')

    return 'find_email'

def is_valid_email(email): #функция для проверки на тире в самом начале и конце адреса или доменах
    address = email.split('@')[0]
    if address.startswith('-') or address.endswith('-') or address.startswith('_'): #еще дополнительно не в доменной части проверяем чтоб не начинался адрес на _
            return False

    domain = email.split('@')[1]
    for subdomain in domain.split('.'):
        if subdomain.startswith('-') or subdomain.endswith('-'):
            return False

    return True

def find_email (update: Update, context):
    user_input = update.message.text # Получаем текст, содержащий(или нет) номера телефонов
    email_regex = re.compile(r'[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')

    emailList = email_regex.findall(user_input) # Ищем email адреса

    if not emailList: # Обрабатываем случай, когда адресов нет
        update.message.reply_text('Email адреса не найдены')
        return ConversationHandler.END
    else:
        emailAddresses = ''
        for i in range(len(emailList)):
            if is_valid_email(emailList[i]):
                emailAddresses += f'{i+1}. {emailList[i]}\n'

        context.user_data['emails'] = emailAddresses  # Сохраняем адреса в контекст
        # Создаем кнопку
        keyboard = [[InlineKeyboardButton("Добавить email адрес(а) в базу данных", callback_data='add_email')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(emailAddresses.lower(), reply_markup=reply_markup)

    return ConversationHandler.END # Завершаем работу обработчика диалога



def find_phone_number(update: Update, context):
    user_input = update.message.text  # Получаем текст, содержащий номера телефонов
    phone_num_regex = re.compile(r'(\+7|8)[\-\s]?(\(?\d{3}\)?)[\-\s]?\d{3}[\-\s]?\d{2}[\-\s]?\d{2}')

    # Используем finditer для поиска всех номеров в тексте
    matches = phone_num_regex.finditer(user_input)
    phone_numbers = ''
    for i, match in enumerate(matches, start=1):
        phone_numbers += f'{i}. {match.group()}\n'  # Сохраняем полный текст совпадения

    # Проверяем, есть ли совпадения в тексте
    if not phone_numbers:
        update.message.reply_text('Телефонные номера не найдены')
        return ConversationHandler.END  # Завершаем работу обработчика диалога

    else:
        context.user_data['phone_numbers'] = phone_numbers  # Сохраняем номера в контекст
        # Создаем кнопку
        keyboard = [[InlineKeyboardButton("Добавить номер(а) в базу данных", callback_data='add_phone')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(phone_numbers, reply_markup=reply_markup)

    return ConversationHandler.END  # Завершаем работу обработчика диалога


def button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    if query.data == 'add_phone':
        phone_numbers = context.user_data.get('phone_numbers')
        print(phone_numbers)
        phone_list = phone_numbers.strip().split('\n')
        phone_list = [phone.strip().split('. ')[1] for phone in phone_list]
        for phone_number in phone_list:
            sql = f"INSERT INTO phone_numbers (phone_number) VALUES ('{phone_number}');"
            set_database_data(sql)
        query.edit_message_text(text="Номер(а) добавлены в базу данных!")

    if query.data == 'add_email':
        email_addresses = context.user_data.get('emails')
        print(email_addresses)
        email_list = email_addresses.strip().split('\n')
        email_list = [email.strip().split('. ')[1] for email in email_list]
        for email_address in email_list:
            sql = f"INSERT INTO email_addresses (email) VALUES ('{email_address}');"
            set_database_data(sql)
        query.edit_message_text(text="Email адрес(а) добавлена в базу данных!")



def verify_passwordCommand(update: Update, context):
    update.message.reply_text('Введите Ваш пароль для оценки его сложности')

    return 'verify_password'

def verify_password (update: Update, context):
    user_input = update.message.text # Получаем текст

    password_regex = re.compile(r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*()])[A-Za-z\d!@#$%^&*()]{8,}$')

    passwordList = password_regex.findall(user_input) # проверяем соотвестувет ли пароль заданным требованям
    if passwordList: # проверяем соотвестувет ли пароль заданным требованям
        update.message.reply_text('Пароль сложный!')
        return ConversationHandler.END # Завершаем работу обработчика диалога
    else:
        msg = '''Пароль простой! Придумай что-нибудь посложнее.\n\nСложный пароль должен соответствовать данным требованиям:\n
- Пароль должен содержать не менее восьми символов.
- Пароль должен включать как минимум одну заглавную букву (A–Z).
- Пароль должен включать хотя бы одну строчную букву (a–z).
- Пароль должен включать хотя бы одну цифру (0–9).
- Пароль должен включать хотя бы один специальный символ, такой как !@#$%^&*().
        '''
        update.message.reply_text(msg)
        return ConversationHandler.END # Завершаем работу обработчика диалога


def echo(update: Update, context):
    update.message.reply_text(update.message.text)


def main():
    updater = Updater(TOKEN, use_context=True)

    # Получаем диспетчер для регистрации обработчиков
    dp = updater.dispatcher

    # Обработчик диалога
    convHandlerFindPhoneNumbers = ConversationHandler(
        entry_points=[CommandHandler('find_phone_number', find_phone_numberCommand)],
        states={
            'find_phone_number': [MessageHandler(Filters.text & ~Filters.command, find_phone_number)],
        },
        fallbacks=[]
    )

    convHandlerFindEmail = ConversationHandler(
        entry_points=[CommandHandler('find_email', find_emailCommand)],
        states={
            'find_email': [MessageHandler(Filters.text & ~Filters.command, find_email)],
        },
        fallbacks=[]
    )

    convHandlerVerifyPassword = ConversationHandler(
        entry_points=[CommandHandler('verify_password', verify_passwordCommand)],
        states={
            'verify_password': [MessageHandler(Filters.text & ~Filters.command, verify_password)],
        },
        fallbacks=[]
    )


    convHandlerget_apt_list = ConversationHandler(
        entry_points=[CommandHandler('get_apt_list', get_apt_listCommand)],
        states={
            'get_apt_list': [MessageHandler(Filters.text & ~Filters.command, get_apt_list)],
        },
        fallbacks=[]
    )

        # Регистрируем обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", helpCommand))

    dp.add_handler(CommandHandler("get_release", get_release))
    dp.add_handler(CommandHandler("get_uname", get_uname))
    dp.add_handler(CommandHandler("get_uptime", get_uptime))
    dp.add_handler(CommandHandler("get_df", get_df))
    dp.add_handler(CommandHandler("get_free", get_free))
    dp.add_handler(CommandHandler("get_mpstat", get_mpstat))
    dp.add_handler(CommandHandler("get_w", get_w))
    dp.add_handler(CommandHandler("get_auths", get_auths))
    dp.add_handler(CommandHandler("get_critical", get_critical))
    dp.add_handler(CommandHandler("get_ps", get_ps))
    dp.add_handler(CommandHandler("get_ss", get_ss))
    dp.add_handler(CommandHandler("club_rules", club_rules))
    dp.add_handler(CommandHandler("get_repl_logs", get_repl_logs))
    dp.add_handler(CommandHandler("get_emails", get_emails))
    dp.add_handler(CommandHandler("get_phone_numbers", get_phone_numbers))
    dp.add_handler(CallbackQueryHandler(button_callback))

    dp.add_handler(convHandlerFindPhoneNumbers)
    dp.add_handler(convHandlerFindEmail)
    dp.add_handler(convHandlerVerifyPassword)
    dp.add_handler(convHandlerget_apt_list)

        # Регистрируем обработчик текстовых сообщений
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

        # Запускаем бота
    updater.start_polling()

        # Останавливаем бота при нажатии Ctrl+C
    updater.idle()


if __name__ == '__main__':
    main()
