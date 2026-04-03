import streamlit as st
from groq import Groq
import json

# --- CONFIG ---
st.set_page_config(page_title="Eve: Modern DM", layout="wide")

st.markdown("""
    <style>
    .status-board {
        background-color: #1a1a2e; border: 2px solid #00d4ff; padding: 15px;
        border-radius: 10px; color: #e0e0e0; font-family: sans-serif;
        margin-bottom: 20px; position: sticky; top: 0; z-index: 999;
    }
    </style>
    """, unsafe_allow_html=True)

# --- INITIALIZE SESSION STATE ---
if "game_started" not in st.session_state:
    st.session_state.game_started = False
if "phase" not in st.session_state:
    st.session_state.phase = "Session 0"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "party" not in st.session_state:
    st.session_state.party = {}

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- SIDEBAR ---
with st.sidebar:
    st.title("🏙️ New Cyre Ops")
    st.write(f"**Current Phase:** {st.session_state.phase}")
    
    with st.expander("Register Agents", expanded=(not st.session_state.game_started)):
        p_name = st.text_input("Name")
        p_concept = st.text_area("Concept")
        if st.button("Add to Game"):
            if p_name:
                st.session_state.party[p_name] = {"concept": p_concept}
                # If game is already live, we send a silent 'ping' to Eve
                if st.session_state.game_started:
                    st.session_state.messages.append({"role": "system", "content": f"System Alert: {p_name} has joined the game. Concept: {p_concept}."})
                st.success(f"{p_name} registered.")

    st.divider()
    campaign_data = {"party": st.session_state.party, "messages": st.session_state.messages, "game_started": st.session_state.game_started, "phase": st.session_state.phase}
    st.download_button("💾 Save Campaign (FOR BRAD)", json.dumps(campaign_data), file_name="new_cyre_save.json")
    
    uploaded_file = st.file_uploader("📂 Load Campaign (FOR BRAD)", type="json")
    if uploaded_file:
        data = json.load(uploaded_file)
        st.session_state.update(data)
        st.rerun()

# --- HUD ---
if st.session_state.game_started:
    st.markdown(f"""<div class="status-board"><b>📍 NEW CYRE</b> | <b>🎭 {st.session_state.phase}</b> | <b>👥 AGENTS:</b> {', '.join(st.session_state.party.keys())}</div>""", unsafe_allow_html=True)

# --- MAIN ENGINE ---
if not st.session_state.game_started:
    st.header("✨ Project: New Cyre")
    if st.button("🚀 INITIATE SESSION 0"):
        if st.session_state.party:
            party_info = "\n".join([f"{n}: {d['concept']}" for n, d in st.session_state.party.items()])
            sys_prompt = f"System: You are Eve, the DM. Setting: New Cyre. Party: {party_info}. Begin Session 0."
            response = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "system", "content": sys_prompt}], temperature=0.8)
            st.session_state.messages.append({"role": "system", "content": sys_prompt})
            st.session_state.messages.append({"role": "assistant", "content": response.choices[0].message.content})
            st.session_state.game_started = True
            st.rerun()
else:
    # Phase Buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.session_state.phase == "Session 0" and st.button("✅ Start Character Creation"):
            st.session_state.phase = "Character Creation"
            st.rerun()
    with col2:
        if st.session_state.phase == "Character Creation" and st.button("⚔️ START CAMPAIGN"):
            st.session_state.phase = "Active Campaign"
            st.rerun()

    # Chat Display
    for msg in st.session_state.messages:
        if msg["role"] != "system":
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # Chat Input
    if user_input := st.chat_input("Speak or type..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"): st.markdown(user_input)
        with st.chat_message("assistant"):
            response = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=st.session_state.messages, temperature=0.7)
            st.markdown(response.choices[0].message.content)
            st.session_state.messages.append({"role": "assistant", "content": response.choices[0].message.content})
            st.rerun()
          
