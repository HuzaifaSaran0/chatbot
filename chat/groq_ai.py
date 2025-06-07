import os
import httpx
import logging

logger = logging.getLogger(__name__)

def get_groq_reply(user_message: str) -> str:
    headers = {
        "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
        "Content-Type": "application/json"
    }

    json_data = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "system", "content": "You are a friendly and helpful assistant."},
            {"role": "user", "content": user_message}
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
