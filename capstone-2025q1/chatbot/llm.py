"""
LLM for the chatbot
"""

import os

from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    HarmBlockThreshold,
    HarmCategory,
)

from chatbot.configs import MODEL_NAME, TEMPERATURE, SYSTEM_PROMPT

from dotenv import load_dotenv

load_dotenv(override=True)

# Initialize the Gemini model
try:
    llm = ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        temperature=TEMPERATURE,
        google_api_key=os.getenv("GOOGLE_API_KEY"),  # Explicitly pass the API key
        safety_settings={
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        },
    )
    print(f"[INFO] LLM initialized successfully with model: {MODEL_NAME}")
except Exception as e:
    print(f"[ERROR] Error initializing LLM: {e}")
    llm = None  # Set to None if an error occurs
