import os

cards = [
    "The Fool", "The Fool", "The Magician", "The Magician", "The High Priestess", "The High Priestess",
    "The Empress", "The Empress", "The Emperor", "The Emperor", "The Hierophant", "The Hierophant",
    "The Lovers", "The Lovers", "The Chariot", "The Chariot", "Strength", "Strength", "The Hermit",
    "The Hermit", "Wheel of Fortune", "Wheel of Fortune", "Justice", "Justice", "The Hanged Man",
    "The Hanged Man", "Death", "Death", "Temperance", "Temperance", "The Devil", "The Devil",
    "The Tower", "The Tower", "The Star", "The Star", "The Moon", "The Moon", "The Sun", "The Sun",
    "Judgement", "Judgement", "The World", "The World", "Ace of Wands", "Two of Wands", "Two of Wands",
    "Three of Wands", "Three of Wands", "Four of Wands", "Four of Wands", "Five of Wands", "Five of Wands",
    "Six of Wands", "Six of Wands", "Seven of Wands", "Seven of Wands", "Eight of Wands", "Eight of Wands",
    "Nine of Wands", "Nine of Wands", "Ten of Wands", "Ten of Wands", "Page of Wands", "Page of Wands",
    "Knight of Wands", "Knight of Wands", "Queen of Wands", "Queen of Wands", "King of Wands", "King of Wands", 
    "Ace of Cups", "Two of Cups", "Two of Cups", "Three of Cups", "Three of Cups", "Four of Cups", "Four of Cups", 
    "Five of Cups", "Five of Cups", "Six of Cups", "Six of Cups", "Seven of Cups", "Seven of Cups", "Eight of Cups", 
    "Eight of Cups", "Nine of Cups", "Nine of Cups", "Ten of Cups", "Ten of Cups", "Page of Cups", "Page of Cups", 
    "Knight of Cups", "Knight of Cups", "Queen of Cups", "Queen of Cups", "King of Cups", "King of Cups",
    "Ace of Swords", "Ace of Swords", "Two of Swords", "Two of Swords", "Three of Swords", "Three of Swords",
    "Four of Swords", "Four of Swords", "Five of Swords", "Five of Swords", "Six of Swords", "Six of Swords",
    "Seven of Swords", "Seven of Swords", "Eight of Swords", "Eight of Swords", "Nine of Swords", "Nine of Swords",
    "Ten of Swords", "Ten of Swords", "Page of Swords", "Page of Swords", "Knight of Swords", "Knight of Swords",
    "Queen of Swords", "Queen of Swords", "King of Swords", "King of Swords", "Ace of Pentacles", "Ace of Pentacles",
    "Two of Pentacles", "Two of Pentacles", "Three of Pentacles", "Three of Pentacles", "Four of Pentacles", 
    "Four of Pentacles", "Five of Pentacles", "Five of Pentacles", "Six of Pentacles", "Six of Pentacles", 
    "Seven of Pentacles", "Seven of Pentacles", "Eight of Pentacles", "Eight of Pentacles", "Nine of Pentacles", 
    "Nine of Pentacles", "Ten of Pentacles", "Ten of Pentacles", "Page of Pentacles", "Page of Pentacles", 
    "Knight of Pentacles", "Knight of Pentacles", "Queen of Pentacles", "Queen of Pentacles", "King of Pentacles", 
    "King of Pentacles"
]

# Filter unique cards while maintaining the order
seen = set()
unique_cards = []
for card in cards:
    if card not in seen:
        unique_cards.append(card)
        seen.add(card)

# Path to the directory containing the jpg files
directory = os.getcwd()

# Get a list of all jpg files in the directory
jpg_files = [file for file in os.listdir(directory) if file.lower().endswith('.jpg')]

# Sort jpg_files based on the numerical part of their names (assuming 2 digits at positions 0 and 1)
jpg_files.sort(key=lambda x: int(x[:2]))

print(f"Found {len(jpg_files)} jpg files.")
print(f"Found {len(unique_cards)} unique cards.")

# Check if the number of jpg files matches the number of new names
if len(jpg_files) != len(unique_cards):
    print("Error: The number of jpg files does not match the number of new names.")
else:
    for i, file_name in enumerate(jpg_files):
        new_name = f"{unique_cards[i]}.jpg"
        old_file_path = os.path.join(directory, file_name)
        new_file_path = os.path.join(directory, new_name)
        os.rename(old_file_path, new_file_path)
        print(f"Renamed '{file_name}' to '{new_name}'")

print("Renaming completed.")
