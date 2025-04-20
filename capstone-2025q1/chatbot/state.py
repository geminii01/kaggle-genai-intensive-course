"""
State for the chatbot
"""

from typing import TypedDict, Annotated, List, Optional, Dict, Any

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


# Define the state for the chatbot
class State(TypedDict):
    # Message storage
    messages: Annotated[List[BaseMessage], add_messages]

    # Current product information
    category_type: Optional[str]  # Product category
    product_type: Optional[str]  # Product type
    product_brand: Optional[str]  # Product brand
    product_rating: Optional[float]  # Product rating
    product_review: Optional[int]  # Number of product reviews
    product_price: Optional[float]  # Product price

    # Shopping cart
    cart_items: List[Dict[str, Any]]  # List of items in the cart

    # Transaction status
    finished: Optional[bool]  # Whether the transaction is complete
