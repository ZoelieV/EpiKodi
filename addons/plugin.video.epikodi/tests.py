import os
import pickle
import requests

# === Configuration ===
TMDB_API_KEY = 'VOTRE_CLE_API_TMDB'  # Remplacez par votre clé TMDB
FAV_FILE = 'favoris_tmdb.pickle'

# === Fonctions de gestion des favoris ===
def load_favorites():
    if os.path.exists(FAV_FILE):
        with open(FAV_FILE, 'rb') as f:
            return pickle.load(f)
    return []

def save_favorites(favs):
    with open(FAV_FILE, 'wb') as f:
        pickle.dump(favs, f)

def add_favorite(movie_id):
    favs = load_favorites()
    if movie_id not in favs:
        favs.append(movie_id)
        save_favorites(favs)
        print(f"✅ Film {movie_id} ajouté aux favoris.")
    else:
        print("⚠️ Ce film est déjà dans vos favoris.")

def remove_favorite(movie_id):
    favs = load_favorites()
    if movie_id in favs:
        favs.remove(movie_id)
        save_favorites(favs)
        print(f"🗑️ Film {movie_id} supprimé des favoris.")
    else:
        print("❌ Film non trouvé dans vos favoris.")

def list_favorites():
    favs = load_favorites()
    if not favs:
        print("📂 Aucun favori trouvé.")
        return

    print("⭐ Vos favoris TMDB :")
    for movie_id in favs:
        movie = get_movie_info(movie_id)
        if movie:
            print(f"- {movie['title']} ({movie['release_date'][:4]}) - ID: {movie_id}")
        else:
            print(f"- ID inconnu : {movie_id}")

# === Fonctions liées à TMDB ===
def get_movie_info(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    params = {'api_key': TMDB_API_KEY, 'language': 'fr'}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    return None

def search_movie(query):
    url = f"https://api.themoviedb.org/3/search/movie"
    params = {'api_key': TMDB_API_KEY, 'query': query, 'language': 'fr'}
    response = requests.get(url, params=params)
    results = response.json().get('results', [])
    for movie in results[:5]:  # afficher les 5 premiers
        print(f"{movie['title']} ({movie['release_date'][:4]}) - ID: {movie['id']}")

# === Interface simple ===
if __name__ == '__main__':
    while True:
        print("\n--- Menu Favoris TMDB ---")
        print("1. Ajouter un favori (via ID TMDB)")
        print("2. Supprimer un favori")
        print("3. Voir les favoris")
        print("4. Rechercher un film")
        print("0. Quitter")
        choix = input("Votre choix : ")

        if choix == '1':
            mid = input("ID TMDB du film à ajouter : ")
            add_favorite(int(mid))
        elif choix == '2':
            mid = input("ID TMDB du film à retirer : ")
            remove_favorite(int(mid))
        elif choix == '3':
            list_favorites()
        elif choix == '4':
            query = input("Titre du film à rechercher : ")
            search_movie(query)
        elif choix == '0':
            break
        else:
            print("❓ Choix non reconnu.")
