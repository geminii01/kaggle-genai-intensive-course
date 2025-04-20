"""
Data Loader for the chatbot
"""

import pandas as pd

from chatbot.configs import DATA_FILE_PATH

data = None
available_categories = []

print("[INFO] Initializing Data Loader")
try:
    # Use the path defined in the config file
    data = pd.read_csv(DATA_FILE_PATH)
    print(f"[INFO] CSV data loaded successfully from {DATA_FILE_PATH}!")

    if not data.empty and "category_type" in data.columns:
        # Prepare the category list (unique values, lowercase, remove spaces)
        available_categories = (
            data["category_type"].astype(str).str.strip().str.lower().unique().tolist()
        )
        print(f"[INFO] Available categories: {available_categories}")
    else:
        # If the data is empty or the column is missing, print a warning
        available_categories = []
        print("[WARNING] Loaded data is empty or 'category_type' column is missing.")

except FileNotFoundError:
    print(f"[ERROR] Data file not found at {DATA_FILE_PATH}. Please check the path.")
    # If an error occurs, keep the empty list
    available_categories = []
    data = pd.DataFrame(columns=["category_type"])  # Initialize with an empty dataframe

except Exception as e:
    print(f"[ERROR] An unexpected error occurred during data loading - {e}")
    # If an error occurs, keep the empty list
    available_categories = []
    data = pd.DataFrame(columns=["category_type"])  # Initialize with an empty dataframe

print("[INFO] Data Loader Initialization Complete")

# Export the data and available categories for use in other modules (optional, wrap in a function if needed)
# Example: def get_available_categories(): return available_categories
