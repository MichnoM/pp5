import streamlit as st
import hashlib
import sqlite3
import random
import time

# Helper functions for password hashing
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Database setup
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    # Create the table if it doesn't exist
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            best_score REAL DEFAULT 0
        )
    ''')
    # Check if 'best_score' column exists, add it if not
    c.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in c.fetchall()]
    if "best_score" not in columns:
        c.execute("ALTER TABLE users ADD COLUMN best_score REAL DEFAULT 0")
    conn.commit()
    conn.close()

# Ensure the database is initialized only once
init_db()

def register_user(username, password):
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hash_password(password)))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def login_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, hash_password(password)))
    user = c.fetchone()
    conn.close()
    return user is not None

def get_best_score(username):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT best_score FROM users WHERE username = ?", (username,))
    best_score = c.fetchone()
    conn.close()
    return best_score[0] if best_score else 0

def update_best_score(username, new_score):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT best_score FROM users WHERE username = ?", (username,))
    current_best = c.fetchone()[0]
    if new_score > current_best:
        c.execute("UPDATE users SET best_score = ? WHERE username = ?", (new_score, username))
        conn.commit()
    conn.close()

# Sample texts for the Typing Speed Test
SAMPLE_TEXTS = [
    "The quick brown fox jumps over the lazy dog. A journey of a thousand miles begins with a single step.",
    "Actions speak louder than words. Better late than never.",
    "In the middle of difficulty lies opportunity. Success is not final, failure is not fatal: It is the courage to continue that counts.",
    "A journey of a thousand miles begins with a single step, but every step requires persistence and determination.",
    "Machine learning models utilize optimization algorithms to minimize loss functions and improve predictive accuracy."
]

def calculate_wpm(start_time, end_time, text):
    time_taken = end_time - start_time  # Time in seconds
    word_count = len(text.split())  # Number of words in the text
    wpm = (word_count / time_taken) * 60  # Words per minute
    return wpm, time_taken

def main():
    st.title("Welcome to the Typing Speed Test!")

    # Initialize session state for login and game state
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = ""
    if "game_started" not in st.session_state:
        st.session_state.game_started = False
        st.session_state.start_time = None
        st.session_state.selected_text = None
        st.session_state.current_score = None

    # Navigation with tabs
    tab1, tab2, tab3 = st.tabs(["Home", "Register", "Login"])

    with tab1:
        if st.session_state.logged_in:
            st.success(f"Logged in as {st.session_state.username}")
            st.subheader("Take the test!")

            best_score = get_best_score(st.session_state.username)
            st.write(f"Your Best Score: **{round(best_score, 2)} WPM**")

            # Typing Speed Test Section
            if not st.session_state.game_started:
                st.write("Click the button below to start the Typing Speed Test.")
                if st.button("Start Typing Speed Test"):
                    st.session_state.game_started = True
                    st.session_state.start_time = time.time()
                    st.session_state.selected_text = random.choice(SAMPLE_TEXTS)
                    st.rerun()
            else:
                st.write("**Type the text below as quickly as possible:**")
                st.write(f"> {st.session_state.selected_text}")
                user_input = st.text_area("Start typing here:", height=150)

                # Check if the user has completed typing
                if user_input.strip() == st.session_state.selected_text:
                    end_time = time.time()
                    wpm, time_taken = calculate_wpm(
                        st.session_state.start_time, end_time, st.session_state.selected_text
                    )
                    st.success(f"Great job! You completed the test in {round(time_taken, 2)} seconds.")
                    st.success(f"Your typing speed is {round(wpm, 2)} WPM.")
                    st.session_state.current_score = wpm

                    # Update the user's best score
                    update_best_score(st.session_state.username, wpm)

                    # Reset game state for replay
                    st.session_state.game_started = False

            # Restart button
            if st.session_state.current_score is not None:
                if st.button("Restart Test"):
                    st.session_state.game_started = False
                    st.session_state.start_time = None
                    st.session_state.selected_text = None
                    st.session_state.current_score = None
                    st.rerun()

        else:
            st.write("Please register or log in to access the game.")

    with tab2:
        st.subheader("Register")
        username = st.text_input("Username", key="register_username")
        password = st.text_input("Password", type="password", key="register_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="register_confirm_password")
        
        if st.button("Register", key="register_button"):
            if username and password:
                if password == confirm_password:
                    if register_user(username, password):
                        st.success("Registration successful! Please log in.")

                    else:
                        st.error("Username already exists. Please choose another.")
                else:
                    st.error("Passwords do not match.")
            else:
                st.error("Please enter username and password.")

    with tab3:
        st.subheader("Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login", key="login_button"):
            if login_user(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()

            else:
                st.error("Invalid username or password. Please try again.")
        
        if st.session_state.logged_in:
            st.success(f"Welcome {username}! You are logged in.")

if __name__ == '__main__':
    main()
