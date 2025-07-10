#non thread code

# from dotenv import load_dotenv
# load_dotenv()  
# from fastapi import FastAPI, Depends
# from fastapi.responses import StreamingResponse
# from pydantic import BaseModel
# from .db import chat_collection
# from datetime import datetime
# from .auth import login_handler, get_current_user
# from .agent import run_agent  
# from dotenv import load_dotenv
# load_dotenv() 

# app = FastAPI()

# default_model_config = {"orm_mode": True}
# class LoginForm(BaseModel):
#     username: str
#     password: str

# class ChatRequest(BaseModel):
#     query: str

# @app.post("/login")
# async def login(form: LoginForm):
#     return await login_handler(form)

# @app.get("/ping-mongo")
# def test_mongo():
#     chat_collection.insert_one({"ping": "pong"})
#     return {"status": "ok"}

# @app.post("/chat")
# async def chat_endpoint(
#     request: ChatRequest,
#     user=Depends(get_current_user)
# ):
#     user_id = user["username"]
#     query = request.query
#     response = run_agent(query)
#     chat_collection.insert_one({"test": "hello from FastAPI"})
#     print("Inserting to Mongo:", query, response)
#     try:
#         chat_collection.insert_many([
#         {
#             "user_id": user_id,
#             "role": "user",
#             "content": query,
#             "timestamp": datetime.utcnow()
#         },
#         {
#             "user_id": user_id,
#             "role": "agent",
#             "content": response,
#             "timestamp": datetime.utcnow()
#         }
#         ])
#     except Exception as e:
#         print("❌ Mongo insert failed:", e)
#     return {"response": response}


#----------------------------------------thread code ------------------------------------------

# from dotenv import load_dotenv
# load_dotenv()

# import uuid
# from fastapi import FastAPI, Depends, HTTPException
# from pydantic import BaseModel
# from fastapi.responses import StreamingResponse
# from datetime import datetime

# from .db import chat_collection
# from .auth import login_handler, get_current_user
# from .agent import run_agent
# app = FastAPI()

# class LoginForm(BaseModel):
#     username: str
#     password: str

# class ChatRequest(BaseModel):
#     query: str
#     thread_id: str

# @app.post("/login")
# async def login(form: LoginForm):
#     token = await login_handler(form)
#     if not token:
#         raise HTTPException(401, "Invalid credentials")
#     session_thread = str(uuid.uuid4())
#     return {"access_token": token, "thread_id": session_thread}

# @app.get("/ping-mongo")
# def test_mongo():
#     chat_collection.insert_one({"ping": "pong"})
#     return {"status": "ok"}

# @app.post("/chat")
# async def chat_endpoint(
#     request: ChatRequest,
#     user=Depends(get_current_user)
# ):
#     user_id   = user["username"]
#     query     = request.query
#     thread_id = request.thread_id

#     response = run_agent(query, thread_id)

#     now = datetime.utcnow()
#     try:
#         chat_collection.insert_many([
#             {"user_id": user_id, "role": "user",  "content": query,    "timestamp": now},
#             {"user_id": user_id, "role": "agent", "content": response, "timestamp": now},
#         ])
#     except Exception as e:
#         print("❌ Mongo insert failed:", e)

#     return {
#         "response":   response,
#         "thread_id":  thread_id
#     }

# main.py
from dotenv import load_dotenv
load_dotenv()

import uuid
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from datetime import datetime

from .db import chat_collection
from .auth import login_handler, get_current_user
from .agent import run_agent, run_agent_stream

app = FastAPI()

class LoginForm(BaseModel):
    username: str
    password: str

class ChatRequest(BaseModel):
    query: str
    thread_id: str

@app.post("/login")
async def login(form: LoginForm):
    token = await login_handler(form)
    if not token:
        raise HTTPException(401, "Invalid credentials")
    return {"access_token": token, "thread_id": str(uuid.uuid4())}

@app.post("/chat")
async def chat(request: ChatRequest, user=Depends(get_current_user)):
    user_id, q, tid = user["username"], request.query, request.thread_id
    resp = run_agent(q, tid)
    ts = datetime.utcnow()
    chat_collection.insert_many([
        {"user_id":user_id, "thread_id":tid, "role":"user",  "content":q,   "timestamp":ts},
        {"user_id":user_id, "thread_id":tid, "role":"agent", "content":resp,"timestamp":ts},
    ])
    return {"response":resp, "thread_id":tid}

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest, user=Depends(get_current_user)):
    user_id, q, tid = user["username"], request.query, request.thread_id
    now = datetime.utcnow()
    # persist the user’s question as a single doc
    chat_collection.insert_one({
        "user_id":    user_id,
        "thread_id":  tid,
        "role":       "user",
        "content":    q,
        "timestamp":  now
    })

    # synchronous generator for SSE
    # def event_gen():
    #     assistant_accum = ""
    #     for token in run_agent_stream(q, tid):
    #         # if neither side has space/newline, inject one
    #         if assistant_accum \
    #            and not assistant_accum.endswith((" ", "\n")) \
    #            and not token.startswith((" ", "\n")):
    #             token = " " + token

    #         assistant_accum += token
    #         # emit *just* the new bit (with any leading space you added)
    #         yield f"data: {token}\n\n"

    #         # persist the growing assistant reply if you like
    #         chat_collection.insert_one({
    #             "user_id":    user_id,
    #             "thread_id":  tid,
    #             "role":       "agent",
    #             "content":    assistant_accum,
    #             "timestamp":  datetime.utcnow()
    #         })
    
    def event_gen():
        assistant_accum = ""
        for token in run_agent_stream(q, tid):
            # only inject if both sides are alphanumeric
            if assistant_accum and assistant_accum[-1].isalnum() \
               and token and token[0].isalnum():
                # use non-breaking space so HTML won't collapse it
                token = "\u00A0" + token

            assistant_accum += token

            # emit just this chunk (with any NBSP we added)
            yield f"data: {token}\n\n"

            # optionally persist the growing assistant reply
            chat_collection.insert_one({
                "user_id":   user_id,
                "thread_id": tid,
                "role":      "agent",
                "content":   assistant_accum,
                "timestamp": datetime.utcnow(),
            })

    return StreamingResponse(event_gen(), media_type="text/event-stream")