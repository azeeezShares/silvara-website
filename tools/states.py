from telebot.states import State, StatesGroup

# Define States
class UserStates(StatesGroup):
    login = State()
    password = State()
    admin_menu = State()
    student_menu = State()

class StudentJoinGroupStates(StatesGroup):
    view_group = State()
    select_group = State()

class AdminStates(StatesGroup):
    new_user_username = State()
    new_user_password = State()
    new_user_role = State()
    new_user_name = State()
    
class AdminNewGroupStates(StatesGroup):
    new_group_name = State()
    new_group_quota = State()

class AdminNewSubjectStates(StatesGroup):
    new_subject_name = State()
    
class AdminAssignStudentAndSubject(StatesGroup):
    assign_student_name = State()
    assign_subject_name = State()

class AdminAssignSubjectStates(StatesGroup):
    view_group = State()
    select_group = State()
    select_subject = State()