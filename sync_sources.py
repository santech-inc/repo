#!/usr/bin/env python3
"""
sync_sources.py — Scan clasic/ and pal/ for IPA/ADP files,
extract metadata, update all three sources JSON, and copy icons.

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
SOURCES_JSON = ROOT / "sources.json"
CLASIC_SOURCES_JSON = ROOT / "clasic.sources.json"
PAL_SOURCES_JSON = ROOT / "pal.sources.json"

MANIFEST_DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

RAW_BASE = "https://raw.githubusercontent.com/santech-inc/repo/main"
REPO_URL = "https://github.com/santech-inc/repo"

SOURCE_TEMPLATE = {
    "name": "SanTech Inc Apps Repo",
    "identifier": "com.santechinc.repo",
    "website": REPO_URL,
    "tintColor": "#007AFF",
}


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
                if len(parts) == 3 and parts[0] == "Payload" and parts[2].endswith(".app"):
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
                    if name.split("/")[-1].lower().endswith(".png"):
                        info = zf.getinfo(name)
                        candidates.append((info.file_size, name))

            if not candidates:
                return False

            candidates.sort(key=lambda x: x[0], reverse=True)
            _, icon_name = candidates[0]
            icon_data = zf.read(icon_name)
            ext = Path(icon_name).suffix or ".png"
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
# JSON builders
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


def make_base_app_fields(entry: dict) -> dict:
    """Build the common app-level fields matching Cizzuk's structure."""
    icon = find_existing_icon(entry["bundleIdentifier"])
    if not icon:
        icon = default_icon_url(entry["bundleIdentifier"])

    name = entry["name"]
    return {
        "name": name,
        "bundleIdentifier": entry["bundleIdentifier"],
        "developerName": entry.get("developerName", "SanTech Inc"),
        "subtitle": "",
        "localizedSubtitles": {"en": ""},
        "localizedDescription": "",
        "localizedDescriptions": {"en": ""},
        "iconURL": icon,
        "tintColor": "#007AFF",
        "category": "utilities",
        "beta": False,
        "screenshots": {},
        "appPermissions": {"entitlements": [], "privacy": {}},
    }


def make_version_entry(entry: dict, download_url: str) -> dict:
    """Build a single version entry."""
    version_entry = {
        "version": entry["version"],
        "buildVersion": entry.get("buildVersion", "1"),
        "date": datetime.now(timezone.utc).strftime(MANIFEST_DATE_FORMAT),
        "size": entry["size"],
        "downloadURL": download_url,
        "localizedDescription": "",
        "localizedDescriptions": {"en": ""},
    }
    if entry.get("minOSVersion"):
        version_entry["minOSVersion"] = entry["minOSVersion"]
    return version_entry


def make_mixed_entry(entry: dict, distribution: str) -> dict:
    """Create a full app entry for sources.json (mixed format)."""
    if distribution == "classic":
        download = f"{RAW_BASE}/clasic/{entry['ipa_path'].name}"
    else:
        download = f"{RAW_BASE}/pal/{entry['adp_dir'].name}/manifest.json"

    result = make_base_app_fields(entry)
    result["distribution"] = distribution
    result["versions"] = [make_version_entry(entry, download)]

    if entry.get("marketplaceID"):
        result["marketplaceID"] = entry["marketplaceID"]

    return result


def make_classic_entry(entry: dict) -> dict:
    """Create a full app entry for clasic.sources.json."""
    result = make_base_app_fields(entry)
    result.pop("screenshots", None)
    result.pop("appPermissions", None)
    result["versions"] = [
        make_version_entry(entry, f"{RAW_BASE}/clasic/{entry['ipa_path'].name}")
    ]
    return result


def make_pal_entry(entry: dict) -> dict:
    """Create a full app entry for pal.sources.json."""
    result = make_base_app_fields(entry)
    result["versions"] = [
        make_version_entry(entry, f"{RAW_BASE}/pal/{entry['adp_dir'].name}/manifest.json")
    ]
    if entry.get("marketplaceID"):
        result["marketplaceID"] = entry["marketplaceID"]
    return result


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
    all_mixed = []
    classic_full = []
    pal_full = []

    for app in ipa_apps:
        all_mixed.append(make_mixed_entry(app, "classic"))
        classic_full.append(make_classic_entry(app))

    for app in adp_apps:
        all_mixed.append(make_mixed_entry(app, "pal"))
        pal_full.append(make_pal_entry(app))

    def merge(existing: list, new_entries: list, key: str) -> list:
        by_key = {}
        for item in existing:
            by_key[item[key]] = item
        for item in new_entries:
            by_key[item[key]] = item
        return list(by_key.values())

    # sources.json (mixed)
    mixed_data = {
        "name": "SanTech Inc Apps Repo",
        "identifier": "com.santechinc.repo",
        "subtitle": "Apps by SanTech Inc for AltStore Classic & PAL",
        "localizedSubtitles": {
            "en": "Apps by SanTech Inc for AltStore Classic & PAL",
        },
        "description": "A curated collection of apps distributed via AltStore. Available for both Classic (sideloading) and PAL (EU/Japan/Brazil marketplace).",
        "localizedDescriptions": {
            "en": "A curated collection of apps distributed via AltStore. Available for both Classic (sideloading) and PAL (EU/Japan/Brazil marketplace).",
        },
        "website": REPO_URL,
        "iconURL": f"{RAW_BASE}/icons/source_icon.png",
        "tintColor": "#007AFF",
        "apps": all_mixed,
    }

    # clasic.sources.json
    existing_clasic = _load_json(CLASIC_SOURCES_JSON)
    clasic_data = {
        **SOURCE_TEMPLATE,
        "subtitle": "Apps by SanTech Inc for AltStore Classic",
        "localizedSubtitles": {
            "en": "Apps by SanTech Inc for AltStore Classic",
        },
        "description": "A curated collection of apps distributed via AltStore Classic. Sideload your favorite apps using AltServer.",
        "localizedDescriptions": {
            "en": "A curated collection of apps distributed via AltStore Classic. Sideload your favorite apps using AltServer.",
        },
        "iconURL": f"{RAW_BASE}/icons/source_icon.png",
        "apps": merge(existing_clasic.get("apps", []), classic_full, "bundleIdentifier"),
    }

    # pal.sources.json
    existing_pal = _load_json(PAL_SOURCES_JSON)
    pal_data = {
        **SOURCE_TEMPLATE,
        "subtitle": "Apps by SanTech Inc for AltStore PAL",
        "localizedSubtitles": {
            "en": "Apps by SanTech Inc for AltStore PAL",
        },
        "description": "A curated collection of apps distributed via AltStore PAL. Available in the EU, Japan, and Brazil.",
        "localizedDescriptions": {
            "en": "A curated collection of apps distributed via AltStore PAL. Available in the EU, Japan, and Brazil.",
        },
        "iconURL": f"{RAW_BASE}/icons/source_icon.png",
        "apps": merge(existing_pal.get("apps", []), pal_full, "bundleIdentifier"),
    }

    files = [
        (SOURCES_JSON, mixed_data),
        (CLASIC_SOURCES_JSON, clasic_data),
        (PAL_SOURCES_JSON, pal_data),
    ]

    for path, data in files:
        content = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        if dry_run:
            print(f"\n--- {path.name} (dry run) ---")
            print(content[:500] + ("..." if len(content) > 500 else ""))
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
