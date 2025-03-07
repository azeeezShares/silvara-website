import psycopg2
from psycopg2.extensions import connection


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

def get_all_subjects(conn:connection, ):
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


def create_group(conn: connection, name:str, quota: int):
    cur = conn.cursor()
    
    query = "INSERT INTO groups (name, quota) VALUES (%s, %s) RETURNING id;"
    cur.execute(query, (name, quota))
    
    conn.commit()
    cur.close()
    conn.close()
    
    


def assign_student_and_subjects(conn: connection, group_id, student_ids, subject_ids):
    try:
        cur = conn.cursor()
        # Insert students into group_students table
        for student_id in student_ids:
            student_query = "INSERT INTO group_students (group_id, student_id) VALUES (%s, %s);"
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

def check_user_role(conn: connection, username: str, password: str):
    cur = conn.cursor()
    cur.execute("SELECT role FROM users WHERE username=%s AND password=%s", (username, password))
    user = cur.fetchone()
    cur.close()
    conn.close()
    
    if user: return 'admin' if user[0] == 'admin' else 'student'
    else: return False

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