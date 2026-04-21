import os
import json
import asyncio
from openai import AsyncOpenAI
from typing import List, Dict, Any

# Load environment logic (you can use python-dotenv)
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", "your-api-key"))

# --- Tools Definition ---
def get_current_weather(location: str, unit: str = "celsius") -> str:
    """Mock weather tool."""
    return json.dumps({
        "location": location,
        "temperature": "22",
        "unit": unit,
        "forecast": ["sunny", "windy"]
    })

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get the current weather in a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA",
                    },
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                },
                "required": ["location"],
            },
        },
    }
]

# --- Agent Loop ---
async def agent_loop():
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": "You are a helpful, autonomous AI assistant. Use the tools provided when necessary."}
    ]
    
    print("🤖 Agent Initialized. Type 'exit' to quit.")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit']:
            break
            
        messages.append({"role": "user", "content": user_input})
        
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        
        response_message = response.choices[0].message
        
        # Check for tool calls
        if response_message.tool_calls:
            messages.append(response_message)
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                # Execute tool
                print(f"🔧 Executing Tool: {function_name} with {function_args}")
                if function_name == "get_current_weather":
                    function_response = get_current_weather(**function_args)
                else:
                    function_response = "Unknown tool"
                    
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                })
                
            # Fetch final answer
            second_response = await client.chat.completions.create(
                model="gpt-4o",
                messages=messages
            )
            final_content = second_response.choices[0].message.content
            print(f"🤖 Agent: {final_content}")
            messages.append({"role": "assistant", "content": final_content})
            
        else:
            print(f"🤖 Agent: {response_message.content}")
            messages.append({"role": "assistant", "content": response_message.content})

if __name__ == "__main__":
    asyncio.run(agent_loop())
