import json
import os

def read_and_categorize_clipboard():
    """
    Reads the clipboard history from a file, categorizes items into
    'Favourites' and 'Regular', and prints the result.
    """
    # Construct the full path to the registry file
    home_dir = os.path.expanduser("~")
    registry_path = os.path.join(home_dir, ".cache", "clipboard-indicator@tudmotu.com", "registry.txt")

    try:
        with open(registry_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: The file was not found at {registry_path}")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from the file at {registry_path}")
        return
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return

    favourites = []
    regular = []

    for item in data:
        content = item.get("contents", "").strip()
        if item.get("favorite"):
            favourites.append(content)
        else:
            regular.append(content)

    # Using a dictionary to hold the categorized lists
    categorized_data = {
        "Favourites": favourites,
        "Regular": regular
    }

    # Printing the dictionary in a JSON-like string format
    print(json.dumps(categorized_data, indent=4))

if __name__ == "__main__":
    read_and_categorize_clipboard()
