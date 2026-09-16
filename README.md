# Santech Inc Apps Repo

AltStore source repository for apps by Santech Inc. Distributes apps via both **AltStore Classic** (sideloading) and **AltStore PAL** (EU/Japan/Brazil marketplace).

## Add This Source

### AltStore Classic

Requires [AltServer](https://altstore.io) running on a Mac or PC.

**Deep link** (tap on iOS):
```
altstore-classic://source?url=https://santech-inc.github.io/repo/clasic.sources.json
```

**Manual** — copy this URL and paste it into AltStore > Sources > Add Source:
```
https://santech-inc.github.io/repo/clasic.sources.json
```

### AltStore PAL

Available on iOS 18.0+ in the EU, Japan, and Brazil.

**Deep link** (tap on iOS):
```
altstore-pal://source?url=https://santech-inc.github.io/repo/pal.sources.json
```

**Manual** — copy this URL and paste it into AltStore > Sources > Add Source:
```
https://santech-inc.github.io/repo/pal.sources.json
```

## Source JSON

<details>
<summary><code>sources.json</code> — mixed (Classic + PAL)</summary>

```json
{
  "name": "Santech Inc Apps Repo",
  "identifier": "com.santechinc.repo",
  "subtitle": "Apps by SanTech Inc for AltStore Classic & PAL",
  "description": "A curated collection of apps distributed via AltStore. Available for both Classic (sideloading) and PAL (EU/Japan/Brazil marketplace).",
  "website": "https://github.com/santech-inc/repo",
  "apps": [
    {
      "name": "ExampleApp",
      "bundleIdentifier": "com.santechinc.exampleapp",
      "version": "1.0.0",
      "downloadURL": "./clasic/exampleapp.ipa",
      "distribution": "classic"
    },
    {
      "name": "ExampleApp",
      "bundleIdentifier": "com.santechinc.exampleapp",
      "version": "1.0.0",
      "downloadURL": "./pal/exampleapp/manifest.json",
      "distribution": "pal"
    }
  ]
}
```

</details>

<details>
<summary><code>clasic.sources.json</code> — AltStore Classic</summary>

```json
{
  "name": "SanTech Inc Apps Repo",
  "identifier": "com.santechinc.repo",
  "subtitle": "Apps by SanTech Inc for AltStore Classic",
  "description": "A curated collection of apps distributed via AltStore Classic. Sideload your favorite apps using AltServer.",
  "iconURL": "./icons/source_icon_v2.png",
  "website": "https://github.com/santech-inc/repo",
  "tintColor": "#2D80E4",
  "apps": [
    {
      "name": "ExampleApp",
      "bundleIdentifier": "com.santechinc.exampleapp",
      "developerName": "SanTech Inc",
      "subtitle": "An example app placeholder.",
      "localizedDescription": "This is a placeholder app. Replace with real app data when publishing.",
      "iconURL": "./icons/exampleapp.png",
      "tintColor": "#2D80E4",
      "category": "utilities",
      "versions": [
        {
          "version": "1.0.0",
          "buildVersion": "1",
          "date": "2026-01-01T00:00:00Z",
          "localizedDescription": "Initial release.",
          "downloadURL": "./clasic/exampleapp.ipa",
          "size": 0
        }
      ]
    }
  ]
}
```

</details>

<details>
<summary><code>pal.sources.json</code> — AltStore PAL</summary>

```json
{
  "name": "SanTech Inc Apps Repo",
  "identifier": "com.santechinc.repo",
  "subtitle": "Apps by SanTech Inc for AltStore PAL",
  "description": "A curated collection of apps distributed via AltStore PAL. Available in the EU, Japan, and Brazil.",
  "iconURL": "./icons/source_icon_v2.png",
  "website": "https://github.com/santech-inc/repo",
  "tintColor": "#2D80E4",
  "apps": [
    {
      "name": "ExampleApp",
      "bundleIdentifier": "com.santechinc.exampleapp",
      "marketplaceID": "12345678",
      "developerName": "SanTech Inc",
      "subtitle": "An example app placeholder.",
      "localizedDescription": "This is a placeholder app. Replace with real app data when publishing.",
      "iconURL": "./icons/exampleapp.png",
      "tintColor": "#2D80E4",
      "category": "utilities",
      "versions": [
        {
          "version": "1.0.0",
          "buildVersion": "1",
          "date": "2026-01-01T00:00:00Z",
          "localizedDescription": "Initial release.",
          "downloadURL": "./pal/exampleapp/manifest.json",
          "size": 0
        }
      ]
    }
  ]
}
```

</details>

## Published Apps

| App | Bundle ID | Version | Classic | PAL |
|-----|-----------|---------|---------|-----|
| *No apps published yet* | — | — | — | — |

> This table will be updated as new apps are added to the source.

## Disclaimer

All apps in this repository are provided **"as is"** without warranty of any kind, express or implied. Use at your own risk. The developers are not responsible for any damage, data loss, or issues that may arise from installing or using these apps.

By adding this source to AltStore, you acknowledge that you understand and accept these terms.

## Adding Apps

1. Drop `.ipa` files into `clasic/`.
2. Drop ADP folders (containing `manifest.json`) into `pal/`.
3. Place app screenshots in `screenshots/<bundle-id>/` (for example `screenshots/com.santech.simonInSpaceGame/1.png`).
4. Place optional app metadata files next to the IPA or inside the PAL app folder:
   ```text
   clasic/<bundle_id_slug>.changelog.txt
   clasic/<bundle_id_slug>.description.<locale>.txt
   pal/<app>/<bundle_id_slug>.changelog.txt
   pal/<app>/<bundle_id_slug>.description.<locale>.txt
   ```
   The `en-US` description is preferred for the app-level `localizedDescription`; otherwise, the first available locale is used. All locale files are emitted in `localizedDescriptions`.
5. Run the sync script:
   ```bash
   python3 sync_sources.py
   ```
   This scans both directories, extracts metadata and icons from the binaries, and adds screenshots to each app entry in the source JSONs automatically.
   App descriptions are preserved in memory from the existing source files before stale apps are removed, so they are restored when an app is regenerated. No auxiliary backup file is created.

   Use `--dry-run` to preview changes without writing files.

See the [Wiki](https://github.com/santech-inc/repo/wiki) for detailed instructions.

## License

&copy; 2026 Santech Inc. All rights reserved.
