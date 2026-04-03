import streamlit as st
from groq import Groq
import json

# --- CONFIG & HUD STYLING ---
st.set_page_config(page_title="Eve: Modern DM", layout="wide")

st.markdown("""
    <style>
    .status-board {
        background-color: #1a1a2e; border: 2px solid #00d4ff; padding: 15px;
        border-radius: 10px; color: #e0e0e0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        margin-bottom: 20px; position: sticky; top: 0; z-index: 999; box-shadow: 0px 4px 10px rgba(0, 212, 255, 0.3);
    }
    .stChatMessage { border-radius: 15px; border-left: 5px solid #00d4ff; }
    .stButton>button { background-color: #0f3460; color: white; border: 1px solid #00d4ff; }
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
if "location" not in st.session_state:
    st.session_state.location = "New Cyre: The Neon Plaza"

# --- SECURE GROQ CLIENT ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- SIDEBAR ---
with st.sidebar:
    st.title("🏙️ New Cyre Ops")
    st.write(f"**Current Phase:** {st.session_state.phase}")
    
    with st.expander("Register Agents", expanded=(not st.session_state.game_started)):
        p_name = st.text_input("Name")
        p_concept = st.text_area("Concept (e.g. Corporate Spy)")
        if st.button("Add to Game"):
            if p_name:
                st.session_state.party[p_name] = {"concept": p_concept}
                st.success(f"{p_name} registered.")

    st.divider()
    campaign_data = {"party": st.session_state.party, "messages": st.session_state.messages, "game_started": st.session_state.game_started, "phase": st.session_state.phase}
    st.download_button("💾 Download Save", json.dumps(campaign_data), file_name="new_cyre_master.json")
    
    uploaded_file = st.file_uploader("📂 Upload Save", type="json")
    if uploaded_file:
        data = json.load(uploaded_file)
        st.session_state.update(data)
        st.rerun()

# --- THE STATUS BOARD (HUD) ---
if st.session_state.game_started:
    st.markdown(f"""
    <div class="status-board">
        <b>📍 LOCATION:</b> {st.session_state.location} | 
        <b>🎭 PHASE:</b> {st.session_state.phase} <br>
        <b>👥 AGENTS:</b> {', '.join(st.session_state.party.keys())}
    </div>
    """, unsafe_allow_html=True)

# --- MAIN LOGIC ---
if not st.session_state.game_started:
    st.header("✨ Project: New Cyre")
    st.info("Register the crew in the sidebar, then hit Initiate.")
    
    if st.button("🚀 INITIATE SESSION 0"):
        if not st.session_state.party:
            st.error("Register at least one agent (you!) first.")
        else:
            with st.spinner("Eve is constructing New Cyre..."):
                party_info = "\n".join([f"{n}: {d['concept']}" for n, d in st.session_state.party.items()])
                sys_prompt = f"""You are Eve, the DM. Setting: New Cyre (Modern Fantasy). Party: {party_info}. 
                Phase: Session 0. Provide history and a starting scene. Prompt players to discuss their vibes."""
                
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
            creation_prompt = """
            Update Phase: Character Creation.
            Eve, present the players with a list of 'Modern Archetypes' based on 5e Classes. 
            Example Translations:
            - Fighter -> Urban Soldier / Street Samurai
            - Rogue -> Hacker / Infiltrator
            - Wizard -> Code-Weaver / Arcano-Scientist
            - Cleric -> Field Medic / Bio-Aura Specialist
            - Druid -> Urban Shaman / Beast-Machine Hybrid
            - Artificer -> Tech-Engineer / Gadgeteer
            
            Prompt the players to choose one or suggest their own. Be ready to generate full 2014 Stat Blocks once they choose.
            """
            st.session_state.messages.append({"role": "system", "content": creation_prompt})
            
            # Immediately get Eve's list
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=st.session_state.messages,
                temperature=0.7
            )
            st.session_state.messages.append({"role": "assistant", "content": response.choices[0].message.content})
            st.rerun()
            
    elif st.session_state.phase == "Character Creation":
        if st.button("⚔️ START MAIN CAMPAIGN"):
            st.session_state.phase = "Active Campaign"
            st.session_state.messages.append({"role": "system", "content": "Update Phase: Active Campaign. Begin the adventure!"})
            st.rerun()

    # --- CHAT DISPLAY ---
    for msg in st.session_state.messages:
        if msg["role"] != "system":
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # --- INPUT ---
    user_input = st.chat_input("Input action or dialogue...")
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
          
