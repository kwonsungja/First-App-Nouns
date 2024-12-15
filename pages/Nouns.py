import gradio as gr
import pandas as pd
import random
from functools import lru_cache

@lru_cache(maxsize=1)
def load_csv():
    # CSV URL을 업데이트
    csv_url = "https://raw.githubusercontent.com/kwonsungja/First-App-Nouns/main/regular_Nouns_real.csv"
    try:
        df = pd.read_csv(csv_url)
        df.columns = df.columns.str.lower()
        df["singular"] = df["singular"].str.strip()
        df["level"] = df["level"].str.strip()
        return df
    except Exception as e:
        raise Exception(f"Failed to load the CSV file: {e}")

df = load_csv()

# 각 레벨의 항목 수 계산
counts = df["level"].value_counts()
levels_with_counts = [
    f"{level} ({counts.get(level, 0)} items)"
    for level in ["s", "es", "ies"]
]

def initialize_user_state():
    return {
        "remaining_nouns": pd.DataFrame(),
        "current_level": None,
        "score": 0,
        "trials": 0,
        "current_index": -1,
        "level_scores": {level: {"score": 0, "trials": 0} for level in ["s", "es", "ies"]},
    }

def pluralize(noun):
    noun = noun.strip()
    if noun.endswith(('s', 'ss', 'sh', 'ch', 'x', 'z', 'o')):
        return noun + 'es'
    elif noun.endswith('y') and not noun[-2] in 'aeiou':
        return noun[:-1] + 'ies'
    else:
        return noun + 's'

def filter_nouns_if_needed(level_with_count, user_state):
    level = level_with_count.split(" ")[0]
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

def show_next_noun(level_with_count, user_state):
    user_state, feedback = filter_nouns_if_needed(level_with_count, user_state)
    if user_state["remaining_nouns"].empty:
        return user_state, feedback or "All nouns have been answered correctly. Great job!", ""
    selected_noun = user_state["remaining_nouns"].sample(1).iloc[0]
    user_state["current_index"] = selected_noun.name
    return user_state, f"What's the plural form of '{selected_noun['singular']}'?", ""

def check_plural(user_plural, user_state):
    if user_state["remaining_nouns"].empty:
        return user_state, f"All nouns have been answered correctly. Great job! (Score: {user_state['score']}/{user_state['trials']})"

    index = user_state["current_index"]
    if index == -1:
        return user_state, f"Please click 'Show Noun' first. (Score: {user_state['score']}/{user_state['trials']})"

    noun_data = user_state["remaining_nouns"].iloc[index]
    singular = noun_data["singular"]
    correct_plural = pluralize(singular)

    user_state["trials"] += 1
    user_state["level_scores"][user_state["current_level"]]["trials"] += 1

    if user_plural.strip().lower() == correct_plural.strip().lower():
        user_state["score"] += 1
        user_state["level_scores"][user_state["current_level"]]["score"] += 1
        feedback = f"✅ Correct! '{correct_plural}' is the plural form of '{singular}'. Click 'Show Noun' to continue."
        user_state["remaining_nouns"] = user_state["remaining_nouns"].drop(index)
    else:
        feedback = f"❌ Incorrect. The correct plural form is '{correct_plural}' for '{singular}'."

    return user_state, f"{feedback} (Score: {user_state['score']}/{user_state['trials']})"

def display_total_score(user_state):
    total_score = ", ".join(
        f"{level}({user_state['level_scores'][level]['score']}/{user_state['level_scores'][level]['trials']})"
        for level in ["s", "es", "ies"]
    )
    return total_score

# Gradio 인터페이스 설정
with gr.Blocks() as app:
    gr.Markdown("# NounSmart: Practice Regular Plural Nouns")
    gr.Markdown("""
    ## How to Use the App
    1. **Select a Level and start practicing!**
    2. **Follow the steps to answer and review your progress.**
    """)

    with gr.Row():
        level_dropdown = gr.Dropdown(
            label="Select Level",
            choices=levels_with_counts,
            value=levels_with_counts[0],
            interactive=True
        )

    with gr.Row():
        show_button = gr.Button("Show Noun")
        noun_display = gr.Textbox(label="Singular Noun", value="Select a level to start", interactive=False)

    with gr.Row():
        plural_input = gr.Textbox(
            label="Enter Your Answer",
            placeholder="Type the plural form here",
            interactive=True
        )

    with gr.Row():
        submit_button = gr.Button("Submit Answer")
        feedback_display = gr.Textbox(label="Feedback", interactive=False)

    with gr.Row():
        total_score_button = gr.Button("Show Total Score")
        total_score_display = gr.Textbox(label="Overall Score", interactive=False)

    state = gr.State(initialize_user_state())

    # 버튼 기능 연결
    show_button.click(fn=show_next_noun, inputs=[level_dropdown, state], outputs=[state, noun_display, plural_input])
    submit_button.click(fn=check_plural, inputs=[plural_input, state], outputs=[state, feedback_display])
    total_score_button.click(fn=display_total_score, inputs=state, outputs=total_score_display)

app.launch()
