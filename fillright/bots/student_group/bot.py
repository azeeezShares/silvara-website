import os
import telebot
import psycopg2
from django.conf import settings

from dotenv import load_dotenv
from telebot import custom_filters
from telebot.storage import StateMemoryStorage
from telebot.states.sync.context import StateContext
from .tools.db import get_all_groups, create_subject, get_all_subjects, get_all_users, check_user_role, create_group
from telebot.types import  Message, ReplyKeyboardMarkup, KeyboardButton,ReplyParameters, ReplyKeyboardRemove
from .tools.states import UserStates, AdminStates, AdminNewGroupStates, AdminNewSubjectStates
# from telebot.states.sync.middleware import StateMiddleware

# load dotenv
load_dotenv(settings.BASE_DIR/'.env')



# Bot Token
TOKEN = os.getenv("BOT_TOKEN")
state_storage = StateMemoryStorage()
bot = telebot.TeleBot(TOKEN, state_storage=state_storage, use_class_middlewares=True, parse_mode="HTML")

# Database Connection
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}
def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


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
        if role == "admin":
            state.set(UserStates.admin_menu)
            send_admin_menu(message)
        else:
            state.set(UserStates.student_menu)
            send_student_menu(message)
    else:
        bot.send_message(message.chat.id, "Noto'g'ri username yoki parol. Qayta kiriting.")
        state.set(UserStates.login)

# Admin Menu
def send_admin_menu(message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True,)
    keyboard.add(KeyboardButton("Guruh yaratish"), KeyboardButton("Guruhlar ro'yhati"))
    keyboard.add( KeyboardButton("Fan yaratish"), KeyboardButton("Fanlar ro'yhati"))
    keyboard.add(KeyboardButton("Talaba yaratish"), KeyboardButton("Talabalar Ro'yhati"))
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
        "Menga yangi gutuh uchun nom yuboring.",
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
        create_group(name, quota)
    
    
    state.bot.send_message(
        message.chat.id,
        "<b>%s</b> nomli guruh yaratildi ✅" % (name, ),
        reply_parameters=ReplyParameters(message.id),
    )
    
    state.set(UserStates.admin_menu)
    send_admin_menu(message)
        
# New group end



# Groups list
@bot.message_handler(text=['Guruhlar ro\'yhati', ])
def view_groups(message: Message, state: StateContext):
    bot.send_message(
            message.chat.id,
            '\n'.join(["%s. <b>%s</b>. Kvota: %d" % i for i in get_all_groups(get_db_connection())]),
            reply_parameters=ReplyParameters(message.id),
            parse_mode="HTML",
        )
    
    return
# Groups list end

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
    

@bot.message_handler(text=["Fanlar ro'yhati"])
def view_subjects(message: Message, state: StateContext):
    bot.send_message(
            message.chat.id,
            '\n'.join(["%s. <b>%s</b>." % i for i in get_all_subjects(get_db_connection())]),
            reply_parameters=ReplyParameters(message.id),
            parse_mode="HTML",
        )
    
# New subject ends


# Assign subject
@bot.message_handler(text=["Fan qo'shish"])
def admin_assign_subject(message: Message, state: StateContext):
    
    
    
    bot.send_message(
            message.chat.id,
            '\n'.join(["%s. <b>%s</b>." % i for i in get_all_subjects(get_db_connection())]),
            reply_parameters=ReplyParameters(message.id),
            parse_mode="HTML",
        )

# Assign subject ends


# Student Menu
def send_student_menu(message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("Guruhlar ro'yhati"), KeyboardButton("Join Group"))
    keyboard.add(KeyboardButton("Leave Group"))
    bot.send_message(message.chat.id, "Student Menu:", reply_markup=keyboard)

@bot.message_handler(state=UserStates.student_menu, text=["Guruhlar ro'yhati", ])
def view_groups(message):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM groups")
    groups = cur.fetchall()
    cur.close()
    conn.close()
    
    group_list = "\n".join([g[0] for g in groups]) if groups else "No groups available."
    bot.send_message(message.chat.id, f"Available Groups:\n{group_list}")


# Add custom filters
bot.add_custom_filter(custom_filters.StateFilter(bot))
bot.add_custom_filter(custom_filters.IsDigitFilter())
bot.add_custom_filter(custom_filters.TextMatchFilter())

# necessary for state parameter in handlers.
from telebot.states.sync.middleware import StateMiddleware

bot.setup_middleware(StateMiddleware(bot))