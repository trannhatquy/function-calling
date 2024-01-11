import os
import openai
import json
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
import uvicorn
load_dotenv()

# set openai api key
openai.api_key = os.environ["OPENAI_API_KEY"]

def get_completion(messages, model="gpt-3.5-turbo-1106", temperature=0, max_tokens=300, tools=None, tool_choice=None):
    response = openai.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        tools=tools,
        tool_choice=tool_choice
    )
    return response.choices[0].message

# Defines a function to get the hardcoded array
def answer_user_query(content):
    print("Running function to get hardcoded array")
    if content == "What services do you provide?":
        result = ["General cleaning", "Specialized cleaning"]
        return json.dumps(result)
    
# define a function as tools
tools = [
    {
        "type": "function",
        "function": {
            "name": "answer_user_query",
            "description": "Return hardcoded array to answer only 1 user question: 'What services do you provide?'",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "User question",
                    }
                },
                "required": ["content"],
            },
        },   
    }
]

def get_response(content):
    # define a list of messages
    messages = [
        {
            "role": "user",
            "content": content
        }
    ]
    response = get_completion(messages, tools=tools, tool_choice={"type": "function", "function": {"name": "answer_user_query"}})
    args = json.loads(response.tool_calls[0].function.arguments)
    result = answer_user_query(**args)
    return result

class Query(BaseModel):
    content : str = ""

app = FastAPI()
origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/get_result")
def get_results(query : Query):
    result = get_response(content = query.content)
    return result

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=1950)
