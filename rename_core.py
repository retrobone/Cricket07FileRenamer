import os
import xml.etree.ElementTree as ET
from utils import get_ea_hash, safe_join, move_file_safe
import csv

def run_csv_organizer(folder, script_dir, log_func, is_dry, backup_root, manifest):
    log_func("\n[1/4] Running CSV Organizer")
    
    csv_file = os.path.join(script_dir, "C07Files_Complete.csv")
    
    if not os.path.exists(csv_file):
        log_func(f"[SKIP] CSV file 'C07Files_Complete.csv' not found in the folder.")
        return

    count = 0
    try:
        with open(csv_file, mode='r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                original_path = str(row.get('Absolute Path', '')).strip()
                hash_name = str(row.get('MD5 hashed filename', '')).strip()
                
                # Skip empty rows
                if not original_path:
                    continue
                    
                # Calculate hash on the fly if it's missing in the CSV
                if not hash_name:
                    hash_name = get_ea_hash(original_path)
                
                try:
                    target_path = safe_join(folder, original_path)
                except ValueError as e:
                    log_func(str(e))
                    continue
                
                possible_src = [
                    os.path.join(folder, hash_name),             
                    os.path.join(folder, f"{hash_name}.fsh"),    
                    os.path.join(folder, f"{hash_name}.big")     
                ]
                
                for src in possible_src:
                    if move_file_safe(src, target_path, folder, is_dry, backup_root, manifest, log_func):
                        log_func(f"[CSV] Moved: {os.path.basename(src)} -> {original_path}")
                        count += 1
                        break
                        
    except Exception as e:
        log_func(f"[ERROR] Could not read CSV: {e}")
        return

    log_func(f"CSV Module: Organized {count} files.")


def run_face_recovery(folder, log_func, is_dry, backup_root, manifest):
    log_func("\n[2/4] Running Faces Renamer (0-99999)")
    dir_faces = os.path.join(folder, "players", "heads")
    count = 0
    
    for pid in range(0, 100000):
        h = get_ea_hash(f"players/heads/{pid}.big")
        for src in [h, f"{h}.big"]:
            full_src = os.path.join(folder, src)
            target = os.path.join(dir_faces, f"{pid}.big")
            if move_file_safe(full_src, target, folder, is_dry, backup_root, manifest, log_func):
                log_func(f"[FACE] Renamed: {pid}.big")
                count += 1
                break

        hz = get_ea_hash(f"players/heads/{pid}z.big")
        for src in [hz, f"{hz}.big"]:
            full_src = os.path.join(folder, src)
            target = os.path.join(dir_faces, f"{pid}z.big")
            if move_file_safe(full_src, target, folder, is_dry, backup_root, manifest, log_func):
                log_func(f"[FACE] Recovered: {pid}z.big")
                count += 1
                break
        
        if pid % 10000 == 0 and pid > 0:
            log_func(f"... scanned {pid} IDs ...")

    log_func(f"Face Module: Renamed {count} faces.")


def run_bat_fixer(folder, log_func, is_dry, backup_root, manifest):
    log_func("\n--- [3/4] Running Bat Fixer (0-256) ---")
    dir_bats = os.path.join(folder, "misc", "textures")
    
    try:
        if not os.path.exists(dir_bats):
            os.makedirs(dir_bats)
    except OSError:
        log_func(f"[SKIP] Cannot create bat folder: {dir_bats}")
        return

    count = 0
    for bat_id in range(0, 257):
        tens_val = (bat_id // 10) + 48
        ones_val = (bat_id % 10) + 48
        bugged_name = f"bt{chr(tens_val)}{chr(ones_val)}.fsh"
        
        illegal_chars = '<>:"/\\|?*'
        sanitized_name = bugged_name
        for char in illegal_chars:
            sanitized_name = sanitized_name.replace(char, '_')
            
        if bat_id < 10:
            target_name = f"bt0{bat_id}.fsh" 
        else:
            target_name = f"bt{bat_id}.fsh"

        target_path_full = os.path.join(dir_bats, target_name)
        internal_sanitized_path = os.path.join(dir_bats, sanitized_name)

        if os.path.exists(internal_sanitized_path) and not os.path.exists(target_path_full):
            try:
                if not is_dry:
                    os.rename(internal_sanitized_path, target_path_full)
                    manifest.append({"src": internal_sanitized_path, "dest": target_path_full, "dry_run": False})
                else:
                    manifest.append({"src": internal_sanitized_path, "dest": target_path_full, "dry_run": True})
                log_func(f"[BAT-INTERNAL] Renamed: {sanitized_name} -> {target_name}")
                count += 1
                continue 
            except Exception as e:
                log_func(f"[ERR] Could not rename internal {sanitized_name}: {e}")

        internal_bugged_str = f"misc/textures/{bugged_name}"
        h_bugged = get_ea_hash(internal_bugged_str)

        candidates = [bugged_name, sanitized_name, f"{h_bugged}.fsh", h_bugged]
        for cand in candidates:
            full_src = os.path.join(folder, cand)
            if move_file_safe(full_src, target_path_full, folder, is_dry, backup_root, manifest, log_func):
                log_func(f"[BAT-EXTERNAL] Recovered: {cand} -> {target_name}")
                count += 1
                break
    
    log_func(f"Bat Module: Recovered/Fixed {count} bats.")


def run_stadium_fixer(folder, log_func, is_dry, backup_root, manifest):
    log_func("\n--- [4/4] Running Stadium & Texture Fixer ---")
    xml_full_path = os.path.join(folder, "xml", "config", "stadiumselect.xml")
    dir_stadiums = os.path.join(folder, "stadiums")
    dir_menu_tex = os.path.join(folder, "frontend", "textures")

    if not os.path.exists(xml_full_path):
        log_func(f"[WARN] XML config not found at: {xml_full_path}. Skipping stadiums.")
        return

    try:
        root_xml = ET.parse(xml_full_path).getroot()
    except Exception as e:
        log_func(f"[WARN] Failed to parse XML: {e}. Skipping stadiums.")
        return

    count_models = 0
    count_textures = 0

    for stadium in root_xml.findall('stadium'):
        name_raw = stadium.get('Name')
        texture_tag = stadium.get('Texture')

        if not name_raw or not texture_tag: continue

        clean_name = name_raw.strip().lower().replace(" ", "_")
        clean_texture = texture_tag.strip().lower()

        conditions = []
        if stadium.get('Sunny') == '1': conditions.append("sunny")
        if stadium.get('Night') == '1': conditions.append("night")
        if stadium.get('Overcast') == '1': conditions.append("overcast")

        for cond in conditions:
            model_internal = f"stadiums/{clean_name}.{cond}.big"
            model_hash = get_ea_hash(model_internal)
            
            src_candidates = [model_hash, f"{model_hash}.big"]
            target_file = os.path.join(dir_stadiums, f"{clean_name}.{cond}.big")

            for src in src_candidates:
                full_src = os.path.join(folder, src)
                if move_file_safe(full_src, target_file, folder, is_dry, backup_root, manifest, log_func):
                    log_func(f"[STADIUM] Recovered: {clean_name} ({cond})")
                    count_models += 1
                    break

        menu_internal = f"frontend/textures/stad_{clean_texture}.fsh"
        menu_hash = get_ea_hash(menu_internal)

        src_tex_candidates = [menu_hash, f"{menu_hash}.fsh"]
        target_tex = os.path.join(dir_menu_tex, f"stad_{clean_texture}.fsh")

        for src in src_tex_candidates:
            full_src = os.path.join(folder, src)
            if move_file_safe(full_src, target_tex, folder, is_dry, backup_root, manifest, log_func):
                log_func(f"[TEXTURE] Recovered: stad_{clean_texture}")
                count_textures += 1
                break

    log_func(f"Stadium Module: Recovered {count_models} models and {count_textures} menu textures.")
