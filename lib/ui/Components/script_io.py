"""
Script Import/Export — bundle scripts as .zip archives with metadata.
"""

import json
import os
import shutil
import tempfile
import time
import zipfile
from pathlib import Path

from . import script_manifest as manifest


def export_script(script_path: str, dest_zip: str) -> bool:
    """
    Export a single script and its metadata to a .zip archive.
    Returns True on success.
    """
    try:
        src = Path(script_path)
        if not src.exists():
            return False
        meta = manifest.get_meta(script_path)
        meta["exported_ts"] = time.time()
        meta["original_filename"] = src.name

        with zipfile.ZipFile(dest_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(str(src), src.name)
            zf.writestr("manifest.json", json.dumps(meta, indent=2, ensure_ascii=False))
        return True
    except Exception:
        return False


def export_multiple(script_paths: list[str], dest_zip: str) -> bool:
    """Export several scripts into one bundle."""
    try:
        with zipfile.ZipFile(dest_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            bundle_meta = []
            for sp in script_paths:
                src = Path(sp)
                if not src.exists():
                    continue
                meta = manifest.get_meta(sp)
                meta["original_filename"] = src.name
                bundle_meta.append(meta)
                zf.write(str(src), src.name)
            zf.writestr("bundle_manifest.json", json.dumps(bundle_meta, indent=2, ensure_ascii=False))
        return True
    except Exception:
        return False


def import_scripts(zip_path: str, scripts_dir: str) -> list[str]:
    """
    Import scripts from a .zip archive into *scripts_dir*.
    Returns list of imported file paths.
    """
    imported: list[str] = []
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            # Read metadata
            meta_map: dict[str, dict] = {}
            if "manifest.json" in zf.namelist():
                meta = json.loads(zf.read("manifest.json"))
                fname = meta.get("original_filename", "")
                if fname:
                    meta_map[fname] = meta
            if "bundle_manifest.json" in zf.namelist():
                bundle = json.loads(zf.read("bundle_manifest.json"))
                for m in bundle:
                    fname = m.get("original_filename", "")
                    if fname:
                        meta_map[fname] = m

            # Extract .py and .pyj files
            for name in zf.namelist():
                if name.endswith((".py", ".pyj")) and not name.startswith("__"):
                    dest = Path(scripts_dir) / name
                    # Avoid overwrite: add suffix
                    if dest.exists():
                        stem = dest.stem
                        suffix = dest.suffix
                        i = 1
                        while dest.exists():
                            dest = Path(scripts_dir) / f"{stem}_{i}{suffix}"
                            i += 1
                    dest.write_bytes(zf.read(name))
                    imported.append(str(dest))
                    # Apply metadata
                    if name in meta_map:
                        meta_map[name].pop("exported_ts", None)
                        meta_map[name]["imported_ts"] = time.time()
                        manifest.set_meta(str(dest), meta_map[name])
        return imported
    except Exception:
        return imported
