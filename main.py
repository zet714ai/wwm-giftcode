import tkinter as tk
from data_manager import DataManager
from auto_engine import AutoEngine
from scraper_service import ScraperService
from gui_app import WWMApp

def main():
    root = tk.Tk()
    dm = DataManager()
    engine = AutoEngine(dm)
    scraper = ScraperService(dm)
    app = WWMApp(root, dm, engine, scraper)
    root.mainloop()

if __name__ == "__main__":
    main()