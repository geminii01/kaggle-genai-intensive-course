"""
Tools for the chatbot
"""

from langchain_core.tools import tool
from langchain_core.messages import ToolMessage

from typing import List, Dict, Any
from thefuzz import process
import traceback

from chatbot.data_loader import available_categories, data
from chatbot.configs import FUZZY_SCORE_THRESHOLD
from chatbot.state import State


# --- Category Search Tools ---
@tool
def search_category_by_type(category_type: str) -> dict:
    """
    Checks if a category name mentioned by the user exists in the data by finding the closest match.
    Use this tool when the user asks about the existence of a specific category (e.g., 'vegetables', 'fruits', 'dairy').
    It handles potential typos or slightly different phrasings using fuzzy matching.
    Only provide the category name as the 'category_type' argument.

    Args:
        category_type (str): The category name the user wants to check.

    Returns:
        dict: A dictionary containing the search result.
              On success (match found above threshold): {'status': 'found', 'matched_category': 'vegetables', 'input_query': 'veggies', 'score': 85}
              On failure (no similar match found): {'status': 'not_found', 'input_query': 'beverages', 'reason': '...'}
              On error: {'status': 'error', 'message': 'Error message'}
    """
    print(f"\n[INFO] Executing tool: search_category_by_type (Input: {category_type})")
    # Check if the category list is loaded
    if not available_categories:
        print("[ERROR] Category list is empty. Cannot perform search.")
        return {
            "status": "error",
            "message": "Category data could not be loaded or is empty.",
        }

    try:
        query = category_type.strip().lower()

        # Case of exact match
        if query in available_categories:
            print(f"[INFO] Result: Exact match found for category '{query}'")
            return {
                "status": "found",
                "matched_category": query,
                "input_query": category_type,
                "score": 100,
            }

        # Search for similar categories
        result = process.extractOne(query, available_categories)

        if result:
            best_match, score = result
            print(
                f"[INFO] Debug: Potential match '{best_match}' found with score {score}"
            )

            # Compare the threshold
            if score >= FUZZY_SCORE_THRESHOLD:
                print(
                    f"[INFO] Result: Closest category found: '{best_match}' (Score: {score})"
                )
                return {
                    "status": "found",
                    "matched_category": best_match,
                    "input_query": category_type,
                    "score": score,
                }
            else:
                # The threshold is not met
                print(
                    f"[INFO] Result: No similar category found for '{category_type}' (Highest score {score} < {FUZZY_SCORE_THRESHOLD})"
                )
                return {
                    "status": "not_found",
                    "input_query": category_type,
                    "reason": f'Best match "{best_match}" score {score} is below threshold {FUZZY_SCORE_THRESHOLD}.',
                }
        else:
            # Case of extractOne returned None
            print(
                f"[INFO] Result: No similar category found for '{category_type}' (extractOne returned None)"
            )
            return {
                "status": "not_found",
                "input_query": category_type,
                "reason": "extractOne returned None.",
            }

    except Exception as e:
        print(
            f"[ERROR] Exception during search_category_by_type execution - {e}\n{traceback.format_exc()}"
        )
        return {"status": "error", "message": str(e)}


@tool
def search_category_by_type_all() -> dict:
    """
    Retrieves and returns the list of all available grocery categories.
    Use this tool when the user asks for all available categories, to list all categories,
    or asks what kinds of categories exist. This tool does not require any arguments.

    Returns:
        dict: A dictionary containing the result.
              On success: {'status': 'success', 'categories': ['xxxxx', 'yyyyy', 'zzzzz', ...]}
              On failure (no categories available): {'status': 'not_found', 'message': 'No categories are available.'}
              On error: {'status': 'error', 'message': 'Error message'}
    """
    print(f"\n[INFO] Executing tool: search_category_by_type_all")
    try:
        if available_categories:
            print(f"[INFO] Result: Found {len(available_categories)} categories.")
            return {
                "status": "success",
                "categories": available_categories,
            }
        else:
            print("[INFO] Result: No categories available.")
            return {
                "status": "not_found",
                "message": "No categories are available at the moment.",
            }
    except Exception as e:
        print(
            f"[ERROR] Exception during search_category_by_type_all execution - {e}\n{traceback.format_exc()}"
        )
        return {"status": "error", "message": str(e)}


# --- Ingredient Search Tools ---
@tool
def search_multiple_ingredients(product_names: List[str]) -> dict:
    """
    Searches for information about multiple products at once.
    Use this tool when the user requests multiple products.

    Args:
        product_names (List[str]): A list of product names to search for (e.g., ["Apple", "Popcorn"])

    Returns:
        dict: A dictionary containing the search results for each product.
              On success: {'status': 'success', 'products': {product_name: product_info, ...}}
              On partial success: {'status': 'partial', 'found': {...}, 'not_found': [...]}
              On failure: {'status': 'not_found', 'message': 'Requested products not found.'}
    """
    print(
        f"\n[INFO] Executing tool: search_multiple_ingredients (Products: {product_names})"
    )

    if not product_names:
        return {"status": "error", "message": "Product name list is empty."}

    results = {"found": {}, "not_found": []}

    for product_name in product_names:
        # Call the search_ingredient_by_brand function for each product using invoke method
        product_result = search_ingredient_by_brand.invoke(product_name)

        if product_result["status"] == "success":
            # Found the product
            results["found"][product_name] = product_result
        else:
            # Not found the product
            results["not_found"].append(product_name)

    # Evaluate the search results
    if not results["found"]:
        # Not found all products
        return {
            "status": "not_found",
            "message": "Requested products not found.",
            "not_found": results["not_found"],
        }
    elif not results["not_found"]:
        # Found all products
        return {"status": "success", "products": results["found"]}
    else:
        # Found some products
        return {
            "status": "partial",
            "found": results["found"],
            "not_found": results["not_found"],
        }


@tool
def search_ingredient_by_type_all() -> dict:
    """
    Retrieves and returns the list of all available products across all categories.
    Use this tool when the user asks for all available products or ingredients.

    Returns:
        dict: A dictionary containing the result.
              On success: {'status': 'success', 'products': {'XXXXX': ['aaaaa', 'bbbbb'], 'YYYYY': ['ccccc', 'ddddd'], ...}}
              On failure: {'status': 'not_found', 'message': 'No products available.'}
              On error: {'status': 'error', 'message': 'Error message'}
    """
    print(f"\n[INFO] Executing tool: search_ingredient_by_type_all")
    try:
        if data is None or data.empty:
            print("[ERROR] Data is not available. Cannot perform search.")
            return {
                "status": "error",
                "message": "Product data could not be loaded or is empty.",
            }

        # Group products by category
        result = {}
        for category in available_categories:
            category_filter = data["category_type"].str.lower() == category.lower()
            filtered_data = data[category_filter]
            if not filtered_data.empty:
                result[category] = filtered_data["product_type"].unique().tolist()

        if not result:
            print("[INFO] No products available.")
            return {
                "status": "not_found",
                "message": "No products are available at the moment.",
            }

        print(f"[INFO] Found products in {len(result)} categories")
        return {"status": "success", "products_by_category": result}

    except Exception as e:
        print(
            f"[ERROR] Exception during search_ingredient_by_type_all execution - {e}\n{traceback.format_exc()}"
        )
        return {"status": "error", "message": str(e)}


@tool
def search_ingredient_by_brand(product_type: str, brand: str = None) -> dict:
    """
    Searches for ingredients by product type and optionally brand.
    Use this tool when the user asks about specific products from a brand or wants to know what brands are available for a product.

    Args:
        product_type (str): The product type to search for (e.g., 'Carrot', 'Milk', 'Chicken Breast').
        brand (str, optional): The brand name to filter by. If not provided, all brands for the product will be returned.

    Returns:
        dict: A dictionary containing the search results.
              On success with brand: {'status': 'success', 'product': product details}
              On success without brand: {'status': 'success', 'brands': [list of brands for the product]}
              On failure: {'status': 'not_found', 'message': 'No products found matching these criteria.'}
              On error: {'status': 'error', 'message': 'Error message'}
    """
    print(
        f"\n[INFO] Executing tool: search_ingredient_by_brand (Product: {product_type}, Brand: {brand})"
    )
    try:
        if data is None or data.empty:
            print("[ERROR] Data is not available. Cannot perform search.")
            return {
                "status": "error",
                "message": "Product data could not be loaded or is empty.",
            }

        # Search for the product (case-insensitive)
        product_type_lower = product_type.strip().lower()

        # Filter data by product type (case-insensitive)
        product_filter = data["product_type"].str.lower() == product_type_lower
        filtered_data = data[product_filter]

        if filtered_data.empty:
            # Try fuzzy matching for product type
            all_products = data["product_type"].unique().tolist()
            result = process.extractOne(
                product_type_lower, [p.lower() for p in all_products]
            )
            if result and result[1] >= FUZZY_SCORE_THRESHOLD:
                matched_product = all_products[
                    [p.lower() for p in all_products].index(result[0])
                ]
                product_filter = data["product_type"] == matched_product
                filtered_data = data[product_filter]
                print(f"[INFO] Using fuzzy matched product: {matched_product}")
            else:
                print(f"[INFO] Product not found: {product_type}")
                return {
                    "status": "not_found",
                    "message": f"Product '{product_type}' not found in our database.",
                }

        # If brand is specified, filter by brand as well
        if brand:
            brand_lower = brand.strip().lower()
            brand_filter = filtered_data["product_brand"].str.lower() == brand_lower
            brand_filtered_data = filtered_data[brand_filter]

            if brand_filtered_data.empty:
                # Try fuzzy matching for brand
                available_brands = filtered_data["product_brand"].unique().tolist()
                result = process.extractOne(
                    brand_lower, [b.lower() for b in available_brands]
                )
                if result:
                    best_match, score = result
                    if score >= FUZZY_SCORE_THRESHOLD:
                        matched_brand = available_brands[
                            [b.lower() for b in available_brands].index(best_match)
                        ]
                        brand_filter = filtered_data["product_brand"] == matched_brand
                        brand_filtered_data = filtered_data[brand_filter]
                        print(f"[INFO] Using fuzzy matched brand: {matched_brand}")
                    else:
                        print(
                            f"[INFO] Brand '{brand}' score too low, suggesting best match '{best_match}' (score {score})"
                        )
                        return {
                            "status": "not_found",
                            "message": f"Brand '{brand}' not found for product '{product_type}'. Did you mean '{best_match}'?",
                            "available_brands": available_brands,
                            "suggested_brand": best_match,
                            "match_score": score,
                        }
                else:
                    print(f"[INFO] Brand not found for product {product_type}: {brand}")
                    return {
                        "status": "not_found",
                        "message": f"Brand '{brand}' not found for product '{product_type}'.",
                        "available_brands": available_brands,
                    }

            # Return the specific product details
            product_data = brand_filtered_data.iloc[0].to_dict()
            print(f"[INFO] Found product: {product_type} from brand {brand}")
            return {"status": "success", "product": product_data}
        else:
            # Return all brands for this product
            brands = filtered_data["product_brand"].tolist()
            print(f"[INFO] Found {len(brands)} brands for product {product_type}")
            return {"status": "success", "product_type": product_type, "brands": brands}

    except Exception as e:
        print(
            f"[ERROR] Exception during search_ingredient_by_brand execution - {e}\n{traceback.format_exc()}"
        )
        return {"status": "error", "message": str(e)}


@tool
def search_ingredient_by_rating(product_type: str, min_rating: float = 0.0) -> dict:
    """
    Searches for ingredients by product type and minimum rating.
    Use this tool when the user asks about products with a specific rating or wants to find high-rated products.

    Args:
        product_type (str): The product type to search for (e.g., 'Carrot', 'Milk', 'Chicken Breast').
        min_rating (float, optional): The minimum rating to filter by (0.0-5.0). Default is 0.0 (no filtering).

    Returns:
        dict: A dictionary containing the search results.
              On success: {'status': 'success', 'products': [list of product details]}
              On failure: {'status': 'not_found', 'message': 'No products found matching these criteria.'}
              On error: {'status': 'error', 'message': 'Error message'}
    """
    print(
        f"\n[INFO] Executing tool: search_ingredient_by_rating (Product: {product_type}, Min Rating: {min_rating})"
    )
    try:
        if data is None or data.empty:
            print("[ERROR] Data is not available. Cannot perform search.")
            return {
                "status": "error",
                "message": "Product data could not be loaded or is empty.",
            }

        # Validate min_rating
        try:
            min_rating = float(min_rating)
            if min_rating < 0 or min_rating > 5:
                min_rating = 0.0  # Reset to default if invalid
                print("[WARNING] Invalid rating value. Using default value 0.0.")
        except (ValueError, TypeError):
            min_rating = 0.0  # Reset to default if conversion fails
            print("[WARNING] Invalid rating value. Using default value 0.0.")

        # Search for the product (case-insensitive)
        product_type_lower = product_type.strip().lower()

        # Filter data by product type (case-insensitive)
        product_filter = data["product_type"].str.lower() == product_type_lower
        filtered_data = data[product_filter]

        if filtered_data.empty:
            # Try fuzzy matching for product type
            all_products = data["product_type"].unique().tolist()
            result = process.extractOne(
                product_type_lower, [p.lower() for p in all_products]
            )
            if result and result[1] >= FUZZY_SCORE_THRESHOLD:
                matched_product = all_products[
                    [p.lower() for p in all_products].index(result[0])
                ]
                product_filter = data["product_type"] == matched_product
                filtered_data = data[product_filter]
                print(f"[INFO] Using fuzzy matched product: {matched_product}")
            else:
                print(f"[INFO] Product not found: {product_type}")
                return {
                    "status": "not_found",
                    "message": f"Product '{product_type}' not found in our database.",
                }

        # Filter by minimum rating
        if min_rating > 0:
            rating_filter = filtered_data["product_rating"].astype(float) >= min_rating
            filtered_data = filtered_data[rating_filter]

        if filtered_data.empty:
            print(f"[INFO] No products found with rating >= {min_rating}")
            return {
                "status": "not_found",
                "message": f"No {product_type} products found with rating {min_rating} or higher.",
            }

        # Sort by rating (highest first)
        filtered_data = filtered_data.sort_values(by="product_rating", ascending=False)

        # Convert to list of dictionaries
        products = filtered_data.to_dict("records")
        print(f"[INFO] Found {len(products)} products matching criteria")

        return {"status": "success", "products": products}

    except Exception as e:
        print(
            f"[ERROR] Exception during search_ingredient_by_rating execution - {e}\n{traceback.format_exc()}"
        )
        return {"status": "error", "message": str(e)}


@tool
def search_ingredient_by_price(product_type: str, max_price: float = None) -> dict:
    """
    Searches for ingredients by product type and maximum price.
    Use this tool when the user asks about products within a specific price range or wants to know the price of a product.

    Args:
        product_type (str): The product type to search for (e.g., 'Carrot', 'Milk', 'Chicken Breast').
        max_price (float, optional): The maximum price to filter by. If not provided, all prices are shown.

    Returns:
        dict: A dictionary containing the search results.
              On success: {'status': 'success', 'products': [list of product details]}
              On failure: {'status': 'not_found', 'message': 'No products found matching these criteria.'}
              On error: {'status': 'error', 'message': 'Error message'}
    """
    print(
        f"\n[INFO] Executing tool: search_ingredient_by_price (Product: {product_type}, Max Price: {max_price})"
    )
    try:
        if data is None or data.empty:
            print("[ERROR] Data is not available. Cannot perform search.")
            return {
                "status": "error",
                "message": "Product data could not be loaded or is empty.",
            }

        # Validate max_price
        if max_price is not None:
            try:
                max_price = float(max_price)
                if max_price <= 0:
                    max_price = None  # Reset to default if invalid
                    print("[WARNING] Invalid price value. Showing all prices.")
            except (ValueError, TypeError):
                max_price = None  # Reset to default if conversion fails
                print("[WARNING] Invalid price value. Showing all prices.")

        # Search for the product (case-insensitive)
        product_type_lower = product_type.strip().lower()

        # Filter data by product type (case-insensitive)
        product_filter = data["product_type"].str.lower() == product_type_lower
        filtered_data = data[product_filter]

        if filtered_data.empty:
            # Try fuzzy matching for product type
            all_products = data["product_type"].unique().tolist()
            result = process.extractOne(
                product_type_lower, [p.lower() for p in all_products]
            )
            if result and result[1] >= FUZZY_SCORE_THRESHOLD:
                matched_product = all_products[
                    [p.lower() for p in all_products].index(result[0])
                ]
                product_filter = data["product_type"] == matched_product
                filtered_data = data[product_filter]
                print(f"[INFO] Using fuzzy matched product: {matched_product}")
            else:
                print(f"[INFO] Product not found: {product_type}")
                return {
                    "status": "not_found",
                    "message": f"Product '{product_type}' not found in our database.",
                }

        # Filter by maximum price
        if max_price is not None:
            price_filter = filtered_data["product_price"].astype(float) <= max_price
            filtered_data = filtered_data[price_filter]

        if filtered_data.empty:
            print(f"[INFO] No products found with price <= {max_price}")
            return {
                "status": "not_found",
                "message": f"No {product_type} products found with price {max_price} or lower.",
            }

        # Sort by price (lowest first)
        filtered_data = filtered_data.sort_values(by="product_price", ascending=True)

        # Convert to list of dictionaries
        products = filtered_data.to_dict("records")
        print(f"[INFO] Found {len(products)} products matching criteria")

        return {"status": "success", "products": products}

    except Exception as e:
        print(
            f"[ERROR] Exception during search_ingredient_by_price execution - {e}\n{traceback.format_exc()}"
        )
        return {"status": "error", "message": str(e)}


@tool
def search_ingredient_by_review(
    product_type: str = None, min_reviews: int = 0, category_type: str = None
) -> dict:
    """
    Searches for ingredients by minimum review count or finds products with the most reviews.
    Use this tool when the user wants to find popular products based on review counts.

    Args:
        product_type (str, optional): The specific product type to search for. If None, will search across all products.
        min_reviews (int, optional): The minimum number of reviews to filter by. Default is 0 (no filtering).
        category_type (str, optional): The category to search within. If provided, narrows the search to this category.

    Returns:
        dict: A dictionary containing the search results.
              On success: {'status': 'success', 'products': [list of product details]}
              On failure: {'status': 'not_found', 'message': 'No products found matching these criteria.'}
              On error: {'status': 'error', 'message': 'Error message'}
    """
    print(
        f"\n[INFO] Executing tool: search_ingredient_by_review (Product: {product_type}, Min Reviews: {min_reviews}, Category: {category_type})"
    )
    try:
        if data is None or data.empty:
            print("[ERROR] Data is not available. Cannot perform search.")
            return {
                "status": "error",
                "message": "Product data could not be loaded or is empty.",
            }

        # Validate min_reviews
        try:
            min_reviews = int(min_reviews)
            if min_reviews < 0:
                min_reviews = 0  # Reset to default if invalid
                print("[WARNING] Invalid review count. Using default value 0.")
        except (ValueError, TypeError):
            min_reviews = 0  # Reset to default if conversion fails
            print("[WARNING] Invalid review count. Using default value 0.")

        # Start with all data
        filtered_data = data.copy()

        # Filter by product_type if specified
        if product_type:
            product_type_lower = product_type.strip().lower()
            product_filter = (
                filtered_data["product_type"].str.lower() == product_type_lower
            )
            product_filtered_data = filtered_data[product_filter]

            if product_filtered_data.empty:
                # Try fuzzy matching for product type
                all_products = data["product_type"].unique().tolist()
                result = process.extractOne(
                    product_type_lower, [p.lower() for p in all_products]
                )
                if result and result[1] >= FUZZY_SCORE_THRESHOLD:
                    matched_product = all_products[
                        [p.lower() for p in all_products].index(result[0])
                    ]
                    product_filter = filtered_data["product_type"] == matched_product
                    product_filtered_data = filtered_data[product_filter]
                    print(f"[INFO] Using fuzzy matched product: {matched_product}")
                else:
                    print(f"[INFO] Product not found: {product_type}")
                    return {
                        "status": "not_found",
                        "message": f"Product '{product_type}' not found in our database.",
                    }

            filtered_data = product_filtered_data

        # Filter by category if specified
        if category_type:
            category_type_lower = category_type.strip().lower()

            # Check if the category exists
            if category_type_lower not in [cat.lower() for cat in available_categories]:
                # Try fuzzy matching
                result = process.extractOne(
                    category_type_lower, [cat.lower() for cat in available_categories]
                )
                if result and result[1] >= FUZZY_SCORE_THRESHOLD:
                    category_type_lower = result[0]
                    print(f"[INFO] Using fuzzy matched category: {category_type_lower}")
                else:
                    print(f"[INFO] Category not found: {category_type}")
                    return {
                        "status": "not_found",
                        "message": f"Category '{category_type}' not found in our database.",
                    }

            # Filter by the category
            category_filter = (
                filtered_data["category_type"].str.lower() == category_type_lower
            )
            filtered_data = filtered_data[category_filter]

            if filtered_data.empty:
                print(f"[INFO] No products found in category: {category_type}")
                return {
                    "status": "not_found",
                    "message": f"No products found in category '{category_type}'.",
                }

        # Filter by minimum review count
        if min_reviews > 0:
            review_filter = filtered_data["product_review"].astype(int) >= min_reviews
            filtered_data = filtered_data[review_filter]

        if filtered_data.empty:
            print(f"[INFO] No products found with review count >= {min_reviews}")
            return {
                "status": "not_found",
                "message": f"No products found with review count {min_reviews} or higher.",
            }

        # Sort by review count (highest first)
        filtered_data = filtered_data.sort_values(by="product_review", ascending=False)

        # Convert to list of dictionaries
        products = filtered_data.to_dict("records")
        print(f"[INFO] Found {len(products)} products matching criteria")

        return {"status": "success", "products": products}

    except Exception as e:
        print(
            f"[ERROR] Exception during search_ingredient_by_review execution - {e}\n{traceback.format_exc()}"
        )
        return {"status": "error", "message": str(e)}


# --- Ingredient Comparison Tools ---
@tool
def compare_ingredient_by_rating(product_type: str) -> dict:
    """
    Compares different brands of a product by their ratings.
    Use this tool when the user wants to compare different options for a product based on ratings.

    Args:
        product_type (str): The product type to compare (e.g., 'Carrot', 'Milk', 'Chicken Breast').

    Returns:
        dict: A dictionary containing the comparison results.
              On success: {'status': 'success', 'comparisons': [list of products sorted by rating]}
              On failure: {'status': 'not_found', 'message': 'No products found for comparison.'}
              On error: {'status': 'error', 'message': 'Error message'}
    """
    print(
        f"\n[INFO] Executing tool: compare_ingredient_by_rating (Product: {product_type})"
    )
    try:
        if data is None or data.empty:
            print("[ERROR] Data is not available. Cannot perform comparison.")
            return {
                "status": "error",
                "message": "Product data could not be loaded or is empty.",
            }

        # Search for the product (case-insensitive)
        product_type_lower = product_type.strip().lower()

        # Filter data by product type (case-insensitive)
        product_filter = data["product_type"].str.lower() == product_type_lower
        filtered_data = data[product_filter]

        if filtered_data.empty:
            # Try fuzzy matching for product type
            all_products = data["product_type"].unique().tolist()
            result = process.extractOne(
                product_type_lower, [p.lower() for p in all_products]
            )
            if result and result[1] >= FUZZY_SCORE_THRESHOLD:
                matched_product = all_products[
                    [p.lower() for p in all_products].index(result[0])
                ]
                product_filter = data["product_type"] == matched_product
                filtered_data = data[product_filter]
                print(f"[INFO] Using fuzzy matched product: {matched_product}")
            else:
                print(f"[INFO] Product not found: {product_type}")
                return {
                    "status": "not_found",
                    "message": f"Product '{product_type}' not found in our database.",
                }

        if len(filtered_data) < 2:
            print(f"[INFO] Not enough products for comparison: {product_type}")
            return {
                "status": "not_found",
                "message": f"Not enough {product_type} products for comparison.",
            }

        # Sort by rating (highest first)
        filtered_data = filtered_data.sort_values(by="product_rating", ascending=False)

        # Convert to list of dictionaries
        comparisons = filtered_data.to_dict("records")
        print(f"[INFO] Compared {len(comparisons)} products by rating")

        return {"status": "success", "metric": "rating", "comparisons": comparisons}

    except Exception as e:
        print(
            f"[ERROR] Exception during compare_ingredient_by_rating execution - {e}\n{traceback.format_exc()}"
        )
        return {"status": "error", "message": str(e)}


@tool
def compare_ingredient_by_price(product_type: str) -> dict:
    """
    Compares different brands of a product by their prices.
    Use this tool when the user wants to compare different options for a product based on prices.

    Args:
        product_type (str): The product type to compare (e.g., 'Carrot', 'Milk', 'Chicken Breast').

    Returns:
        dict: A dictionary containing the comparison results.
              On success: {'status': 'success', 'comparisons': [list of products sorted by price]}
              On failure: {'status': 'not_found', 'message': 'No products found for comparison.'}
              On error: {'status': 'error', 'message': 'Error message'}
    """
    print(
        f"\n[INFO] Executing tool: compare_ingredient_by_price (Product: {product_type})"
    )
    try:
        if data is None or data.empty:
            print("[ERROR] Data is not available. Cannot perform comparison.")
            return {
                "status": "error",
                "message": "Product data could not be loaded or is empty.",
            }

        # Search for the product (case-insensitive)
        product_type_lower = product_type.strip().lower()

        # Filter data by product type (case-insensitive)
        product_filter = data["product_type"].str.lower() == product_type_lower
        filtered_data = data[product_filter]

        if filtered_data.empty:
            # Try fuzzy matching for product type
            all_products = data["product_type"].unique().tolist()
            result = process.extractOne(
                product_type_lower, [p.lower() for p in all_products]
            )
            if result and result[1] >= FUZZY_SCORE_THRESHOLD:
                matched_product = all_products[
                    [p.lower() for p in all_products].index(result[0])
                ]
                product_filter = data["product_type"] == matched_product
                filtered_data = data[product_filter]
                print(f"[INFO] Using fuzzy matched product: {matched_product}")
            else:
                print(f"[INFO] Product not found: {product_type}")
                return {
                    "status": "not_found",
                    "message": f"Product '{product_type}' not found in our database.",
                }

        if len(filtered_data) < 2:
            print(f"[INFO] Not enough products for comparison: {product_type}")
            return {
                "status": "not_found",
                "message": f"Not enough {product_type} products for comparison.",
            }

        # Sort by price (lowest first)
        filtered_data = filtered_data.sort_values(by="product_price", ascending=True)

        # Convert to list of dictionaries
        comparisons = filtered_data.to_dict("records")
        print(f"[INFO] Compared {len(comparisons)} products by price")

        return {"status": "success", "metric": "price", "comparisons": comparisons}

    except Exception as e:
        print(
            f"[ERROR] Exception during compare_ingredient_by_price execution - {e}\n{traceback.format_exc()}"
        )
        return {"status": "error", "message": str(e)}


@tool
def compare_ingredient_by_review(product_type: str) -> dict:
    """
    Compares different brands of a product by their review counts.
    Use this tool when the user wants to compare different options for a product based on popularity.

    Args:
        product_type (str): The product type to compare (e.g., 'Carrot', 'Milk', 'Chicken Breast').

    Returns:
        dict: A dictionary containing the comparison results.
              On success: {'status': 'success', 'comparisons': [list of products sorted by review count]}
              On failure: {'status': 'not_found', 'message': 'No products found for comparison.'}
              On error: {'status': 'error', 'message': 'Error message'}
    """
    print(
        f"\n[INFO] Executing tool: compare_ingredient_by_review (Product: {product_type})"
    )
    try:
        if data is None or data.empty:
            print("[ERROR] Data is not available. Cannot perform comparison.")
            return {
                "status": "error",
                "message": "Product data could not be loaded or is empty.",
            }

        # Search for the product (case-insensitive)
        product_type_lower = product_type.strip().lower()

        # Filter data by product type (case-insensitive)
        product_filter = data["product_type"].str.lower() == product_type_lower
        filtered_data = data[product_filter]

        if filtered_data.empty:
            # Try fuzzy matching for product type
            all_products = data["product_type"].unique().tolist()
            result = process.extractOne(
                product_type_lower, [p.lower() for p in all_products]
            )
            if result and result[1] >= FUZZY_SCORE_THRESHOLD:
                matched_product = all_products[
                    [p.lower() for p in all_products].index(result[0])
                ]
                product_filter = data["product_type"] == matched_product
                filtered_data = data[product_filter]
                print(f"[INFO] Using fuzzy matched product: {matched_product}")
            else:
                print(f"[INFO] Product not found: {product_type}")
                return {
                    "status": "not_found",
                    "message": f"Product '{product_type}' not found in our database.",
                }

        if len(filtered_data) < 2:
            print(f"[INFO] Not enough products for comparison: {product_type}")
            return {
                "status": "not_found",
                "message": f"Not enough {product_type} products for comparison.",
            }

        # Sort by review count (highest first)
        filtered_data = filtered_data.sort_values(by="product_review", ascending=False)

        # Convert to list of dictionaries
        comparisons = filtered_data.to_dict("records")
        print(f"[INFO] Compared {len(comparisons)} products by review count")

        return {
            "status": "success",
            "metric": "review count",
            "comparisons": comparisons,
        }

    except Exception as e:
        print(
            f"[ERROR] Exception during compare_ingredient_by_review execution - {e}\n{traceback.format_exc()}"
        )
        return {"status": "error", "message": str(e)}


# --- Shopping Cart Tools ---
# def view_cart(state_dict: dict = None) -> dict:
@tool
def view_cart() -> dict:
    """
    Shows the current contents of the shopping cart. (Dummy for LLM tool-call; handled in view_cart_node)
    """
    return {
        "status": "dummy",
        "message": "view_cart should be handled by view_cart_node!",
    }


# def view_cart(state: State) -> dict:
#     """
#     Displays the current contents of the shopping cart by directly accessing the graph state.
#     This function is intended to be called from a dedicated node in the graph, not as a standard LLM tool.

#     Args:
#         state (State): The current graph state containing cart items.

#     Returns:
#         dict: A dictionary containing the cart contents.
#               On success: {'status': 'success', 'cart_items': [list of items], 'total_price': float, 'item_count': int, 'formatted_total': str}
#               On empty cart: {'status': 'empty', 'message': 'Your cart is empty.'}
#               On error: {'status': 'error', 'message': 'Error message'}
#     """
#     print(f"\n[INFO] Executing function: view_cart (Accessing State Directly)")
#     try:
#         print(f"[DEBUG] Current state received in view_cart: {state}")

#         # Check if the state object or cart_items key/list exists
#         if not state or "cart_items" not in state or not state["cart_items"]:
#             print("[INFO] Cart is empty based on state")
#             return {"status": "empty", "message": "Your cart is empty."}

#         # Cart is not empty, process the information
#         cart_items = state["cart_items"]

#         # Calculate totals
#         total_price = sum(
#             float(item.get("item_total", 0))
#             for item in cart_items  # Use individual item totals
#         )
#         item_count = sum(item.get("quantity", 1) for item in cart_items)

#         # Prepare a formatted cart summary (more detailed)
#         cart_summary = []
#         for item in cart_items:
#             item_summary = {
#                 "product": f"{item.get('product_brand', 'Unknown')} {item.get('product_type', 'Unknown')}",
#                 "quantity": item.get("quantity", 1),
#                 "price_per_unit": f"${item.get('price', 0):.2f}",
#                 "item_total": f"${item.get('item_total', 0):.2f}",
#             }
#             cart_summary.append(item_summary)

#         print(
#             f"[INFO] Found {len(cart_items)} unique item types ({item_count} total items) in cart, total: ${total_price:.2f}"
#         )
#         return {
#             "status": "success",
#             "cart_items": cart_summary,  # formatted summary information
#             "total_price": total_price,
#             "item_count": item_count,
#             "formatted_total": f"${total_price:.2f}",
#         }

#     except Exception as e:
#         print(
#             f"[ERROR] Exception during view_cart execution - {e}\n{traceback.format_exc()}"
#         )
#         return {"status": "error", "message": str(e)}


@tool
def add_to_cart(product_type: str, brand: str, quantity: int = 1) -> dict:
    """
    Adds a product to the shopping cart.
    Use this tool when the user wants to add an item to their cart.

    Args:
        product_type (str): The product type to add (e.g., 'Carrot', 'Milk').
        brand (str): The brand of the product to add.
        quantity (int, optional): The quantity to add. Default is 1.

    Returns:
        dict: A dictionary containing the result.
              On success: {'status': 'success', 'message': 'Item added to cart.', 'item': item details}
              On failure: {'status': 'not_found', 'message': 'Product not found.'}
              On error: {'status': 'error', 'message': 'Error message'}
    """
    print(
        f"\n[INFO] Executing tool: add_to_cart (Product: {product_type}, Brand: {brand}, Quantity: {quantity})"
    )
    try:
        if data is None or data.empty:
            print("[ERROR] Data is not available. Cannot add to cart.")
            return {
                "status": "error",
                "message": "Product data could not be loaded or is empty.",
            }

        # Validate quantity
        try:
            quantity = int(quantity)
            if quantity <= 0:
                quantity = 1  # Reset to default if invalid
                print("[WARNING] Invalid quantity. Using default value 1.")
        except (ValueError, TypeError):
            quantity = 1  # Reset to default if conversion fails
            print("[WARNING] Invalid quantity. Using default value 1.")

        # Search for the product (case-insensitive)
        product_type_lower = product_type.strip().lower()
        brand_lower = brand.strip().lower()

        # Filter data by product type and brand (case-insensitive)
        product_filter = data["product_type"].str.lower() == product_type_lower
        brand_filter = data["product_brand"].str.lower() == brand_lower
        filtered_data = data[product_filter & brand_filter]

        if filtered_data.empty:
            # Try fuzzy matching
            print(f"[INFO] Product not found: {product_type} from {brand}")
            return {
                "status": "not_found",
                "message": f"Could not find {product_type} from {brand} in our database.",
            }

        # Get the product details
        product = filtered_data.iloc[0].to_dict()

        # Create cart item
        cart_item = {
            "product_type": product["product_type"],
            "product_brand": product["product_brand"],
            "price": float(product["product_price"]),
            "quantity": quantity,
            "item_total": float(product["product_price"]) * quantity,
        }

        print(
            f"[INFO] Added to cart: {quantity} {product['product_brand']} {product['product_type']}"
        )
        return {
            "status": "success",
            "message": f"Added {quantity} {product['product_brand']} {product['product_type']} to your cart.",
            "item": cart_item,
        }

    except Exception as e:
        print(
            f"[ERROR] Exception during add_to_cart execution - {e}\n{traceback.format_exc()}"
        )
        return {"status": "error", "message": str(e)}


@tool
def remove_from_cart(product_type: str, brand: str = None) -> dict:
    """
    Removes a product from the shopping cart.
    Use this tool when the user wants to remove an item from their cart.

    Args:
        product_type (str): The product type to remove (e.g., 'Carrot', 'Milk').
        brand (str, optional): The brand of the product to remove. If not provided, all brands of the product are removed.

    Returns:
        dict: A dictionary containing the result.
              On success: {'status': 'success', 'message': 'Item removed from cart.'}
              On failure: {'status': 'not_found', 'message': 'Item not found in cart.'}
              On error: {'status': 'error', 'message': 'Error message'}
    """
    print(
        f"\n[INFO] Executing tool: remove_from_cart (Product: {product_type}, Brand: {brand})"
    )
    try:
        # This would be replaced with actual state management in production
        # For now, we'll just return a success message

        print(
            f"[INFO] Removed from cart: {product_type} (Brand: {brand if brand else 'Any'})"
        )
        return {
            "status": "success",
            "message": f"Removed {product_type} {f'from {brand}' if brand else ''} from your cart.",
        }

    except Exception as e:
        print(
            f"[ERROR] Exception during remove_from_cart execution - {e}\n{traceback.format_exc()}"
        )
        return {"status": "error", "message": str(e)}


@tool
def modify_cart(product_type: str, brand: str, quantity: int) -> dict:
    """
    Modifies the quantity of a product in the shopping cart.
    Use this tool when the user wants to change the quantity of an item in their cart.

    Args:
        product_type (str): The product type to modify (e.g., 'Carrot', 'Milk').
        brand (str): The brand of the product to modify.
        quantity (int): The new quantity. Must be a positive integer.

    Returns:
        dict: A dictionary containing the result.
              On success: {'status': 'success', 'message': 'Item quantity updated.'}
              On failure: {'status': 'not_found', 'message': 'Item not found in cart.'}
              On error: {'status': 'error', 'message': 'Error message'}
    """
    print(
        f"\n[INFO] Executing tool: modify_cart (Product: {product_type}, Brand: {brand}, New Quantity: {quantity})"
    )
    try:
        # Validate quantity
        try:
            quantity = int(quantity)
            if quantity <= 0:
                print("[ERROR] Invalid quantity. Quantity must be positive.")
                return {
                    "status": "error",
                    "message": "Quantity must be a positive number.",
                }
        except (ValueError, TypeError):
            print("[ERROR] Invalid quantity. Not a number.")
            return {"status": "error", "message": "Quantity must be a valid number."}

        # This would be replaced with actual state management in production
        # For now, we'll just return a success message

        print(
            f"[INFO] Modified cart: {product_type} from {brand}, new quantity: {quantity}"
        )
        return {
            "status": "success",
            "message": f"Updated {brand} {product_type} quantity to {quantity} in your cart.",
        }

    except Exception as e:
        print(
            f"[ERROR] Exception during modify_cart execution - {e}\n{traceback.format_exc()}"
        )
        return {"status": "error", "message": str(e)}


@tool
def clear_cart() -> dict:
    """
    Clears all items from the shopping cart.
    Use this tool when the user wants to empty their cart or start fresh.

    Returns:
        dict: A dictionary containing the result.
              On success: {'status': 'success', 'message': 'Cart cleared successfully.'}
              On error: {'status': 'error', 'message': 'Error message'}
    """
    print(f"\n[INFO] Executing tool: clear_cart")
    try:
        # This would be replaced with actual state management in production
        # For now, we'll just return a success message

        print(f"[INFO] Cart cleared")
        return {"status": "success", "message": "Your cart has been cleared."}

    except Exception as e:
        print(
            f"[ERROR] Exception during clear_cart execution - {e}\n{traceback.format_exc()}"
        )
        return {"status": "error", "message": str(e)}


# --- Support and Miscellaneous Tools ---
@tool
def help() -> dict:
    """
    Provides help information about the chatbot capabilities.
    Use this tool when the user asks for help or guidance on how to use the chatbot.

    Returns:
        dict: A dictionary containing help information.
              {'status': 'success', 'help_info': help information}
    """
    print(f"\n[INFO] Executing tool: help")
    try:
        help_info = {
            "available_features": [
                "Search for product categories",
                "Search for specific products",
                "Compare products by price, rating, or reviews",
                "Add products to your shopping cart",
                "View, modify, or clear your shopping cart",
            ],
            "example_queries": [
                "What categories do you have?",
                "Show me all vegetables",
                "What brands of milk do you have?",
                "What's the cheapest brand of chicken?",
                "Add 2 FreshFarm carrots to my cart",
                "Show me my cart",
                "Remove apples from my cart",
            ],
        }

        print(f"[INFO] Help information provided")
        return {"status": "success", "help_info": help_info}

    except Exception as e:
        print(
            f"[ERROR] Exception during help execution - {e}\n{traceback.format_exc()}"
        )
        return {"status": "error", "message": str(e)}


@tool
def greeting() -> dict:
    """
    Handles user greetings and provides a welcome message with featured products.
    Use this tool when the user greets the chatbot or starts a new conversation.

    Returns:
        dict: A dictionary containing greeting information.
              {'status': 'success', 'greeting': greeting message, 'featured_products': list of featured products}
    """
    print(f"\n[INFO] Executing tool: greeting")
    try:
        # Get some featured products (random selection)
        featured_products = []
        if data is not None and not data.empty:
            # Sample products from different categories
            for category in available_categories[:3]:  # Limit to 3 categories
                category_filter = data["category_type"].str.lower() == category.lower()
                category_data = data[category_filter]
                if not category_data.empty:
                    # Get highest rated product in this category
                    top_product = (
                        category_data.sort_values(by="product_rating", ascending=False)
                        .iloc[0]
                        .to_dict()
                    )
                    featured_products.append(top_product)

        greeting_info = {
            "welcome_message": "Welcome to our Online Grocery Store! How can I help you today?",
            "featured_products": featured_products,
        }

        print(
            f"[INFO] Greeting provided with {len(featured_products)} featured products"
        )
        return {"status": "success", "greeting_info": greeting_info}

    except Exception as e:
        print(
            f"[ERROR] Exception during greeting execution - {e}\n{traceback.format_exc()}"
        )
        return {"status": "error", "message": str(e)}


@tool
def fallback() -> dict:
    """
    Handles unrecognized user intents or requests for unsupported features.
    This tool is called when the chatbot cannot understand the user's request
    or when the request corresponds to a feature that is not implemented.
    Provides helpful suggestions in English for what the user can try next.

    Returns:
        dict: A dictionary containing fallback information and suggestions.
              e.g., {'status': 'success', 'fallback_info': {'message': '...', 'suggestions': [...]}}
              On error: {'status': 'error', 'message': 'Error message'}
    """
    print(f"\n[INFO] Executing tool: fallback")
    try:
        fallback_info = {
            "message": (
                "I'm sorry, I couldn't quite understand your request, or it might be about a feature I don't support yet. "
                "Perhaps you could try one of the things I can help with?"
            ),
            "suggestions": [
                "🔍 Browse product categories (e.g., 'Show me the vegetable category')",
                "🔍 Search for specific products (e.g., 'Find Brand A milk')",
                "🛒 Check your shopping cart (e.g., 'View my cart')",
                "❓ Ask for help (e.g., 'help', 'how to use')",
            ],
        }

        print(
            f"[INFO] Fallback provided with enhanced English message and suggestions."
        )
        return {"status": "success", "fallback_info": fallback_info}

    except Exception as e:
        print(
            f"[ERROR] Exception during fallback execution - {e}\n{traceback.format_exc()}"
        )
        return {"status": "error", "message": str(e)}


# --- Combine all tools ---
all_tools = [
    # Category Search Tools
    search_category_by_type,
    search_category_by_type_all,
    # Ingredient Search Tools
    search_multiple_ingredients,
    search_ingredient_by_type_all,
    search_ingredient_by_brand,
    search_ingredient_by_rating,
    search_ingredient_by_price,
    search_ingredient_by_review,
    # Ingredient Comparison Tools
    compare_ingredient_by_rating,
    compare_ingredient_by_price,
    compare_ingredient_by_review,
    # Shopping Cart Tools
    view_cart,
    add_to_cart,
    remove_from_cart,
    modify_cart,
    clear_cart,
    # Support and Miscellaneous Tools
    help,
    greeting,
    fallback,
]

# Print loaded tools for confirmation
print(f"[INFO] Tools List Loaded: {[t.name for t in all_tools]}")
