"""
Configuration for the chatbot
"""

# Model Configuration
MODEL_NAME = "gemini-2.0-flash"
TEMPERATURE = 0.56

# Data Path
DATA_FILE_PATH = "./data/sample_data.csv"  # Relative path from the main.py file

# Fuzzy Matching Configuration
FUZZY_SCORE_THRESHOLD = 75  # threshold

# Chatbot Prompt
SYSTEM_PROMPT = """You are a helpful shopping assistant for an online grocery store.
Your role is to help users find products, compare options, and manage their shopping cart.
Always be concise and focus on completing the user's request efficiently.
When users ask about products, use the available tools to search the database."""

def get_welcome_message():
    from chatbot.data_loader import available_categories
    return f"""Welcome to our Online Grocery Store Chat Assistant! 

I can help you:
- Browse product categories
- Find specific products
- Compare prices, ratings, and reviews
- Add items to your cart

Available Categories: 
{", ".join(available_categories)}

What would you like to do today?"""
