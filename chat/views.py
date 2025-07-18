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
import pytz
from datetime import datetime

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Conversation, Message
from django.shortcuts import get_object_or_404
from django.utils.timesince import timesince

from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView

class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter


# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_conversation(request):
    conv = Conversation.objects.create(user=request.user)
    return Response({"conversation_id": conv.id})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_conversations(request):
    convs = Conversation.objects.filter(user=request.user).order_by('-started_at')
    data = []
    for c in convs:
        started_display = c.started_at.strftime("%b %d, %Y %I:%M %p")  # Example: Jul 05, 2025 10:23 AM
        data.append({
            "id": c.id,
            "started_at": c.started_at,
            "title": f"Chat - {started_display}"
        })
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_messages(request, conversation_id):
    conv = get_object_or_404(Conversation, id=conversation_id, user=request.user)
    msgs = conv.messages.order_by('timestamp')
    data = [{"sender": m.sender, "content": m.content, "timestamp": m.timestamp} for m in msgs]
    return Response(data)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_conversation(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
    conversation.delete()
    return Response({"message": "Conversation deleted successfully"})



class ChatAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_message = request.data.get("message", "")
        conversation_id = request.data.get("conversation_id")
        history = request.data.get("history", [])
        if not user_message or not conversation_id:
            return Response({"error": "Missing message or conversation_id"}, status=400)
            # return Response({"error": "No message provided"}, status=400)
        conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
        Message.objects.create(
            conversation=conversation,
            sender="user",
            content=user_message
        )

        logger.info(f"User message: {user_message}")


        # Get current time in Pakistan timezone
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
        
        full_messages = [{"role": "system", "content": system_prompt}] + history
        headers = {
            "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
            "HTTP-Referer": "http://localhost",  # optional
            "X-Title": "ReactChatWithOpenRouter"
        }

        json_data = {
            "model": "deepseek/deepseek-r1-distill-llama-70b:free",
            "messages": full_messages
        }

        try:
            response = httpx.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=json_data)
            response.raise_for_status()
            reply = response.json()["choices"][0]["message"]["content"]
            Message.objects.create(
                conversation=conversation,
                sender="bot",
                content=reply.strip()
            )
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
        history = request.data.get("history", [])
        if not user_message:
            return Response({"error": "No message provided"}, status=400)

        logger.info(f"[GROQ] User message: {user_message}")

        headers = {
            "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
            "Content-Type": "application/json"
        }
        # Get current time in Pakistan timezone
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
                "model": "llama3-8b-8192",  # Or another one listed above
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ] + history
        }

        try:
            response = httpx.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=json_data)
            response.raise_for_status()
            reply = response.json()["choices"][0]["message"]["content"]
            conversation_id = request.data.get("conversation_id")
            if conversation_id:
                conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
                Message.objects.create(conversation=conversation, sender="user", content=user_message)
                Message.objects.create(conversation=conversation, sender="bot", content=reply.strip())
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
        history = request.data.get("history", [])
        if not user_message:
            return Response({"error": "No message provided"}, status=400)

        logger.info(f"[GROQ] User message: {user_message}")

        headers = {
            "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
            "Content-Type": "application/json"
        }
        # Get current time in Pakistan timezone
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
                "model": "llama3-70b-8192",  # Or another one listed above
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ] + history
        }

        try:
            response = httpx.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=json_data)
            response.raise_for_status()
            reply = response.json()["choices"][0]["message"]["content"]
            conversation_id = request.data.get("conversation_id")
            if conversation_id:
                conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
                Message.objects.create(conversation=conversation, sender="user", content=user_message)
                Message.objects.create(conversation=conversation, sender="bot", content=reply.strip())

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


