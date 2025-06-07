import os
import logging
import httpx
from dotenv import load_dotenv
from rest_framework.views import APIView
from rest_framework.response import Response

# telegram related imports
import json
import requests
from rest_framework.permissions import AllowAny
from chat.groq_ai import get_groq_reply



# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class ChatAPIView(APIView):
    def post(self, request):
        user_message = request.data.get("message", "")
        if not user_message:
            return Response({"error": "No message provided"}, status=400)

        logger.info(f"User message: {user_message}")

        headers = {
            "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
            "HTTP-Referer": "http://localhost",  # optional
            "X-Title": "ReactChatWithOpenRouter"
        }

        json_data = {
            "model": "deepseek/deepseek-r1-distill-llama-70b:free",
            "messages": [
                # {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Respond briefly in a friendly tone: {user_message}"},
                {"role": "user", "content": user_message}
            ]
        }

        try:
            response = httpx.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=json_data)
            response.raise_for_status()
            reply = response.json()["choices"][0]["message"]["content"]
            return Response({"reply": reply.strip()})
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ HTTP error: {str(e)}")
            return Response({"error": "OpenRouter API Error", "details": str(e)}, status=500)
        except Exception as e:
            logger.error(f"❌ General error: {str(e)}")
            return Response({"error": "Internal Server Error", "details": str(e)}, status=500)
        

class GroqChatAPIView(APIView):
    def post(self, request):
        user_message = request.data.get("message", "")
        if not user_message:
            return Response({"error": "No message provided"}, status=400)

        logger.info(f"[GROQ] User message: {user_message}")

        headers = {
            "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
            "Content-Type": "application/json"
        }

        json_data = {
                "model": "llama3-8b-8192",  # Or another one listed above
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_message}
            ]
        }

        try:
            response = httpx.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=json_data)
            response.raise_for_status()
            reply = response.json()["choices"][0]["message"]["content"]
            return Response({"reply": reply.strip()})
        except httpx.HTTPStatusError as e:
            logger.error(f"[GROQ] ❌ HTTP error: {str(e)}")
            return Response({"error": "Groq API Error", "details": str(e)}, status=500)
        except Exception as e:
            logger.error(f"[GROQ] ❌ General error: {str(e)}")
            return Response({"error": "Internal Server Error", "details": str(e)}, status=500)


class GroqChatTwoAPIView(APIView):
    def post(self, request):
        user_message = request.data.get("message", "")
        if not user_message:
            return Response({"error": "No message provided"}, status=400)

        logger.info(f"[GROQ] User message: {user_message}")

        headers = {
            "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
            "Content-Type": "application/json"
        }

        json_data = {
                "model": "llama3-70b-8192",  # Or another one listed above
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_message}
            ]
        }

        try:
            response = httpx.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=json_data)
            response.raise_for_status()
            reply = response.json()["choices"][0]["message"]["content"]
            return Response({"reply": reply.strip()})
        except httpx.HTTPStatusError as e:
            logger.error(f"[GROQ] ❌ HTTP error: {str(e)}")
            return Response({"error": "Groq API Error", "details": str(e)}, status=500)
        except Exception as e:
            logger.error(f"[GROQ] ❌ General error: {str(e)}")
            return Response({"error": "Internal Server Error", "details": str(e)}, status=500)


class TelegramBotAPIView(APIView):
    permission_classes = [AllowAny]  # Required since Telegram doesn't send auth

    
    def get(self, request):  # Optional GET handler to avoid 500
        print(os.getenv('TELEGRAM_BOT_TOKEN'))
        return Response({"message": "Telegram Bot Webhook is ready."})


    def post(self, request):
        data = request.data
        message = data.get("message", {}).get("text")
        chat_id = data.get("message", {}).get("chat", {}).get("id")

        if not message or not chat_id:
            logger.warning("Invalid Telegram request: Missing chat_id or message")
            return Response({"status": "ignored"})

        logger.info(f"📩 Telegram message from {chat_id}: {message}")

        # Process message with your AI backend (Groq/OpenRouter)
        try:
            reply = get_groq_reply(message)  # or get_openrouter_reply(message)
        except Exception as e:
            logger.error(f"❌ Error getting AI reply: {str(e)}")
            reply = "Oops! AI backend error."

        # Send reply back to Telegram
        telegram_api = f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/sendMessage"
        print(f"Sending reply to Telegram: {telegram_api}")
        payload = {
            "chat_id": chat_id,
            "text": reply,
        }
        try:
            # proxies = {
            #     "http": "http://102.23.235.205",    # Sample public proxy
            #     "https": "http://102.23.235.205"
            # }

            response = requests.post(telegram_api, json=payload, timeout=10)
            response.raise_for_status()
            logger.info(f"✅ Telegram sent reply: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"❌ Failed to send Telegram reply: {str(e)}")
        # try:
        #     requests.post(telegram_api, json=payload)
        # except Exception as e:
        #     logger.error(f"❌ Failed to send Telegram reply: {str(e)}")

        return Response({"status": "ok"})