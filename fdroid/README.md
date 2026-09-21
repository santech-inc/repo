# F-Droid metadata

This directory holds only **small, committed text metadata** for apps
published to the self-hosted F-Droid repo — the fastlane-style layout
`fdroidserver` reads:

```
fdroid/metadata/<applicationId>.yml
fdroid/metadata/<applicationId>/<locale>/title.txt
fdroid/metadata/<applicationId>/<locale>/short_description.txt
fdroid/metadata/<applicationId>/<locale>/full_description.txt
fdroid/metadata/<applicationId>/<locale>/changelogs/<versionCode>.txt
fdroid/metadata/<applicationId>/<locale>/images/icon.png
fdroid/metadata/<applicationId>/<locale>/images/phoneScreenshots/*
```

**This is not the served F-Droid index.** The actual repo index
(`index-v1.jar`, `index-v1.json`, `index-v2.json`, `entry.json`), the
extracted icons the index uses, and the `.apk` files themselves are never
committed here — they're uploaded as assets of a single fixed-tag GitHub
Release, **`fdroid-repo`**, in this repo. The F-Droid client adds this repo
at:

```
https://github.com/santech-inc/repo/releases/download/fdroid-repo
```

This directory only exists so the fastlane metadata source has version
history / is browsable in git, mirroring why `clasic.sources.json` /
`pal.sources.json` are committed for AltStore. It's written by each
project's own `scripts/publish_fdroid.py --push --confirm` — never edited by
hand here.
