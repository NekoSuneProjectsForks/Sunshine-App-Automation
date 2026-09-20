# Sunshine Game Importer

This Python script automatically imports your INSTALLED Steam games into Sunshine, a game streaming server, complete with grid images for each game. 

It also imports non-Steam Windows games through game shortcuts, Epic installation
manifests, and a custom game list. Both `python run.py` and `python main.py` work.

## Non-Steam games

Run `uv run run.py --dry-run --no-restart` to preview Steam and non-Steam changes,
or `uv run run.py --non-steam-only --no-restart` to add only non-Steam games.
Omit `--no-restart` to restart Sunshine after saving.

Automatic discovery reads:

- Epic Games installation manifests, using the Epic launcher URI.
- Desktop and Start Menu shortcuts for known games, including NTE, Wuthering
  Waves, Star Citizen / RSI Launcher, HoYo games, FiveM, Roblox, and others.
- Shortcuts in a folder named **Games** and supported game-launcher `.url` shortcuts.
- Any EXE shortcut placed in a **Sunshine Games** folder on your Desktop or Start Menu.

Star Citizen opens RSI Launcher so you can sign in and launch the desired channel.
Launchers use Detached Commands, keeping the stream alive when a launcher exits.
Use Moonlight's Quit Session when finished.

Missing EXE targets are logged and skipped. URI shortcuts may outlive a game
installation, so remove obsolete shortcuts. Automatic discovery cannot identify
every portable game or launcher; use `custom_games.json` for anything else:

```json
[
  {
    "name": "My Game",
    "target": "E:/Games/My Game/launcher.exe",
    "arguments": ["--game", "my-game"],
    "working_dir": "E:/Games/My Game",
    "image_path": "C:/Sunshine_Grids/my-game.png",
    "enabled": true
  }
]
```

Only `name` and `target` are required. Use an absolute EXE path or a supported
Steam, Epic, Ubisoft, Battle.net, EA/Origin, or GOG launcher URI. Arguments may be
a list or the exact argument string from a shortcut. See
`custom_games.example.json` for the three requested games; its paths are examples,
not automatically imported. The SteamGridDB API key is optional and is used only
for Steam artwork. Non-Steam images can be supplied using `image_path`.

`--custom-games PATH` selects another JSON file. `--no-discovery` disables
automatic non-Steam discovery and uses only that file. Custom definitions override
discovery for the same name before importing. Existing Sunshine entries and manual
settings are preserved; edit an already imported entry in Sunshine to change its
launcher. Non-Steam imports are additive and do not remove entries when a drive is
offline. Repeated runs skip matching names and launch commands.

Dry runs do not save apps, download artwork, delete images, or restart processes;
they still write diagnostic logs. Run `uv run python -m unittest -v test_nonsteam`
for the non-Steam importer checks.

Example: 
![IMG_0759](https://github.com/user-attachments/assets/365301a4-57d8-4b5e-a9d6-5ba4573af638)

## Features

- **Automatically detects installed Steam games** with concurrent processing for speed
- **Fetches game names and grid images** from SteamGridDB with retry logic
- **Updates Sunshine's apps.json** with Steam games and their grid images
- **Cross-platform support** for Windows, Linux, and macOS
- **Robust error handling** with comprehensive logging
- **Command-line options** for verbose output, dry runs, and more
- **Environment-based configuration** using .env files
- **Automatic backup** of configuration files before changes

## Prerequisites

Before you begin, ensure you have met the following requirements:

- **Python 3.12 or higher** installed
- **uv package manager** (recommended) or pip
- **Sunshine** installed and configured
- **An optional SteamGridDB API key** for Steam artwork (get one from [SteamGridDB](https://www.steamgriddb.com/profile/preferences/api))

## Installation

### Recommended: Using uv (Fast and Modern)

1. **Install uv** if you haven't already:
   ```bash
   # Windows
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Clone this repository**:
   ```bash
   git clone <repository-url>
   cd Sunshine-App-Automation
   ```

3. **Install dependencies using uv**:
   ```bash
   uv sync
   ```

### Alternative: Using pip

1. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

The script now uses environment variables for configuration. Create a `.env` file in the project directory:

```env
# Required variables
STEAM_LIBRARY_VDF_PATH=C:/Program Files (x86)/Steam/steamapps/libraryfolders.vdf
SUNSHINE_APPS_JSON_PATH=C:/Program Files/Sunshine/config/apps.json
SUNSHINE_GRIDS_FOLDER=C:/Sunshine_Grids
# Optional, for Steam artwork
STEAMGRIDDB_API_KEY=your_api_key_here

# Optional variables (for Windows process restart)
STEAM_EXE_PATH=C:/Program Files (x86)/Steam/steam.exe
SUNSHINE_EXE_PATH=C:/Program Files/Sunshine/sunshine.exe
```

### Path Examples by Platform:

**Windows:**
- Steam Library: `C:/Program Files (x86)/Steam/steamapps/libraryfolders.vdf`
- Sunshine Apps: `C:/Program Files/Sunshine/config/apps.json`
- Grids Folder: `C:/Sunshine_Grids`

**Linux:**
- Steam Library: `/home/username/.local/share/Steam/steamapps/libraryfolders.vdf`
- Sunshine Apps: `/home/username/.config/sunshine/apps.json`
- Grids Folder: `/home/username/.config/sunshine/grids`

**macOS:**
- Steam Library: `/Users/username/Library/Application Support/Steam/steamapps/libraryfolders.vdf`
- Sunshine Apps: `/Users/username/.config/sunshine/apps.json`
- Grids Folder: `/Users/username/.config/sunshine/grids`

## Usage

### Basic Usage

```bash
# Using uv (recommended)
uv run main.py

# Using python directly
python main.py
```

### Command-line Options

```bash
# Verbose logging for debugging
uv run main.py --verbose

# Preview changes without making them
uv run main.py --dry-run

# Skip restarting Steam and Sunshine
uv run main.py --no-restart

# Combine options
uv run main.py --verbose --dry-run
```

### What the script does:

1. **Validates configuration** and checks all required paths
2. **Loads Steam library** and discovers installed games (concurrent processing)
3. **Downloads grid images** from SteamGridDB (with retry logic)
4. **Updates Sunshine configuration** with new games and removes uninstalled ones
5. **Creates backups** of your configuration before making changes
6. **Provides detailed logging** of all operations

## Troubleshooting

### Common Issues

- **Stream closes immediately with a DRM-content warning**: Older Windows imports tracked Steam's short-lived URI launcher as the game process. Run the updated importer to migrate those entries to Sunshine's Detached Commands. The stream stays open after Steam finishes launching; use Moonlight's Quit Session when finished. Existing game names and artwork are preserved.
- **"Invalid argument" errors**: Check your `.env` file paths use forward slashes `/` or double backslashes `\\`
- **"Access Denied" errors**: Run with administrator privileges on Windows
- **API rate limiting**: The script includes automatic retry logic with backoff
- **Missing games**: Some games may not have data available in Steam's API

### Log Files

The script creates detailed logs in `sunshine_automation.log`. Use `--verbose` for more detailed output.

### Environment Variable Issues

If you're having path issues, the script will now:
- Automatically normalize Windows paths
- Validate that required directories exist
- Give clear error messages about what's wrong

### Platform-Specific Notes

**Linux with Flatpak Steam:**
The script automatically detects Flatpak Steam installations and uses the correct command format.

**macOS:**
Steam paths may vary depending on installation method (Steam app vs manual install).

## Contributing

Contributions to improve the script are welcome. Please feel free to submit a Pull Request.

## Changelog

### v2.0 (Latest)
- Complete rewrite with improved architecture
- Environment variable configuration
- Concurrent processing for 10x speed improvement
- Robust error handling and retry logic
- Cross-platform support improvements
- Command-line interface with options
- Automatic backup creation
- Comprehensive logging

### v1.0 (Original)
- Basic Steam game detection
- Simple SteamGridDB integration
- Windows-focused implementation

## Acknowledgements

- [Sunshine](https://github.com/LizardByte/Sunshine) for the game streaming server
- [SteamGridDB](https://www.steamgriddb.com/) for providing the grid images
- [uv](https://github.com/astral-sh/uv) for fast Python package management
