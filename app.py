import streamlit as st
from groq import Groq
import json

# --- CONFIG & STYLING ---
st.set_page_config(page_title="Eve: Modern DM", layout="wide")

# Custom CSS to make chat bubbles and buttons look better on phones
st.markdown("""
    <style>
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; }
    .stButton>button { width: 100%; border-radius: 20px; height: 3em; }
    </style>
    """, unsafe_allow_html=True)

# --- INITIALIZE SESSION STATE ---
if "game_started" not in st.session_state:
    st.session_state.game_started = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "party" not in st.session_state:
    st.session_state.party = {}

# --- SECURE GROQ CLIENT ---
if "GROQ_API_KEY" in st.secrets:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
else:
    st.error("Missing API Key! Please add GROQ_API_KEY to your Streamlit Secrets.")
    st.stop()

# --- SIDEBAR: CAMPAIGN TOOLS ---
with st.sidebar:
    st.title("🏙️ New Cyre Ops")
    
    # Party Management
    st.subheader("The Crew")
    with st.expander("Add/Edit Players"):
        new_player = st.text_input("Player Name (e.g. Corey)")
        new_char = st.text_area("Concept (e.g. Elven Hacker, Orc Bodyguard)")
        if st.button("Register Agent"):
            if new_player:
                st.session_state.party[new_player] = new_char
                st.success(f"{new_player} is online.")

    if st.session_state.party:
        for p, c in st.session_state.party.items():
            st.write(f"**{p}**: {c}")
    
    st.divider()
    
    # Save/Load for long-term play
    st.subheader("Data Recovery")
    campaign_data = {
        "party": st.session_state.party,
        "messages": st.session_state.messages,
        "game_started": st.session_state.game_started
    }
    st.download_button("💾 Save Campaign File", json.dumps(campaign_data), file_name="new_cyre_save.json")
    
    uploaded_file = st.file_uploader("📂 Load Campaign File", type="json")
    if uploaded_file:
        data = json.load(uploaded_file)
        st.session_state.party = data.get("party", {})
        st.session_state.messages = data.get("messages", [])
        st.session_state.game_started = data.get("game_started", False)
        st.rerun()

# --- MAIN INTERFACE ---
if not st.session_state.game_started:
    # SESSION 0 SCREEN
    st.header("✨ Project: New Cyre")
    st.write("Welcome to the Modern Arcanum. Please register Corey, Melissa, Sarah, and Liz in the sidebar.")
    
    setting_focus = st.text_input("Campaign Theme", value="Modern Corporate Fantasy / Noir Intrigue")
    
    if st.button("🚀 INITIATE SESSION 0"):
        if not st.session_state.party:
            st.warning("No players registered! Add your friends in the sidebar first.")
        else:
            party_list = "\n".join([f"{p}: {c}" for p, c in st.session_state.party.items()])
            
            # THE BRAIN: System Instructions for Eve
            eve_instructions = f"""
            You are 'Eve', the Dungeon Master for a Modern High Fantasy campaign set in 'New Cyre'.
            World Logic: Magic is technology. Dragons are CEOs. Dungeons are server farms.
            Players: {party_list}
            Theme: {setting_focus}

            YOUR FIRST TASK:
            1. Invent a vivid, 3-paragraph history of New Cyre. Explain how the 'Old World' became this modern magical dystopia.
            2. Introduce the current scene: The players are meeting in a high-end mana-bar or corporate plaza.
            3. INTERVIEW MODE: Stop and ask Corey, Melissa, Sarah, and Liz one question each to help them build their 5e stats based on their concepts. 
            4. Be encouraging, witty, and immersive. Use D&D 5e (2014) rules.
            """
            st.session_state.messages.append({"role": "system", "content": eve_instructions})
            st.session_state.game_started = True
            st.rerun()

else:
    # ADVENTURE MODE
    st.caption("📱 Tip: Use your phone's microphone icon on the keyboard to speak your actions!")
    
    # Display Chat History
    for msg in st.session_state.messages:
        if msg["role"] != "system":
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # Input Handling
    if prompt := st.chat_input("Speak your action..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                # Using the Llama 3.3 70B for the highest quality DMing
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=st.session_state.messages,
                    temperature=0.8,
                    max_tokens=1500
                )
                answer = response.choices[0].message.content
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                st.error(f"Signal Lost: {e}")
              
