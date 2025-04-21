"""
Graph for the chatbot
"""

import json
import traceback

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import AIMessage, ToolMessage

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


def view_cart_node(state: State):
    """Node that directly accesses the cart from the state"""
    print("\n[INFO] View Cart Node Execution")
    # Call the modified view_cart function (pass the entire state)
    try:
        # Check if the state object or cart_items key/list exists
        if not state or "cart_items" not in state or not state["cart_items"]:
            print("[INFO] Cart is empty based on state")
            cart_result = {"status": "empty", "message": "Your cart is empty."}
        else:
            cart_items = state["cart_items"]
            # Calculate totals
            total_price = sum(float(item.get("item_total", 0)) for item in cart_items)
            item_count = sum(item.get("quantity", 1) for item in cart_items)
            # Prepare a formatted cart summary
            cart_summary = []
            for item in cart_items:
                cart_summary.append(
                    {
                        "product": f"{item.get('product_brand', 'Unknown')} {item.get('product_type', 'Unknown')}",
                        "quantity": item.get("quantity", 1),
                        "price_per_unit": f"${item.get('price', 0):.2f}",
                        "item_total": f"${item.get('item_total', 0):.2f}",
                    }
                )
            print(
                f"[INFO] Found {len(cart_items)} unique item types ({item_count} total items) in cart, total: ${total_price:.2f}"
            )
            cart_result = {
                "status": "success",
                "cart_items": cart_summary,
                "total_price": total_price,
                "item_count": item_count,
                "formatted_total": f"${total_price:.2f}",
            }
    except Exception as e:
        print(
            f"[ERROR] Exception during view_cart_node execution - {e}\n{traceback.format_exc()}"
        )
        cart_result = {"status": "error", "message": str(e)}

    # Create a ToolMessage from the result
    last_message = state["messages"][-1]
    tool_call_id = ""
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        # Find the view_cart call (typically the first or only call)
        view_cart_call = next(
            (tc for tc in last_message.tool_calls if tc.get("name") == "view_cart"),
            None,
        )
        if view_cart_call:
            tool_call_id = view_cart_call.get("id", "")
        else:
            print(
                f"[WARNING] view_cart_node reached but no 'view_cart' tool call found in last AI message. Tool calls: {last_message.tool_calls}"
            )
            # Use default ID or empty ID
            tool_call_id = (
                last_message.tool_calls[0].get("id", "")
                if last_message.tool_calls
                else ""
            )

    # Format the result as a string (JSON usage possible)
    # result_content = json.dumps(cart_result)
    # Create a string
    result_content = f"Cart status: {cart_result.get('status', 'unknown')}\n"
    if cart_result.get("status") == "success":
        items_str = ", ".join(
            [
                f"{item['quantity']}x {item['product']}"
                for item in cart_result.get("cart_items", [])
            ]
        )
        result_content += (
            f"Items ({cart_result.get('item_count', 0)} total): [{items_str}]\n"
        )
        result_content += f"Total Price: {cart_result.get('formatted_total', '$0.00')}"
    elif cart_result.get("status") == "empty":
        result_content += cart_result.get("message", "Cart is empty.")
    else:  # Error case
        result_content += f"Error: {cart_result.get('message', 'Failed to view cart.')}"

    print(f"[INFO] view_cart_node result for LLM: {result_content}")

    # Wrap the result in a ToolMessage and return
    return {
        "messages": [ToolMessage(content=result_content, tool_call_id=tool_call_id)]
    }


def should_call_tool(state: State):
    """Determine if a tool should be called based on the LLM's response"""
    print("[INFO] Checking for tool call")
    last_message = state["messages"][-1]
    # Check if the last message is an AIMessage and has tool_calls
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        # Check the first tool call name
        if last_message.tool_calls:
            first_tool_call_name = last_message.tool_calls[0].get("name")
            if first_tool_call_name == "view_cart":
                print(
                    "[INFO] Decision: 'view_cart' call required -> Routing to view_cart_node"
                )
                return "call_view_cart"
            else:
                print(
                    f"[INFO] Decision: Tool call required ({len(last_message.tool_calls)} calls, first: {first_tool_call_name}) -> Routing to action node"
                )
                return "call_tool"
        else:
            print("[INFO] Decision: No tool call required (empty tool_calls list)")
            return "end"
    else:
        print("[INFO] Decision: No tool call required (End Turn)")
        return "end"


def update_cart_node(state):
    """Updates the cart based on tool output"""
    updated_state = state.copy()  # Use a copy of the state

    # Check if the last message is a ToolMessage
    # ToolNode add the result as a ToolMessage
    last_message = updated_state["messages"][-1]
    tool_output_message = None
    if isinstance(last_message, ToolMessage):
        tool_output_message = last_message
        print(
            f"[DEBUG] update_cart_node processing ToolMessage: ID={tool_output_message.tool_call_id}, Content Snippet={tool_output_message.content[:100]}..."
        )
    else:
        print(
            f"[DEBUG] update_cart_node: Last message is not ToolMessage ({type(last_message)}), skipping cart update based on tool output."
        )
        return updated_state  # Return the unchanged state if no ToolMessage

    # Find tool_calls in the previous AI messages to identify the result of a tool call
    tool_call_info = None

    # Find the AIMessage with the matching tool_call_id in the message history
    # search excluding the last ToolMessage
    for msg in reversed(updated_state["messages"][:-1]):
        if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                if tc.get("id") == tool_output_message.tool_call_id:
                    tool_call_info = tc
                    print(
                        f"[DEBUG] Found corresponding tool call in history: {tool_call_info}"
                    )
                    break
            if tool_call_info:
                break

        if not tool_call_info:
            # Fallback: try to match ToolMessages and tool_calls by order
            print(
                f"[WARNING] update_cart_node: Could not find matching tool call for ToolMessage ID {tool_output_message.tool_call_id}. Trying order-based fallback matching..."
            )
            # Collect AIMessage/ToolMessage within the current turn (since last agent)
            ai_messages = [
                msg
                for msg in updated_state["messages"][:-1]
                if isinstance(msg, AIMessage)
            ]
            tool_messages = [
                msg
                for msg in updated_state["messages"][:-1]
                if isinstance(msg, ToolMessage)
            ]
            if ai_messages and tool_messages:
                last_ai = ai_messages[-1]
                # Fallback: try to match ToolMessages and tool_calls by tool_call_id
                idx = None
                for i, msg in enumerate(tool_messages):
                    if getattr(msg, "tool_call_id", None) == getattr(
                        tool_output_message, "tool_call_id", None
                    ):
                        idx = i
                        break
                if idx is not None and idx < len(last_ai.tool_calls):
                    tool_call_info = last_ai.tool_calls[idx]
                    print(
                        f"[DEBUG] [Fallback order-matching] Using tool_call_info via order: {tool_call_info}"
                    )
                else:
                    print(
                        "[ERROR] Could not find matching tool_call_id in tool_messages during order-based fallback."
                    )
                    return updated_state

    tool_name = tool_call_info.get("name")
    tool_args = tool_call_info.get("args", {})

    print(f"[INFO] update_cart_node triggered by tool: {tool_name}")

    # initialize cart_items
    if "cart_items" not in updated_state or not isinstance(
        updated_state["cart_items"], list
    ):
        updated_state["cart_items"] = []
        print("[DEBUG] Initialized cart_items in state.")

    # Perform cart update logic based on tool name and arguments
    try:
        tool_result = {}
        try:
            # Assume the content is a JSON string of a dict
            parsed_content = json.loads(tool_output_message.content)
            if isinstance(parsed_content, dict):
                tool_result = parsed_content
            print("[DEBUG] Successfully parsed ToolMessage content as JSON.")
        except json.JSONDecodeError:
            print(
                f"[WARNING] Could not parse ToolMessage content as JSON. Content: {tool_output_message.content}"
            )
            # Parse failure, use tool_name and tool_args for processing

        # --- Cart update logic ---
        if tool_name == "add_to_cart":
            item_to_add = (
                tool_result.get("item")
                if tool_result.get("status") == "success"
                else None
            )

            if item_to_add and isinstance(item_to_add, dict):
                # Check if the item is already in the cart
                existing_item_index = -1
                for i, item in enumerate(updated_state["cart_items"]):
                    if item.get("product_type") == item_to_add.get(
                        "product_type"
                    ) and item.get("product_brand") == item_to_add.get("product_brand"):
                        existing_item_index = i
                        break

                if existing_item_index != -1:
                    # Update the quantity and total price of the existing product
                    current_quantity = updated_state["cart_items"][
                        existing_item_index
                    ].get("quantity", 0)
                    added_quantity = item_to_add.get("quantity", 1)
                    new_quantity = current_quantity + added_quantity
                    price = updated_state["cart_items"][existing_item_index].get(
                        "price", 0
                    )

                    updated_state["cart_items"][existing_item_index][
                        "quantity"
                    ] = new_quantity
                    updated_state["cart_items"][existing_item_index]["item_total"] = (
                        price * new_quantity
                    )
                    print(
                        f"[INFO] Updated cart item quantity: {updated_state['cart_items'][existing_item_index]}"
                    )
                else:
                    # Add new product
                    updated_state["cart_items"].append(item_to_add)
                    print(f"[INFO] Added to cart: {item_to_add}")

            elif tool_result.get("status") != "success":
                print(
                    f"[INFO] add_to_cart tool did not succeed. Status: {tool_result.get('status')}, Message: {tool_result.get('message')}"
                )
            else:
                print(
                    "[WARNING] add_to_cart executed but no valid 'item' found in result."
                )

        elif tool_name == "remove_from_cart":
            # Get product info from tool_args
            product_type = tool_args.get("product_type")
            brand = tool_args.get("brand")

            if product_type:
                original_count = len(updated_state["cart_items"])
                product_type_lower = product_type.lower()
                brand_lower = brand.lower() if brand else None

                new_cart_items = []
                removed_items_desc = []

                for item in updated_state["cart_items"]:
                    item_product_lower = item.get("product_type", "").lower()
                    item_brand_lower = item.get("product_brand", "").lower()
                    matches_product = item_product_lower == product_type_lower

                    # Brand specified: both product type and brand must match
                    if brand_lower:
                        if not (matches_product and item_brand_lower == brand_lower):
                            new_cart_items.append(item)
                        else:
                            removed_items_desc.append(
                                f"{item.get('quantity')}x {item.get('product_brand')} {item.get('product_type')}"
                            )
                    # Brand not specified: only product type matches
                    else:
                        if not matches_product:
                            new_cart_items.append(item)
                        else:
                            removed_items_desc.append(
                                f"{item.get('quantity')}x {item.get('product_brand')} {item.get('product_type')}"
                            )

                if len(new_cart_items) < original_count:
                    print(f"[INFO] Removed from cart: {', '.join(removed_items_desc)}")
                    updated_state["cart_items"] = new_cart_items
                else:
                    print(
                        f"[INFO] Item to remove not found in cart: {product_type} (Brand: {brand if brand else 'Any'})"
                    )

            else:
                print("[WARNING] remove_from_cart called without product_type.")

        elif tool_name == "modify_cart":
            product_type = tool_args.get("product_type")
            brand = tool_args.get("brand")
            quantity = tool_args.get("quantity")

            if product_type and brand and quantity is not None:
                product_type_lower = product_type.lower()
                brand_lower = brand.lower()
                found = False
                new_cart_items = []
                for i, item in enumerate(updated_state["cart_items"]):
                    if (
                        item.get("product_type", "").lower() == product_type_lower
                        and item.get("product_brand", "").lower() == brand_lower
                    ):
                        found = True
                        if quantity > 0:
                            item["quantity"] = quantity
                            item["item_total"] = item.get("price", 0) * quantity
                            new_cart_items.append(item)
                            print(f"[INFO] Modified cart item: {item}")
                        else:
                            # if quantity is 0, remove the item
                            print(
                                f"[INFO] Removed item due to quantity 0: {item.get('product_brand')} {item.get('product_type')}"
                            )
                    else:
                        new_cart_items.append(item)

                if not found:
                    print(
                        f"[INFO] Item to modify not found in cart: {brand} {product_type}"
                    )

                updated_state["cart_items"] = new_cart_items

            else:
                print("[WARNING] modify_cart called with missing arguments.")

        elif tool_name == "clear_cart":
            if updated_state["cart_items"]:
                print(
                    f"[INFO] Cart cleared. Removed {len(updated_state['cart_items'])} item types."
                )
                updated_state["cart_items"] = []
            else:
                print("[INFO] Cart is already empty.")

        # after update, log cart status
        total_items = sum(
            item.get("quantity", 0) for item in updated_state["cart_items"]
        )
        total_price = sum(
            item.get("item_total", 0) for item in updated_state["cart_items"]
        )
        print(
            f"[DEBUG] Cart items after update: {len(updated_state['cart_items'])} types, {total_items} total items, total price ${total_price:.2f}"
        )

    except Exception as e:
        print(
            f"[ERROR] Error during cart update logic in update_cart_node: {e}\n{traceback.format_exc()}"
        )

    return updated_state


# Build the graph
graph_builder = StateGraph(State)

# Add nodes
graph_builder.add_node("agent", agent_node)
graph_builder.add_node("action", tool_node)
graph_builder.add_node("view_cart", view_cart_node)
graph_builder.add_node("update_cart", update_cart_node)

# Set the entry point
graph_builder.set_entry_point("agent")

# Set the conditional edges
graph_builder.add_conditional_edges(
    "agent",
    should_call_tool,
    {
        "call_tool": "action",  # tool call => action node
        "call_view_cart": "view_cart",  # view_cart call => view_cart node
        "end": END,  # no tool call => end
    },
)


# connect to update_cart node after general tool execution
graph_builder.add_edge("action", "update_cart")
# connect to agent node after cart update
graph_builder.add_edge("update_cart", "agent")
# connect to agent node after view_cart node execution
graph_builder.add_edge("view_cart", "agent")

# Compile the graph
try:
    app = graph_builder.compile()
    print("[INFO] Graph compiled successfully!")
except Exception as e:
    print(f"[ERROR] Error compiling graph: {e}")
    app = None  # Set to None if an error occurs

# Make the compiled app object available to other modules (main.py)
