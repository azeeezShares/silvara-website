import os
import psycopg2
from django.conf import settings

from dotenv import load_dotenv
from telebot import custom_filters
from psycopg2.extensions import connection
import telebot
from telebot.storage import StateRedisStorage
from telebot.states.sync.context import StateContext
from .tools.db import ( 
    assign_student_and_subjects, 
    get_all_groups, create_subject, 
    get_all_subjects, get_all_users, 
    check_user_role, create_group, 
    get_assigments, 
    get_group_by_id, 
    get_subject_by_id,
    get_user_by_id,
)

from telebot.types import  (
    Message, 
    ReplyKeyboardMarkup, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton,
    CallbackQuery,
    KeyboardButton,
    ReplyParameters, 
    ReplyKeyboardRemove,
)
from tools.states import (
    UserStates,
    AdminStates,
    AdminNewGroupStates, 
    AdminNewSubjectStates,
    AdminAssignSubjectStates,
    StudentJoinGroupStates, 
)
# from telebot.states.sync.middleware import StateMiddleware

# load dotenv
load_dotenv(settings.BASE_DIR/'.env')



# Bot Token
TOKEN = os.getenv("BOT_TOKEN")
state_storage = StateRedisStorage(host='localhost', port=6379, db=0)
bot = telebot.TeleBot(TOKEN, state_storage=state_storage, use_class_middlewares=True, parse_mode="HTML")

# Database Connection
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}
def get_db_connection() -> connection:
    return psycopg2.connect(**DB_CONFIG)


# cancel query
@bot.callback_query_handler(func=lambda call: call.data == 'cancel')
def cancel_and_admin_view(call: CallbackQuery, state: StateContext):
    state.delete()
    state.set(UserStates.admin_menu)
    bot.delete_message(call.message.chat.id, call.message.id)
    send_admin_menu(call.message)

@bot.message_handler(text=["Akkauntdan chiqish", ])
def logout(message: Message, state: StateContext):
    state.delete()
    
    bot.send_message(message.chat.id, 'Akkauntdan chiqildi. Qayta kiring.')
    start(message, state)

# Start Command (Login)
@bot.message_handler(commands=["start"])
def start(message, state: StateContext):
    state.set(UserStates.login)
    bot.send_message(message.chat.id, "Iltimos username kiriting:", reply_markup=ReplyKeyboardRemove())

@bot.message_handler(state=UserStates.login)
def get_username(message, state: StateContext):
    state.add_data(username=message.text)
    state.set(UserStates.password)
    bot.send_message(message.chat.id, "Endi parol kiriting:")

@bot.message_handler(state=UserStates.password)
def check_login(message, state: StateContext):
    with state.data() as data:
        username = data.get("username")
        password = message.text
        
    
    role = check_user_role(get_db_connection(), username, password)
    
    if role:
        state.delete()
        if role[0] == "admin":
            state.set(UserStates.admin_menu)
            send_admin_menu(message)
        else:
            state.set(UserStates.student_menu)
            state.add_data(student_id=int(role[1])) 
            send_student_menu(message)
    else:
        bot.send_message(message.chat.id, "Noto'g'ri username yoki parol. Qayta kiriting.")
        state.set(UserStates.login)

# Admin Menu
def send_admin_menu(message: Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True,)
    keyboard.add(KeyboardButton("Guruh yaratish"), KeyboardButton("Guruhlar ro'yhati"))
    keyboard.add( KeyboardButton("Fan yaratish"), KeyboardButton("Fanlar ro'yhati"))
    keyboard.add(KeyboardButton("Talaba yaratish"), KeyboardButton("Talabalar Ro'yhati"))
    keyboard.add(KeyboardButton("Akkauntdan chiqish"))
    bot.send_message(message.chat.id, "Admin Menu:", reply_markup=keyboard)

@bot.message_handler(state=UserStates.admin_menu, text=["Talaba yaratish", ])
def admin_create_user(message, state: StateContext):
    state.set(AdminStates.new_user_username)
    bot.send_message(message.chat.id, "Enter the new user's username:")


# New user 
@bot.message_handler(state=AdminStates.new_user_username)
def admin_new_user_username(message, state: StateContext):
    state.add_data(username=message.text)
    state.set(AdminStates.new_user_password)
    bot.send_message(message.chat.id, "Enter the new user's password:")

@bot.message_handler(state=AdminStates.new_user_password)
def admin_new_user_password(message, state: StateContext):
    state.add_data(password=message.text)
    state.set(AdminStates.new_user_role)
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("admin"), KeyboardButton("student"))
    bot.send_message(message.chat.id, "Select role:", reply_markup=keyboard)

@bot.message_handler(state=AdminStates.new_user_role, text=["admin", "student"])
def admin_new_user_role(message, state: StateContext):
    state.add_data(role=message.text)
    state.set(AdminStates.new_user_name)
    bot.send_message(message.chat.id, "Enter full name:")

@bot.message_handler(state=AdminStates.new_user_name)
def admin_new_user_name(message, state: StateContext):
    with state.data() as data:
        username = data.get("username")
        password = data.get("password")
        role = data.get("role")
        name = message.text
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO users (username, password, role, name) VALUES (%s, %s, %s, %s)",
                (username, password, role, name))
    conn.commit()
    cur.close()
    conn.close()
    
    bot.send_message(message.chat.id, "User created successfully!")
    state.set(UserStates.admin_menu)
    send_admin_menu(message)
# New user end

# New group 
@bot.message_handler(text=['Guruh yaratish', ])
def admin_create_group(message: Message, state: StateContext):
    state.set(AdminNewGroupStates.new_group_name)
    state.bot.send_message(
        message.chat.id,
        "Menga yangi guruh uchun nom yuboring.",
        reply_parameters=ReplyParameters(message.id),
        reply_markup=ReplyKeyboardRemove()
    )

@bot.message_handler(state=AdminNewGroupStates.new_group_name)
def admin_new_group_name(message: Message, state: StateContext):
    state.set(AdminNewGroupStates.new_group_quota)
    state.add_data(name=message.text)
    state.bot.send_message(
        message.chat.id,
        "Yangi guruh uchun kvotalar sonini yuboring.",
        reply_parameters=ReplyParameters(message.id)
    )

@bot.message_handler(state=AdminNewGroupStates.new_group_quota)
def admin_new_group_quota(message: Message, state: StateContext):
    
    if not message.text.isnumeric():
        state.bot.send_message(
            message.chat.id,
            "<b>Kvota</b> raqam bo'lishi kerak!",
            reply_parameters=ReplyParameters(message.id),
        )
        return
    
    with state.data() as data:
        name = data.get("name")
        quota = int(message.text)
        create_group(get_db_connection(),name, quota)
    
    
    state.bot.send_message(
        message.chat.id,
        "<b>%s</b> nomli guruh yaratildi ✅" % (name, ),
        reply_parameters=ReplyParameters(message.id),
    )
    
    state.set(UserStates.admin_menu)
    send_admin_menu(message)  
# New group end


# Groups list
@bot.message_handler(text=["Guruhlar ro'yhati", ], state=UserStates.admin_menu)
def view_groups(message: Message, state: StateContext):
    
    
    groups = get_all_groups(get_db_connection())
    state.set(AdminAssignSubjectStates.view_group)
    if groups:
        
        keyboard = InlineKeyboardMarkup()
        for i in groups:
            keyboard.add(
                InlineKeyboardButton(f"{i[1]}", callback_data=f"gr_{i[0]}")
            )
        keyboard.add(InlineKeyboardButton("Bekor qilish", callback_data="cancel"))
        bot.send_message(message.chat.id, "Guruhlar ro'yhati", reply_markup=ReplyKeyboardRemove())
        bot.send_message(
                message.chat.id,
                "Guruhni tanlang 👇",
                reply_parameters=ReplyParameters(message.id),
                parse_mode="HTML",
                reply_markup=keyboard
            )
    else : 
        bot.send_message(message.chat.id, "Hech qanday gruhlar mavjud emas.")
        state.set(UserStates.admin_menu)
        send_admin_menu(message)
    
    return

@bot.message_handler(text=["Guruhlar ro'yhati", ], state=UserStates.student_menu)
def view_groups_by_student(message: Message, state: StateContext):
    state.set(StudentJoinGroupStates.view_group)
    groups = get_all_groups(get_db_connection())
    if groups:
        
        keyboard = InlineKeyboardMarkup()
        for i in groups:
            keyboard.add(
                InlineKeyboardButton(f"{i[1]}", callback_data=f"gr_{i[0]}")
            )
        bot.send_message(message.chat.id, "Guruhlar ro'yhati", reply_markup=ReplyKeyboardRemove())
        
        bot.send_message(
                message.chat.id,
                "Yozilish uchun guruhni tanlang 👇",
                reply_parameters=ReplyParameters(message.id),
                parse_mode="HTML",
                reply_markup=keyboard
            )
# Groups list end

# Group details
@bot.callback_query_handler(state=AdminAssignSubjectStates.view_group)
def view_group_details(call: CallbackQuery, state: StateContext):
    state.set(AdminAssignSubjectStates.select_group)
    
    bot.delete_message(call.message.chat.id, call.message.id)
    
    group = get_group_by_id(get_db_connection(), call.data.split("_")[1])
    assigments = get_assigments(get_db_connection(), group[0])
    subjects_list = []
    students_list = []
    
    for i in assigments[0]:
        subject = get_subject_by_id(get_db_connection(), i[0])
        subjects_list.append(subject[1])
    
    for j in assigments[1]:
        student = get_user_by_id(get_db_connection(), j[0])
        students_list.append(student[1])
        
    text = f"<b>Guruh nomi:</b> {group[1]}.\n<b>Kvotalar soni: {group[2]}</b> \n\n<b>Fanlar:</b>\n"
    text+=", ".join(subjects_list)
    
    text+="\n\n<b>Guruhdagi talabalar:</b> "
    text+=", ".join(students_list)
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Fan qo'shish", callback_data=f"gr_{group[0]}"))
    keyboard.add(InlineKeyboardButton("Bekor qilish", callback_data=f"cancel"))
    
    bot.send_message(call.message.chat.id, text, reply_markup=keyboard)

@bot.callback_query_handler(state=StudentJoinGroupStates.view_group)
def view_group_details_for_students(call: CallbackQuery, state: StateContext):
    group_id = call.data.split("_")[1]
    
    state.set(StudentJoinGroupStates.select_group)
    state.add_data(group_id=group_id)
    
    group = get_group_by_id(get_db_connection(), group_id)
    assigments = get_assigments(get_db_connection(), group[0])
    
    subjects_list = []
    for i in assigments[0]:
        subject = get_subject_by_id(get_db_connection(), i[0])
        subjects_list.append(subject[1])
    
    text = f"<b>Guruh nomi:</b> {group[1]}.\n<b>Kvotalar soni: {group[2]}</b> \n\nFanlar:\n"
    text+=", ".join(subjects_list)
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Guruhga yozilish", callback_data=f"gr_{group[0]}"))
    
    bot.delete_message(call.message.chat.id, call.message.id)
    bot.send_message(call.message.chat.id, text, reply_markup=keyboard)
# Group details end


# Get all Students
@bot.message_handler(text=['Talabalar Ro\'yhati', ])
def view_students(message: Message, state: StateContext):
    users = get_all_users(get_db_connection(), 'student')
    
    bot.send_message(
            message.chat.id,
            '\n'.join(["<b>%d</b>. <i>%s</i>,  %s" % (i[0], i[1], i[3]) for i in users ]),
            reply_parameters=ReplyParameters(message.id),
            parse_mode="HTML",
        )
    
    return
# Get all Students end


# New subject starts
@bot.message_handler(text=['Fan yaratish', ])
def admin_new_subject(message: Message, state: StateContext):
    state.set(AdminNewSubjectStates.new_subject_name)
    bot.send_message(
            message.chat.id,
            'Menga fan nomini yuboring.',
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove()
        )

@bot.message_handler(state=AdminNewSubjectStates.new_subject_name)
def admin_new_subject_name(message: Message, state: StateContext):
    create_subject(get_db_connection(), message.text)
    state.bot.send_message(
        message.chat.id,
        "<b>%s</b> nomli fan yaratildi ✅" % (message.text, ),
        reply_parameters=ReplyParameters(message.id),
    )
    state.set(UserStates.admin_menu)
    send_admin_menu(message)
# New Subject ends 
    
    
# Fanlar ro'yhati start
@bot.message_handler(text=["Fanlar ro'yhati"])
def view_subjects(message: Message, state: StateContext):
    bot.send_message(
            message.chat.id,
            '\n'.join(["%s. <b>%s</b>." % i for i in get_all_subjects(get_db_connection())]),
            reply_parameters=ReplyParameters(message.id),
            parse_mode="HTML",
        )
    
    return
# Fanlar ro'yhati ends ends


# assignments starts
@bot.callback_query_handler(state=AdminAssignSubjectStates.select_group)
def admin_assign_subject_group(call: CallbackQuery, state: StateContext):
    state.set(AdminAssignSubjectStates.select_subject)
    data = call.data.split("_")
    state.add_data(group_id=data[1])
    
    subjects = get_all_subjects(get_db_connection())
    
    if subjects:
        
        group = get_group_by_id(get_db_connection(), int(data[1]) )
        assigments = get_assigments(get_db_connection(), int(data[1]))
        keyboard = InlineKeyboardMarkup()
        for _id, _name in subjects:
            has = False
            for i in assigments[0]:
                print(i[0] == _id)
                has = True if i[0] == _id else False
            
            if not has: keyboard.add(InlineKeyboardButton(_name, callback_data=f'sb_{_id}'))
            else: keyboard.add(InlineKeyboardButton(f"Mavjud: {_name}", callback_data="0"))
            
        
        bot.answer_callback_query(call.id, "✅")
        bot.delete_message(call.message.chat.id, call.message.id)
        
        
        text = f"<b>{group[1]}</b> guruhi uchun qo'shmoqchi bo'lgan fanni tanlang!"
        bot.send_message(call.message.chat.id, text, reply_markup=keyboard)
    
    else:
        state.delete()
        bot.send_message("Hozircha Fanlar mavjud emas.")
        send_admin_menu(call.message)
        
@bot.callback_query_handler(state=AdminAssignSubjectStates.select_subject)
def admin_assign_subject_subject(call: CallbackQuery, state: StateContext):
    
    bot.answer_callback_query(call.id, "✅")
    bot.delete_message(call.message.chat.id, call.message.id)
    
    data = call.data.split("_")
    
    with state.data() as dt:
        
        group_id = dt.get("group_id")
        subject_id = data[1]
        assign_student_and_subjects(get_db_connection(), group_id, [], [subject_id, ])
    
    
    state.delete()
    state.set(UserStates.admin_menu)
    bot.send_message(call.message.chat.id, "✅ Fan biriktirildi.")
    send_admin_menu(call.message)


@bot.callback_query_handler(state=StudentJoinGroupStates.select_group)
def join_group_by_students(call: CallbackQuery, state: StateContext):
    
    with state.data() as data:
        assign_student_and_subjects(get_db_connection(), int(data.get("group_id")), [data.get("student_id"), ], [])
    
    bot.delete_message(call.message.chat.id, call.message.id)
    bot.send_message(call.message.chat.id, "Siz guruhga qo'shildingiz")
    state.set(UserStates.student_menu)
    send_student_menu(call.message)
# assigments ends


# Student Menu
def send_student_menu(message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("Guruhlar ro'yhati"))
    keyboard.add(KeyboardButton("Akkauntdan chiqish"))
    bot.send_message(message.chat.id, "Student Menu:", reply_markup=keyboard)


# Add custom filters
bot.add_custom_filter(custom_filters.StateFilter(bot))
bot.add_custom_filter(custom_filters.IsDigitFilter())
bot.add_custom_filter(custom_filters.TextMatchFilter())

# necessary for state parameter in handlers.
from telebot.states.sync.middleware import StateMiddleware

bot.setup_middleware(StateMiddleware(bot))