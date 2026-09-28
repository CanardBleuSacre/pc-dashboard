"""Local metrics and backup report parsing."""
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


def disk_info(path):
    usage = shutil.disk_usage(path)
    return {'total': usage.total, 'used': usage.used, 'free': usage.free, 'free_percent': 100 * usage.free / usage.total}


def human(n):
    for unit in ('o', 'Kio', 'Mio', 'Gio', 'Tio'):
        if abs(n) < 1024 or unit == 'Tio':
            return f'{n:.1f} {unit}'
        n /= 1024


def directory_sizes(folder):
    """One pass over regular files, accounting for bytes in each direct child."""
    folder = Path(folder).resolve()
    if not folder.is_dir():
        raise ValueError('Dossier introuvable')
    totals = {}
    errors = 0
    for path in folder.rglob('*'):
        if path.is_symlink() or not path.is_file():
            continue
        try:
            relative = path.relative_to(folder)
            key = relative.parts[0] if len(relative.parts) > 1 else '(fichiers à la racine)'
            totals[key] = totals.get(key, 0) + path.stat().st_size
        except OSError:
            errors += 1
    return sorted(totals.items(), key=lambda item: item[1], reverse=True), errors


def backup_status(path):
    path = Path(path)
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict) or data.get('status') not in ('ok', 'error') or not isinstance(data.get('finished_at'), str):
        raise ValueError('Rapport de sauvegarde invalide')
    datetime.fromisoformat(data['finished_at'].replace('Z', '+00:00'))
    return data


def alerts(disk, backup, threshold=15, max_age_hours=48):
    found = []
    if disk['free_percent'] < threshold:
        found.append(f'Espace libre inférieur à {threshold} %')
    if backup is None:
        found.append('Aucun rapport de sauvegarde disponible')
    else:
        if backup['status'] != 'ok':
            found.append('La dernière sauvegarde a rencontré une erreur')
        try:
            last = datetime.fromisoformat(backup['finished_at'].replace('Z', '+00:00'))
            if last.tzinfo is None:
                raise ValueError('Fuseau horaire absent')
            if (datetime.now(timezone.utc) - last).total_seconds() > max_age_hours * 3600:
                found.append(f'Dernière sauvegarde datant de plus de {max_age_hours} h')
        except ValueError:
            found.append('Date de sauvegarde invalide')
    return found
