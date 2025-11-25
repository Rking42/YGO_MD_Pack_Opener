import os
import sys
import webbrowser
from tkinter import Toplevel, Label, Button, messagebox
from PIL import Image, ImageTk
#from tkinter_video import TkinterVideo
import subprocess


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def launch(on_close_callback=None):
    win = Toplevel()
    win.title("Trolled!")
    win.geometry("600x600")

    def on_close():
        if on_close_callback:
            on_close_callback()
        win.destroy()

    #def open_website():
    #    webbrowser.open("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    
    #def play_video():
    #    try:
    #        video_path = resource_path("video.mp4")  # Replace with your actual video file
    #        player = TkinterVideo(master=win, scaled=True)
    #        player.load(video_path)
    #        player.pack(expand=True, fill="both")
    #        player.play()
    #    except Exception as e:
    #        messagebox.showerror("Video Error", f"Failed to play video: {e}")
    
    def play_video_with_ffplay():
        video_path = resource_path("never gonna give you up.mp4")
        try:
            if sys.platform == "win32":
                # Suppress the console window on Windows
                subprocess.Popen(
                    ["ffplay", "-autoexit", "-window_title", "FROM NOW OOOOOOOOONNNNNNNNN!!!!!!!!!", video_path],
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                # For Linux/macOS just run normally
                subprocess.Popen(["ffplay", "-autoexit", "-window_title", "FROM NOW OOOOOOOOONNNNNNNNN!!!!!!!!!", video_path])
        except Exception as e:
            messagebox.showerror("Error", f"Could not play video: {e}")

    win.protocol("WM_DELETE_WINDOW", on_close)

    try:
        text_label = Label(win, text="This single chicken is ready for finger licking", font=("Arial", 18))
        text_label.pack(pady=(20, 10))
        button = Button(win, text="Let Hensley know you're just 0.8 miles away!", command=play_video_with_ffplay)
        button.pack(pady=(0, 15)) 
        img_path = resource_path("Hen.jpg")
        img = Image.open(img_path)
        img.thumbnail((320, 480), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        label = Label(win, image=photo)
        label.image = photo
        label.pack(expand=True)
    except Exception as e:
        label = Label(win, text=f"Failed to load image: {e}")
        label.pack(padx=20, pady=20)
