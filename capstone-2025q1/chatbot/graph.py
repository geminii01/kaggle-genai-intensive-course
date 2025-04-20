"""
Graph for the chatbot
"""

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import AIMessage

from chatbot.state import State
from chatbot.llm import llm
from chatbot.tools import all_tools

print("[INFO] Building Graph")

# Bind tools to LLM
if llm and all_tools:  # Check if LLM and tools are loaded properly
    llm_with_tools = llm.bind_tools(all_tools)
    print("[INFO] LLM successfully bound with tools.")
else:
    print("[ERROR] LLM or tools not available. Cannot bind tools.")
    # Add logic for error handling or using a default LLM (for error situation)
    llm_with_tools = llm  # Use LLM without tools (for error situation)


# Define the node functions
def agent_node(state: State):
    """Node that calls the LLM to decide on a response or tool call"""
    print("[INFO] Agent Node Execution")
    if not llm_with_tools:
        # Return an error message if LLM initialization fails
        return {
            "messages": [
                AIMessage(
                    content="Sorry, I cannot process your request right now due to an internal error."
                )
            ]
        }
    # Call the LLM
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}


# Create a ToolNode (responsible for executing tools)
tool_node = ToolNode(all_tools)


def should_call_tool(state: State):
    """Determine if a tool should be called based on the LLM's response"""
    print("[INFO] Checking for tool call")
    last_message = state["messages"][-1]
    # Check if the last message is an AIMessage and has tool_calls
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        print(
            f"[INFO] Decision: Tool call required ({len(last_message.tool_calls)} calls)"
        )
        return "call_tool"  # Route to the action node
    else:
        print("[INFO] Decision: No tool call required (End Turn)")
        return "end"  # End the graph execution (this turn)


def update_cart_node(state):
    """Updates the cart based on tool output"""
    tool_output = state.get("action", {})

    if not state.get("cart_items"):
        state["cart_items"] = []

    # Add item to cart
    if "name" in tool_output and tool_output["name"] == "add_to_cart":
        if "output" in tool_output and tool_output["output"].get("status") == "success":
            new_item = tool_output["output"].get("item")
            if new_item:
                # Check if the same product already exists
                existing_item = None
                for i, item in enumerate(state["cart_items"]):
                    if (
                        item["product_type"] == new_item["product_type"]
                        and item["product_brand"] == new_item["product_brand"]
                    ):
                        existing_item = i
                        break

                if existing_item is not None:
                    # Update the quantity and total price of the existing product
                    current_quantity = state["cart_items"][existing_item]["quantity"]
                    new_quantity = current_quantity + new_item["quantity"]
                    price = state["cart_items"][existing_item]["price"]
                    state["cart_items"][existing_item]["quantity"] = new_quantity
                    state["cart_items"][existing_item]["item_total"] = (
                        price * new_quantity
                    )
                    print(
                        f"[INFO] Updated cart item quantity: {state['cart_items'][existing_item]}"
                    )
                else:
                    # Add new product
                    state["cart_items"].append(new_item)
                    print(f"[INFO] Added to cart: {new_item}")

                # Print the cart history
                total = sum(item["item_total"] for item in state["cart_items"])
                print(
                    f"[INFO] Cart now has {len(state['cart_items'])} items, total: ${total:.2f}"
                )

    # Remove item from cart
    elif "name" in tool_output and tool_output["name"] == "remove_from_cart":
        if "output" in tool_output and tool_output["output"].get("status") == "success":
            product_type = tool_output["args"].get("product_type")
            brand = tool_output["args"].get("brand")

            if product_type:
                # If the brand is specified, remove only the specified brand's product
                if brand:
                    state["cart_items"] = [
                        item
                        for item in state["cart_items"]
                        if not (
                            item["product_type"].lower() == product_type.lower()
                            and item["product_brand"].lower() == brand.lower()
                        )
                    ]
                    print(f"[INFO] Removed {brand} {product_type} from cart")
                # If the brand is not specified, remove all products of the specified type
                else:
                    state["cart_items"] = [
                        item
                        for item in state["cart_items"]
                        if item["product_type"].lower() != product_type.lower()
                    ]
                    print(f"[INFO] Removed all {product_type} items from cart")

    # Modify cart item quantity
    elif "name" in tool_output and tool_output["name"] == "modify_cart":
        if "output" in tool_output and tool_output["output"].get("status") == "success":
            product_type = tool_output["args"].get("product_type")
            brand = tool_output["args"].get("brand")
            quantity = tool_output["args"].get("quantity", 1)

            if product_type and brand and quantity:
                for i, item in enumerate(state["cart_items"]):
                    if (
                        item["product_type"].lower() == product_type.lower()
                        and item["product_brand"].lower() == brand.lower()
                    ):
                        state["cart_items"][i]["quantity"] = quantity
                        state["cart_items"][i]["item_total"] = (
                            state["cart_items"][i]["price"] * quantity
                        )
                        print(
                            f"[INFO] Modified cart: {product_type} from {brand}, new quantity: {quantity}"
                        )
                        break

    # Clear cart
    elif "name" in tool_output and tool_output["name"] == "clear_cart":
        if "output" in tool_output and tool_output["output"].get("status") == "success":
            state["cart_items"] = []
            print(f"[INFO] Cart cleared")

    return state


# Build the graph
graph_builder = StateGraph(State)

# Add nodes
graph_builder.add_node("agent", agent_node)
graph_builder.add_node("action", tool_node)

# Set the entry point
graph_builder.set_entry_point("agent")

# Set the conditional edges
graph_builder.add_conditional_edges(
    "agent",
    should_call_tool,
    {
        "call_tool": "action",  # Route to the action node if tool call is needed
        "end": END,  # End the graph if no tool call is needed
    },
)


# Add the update_cart node and connect it to the action node
graph_builder.add_node("update_cart", update_cart_node)
graph_builder.add_edge("action", "update_cart")
graph_builder.add_edge("update_cart", "agent")

# Compile the graph
try:
    app = graph_builder.compile()
    print("[INFO] Graph compiled successfully!")
except Exception as e:
    print(f"[ERROR] Error compiling graph: {e}")
    app = None  # Set to None if an error occurs

# Make the compiled app object available to other modules (main.py)
