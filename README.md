<div align="center">

<img src="logo.png" alt="Aniro logo" width="180">

# Aniro

**Your Anime. Your Wallpaper.**

Anime wallpapers for Windows

</div>

Anime wallpaper manager for Windows with a floating liquid-glass-inspired bottom dock.

## Features
- Wallpapers, Favorites, Search and Import in a bottom navigation dock (no sidebar)
- Search SFW anime wallpapers using the Wallhaven API
- Preview, download, and apply wallpapers to the Windows desktop
- Save favorites locally in `%APPDATA%\Aniro\favorites.json`
- Import your own images; filter online wallpapers by minimum resolution

## Run
Install Python 3.11+ on Windows, then:

```powershell
py -m pip install -r requirements.txt
py app.py
```

## Build EXE
Run `build.bat` on Windows; output is `dist\Aniro.exe`.

Alternatively open **Actions → Build Aniro for Windows** in GitHub and download the **Aniro-Windows-EXE** artifact from a successful run. The EXE is portable; this is not an installer.

## Notes
Internet access is required to search Wallhaven. Respect artwork copyright. Supports static wallpapers, not animated wallpapers. The glass dock is a Qt translucent visual effect, not native Windows acrylic. The original W logo is embedded in the app header, window icon, and Windows EXE build.
