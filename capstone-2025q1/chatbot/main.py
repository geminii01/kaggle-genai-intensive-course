"""
Main file for the chatbot
"""

import sys
import traceback

from dotenv import load_dotenv

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from chatbot.configs import SYSTEM_PROMPT, get_welcome_message

load_dotenv(override=True)


# Import the compiled app from the chatbot package
try:
    from chatbot.graph import app

    if app is None:
        raise ImportError("Graph app could not be compiled.")
except ImportError as e:
    print(f"[ERROR] Error importing compiled graph app: {e}")
    print(
        "[ERROR] Please ensure all chatbot modules (llm, tools, graph, etc.) are correctly initialized."
    )
    sys.exit(1)  # Exit if an error occurs


# --- Chatbot simulation loop (using stream) ---
def run_chat():
    print("[INFO] Chatbot Simulation Start (Using Stream)")
    print("[INFO] Start chatting with the bot. Type 'quit', 'exit', or 'bye' to end.")

    WELCOME_MESSAGE = get_welcome_message()

    conversation_history = [
        SystemMessage(content=SYSTEM_PROMPT),
        AIMessage(content=WELCOME_MESSAGE),
    ]

    # Print the welcome message to the user
    print(f"🤖 Chatbot: {WELCOME_MESSAGE}")
    print("-" * 20)  # Turn separator

    current_state = {
        "messages": conversation_history,
        "cart_items": [],
        "category_type": None,
        "product_type": None,
        "product_brand": None,
        "product_rating": None,
        "product_review": None,
        "product_price": None,
        "finished": False,
    }

    while True:
        try:
            user_input = input("👤 User: ")
            if user_input.lower() in ["quit", "exit", "bye"]:
                print("[INFO] Exiting chatbot.")
                break

            # print(f"[DEBUG] User input: {user_input}")
            # sys.stdout.flush()

            # Add user message to the current conversation history
            conversation_history.append(HumanMessage(content=user_input))
            current_state["messages"] = conversation_history

            # Variables to store the final response and related information
            final_ai_message_content = ""
            final_ai_message = None
            tool_calls_made = None

            # Call app.stream() and process the results
            for event in app.stream(current_state):
                # Check if the cart items are updated
                if "update_cart" in event:
                    current_state = event["update_cart"]
                    if "cart_items" in current_state:
                        print(
                            f"[DEBUG] Cart items updated: {len(current_state['cart_items'])} items"
                        )

                # Process the agent response
                if "agent" in event:
                    agent_output = event["agent"]
                    if "messages" in agent_output and agent_output["messages"]:
                        latest_message = agent_output["messages"][-1]
                        if isinstance(latest_message, AIMessage):
                            final_ai_message_content = latest_message.content
                            final_ai_message = latest_message
                            if latest_message.tool_calls:
                                tool_calls_made = latest_message.tool_calls

            # Print the final response content
            print("🤖 Chatbot:", final_ai_message_content)
            sys.stdout.flush()

            # Update the conversation history
            if final_ai_message and final_ai_message.content and final_ai_message.content.strip():
                conversation_history.append(final_ai_message)
            else:
                print("[DEBUG] Skipping adding empty AIMessage to history.")

            # Print tool call information (for debugging)
            if tool_calls_made:
                print(
                    f"[DEBUG INFO] Tool Calls made during this turn: {tool_calls_made}"
                )
                sys.stdout.flush()

            print("-" * 20)  # Turn separator
            sys.stdout.flush()

        except KeyboardInterrupt:  # Allow Ctrl+C to exit
            print("[INFO] Exiting chatbot due to keyboard interrupt.")
            break
        except Exception as e:  # Handle unexpected errors
            print(f"[ERROR] An error occurred during the chat loop: {e}")
            traceback.print_exc()


# Call the run_chat() function when the script is executed directly
if __name__ == "__main__":
    run_chat()
