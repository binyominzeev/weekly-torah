# Heti Tóra – Hetiszakasz archívum

Ez a projekt egy egyszerű, statikus weboldal, amely a heti Tóra-szakaszokhoz kapcsolódó YouTube videók archívumát jeleníti meg. Az adatokat egy Google Sheets táblázatból olvassa be, majd automatikusan generál egy modern, reszponzív HTML oldalt.

## Főbb jellemzők

- **Automatikus adatfrissítés**: A videók listája Google Sheets-ből frissül.
- **YouTube metaadatok**: A videókhoz tartozó hossz és publikálási dátum automatikusan lekérdezhető a YouTube API segítségével.
- **FTP feltöltés**: Az elkészült oldal automatikusan feltölthető FTP-n keresztül.
- **Reszponzív dizájn**: Mobilbarát, letisztult felület.

## Fájlok

- [`heti-bz.py`](heti-bz.py): A fő Python script, amely letölti az adatokat, generálja az oldalt és feltölti FTP-re.
- [`index.html`](index.html): A generált statikus weboldal.
- [`manifest.json`](manifest.json): PWA manifest, ikonok és metaadatok.
- `config.json`: FTP és egyéb konfigurációs adatok (gitignore-ozva).
- `icon-192.png`, `icon-512.png`: Webapp ikonok (nem részei a repónak).

## Használat

1. **Függőségek telepítése**

   Python 3 szükséges. A következő csomagokat kell telepíteni:

   ```sh
   pip install requests
   ```

2. **Konfiguráció**

   Hozz létre egy `config.json` fájlt az alábbi mintával:

   ```json
   {
     "FTP_HOST": "ftp.szervered.hu",
     "FTP_USER": "felhasznalo",
     "FTP_PASS": "jelszo",
     "FTP_PATH": "/public_html/"
   }
   ```

3. **Futtatás**

   ```sh
   python3 heti-bz.py
   ```

   Ez letölti a Google Sheets adatokat, generálja az `index.html`-t, majd feltölti az FTP-re.

## Google Sheets beállítás

- A script a `SHEET_ID` és `SHEET_GID` alapján tölti le a táblázatot CSV formátumban.
- A táblázatnak legalább `title` és `link` oszlopokat kell tartalmaznia.

## YouTube API kulcs

- A YouTube videók hosszának és publikálási dátumának lekéréséhez szükséges egy [YouTube Data API v3](https://console.developers.google.com/) kulcs.
- A kulcsot a scriptben a `YOUTUBE_API_KEY` változóban kell megadni.

## Licenc

MIT

---

**Készítette:** Binjomin rabbi archívuma alapján  
**Fejlesztő:** [GitHub Copilot](https://github.com/features/copilot)