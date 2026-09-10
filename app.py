import streamlit as st
import re
from collections import Counter
from datetime import datetime

st.set_page_config(page_title="Ms. Velasco's Assistant", page_icon="🇪🇸", layout="wide")

st.title("🇪🇸 Ms. Velasco's Assistant")
st.caption("A teacher productivity tool for checking Spanish writing, giving feedback, and spotting class-wide patterns.")

if "results" not in st.session_state:
    st.session_state.results = []

COMMON_ERRORS = [
    (r"\byo\s+soy\s+\w+o\b", "Check whether the adjective/noun agrees with the subject.", "Review gender and number agreement."),
    (r"\b(yo|tú|él|ella)\s+es\s+\w+\b", "Check the subject-verb combination.", "Make sure the form of ser matches the subject."),
    (r"\byo\s+tiene\b", "Yo tengo", "The verb tener is irregular: yo tengo."),
    (r"\byo\s+es\b", "Yo soy", "Use soy with yo when using ser."),
    (r"\btu\s+\b", "tú", "Use the accent in tú when it means 'you'."),
    (r"\bcomo\s+estas\b", "¿Cómo estás?", "Cómo and estás require accents in this question."),
    (r"\bque\s+tal\b", "¿Qué tal?", "Qué takes an accent in this expression/question."),
    (r"\b(esta|estas)\b", "Check whether está/estás is needed.", "Estar forms often require an accent: está, estás."),
]


def check_spanish(text, min_words):
    mistakes = []
    words = re.findall(r"\b[\wáéíóúüñÁÉÍÓÚÜÑ'-]+\b", text)
    word_count = len(words)

    if min_words and word_count < min_words:
        mistakes.append({
            "type": "Requirement",
            "original": f"{word_count} words",
            "correction": f"At least {min_words} words",
            "explanation": "The response is below the required word count."
        })

    if text and text[0].islower():
        mistakes.append({"type": "Capitalization", "original": text[0], "correction": text[0].upper(), "explanation": "Start a sentence with a capital letter."})

    if text.strip() and text.rstrip()[-1] not in ".!?¿¡":
        mistakes.append({"type": "Punctuation", "original": "No ending punctuation", "correction": "Add . ! or ?", "explanation": "Complete sentences should normally end with punctuation."})

    for pattern, correction, explanation in COMMON_ERRORS:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            mistakes.append({"type": "Grammar", "original": match.group(0), "correction": correction, "explanation": explanation})

    return word_count, mistakes


def estimate_grade(word_count, mistakes, min_words):
    score = 100
    if min_words and word_count < min_words:
        score -= 10
    score -= min(len(mistakes), 9) * 7
    return max(0, min(100, score))

page = st.sidebar.radio("Go to", ["Check Assignment", "Class Results"])

if page == "Check Assignment":
    st.header("Check a Student Assignment")
    st.write("Enter the assignment requirements and the student's Spanish response. The assistant will flag common issues and generate teacher-friendly feedback.")

    col1, col2 = st.columns(2)
    with col1:
        assignment = st.text_input("Assignment name", placeholder="Mi familia")
        student = st.text_input("Student name", placeholder="Student 1")
    with col2:
        min_words = st.number_input("Minimum word count", min_value=0, value=50, step=5)
        rubric = st.text_area("Teacher focus / rubric", placeholder="Use ser and estar correctly; describe your family.")

    response = st.text_area("Student's Spanish response", height=260, placeholder="Paste the student's response here...")

    if st.button("Check Assignment", type="primary"):
        if not student.strip() or not response.strip():
            st.warning("Please enter a student name and response.")
        else:
            words, mistakes = check_spanish(response, min_words)
            grade = estimate_grade(words, mistakes, min_words)
            result = {
                "student": student.strip(),
                "assignment": assignment.strip() or "Untitled Assignment",
                "grade": grade,
                "mistakes": mistakes,
                "words": words,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            st.session_state.results.append(result)

            st.success("Assignment checked.")
            a, b, c = st.columns(3)
            a.metric("Estimated grade", f"{grade}/100")
            b.metric("Word count", words)
            c.metric("Issues flagged", len(mistakes))

            st.subheader("Mistakes and corrections")
            if mistakes:
                for i, mistake in enumerate(mistakes, 1):
                    with st.expander(f"{i}. {mistake['type']}: {mistake['original']}"):
                        st.write(f"**Suggested correction:** {mistake['correction']}")
                        st.write(f"**Why:** {mistake['explanation']}")
            else:
                st.info("No issues from the current rule set were detected. This does not guarantee the response is error-free.")

            st.subheader("Student feedback")
            if not mistakes:
                st.write("Good work. Keep checking your grammar, accents, and punctuation before submitting.")
            elif len(mistakes) <= 2:
                st.write("Good start. Review the flagged corrections and revise your response before submitting.")
            else:
                st.write("There are several areas to revise. Focus on the flagged grammar and punctuation issues, then proofread the full response again.")

            if rubric:
                st.caption(f"Teacher rubric entered: {rubric}")

elif page == "Class Results":
    st.header("Class Results")
    results = st.session_state.results
    if not results:
        st.info("No assignments have been checked yet. Results will appear here after you check student work.")
    else:
        avg = sum(r["grade"] for r in results) / len(results)
        total_mistakes = sum(len(r["mistakes"]) for r in results)
        a, b, c = st.columns(3)
        a.metric("Assignments checked", len(results))
        b.metric("Average estimated grade", f"{avg:.1f}")
        c.metric("Issues flagged", total_mistakes)

        st.subheader("Student results")
        for r in results:
            st.write(f"**{r['student']}** · {r['assignment']} · **{r['grade']}/100** · {r['words']} words · {len(r['mistakes'])} issues")

        st.subheader("Most common issue types")
        counts = Counter(m["type"] for r in results for m in r["mistakes"])
        if counts:
            for issue_type, count in counts.most_common():
                st.write(f"- **{issue_type}:** {count}")
        else:
            st.write("No issues have been flagged.")

        st.subheader("Teacher takeaway")
        if counts:
            top_issue = counts.most_common(1)[0][0]
            st.write(f"The most frequently flagged area is **{top_issue}**. This can help identify a topic worth reviewing with the class.")
        else:
            st.write("The checked responses currently show no flagged issues from the assistant's rule set.")

        if st.button("Clear session results"):
            st.session_state.results = []
            st.rerun()

st.divider()
st.caption("Prototype: automated flags are suggestions, not a replacement for teacher judgment. The current version uses rule-based checks rather than a full AI language model.")
