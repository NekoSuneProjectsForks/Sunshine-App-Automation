import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import main
import nonsteam


class NonSteamTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.exe = self.root / 'Game Launcher.exe'
        self.exe.touch()

    def test_launcher_arguments_and_working_directory(self):
        app = nonsteam.make_app({'name': 'Wuthering Waves', 'target': str(self.exe),
                                'arguments': ['--game', 'two words']})
        self.assertEqual(app['cmd'], '')
        self.assertEqual(app['detached'], [f'"{self.exe}" --game "two words"'])
        self.assertEqual(app['working-dir'], str(self.root))

    def test_missing_launcher_and_non_executable_are_rejected(self):
        self.assertIsNone(nonsteam.make_app({'name': 'Missing', 'target': str(self.root / 'absent.exe')}))
        text = self.root / 'notes.txt'
        text.touch()
        self.assertIsNone(nonsteam.make_app({'name': 'Notes', 'target': str(text)}))

    def test_rsi_uses_launcher(self):
        app = nonsteam.make_app({'name': 'RSI Launcher', 'target': str(self.exe)})
        self.assertEqual(app['name'], 'Star Citizen')
        self.assertEqual(app['detached'], [f'"{self.exe}"'])

    def test_merge_preserves_manual_apps_and_deduplicates(self):
        app = nonsteam.make_app({'name': 'Game', 'target': str(self.exe)})
        existing = [{'name': 'Desktop'}, {'name': 'Manual', 'cmd': 'custom', 'image-path': 'art.png'}]
        original = copy.deepcopy(existing)
        merged = nonsteam.merge_games(existing, [app, dict(app, name='Duplicate shortcut')])
        self.assertEqual(len(merged), 3)
        self.assertEqual(existing, original)
        self.assertEqual(nonsteam.merge_games(merged, [app]), merged)

    def test_epic_complete_and_missing_install(self):
        manifest = {'AppName': 'app', 'CatalogNamespace': 'ns', 'CatalogItemId': 'id',
                    'DisplayName': 'Epic Game', 'InstallLocation': str(self.root),
                    'LaunchExecutable': self.exe.name}
        path = self.root / 'game.item'
        path.write_text(json.dumps(manifest))
        records = nonsteam.discover_epic(self.root)
        self.assertEqual(records[0]['target'], 'com.epicgames.launcher://apps/ns%3Aid%3Aapp?action=launch&silent=true')
        self.exe.unlink()
        self.assertEqual(nonsteam.discover_epic(self.root), [])

    def test_custom_disabled_and_override(self):
        path = self.root / 'custom.json'
        record = {'name': 'Game', 'target': str(self.exe), 'arguments': '--custom'}
        path.write_text(json.dumps([record, {'name': 'Disabled', 'enabled': False}]))
        with patch.object(nonsteam, 'discover_epic', return_value=[dict(record, arguments='--auto')]), \
             patch.object(nonsteam, 'discover_shortcuts', return_value=[]):
            apps = nonsteam.discover_games(path)
        self.assertEqual(len(apps), 1)
        self.assertTrue(apps[0]['detached'][0].endswith('--custom'))

    def test_nonsteam_dry_run_never_restarts_or_writes(self):
        config = {'SUNSHINE_APPS_JSON_PATH': 'unused', 'SUNSHINE_GRIDS_FOLDER': 'unused', 'STEAMGRIDDB_API_KEY': ''}
        app = nonsteam.make_app({'name': 'Game', 'target': str(self.exe)})
        with patch('sys.argv', ['run.py', '--non-steam-only', '--dry-run']), \
             patch.object(main, 'setup_logging'), \
             patch.object(main, 'validate_config', return_value=config), \
             patch.object(main, 'discover_games', return_value=[app]), \
             patch.object(main, 'get_sunshine_config', return_value={'apps': [{'name': 'Desktop'}]}), \
             patch.object(main, 'restart_steam') as steam, \
             patch.object(main, 'restart_sunshine') as sunshine, \
             patch.object(main, 'save_sunshine_config') as save, \
             patch.object(main, 'load_installed_games') as scan, \
             patch.object(main.os, 'makedirs') as mkdir:
            main.main()
        for mocked in (steam, sunshine, save, scan, mkdir):
            mocked.assert_not_called()

    def test_nonsteam_only_preserves_steam_entries(self):
        config = {'SUNSHINE_APPS_JSON_PATH': 'unused', 'SUNSHINE_GRIDS_FOLDER': str(self.root), 'STEAMGRIDDB_API_KEY': ''}
        steam_app = {'name': 'VRChat', 'cmd': '', 'detached': ['steam://rungameid/438100'], 'image-path': 'vrchat.png'}
        app = nonsteam.make_app({'name': 'Game', 'target': str(self.exe)})
        with patch('sys.argv', ['run.py', '--non-steam-only', '--no-restart']), \
             patch.object(main, 'setup_logging'), \
             patch.object(main, 'validate_config', return_value=config), \
             patch.object(main, 'discover_games', return_value=[app]), \
             patch.object(main, 'get_sunshine_config', return_value={'apps': [steam_app]}), \
             patch.object(main, 'save_sunshine_config') as save:
            main.main()
        self.assertEqual(save.call_args.args[1]['apps'], [steam_app, app])


if __name__ == '__main__':
    unittest.main()
