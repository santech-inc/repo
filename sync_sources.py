#!/usr/bin/env python3
"""
sync_sources.py — Scan clasic/ and pal/ for IPA/ADP files,
extract metadata, update Classic and PAL source JSONs, and copy icons.

Usage:
    python3 sync_sources.py [--dry-run]

Requirements: Python 3.8+ (no external dependencies).
"""

import argparse
import json
import os
import plistlib
import shutil
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CLASIC_DIR = ROOT / "clasic"
PAL_DIR = ROOT / "pal"
ICONS_DIR = ROOT / "icons"
SCREENSHOTS_DIR = ROOT / "screenshots"
CLASIC_SOURCES_JSON = ROOT / "clasic.sources.json"
PAL_SOURCES_JSON = ROOT / "pal.sources.json"

MANIFEST_DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

RAW_BASE = "https://raw.githubusercontent.com/santech-inc/repo/main"
REPO_URL = "https://github.com/santech-inc/repo"


# ---------------------------------------------------------------------------
# IPA helpers
# ---------------------------------------------------------------------------

def read_ipa_info(ipa_path: Path) -> dict | None:
    """Extract Info.plist from an IPA and return key fields."""
    try:
        with zipfile.ZipFile(ipa_path, "r") as zf:
            for name in zf.namelist():
                parts = name.split("/")
                if len(parts) == 3 and parts[0] == "Payload" and parts[2] == "Info.plist":
                    with zf.open(name) as f:
                        plist = plistlib.load(f)
                    return plist
    except (zipfile.BadZipFile, Exception) as e:
        print(f"  [WARN] Could not read {ipa_path.name}: {e}", file=sys.stderr)
    return None


def extract_ipa_icon(ipa_path: Path, dest: Path) -> bool:
    """Try to pull the largest square PNG from the .app as the icon."""
    try:
        with zipfile.ZipFile(ipa_path, "r") as zf:
            app_dir = None
            for name in zf.namelist():
                parts = name.split("/")
                if len(parts) >= 2 and parts[0] == "Payload" and parts[1].endswith(".app"):
                    app_dir = "/".join(parts[:2])
                    break
            if not app_dir:
                return False

            candidates = []
            for name in zf.namelist():
                if not name.startswith(app_dir + "/"):
                    continue
                fname = name.split("/")[-1].lower()
                if fname.endswith(".png") and "icon" in fname:
                    info = zf.getinfo(name)
                    candidates.append((info.file_size, name))
            if not candidates:
                for name in zf.namelist():
                    if not name.startswith(app_dir + "/"):
                        continue
                    fname = name.split("/")[-1].lower()
                    if fname == "appicon60x60@2x.png" or fname == "appicon60x60@3x.png":
                        candidates.append((zf.getinfo(name).file_size, name))
            if not candidates:
                for name in zf.namelist():
                    if not name.startswith(app_dir + "/"):
                        continue
                    fname = name.split("/")[-1].lower()
                    if fname.endswith(".png") and fname.startswith("appicon"):
                        info = zf.getinfo(name)
                        candidates.append((info.file_size, name))
            if not candidates:
                for name in zf.namelist():
                    if not name.startswith(app_dir + "/"):
                        continue
                    if name.split("/")[-1].lower().endswith(".png"):
                        info = zf.getinfo(name)
                        candidates.append((info.file_size, name))

            if not candidates:
                return False

            candidates.sort(key=lambda x: x[0], reverse=True)
            _, icon_name = candidates[0]
            icon_data = zf.read(icon_name)
            dest.write_bytes(icon_data)
            return True
    except Exception as e:
        print(f"  [WARN] Could not extract icon from {ipa_path.name}: {e}", file=sys.stderr)
    return False


# ---------------------------------------------------------------------------
# ADP helpers
# ---------------------------------------------------------------------------

def read_adp_manifest(adp_dir: Path) -> dict | None:
    """Read manifest.json from an ADP directory."""
    manifest = adp_dir / "manifest.json"
    if not manifest.exists():
        for child in adp_dir.iterdir():
            if child.is_dir():
                nested = child / "manifest.json"
                if nested.exists():
                    manifest = nested
                    break
        else:
            print(f"  [WARN] No manifest.json in {adp_dir.name}", file=sys.stderr)
            return None
    try:
        return json.loads(manifest.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"  [WARN] Could not read {manifest}: {e}", file=sys.stderr)
    return None


def extract_adp_icon(adp_dir: Path, dest: Path) -> bool:
    """Try to find an icon file in the ADP directory."""
    icon_names = ["icon.png", "icon@2x.png", "AppIcon.png", "AppIcon@2x.png"]
    for root_dir in [adp_dir, adp_dir / "Assets.xcassets" / "AppIcon.appiconset"]:
        if not root_dir.exists():
            continue
        for name in icon_names:
            candidate = root_dir / name
            if candidate.exists():
                shutil.copy2(candidate, dest)
                return True
    return False


# ---------------------------------------------------------------------------
# Build app entries
# ---------------------------------------------------------------------------

def build_app_entry_from_ipa(ipa_path: Path) -> dict | None:
    plist = read_ipa_info(ipa_path)
    if not plist:
        return None

    bundle_id = plist.get("CFBundleIdentifier", ipa_path.stem)
    version = plist.get("CFBundleShortVersionString", "1.0.0")
    build = plist.get("CFBundleVersion", "1")
    name = plist.get("CFBundleDisplayName") or plist.get("CFBundleName") or ipa_path.stem
    min_os = plist.get("MinimumOSVersion", "")
    size = ipa_path.stat().st_size

    return {
        "name": name,
        "bundleIdentifier": bundle_id,
        "developerName": "SanTech Inc",
        "version": version,
        "buildVersion": build,
        "minOSVersion": min_os,
        "size": size,
        "ipa_path": ipa_path,
    }


def build_app_entry_from_adp(adp_dir: Path, manifest: dict) -> dict | None:
    bundle_id = manifest.get("identifier") or adp_dir.name
    app_info = manifest.get("app", {})
    name = app_info.get("title") or manifest.get("name") or adp_dir.name
    version = manifest.get("version") or app_info.get("version") or "1.0.0"
    build = manifest.get("build") or app_info.get("buildVersion") or "1"
    min_os = manifest.get("minimumOSVersion") or manifest.get("minOSVersion") or ""
    marketplace_id = manifest.get("marketplaceID") or ""

    adp_size = sum(f.stat().st_size for f in adp_dir.rglob("*") if f.is_file())

    entry = {
        "name": name,
        "bundleIdentifier": bundle_id,
        "developerName": "SanTech Inc",
        "version": version,
        "buildVersion": build,
        "minOSVersion": min_os,
        "size": adp_size,
        "adp_dir": adp_dir,
    }
    if marketplace_id:
        entry["marketplaceID"] = marketplace_id
    return entry


# ---------------------------------------------------------------------------
# URL helpers
# ---------------------------------------------------------------------------

def find_existing_icon(bundle_id: str) -> str | None:
    """Check if an icon already exists for this bundle ID (prefer .png)."""
    for ext in (".png", ".svg"):
        name = bundle_id.replace(".", "_") + ext
        if (ICONS_DIR / name).exists():
            return f"{RAW_BASE}/icons/{name}"
    return None


def default_icon_url(bundle_id: str) -> str:
    """Return the expected icon URL for a bundle ID."""
    return f"{RAW_BASE}/icons/{bundle_id.replace('.', '_')}.png"


def _natural_sort_key(value: str) -> list:
    """Sort filenames like 1.png, 2.png, 10.png in numeric order."""
    parts = []
    for piece in value.split(".")[:-1]:
        if piece.isdigit():
            parts.append((0, int(piece)))
        else:
            parts.append((1, piece.lower()))
    return parts


def collect_screenshot_urls(bundle_id: str) -> list[str]:
    """Collect screenshot URLs from the screenshots/ folder for an app.

    Supports both legacy root-level naming like 'com_santech_app_1.png' and the
    newer per-app folder layout: 'screenshots/com.santech.app/1.png' or
    'screenshots/com_santech_app/1.png'.
    """
    urls = []
    if not SCREENSHOTS_DIR.exists():
        return urls

    bundle_variants = {
        bundle_id,
        bundle_id.replace(".", "_"),
        bundle_id.replace(".", "-"),
        bundle_id.replace(".", ""),
    }

    app_folders = [
        p for p in SCREENSHOTS_DIR.iterdir()
        if p.is_dir() and p.name in bundle_variants
    ]

    if app_folders:
        chosen = sorted(app_folders, key=lambda p: p.name)[0]
        files = [
            f for f in sorted(chosen.iterdir(), key=lambda p: _natural_sort_key(p.name))
            if f.is_file() and f.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
        ]
        for f in files:
            urls.append(f"{RAW_BASE}/screenshots/{chosen.name}/{f.name}")
        return urls

    prefix = bundle_id.replace(".", "_")
    for f in sorted(SCREENSHOTS_DIR.glob(f"{prefix}_*.png"), key=lambda p: _natural_sort_key(p.name)):
        urls.append(f"{RAW_BASE}/screenshots/{f.name}")
    if urls:
        return urls

    for f in sorted(SCREENSHOTS_DIR.glob(f"{prefix}*.png"), key=lambda p: _natural_sort_key(p.name)):
        urls.append(f"{RAW_BASE}/screenshots/{f.name}")

    return urls


# ---------------------------------------------------------------------------
# JSON builders — Classic format
# ---------------------------------------------------------------------------

def make_classic_source_entry() -> dict:
    """Create the source-level structure for clasic.sources.json."""
    return {
        "name": "SanTech Inc Apps Repo",
        "identifier": "com.santechinc.repo",
        "subtitle": "Apps by SanTech Inc for AltStore Classic",
        "localizedSubtitles": {"en": "Apps by SanTech Inc for AltStore Classic"},
        "description": "A curated collection of apps distributed via AltStore Classic. Sideload your favorite apps using AltServer.",
        "localizedDescriptions": {
            "en": "A curated collection of apps distributed via AltStore Classic. Sideload your favorite apps using AltServer."
        },
        "website": REPO_URL,
        "iconURL": f"{RAW_BASE}/icons/source_icon_v2.png",
        "tintColor": "#007AFF",
        "featuredApps": [],
        "news": [],
    }


def make_classic_app_entry(entry: dict) -> dict:
    """Create a full app entry for clasic.sources.json."""
    icon = find_existing_icon(entry["bundleIdentifier"])
    if not icon:
        icon = default_icon_url(entry["bundleIdentifier"])

    screenshot_urls = collect_screenshot_urls(entry["bundleIdentifier"])

    app = {
        "name": entry["name"],
        "bundleIdentifier": entry["bundleIdentifier"],
        "developerName": entry.get("developerName", "SanTech Inc"),
        "localizedDescription": "",
        "iconURL": icon,
        "tintColor": "#007AFF",
        "versions": [
            {
                "version": entry["version"],
                "buildVersion": entry.get("buildVersion", "1"),
                "date": datetime.now(timezone.utc).strftime(MANIFEST_DATE_FORMAT),
                "downloadURL": f"{RAW_BASE}/clasic/{entry['ipa_path'].name}",
                "size": entry["size"],
                "localizedDescription": "",
                **({"minOSVersion": entry["minOSVersion"]} if entry.get("minOSVersion") else {}),
            }
        ],
    }
    if screenshot_urls:
        app["screenshotURLs"] = screenshot_urls

    return app


# ---------------------------------------------------------------------------
# JSON builders — PAL format
# ---------------------------------------------------------------------------

def make_pal_source_entry() -> dict:
    """Create the source-level structure for pal.sources.json."""
    return {
        "name": "SanTech Inc Apps Repo",
        "subtitle": "Apps by SanTech Inc for AltStore PAL",
        "localizedSubtitles": {"en": "Apps by SanTech Inc for AltStore PAL"},
        "description": "A curated collection of apps distributed via AltStore PAL. Available in the EU, Japan, and Brazil.",
        "localizedDescriptions": {
            "en": "A curated collection of apps distributed via AltStore PAL. Available in the EU, Japan, and Brazil."
        },
        "website": REPO_URL,
        "iconURL": f"{RAW_BASE}/icons/source_icon_v2.png",
        "tintColor": "#007AFF",
        "featuredApps": [],
    }


def make_pal_app_entry(entry: dict) -> dict:
    """Create a full app entry for pal.sources.json."""
    icon = find_existing_icon(entry["bundleIdentifier"])
    if not icon:
        icon = default_icon_url(entry["bundleIdentifier"])

    screenshot_urls = collect_screenshot_urls(entry["bundleIdentifier"])

    app = {
        "name": entry["name"],
        "bundleIdentifier": entry["bundleIdentifier"],
        "marketplaceID": entry.get("marketplaceID", ""),
        "developerName": entry.get("developerName", "SanTech Inc"),
        "localizedDescription": "",
        "category": "utilities",
        "iconURL": icon,
        "tintColor": "#007AFF",
        "appPermissions": {
            "entitlements": [],
            "privacy": {},
        },
        "screenshots": {"iPhone": screenshot_urls} if screenshot_urls else {},
        "versions": [
            {
                "version": entry["version"],
                "buildVersion": entry.get("buildVersion", "1"),
                "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "downloadURL": f"{RAW_BASE}/pal/{entry['adp_dir'].name}/manifest.json",
                "size": entry["size"],
                "localizedDescription": "",
            }
        ],
    }
    if entry.get("minOSVersion"):
        app["minOSVersion"] = entry["minOSVersion"]

    return app


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def scan_clasic() -> list[dict]:
    apps = []
    if not CLASIC_DIR.exists():
        return apps
    for ipa in sorted(CLASIC_DIR.glob("*.ipa")):
        print(f"  IPA: {ipa.name}")
        entry = build_app_entry_from_ipa(ipa)
        if entry:
            apps.append(entry)
    return apps


def scan_pal() -> list[dict]:
    apps = []
    if not PAL_DIR.exists():
        return apps
    for child in sorted(PAL_DIR.iterdir()):
        if not child.is_dir():
            continue
        manifest = child / "manifest.json"
        if not manifest.exists():
            for sub in child.iterdir():
                if sub.is_dir() and (sub / "manifest.json").exists():
                    manifest = sub / "manifest.json"
                    child = sub
                    break
            else:
                continue
        print(f"  ADP: {child.name}")
        data = read_adp_manifest(child)
        if data:
            entry = build_app_entry_from_adp(child, data)
            if entry:
                apps.append(entry)
    return apps


def extract_icons(ipa_apps: list[dict], adp_apps: list[dict]):
    ICONS_DIR.mkdir(exist_ok=True)
    for app in ipa_apps:
        icon_name = app["bundleIdentifier"].replace(".", "_") + ".png"
        dest = ICONS_DIR / icon_name
        if dest.exists():
            continue
        ok = extract_ipa_icon(app["ipa_path"], dest)
        if ok:
            print(f"    Icon saved: {icon_name}")
        else:
            print(f"    [SKIP] No icon in {app['ipa_path'].name}")

    for app in adp_apps:
        icon_name = app["bundleIdentifier"].replace(".", "_") + ".png"
        dest = ICONS_DIR / icon_name
        if dest.exists():
            continue
        ok = extract_adp_icon(app["adp_dir"], dest)
        if ok:
            print(f"    Icon saved: {icon_name}")
        else:
            print(f"    [SKIP] No icon in {app['adp_dir'].name}")


def write_sources(ipa_apps: list[dict], adp_apps: list[dict], dry_run: bool):
    classic_apps = [make_classic_app_entry(app) for app in ipa_apps]
    pal_apps = [make_pal_app_entry(app) for app in adp_apps]

    def merge(existing: list, new_entries: list, key: str) -> list:
        by_key = {}
        for item in existing:
            if key in item:
                by_key[item[key]] = item
        for item in new_entries:
            by_key[item[key]] = item
        return list(by_key.values())

    def keep_current(existing: list, current_ids: set[str], key: str) -> list:
        return [item for item in existing if item.get(key) in current_ids]

    current_classic_ids = {app["bundleIdentifier"] for app in classic_apps}
    current_pal_ids = {app["bundleIdentifier"] for app in pal_apps}

    # clasic.sources.json
    existing_clasic = _load_json(CLASIC_SOURCES_JSON)
    clasic_data = make_classic_source_entry()
    clasic_data["apps"] = keep_current(
        merge(existing_clasic.get("apps", []), classic_apps, "bundleIdentifier"),
        current_classic_ids,
        "bundleIdentifier",
    )
    clasic_data["featuredApps"] = [
        a["bundleIdentifier"] for a in clasic_data["apps"] if a["bundleIdentifier"] in current_classic_ids
    ]

    # pal.sources.json
    existing_pal = _load_json(PAL_SOURCES_JSON)
    pal_data = make_pal_source_entry()
    pal_data["apps"] = keep_current(
        merge(existing_pal.get("apps", []), pal_apps, "bundleIdentifier"),
        current_pal_ids,
        "bundleIdentifier",
    )
    pal_data["featuredApps"] = [
        a["bundleIdentifier"] for a in pal_data["apps"] if a["bundleIdentifier"] in current_pal_ids
    ]

    files = [
        (CLASIC_SOURCES_JSON, clasic_data),
        (PAL_SOURCES_JSON, pal_data),
    ]

    for path, data in files:
        content = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        if dry_run:
            print(f"\n--- {path.name} (dry run) ---")
            print(content[:800] + ("..." if len(content) > 800 else ""))
        else:
            path.write_text(content, encoding="utf-8")
            print(f"  Written: {path.name}")


def _load_json(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def main():
    parser = argparse.ArgumentParser(description="Sync IPA/ADP files to AltStore source JSONs")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing files")
    args = parser.parse_args()

    print("Scanning clasic/...")
    ipa_apps = scan_clasic()
    print(f"  Found {len(ipa_apps)} IPA(s)\n")

    print("Scanning pal/...")
    adp_apps = scan_pal()
    print(f"  Found {len(adp_apps)} ADP(s)\n")

    if not ipa_apps and not adp_apps:
        print("No apps found. Place .ipa files in clasic/ or ADP folders in pal/.")
        return

    print("Extracting icons...")
    extract_icons(ipa_apps, adp_apps)
    print()

    print("Writing source files...")
    write_sources(ipa_apps, adp_apps, args.dry_run)
    print("\nDone.")


if __name__ == "__main__":
    main()
