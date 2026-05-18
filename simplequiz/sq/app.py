import streamlit as st
import random
import json

st.set_page_config(
    page_title="School Quiz Challenge",
    page_icon="🎓",
    layout="centered"
)

# Load questions from JSON file
with open("questions.json", "r", encoding="utf-8") as file:
    QUESTION_BANK = json.load(file)

# Initialize Session State
if "quiz_questions" not in st.session_state:
    st.session_state.quiz_questions = random.sample(QUESTION_BANK, 10)

if "submitted" not in st.session_state:
    st.session_state.submitted = False

st.title("🎓 School Quiz Challenge")
st.write("Test your knowledge with fun questions!")

user_answers = []

with st.form("quiz_form"):
    for index, q in enumerate(st.session_state.quiz_questions):
        st.subheader(f"Question {index + 1}")
        st.caption(q["category"])

        answer = st.radio(
            q["question"],
            q["options"],
            key=f"q_{index}"
        )

        user_answers.append(answer)

    submit_button = st.form_submit_button("Submit Quiz")

# Evaluate Score
if submit_button:
    score = 0

    st.divider()
    st.header("📊 Quiz Results")

    for index, q in enumerate(st.session_state.quiz_questions):
        correct_answer = q["answer"]
        selected_answer = user_answers[index]

        if selected_answer == correct_answer:
            score += 1
            st.success(f"Q{index + 1}: Correct! ✅")
        else:
            st.error(
                f"Q{index + 1}: Wrong ❌ | Correct Answer: {correct_answer}"
            )

    st.divider()

    st.metric("Your Score", f"{score} / 10")

    if score >= 8:
        st.balloons()
        st.success("Excellent work! 🌟")
    elif score >= 5:
        st.info("Good job! Keep learning! 📚")
    else:
        st.warning("Nice try! Practice makes perfect! 💡")

# Restart Button
if st.button("🔄 Start New Quiz"):
    st.session_state.quiz_questions = random.sample(QUESTION_BANK, 10)
    st.rerun()