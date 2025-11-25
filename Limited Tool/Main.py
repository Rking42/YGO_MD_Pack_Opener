import tkinter as tk
from tkinter import messagebox
import Scraper
import Manager
import Pack_Simulator
import sys
import webbrowser
import Pull_History
import Troll

def main_menu():
    menu_root = tk.Tk()
    menu_root.title("Main Menu")
    
    menu_root._exiting = False

    def show_menu_again():
        if not menu_root._exiting and menu_root.winfo_exists():
            menu_root.deiconify()

    def launch_scraper():
        if menu_root.winfo_exists():
            menu_root.withdraw()
            Scraper.launch(on_close_callback=show_menu_again)

    def launch_manager():
        if menu_root.winfo_exists():
            menu_root.withdraw()
            Manager.launch(on_close_callback=show_menu_again, parent=menu_root)

    def launch_simulator():
        if menu_root.winfo_exists():
            menu_root.withdraw()
            Pack_Simulator.launch(on_close_callback=show_menu_again)

    def launch_pull_history_analyzer():
        if menu_root.winfo_exists():
            menu_root.withdraw()
            Pull_History.launch(on_close_callback=show_menu_again)

    def troll():
        if menu_root.winfo_exists():
            menu_root.withdraw()
            Troll.launch(on_close_callback=show_menu_again)

    def exit_app():
        if not messagebox.askokcancel("Quit", "Do you want to exit the app?"):
            return
            
        menu_root._exiting = True
        
        for child in menu_root.winfo_children():
            try:
                child.destroy()
            except:
                pass
                
        menu_root.quit()
        menu_root.destroy()
        
        if hasattr(sys, '_MEIPASS'):
            sys.exit(0)

    tk.Label(menu_root, text="Welcome to the Limited Tool! (Name Pending)", 
            font=("Arial", 16)).pack(pady=10)

    buttons = [
        ("Open Pack Scraper", launch_scraper),
        ("Open Collection Manager", launch_manager),
        ("Open Pack Simulator", launch_simulator),
        ("View Pull History", launch_pull_history_analyzer),
        ("Make 1 Less Lonely Mama, NOW! (pls)", troll),
        ("Exit", exit_app)
    ]
    
    for text, command in buttons:
        tk.Button(menu_root, text=text, command=command, 
                 width=30).pack(pady=5)

    menu_root.protocol("WM_DELETE_WINDOW", exit_app)
    
    try:
        menu_root.mainloop()
    except KeyboardInterrupt:
        exit_app()

if __name__ == "__main__":
    main_menu()