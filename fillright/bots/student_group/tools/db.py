import psycopg2
from psycopg2.extensions import connection


def check_user_role(conn: connection, username: str, password: str):
    cur = conn.cursor()
    cur.execute(
        "SELECT id, role FROM users WHERE username=%s AND password=%s", (username, password))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user:
        return ('admin', user[0]) if user[1] == 'admin' else ('student', user[0])
    else:
        return False


def get_all_users(conn: connection, role: str):
    try:
        cur = conn.cursor()

        # SQL query to get all users
        query = "SELECT id, username, role, name FROM users WHERE role = %s;"
        cur.execute(query, (role,))

        # Fetch all users
        users = cur.fetchall()

        # Close connection
        cur.close()
        conn.close()

        return users  # Return list of users

    except psycopg2.Error as e:
        return []


def get_users_by_group_id(conn: connection, group_id: int):
    try:
        cur = conn.cursor()
        query = """
                    SELECT u.id, u.username, u.role, u.name
                    FROM users u
                    JOIN group_students gs ON u.id = gs.user_id
                    WHERE gs.group_id = %s;
                """
        cur.execute(query, (group_id,))
        users = cur.fetchall()
        cur.close()
        conn.close()
        return users
    except psycopg2.Error:
        return []


def get_user_by_id(conn: connection, user_id):
    cur = conn.cursor()

    # SQL query to get all subjects
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cur.execute(query)

    # Fetch subject
    subject = cur.fetchall()[0]

    # Close connection
    cur.close()
    conn.close()

    return subject  # Return subject


def create_subject(conn: connection, name: str):
    try:
        cur = conn.cursor()

        # SQL query to insert a subject
        query = "INSERT INTO subjects (name) VALUES (%s) RETURNING id;"
        cur.execute(query, (name,))

        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        return False


def get_all_subjects(conn: connection, ):
    cur = conn.cursor()

    # SQL query to get all groups
    query = "SELECT id, name FROM subjects;"
    cur.execute(query)

    # Fetch all groups
    groups = cur.fetchall()

    # Close connection
    cur.close()
    conn.close()

    return groups  # Return list of groups


def get_subject_by_id(conn: connection, subject_id: int):
    cur = conn.cursor()

    # SQL query to get all subjects
    query = f"SELECT * FROM subjects WHERE id = {subject_id}"
    cur.execute(query)

    # Fetch subject
    subject = cur.fetchall()[0]

    # Close connection
    cur.close()
    conn.close()

    return subject  # Return subject


def create_group(conn: connection, name: str, quota: int):
    cur = conn.cursor()

    query = "INSERT INTO groups (name, quota) VALUES (%s, %s) RETURNING id;"
    cur.execute(query, (name, quota))

    conn.commit()
    cur.close()
    conn.close()


def get_all_groups(conn: connection):
    cur = conn.cursor()

    # SQL query to get all groups
    query = "SELECT id, name, quota FROM groups;"
    cur.execute(query)

    # Fetch all groups
    groups = cur.fetchall()

    # Close connection
    cur.close()
    conn.close()

    return groups  # Return list of groups


def get_group_by_id(conn: connection, group_id: int):
    cur = conn.cursor()

    # SQL query to get all groups
    query = f"SELECT * FROM groups WHERE id = {group_id}"
    cur.execute(query)

    # Fetch group
    group = cur.fetchall()[0]

    # Close connection
    cur.close()
    conn.close()

    return group  # Return group


def assign_student_and_subjects(conn: connection, group_id, student_ids, subject_ids):
    try:
        cur = conn.cursor()
        # Insert students into group_students table
        for student_id in student_ids:
            student_query = "INSERT INTO group_students (group_id, user_id) VALUES (%s, %s);"
            cur.execute(student_query, (group_id, student_id))

        # Insert subjects into group_subjects table
        for subject_id in subject_ids:
            subject_query = "INSERT INTO group_subjects (group_id, subject_id) VALUES (%s, %s);"
            cur.execute(subject_query, (group_id, subject_id))

        # Commit transaction
        conn.commit()

        # Close connection
        cur.close()
        conn.close()

    except psycopg2.Error as e:
        print("Database error:", e)


def get_assigments(conn: connection, group_id):
    subjects = []
    students = []

    cur = conn.cursor()

    cur.execute(
        "SELECT subject_id FROM group_subjects WHERE group_id=%s", (group_id, ))
    subjects = cur.fetchall()

    cur.execute(
        "SELECT user_id FROM group_students WHERE group_id=%s", (group_id, ))
    students = cur.fetchall()

    cur.close()
    conn.close()

    return subjects, students
