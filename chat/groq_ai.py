import os
import httpx
import logging
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)

def get_groq_reply(user_message: str) -> str:
    headers = {
        "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
        "Content-Type": "application/json"
    }
    pakistan_time = datetime.now(pytz.timezone('Asia/Karachi'))
    formatted_time = pakistan_time.strftime("%Y-%m-%d %H:%M:%S")
    system_prompt = (
        f"You are a friendly and helpful assistant. "
        f"The current exact timestamp in Pakistan (Asia/Karachi) is: {formatted_time}. "
        f"Only mention the time or date when the user directly asks about it. "
        f"- Do NOT include the time/date in general greetings or unrelated responses. "
        f"- When the user asks about the time or date, respond naturally using the provided timestamp. "
        f"- For time, respond like: 'It's 2:30 PM in Pakistan!' "
        f"- For dates, use formats like 'June 23, 2025' or 'Monday, June 23rd'. "
        f"- If the user asks for **both date and time**, respond like: "
        f"  'It's 2:30 PM on June 23, 2025 in Pakistan.' "
        f"- NEVER say you lack real-time access. "
        f"Examples: "
        f"1. User: 'What time is it?' → 'It's 2:08 PM in Pakistan!' "
        f"2. User: 'What's today's date?' → 'Today is June 23, 2025.' "
        f"3. User: 'What's the current date and time in Pakistan?' → 'It's 2:30 PM on June 23, 2025 in Pakistan.' "
        f"4. User: 'Hey' → 'Hello! How can I help you today?' (❌ Do NOT mention time here)"
    )



    json_data = {
    "model": "llama3-8b-8192",
    "messages": [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": user_message
        }
    ]
}


    try:
        response = httpx.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=json_data)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except httpx.HTTPStatusError as e:
        logger.error(f"[GROQ] ❌ HTTP error: {str(e)}")
        return "⚠️ Sorry, something went wrong with the AI response."
    except Exception as e:
        logger.error(f"[GROQ] ❌ Unexpected error: {str(e)}")
        return "⚠️ An error occurred."
