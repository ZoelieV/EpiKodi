import sys
import xbmcplugin
import xbmcgui
import local_scanner

def show_local_library():
    handle = int(sys.argv[1])

    # Demander un dossier à scanner
    folder = xbmcgui.Dialog().browse(0, "Sélectionner un dossier", "files", "", False, False, "/home/zoeliev/Vidéos")
    if not folder:
        return

    xbmcgui.Dialog().notification("EpiKodi", "Scan du dossier en cours", xbmcgui.NOTIFICATION_INFO, 3000)

    # Scanner le dossier et enrichir les données
    videos = local_scanner.scan_directory(folder)
    enriched_videos = local_scanner.enrich_with_tmdb(videos)

    if not enriched_videos:
        xbmcgui.Dialog().ok("Bibliothèque", "Aucun fichier vidéo trouvé.")
        return

    # Afficher la liste enrichie
    for video in enriched_videos:
        item = xbmcgui.ListItem(label=f"{video['title']} ({video['year']})")
        item.setArt({"poster": video['poster'], "thumb": video['poster']})
        item.setInfo("video", {"title": video['title'], "plot": video['plot'], "year": video['year']})

        # Pas d’action pour l’instant
        xbmcplugin.addDirectoryItem(handle, "", item, isFolder=False)

    xbmcplugin.endOfDirectory(handle)

# Ajoute une option pour lancer la fonction
if __name__ == "__main__":
    choice = xbmcgui.Dialog().select("EpiKodi", ["Rechercher un film", "Scanner la bibliothèque locale"])
    if choice == 0:
        search_movie()
    elif choice == 1:
        show_local_library()