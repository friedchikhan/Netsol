# import os, uuid, json, requests, gradio as gr

# API_URL = os.getenv("API_URL", "http://localhost:8000")

# def login(username, password):
#     resp = requests.post(f"{API_URL}/login", json={"username":username, "password":password})
#     resp.raise_for_status()
#     data = resp.json()
#     return data["access_token"], data["thread_id"]

# def new_chat(sessions):
#     # 1) Create a new session ID
#     new_id = str(uuid.uuid4())
#     sessions[new_id] = []  # start with empty history

#     # 2) Use gr.update to refresh dropdown choices & set its value
#     dropdown_update = gr.update(choices=list(sessions.keys()), value=new_id)

#     # 3) Return in the same order as outputs:
#     #    [session_selector, thread_state, sessions_state, chatbot]
#     return dropdown_update, new_id, sessions, []

# def switch_session(chosen_id, sessions):
#     # reload the history for that session
#     return sessions.get(chosen_id, []), chosen_id

# def chat_func(message, history, token, thread_id, sessions):
#     headers = {"Authorization": f"Bearer {token}"}
#     payload = {"query": message, "thread_id": thread_id}
#     resp = requests.post(f"{API_URL}/chat", json=payload, headers=headers)

#     # parse response
#     try:
#         data = resp.json()
#         if resp.status_code == 200:
#             bot_reply = data.get("response", "[no response]")
#         else:
#             detail = data.get("detail", resp.text)
#             bot_reply = json.dumps(detail) if isinstance(detail,(list,dict)) else detail
#     except ValueError:
#         bot_reply = f"[Invalid JSON] {resp.text}"

#     # append and persist
#     history = history or []
#     history.append((message, bot_reply))
#     sessions[thread_id] = history

#     return history, thread_id, sessions

# with gr.Blocks() as demo:
#     gr.Markdown("## Netsol-Agent Multi-Chat")

#     with gr.Row():
#         user_input    = gr.Textbox(label="Username")
#         pwd_input     = gr.Textbox(label="Password", type="password")
#         login_btn     = gr.Button("🔑 Login")
#         token_state   = gr.State()
#         sessions_state= gr.State(value={})
#         thread_state  = gr.State(value=None)

#     login_btn.click(
#         login,
#         inputs=[user_input, pwd_input],
#         outputs=[token_state, thread_state]
#     )

#     with gr.Row():
#         new_chat_btn     = gr.Button("➕ New Chat")
#         session_selector = gr.Dropdown(
#             choices=[], label="Active Chats", allow_custom_value=True
#         )

#     chatbot = gr.Chatbot(type="tuples")
#     msg     = gr.Textbox(placeholder="Type your message…")

#     # NEW CHAT: create session, update dropdown & clear chat
#     new_chat_btn.click(
#         new_chat,
#         inputs=[sessions_state],
#         outputs=[session_selector, thread_state, sessions_state, chatbot]
#     )

#     # SWITCH SESSION: when dropdown changes, reload history
#     session_selector.change(
#         switch_session,
#         inputs=[session_selector, sessions_state],
#         outputs=[chatbot, thread_state]
#     )

#     # CHAT: send message under current thread
#     msg.submit(
#         chat_func,
#         inputs=[msg, chatbot, token_state, thread_state, sessions_state],
#         outputs=[chatbot, thread_state, sessions_state]
#     )

#     demo.launch()

#----------------------------------streaming-------------------------------

# gradio_app.py
import os, uuid, json, requests, gradio as gr

API_URL = os.getenv("API_URL","http://localhost:8000")

def login(u,p):
    r = requests.post(f"{API_URL}/login", json={"username":u,"password":p})
    r.raise_for_status()
    j = r.json()
    return j["access_token"], j["thread_id"]

def new_chat(sessions):
    new_id = str(uuid.uuid4())
    sessions[new_id] = []
    return gr.update(choices=list(sessions), value=new_id), new_id, sessions, []

def switch(sess_id, sessions):
    return sessions.get(sess_id, []), sess_id

def chat_stream(message, history, token, thread_id, sessions):
    history = history or []
    # append user turn
    history.append({"role":"user","content":message})

    # call the streaming endpoint
    headers = {"Authorization":f"Bearer {token}"}
    payload = {"query":message, "thread_id":thread_id}
    resp    = requests.post(f"{API_URL}/chat/stream",
                            json=payload,
                            headers=headers,
                            stream=True)

    assistant_text = ""
    for line in resp.iter_lines():
        if not line: continue
        # strip off leading "data: "
        chunk = line.decode().removeprefix("data: ").strip()
        assistant_text += chunk
        # yield updated history
        yield history + [{"role":"assistant","content":assistant_text}], thread_id, sessions

    # finalize in your sessions store
    sessions[thread_id] = history + [{"role":"assistant","content":assistant_text}]

with gr.Blocks() as demo:
    gr.Markdown("## Netsol-Agent (streaming)")

    with gr.Row():
        user_in  = gr.Textbox(label="Username")
        pwd_in   = gr.Textbox(label="Password", type="password")
        btn_login= gr.Button("🔑 Login")
        tok_state= gr.State()
        sess_state=gr.State(value={})
        thr_state= gr.State(value=None)

    btn_login.click(login, [user_in,pwd_in], [tok_state, thr_state])

    with gr.Row():
        btn_new = gr.Button("➕ New Chat")
        sel     = gr.Dropdown(choices=[], label="Sessions", allow_custom_value=True)

    chatbot = gr.Chatbot(type="messages")
    msgbox  = gr.Textbox(placeholder="Type and enter…")

    btn_new.click(new_chat,
                  inputs=[sess_state],
                  outputs=[sel, thr_state, sess_state, chatbot])

    sel.change(switch,
               inputs=[sel, sess_state],
               outputs=[chatbot, thr_state])

    msgbox.submit(chat_stream,
                  inputs=[msgbox, chatbot, tok_state, thr_state, sess_state],
                  outputs=[chatbot, thr_state, sess_state])

    demo.launch()
    
#-----------------------------------------working---------------------------------------

# import os
# import requests
# import gradio as gr

# API_URL = os.getenv("API_URL", "http://localhost:8000")


# # ✅ Login function
# def login(username, password):
#     try:
#         resp = requests.post(
#             f"{API_URL}/login", json={"username": username, "password": password}
#         )
#         resp.raise_for_status()
#         data = resp.json()
#         token = data.get("access_token")
#         if token:
#             return "✅ Logged in!", token
#         else:
#             return "❌ Login failed.", ""
#     except Exception as e:
#         return f"❌ Error: {str(e)}", ""


# # ✅ Chat function (no streaming version)
# def chat_func(message, chat_history, token):
#     if not token:
#         return chat_history + [("System", "❌ Please log in first.")], token

#     headers = {"Authorization": f"Bearer {token}"}
#     try:
#         resp = requests.post(
#             f"{API_URL}/chat", json={"query": message}, headers=headers
#         )
#         resp.raise_for_status()
#         bot_reply = resp.json().get("response", "⚠️ No response")
#     except Exception as e:
#         bot_reply = f"❌ Error: {str(e)}"

#     chat_history.append((message, bot_reply))
#     return chat_history, token


# # ✅ Gradio UI
# with gr.Blocks() as demo:
#     gr.Markdown("## 💬 Netsol-Agent Chat")

#     # --- Login Section ---
#     with gr.Row():
#         user_input = gr.Textbox(label="Username")
#         pwd_input = gr.Textbox(label="Password", type="password")
#         login_btn = gr.Button("🔐 Login")
#         login_status = gr.Textbox(label="Login Status", interactive=False)
#         token_state = gr.State(value="")

#     login_btn.click(
#         fn=login,
#         inputs=[user_input, pwd_input],
#         outputs=[login_status, token_state]
#     )

#     # --- Chat Section ---
#     chatbot = gr.Chatbot(label="Chat History")
#     msg = gr.Textbox(placeholder="Type your message and hit enter...")

#     msg.submit(
#         fn=chat_func,
#         inputs=[msg, chatbot, token_state],
#         outputs=[chatbot, token_state]
#     )

# demo.launch()