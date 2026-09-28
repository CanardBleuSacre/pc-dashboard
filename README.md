# PC Dashboard

Application de bureau Python pour consulter l'espace disque, les dossiers volumineux, le résultat de la dernière sauvegarde et des alertes locales.

## Fonctionnalités

- Afficher la capacité, l'espace utilisé et l'espace libre du volume contenant le chemin indiqué.
- Analyser à la demande la taille des sous-dossiers sans bloquer la fenêtre.
- Lire un rapport de sauvegarde JSON et signaler une erreur ou une sauvegarde trop ancienne.
- Régler les seuils d'alerte pour l'espace libre et l'âge de la sauvegarde.

Les indicateurs se rafraîchissent toutes les minutes pendant que la fenêtre est ouverte. L'analyse des dossiers doit être déclenchée manuellement et peut prendre du temps. Le programme ne surveille rien lorsque la fenêtre est fermée.

## Installer et lancer

Python 3.10 ou plus récent est nécessaire. Dans un terminal ouvert à la racine du dépôt :

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

## Produire un rapport de sauvegarde

Crée un dossier de destination sur le disque externe **monté**. Ensuite, adapte les chemins et lance :

```bash
python backup_example.py ~/Documents /media/$USER/MON_DISQUE/sauvegarde
```

Le script copie les fichiers nouveaux ou dont la taille ou la date de modification diffère, puis écrit `~/backup-report.json`. Il refuse une destination inexistante. Vérifie le chemin et le montage du disque avant chaque lancement. Il ne garde pas de versions précédentes et ne contrôle pas l'intégrité des copies après écriture. Tu peux remplacer ce script par un autre programme qui produit le même rapport.

Dans la fenêtre, indique le chemin de ce rapport dans le champ **Rapport de sauvegarde**. Exemple de format :

```json
{
  "finished_at": "2026-09-28T12:00:00+00:00",
  "status": "ok",
  "copied": 3,
  "errors": []
}
```

Si le rapport est absent, le tableau de bord affiche une alerte. Les fichiers personnels et les rapports réels ne doivent pas être publiés sur GitHub.

## Structure

- `main.py` : interface PySide6.
- `core.py` : mesures, tailles de dossiers et alertes.
- `backup_example.py` : sauvegarde d'exemple avec rapport JSON.
- `requirements.txt` : dépendance graphique.
- `.gitignore` : fichiers locaux exclus de Git.
