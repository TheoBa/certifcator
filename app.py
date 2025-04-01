import streamlit as st
import json
import os
from pathlib import Path
import random
from datetime import datetime

# Set page config
st.set_page_config(
    page_title="QCM Test App",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        margin: 0.5rem 0;
        padding: 0.5rem;
        border-radius: 0.5rem;
        background-color: #4CAF50;
        color: white;
        border: none;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #45a049;
        transform: translateY(-2px);
    }
    .test-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 1rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .mode-button {
        background-color: #2196F3 !important;
    }
    .mode-button:hover {
        background-color: #1976D2 !important;
    }
    .score-display {
        position: fixed;
        top: 5rem;
        right: 2rem;
        background-color: #4CAF50;
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        z-index: 1000;
        min-width: 150px;
        text-align: center;
    }
    .question-card {
        background-color: #e3f2fd;
        padding: 1.5rem;
        border-radius: 1rem;
        margin: 1rem 0;
        text-align: left;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .answer-button {
        text-align: left !important;
        padding-left: 1rem !important;
    }
    .correct-answer {
        background-color: #c8e6c9 !important;
        border: 2px solid #4CAF50 !important;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'current_test' not in st.session_state:
    st.session_state.current_test = None
if 'test_mode' not in st.session_state:
    st.session_state.test_mode = None
if 'current_question' not in st.session_state:
    st.session_state.current_question = 0
if 'answers' not in st.session_state:
    st.session_state.answers = {}  # Changed to dictionary
if 'test_history' not in st.session_state:
    st.session_state.test_history = []
if 'shuffled_questions' not in st.session_state:
    st.session_state.shuffled_questions = None
if 'show_answer' not in st.session_state:
    st.session_state.show_answer = False
if 'answered' not in st.session_state:
    st.session_state.answered = False
if 'navigation' not in st.session_state:
    st.session_state.navigation = None

def load_available_tests():
    """Load all available tests from the questions directory."""
    questions_dir = Path("questions")
    tests = {}
    for file in questions_dir.glob("*.json"):
        with open(file, 'r') as f:
            tests[file.stem] = json.load(f)
    return tests

def save_test_result(test_name, mode, answers, score):
    """Save test result to a JSON file."""
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    
    result = {
        "test_name": test_name,
        "mode": mode,
        "timestamp": datetime.now().isoformat(),
        "answers": answers,
        "score": score
    }
    
    # Load existing results
    results_file = results_dir / "test_history.json"
    if results_file.exists():
        with open(results_file, 'r') as f:
            history = json.load(f)
    else:
        history = []
    
    # Append new result
    history.append(result)
    
    # Save updated history
    with open(results_file, 'w') as f:
        json.dump(history, f, indent=2)

def load_test_history():
    """Load test history from the results file."""
    results_file = Path("results") / "test_history.json"
    if results_file.exists():
        with open(results_file, 'r') as f:
            return json.load(f)
    return []

def calculate_score():
    """Calculate the current score based on answered questions."""
    if not st.session_state.answers:
        return 0
    correct_answers = sum(1 for answer in st.session_state.answers.values() 
                         if answer["selected"] == answer["correct"])
    return (correct_answers / len(st.session_state.answers)) * 100

def main():
    # Sidebar
    with st.sidebar:
        st.title("📝 QCM Test App")
        st.markdown("---")
        st.markdown("### Navigation")
        if st.button("🏠 Home", key="home"):
            st.session_state.current_test = None
            st.session_state.test_mode = None
            st.session_state.current_question = 0
            st.session_state.answers = {}
            st.session_state.shuffled_questions = None
            st.session_state.show_answer = False
            st.session_state.answered = False
            st.session_state.navigation = None
            st.rerun()
        
        # Test controls in learning mode
        if st.session_state.test_mode == "learning":
            st.markdown("### Test Controls")
            st.session_state.show_answer = st.toggle("Show Answer", key="show_answer_toggle")
            
            # Navigation buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("⬅️ Previous", key="prev_question", 
                           disabled=st.session_state.current_question == 0):
                    st.session_state.navigation = "prev"
                    st.session_state.show_answer = False
                    st.session_state.answered = False
                    st.rerun()
            
            with col2:
                if st.button("Next ➡️", key="next_question", 
                           disabled=st.session_state.current_question >= len(st.session_state.shuffled_questions) - 1):
                    st.session_state.navigation = "next"
                    st.session_state.show_answer = False
                    st.session_state.answered = False
                    st.rerun()
        
        st.markdown("### Test History")
        history = load_test_history()
        if history:
            for result in history[-5:]:  # Show last 5 attempts
                st.markdown(f"""
                    <div style='background-color: #f0f2f6; padding: 0.5rem; border-radius: 0.5rem; margin: 0.5rem 0;'>
                        <strong>{result['test_name']}</strong><br>
                        Mode: {result['mode']}<br>
                        Score: {result['score']:.1f}%<br>
                        Date: {datetime.fromisoformat(result['timestamp']).strftime('%Y-%m-%d %H:%M')}
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No test history yet")
    
    # Main content
    st.title("Welcome to QCM Test App")
    st.markdown("---")
    
    # Load available tests
    tests = load_available_tests()
    
    # Test selection page
    if st.session_state.current_test is None:
        st.header("Available Tests")
        st.markdown("Select a test to begin:")
        
        # Display available tests in a grid
        cols = st.columns(2)
        for idx, test_name in enumerate(tests.keys()):
            with cols[idx % 2]:
                st.markdown(f"""
                    <div class='test-card'>
                        <h3>{test_name}</h3>
                        <p>Number of questions: {len(tests[test_name])}</p>
                    </div>
                """, unsafe_allow_html=True)
                if st.button("Start Test", key=f"test_{test_name}"):
                    st.session_state.current_test = test_name
                    st.rerun()
    
    # Test mode selection
    elif st.session_state.test_mode is None:
        st.header(f"Select Mode for {st.session_state.current_test}")
        st.markdown("Choose how you want to take the test:")
        
        # Mode selection with better styling
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Learning Mode")
            st.markdown("""
                - Get immediate feedback on your answers
                - See correct answers after each question
                - Track your progress in real-time
                - Perfect for practice and learning
            """)
            if st.button("Start Learning Mode", key="learning", help="Start the test in learning mode"):
                st.session_state.test_mode = "learning"
                st.session_state.current_question = 0
                st.session_state.answers = {}
                # Initialize shuffled questions when starting the test
                questions = list(tests[st.session_state.current_test].items())
                random.shuffle(questions)
                st.session_state.shuffled_questions = questions
                st.rerun()
        
        with col2:
            st.markdown("### Test Mode")
            st.markdown("""
                - No feedback until the end
                - Simulates real exam conditions
                - Final score revealed at completion
                - Best for self-assessment
            """)
            if st.button("Start Test Mode", key="test", help="Start the test in exam mode"):
                st.session_state.test_mode = "test"
                st.session_state.current_question = 0
                st.session_state.answers = {}
                # Initialize shuffled questions when starting the test
                questions = list(tests[st.session_state.current_test].items())
                random.shuffle(questions)
                st.session_state.shuffled_questions = questions
                st.rerun()
    
    # Test page
    else:
        display_test(tests[st.session_state.current_test])

def display_test(test_data):
    """Display the current question and handle user interaction."""
    # Handle navigation
    if st.session_state.navigation == "prev":
        st.session_state.current_question = max(0, st.session_state.current_question - 1)
        st.session_state.navigation = None
        st.session_state.show_answer = False
        st.session_state.answered = False
        st.rerun()
    elif st.session_state.navigation == "next":
        st.session_state.current_question = min(len(st.session_state.shuffled_questions) - 1, 
                                              st.session_state.current_question + 1)
        st.session_state.navigation = None
        st.session_state.show_answer = False
        st.session_state.answered = False
        st.rerun()
    
    if st.session_state.current_question < len(st.session_state.shuffled_questions):
        question_num, question_data = st.session_state.shuffled_questions[st.session_state.current_question]
        
        # Progress bar
        progress = (st.session_state.current_question + 1) / len(st.session_state.shuffled_questions)
        st.progress(progress)
        
        # Display current score in learning mode
        if st.session_state.test_mode == "learning" and st.session_state.answers:
            score = calculate_score()
            st.markdown(f"""
                <div class='score-display'>
                    <h4>Current Score: {score:.1f}%</h4>
                </div>
            """, unsafe_allow_html=True)
        
        # Question display with left alignment
        st.markdown(f"""
            <div class='question-card'>
                <h3 style='text-align: left;'>Question {st.session_state.current_question + 1}/{len(st.session_state.shuffled_questions)}</h3>
                <p style='text-align: left;'>{question_data["question"]}</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Display answer options with letters and left alignment
        for option in ["A", "B", "C", "D", "E"]:
            answer_text = f"{option}. {question_data[option]}"
            
            # Check if this is the correct answer and should be highlighted
            button_class = "correct-answer" if (st.session_state.test_mode == "learning" and 
                                              st.session_state.show_answer and 
                                              option == question_data["correct_answer"]) else ""
            
            # Check if this question was already answered
            is_selected = (st.session_state.current_question in st.session_state.answers and 
                         st.session_state.answers[st.session_state.current_question]["selected"] == option)
            
            if st.button(answer_text, key=f"option_{option}", help="Click to select this answer", 
                        type="primary" if button_class or is_selected else "secondary"):
                
                # Update or add the answer for this question
                st.session_state.answers[st.session_state.current_question] = {
                    "question": question_data["question"],
                    "selected": option,
                    "correct": question_data["correct_answer"]
                }
                
                # In learning mode, show feedback
                if st.session_state.test_mode == "learning":
                    st.session_state.answered = True
                    if option == question_data["correct_answer"]:
                        st.success("Correct! 🎉")
                    else:
                        st.error(f"Wrong! The correct answer is {question_data['correct_answer']}")
                    
                    # Show current score
                    score = calculate_score()
                    st.markdown(f"""
                        <div style='background-color: #e8f5e9; padding: 1rem; border-radius: 0.5rem; margin: 1rem 0;'>
                            <h4>Current Score: {score:.1f}%</h4>
                        </div>
                    """, unsafe_allow_html=True)
                
                # Move to next question if not at the end
                if st.session_state.current_question < len(st.session_state.shuffled_questions) - 1:
                    st.session_state.current_question += 1
                    st.session_state.show_answer = False
                    st.session_state.answered = False
                    st.rerun()
    
    # Test completed
    else:
        # Calculate final score
        score = calculate_score()
        
        # Convert answers dict to list for saving
        answers_list = [
            {
                "question": answer["question"],
                "selected": answer["selected"],
                "correct": answer["correct"]
            }
            for answer in st.session_state.answers.values()
        ]
        
        # Save result
        save_test_result(
            st.session_state.current_test,
            st.session_state.test_mode,
            answers_list,
            score
        )
        
        # Display results with better styling
        st.markdown("""
            <div style='background-color: #e8f5e9; padding: 2rem; border-radius: 1rem; margin: 1rem 0;'>
                <h2>🎉 Test Completed! 🎉</h2>
                <h3>Final Score: {:.1f}%</h3>
            </div>
        """.format(score), unsafe_allow_html=True)
        
        # Show detailed results
        st.subheader("Detailed Results")
        for i, answer in enumerate(answers_list):
            st.markdown(f"""
                <div style='background-color: {'#e8f5e9' if answer['selected'] == answer['correct'] else '#ffebee'}; 
                            padding: 1rem; border-radius: 0.5rem; margin: 0.5rem 0;'>
                    <h4>Question {i+1}</h4>
                    <p>Your answer: {answer['selected']}</p>
                    <p>Correct answer: {answer['correct']}</p>
                    <p>{'✅ Correct!' if answer['selected'] == answer['correct'] else '❌ Wrong!'}</p>
                </div>
            """, unsafe_allow_html=True)
        
        # Reset session state
        st.session_state.current_test = None
        st.session_state.test_mode = None
        st.session_state.current_question = 0
        st.session_state.answers = {}  # Reset to empty dictionary
        st.session_state.shuffled_questions = None
        st.session_state.show_answer = False
        st.session_state.answered = False
        st.session_state.navigation = None
        
        if st.button("Take Another Test", key="another_test"):
            st.rerun()

if __name__ == "__main__":
    main()
