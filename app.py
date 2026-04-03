import streamlit as st
from groq import Groq
import json

# --- CONFIG & HUD STYLING ---
st.set_page_config(page_title="Eve: Modern DM", layout="wide")

st.markdown("""
    <style>
    .status-board {
        background-color: #1e1e1e; border: 2px solid #3e3e3e; padding: 15px;
        border-radius: 10px; color: #00ffcc; font-family: 'Courier New', Courier, monospace;
        margin-bottom: 20px; position: sticky; top: 0; z-index: 999;
    }
    .stChatMessage { border-radius: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- INITIALIZE SESSION STATE ---
if "game_started" not in st.session_state:
    st.session_state.game_started = False
if "phase" not in st.session_state:
    st.session_state.phase = "Session 0" # Phases: Session 0 -> Character Creation -> Active Campaign
if "messages" not in st.session_state:
    st.session_state.messages = []
if "party" not in st.session_state:
    st.session_state.party = {}
if "location" not in st.session_state:
    st.session_state.location = "The Neon Plaza"

# --- SECURE GROQ CLIENT ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- SIDEBAR: CAMPAIGN DATA ---
with st.sidebar:
    st.title("🏙️ New Cyre Ops")
    st.write(f"**Current Phase:** {st.session_state.phase}")
    
    with st.expander("Register Agents", expanded=(not st.session_state.game_started)):
        p_name = st.text_input("Name")
        p_concept = st.text_area("Concept")
        if st.button("Add to Game"):
            if p_name:
                st.session_state.party[p_name] = {"concept": p_concept, "stats": "Pending..."}
                st.success(f"{p_name} registered.")

    st.divider()
    # Save/Load System
    campaign_data = {"party": st.session_state.party, "messages": st.session_state.messages, "game_started": st.session_state.game_started, "phase": st.session_state.phase}
    st.download_button("💾 Download Save", json.dumps(campaign_data), file_name="new_cyre_master.json")
    
    uploaded_file = st.file_uploader("📂 Upload Save", type="json")
    if uploaded_file:
        data = json.load(uploaded_file)
        st.session_state.update(data)
        st.rerun()

    if st.button("🗑️ Full Reset"):
        st.session_state.clear()
        st.rerun()

# --- THE STATUS BOARD (HUD) ---
if st.session_state.game_started:
    st.markdown(f"""
    <div class="status-board">
        <b>📍 LOCATION:</b> {st.session_state.location} | 
        <b>🎭 PHASE:</b> {st.session_state.phase} <br>
        <b>👥 PARTY:</b> {', '.join(st.session_state.party.keys())}
    </div>
    """, unsafe_allow_html=True)

# --- MAIN LOGIC ---
if not st.session_state.game_started:
    st.header("✨ Project: New Cyre")
    st.info("Register Brad, Corey, Melissa, Sarah, and Liz in the sidebar, then hit Initiate.")
    
    if st.button("🚀 INITIATE SESSION 0"):
        if not st.session_state.party:
            st.error("Register the crew first!")
        else:
            with st.spinner("Eve is coming online..."):
                party_info = "\n".join([f"{n}: {d['concept']}" for n, d in st.session_state.party.items()])
                sys_prompt = f"""You are Eve, the DM. 
                Setting: New Cyre Modern Fantasy. 
                Party: {party_info}. 
                Phase: Session 0.
                PROTOCOL: 
                1. Narrative: Give 3 paragraphs of history.
                2. Setup: Start the 'Character Interview' process. 
                3. Structure: Address ONE player at a time (e.g. '@Corey: ...'). Ask them for their Class/Race choice.
                4. Wait for player input before moving to the next person."""
                
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "system", "content": sys_prompt}],
                    temperature=0.8
                )
                st.session_state.messages.append({"role": "system", "content": sys_prompt})
                st.session_state.messages.append({"role": "assistant", "content": response.choices[0].message.content})
                st.session_state.game_started = True
                st.rerun()

else:
    # --- PHASE CONTROLLER ---
    if st.session_state.phase == "Session 0":
        if st.button("✅ Start Character Creation"):
            st.session_state.phase = "Character Creation"
            st.session_state.messages.append({"role": "system", "content": "Update Phase: Character Creation. Eve, provide D&D 5e Stat Blocks for each player as they finalize their concepts."})
            st.rerun()
    elif st.session_state.phase == "Character Creation":
        if st.button("⚔️ START MAIN CAMPAIGN"):
            st.session_state.phase = "Active Campaign"
            st.session_state.messages.append({"role": "system", "content": "Update Phase: Active Campaign. Begin the first quest. Manage initiative and rolls as needed."})
            st.rerun()

    # --- CHAT DISPLAY ---
    for msg in st.session_state.messages:
        if msg["role"] != "system":
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # --- INPUT ---
    user_input = st.chat_input("Speak or type your action...")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=st.session_state.messages,
                temperature=0.7
            )
            answer = response.choices[0].message.content
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.rerun()
              
