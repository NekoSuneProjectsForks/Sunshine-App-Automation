"""Additive non-Steam discovery; never execute games during an import."""
import json
import logging
import os
from pathlib import Path
import subprocess
from urllib.parse import quote


GAME_PROTOCOLS = ('com.epicgames.launcher://', 'uplay://', 'battlenet://',
                  'origin://', 'origin2://', 'goggalaxy://', 'steam://')


def make_app(record):
    """Validate an explicit target and retain launcher arguments and cwd."""
    name = str(record.get('name', '')).strip()
    target = os.path.expandvars(str(record.get('target', ''))).strip()
    if not name or not target:
        logging.warning('Skipping non-Steam entry with missing name or target: %s', name)
        return None
    if any(c in target for c in ('\n', '\r', '"')):
        logging.warning('Skipping invalid target for %s', name)
        return None
    arguments = record.get('arguments', '')
    if isinstance(arguments, list):
        arguments = subprocess.list2cmdline([str(arg) for arg in arguments])
    if not isinstance(arguments, str) or '\n' in arguments or '\r' in arguments:
        raise ValueError(f'Invalid arguments for {name}')
    if target.lower().startswith(GAME_PROTOCOLS):
        command = f'"{target}"'
        working_dir = ''
    else:
        executable = Path(target)
        if not executable.is_file():
            logging.warning('Skipping %s: target does not exist: %s', name, target)
            return None
        if executable.suffix.lower() != '.exe':
            logging.warning('Skipping %s: target must be an EXE or supported game URI', name)
            return None
        command = f'"{executable}"'
        working_dir = os.path.expandvars(record.get('working_dir', '') or str(executable.parent))
        if not Path(working_dir).is_dir():
            logging.warning('Invalid working directory for %s; using executable folder', name)
            working_dir = str(executable.parent)
    if arguments:
        command += ' ' + arguments
    # RSI authentication/update flow belongs to the launcher, not StarCitizen.exe.
    if name.casefold() == 'rsi launcher':
        name = 'Star Citizen'
    app = {'name': name, 'cmd': '', 'detached': [command],
           'working-dir': working_dir, 'image-path': record.get('image_path', ''),
           'elevated': False, 'wait-all': False}
    return app


def discover_shortcuts():
    if os.name != 'nt':
        return []
    script = Path(__file__).with_name('discover_shortcuts.ps1')
    try:
        result = subprocess.run(
            ['powershell.exe', '-NoProfile', '-NonInteractive', '-ExecutionPolicy',
             'Bypass', '-File', str(script)], capture_output=True, text=True,
            encoding='utf-8-sig', timeout=180, check=True,
            creationflags=subprocess.CREATE_NO_WINDOW)
        records = json.loads(result.stdout or '[]')
        return records if isinstance(records, list) else [records]
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        logging.warning('Shortcut discovery failed: %s', exc)
        return []


def discover_epic(manifest_dir=None):
    directory = Path(manifest_dir or Path(os.environ.get('PROGRAMDATA', 'C:/ProgramData')) /
                     'Epic/EpicGamesLauncher/Data/Manifests')
    records = []
    for path in sorted(directory.glob('*.item')):
        try:
            data = json.loads(path.read_text(encoding='utf-8-sig'))
            if data.get('bIsIncompleteInstall') or not data.get('LaunchExecutable'):
                continue
            install = Path(data.get('InstallLocation', ''))
            if not (install / data['LaunchExecutable']).is_file():
                logging.warning('Skipping Epic game %s: executable missing', data.get('DisplayName', path.stem))
                continue
            app_id = data['AppName']
            if data.get('CatalogNamespace') and data.get('CatalogItemId'):
                app_id = ':'.join([data['CatalogNamespace'], data['CatalogItemId'], app_id])
            records.append({'name': data['DisplayName'],
                            'target': 'com.epicgames.launcher://apps/' + quote(app_id, safe='') + '?action=launch&silent=true'})
        except (OSError, ValueError, KeyError, TypeError) as exc:
            logging.warning('Skipping Epic manifest %s: %s', path.name, exc)
    return records


def load_custom(path):
    path = Path(path)
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding='utf-8-sig'))
    if not isinstance(data, list) or any(not isinstance(row, dict) for row in data):
        raise ValueError('Custom games JSON must contain a list of game objects')
    return [row for row in data if row.get('enabled', True)]


def discover_games(custom_path, auto=True):
    records = (discover_epic() + discover_shortcuts()) if auto and os.name == 'nt' else []
    # Explicit custom definitions take precedence over discovered definitions.
    records.extend(load_custom(custom_path))
    apps = {}
    for record in records:
        app = make_app(record)
        if app:
            apps[app['name'].casefold()] = app
    logging.info('Found %s valid non-Steam games/launchers', len(apps))
    return list(apps.values())


def merge_games(existing, discovered):
    """Keep manual settings and offline entries; add only unseen games."""
    result = list(existing)
    names = {app.get('name', '').casefold() for app in result}
    commands = set()
    for app in result:
        detached = app.get('detached') or []
        if isinstance(detached, str):
            detached = [detached]
        commands.update(str(cmd).strip().casefold() for cmd in detached)
        if app.get('cmd'):
            commands.add(app['cmd'].strip().casefold())
    for app in discovered:
        command = app['detached'][0].strip().casefold()
        if app['name'].casefold() in names or command in commands:
            continue
        result.append(app)
        names.add(app['name'].casefold())
        commands.add(command)
        logging.info('Adding non-Steam game: %s', app['name'])
    return result
