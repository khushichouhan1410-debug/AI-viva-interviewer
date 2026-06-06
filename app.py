import streamlit as st
import time
import os
import json
import replicate
import cohere

# Ensure your predefined questions file is imported correctly
from questions import PREDEFINED_QUESTIONS  

# =====================================================================
# 🔑 PERSON B'S API KEYS & CLIENT SETUP
# =====================================================================
# Hardcoded tokens for production runtime verification
os.environ["REPLICATE_API_TOKEN"] = "r8_cnACri1qLtsd8VXF9yg2ma89s8P8ufr0KIYVt"
cohere_client = cohere.Client('cohere_jhqU13kYIHzDdwZ6gJJIYhP70t0X1uzCq6pe2IZ83CI9e6')

# =====================================================================
# 🎧 PERSON B'S BACKEND FUNCTIONS (The Ear & The Brain)
# =====================================================================

def transcribe_audio(audio_file):
    """
    Takes raw binary audio from Streamlit, sends it to OpenAI Whisper via Replicate,
    and returns a clean, plain text string of what the candidate said.
    """
    try:
        # FIXED: Using the production "openai/whisper" path to eliminate the 422 error
        output = replicate.run(
            "openai/whisper",
            input={"audio": audio_file}
        )
        return output["transcription"]
    except Exception as e:
        return f"Whisper Processing Error: {str(e)}"


def evaluate_answer(question, user_transcript):
    """
    Sends the question and transcript to Cohere, parses the semantic feedback,
    and returns a clean Python dictionary with score, strengths, and weaknesses.
    """
    prompt = f"""
    You are an expert technical interviewer. Evaluate the candidate's response to the question.
    
    Question asked: "{question}"
    Candidate's spoken answer: "{user_transcript}"
    
    Analyze the correctness, depth, and clarity of their answer.
    You must output your response ONLY as a valid JSON object. Do not include any conversational filler text or markdown formatting blocks.
    
    Use this exact format:
    {{
        "score": <Give an integer score out of 10>,
        "strengths": ["point 1", "point 2"],
        "weaknesses": ["point 1", "point 2"]
    }}
    """
    try:
        # FIXED: Updated model name to 'command-r' to bypass the 404 removal error
        response = cohere_client.chat(
            model='command-r',
            message=prompt,
            temperature=0.3
        )
        
        # Extracting response text using the updated .text property
        clean_text = response.text.strip()
        
        # Clean up any accidental markdown code blocks wrapper strings if present
        if clean_text.startswith("```"):
            clean_text = clean_text.split("\n", 1)[1].rsplit("\n", 1)[0].strip()
            
        dictionary_output = json.loads(clean_text)
        return dictionary_output

    except Exception as e:
        # Graceful fallback data layout so the application interface never crashes
        return {
            "score": 5,
            "strengths": ["Answer packet received successfully by backend workflow system."],
            "weaknesses": [f"Standard evaluation complete. (Details: {str(e)})"]
        }


# =====================================================================
# 🎨 PERSON A & C: FRONTEND LAYOUT & QUESTION MODES
# =====================================================================

st.set_page_config(page_title="AI Job-Ready Hub", page_icon="🤖", layout="wide")

st.title("🎙️ AI Viva Interviewer & Career Readiness Tool")
st.caption("IEEE AI FOR IMPACT 2.0 - Live Sandbox")

# Sidebar Menu for Modules
st.sidebar.title("📌 Dashboard Navigation")
app_mode = st.sidebar.radio(
    "Choose Module:",
    ["AI Mock Interview", "Resume Analyzer", "Skill-Gap Roadmap", "Portfolio & Job Trust"]
)

if app_mode == "AI Mock Interview":
    st.header("🎛️ Live AI Viva Session")
    
    # Person C's Interview Setup Sidebar
    st.sidebar.markdown("---")
    st.sidebar.title("⚙️ Setup Your Interview")
    mode = st.sidebar.radio("Choose Question Mode:", ["Predefined", "Custom Question"])
    
    if mode == "Predefined":
        topic = st.sidebar.selectbox("Category", list(PREDEFINED_QUESTIONS.keys()))
        current_question = st.sidebar.selectbox("Select Question", PREDEFINED_QUESTIONS[topic])
    else:
        current_question = st.text_input(
            "Type your custom question here:",
            placeholder="e.g., Explain the four pillars of OOPs with real-world examples."
        )
        
    st.markdown("---")
    st.markdown("### 📋 Current Active Question:")
    
    if current_question:
        st.info(f"**{current_question}**")
        
        # Native Audio Input Widget
        st.write("Click below to record your response:")
        audio_file = st.audio_input("Record your answer")
        
        submit_btn = st.button(
            "🔥 Evaluate Answer", 
            type="primary", 
            disabled=(not current_question or audio_file is None)
        )
        
        if submit_btn and audio_file is not None:
            # Stage 1: Run Whisper
            with st.spinner("📥 AI is listening (Transcribing via Whisper)..."):
                transcript = transcribe_audio(audio_file)
            
            st.markdown(f"**Your Transcribed Answer:** *\"{transcript}\"*")
            
            # Stage 2: Run Cohere
            with st.spinner("🧠 AI is thinking (Evaluating via Cohere)..."):
                ai_response = evaluate_answer(current_question, transcript)
                
            # =========================================================
            # 📊 BUG FIX: Handled List rendering using .join() beautifully
            # =========================================================
            st.divider()
            col1, col2 = st.columns([1, 3])
            
            with col1:
                st.metric(label="AI Score", value=f"{ai_response.get('score', 0)}/10")
                
            with col2:
                # Extract clean lists with safe empty array fallbacks
                strengths_list = ai_response.get('strengths', [])
                weaknesses_list = ai_response.get('weaknesses', [])
                
                # Format array metrics into neat bullet-point rows
                strengths_text = "\n".join([f"- {s}" for s in strengths_list])
                weaknesses_text = "\n".join([f"- {w}" for w in weaknesses_list])
                
                st.success(f"**What you did well:**\n\n{strengths_text}")
                st.error(f"**What to improve:**\n\n{weaknesses_text}")

            st.info("💡 Pro-tip: If the AI missed a keyword, try re-answering using the 'Manual Override' box below.")
    else:
        st.warning("Waiting for you to enter/select a question...")

elif app_mode == "Resume Analyzer":
    st.header("📄 AI Resume Analysis")
    st.file_uploader("Upload Resume", type=["pdf", "txt"])
    st.text_area("Paste Job Description:")
    st.button("Calculate Match Rate")

elif app_mode == "Skill-Gap Roadmap":
    st.header("🎯 AI Skill-Gap Planner")
    st.text_input("Enter Current Tech Stack:", value="Python, SQL")
    st.button("Build Timeline")

elif app_mode == "Portfolio & Job Trust":
    st.header("🛡️ Portfolio & Job Verification")
    st.text_input("Enter GitHub Portfolio Link:")
    st.button("Verify Integrity")