$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$roots = @(
    [Environment]::GetFolderPath('Desktop'),
    [Environment]::GetFolderPath('CommonDesktopDirectory'),
    [Environment]::GetFolderPath('StartMenu'),
    [Environment]::GetFolderPath('CommonStartMenu')
) | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -Unique
$knownGames = '(?i)\b(NTE|Neverness|Wuthering|Star Citizen|RSI Launcher|Genshin|Honkai|Zenless|Endfield|Arknights|Tower of Fantasy|Palia|Fortnite|Minecraft|Roblox|Valorant|League of Legends|Overwatch|Diablo|World of Warcraft|Hearthstone|StarCraft|Warcraft|Tarkov|FiveM|RedM|PokeMMO|Guild Wars|Final Fantasy|Keizaal)\b'
$shell = New-Object -ComObject WScript.Shell
$records = @(
    foreach ($root in $roots) {
        Get-ChildItem -LiteralPath $root -Recurse -File -ErrorAction SilentlyContinue |
            Where-Object { $_.Extension -in '.lnk', '.url' } |
            ForEach-Object {
                $file = $_
                if ($file.BaseName -match '(?i)uninstall|repair|crash|support|editor|studio|sdk') { return }
                # A folder named Sunshine Games explicitly opts in any shortcut.
                $optIn = $file.FullName -match '(?i)[\\/]Sunshine Games[\\/]'
                if ($file.Extension -eq '.url') {
                    $url = Get-Content -LiteralPath $file.FullName | Where-Object { $_ -match '^URL=' } | Select-Object -First 1
                    if ($url) {
                        $url = $url.Substring(4)
                        if ($url -match '^(com\.epicgames\.launcher|uplay|battlenet|origin2?|goggalaxy)://' -or $optIn) {
                            [pscustomobject]@{name=$file.BaseName; target=$url; arguments=''; working_dir=''; source=$file.FullName}
                        }
                    }
                } elseif ($optIn -or $file.BaseName -match $knownGames -or $file.FullName -match '(?i)[\\/]Games[\\/]') {
                    $shortcut = $shell.CreateShortcut($file.FullName)
                    [pscustomobject]@{name=$file.BaseName; target=$shortcut.TargetPath; arguments=$shortcut.Arguments; working_dir=$shortcut.WorkingDirectory; source=$file.FullName}
                }
            }
    }
)
ConvertTo-Json -InputObject $records -Depth 4 -Compress
