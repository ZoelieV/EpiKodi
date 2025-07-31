import xbmcgui
from tmdb import API_KEY, BASE_URL, IMAGE_URL
import json
import os
import xbmcvfs


HISTORY_FILE = os.path.join(xbmcvfs.translatePath("special://profile/addon_data/plugin.video.epikodi/history.json"), "history.json")


def remove_from_history(movie):
    history = load_history()
    history = [m for m in history if m["id"] != movie["id"]]
    save_history(history)

def clear_history():
    save_history([])

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_history(history):
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=4)

def add_to_history(movie):
    history = load_history()
    if not any(m['id'] == movie['id'] for m in history):
        history.insert(0, movie)
    else:
        history = [m for m in history if m['id'] != movie['id']]
        history.insert(0, movie)
    save_history(history)

def show_history(add_movie_listitem_callback):
    history = load_history()
    if not history:
        xbmcgui.Dialog().ok("Historique", "Aucun film consulté récemment.")
        return
    for movie in history:
        add_movie_listitem_callback(movie)
