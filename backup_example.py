"""Example adapter: run a simple backup and write its machine-readable report."""
import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description='Sauvegarde incrémentale simple avec rapport JSON.')
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    parser.add_argument('--report', type=Path, default=Path.home() / 'backup-report.json')
    args = parser.parse_args()
    source, destination = args.source.resolve(), args.destination.resolve()
    if not source.is_dir() or not destination.is_dir() or source == destination or source in destination.parents or destination in source.parents:
        parser.error('Source ou destination introuvable, ou dossiers imbriqués. Crée la destination sur le disque monté avant la sauvegarde.')
    copied, errors = 0, []
    for path in source.rglob('*'):
        if not path.is_file() or path.is_symlink():
            continue
        target = destination / path.relative_to(source)
        try:
            stat = path.stat()
            if target.exists() and target.stat().st_size == stat.st_size and target.stat().st_mtime_ns == stat.st_mtime_ns:
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
            copied += 1
        except OSError as exc:
            errors.append(f'{path}: {exc}')
    report = {'finished_at': datetime.now(timezone.utc).isoformat(), 'status': 'error' if errors else 'ok', 'copied': copied, 'errors': errors}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    temp = args.report.with_name(args.report.name + '.tmp')
    temp.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    temp.replace(args.report)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if errors:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
