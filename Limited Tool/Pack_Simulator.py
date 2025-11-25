import csv
import json
import os
import random
import tkinter as tk
from collections import defaultdict
from tkinter import filedialog, messagebox
from datetime import datetime
import pandas as pd

class PackOpener:
    higher_rarity_weights = {
        "Ultra Rare": 10,
        "Super Rare": 20,
        "Rare": 70
    }

    def __init__(self, root):
        self.root = root
        self.card_pool = defaultdict(list)
        self.all_pulled_cards = []
        self.set_name = ""
        self.output_text = None
        self.packs_opened_label = None
        self.packs_to_open_entry = None
        self.history_file = "pull_history.json"
        self.card_file = "pulled_cards.csv"
        self.session_pulled_cards = []
        self.counter_file = "pack_counter.json"
        self.current_pack_count = 0

    def load_card_pool(self, filename):
        self.card_pool.clear()
        try:
            with open(filename, newline='', encoding='utf-8-sig') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    try:
                        card_name = row.get("cardname", "").strip()
                        rarity = row.get("cardrarity", "").strip()
                        card_id = row.get("cardid", "").strip()
                        card_code = row.get("cardcode", "").strip()

                        if not card_name or rarity not in {
                            "Ultra Rare", "Super Rare", "Rare", "Common", 
                            "Ghost Rare", "Starlight Rare", "Collector's Rare",
                            "Quarter Century Secret Rare", "Duel Terminal Ultra Parallel Rare"
                        }:
                            continue

                        card_code = card_code if card_code else ""
                        card_id = card_id if card_id else ""

                        self.card_pool[rarity].append({
                            "name": card_name,
                            "id": card_id,
                            "code": card_code
                        })
                    except Exception as e:
                        print(f"Error processing row: {row}. Error: {str(e)}")
                        continue
                    
            self.set_name = os.path.splitext(os.path.basename(filename))[0].replace("_", " ").title()
            return True
        except Exception as e:
            print(f"Error loading file: {str(e)}")
            return False

    def get_random_card(self, rarity):
        return random.choice(self.card_pool[rarity])

    def choose_higher_rarity(self):
        rarities = list(self.higher_rarity_weights.keys())
        weights = list(self.higher_rarity_weights.values())
        return random.choices(rarities, weights=weights, k=1)[0]

    def open_master_duel_pack(self):
        pack = []
        for _ in range(5):
            card = self.get_random_card("Common")
            pack.append(("Common", card, self.set_name))
        for _ in range(3):
            rarity = self.choose_higher_rarity()
            card = self.get_random_card(rarity)
            pack.append((rarity, card, self.set_name))
        self.all_pulled_cards.extend(pack)
        self.session_pulled_cards.extend(pack)
        return pack

    def write_pull_history(self):
        if not self.session_pulled_cards:
            return

        history = []
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        history = data
                    else:
                        history = []
            except Exception:
                history = []

        for rarity, card, set_name in self.session_pulled_cards:
            history.append({
                "cardname": card["name"],
                "cardrarity": rarity,
                "cardset": set_name,
                "cardcode": card.get("code", ""),
                "cardid": card.get("id", "")
            })

        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)

        self.session_pulled_cards.clear()

    def display_pack(self, pack, pack_number):
        self.output_text.insert(tk.END, f"\nOpened the {self.set_name} Pack:\n\n")
        for rarity, card, _ in pack:
            self.output_text.insert(tk.END, f"[{rarity}] {card['name']}\n")
        self.output_text.insert(tk.END, f"\nOpened Pack (#{pack_number})\n")
        self.output_text.see(tk.END)

    def select_csv_file_gui(self):
        root = tk.Tk()
        root.withdraw()
        return filedialog.askopenfilename(title="Select a Pack CSV", filetypes=[("CSV Files", "*.csv")])

    def read_pack_count(self):
        if os.path.exists(self.counter_file):
            try:
                with open(self.counter_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("pack_count", 0)
            except Exception:
                return 0
        return 0

    def write_pack_count(self, count):
        with open(self.counter_file, "w", encoding="utf-8") as f:
            json.dump({"pack_count": count}, f)

    def update_packs_opened_label(self, count=None):
        if count is None:
            count = self.current_pack_count
        self.packs_opened_label.config(text=f"Total Packs Opened: {count}")


    def read_existing_card_pulls(self):
        pulls = defaultdict(int)
        if not os.path.exists(self.card_file):
            return pulls
        with open(self.card_file, mode='r', encoding='utf-8-sig', newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                key = (
                    row['cardname'],
                    row['cardrarity'],
                    row['cardset'],
                    row['cardcode'],
                    row['cardid']
                )
                pulls[key] += int(row['cardq'])
        return pulls

    def save_card_pulls(self, pulls):
        try:
            with open(self.card_file, mode='w', encoding='utf-8-sig', newline='') as file:
                writer = csv.writer(file, lineterminator='\r')
                writer.writerow([
                    "cardname", "cardq", "cardrarity", "card_edition",
                    "cardset", "cardcode", "cardid", "print_id"
                ])

                for (cardname, rarity, set_name, cardcode, cardid), count in sorted(pulls.items()):
                    writer.writerow([
                        cardname, count, rarity, "Unlimited",
                        set_name, cardcode, cardid, ""
                    ])
            return True
        except Exception as e:
            print(f"Error saving card pulls: {str(e)}")
            return False

    def auto_save_pulled_cards(self, packs_opened_this_time):
        if not self.all_pulled_cards:
            return

        pulls = self.read_existing_card_pulls()

        session_counts = defaultdict(int)
        for rarity, card, set_name in self.all_pulled_cards:
            key = (card["name"], rarity, set_name, card["code"], card["id"])
            session_counts[key] += 1

        for key, count in session_counts.items():
            pulls[key] += count

        if self.save_card_pulls(pulls):
            total_packs = self.read_pack_count() + packs_opened_this_time
            self.write_pack_count(total_packs)
            self.output_text.insert(tk.END, f"\nSaved {packs_opened_this_time} pack(s) to pulled_cards.csv\n")
        else:
            self.output_text.insert(tk.END, "\nFailed to save pulled cards!\n")

        self.output_text.see(tk.END)
        self.update_packs_opened_label()
        self.all_pulled_cards.clear()
        self.write_pull_history()
        self.write_pack_count(self.current_pack_count)

    def reset_pack_counter(self):
        if os.path.exists(self.history_file):
            os.makedirs("pull_logs", exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            archived_file = os.path.join("pull_logs", f"pull_history_{timestamp}.json")
            os.rename(self.history_file, archived_file)
            self.output_text.insert(tk.END, f"\nArchived pull history to {archived_file}\n")

        self.write_pack_count(0)
        self.session_pulled_cards.clear()
        self.current_pack_count = 0

        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump([], f)

        self.output_text.insert(tk.END, "\nPack counter reset to 0.\n")
        self.output_text.see(tk.END)
        self.update_packs_opened_label()

    def run_gui(self, on_close_callback=None):
        #root = tk.Tk()
        self.root.title("Yu-Gi-Oh! Pack Opener")

        def on_close():
            if on_close_callback:
                on_close_callback()
            self.root.destroy()


        self.output_text = tk.Text(self.root, height=20, width=60)
        self.output_text.pack(padx=10, pady=10)

        control_frame = tk.Frame(self.root)
        control_frame.pack(pady=5)

        def load_csv():
            filename = self.select_csv_file_gui()
            if filename:
                if self.load_card_pool(filename):
                    self.output_text.insert(tk.END, f"\nLoaded card pool from {self.set_name}\n")
                else:
                    self.output_text.insert(tk.END, f"Failed to load card pool from {filename}\n")
            else:
                self.output_text.insert(tk.END, "No file selected.\n")

        tk.Button(control_frame, text="Load Pack CSV", command=load_csv).grid(row=0, column=0, padx=5)

        tk.Label(control_frame, text="Packs to open:").grid(row=0, column=1, padx=5)
        self.packs_to_open_entry = tk.Entry(control_frame, width=5)
        self.packs_to_open_entry.insert(0, "1")
        self.packs_to_open_entry.grid(row=0, column=2, padx=5)

        def open_packs():
            if not self.card_pool:
                messagebox.showwarning("Warning", "Please load a pack CSV first.")
                return
            try:
                num_packs = int(self.packs_to_open_entry.get())
                if num_packs < 1:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Enter a valid number of packs.")
                return

            start_count = self.current_pack_count
            self.current_pack_count += num_packs

            for i in range(num_packs):
                pack = self.open_master_duel_pack()
                self.display_pack(pack, start_count + i + 1)

            self.write_pack_count(self.current_pack_count)
            self.update_packs_opened_label(self.current_pack_count)
            self.auto_save_pulled_cards(num_packs)


        tk.Button(control_frame, text="Open Packs", command=open_packs).grid(row=0, column=3, padx=5)
        tk.Button(control_frame, text="Reset Counter", command=self.reset_pack_counter).grid(row=0, column=4, padx=5)
        tk.Button(control_frame, text="Exit", command=on_close).grid(row=0, column=5, padx=5)

        self.packs_opened_label = tk.Label(self.root, text="Total Packs Opened: 0")
        self.packs_opened_label.pack(pady=5)

        self.current_pack_count = self.read_pack_count()
        self.update_packs_opened_label()


def launch(on_close_callback=None):
    root = tk.Tk()
    app = PackOpener(root)
    
    def on_close():
        if on_close_callback:
            on_close_callback()
        root.quit()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_close)
    app.run_gui(on_close_callback=on_close_callback)
    root.mainloop()



if __name__ == "__main__":
    launch()