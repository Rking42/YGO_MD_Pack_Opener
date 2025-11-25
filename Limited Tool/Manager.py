import csv
import tkinter as tk
from tkinter import filedialog, messagebox
from collections import defaultdict
import requests
import re
import urllib.parse
from bs4 import BeautifulSoup
import os

class CollectionManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Yu-Gi-Oh! Collection Manager")
        self.on_close_callback = None

        tk.Label(root, text="Search:").pack(anchor="w", padx=5, pady=(5, 0))
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(root, textvariable=self.search_var)
        self.search_entry.pack(fill="x", padx=5)
        self.search_var.trace_add("write", lambda *args: self.update_list())

        list_frame = tk.Frame(root)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.listbox = tk.Listbox(list_frame)
        self.listbox.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(list_frame, command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=scrollbar.set)

        add_frame = tk.Frame(root, relief=tk.RIDGE, borderwidth=1)
        add_frame.pack(side="bottom", fill="x", padx=5, pady=5)

        tk.Label(add_frame, text="Card Name:").grid(row=0, column=0, padx=5, pady=2)
        self.add_name_entry = tk.Entry(add_frame)
        self.add_name_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")

        tk.Label(add_frame, text="Quantity:").grid(row=0, column=2, padx=5, pady=2)
        self.add_qty_entry = tk.Entry(add_frame, width=5)
        self.add_qty_entry.grid(row=0, column=3, padx=5, pady=2)

        tk.Label(add_frame, text="Set Name:").grid(row=0, column=4, padx=5, pady=2)
        self.add_set_entry = tk.Entry(add_frame)
        self.add_set_entry.grid(row=0, column=5, padx=5, pady=2, sticky="ew")

        add_button = tk.Button(add_frame, text="Add Card", command=self.add_card)
        add_button.grid(row=0, column=6, padx=5, pady=2)

        self.crafted_var = tk.BooleanVar(value=False)
        crafted_checkbox = tk.Checkbutton(
            add_frame, 
            text="Crafted Card", 
            variable=self.crafted_var,
            command=self._toggle_set_entry
        )
        crafted_checkbox.grid(row=1, column=5, padx=5, pady=2, sticky="w")
        self._toggle_set_entry()

        exit_button = tk.Button(add_frame, text="Exit", command=self._close_window)
        exit_button.grid(row=1, column=6, padx=5, pady=2, sticky="e")

        whitelist_button = tk.Button(add_frame, text="Export Whitelist", command=self.generate_whitelist_from_file)
        whitelist_button.grid(row=1, column=0, columnspan=4, padx=5, pady=(5, 5), sticky="ew")

        add_frame.columnconfigure(1, weight=3)
        add_frame.columnconfigure(5, weight=2)

        self.collection = {}

        default_csv = "pulled_cards.csv"
        if os.path.exists(default_csv):
            self.load_csv_from_path(default_csv)

        menubar = tk.Menu(root)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Load CSV", command=self.load_csv)
        filemenu.add_command(label="Save CSV", command=self.save_csv)
        menubar.add_cascade(label="File", menu=filemenu)
        root.config(menu=menubar)

        #self.remove_card_button = tk.Button(self.root, text="Remove Card", command=self.remove_card_popup)
        #self.remove_card_button.pack()
        self.default_csv_path = default_csv

        self.remove_card_button = tk.Button(
            self.root, 
            text="Remove Card", 
            command=self.remove_selected_card
        )
        self.remove_card_button.pack()

        self.listbox.config(selectmode=tk.SINGLE)


    def remove_selected_card(self):
        selected = self.listbox.curselection()
        if not selected:
            messagebox.showerror("Error", "Please select a card to remove")
            return
        
        selected_text = self.listbox.get(selected[0])
        
        try:
            cardname = selected_text.split(" - Total:")[0].strip()
            
            matching_entries = [(name, setname) for (name, setname) in self.collection.keys() if name == cardname]
            
            if not matching_entries:
                messagebox.showerror("Error", "Selected card not found in collection")
                return
            
            if len(matching_entries) == 1:
                setname = matching_entries[0][1]
                self._remove_card_from_set(cardname, setname)
            else:
                self._show_set_selection_popup(cardname, matching_entries)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to parse selection: {str(e)}")

    def _remove_card_from_set(self, cardname, setname, quantity=1):
        key = (cardname, setname)
        if key in self.collection:
            current_qty = self.collection[key]["quantity"]
            if quantity >= current_qty:
                del self.collection[key]
            else:
                self.collection[key]["quantity"] -= quantity
            
            self.update_list()
            self.autosave_csv()
        else:
            messagebox.showerror("Error", "Card not found in specified set")

    def _show_set_selection_popup(self, cardname, matching_entries):
        popup = tk.Toplevel(self.root)
        popup.title("Select Set to Remove From")
        
        tk.Label(popup, text=f"Select set for: {cardname}").pack(pady=5)
        
        set_var = tk.StringVar()
        set_dropdown = tk.OptionMenu(
            popup, 
            set_var, 
            *[setname for (_, setname) in matching_entries]
        )
        set_dropdown.pack(pady=5)
        set_var.set(matching_entries[0][1])
        
        tk.Label(popup, text="Quantity to remove:").pack()
        qty_var = tk.IntVar(value=1)
        qty_spin = tk.Spinbox(popup, from_=1, to=100, textvariable=qty_var)
        qty_spin.pack(pady=5)
        
        def confirm_remove():
            setname = set_var.get()
            qty = qty_var.get()
            self._remove_card_from_set(cardname, setname, qty)
            popup.destroy()
        
        tk.Button(popup, text="Remove", command=confirm_remove).pack(side=tk.LEFT, padx=5)
        tk.Button(popup, text="Cancel", command=popup.destroy).pack(side=tk.RIGHT, padx=5)

    def remove_card_popup(self):
        selected_index = self.listbox.curselection()
        if not selected_index:
            messagebox.showerror("Error", "Please select a card to remove.")
            return

        selected_text = self.listbox.get(selected_index)
        cardname = selected_text.split(" (")[0]

        matching_entries = [(name, setname, data) for (name, setname), data in self.collection.items() if name == cardname]

        if not matching_entries:
            messagebox.showerror("Error", "Card not found in collection.")
            return

        popup = tk.Toplevel(self.root)
        popup.title("Remove Card")

        tk.Label(popup, text=f"Card: {cardname}").pack()

        tk.Label(popup, text="Select Set:").pack()
        set_var = tk.StringVar()
        set_dropdown = tk.Combobox(popup, textvariable=set_var, values=[s for _, s, _ in matching_entries])
        set_dropdown.pack()
        set_dropdown.current(0)

        tk.Label(popup, text="Quantity to remove:").pack()
        quantity_var = tk.IntVar(value=1)
        quantity_spinbox = tk.Spinbox(popup, from_=1, to=100, textvariable=quantity_var)
        quantity_spinbox.pack()

        def confirm_removal():
            selected_set = set_var.get()
            qty_to_remove = quantity_var.get()

            key = (cardname, selected_set)
            if key in self.collection:
                current_qty = self.collection[key]["quantity"]
                new_qty = current_qty - qty_to_remove
                if new_qty <= 0:
                    del self.collection[key]
                else:
                    self.collection[key]["quantity"] = new_qty

                self.update_list()
                self.autosave_csv()
                popup.destroy()
            else:
                messagebox.showerror("Error", "Selected card and set not found.")

        tk.Button(popup, text="Remove", command=confirm_removal).pack()
        tk.Button(popup, text="Cancel", command=popup.destroy).pack()

    def _toggle_set_entry(self):
        if self.crafted_var.get():
            self.add_set_entry.config(state="disabled")
            self.add_set_entry.delete(0, tk.END)
            self.add_set_entry.insert(0, "Crafted Card")
        else:
            self.add_set_entry.config(state="normal")

    def _close_window(self):
        if self.on_close_callback:
            self.on_close_callback()
        self.root.destroy()

    def load_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not path:
            return

        try:
            with open(path, newline='', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                self.collection.clear()
                for row in reader:
                    name = row.get("cardname", "").strip()
                    qty = row.get("cardq", "0").strip()
                    setname = row.get("cardset", "Unknown Set").strip()

                    rarity = row.get("cardrarity", "Unknown")
                    edition = row.get("cardedition", "Unlimited")
                    cardid = row.get("cardid", "")
                    cardcode = row.get("cardcode", "")
                    print_id = row.get("print_id", "")

                    if name:
                        try:
                            qty_int = int(qty)
                        except ValueError:
                            qty_int = 0
                        key = (name, setname)
                        if key not in self.collection:
                            self.collection[key] = {
                                "quantity": 0,
                                "rarity": rarity,
                                "edition": edition,
                                "cardid": cardid,
                                "cardcode": cardcode,
                                "print_id": print_id
                            }
                        self.collection[key]["quantity"] += qty_int

            self.update_list()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load CSV: {e}")
    
    def load_csv_from_path(self, path):
        try:
            with open(path, newline='', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                self.collection.clear()
                for row in reader:
                    name = row.get("cardname", "").strip()
                    qty = row.get("cardq", "0").strip()
                    setname = row.get("cardset", "Unknown Set").strip()
                    rarity = row.get("cardrarity", "Unknown")
                    edition = row.get("cardedition", "Unlimited")
                    cardid = row.get("cardid", "")
                    cardcode = row.get("cardcode", "")
                    print_id = row.get("print_id", "")

                    if name:
                        try:
                            qty_int = int(qty)
                        except ValueError:
                            qty_int = 0
                        key = (name, setname)
                        if key not in self.collection:
                            self.collection[key] = {
                                "quantity": 0,
                                "rarity": rarity,
                                "edition": edition,
                                "cardid": cardid,
                                "cardcode": cardcode,
                                "print_id": print_id
                            }
                        self.collection[key]["quantity"] += qty_int

            self.update_list()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load CSV from {path}: {e}")


    def save_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                            filetypes=[("CSV files", "*.csv")])
        if not path:
            return

        try:
            with open(path, mode="w", newline="", encoding='utf-8-sig') as f:
                fieldnames = ["cardname", "cardq", "cardrarity", "card_edition", "cardset", "cardcode", "cardid", "print_id"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for (cardname, setname), data in sorted(self.collection.items()):
                    card_id = data.get("cardid", "")
                    cardset_prefix = setname[:3].upper() 

                    cardcode = f"{cardset_prefix}{card_id}" if card_id else 0
                    cardid_field = card_id if card_id else "unlisted"

                    writer.writerow({
                        "cardname": cardname,
                        "cardq": data.get("quantity", 0),
                        "cardrarity": data.get("rarity", "Unknown"),
                        "card_edition": data.get("edition", "Unlimited"),
                        "cardset": setname,
                        "cardcode": cardcode,
                        "cardid": cardid_field,
                        "print_id": data.get("print_id", "")
                    })
            messagebox.showinfo("Success", f"Collection saved to {path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save CSV: {e}")

    def autosave_csv(self):
        try:
            with open(self.default_csv_path, mode="w", newline="", encoding='utf-8-sig') as f:
                fieldnames = ["cardname", "cardq", "cardrarity", "card_edition", "cardset", "cardcode", "cardid", "print_id"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for (cardname, setname), data in sorted(self.collection.items()):
                    card_id = data.get("cardid", "")
                    cardset_prefix = setname[:3].upper()
                    cardcode = f"{cardset_prefix}{card_id}" if card_id else 0
                    cardid_field = card_id if card_id else "unlisted"
                    writer.writerow({
                        "cardname": cardname,
                        "cardq": data.get("quantity", 0),
                        "cardrarity": data.get("rarity", "Unknown"),
                        "card_edition": data.get("edition", "Unlimited"),
                        "cardset": setname,
                        "cardcode": cardcode,
                        "cardid": cardid_field,
                        "print_id": data.get("print_id", "")
                    })
        except Exception as e:
            messagebox.showerror("Error", f"Failed to autosave CSV: {e}")


    def get_card_id(self, encoded_card_name):
        card_name = urllib.parse.unquote(encoded_card_name)
        manual_overrides = {
            "The Winged Dragon of Ra":"10000010",
            "The Winged Dragon of Ra - Immortal Phoenix":"10000090",
            "The Winged Dragon of Ra - Sphere Mode":"10000080",
            "Obelisk the Tormentor":"10000000",
            "Slifer the Sky Dragon":"10000020",
            "":"",

        }
        
        if card_name in manual_overrides:
            return manual_overrides[card_name]
        
        def try_fetch(name_variant, base_url):
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            url = f"{base_url}/{name_variant}"
            try:
                response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
                if response.status_code != 200:
                    return None, url
                html = response.text
                if "yugioh.fandom.com" in base_url:
                    marker = '<a href="/wiki/Passcode" title="Passcode">Passcode</a>'
                else:
                    marker = 'Passcode</th>'
                pos = html.find(marker)
                if pos == -1:
                    return None, url
                match = re.search(r'\b\d{8}\b', html[pos:pos+200])
                return (match.group(0) if match else None), url
            except Exception as e:
                print(f"Error fetching {url}: {e}")
                return None, url

        # Debug-friendly version
        card_name = urllib.parse.unquote(encoded_card_name)
        for attempt in [
            ("Fandom", encoded_card_name, "https://yugioh.fandom.com/wiki"),
            ("Yugipedia", encoded_card_name, "https://yugipedia.com/wiki"),
            ("Fandom (fallback)", f"{encoded_card_name}_(card)", "https://yugioh.fandom.com/wiki"),
            ("Yugipedia (fallback)", f"{encoded_card_name}_(card)", "https://yugipedia.com/wiki")
        ]:
            source, name_variant, base_url = attempt
            card_id, used_url = try_fetch(name_variant, base_url)
            if card_id:
                print(f"✓ Found ID for '{card_name}' via {source}")
                return card_id

        print(f"✗ Failed to find ID for '{card_name}'")
        return None
    
    
    def update_list(self, *args):
        search_text = self.search_var.get().lower()
        self.listbox.delete(0, tk.END)

        agg = defaultdict(lambda: {"total": 0, "sets": defaultdict(int)})
        for (name, setname), data in self.collection.items():
            agg[name]["total"] += data["quantity"]
            agg[name]["sets"][setname] += data["quantity"]

        for cardname, data in sorted(agg.items()):
            if search_text and search_text not in cardname.lower():
                continue
            sets_str = ", ".join(f"{setname}: {qty}" for setname, qty in data["sets"].items())
            line = f"{cardname} - Total: {data['total']} ({sets_str})"
            self.listbox.insert(tk.END, line)

    def add_card(self):
        cardname = self.add_name_entry.get().strip()
        qty_str = self.add_qty_entry.get().strip()
        setname = self.add_set_entry.get().strip()

        if self.crafted_var.get():
            setname = "Crafted Card"
        else:
            setname = self.add_set_entry.get().strip()

        if not cardname or not qty_str or not setname:
            messagebox.showerror("Error", "Please provide card name, quantity, and set name.")
            return

        try:
            qty = int(qty_str)
            if qty < 1:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Quantity must be a positive integer.")
            return

        if setname != "Crafted Card" and not self.check_set_exists(setname):
            messagebox.showerror("Error", f"Set name '{setname}' not found on Master Duel Meta. Please check spelling.")
            return

        if setname != "Crafted Card" and not self.check_card_exists(cardname):
            messagebox.showerror("Error", f"Card name '{cardname}' not found on Master Duel Meta. Please check spelling.")
            return

        encoded_name = urllib.parse.quote(cardname)
        cardid = self.get_card_id(encoded_name)
        if not cardid:
            messagebox.showwarning("Warning", f"Card ID not found for '{cardname}'. Added without ID.")
            cardid = ""

        rarity = self.get_card_rarity(encoded_name)
        edition = "Unlimited"
        cardcode = ""
        print_id = ""

        key = (cardname, setname)
        if key not in self.collection:
            self.collection[key] = {
                "quantity": 0,
                "rarity": rarity,
                "edition": edition,
                "cardid": cardid,
                "cardcode": cardcode,
                "print_id": print_id
            }
        self.collection[key]["quantity"] += qty

        self.update_list()
        self.autosave_csv()
        self.add_name_entry.delete(0, tk.END)
        self.add_qty_entry.delete(0, tk.END)
        if not self.crafted_var.get():
            self.add_set_entry.delete(0, tk.END)
        else:
            pass

    def check_set_exists(self, setname):
        normalized = setname.lower().replace(" ", "-")
        url = f"https://masterduelmeta.com/articles/sets/{normalized}"
        response = requests.get(url)
        return response.status_code == 200

    def check_card_exists(self, cardname):
        encoded = urllib.parse.quote(cardname)
        url = f"https://masterduelmeta.com/cards/{encoded}"
        response = requests.get(url)
        return response.status_code == 200
    
    def get_card_rarity(self, encoded_name):
        RARITY_MAP = {
            "UR": "Ultra Rare",
            "SR": "Super Rare",
            "R": "Rare",
            "C": "Common",
        }

        url = f"https://masterduelmeta.com/cards/{encoded_name}"
        response = requests.get(url)
        if response.status_code != 200:
            return "Unknown"
        soup = BeautifulSoup(response.text, "html.parser")
        
        img_rarity = soup.find("img", alt=re.compile(r"Rarity", re.IGNORECASE))
        if img_rarity and img_rarity.has_attr("alt"):
            rarity_abbr = img_rarity["alt"].replace(" Rarity", "").strip()
            return RARITY_MAP.get(rarity_abbr, rarity_abbr) 
        
        return "Unknown"
    
    def generate_whitelist_from_file(self):
        '''output_path = filedialog.asksaveasfilename(
            defaultextension=".conf",
            filetypes=[("Whitelist Conf", "*.conf")],
            title="Save Whitelist As"
        )'''

        output_path = os.path.join("whitelist.conf")

        
        if not output_path:
            return

        try:
            card_counts = defaultdict(int)

            for (cardname, setname), data in self.collection.items():
                cardid = data.get("cardid", "").strip()
                qty = data.get("quantity", 0)
                if cardid.isdigit():
                    card_counts[cardid] += qty

            for card in card_counts:
                card_counts[card] = min(card_counts[card], 3)

            with open(output_path, "w", encoding="utf-8") as outfile:
                outfile.write("!Limited Between Reece & Ant\n$whitelist\n")
                for cardid, qty in sorted(card_counts.items()):
                    outfile.write(f"{cardid} {qty}\n")

            messagebox.showinfo("Success", f"Whitelist saved") #to:\n{output_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate whitelist: {e}")

def launch(on_close_callback=None, parent=None):
    if parent is None:
        root = tk.Tk()
        own_root = True
    else:
        root = tk.Toplevel(parent)
        own_root = False
    app = CollectionManager(root)
    app.on_close_callback = on_close_callback
    
    root.protocol("WM_DELETE_WINDOW", app._close_window)
    
    if own_root:
        root.mainloop()

if __name__ == "__main__":
    launch()