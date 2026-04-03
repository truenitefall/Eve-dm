import streamlit as st
from groq import Groq
import json

# --- CONFIG & MOBILE OPTIMIZATION ---
st.set_page_config(page_title="Eve: Modern DM", layout="wide")

st.markdown("""
    <style>
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; }
    .stButton>button { width: 100%; border-radius: 20px; height: 3.5em; font-weight: bold; }
    .stTextArea textarea { font-size: 1.1rem; }
    </style>
    """, unsafe_allow_html=True)

# --- INITIALIZE SESSION STATE ---
if "game_started" not in st.session_state:
    st.session_state.game_started = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "party" not in st.session_state:
    st.session_state.party = {}
if "input_draft" not in st.session_state:
    st.session_state.input_draft = ""

# --- SECURE GROQ CLIENT ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- SIDEBAR: PERSISTENCE ---
with st.sidebar:
    st.title("🏙️ New Cyre Ops")
    
    with st.expander("Register/Edit Agents"):
        p_name = st.text_input("Name")
        p_concept = st.text_area("Concept (e.g. Rogue Hacker)")
        if st.button("Add to Game"):
            st.session_state.party[p_name] = p_concept
            st.success(f"{p_name} registered.")

    st.write("---")
    # Save/Load System
    campaign_data = {"party": st.session_state.party, "messages": st.session_state.messages, "game_started": st.session_state.game_started}
    st.download_button("💾 Save Campaign", json.dumps(campaign_data), file_name="new_cyre_save.json")
    
    uploaded_file = st.file_uploader("📂 Load Save", type="json")
    if uploaded_file:
        data = json.load(uploaded_file)
        st.session_state.party, st.session_state.messages, st.session_state.game_started = data["party"], data["messages"], data["game_started"]
        st.rerun()

# --- MAIN INTERFACE ---
if not st.session_state.game_started:
    st.header("✨ Project: New Cyre")
    st.write("Register the party in the sidebar, then hit the button below. Eve will handle the rest.")
    
    if st.button("🚀 INITIATE SESSION 0"):
        if not st.session_state.party:
            st.warning("Add the players in the sidebar first!")
        else:
            party_list = "\n".join([f"{p}: {c}" for p, c in st.session_state.party.items()])
            eve_instructions = f"""
            System: You are 'Eve', the FULL Dungeon Master.
            Setting: New Cyre (Modern Corporate Fantasy).
            Party: {party_list}
            
            YOUR PROTOCOL:
            1. You are the narrator and referee. Never wait for a 'human' DM.
            2. OPENING: Invent the history of New Cyre and describe the starting mana-bar.
            3. PROMPT: Explicitly ask one player at a time to describe their character's look or vibes.
            4. ACTION: Always end your response with a clear prompt for a specific player or the whole group.
            """
            st.session_state.messages.append({"role": "system", "content": eve_instructions})
            st.session_state.game_started = True
            st.rerun()

else:
    # --- CHAT HISTORY ---
    for msg in st.session_state.messages:
        if msg["role"] != "system":
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # --- THE DRAFTING ZONE (Speech-to-Text friendly) ---
    st.divider()
    st.caption("🎙️ Tap the Mic on your keyboard to speak into the box below. Check the text, then hit 'Send to Eve'.")
    
    # Text area for drafting (easier to see what was said/typed)
    user_draft = st.text_area("Your Action / Dialogue:", value=st.session_state.input_draft, placeholder="e.g. Corey: I try to hack the mana-lock.", key="input_box")

    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("SEND 🎲"):
            if user_draft:
                st.session_state.messages.append({"role": "user", "content": user_draft})
                # Clear the draft
                st.session_state.input_draft = ""
                
                with st.chat_message("assistant"):
                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=st.session_state.messages,
                        temperature=0.8
                    )
                    answer = response.choices[0].message.content
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                st.rerun()
    with col1:
        if st.button("Clear Draft"):
            st.session_state.input_draft = ""
            st.rerun()
          
