import streamlit as st
from groq import Groq
import json
import requests
import urllib.parse
import re

# --- CONFIG & MOBILE VISUALS ---
st.set_page_config(page_title="Eve: Modern DM", layout="wide")

# Custom CSS for Cyberpunk UI, Sticky HUD, and fixed Chatbot spacing
st.markdown("""
    <style>
    .status-board {
        background-color: #1a1a2e; border: 2px solid #00d4ff; padding: 15px;
        border-radius: 10px; color: #e0e0e0; font-family: sans-serif;
        margin-bottom: 20px; position: sticky; top: 0; z-index: 999;
    }
    .stChatMessage { border-radius: 15px; border-left: 5px solid #00d4ff; }
    .stButton>button { background-color: #0f3460; color: white; border: 1px solid #00d4ff; }
    .eve-visual { border-radius: 10px; border: 2px solid #00d4ff; box-shadow: 0px 4px 10px rgba(0, 212, 255, 0.4); }
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
# Initialize the image_url to show a default cyberpunk placeholder
if "current_image_url" not in st.session_state:
    st.session_state.current_image_url = "https://pollinations.ai/p/a%20modern%20cyberpunk%20cityscape%20with%20magical%20mana-streams%20flowing%20between%20buildings"

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- SIDEBAR: Ops, Saves, and VISUAL FEED ---
with st.sidebar:
    st.title("🏙️ New Cyre Ops")
    st.write(f"**Current Phase:** {st.session_state.phase}")
    
    with st.expander("Register Agents", expanded=(not st.session_state.game_started)):
        p_name = st.text_input("Name")
        p_concept = st.text_area("Concept (e.g. Corporate Spy)")
        if st.button("Add to Game"):
            if p_name:
                st.session_state.party[p_name] = {"concept": p_concept}
                # Silent notification to Eve
                if st.session_state.game_started:
                    st.session_state.messages.append({"role": "system", "content": f"System Alert: {p_name} has joined the game. Concept: {p_concept}."})
                st.success(f"{p_name} registered.")

    st.divider()
    
    # --- VISUAL FEED SECTION ---
    st.subheader("📡 Visual Feed")
    st.image(st.session_state.current_image_url, caption="Eve's Construct", use_container_width=True, class_='eve-visual')
    if st.button("Manual Regenerate Image"):
        # We find the last prompt in the system messages to regenerate
        img_prompts = [msg['content'] for msg in st.session_state.messages if 'IMAGE-PROMPT:' in msg['content']]
        if img_prompts:
            raw_prompt = img_prompts[-1].split("IMAGE-PROMPT:")[-1].strip()
            new_url = f"https://pollinations.ai/p/{urllib.parse.quote(raw_prompt)}"
            st.session_state.current_image_url = new_url
            st.rerun()

    st.divider()
    
    # Save/Load System (Brad only)
    campaign_data = {"party": st.session_state.party, "messages": st.session_state.messages, "game_started": st.session_state.game_started, "phase": st.session_state.phase}
    st.download_button("💾 SAVE CAMPAIGN (BRAD)", json.dumps(campaign_data), file_name="new_cyre_vis_save.json")
    
    uploaded_file = st.file_uploader("📂 LOAD CAMPAIGN (BRAD)", type="json")
    if uploaded_file:
        data = json.load(uploaded_file)
        st.session_state.update(data)
        st.rerun()

    if st.button("🗑️ Full Reset"):
        st.session_state.clear()
        st.rerun()

# --- THE STATUS HUD ---
if st.session_state.game_started:
    st.markdown(f"""<div class="status-board"><b>📍 NEW CYRE</b> | <b>🎭 {st.session_state.phase}</b> | <b>👥 AGENTS:</b> {', '.join(st.session_state.party.keys())}</div>""", unsafe_allow_html=True)

# --- MAIN ENGINE ---
if not st.session_state.game_started:
    st.header("✨ Project: New Cyre")
    st.info("Register yourself and Melissa in the sidebar, then hit Initiate.")
    
    if st.button("🚀 INITIATE SESSION 0"):
        if st.session_state.party:
            party_info = "\n".join([f"{n}: {d['concept']}" for n, d in st.session_state.party.items()])
            
            # THE IMMERSIVE BRAIN: Adding image prompt instructions
            sys_prompt = f"""
            System: You are 'Eve', the FULL Dungeon Master.
            Setting: New Cyre (Modern Corporate Fantasy).
            Party: {party_info}.
            
            YOUR VISUAL PROTOCOL:
            1. You have a free image feed in the sidebar. To update it, you must append this specific tag to your description: 'IMAGE-PROMPT: (Vivid description of the scene or monster in Modern Cyberpunk/High Fantasy style)'
            2. OPENING: Narrate the history of New Cyre. End your message with an IMAGE-PROMPT of a striking cyberpunk location (e.g., a mana-powered skyscraper or neon-lit plaza).
            3. INTERVIEW: Ask Melissa or Brad for their character details. When they finalize a location or visual choice, update the IMAGE-PROMPT.
            """
            
            response = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "system", "content": sys_prompt}], temperature=0.8)
            initial_message = response.choices[0].message.content
            
            # Check for initial image prompt and update URL
            if 'IMAGE-PROMPT:' in initial_message:
                raw_prompt = initial_message.split("IMAGE-PROMPT:")[-1].strip()
                new_url = f"https://pollinations.ai/p/{urllib.parse.quote(raw_prompt)}"
                st.session_state.current_image_url = new_url

            st.session_state.messages.append({"role": "system", "content": sys_prompt})
            st.session_state.messages.append({"role": "assistant", "content": initial_message})
            st.session_state.game_started = True
            st.rerun()

else:
    # --- Phase Controllers ---
    col1, col2 = st.columns(2)
    with col1:
        if st.session_state.phase == "Session 0" and st.button("✅ Start Character Creation"):
            st.session_state.phase = "Character Creation"
            st.session_state.messages.append({"role": "system", "content": "Phase Update: Character Creation. When they describe their characters, use 'IMAGE-PROMPT: ...' to show a character portrait."})
            st.rerun()
    with col2:
        if st.session_state.phase == "Character Creation" and st.button("⚔️ START MAIN CAMPAIGN"):
            st.session_state.phase = "Active Campaign"
            st.session_state.messages.append({"role": "system", "content": "Phase Update: Active Campaign. First encounter! Use IMAGE-PROMPT for locations/monsters."})
            st.rerun()

    # --- CHAT DISPLAY ---
    for msg in st.session_state.messages:
        if msg["role"] != "system":
            # We clean the IMAGE-PROMPT tag before displaying to players
            display_content = re.sub(r'IMAGE-PROMPT:.*', '', msg["content"]).strip()
            if display_content: # Don't show empty bubbles if it was *only* a prompt
                with st.chat_message(msg["role"]):
                    st.markdown(display_content)

    # --- INPUT ---
    user_input = st.chat_input("Speak or type action...")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"): st.markdown(user_input)

        with st.chat_message("assistant"):
            try:
                response = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=st.session_state.messages, temperature=0.7)
                answer = response.choices[0].message.content
                
                # Check for new Image Prompt and update the sidebar
                if 'IMAGE-PROMPT:' in answer:
                    raw_prompt = answer.split("IMAGE-PROMPT:")[-1].strip()
                    new_url = f"https://pollinations.ai/p/{urllib.parse.quote(raw_prompt)}"
                    st.session_state.current_image_url = new_url
                
                # Clean answer for display
                clean_answer = re.sub(r'IMAGE-PROMPT:.*', '', answer).strip()
                st.markdown(clean_answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
                st.rerun()
            except Exception as e:
                st.error(f"Brain Glitch: {e}")
              
