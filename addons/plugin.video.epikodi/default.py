import sys
import xbmcplugin
import xbmcgui
import local_scanner
import requests
from tmdb import API_KEY, BASE_URL, IMAGE_URL
import json
import urllib.parse
from favorite import add_to_favorites, remove_from_favorites, show_favorites, manual_add_to_favorites, load_favorites
from review_note import add_review
from films_fiche import show_movie_info, get_movie_credits

def get_similar_movies(movie_id):
    url = f"{BASE_URL}/movie/{movie_id}/similar?api_key={API_KEY}&language=fr-FR"
    resp = requests.get(url)
    if resp.status_code != 200:
        return []
    results = resp.json().get('results', [])
    for movie in results:
        credits = get_movie_credits(movie['id'])
        movie['top_cast'] = [actor['name'] for actor in credits.get('cast', [])[:3]] if credits else []
    return results

def search_movie(query):
    url = f"{BASE_URL}/search/movie?api_key={API_KEY}&language=fr-FR&query={query}"
    resp = requests.get(url)
    if resp.status_code != 200:
        return []
    results = resp.json().get('results', [])
    for movie in results:
        credits = get_movie_credits(movie['id'])
        movie['top_cast'] = [actor['name'] for actor in credits.get('cast', [])[:3]] if credits else []
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

def play_movie(movie_id):
    """Lecture de la bande-annonce d'un film."""
    url = f"{BASE_URL}/movie/{movie_id}/videos?api_key={API_KEY}&language=fr-FR"
    resp = requests.get(url)
    if resp.status_code == 200:
        videos = resp.json().get("results", [])
        trailer = next((v for v in videos if v['type'] == 'Trailer' and v['site'] == 'YouTube'), None)
        if trailer and 'key' in trailer:
            video_url = f"https://www.youtube.com/watch?v={trailer['key']}"
            listitem = xbmcgui.ListItem(path=video_url)
            xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, listitem)
            return
        else:
            xbmcgui.Dialog().notification("EpiKodi", "Aucune bande-annonce YouTube trouvée.", xbmcgui.NOTIFICATION_INFO, 3000)
    else:
        xbmcgui.Dialog().notification("EpiKodi", f"Erreur API : {resp.status_code}", xbmcgui.NOTIFICATION_ERROR, 3000)


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

    item.addContextMenuItems(context_menu)

    url = f"{sys.argv[0]}?action=show_info&movie={movie_json}"
    xbmcplugin.addDirectoryItem(handle, url, item, isFolder=False)


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
                movie = json.loads(urllib.parse.unquote(movie_arg))
                add_to_favorites(movie)
            except json.JSONDecodeError:
                xbmcgui.Dialog().notification("EpiKodi", "Erreur : données du film invalides.", xbmcgui.NOTIFICATION_ERROR, 3000)

    elif action == "show_favorites":
        show_favorites()

    elif action == "manual_add":
        manual_add_to_favorites()

    elif action == "remove_from_favorites":
        movie_arg = args.get('movie')
        if movie_arg:
            try:
                movie = json.loads(urllib.parse.unquote(movie_arg))
                remove_from_favorites(movie)
            except json.JSONDecodeError:
                xbmcgui.Dialog().notification("EpiKodi", "Erreur : données du film invalides.", xbmcgui.NOTIFICATION_ERROR, 3000)

    elif action == "play":
        movie_id = args.get('movie_id')
        if movie_id:
            play_movie(movie_id)

    elif action == "show_info":
        movie_arg = args.get('movie')
        if movie_arg:
            movie = json.loads(urllib.parse.unquote(movie_arg))
            show_movie_info(movie)

    elif action == "add_review":
        movie_arg = args.get('movie')
        if movie_arg:
            movie = json.loads(urllib.parse.unquote(movie_arg))
            add_review(movie['id'], movie['title'])

    else:
        choice = xbmcgui.Dialog().select("EpiKodi", [
            "Rechercher un film",
            "Scanner la bibliothèque locale",
            "Voir les favoris",
            "Ajouter un favori manuellement",
            "Rechercher des films similaires"
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

        elif choice == 4:
            query = xbmcgui.Dialog().input("Entrez le film de référence")
            search_results = search_movie(query)
            if search_results:
                selected_index = xbmcgui.Dialog().select("Choisissez un film", [m['title'] for m in search_results])
                if selected_index >= 0:
                    selected_movie = search_results[selected_index]
                    similar_movies = get_similar_movies(selected_movie['id'])
                    for similar in similar_movies:
                        add_movie_listitem(similar)
                    xbmcplugin.endOfDirectory(handle)