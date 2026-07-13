import os
import shutil
import hashlib

def get_ea_hash(path_string):
    normalized = path_string.replace('\\', '/').lower().strip()
    normalized = normalized.replace('-', '_')
    path_no_ext = os.path.splitext(normalized)[0]
    return hashlib.md5(path_no_ext.encode('utf-8')).hexdigest()

def safe_join(root, rel_path):
    rel_path = rel_path.replace("/", os.sep).replace("\\", os.sep)
    rel_path = rel_path.lstrip(os.sep)
    full = os.path.normpath(os.path.join(root, rel_path))
    root_norm = os.path.normpath(root)
    if not full.startswith(root_norm + os.sep) and full != root_norm:
        raise ValueError(f"[BLOCKED] Path escaped root: '{rel_path}' -> '{full}'")
    return full

def move_file_safe(src_path, dest_path, output_root, is_dry_run, backup_root, manifest, log_func):
    if not os.path.exists(src_path):
        return False

    if os.path.exists(dest_path) and os.path.abspath(src_path) != os.path.abspath(dest_path):
        log_func(f"[CONFLICT] Dest already exists, skipping: {dest_path}")
        return False

    if is_dry_run:
        log_func(f"[DRY-RUN] Would move: {os.path.basename(src_path)} -> {os.path.basename(dest_path)}")
        manifest.append({"src": src_path, "dest": dest_path, "dry_run": True})
        return True

    try:
        dest_dir = os.path.dirname(dest_path)
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir, exist_ok=True)
    except OSError as e:
        log_func(f"[SKIP] Could not create folder for {dest_path}. Error: {e}")
        return False

    if backup_root:
        try:
            rel = os.path.relpath(src_path, output_root)
            backup_path = os.path.join(backup_root, rel)
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            if not os.path.exists(backup_path):
                shutil.copy2(src_path, backup_path)
        except Exception as e:
            log_func(f"[WARN] Backup failed for {src_path}: {e}")
            return False 

    try:
        shutil.copy2(src_path, dest_path)
        if os.path.exists(dest_path):
            os.remove(src_path)
            manifest.append({"src": src_path, "dest": dest_path, "dry_run": False})
            return True
    except Exception as e:
        log_func(f"[ERROR] Failed to move {src_path}: {e}")

    return False