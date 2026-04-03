import streamlit as st
from groq import Groq
import json

# --- CONFIG ---
st.set_page_config(page_title="Eve: AI DM", layout="wide")

# --- INITIALIZE SESSION STATE ---
if "game_started" not in st.session_state:
    st.session_state.game_started = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "party" not in st.session_state:
    st.session_state.party = {}

# --- SECURE GROQ CLIENT ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- SIDEBAR: PERSISTENCE & PARTY ---
with st.sidebar:
    st.title("📜 Campaign Management")
    
    # Party Setup
    st.subheader("The Adventurers")
    new_player = st.text_input("Add Player Name")
    new_char = st.text_area("Character Details (Class, Race, Key Stats)")
    if st.button("Add to Party"):
        st.session_state.party[new_player] = new_char
        st.success(f"{new_player} joined!")

    st.write("Current Party:", st.session_state.party)

    st.divider()
    
    # Save/Load Feature (Crucial for free hosting!)
    st.subheader("Save/Load Game")
    campaign_data = {
        "party": st.session_state.party,
        "messages": st.session_state.messages,
        "game_started": st.session_state.game_started
    }
    st.download_button("Download Campaign Save", json.dumps(campaign_data), file_name="eve_save.json")
    
    uploaded_file = st.file_opener("Upload Campaign Save", type="json")
    if uploaded_file:
        data = json.load(uploaded_file)
        st.session_state.party = data["party"]
        st.session_state.messages = data["messages"]
        st.session_state.game_started = data["game_started"]
        st.rerun()

# --- MAIN SCREEN ---
if not st.session_state.game_started:
    # SESSION 0 SCREEN
    st.header("Welcome to Session 0")
    st.write("Before we begin, ensure the party is listed in the sidebar.")
    campaign_setting = st.text_input("Campaign Setting (e.g. Curse of Strahd, Eberron, or a Custom World)")
    
    if st.button("Start Adventure"):
        if not st.session_state.party:
            st.warning("You need at least one player to start!")
        else:
            # Create the 'Master Instruction' for Eve
            party_desc = "\n".join([f"{p}: {c}" for p, c in st.session_state.party.items()])
            initial_prompt = f"System: You are Eve, the DM. Setting: {campaign_setting}. Party: {party_desc}. Start the adventure with a vivid opening narration."
            
            st.session_state.messages.append({"role": "system", "content": initial_prompt})
            st.session_state.game_started = True
            st.rerun()

else:
    # ADVENTURE MODE (CHAT)
    for msg in st.session_state.messages:
        if msg["role"] != "system":
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    if prompt := st.chat_input("Corey says... / Melissa casts..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=st.session_state.messages,
                temperature=0.8
            )
            answer = response.choices[0].message.content
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
