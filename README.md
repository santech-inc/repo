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
3. Run the sync script:
   ```bash
   python3 sync_sources.py
   ```
   This scans both directories, extracts metadata and icons from the binaries, and updates all three source JSONs automatically.

   Use `--dry-run` to preview changes without writing files.

See the [Wiki](https://github.com/santech-inc/repo/wiki) for detailed instructions.

## License

&copy; 2026 Santech Inc. All rights reserved.
