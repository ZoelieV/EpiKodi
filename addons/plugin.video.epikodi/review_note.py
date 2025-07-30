import xbmcgui
import os
from tmdb import API_KEY, BASE_URL, IMAGE_URL
import json
import xbmcvfs


REVIEW_FILE = xbmcvfs.translatePath("special://profile/addon_data/plugin.video.epikodi/reviews.json")


def load_reviews():
    if os.path.exists(REVIEW_FILE):
        with open(REVIEW_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_reviews(reviews):
    os.makedirs(os.path.dirname(REVIEW_FILE), exist_ok=True)
    with open(REVIEW_FILE, "w", encoding="utf-8") as f:
        json.dump(reviews, f, ensure_ascii=False, indent=4)

def add_review(movie_id, movie_title):
    reviews = load_reviews()

    rating = xbmcgui.Dialog().numeric(0, f"Note pour {movie_title} (0-10)")
    if rating == "":
        if str(movie_id) in reviews:
            del reviews[str(movie_id)]
            save_reviews(reviews)
            xbmcgui.Dialog().notification("EpiKodi", "Note supprimée.", xbmcgui.NOTIFICATION_INFO, 3000)
        else:
            xbmcgui.Dialog().notification("EpiKodi", "Aucune note à supprimer.", xbmcgui.NOTIFICATION_INFO, 3000)
        return

    try:
        rating = float(rating)
    except ValueError:
        xbmcgui.Dialog().notification("EpiKodi", "Note invalide.", xbmcgui.NOTIFICATION_ERROR, 3000)
        return

    if rating > 10:
        xbmcgui.Dialog().notification("EpiKodi", "La note ne peut pas dépasser 10.", xbmcgui.NOTIFICATION_ERROR, 3000)
        return

    review_text = xbmcgui.Dialog().input(f"Votre avis sur {movie_title}")

    reviews[str(movie_id)] = {
        "rating": rating,
        "review": review_text
    }
    save_reviews(reviews)
    xbmcgui.Dialog().notification("EpiKodi", "Avis enregistré.", xbmcgui.NOTIFICATION_INFO, 3000)
