import streamlit as st
import pandas as pd
import random

# Load CSV from the URL
@st.cache_data
def load_csv():
    csv_url = "https://raw.githubusercontent.com/kwonsungja/First-App-Nouns/main/regular_Nouns_real.csv"
    try:
        df = pd.read_csv(csv_url)
        df.columns = df.columns.str.lower()
        df["singular"] = df["singular"].str.strip()
        df["level"] = df["level"].str.strip()
        return df
    except Exception as e:
        st.error(f"Failed to load the CSV file: {e}")
        return pd.DataFrame()

df = load_csv()

# Initialize user state
if "user_state" not in st.session_state:
    st.session_state.user_state = {
        "remaining_nouns": pd.DataFrame(),
        "current_level": None,
        "score": 0,
        "trials": 0,
        "current_index": -1,
        "level_scores": {level: {"score": 0, "trials": 0} for level in ["s", "es", "ies"]},
    }
if "question" not in st.session_state:
    st.session_state.question = ""

# Helper functions
def pluralize(noun):
    noun = noun.strip()
    if noun.endswith(('s', 'ss', 'sh', 'ch', 'x', 'z', 'o')):
        return noun + 'es'
    elif noun.endswith('y') and not noun[-2] in 'aeiou':
        return noun[:-1] + 'ies'
    else:
        return noun + 's'

def filter_nouns_if_needed(level, user_state):
    if user_state["current_level"] != level:
        filtered_nouns = df[df["level"] == level].copy()
        if filtered_nouns.empty:
            return user_state, f"No nouns available for the Level: {level}. Please select a different level."
        user_state["remaining_nouns"] = filtered_nouns
        user_state["current_level"] = level
        user_state["score"] = 0
        user_state["trials"] = 0
        user_state["current_index"] = -1
        return user_state, f"Level {level} selected. Click 'Show Noun' to start!"
    return user_state, None

def show_next_noun(level, user_state):
    user_state, feedback = filter_nouns_if_needed(level, user_state)
    if user_state["remaining_nouns"].empty:
        return user_state, feedback or "All nouns have been answered correctly. Great job!"
    selected_noun = user_state["remaining_nouns"].sample(1).iloc[0]
    user_state["current_index"] = selected_noun.name
    return user_state, f"What's the plural form of '{selected_noun['singular']}'?"

def check_plural(user_plural, user_state):
    if user_state["remaining_nouns"].empty:
        return user_state, f"All nouns have been answered correctly. Great job! (Score: {user_state['score']}/{user_state['trials']})"

    index = user_state["current_index"]
    if index == -1:
        return user_state, "Please click 'Show Noun' first."

    noun_data = user_state["remaining_nouns"].iloc[index]
    singular = noun_data["singular"]
    correct_plural = pluralize(singular)

    user_state["trials"] += 1
    user_state["level_scores"][user_state["current_level"]]["trials"] += 1

    if user_plural.strip().lower() == correct_plural.strip().lower():
        user_state["score"] += 1
        user_state["level_scores"][user_state["current_level"]]["score"] += 1
        feedback = f"✅ Correct! '{correct_plural}' is the plural form of '{singular}'."
        user_state["remaining_nouns"] = user_state["remaining_nouns"].drop(index)
    else:
        feedback = f"❌ Incorrect. The correct plural form is '{correct_plural}' for '{singular}'."

    return user_state, feedback

def display_total_score(user_state):
    return ", ".join(
        f"{level}({user_state['level_scores'][level]['score']}/{user_state['level_scores'][level]['trials']})"
        for level in ["s", "es", "ies"]
    )

# Streamlit UI
st.title("NounSmart: Practice Regular Plural Nouns")
st.write("## How to Use the App")
st.write("1. Select a Level and start practicing!")
st.write("2. Follow the steps to answer and review your progress.")

# Level Selection
levels = ["s", "es", "ies"]
selected_level = st.selectbox("Select Level", levels, key="selected_level")

# Show Noun Button
if st.button("Show Noun"):
    st.session_state.user_state, question = show_next_noun(selected_level, st.session_state.user_state)
    st.session_state.question = question
    st.write(question)

# Display Question and Input
if st.session_state.question:
    st.text_input("Enter Your Answer", key="user_input")
    if st.button("Submit Answer"):
        user_input = st.session_state.user_input
        st.session_state.user_state, feedback = check_plural(user_input, st.session_state.user_state)
        st.write(feedback)

# Show Total Score
if st.button("Show Total Score"):
    total_score = display_total_score(st.session_state.user_state)
    st.write(f"Overall Score: {total_score}")

