#!/usr/bin/python

import telebot
from telebot import types
import psycopg2
import uuid

API_TOKEN = '745109143:AAEd3p0TEjVV2VfOSzyiPl3T7orUsEFDMr4'

is_testing = False
is_inserting_data = False

user_test_code = ''
user_right_answers = 0

db_elements = []

user_answers = []
right_answers = []
results = []
question_markups = []

markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
item1 = types.KeyboardButton('Choose a test')
item2 = types.KeyboardButton('Contact')
markup.row(item1)
markup.row(item2)

bot = telebot.TeleBot(API_TOKEN)


def clear_test_data():
    global user_answers
    global right_answers
    global results
    global question_markups
    user_answers = []
    right_answers = []
    results = []
    question_markups = []


def find_id(question):
    for element in db_elements:
        if element[1] == question:
            return db_elements.index(element)


def create_question_markups():
    global question_markups
    for i in range(len(db_elements)):
        curr_element = db_elements[i]
        answers = curr_element[2].split(', ')
        question_markup = types.InlineKeyboardMarkup()
        for x in range(len(answers)):
            answer = types.InlineKeyboardButton(text='{}'.format(answers[x]), callback_data='{}'.format(x))
            question_markup.add(answer)
        if len(db_elements) != 1:
            if i == 0:
                next_bnt = types.InlineKeyboardButton(text='>', callback_data='next')
                question_markup.add(next_bnt)
            elif i == len(db_elements) - 1:
                prev_button = types.InlineKeyboardButton(text='<', callback_data='prev')
                question_markup.add(prev_button)
            else:
                prev_button = types.InlineKeyboardButton(text='<', callback_data='prev')
                next_bnt = types.InlineKeyboardButton(text='>', callback_data='next')
                question_markup.add(prev_button, next_bnt)
        end_btn = types.InlineKeyboardButton(text='End test', callback_data='end_test')
        question_markup.add(end_btn)
        question_markups.append(question_markup)


def get_question_markup(question_number):
    global question_markups
    return question_markups[question_number]


def check_answers():
    for i in range(len(user_answers)):
        if user_answers[i] == right_answers[i]:
            results.pop(i)
            results.insert(i, 'Right')

# Handle '/start'.
@bot.message_handler(commands=['start'])
def send_welcome(message):
    congrat_message = 'Hello {}!\nChoose what you want to do in a menu.'.format(message.from_user.first_name)
    bot.send_message(message.chat.id, congrat_message, reply_markup=markup)


@bot.message_handler(commands=['break'])
def stop_inserting(message):
    global is_testing
    is_testing = False
    global is_inserting_data
    is_inserting_data = False
    bot.send_message(message.chat.id, 'Action cancelled.\nYou can also open quick menu any time you want.')

# Handle all other messages with content_type 'text' (content_types defaults to ['text'])
@bot.message_handler(func=lambda message: True)
def echo_message(message):
    global is_testing
    global user_test_code
    global is_inserting_data
    if not is_testing:
        if message.text == 'Choose a test':
            bot.send_message(message.chat.id, 'Enter please name of the test')
            is_testing = True
        elif message.text == 'Contact':
            bot.send_message(message.chat.id, 'Made by @m_t0xic (Rebels Corp.)')
        else:
            if is_inserting_data:
                checker = message.text.split(' ')
                if len(checker) != 1:
                    con = None
                    try:
                        con = psycopg2.connect(database="d99gqkbd6vao8t",
                                               user="tjdzfptfviuxhq",
                                               password="013755cf03bd0a8c0d4b0d446921e61702718a849c0eacd2baf477271e601c5d",
                                               host="ec2-46-137-113-157.eu-west-1.compute.amazonaws.com",
                                               port="5432")
                        cursor = con.cursor()
                        cursor.execute("INSERT INTO user_test_results (id, contact_data, test_code, results) VALUES ('{}', '{}', '{}', '{}/{}')".format(str(uuid.uuid4()), message.text, user_test_code, user_right_answers, len(right_answers)))
                        con.commit()
                        cursor.close()
                        is_inserting_data = False
                        bot.send_message(message.chat.id, 'Thank you. We will contact you as soon as possible.')
                    except (Exception, psycopg2.DatabaseError) as error:
                        print(error)
                    finally:
                        if con is not None:
                            con.close()
                else:
                    bot.send_message(message.chat.id, 'Please, check if you put in data correct and resend it again.')
            else:
                bot.send_message(message.chat.id, 'Something went wrong.\nChoose what to do from a menu below', reply_markup=markup)
    else:
        clear_test_data()
        con = None
        try:
            con = psycopg2.connect(database="d99gqkbd6vao8t",
                                   user="tjdzfptfviuxhq",
                                   password="013755cf03bd0a8c0d4b0d446921e61702718a849c0eacd2baf477271e601c5d",
                                   host="ec2-46-137-113-157.eu-west-1.compute.amazonaws.com",
                                   port="5432")
            cursor = con.cursor()
            cursor.execute("SELECT * FROM tests WHERE test_code='{}' AND status='active'".format(message.text))
            rows = cursor.fetchall()
            if len(rows) == 0:
                bot.send_message(message.chat.id, 'Sorry, there are no such tests.\nPlease check test name again.')
            else:
                user_test_code = message.text
                global db_elements
                db_elements = rows
            cursor.close()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if con is not None:
                con.close()
        if len(db_elements) != 0:
            for element in db_elements:
                user_answers.append('No answer')
                results.append('Wrong')
                right_answers.append(element[3])
            curr_element = db_elements[0]
            question = curr_element[1]
            create_question_markups()
            bot.send_message(message.chat.id, question, reply_markup=get_question_markup(0))
        # Maybe in the future
        # bot.send_message(message.chat.id, 'Searching your test...')
        # bot.edit_message_text(question, message.chat.id, message.message_id, reply_markup=get_question_markup(0))


@bot.callback_query_handler(func=lambda call: call.data)
def callback_handler(call):
    if call.data == 'next':
        current_id = find_id(call.message.text)
        curr_element = db_elements[current_id + 1]
        question = curr_element[1]
        bot.edit_message_text(question, call.message.chat.id, call.message.message_id, reply_markup=get_question_markup(current_id + 1))
    if call.data == 'prev':
        current_id = find_id(call.message.text)
        curr_element = db_elements[current_id - 1]
        question = curr_element[1]
        bot.edit_message_text(question, call.message.chat.id, call.message.message_id, reply_markup=get_question_markup(current_id - 1))
    if call.data == 'end_test':
        global is_testing
        global is_inserting_data
        is_testing = False
        result_string = ''
        num_right_answers = 0
        check_answers()
        for i in range(len(results)):
            result_string += 'Question {}:\nYour answer: {} | Right answer: {}\n\n'.format(i + 1, user_answers[i], right_answers[i])
        for i in results:
            if i == 'Right':
                num_right_answers += 1
        global user_right_answers
        user_right_answers = num_right_answers
        result_string += 'Your result: {}/{}'.format(num_right_answers, len(right_answers))
        bot.edit_message_text(result_string, call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, 'Our greetings!\nPlease, leave info about you using this sample:\n\'Name phone number/email\'\nYou can also type \'/break\' if you don\'t want to leave your info for us.')
        is_inserting_data = True
    try:
        if isinstance(int(call.data), int):
            current_id = find_id(call.message.text)
            user_answers.pop(current_id)
            user_answers.insert(current_id, call.message.json['reply_markup']['inline_keyboard'][int(call.data)][0]['text'])
            curr_element = db_elements[current_id]
            question = curr_element[1]
            answers = curr_element[2].split(', ')
            new_question_markup = types.InlineKeyboardMarkup()
            for x in range(len(answers)):
                if x == int(call.data):
                    answer = types.InlineKeyboardButton(text='{' + answers[x] + '}', callback_data='{}'.format(x))
                    new_question_markup.add(answer)
                else:
                    answer = types.InlineKeyboardButton(text='{}'.format(answers[x]), callback_data='{}'.format(x))
                    new_question_markup.add(answer)
            if len(db_elements) != 1:
                if current_id == 0:
                    next_bnt = types.InlineKeyboardButton(text='>', callback_data='next')
                    new_question_markup.add(next_bnt)
                elif current_id == len(db_elements) - 1:
                    prev_button = types.InlineKeyboardButton(text='<', callback_data='prev')
                    new_question_markup.add(prev_button)
                else:
                    prev_button = types.InlineKeyboardButton(text='<', callback_data='prev')
                    next_bnt = types.InlineKeyboardButton(text='>', callback_data='next')
                    new_question_markup.add(prev_button, next_bnt)
            end_btn = types.InlineKeyboardButton(text='End test', callback_data='end_test')
            new_question_markup.add(end_btn)
            question_markups.pop(current_id)
            question_markups.insert(current_id, new_question_markup)
            bot.edit_message_text(question, call.message.chat.id, call.message.message_id, reply_markup=get_question_markup(current_id))
    except ValueError:
        pass


bot.polling()
