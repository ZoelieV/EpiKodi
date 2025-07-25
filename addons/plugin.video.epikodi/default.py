import sys
import xbmcplugin
import xbmcgui
import local_scanner
import requests
import xbmc
import xbmcvfs
from tmdb import API_KEY, BASE_URL, IMAGE_URL
import json
import os
import urllib.parse


FAVORITES_FILE = os.path.join(xbmcvfs.translatePath("special://profile/addon_data/plugin.video.epikodi"), "favorites.json")


def get_movie_credits(movie_id):
    url = f"{BASE_URL}/movie/{movie_id}/credits?api_key={API_KEY}&language=fr-FR"
    resp = requests.get(url)
    if resp.status_code == 200:
        return resp.json()
    return None

def search_movie(query):
    url = f"{BASE_URL}/search/movie?api_key={API_KEY}&language=fr-FR&query={query}"
    resp = requests.get(url)
    if resp.status_code != 200:
        return []
    results = resp.json().get('results', [])
    for movie in results:
        credits = get_movie_credits(movie['id'])
        if credits:
            cast = credits.get('cast', [])
            movie['top_cast'] = [actor['name'] for actor in cast[:3]]
        else:
            movie['top_cast'] = []
    return results

def show_local_library():
    handle = int(sys.argv[1])
    folder = xbmcgui.Dialog().browse(0, "Sélectionner un dossier", "files", "", False, False, "/home/zoeliev/Vidéos")
    if not folder:
        return
    xbmcgui.Dialog().notification("EpiKodi", "Scan du dossier en cours", xbmcgui.NOTIFICATION_INFO, 3000)

    videos = local_scanner.scan_directory(folder)
    enriched_videos = local_scanner.enrich_with_tmdb(videos)

    if not enriched_videos:
        xbmcgui.Dialog().ok("Bibliothèque", "Aucun fichier vidéo trouvé.")
        return

    for video in enriched_videos:
        add_movie_listitem(video)

    xbmcplugin.endOfDirectory(handle)

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

    favorites = load_favorites()
    if movie in favorites:
        context_menu = [("Retirer des favoris", f"RunPlugin({sys.argv[0]}?action=remove_from_favorites&movie={json.dumps(movie)})")]
    else:
        context_menu = [("Ajouter aux favoris", f"RunPlugin({sys.argv[0]}?action=add_to_favorites&movie={json.dumps(movie)})")]

    item.addContextMenuItems(context_menu)

    url = f"{sys.argv[0]}?action=play&movie_id={movie.get('id', '')}"

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
        return fav.get('title', '').lower() == target.get('title', '').lower() and \
               fav.get('release_date', '') == target.get('release_date', '')

    if any(is_same(fav, movie) for fav in favorites):
        xbmcgui.Dialog().notification("EpiKodi", f"'{movie['title']}' est déjà dans les favoris.", xbmcgui.NOTIFICATION_WARNING, 3000)
    else:
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

def play_movie(movie_id):
    # Récupérer la bande-annonce via TMDB
    url = f"{BASE_URL}/movie/{movie_id}/videos?api_key={API_KEY}&language=fr-FR"
    resp = requests.get(url)
    if resp.status_code == 200:
        videos = resp.json().get("results", [])
        trailer = next((v for v in videos if v['type'] == 'Trailer' and v['site'] == 'YouTube'), None)
        if trailer:
            video_url = f"https://www.youtube.com/watch?v={trailer['key']}"
            listitem = xbmcgui.ListItem(path=video_url)
            xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, listitem)
            return

    xbmcgui.Dialog().notification("EpiKodi", "Aucune bande annonce trouvée", xbmcgui.NOTIFICATION_INFO, 3000)

if __name__ == "__main__":
    handle = int(sys.argv[1]) if len(sys.argv) > 1 else -1
    args = {}
    if len(sys.argv) > 2 and sys.argv[2].startswith('?'):
        args = dict(arg.split('=') for arg in sys.argv[2][1:].split('&') if '=' in arg)

    action = args.get('action')
    if action == "add_to_favorites":
        movie_arg = args.get('movie')
        if movie_arg:
            try:
                movie = json.loads(movie_arg)
                add_to_favorites(movie)
            except json.JSONDecodeError:
                xbmcgui.Dialog().notification("EpiKodi", "Erreur : données du film invalides.", xbmcgui.NOTIFICATION_ERROR, 3000)
        else:
            xbmcgui.Dialog().notification("EpiKodi", "Erreur : aucun film spécifié.", xbmcgui.NOTIFICATION_ERROR, 3000)
    elif action == "show_favorites":
        show_favorites()
    elif action == "manual_add":
        manual_add_to_favorites()
    elif action == "remove_from_favorites":
        movie = json.loads(args.get('movie', '{}'))
        remove_from_favorites(movie)
    elif action == "play":
        movie_id = args.get('movie_id')
        if movie_id:
            play_movie(movie_id)
    else:
        choice = xbmcgui.Dialog().select("EpiKodi", [
            "Rechercher un film",
            "Scanner la bibliothèque locale",
            "Voir les favoris",
            "Ajouter un favori manuellement"
        ])

        if choice == 0:
            query = xbmcgui.Dialog().input("Rechercher un film")
            enriched_videos = search_movie(query)
            for movie in enriched_videos:
                add_movie_listitem(movie)
            xbmcplugin.endOfDirectory(handle)

        elif choice == 1:
            show_local_library()

        elif choice == 2:
            show_favorites()

        elif choice == 3:
            manual_add_to_favorites()