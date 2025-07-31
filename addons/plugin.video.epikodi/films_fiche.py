import xbmcgui
import requests
from tmdb import API_KEY, BASE_URL
from review_note import load_reviews
from films_history import add_to_history

def get_movie_credits(movie_id):
    url = f"{BASE_URL}/movie/{movie_id}/credits?api_key={API_KEY}&language=fr-FR"
    resp = requests.get(url)
    if resp.status_code == 200:
        return resp.json()
    return None

def show_movie_info(movie):
    add_to_history(movie)
    reviews = load_reviews()
    user_review = reviews.get(str(movie['id']), {})

    cast_text = ", ".join(movie.get('top_cast', []))
    plot = movie.get('overview', "")
    if cast_text:
        plot += f"\n\n[COLOR yellow]Acteurs principaux :[/COLOR] {cast_text}"

    year = movie.get('release_date', "").split("-")[0] if movie.get('release_date') else "Inconnue"
    rating = f"{movie.get('vote_average', 0):.1f}/10"

    info_text = f"[B]{movie['title']}[/B]\n\n" \
                f"[COLOR lightblue]Année :[/COLOR] {year}\n" \
                f"[COLOR lightblue]Note TMDB :[/COLOR] {rating}\n\n" \
                f"{plot}"

    if user_review:
        info_text += f"\n\n[COLOR orange][B]Votre note :[/B][/COLOR] {user_review['rating']}/10"
        if user_review['review']:
            info_text += f"\n[COLOR orange][B]Votre avis :[/B][/COLOR] {user_review['review']}"

    dialog = xbmcgui.Dialog()
    dialog.textviewer(f"Informations - {movie['title']}", info_text)
