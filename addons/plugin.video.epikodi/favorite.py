import sys
import xbmcplugin
import xbmcgui
import xbmcvfs
from tmdb import API_KEY, BASE_URL, IMAGE_URL
import json
import os
import urllib.parse


FAVORITES_FILE = os.path.join(xbmcvfs.translatePath("special://profile/addon_data/plugin.video.epikodi"), "favorites.json")


def add_movie_listitem(movie):
    handle = int(sys.argv[1])
    poster_url = IMAGE_URL + movie['poster_path'] if movie.get('poster_path') else ""
    item = xbmcgui.ListItem(label=movie['title'])
    item.setArt({"poster": poster_url, "thumb": poster_url})

    cast_text = ", ".join(movie.get('top_cast', []))
    full_plot = movie.get('overview', "")
    if cast_text:
        full_plot += "\n\nActeurs principaux : " + cast_text

    item.setInfo("video", {
        "title": movie['title'],
        "plot": full_plot,
        "year": movie.get('release_date', "").split("-")[0] if movie.get('release_date') else "",
        "rating": float(movie.get('vote_average', 0)),
        "premiered": movie.get('release_date', "")
    })

    movie_json = urllib.parse.quote(json.dumps(movie))
    favorites = load_favorites()

    is_favorite = any(fav.get('id') == movie.get('id') for fav in favorites)

    context_menu = [
        ("Afficher les informations", f"RunPlugin({sys.argv[0]}?action=show_info&movie={movie_json})"),
        ("Ajouter/Modifier ma note et review", f"RunPlugin({sys.argv[0]}?action=add_review&movie={movie_json})"),
        ("Lire la bande-annonce", f"RunPlugin({sys.argv[0]}?action=play&movie_id={movie.get('id', '')})")
    ]

    if is_favorite:
        context_menu.append(("Retirer des favoris", f"RunPlugin({sys.argv[0]}?action=remove_from_favorites&movie={movie_json})"))
    else:
        context_menu.append(("Ajouter aux favoris", f"RunPlugin({sys.argv[0]}?action=add_to_favorites&movie={movie_json})"))

    context_menu.append(("Supprimer de l'historique", f"RunPlugin({sys.argv[0]}?action=remove_from_history&movie={movie_json})"))

    item.addContextMenuItems(context_menu)

    url = f"{sys.argv[0]}?action=show_info&movie={movie_json}"
    xbmcplugin.addDirectoryItem(handle, url, item, isFolder=False)

def load_favorites():
    if not os.path.exists(FAVORITES_FILE):
        return []
    with open(FAVORITES_FILE, "r") as f:
        return json.load(f)

def save_favorites(favorites):
    os.makedirs(os.path.dirname(FAVORITES_FILE), exist_ok=True)
    with open(FAVORITES_FILE, "w") as f:
        json.dump(favorites, f, indent=4)

def add_to_favorites(movie):
    favorites = load_favorites()

    def is_same(fav, target):
        if fav.get('id') and target.get('id'):
            return fav['id'] == target['id']
        return fav.get('title', '').lower() == target.get('title', '').lower() and \
               fav.get('release_date', '') == target.get('release_date', '')

    if any(is_same(fav, movie) for fav in favorites):
        xbmcgui.Dialog().notification("EpiKodi", f"'{movie['title']}' est déjà dans les favoris.", xbmcgui.NOTIFICATION_INFO, 3000)
        return

    favorites.append(movie)
    save_favorites(favorites)
    xbmcgui.Dialog().notification("EpiKodi", f"'{movie['title']}' ajouté aux favoris.", xbmcgui.NOTIFICATION_INFO, 3000)

def remove_from_favorites(movie):
    favorites = load_favorites()

    def is_same(fav, target):
        return fav.get('title', '').lower() == target.get('title', '').lower() and \
               fav.get('release_date', '') == target.get('release_date', '')

    updated = [fav for fav in favorites if not is_same(fav, movie)]

    if len(updated) != len(favorites):
        save_favorites(updated)
        xbmcgui.Dialog().notification("EpiKodi", f"'{movie['title']}' retiré des favoris.", xbmcgui.NOTIFICATION_INFO, 3000)
    else:
        xbmcgui.Dialog().notification("EpiKodi", f"'{movie['title']}' n'a pas été trouvé dans les favoris.", xbmcgui.NOTIFICATION_WARNING, 3000)

def show_favorites():
    favorites = load_favorites()
    if not favorites:
        xbmcgui.Dialog().ok("Favoris", "Aucun film dans les favoris.")
        return

    handle = int(sys.argv[1])
    for movie in favorites:
        add_movie_listitem(movie)
    xbmcplugin.endOfDirectory(handle)

def manual_add_to_favorites():
    title = xbmcgui.Dialog().input("Titre du film à ajouter")
    if not title:
        return

    year = xbmcgui.Dialog().input("Année de sortie (optionnel)")
    movie = {
        "title": title,
        "overview": "",
        "release_date": f"{year}-01-01" if year else "",
        "vote_average": 0.0,
        "poster_path": "",
        "top_cast": []
    }

    add_to_favorites(movie)