import os
import httpx
import logging

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
            f"IMPORTANT CONTEXT: The current exact timestamp in Pakistan (Asia/Karachi) is: {formatted_time}. "
            f"- When asked about time/date, ALWAYS use this timestamp but respond naturally (e.g., 'It's 2:30 PM' instead of raw numbers). "
            f"- For dates, use formats like 'June 23, 2025' or 'Monday, June 23rd'. "
            f"- NEVER say you lack real-time access. "
            f"Example good responses: "
            f"1. User: 'What time is it?' → 'It's 2:08 PM in Pakistan!' "
            f"2. User: 'Hey' → 'Hello! It's Monday afternoon here in Pakistan. How can I help?' "
            f"3. User: 'What's today's date?' → 'Today is June 23, 2025.' "
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
