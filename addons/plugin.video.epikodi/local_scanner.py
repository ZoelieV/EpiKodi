import os
import tmdb

VIDEO_EXTENSIONS = [".mp4", ".mkv", ".avi", ".mov"]

def scan_directory(path):
    """Retourne liste fichiers vidéo d'un dossier"""
    videos = []
    for root, _, files in os.walk(path):
        for file in files:
            if any(file.lower().endswith(ext) for ext in VIDEO_EXTENSIONS):
                full_path = os.path.join(root, file)
                videos.append({"name": clean_name(file), "path": full_path})
    return videos

def clean_name(filename):
    """Recup titre du film"""
    name, _ = os.path.splitext(filename)
    # Supprime les caractères indésirables
    name = name.replace(".", " ").replace("_", " ")
    return name.strip()

def enrich_with_tmdb(videos):
    """Recherche film via TMDB et ajoute les infos"""
    enriched = []
    for video in videos:
        results = tmdb.search_movie(video["name"])
        if results:
            # Prendre le premier résultat
            movie = results[0]
            video.update({
                "title": movie.get("title"),
                "year": movie.get("release_date", "")[:4],
                "plot": movie.get("overview"),
                "poster": tmdb.IMAGE_URL + movie.get("poster_path", "")
            })
        else:
            video.update({
                "title": video["name"],
                "year": "N/A",
                "plot": "Aucune information trouvée.",
                "poster": ""
            })
        enriched.append(video)
    return enriched