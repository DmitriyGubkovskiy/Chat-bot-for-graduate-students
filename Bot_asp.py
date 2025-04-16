import json
import os
import random

import pandas as pd
import redis
import requests
import telebot

token = "**"

greeting = "Вам необходимо пройти регистрацию. Следуйте указаниям."
bot = telebot.TeleBot(token)

# Courses = json.load(open('/data/Courses.json', 'r', encoding='utf-8'))
Courses = json.load(open("Courses.json", "r", encoding="utf-8"))


for_teacher = [
    "Всем",
    "Некоторым курсам",
    "Некоторым группам",
    "Изменить связь между группами и курсами",
]
first_course = []


markup_course = telebot.types.ReplyKeyboardMarkup(
    resize_keyboard=True, one_time_keyboard=True
)
markup_course.add(*[telebot.types.KeyboardButton(button) for button in Courses.keys()])

markup_message = telebot.types.ReplyKeyboardMarkup(
    resize_keyboard=True, one_time_keyboard=True
)
markup_message.add(*[telebot.types.KeyboardButton(button) for button in for_teacher])

group_to_send = ""
course_to_send = ""

MAIN_STATE = "main"
GREETING_STATE = "greeting"
REGISTER_COURSE_STATE = "register_course"
REGISTER_GROUP_STATE = "register_group"
TEACHER_MAIN = "teacher_main"
SEND_TO_ALL = "send_to_all"
SEND_TO_COURSE = "send_to_course"
SEND_TO_GROUPS = "send_to_groups"
CHOOSE_GROUP = "choose_group"
CHOOSE_COURSE = "choose_course"
CHANGE_COURSE = "change_course"
CONFIRM_COURSE = "confirm_course"


# df_persons = pd.read_excel('/data/Data.xlsx')
df_persons = pd.read_excel("Data.xlsx")


redis_url = os.environ.get("REDIS_URL")

if redis_url is None:
    try:
        # data = json.load(open('data/data.json', 'r', encoding='utf-8'))
        data = json.load(open("data.json", "r", encoding="utf-8"))
    except FileNotFoundError:
        data = {
            "states": {},
            MAIN_STATE: {},
            GREETING_STATE: {},
            REGISTER_COURSE_STATE: {},
            REGISTER_GROUP_STATE: {},
            TEACHER_MAIN: {},
            SEND_TO_ALL: {},
            SEND_TO_COURSE: {},
            SEND_TO_GROUPS: {},
            CHOOSE_GROUP: {},
            CHOOSE_COURSE: {},
            CHANGE_COURSE: {},
            CONFIRM_COURSE: {},
        }
else:
    redis_db = redis.from_url(redis_url)
    raw_data = redis_db.get("data")
    if raw_data is None:
        data = {
            "states": {},
            MAIN_STATE: {},
            GREETING_STATE: {},
            REGISTER_COURSE_STATE: {},
            REGISTER_GROUP_STATE: {},
            TEACHER_MAIN: {},
            SEND_TO_ALL: {},
            SEND_TO_COURSE: {},
            SEND_TO_GROUPS: {},
            CHOOSE_GROUP: {},
            CHOOSE_COURSE: {},
            CHANGE_COURSE: {},
            CONFIRM_COURSE: {},
        }
    else:
        data = json.loads(raw_data)


def dowload_data():
    global df_persons
    # df_persons = pd.read_excel('/data/Data.xlsx')
    df_persons = pd.read_excel("Data.xlsx")


def update_data():
    global df_persons
    # df_persons.to_excel("/data/Data.xlsx", index=False)
    df_persons.to_excel("Data.xlsx", index=False)


def update_courses(first_course):
    global df_persons
    global Courses
    Courses["4 Курс"] = Courses["3 Курс"]
    Courses["3 Курс"] = Courses["2 Курс"]
    Courses["2 Курс"] = Courses["1 Курс"]
    Courses["1 Курс"] = first_course

    df_persons = df_persons.loc[df_persons["Course"] != "4 Курс"]

    df_persons.loc[df_persons["Course"] == "3 Курс", "Course"] = "4 Курс"
    df_persons.loc[df_persons["Course"] == "2 Курс", "Course"] = "3 Курс"
    df_persons.loc[df_persons["Course"] == "1 Курс", "Course"] = "2 Курс"

    with open("Courses.json", "w", encoding="utf8") as file:
        file.write(json.dumps(Courses, ensure_ascii=False))
    update_data()


def change_date(key, user_id, value):
    data[key][user_id] = value
    if redis_url is None:
        json.dump(
            data,
            # open('/data/data.json', 'w', encoding='utf-8'),
            open("data.json", "w", encoding="utf-8"),
            indent=2,
            ensure_ascii=False,
        )
    else:
        redis_db = redis.from_url(redis_url)
        redis_db.set("data", json.dumps(data))


@bot.message_handler(
    func=lambda message: True,
    content_types=["document", "text", "photo", "audio", "video"],
)
def dispatcher(message):
    user_id = str(message.from_user.id)
    current_user_state = data["states"].get(user_id, "greeting")
    print(user_id)
    # print(" https://t.me/" + message.from_user.username)
    print(current_user_state)

    if current_user_state == MAIN_STATE:
        main_handler(message)
    elif current_user_state == GREETING_STATE:
        greeting_handler(message)
    elif current_user_state == REGISTER_COURSE_STATE:
        register_course_handler(message)
    elif current_user_state == REGISTER_GROUP_STATE:
        register_group_handler(message)
    elif current_user_state == TEACHER_MAIN:
        teacher_main(message)
    elif current_user_state == SEND_TO_ALL:
        send_to_all(message)
    elif current_user_state == SEND_TO_COURSE:
        send_to_course(message)
    elif current_user_state == SEND_TO_GROUPS:
        send_to_groups(message)
    elif current_user_state == CHOOSE_GROUP:
        choose_group(message)
    elif current_user_state == CHOOSE_COURSE:
        choose_course(message)
    elif current_user_state == CHANGE_COURSE:
        change_courses(message)
    elif current_user_state == CONFIRM_COURSE:
        confirm_courses(message)


def greeting_handler(message):
    user_id = str(message.from_user.id)
    if message.text == "/start":
        bot.send_message(message.from_user.id, greeting)
        change_date("states", user_id, REGISTER_COURSE_STATE)
        bot.send_message(
            message.from_user.id,
            "Пожалуйста, выберите курс или введите код доступа (для преподавателей).",
            reply_markup=markup_course,
        )


def main_handler(message):
    global df_persons
    user_id = str(message.from_user.id)
    if message.text == "Ваши данные.":
        dowload_data()
        for id in df_persons["ID"]:
            if str(id) == user_id:
                try:
                    bot.send_message(
                        message.from_user.id,
                        "Ваши данные: {} группа {}.".format(
                            df_persons[df_persons["ID"] == id]["Course"].to_list()[0],
                            df_persons[df_persons["ID"] == id]["Group"].to_list()[0],
                        ),
                    )
                    break
                except:
                    bot.send_message(message.from_user.id, "Данные не найдены.")
                    break
            else:
                bot.send_message(message.from_user.id, "Данные не найдены.")
                break
    elif message.text == "Сменить группу или курс.":
        for id in df_persons["ID"]:
            if str(id) == user_id:
                df_persons = df_persons.drop(df_persons[df_persons["ID"] == id].index)
                break
        update_data()
        change_date("states", user_id, REGISTER_COURSE_STATE)
        bot.send_message(
            message.from_user.id,
            "Пожалуйста, выберите курс или введите код доступа (для преподавателей).",
            reply_markup=markup_course,
        )
    else:
        bot.send_message(message.from_user.id, "Неизвестная команда.")


def register_course_handler(message):
    user_id = str(message.from_user.id)

    if message.text in Courses.keys():
        global temporary_course
        temporary_course = message.text
        markup_groups = telebot.types.ReplyKeyboardMarkup(
            resize_keyboard=True, one_time_keyboard=True
        )
        markup_groups.add(
            *[telebot.types.KeyboardButton(button) for button in Courses[message.text]]
        )
        bot.send_message(
            message.from_user.id,
            "Пожалуйста, выберите группу.",
            reply_markup=markup_groups,
        )
        change_date("states", user_id, REGISTER_GROUP_STATE)
    elif message.text == "Политех лучше всех":
        bot.send_message(
            message.from_user.id,
            "Вы зарегистрировались как преподаватель.",
            reply_markup=telebot.types.ReplyKeyboardRemove(),
        )
        bot.send_message(
            message.from_user.id,
            "Выберите вариант отправки сообщения или "
            "функцию изменения связи между группами и курсами",
            reply_markup=markup_message,
        )
        change_date("states", user_id, TEACHER_MAIN)
    else:
        bot.send_message(message.from_user.id, "Возникла ошибка.")
        bot.send_message(message.from_user.id, "Пожалуйства, выберите курс.")


def register_group_handler(message):
    user_id = str(message.from_user.id)
    global temporary_course
    if message.text in Courses[temporary_course]:
        bot.send_message(
            message.from_user.id,
            'Вы выбрали "{}" и группу "{}".'.format(temporary_course, message.text),
            reply_markup=telebot.types.ReplyKeyboardRemove(),
        )

        df_persons.loc[len(df_persons.index)] = [
            user_id,
            temporary_course,
            message.text,
        ]
        update_data()
        change_date("states", user_id, MAIN_STATE)

        markup_main = telebot.types.ReplyKeyboardMarkup(
            resize_keyboard=True, one_time_keyboard=True
        )
        markup_main.add(
            *[
                telebot.types.KeyboardButton(button)
                for button in ["Ваши данные.", "Сменить группу или курс."]
            ]
        )
        bot.send_message(
            message.from_user.id,
            "Вы успешно зарегистрировались и можете получать сообщения.",
            reply_markup=markup_main,
        )

    else:
        bot.send_message(message.from_user.id, "Возникла ошибка.")
        bot.send_message(
            message.from_user.id,
            "Пожалуйства, выберите курс.",
            reply_markup=markup_course,
        )
        change_date("states", user_id, REGISTER_COURSE_STATE)
        temporary_course = ""


def teacher_main(message):
    user_id = str(message.from_user.id)

    if message.text == for_teacher[0]:
        bot.send_message(
            message.from_user.id,
            "Напишите сообщение.",
            reply_markup=telebot.types.ReplyKeyboardRemove(),
        )
        change_date("states", user_id, SEND_TO_ALL)
    elif message.text == for_teacher[1]:
        bot.send_message(
            message.from_user.id, "Выберите курс.", reply_markup=markup_course
        )
        change_date("states", user_id, CHOOSE_COURSE)
    elif message.text == for_teacher[2]:
        groups = []
        for key in Courses.keys():
            groups += [i for i in Courses[key]]
        markup_groups = telebot.types.ReplyKeyboardMarkup(
            resize_keyboard=True, one_time_keyboard=True
        )
        markup_groups.add(*[telebot.types.KeyboardButton(button) for button in groups])

        bot.send_message(
            message.from_user.id, "Выберите группу.", reply_markup=markup_groups
        )
        change_date("states", user_id, CHOOSE_GROUP)
    elif message.text == for_teacher[3]:
        bot.send_message(
            message.from_user.id,
            "Введите номера групп первого курса через пробел.",
            reply_markup=telebot.types.ReplyKeyboardRemove(),
        )
        change_date("states", user_id, CHANGE_COURSE)

    else:
        bot.send_message(message.from_user.id, "Возникла ошибка.")
        bot.send_message(
            message.from_user.id,
            "Выберите вариант отправки сообщения или "
            "функцию изменения связи между группами и курсами",
            reply_markup=markup_message,
        )


def send_to_all(message):
    user_id = str(message.from_user.id)

    # for id in df_persons["ID"]:
    #     bot.forward_message(
    #         chat_id=user_id,  # chat_id чата в которое необходимо переслать сообщение
    #         from_chat_id=id,  # chat_id из которого необходимо переслать сообщение
    #         message_id=message.message_id  # message_id которое необходимо переслать
    #     )

    if message.content_type == "document":
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open(message.document.file_name, "wb") as new_file:
            new_file.write(downloaded_file)
        for id in df_persons["ID"]:
            file = open(message.document.file_name, "rb")
            bot.send_document(str(id), file)
            file.close()
        os.remove(message.document.file_name)

    elif message.content_type == "photo":
        photo = bot.download_file(bot.get_file(message.photo[-1].file_id).file_path)
        for id in df_persons["ID"]:
            bot.send_photo(str(id), photo)

    elif message.content_type == "video":
        video = bot.download_file(bot.get_file(message.video.file_id).file_path)
        for id in df_persons["ID"]:
            bot.send_video(str(id), video)

    elif message.content_type == "audio":
        audio = bot.download_file(bot.get_file(message.audio.file_id).file_path)
        for id in df_persons["ID"]:
            bot.send_audio(str(id), audio)

    elif message.content_type == "text":
        for id in df_persons["ID"]:
            bot.send_message(str(id), message.text)

    else:
        bot.send_message(
            message.from_user.id,
            "Данный формат сообщения не поддерживыется для отправки.",
        )
        return

    bot.send_message(message.from_user.id, "Сообщение отправлено всем.")
    change_date("states", user_id, TEACHER_MAIN)

    bot.send_message(
        message.from_user.id,
        "Выберите вариант отправки сообщения или "
        "функцию изменения связи между группами и курсами",
        reply_markup=markup_message,
    )


def send_to_course(message):
    global course_to_send
    user_id = str(message.from_user.id)

    # for id in df_persons[df_persons["Course"] == course_to_send]["ID"]:
    #     bot.forward_message(
    #         chat_id=user_id,  # chat_id чата в которое необходимо переслать сообщение
    #         from_chat_id=id,  # chat_id из которого необходимо переслать сообщение
    #         message_id=message.message_id  # message_id которое необходимо переслать
    #     )

    if message.content_type == "document":
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open(message.document.file_name, "wb") as new_file:
            new_file.write(downloaded_file)

        for id in df_persons[df_persons["Course"] == course_to_send]["ID"]:
            file = open(message.document.file_name, "rb")
            bot.send_document(str(id), file)
            file.close()
        os.remove(message.document.file_name)

    elif message.content_type == "photo":
        photo = bot.download_file(bot.get_file(message.photo[-1].file_id).file_path)
        for id in df_persons[df_persons["Course"] == course_to_send]["ID"]:
            bot.send_photo(str(id), photo)

    elif message.content_type == "video":
        video = bot.download_file(bot.get_file(message.video.file_id).file_path)
        for id in df_persons[df_persons["Course"] == course_to_send]["ID"]:
            bot.send_video(str(id), video)

    elif message.content_type == "audio":
        audio = bot.download_file(bot.get_file(message.audio.file_id).file_path)
        for id in df_persons[df_persons["Course"] == course_to_send]["ID"]:
            bot.send_audio(str(id), audio)

    elif message.content_type == "text":
        for id in df_persons[df_persons["Course"] == course_to_send]["ID"]:
            bot.send_message(str(id), message.text)

    else:
        bot.send_message(
            message.from_user.id,
            "Данный формат сообщения не поддерживыется для отправки.",
        )
        return

    bot.send_message(
        message.from_user.id,
        'Сообщение отправлено выбранному курсу "{}".'.format(course_to_send),
    )
    change_date("states", user_id, TEACHER_MAIN)
    course_to_send = ""
    bot.send_message(
        message.from_user.id,
        "Выберите вариант отправки сообщения или "
        "функцию изменения связи между группами и курсами",
        reply_markup=markup_message,
    )


def send_to_groups(message):
    global group_to_send
    user_id = str(message.from_user.id)

    # for id in df_persons[df_persons["Group"] == group_to_send]["ID"]:
    #     bot.forward_message(
    #         chat_id=user_id,  # chat_id чата в которое необходимо переслать сообщение
    #         from_chat_id=id,  # chat_id из которого необходимо переслать сообщение
    #         message_id=message.message_id  # message_id которое необходимо переслать
    #     )

    if message.content_type == "document":
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open(message.document.file_name, "wb") as new_file:
            new_file.write(downloaded_file)
        for id in df_persons[df_persons["Group"] == group_to_send]["ID"]:
            file = open(message.document.file_name, "rb")
            bot.send_document(str(id), file)
            file.close()
        os.remove(message.document.file_name)

    elif message.content_type == "photo":
        photo = bot.download_file(bot.get_file(message.photo[-1].file_id).file_path)
        for id in df_persons[df_persons["Group"] == group_to_send]["ID"]:
            bot.send_photo(str(id), photo)

    elif message.content_type == "video":
        video = bot.download_file(bot.get_file(message.video.file_id).file_path)
        for id in df_persons[df_persons["Group"] == group_to_send]["ID"]:
            bot.send_video(str(id), video)

    elif message.content_type == "audio":
        audio = bot.download_file(bot.get_file(message.audio.file_id).file_path)
        for id in df_persons[df_persons["Group"] == group_to_send]["ID"]:
            bot.send_audio(str(id), audio)

    elif message.content_type == "text":
        for id in df_persons[df_persons["Group"] == group_to_send]["ID"]:
            bot.send_message(str(id), message.text)

    else:
        bot.send_message(
            message.from_user.id,
            "Данный формат сообщения не поддерживыется для отправки.",
        )
        return

    bot.send_message(
        message.from_user.id,
        'Сообщение отправлено выбранной группе "{}".'.format(group_to_send),
    )
    change_date("states", user_id, TEACHER_MAIN)
    group_to_send = ""
    bot.send_message(
        message.from_user.id,
        "Выберите вариант отправки сообщения или "
        "функцию изменения связи между группами и курсами",
        reply_markup=markup_message,
    )


def choose_group(message):
    global group_to_send
    user_id = str(message.from_user.id)
    groups = []
    for key in Courses.keys():
        groups += [i for i in Courses[key]]
    if message.text in groups:
        group_to_send = message.text
        bot.send_message(
            message.from_user.id,
            "Напишите сообщение.",
            reply_markup=telebot.types.ReplyKeyboardRemove(),
        )
        change_date("states", user_id, SEND_TO_GROUPS)
    else:
        bot.send_message(message.from_user.id, "Возникла ошибка.")
        bot.send_message(
            message.from_user.id,
            "Выберите вариант отправки сообщения или "
            "функцию изменения связи между группами и курсами",
            reply_markup=markup_message,
        )
        change_date("states", user_id, TEACHER_MAIN)


def choose_course(message):
    global course_to_send
    user_id = str(message.from_user.id)
    if message.text in Courses.keys():
        course_to_send = message.text
        bot.send_message(
            message.from_user.id,
            "Напишите сообщение.",
            reply_markup=telebot.types.ReplyKeyboardRemove(),
        )
        change_date("states", user_id, SEND_TO_COURSE)
    else:
        bot.send_message(message.from_user.id, "Возникла ошибка.")
        bot.send_message(
            message.from_user.id,
            "Выберите вариант отправки сообщения или "
            "функцию изменения связи между группами и курсами",
            reply_markup=markup_message,
        )
        change_date("states", user_id, TEACHER_MAIN)


def change_courses(message):
    user_id = str(message.from_user.id)
    global first_course
    first_course = message.text.split()
    Yes_or_not = telebot.types.ReplyKeyboardMarkup(
        resize_keyboard=True, one_time_keyboard=True
    )
    Yes_or_not.add(
        *[telebot.types.KeyboardButton(button) for button in ["Да", "Допущена ошибка"]]
    )
    bot.send_message(
        message.from_user.id,
        "Проверьте введенные значения. Можно ли их сохранить?",
        reply_markup=Yes_or_not,
    )
    change_date("states", user_id, CONFIRM_COURSE)


def confirm_courses(message):
    user_id = str(message.from_user.id)
    global first_course
    if message.text == "Да":
        update_courses(first_course)
        print(first_course)
        first_course.clear()
        bot.send_message(
            message.from_user.id,
            "Выберите вариант отправки сообщения или "
            "функцию изменения связи между группами и курсами",
            reply_markup=markup_message,
        )
        change_date("states", user_id, TEACHER_MAIN)
    elif message.text == "Допущена ошибка":
        first_course.clear()
        bot.send_message(
            message.from_user.id,
            "Введите номера групп первого курса через пробел.",
            reply_markup=telebot.types.ReplyKeyboardRemove(),
        )
        change_date("states", user_id, CHANGE_COURSE)
    else:
        bot.send_message(message.from_user.id, "Возникла ошибка.")
        Yes_or_not = telebot.types.ReplyKeyboardMarkup(
            resize_keyboard=True, one_time_keyboard=True
        )
        Yes_or_not.add(
            *[
                telebot.types.KeyboardButton(button)
                for button in ["Да", "Допущена ошибка"]
            ]
        )
        bot.send_message(
            message.from_user.id,
            "Проверьте введенные значения. Можно ли их сохранить?",
            reply_markup=Yes_or_not,
        )


if __name__ == "__main__":
    bot.polling()
    print("сохранение на диск")
