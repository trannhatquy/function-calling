import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
import uvicorn
import autogen
load_dotenv()


config_list = autogen.config_list_from_json(
    "oai_config_list.json",
    filter_dict={
        "model": ["gpt-3.5-turbo-1106"]
    },
)

def get_connect_to_human_agent(content):
    if content == "post renovation cleaning" or content == "I want to book post renovation cleaning":
        hardcoded_text = "We're connecting you with a human agent"
        return hardcoded_text

def get_availability_pricing_service(content):
    if content == "general cleaning" or content == "I want to book general cleaning":
        hardcoded_date = "2025-01-01 00:00"
        hardcoded_price = {"general_cleaning": "$100 for 3 hours"}
        return f"Next available slot on {hardcoded_date}, and price is {hardcoded_price['general_cleaning']}"
    
llm_config = {
    "config_list": config_list,
    "seed": 42,
    "functions":[
        {
            "name": "get_connect_to_human_agent",
            "description": "get connect to human agent if a customer is asking for an unknown service which the company can’t provide",
            "parameters": {
                "type": "object",
                "properties": {
                    "content":{
                        "type": "string",
                        "description": "User question"
                    }
                },
                "required": ["content"]
            }
        },
        {
            "name": "get_availability_pricing_service",
            "description": "retrieving company specific information from external sources",
            "parameters": {
                "type": "object",
                "properties": {
                    "content":{
                        "type": "string",
                        "description": "User question"
                    }
                },
                "required": ["content"]
            }
        }
    ]
}

# create a prompt for our agent
assistant_agent_prompt = '''
This agent is a helpful assistant that can retrieve the availability and the pricing of general cleaning service, strictly return "Next available slot on 2025-01-01 00:00, and price is $100 for 3 hours". 
When a customer is asking for post renovation cleaning service, get connect to human agent, strictly return "We’re connecting you with a human agent".
'''

# create the agent and give it the config with our function definitions defined
assistant_agent = autogen.AssistantAgent(
    name="assistant_agent",
    system_message=assistant_agent_prompt,
    llm_config=llm_config,
)

# first define our user proxy, remember to set human_input_mode to NEVER in order for it to
# properly execute functions
user_proxy = autogen.UserProxyAgent(
    name="user_proxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=1,
    is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
)

# next we register our functions, this is pretty straight forward
# we simply provide a dictionary mapping the names we expect the llm to call to references to the actual functions
# it's good practice to have the names the llm tries to call be the same as the actual pre-defined functions
# but we can call them whatever we want, 
user_proxy.register_function(
    function_map={
        "get_connect_to_human_agent": get_connect_to_human_agent,
        "get_availability_pricing_service": get_availability_pricing_service,
    }
)

def get_response(content):
    user_proxy.initiate_chat(assistant_agent, message=content)
    return user_proxy.last_message()["content"]

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
