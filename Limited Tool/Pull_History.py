import json
import os
import tkinter as tk
from tkinter import ttk, messagebox
from collections import defaultdict, Counter

RARITY_ORDER = ["Ultra Rare", "Super Rare", "Rare", "Common", "Unknown"]

def load_pull_history(path="pull_history.json"):
    if not os.path.exists(path):
        messagebox.showinfo("Missing File", "Returning to menu, no pull_history.json file.")
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def organize_card_data(cards):
    result = defaultdict(lambda: defaultdict(Counter))
    for card in cards:
        rarity = card.get("cardrarity", "Unknown")
        name = card.get("cardname", "Unknown Card")
        cardset = card.get("cardset", "Unknown Set")
        result[rarity][name][cardset] += 1
    return dict(sorted(result.items(), key=lambda x: RARITY_ORDER.index(x[0]) if x[0] in RARITY_ORDER else len(RARITY_ORDER)))

def populate_tree(tree, organized):
    tree.heading("#0", text="Card Pull History", anchor="w")
    for rarity, cards_by_name in organized.items():
        total = sum(sum(c.values()) for c in cards_by_name.values())
        rarity_id = tree.insert("", "end", text=f"{rarity} ({total})", open=True)
        for cardname, sets in sorted(cards_by_name.items()):
            card_total = sum(sets.values())
            card_id = tree.insert(rarity_id, "end", text=f"{cardname} ({card_total} pulled)", open=False)
            for setname, count in sets.items():
                tree.insert(card_id, "end", text=f"{count} - {setname}", open=True)

def launch(on_close_callback=None):
    root = tk.Toplevel()
    root.title("Pull History Viewer")
    root.geometry("700x600")

    def on_close():
        if on_close_callback:
            on_close_callback()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)

    cards = load_pull_history()
    if not cards:
        root.destroy()
        if on_close_callback:
            on_close_callback()
        return

    organized = organize_card_data(cards)

    tree = ttk.Treeview(root)
    tree.pack(expand=True, fill="both", padx=10, pady=10)

    populate_tree(tree, organized)

