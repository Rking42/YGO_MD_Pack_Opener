import json
from collections import OrderedDict

def remove_duplicate_sets_fast(data, set_size=8):
    unique_data = []
    seen_hashes = OrderedDict()  # Preserves insertion order
    
    # Iterate in steps of 8
    for i in range(0, len(data), set_size):
        current_set = data[i:i+set_size]
        if len(current_set) != set_size:
            unique_data.extend(current_set)  # Add leftover cards
            break
        
        # Create a unique hash for this set (order-sensitive)
        set_hash = hash(tuple(json.dumps(card, sort_keys=True) for card in current_set))
        
        if set_hash not in seen_hashes:
            seen_hashes[set_hash] = True
            unique_data.extend(current_set)
    
    return unique_data

# Example Usage:
with open('pull_history1.json', 'r') as f:
    cards = json.load(f)

cleaned_cards = remove_duplicate_sets_fast(cards)

with open('cleaned_cards.json', 'w') as f:
    json.dump(cleaned_cards, f, indent=2)