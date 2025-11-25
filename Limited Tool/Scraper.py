import re
import urllib.parse
import threading
import time
import os
import csv
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import tkinter as tk
from tkinter import scrolledtext

def get_card_id(encoded_card_name):
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
                return None
            html = response.text
            if "yugioh.fandom.com" in base_url:
                marker = '<a href="/wiki/Passcode" title="Passcode">Passcode</a>'
            else:
                marker = '<a href="/wiki/Password" title="Password">Password</a>'
            pos = html.find(marker)
            if pos == -1:
                return None
            match = re.search(r'\b\d{8}\b', html[pos:pos+200])
            return match.group(0) if match else None
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    # Try Fandom → Yugipedia → Fallbacks
    return (
        try_fetch(encoded_card_name, "https://yugioh.fandom.com/wiki") or
        try_fetch(encoded_card_name, "https://yugipedia.com/wiki") or
        try_fetch(f"{encoded_card_name}_(card)", "https://yugioh.fandom.com/wiki") or
        try_fetch(f"{encoded_card_name}_(card)", "https://yugipedia.com/wiki")
    )

def is_ygoprodeck(url):
    return "ygoprodeck.com" in url.lower()

def parse_masterduelmeta(driver, html, cardset_name, cardset_prefix):
    pattern = re.compile(r'alt="(UR|SR|R|N)"|href="[^"]*/cards/([^"]+)"')
    rarity_map = {"UR": "Ultra Rare", "SR": "Super Rare", "R": "Rare", "N": "Common"}
    current_rarity = None
    cards = []

    for match in pattern.finditer(html):
        rarity = match.group(1)
        encoded_card_name = match.group(2)

        if rarity:
            current_rarity = rarity
        elif encoded_card_name and current_rarity:
            full_rarity = rarity_map.get(current_rarity, current_rarity)
            card_id = get_card_id(encoded_card_name)
            decoded_name = urllib.parse.unquote(encoded_card_name)
            cards.append({
                "cardname": decoded_name,
                "cardq": 0,
                "cardrarity": full_rarity,
                "card_edition": "Unlimited",
                "cardset": cardset_name,
                "cardcode": f"{cardset_prefix}{card_id}" if card_id else 0,
                "cardid": card_id if card_id else "unlisted",
                "print_id": ""
            })
    return cards

def parse_ygoprodeck(driver, html, cardset_name, cardset_prefix):
    soup = BeautifulSoup(html, "html.parser")
    rarities = ["Common", "Rare", "Super Rare", "Ultra Rare"]
    rarity_ids = {"Common": "Common", "Rare": "Rare", "Super Rare": "Super_Rare", "Ultra Rare": "Ultra_Rare"}
    cards = []

    for rarity in rarities:
        div = soup.find("div", id=rarity_ids.get(rarity))
        if not div:
            continue
        for fig in div.find_all("figure"):
            name_tag = fig.find("span", class_="fig-name")
            if not name_tag:
                continue
            cardname = name_tag.text.strip()
            encoded_card_name = urllib.parse.quote(cardname, safe='')
            card_id = get_card_id(encoded_card_name)
            cards.append({
                "cardname": cardname,
                "cardq": 0,
                "cardrarity": rarity,
                "card_edition": "Unlimited",
                "cardset": cardset_name,
                "cardcode": f"{cardset_prefix}{card_id}" if card_id else 0,
                "cardid": card_id if card_id else "unlisted",
                "print_id": ""
            })

    return cards

def process_url(url, output_widget):
    url = url.strip()
    if not url:
        output_widget.insert(tk.END, "Please enter a URL.\n")
        return

    output_widget.insert(tk.END, f"Processing URL: {url}\n")
    output_widget.see(tk.END)

    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")

        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        time.sleep(5)
        html = driver.page_source

        if is_ygoprodeck(url):
            output_widget.insert(tk.END, "Detected: YGOPRODeck\n")
            cardset_name = urllib.parse.unquote(url.split('/pack/')[1].split('/')[0])
            cardset_prefix = cardset_name[:4]
            cards = parse_ygoprodeck(driver, html, cardset_name, cardset_prefix)
        else:
            output_widget.insert(tk.END, "Detected: MasterDuelMeta\n")
            cardset_name = urllib.parse.unquote(url.split("/")[-1]).replace("-", " ").title()
            cardset_prefix = cardset_name[:4]
            cards = parse_masterduelmeta(driver, html, cardset_name, cardset_prefix)

        driver.quit()

        os.makedirs("Secret Packs", exist_ok=True)
        csv_filename = f"{cardset_name}.csv"
        csv_path = os.path.join("Secret Packs", csv_filename)

        with open(csv_path, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=[
                "cardname", "cardq", "cardrarity", "card_edition",
                "cardset", "cardcode", "cardid", "print_id"
            ])
            writer.writeheader()
            for card in cards:
                writer.writerow(card)

        output_widget.insert(tk.END, f"Exported {len(cards)} cards to Secret Packs/{csv_filename}\n\n")
        output_widget.see(tk.END)

    except Exception as e:
        output_widget.insert(tk.END, f"Error: {str(e)}\n\n")
        output_widget.see(tk.END)

def launch(on_close_callback=None):
    global root, url_entry, output_text

    root = tk.Tk()
    root.title("Yu-Gi-Oh! Pack Scraper")

    tk.Label(root, text="Enter pack URL:").pack(pady=(10, 0))
    url_entry = tk.Entry(root, width=80)
    url_entry.pack(padx=10, pady=5)

    buttons_frame = tk.Frame(root)
    buttons_frame.pack(pady=5)

    def on_process_click():
        url = url_entry.get()
        threading.Thread(target=process_url, args=(url, output_text), daemon=True).start()

    def on_close():
        root.destroy()
        if on_close_callback:
            on_close_callback()


    tk.Button(buttons_frame, text="Process", command=on_process_click).pack(side=tk.LEFT, padx=5)
    tk.Button(buttons_frame, text="Exit", command=on_close).pack(side=tk.LEFT, padx=5)

    output_text = scrolledtext.ScrolledText(root, width=90, height=20, state=tk.NORMAL)
    output_text.pack(padx=10, pady=10)

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()

if __name__ == "__main__":
    launch()
