"""
Backup and Restore Service for the Online Examination Platform.

Provides safe database dump creation, listing, metadata validation,
restoration with pre-restore safety snapshots, and secure deletion.
"""
from datetime import datetime
import gzip
import hashlib
import os
import shutil
import subprocess
import tempfile
import threading
import json
import zipfile

from config import Config
from database import fetch_all, fetch_one, execute

# Process-level lock to prevent concurrent backup/restore operations
_backup_lock = threading.RLock()

VALID_EXTENSIONS = {".sql", ".sql.gz", ".zip"}

# The explicitly managed directories for FULL_SYSTEM backups
MANAGED_DIRECTORIES = ["uploads", "media", "storage", "documents", "question_attachments"]

# Sensitive files that must never be restored from a backup
RESTRICTED_FILES = {".env", "config.py", "secrets.json", "credentials.json", "private.key", ".pem"}


def _format_size(num_bytes: int) -> str:
    """Format bytes into human-readable string."""
    for unit in ["B", "KB", "MB", "GB"]:
        if num_bytes < 1024.0:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} TB"


def _resolve_safe_path(filename: str) -> str:
    """
    Ensure the filename is safe, contains no directory traversal,
    has an allowed extension, and resides strictly inside BACKUP_DIR.
    """
    if not filename or not isinstance(filename, str):
        raise ValueError("A valid backup filename must be provided.")

    # Reject path traversal components
    clean_base = os.path.basename(filename.strip())
    if clean_base != filename.strip() or ".." in filename or "/" in filename or "\\" in filename:
        raise ValueError("Invalid filename: directory traversal or nested paths are prohibited.")

    # Enforce extension whitelist
    has_valid_ext = any(clean_base.lower().endswith(ext) for ext in VALID_EXTENSIONS)
    if not has_valid_ext:
        raise ValueError(f"Invalid file extension. Allowed extensions are: {', '.join(sorted(VALID_EXTENSIONS))}")

    real_backup_dir = os.path.realpath(Config.BACKUP_DIR)
    target_path = os.path.realpath(os.path.join(real_backup_dir, clean_base))

    # Verify target stays inside BACKUP_DIR
    if not (target_path.startswith(real_backup_dir + os.sep) or target_path == real_backup_dir):
        raise ValueError("Path security violation: target path escapes backup directory.")

    return target_path


def calculate_checksum(filepath: str) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def calculate_checksum_stream(stream) -> str:
    """Calculate SHA-256 checksum from a file-like stream without reading to disk."""
    sha256_hash = hashlib.sha256()
    for byte_block in iter(lambda: stream.read(4096), b""):
        sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def safe_extract_zip(zf: zipfile.ZipFile, dest_dir: str):
    """
    Safely extract a zip file, rejecting path traversal, absolute paths, and symlinks.
    Validates ALL members before extracting ANY.
    """
    abs_dest = os.path.abspath(dest_dir)
    
    # 1. Validate ALL members first
    for member in zf.namelist():
        # Reject absolute paths and drive letters
        if member.startswith("/") or os.path.isabs(member) or os.path.splitdrive(member)[0]:
            raise ValueError(f"Unsafe absolute path detected in ZIP: {member}")
            
        # Reject path traversal
        if ".." in member.split("/") or ".." in member.split("\\"):
            raise ValueError(f"Unsafe path traversal detected in ZIP: {member}")
            
        # Reject restricted sensitive files
        member_basename = os.path.basename(member.rstrip("/"))
        is_restricted = (
            member_basename in RESTRICTED_FILES or 
            any(part in RESTRICTED_FILES for part in member.replace("\\", "/").split("/")) or
            member_basename.endswith(".pem")
        )
        if is_restricted:
             raise ValueError(f"ZIP contains restricted sensitive file/directory: {member}")
            
        # Check that the final resolved path is safely inside the destination directory
        target_path = os.path.abspath(os.path.join(abs_dest, member))
        if not target_path.startswith(abs_dest + os.sep) and target_path != abs_dest:
             raise ValueError(f"ZIP path attempts to escape destination directory: {member}")
             
        # Reject symlinks (0xA000 indicates symlink in external_attr)
        info = zf.getinfo(member)
        is_symlink = (info.external_attr >> 16) & 0xA000 == 0xA000
        if is_symlink:
             raise ValueError(f"ZIP contains unsafe symlink: {member}")
             
    # 2. If validation passes, extract all
    zf.extractall(dest_dir)


def validate_backup_file(filename: str) -> tuple[bool, str]:
    """
    Perform preliminary safety and header-signature validation on a backup file.
    Does not claim full semantic validity, only structural/header integrity.
    """
    try:
        target_path = _resolve_safe_path(filename)
    except ValueError as e:
        return False, str(e)

    if not os.path.isfile(target_path):
        return False, "Backup file does not exist on disk."

    size = os.path.getsize(target_path)
    if size == 0:
        return False, "Backup file is empty (0 bytes)."

    # Preliminary signature check
    lower_name = filename.lower()
    header_chunk = b""
    try:
        if lower_name.endswith(".zip"):
            with zipfile.ZipFile(target_path, "r") as zf:
                if "manifest.json" not in zf.namelist():
                    return False, "Corrupted archive: Missing manifest.json."
            return True, "Preliminary validation passed: Valid ZIP containing manifest."
        elif lower_name.endswith(".sql.gz"):
            # Check gzip magic bytes \x1f\x8b
            with open(target_path, "rb") as raw_f:
                magic = raw_f.read(2)
                if magic != b"\x1f\x8b":
                    return False, "Corrupted archive: Invalid gzip magic header."
            with gzip.open(target_path, "rb") as gz_f:
                header_chunk = gz_f.read(4096)
        else:
            with open(target_path, "rb") as f:
                header_chunk = f.read(4096)
    except Exception as e:
        return False, f"Failed to read backup header: {str(e)}"

    # Check for MySQL dump signatures
    valid_signatures = [
        b"MySQL dump",
        b"/*!40101",
        b"/*!40014",
        b"CREATE TABLE",
        b"INSERT INTO",
        b"Current Database:",
    ]
    if any(sig in header_chunk for sig in valid_signatures):
        return True, "Preliminary validation passed: Valid MySQL dump header recognized."

    return False, "Preliminary validation failed: Missing recognizable MySQL dump signature."


def get_backup_metadata(filename: str) -> dict:
    """Return detailed metadata for a specific backup file."""
    target_path = _resolve_safe_path(filename)
    if not os.path.isfile(target_path):
        raise FileNotFoundError(f"Backup file '{filename}' was not found.")

    stat = os.stat(target_path)
    is_valid, val_msg = validate_backup_file(filename)
    is_safety = "pre_restore_safety" in filename

    ext = ".zip" if filename.lower().endswith(".zip") else (".sql.gz" if filename.lower().endswith(".sql.gz") else ".sql")
    return {
        "filename": os.path.basename(target_path),
        "size": stat.st_size,
        "size_formatted": _format_size(stat.st_size),
        "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "extension": ext,
        "is_safety_backup": is_safety,
        "validation": {
            "is_valid": is_valid,
            "status": "BASIC_VALID" if is_valid else "INVALID",
            "message": val_msg,
        },
    }


def list_database_backups() -> list[dict]:
    """List all available database backup files with metadata from the database."""
    rows = fetch_all("SELECT * FROM BackupHistory ORDER BY createdAt DESC")
    backups = []
    
    for row in rows:
        meta = {
            "backupId": row["backupId"],
            "filename": row["fileName"],
            "size": row["fileSize"],
            "size_formatted": _format_size(row["fileSize"]),
            "created_at": row["createdAt"].isoformat() if row["createdAt"] else None,
            "created_by": row["createdBy"],
            "status": row["status"],
            "backupType": row["backupType"],
            "is_safety_backup": row["backupType"] == "PRE_RESTORE",
            "verificationStatus": row["verificationStatus"],
            "extension": ".zip" if row["fileName"].lower().endswith(".zip") else (".sql.gz" if row["fileName"].lower().endswith(".sql.gz") else ".sql"),
            "error_message": row["errorMessage"],
        }
        backups.append(meta)

    return backups


def create_database_backup(is_safety_snapshot: bool = False, user_id: int | None = None) -> dict:
    """
    Create a new MySQL database dump using mysqldump via subprocess.run (shell=False).
    Password is passed securely through the environment variable MYSQL_PWD.
    """
    acquired = _backup_lock.acquire(blocking=False)
    if not acquired:
        raise RuntimeError("Another backup or restore operation is currently in progress.")

    backup_id = None
    try:
        os.makedirs(Config.BACKUP_DIR, exist_ok=True)

        prefix = "online_exam_db_pre_restore_safety_" if is_safety_snapshot else "online_exam_db_backup_"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        candidate_name = f"{prefix}{timestamp}.sql"

        target_path = os.path.join(Config.BACKUP_DIR, candidate_name)
        counter = 1
        while os.path.exists(target_path):
            candidate_name = f"{prefix}{timestamp}_{counter}.sql"
            target_path = os.path.join(Config.BACKUP_DIR, candidate_name)
            counter += 1

        backup_type = "PRE_RESTORE" if is_safety_snapshot else "MANUAL"
        
        # Insert initial CREATING record
        backup_id, _ = execute(
            """INSERT INTO BackupHistory (fileName, fileSize, createdBy, status, backupType) 
               VALUES (%s, %s, %s, %s, %s)""",
            (candidate_name, 0, user_id, 'CREATING', backup_type)
        )

        cmd = [
            Config.MYSQLDUMP_PATH,
            "-h", Config.DB_HOST,
            "-P", str(Config.DB_PORT),
            "-u", Config.DB_USER,
            "--single-transaction",
            "--quick",
            "--routines",
            "--triggers",
            "--add-drop-table",
            f"--ignore-table={Config.DB_NAME}.BackupHistory",
            "--databases", Config.DB_NAME,
        ]

        # Pass password strictly through env, never command line args
        sub_env = {**os.environ, "MYSQL_PWD": Config.DB_PASSWORD or ""}

        with open(target_path, "wb") as dump_file:
            res = subprocess.run(
                cmd,
                stdout=dump_file,
                stderr=subprocess.PIPE,
                env=sub_env,
                shell=False,
                timeout=180,
            )

        if res.returncode != 0:
            if os.path.exists(target_path):
                try:
                    os.remove(target_path)
                except OSError:
                    pass
            stderr_text = res.stderr.decode("utf-8", errors="replace").strip()
            execute("UPDATE BackupHistory SET status='FAILED', errorMessage=%s WHERE backupId=%s", (stderr_text, backup_id))
            raise RuntimeError(f"mysqldump failed (code {res.returncode}): {stderr_text}")

        if not os.path.exists(target_path) or os.path.getsize(target_path) == 0:
            if os.path.exists(target_path):
                try:
                    os.remove(target_path)
                except OSError:
                    pass
            execute("UPDATE BackupHistory SET status='FAILED', errorMessage='Empty dump file' WHERE backupId=%s", (backup_id,))
            raise RuntimeError("mysqldump succeeded but generated an empty backup file.")

        # Success: Calculate checksum and update record
        file_size = os.path.getsize(target_path)
        checksum = calculate_checksum(target_path)
        
        execute(
            """UPDATE BackupHistory 
               SET status='COMPLETED', fileSize=%s, checksum=%s, verificationStatus='VERIFIED', verifiedAt=NOW() 
               WHERE backupId=%s""",
            (file_size, checksum, backup_id)
        )

        # Return metadata similar to before but with backupId
        meta = get_backup_metadata(candidate_name)
        meta["backupId"] = backup_id
        return meta

    except Exception as e:
        if backup_id:
            try:
                execute("UPDATE BackupHistory SET status='FAILED', errorMessage=%s WHERE backupId=%s", (str(e), backup_id))
            except:
                pass
        raise e
    finally:
        _backup_lock.release()

def create_full_system_backup(user_id: int | None = None) -> dict:
    """
    Create a full system backup containing the database dump and any persistent application files.
    """
    acquired = _backup_lock.acquire(blocking=False)
    if not acquired:
        raise RuntimeError("Another backup or restore operation is currently in progress.")

    backup_id = None
    temp_dir = tempfile.mkdtemp()
    
    try:
        os.makedirs(Config.BACKUP_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        candidate_name = f"online_exam_full_backup_{timestamp}.zip"
        target_path = os.path.join(Config.BACKUP_DIR, candidate_name)
        
        counter = 1
        while os.path.exists(target_path):
            candidate_name = f"online_exam_full_backup_{timestamp}_{counter}.zip"
            target_path = os.path.join(Config.BACKUP_DIR, candidate_name)
            counter += 1

        # Insert initial CREATING record
        backup_id, _ = execute(
            """INSERT INTO BackupHistory (fileName, fileSize, createdBy, status, backupType) 
               VALUES (%s, %s, %s, %s, %s)""",
            (candidate_name, 0, user_id, 'CREATING', 'FULL_SYSTEM')
        )

        # 1. Database Dump
        db_dump_filename = "database.sql"
        db_dump_path = os.path.join(temp_dir, db_dump_filename)
        cmd = [
            Config.MYSQLDUMP_PATH,
            "-h", Config.DB_HOST,
            "-P", str(Config.DB_PORT),
            "-u", Config.DB_USER,
            "--single-transaction",
            "--quick",
            "--routines",
            "--triggers",
            "--add-drop-table",
            f"--ignore-table={Config.DB_NAME}.BackupHistory",
            "--databases", Config.DB_NAME,
        ]
        sub_env = {**os.environ, "MYSQL_PWD": Config.DB_PASSWORD or ""}
        
        with open(db_dump_path, "wb") as dump_file:
            res = subprocess.run(
                cmd, stdout=dump_file, stderr=subprocess.PIPE,
                env=sub_env, shell=False, timeout=180
            )

        if res.returncode != 0:
            stderr_text = res.stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(f"mysqldump failed (code {res.returncode}): {stderr_text}")

        if not os.path.exists(db_dump_path) or os.path.getsize(db_dump_path) == 0:
            raise RuntimeError("mysqldump succeeded but generated an empty backup file.")

        # 2. Collect persistent files
        project_root = os.path.abspath(os.path.join(Config.BACKUP_DIR, "..", ".."))
        files_to_zip = []  # tuple of (absolute_path, relative_zip_path)
        
        # We also need a database/ directory in the zip
        files_to_zip.append((db_dump_path, f"database/{db_dump_filename}"))
        
        manifest_files = []
        total_uncompressed_size = os.path.getsize(db_dump_path)
        
        manifest_files.append({
            "path": f"database/{db_dump_filename}",
            "size": total_uncompressed_size,
            "checksum": calculate_checksum(db_dump_path)
        })

        for pdir in MANAGED_DIRECTORIES:
            dir_path = os.path.join(project_root, pdir)
            if os.path.isdir(dir_path):
                for root, dirs, files in os.walk(dir_path):
                    for f in files:
                        abs_file_path = os.path.join(root, f)
                        rel_path = os.path.relpath(abs_file_path, project_root)
                        # Avoid path traversal trickery
                        if ".." in rel_path: continue
                        files_to_zip.append((abs_file_path, rel_path.replace("\\", "/")))
                        
                        f_size = os.path.getsize(abs_file_path)
                        total_uncompressed_size += f_size
                        manifest_files.append({
                            "path": rel_path.replace("\\", "/"),
                            "size": f_size,
                            "checksum": calculate_checksum(abs_file_path)
                        })

        # 3. Create manifest.json
        manifest = {
            "backupId": backup_id,
            "backupType": "FULL_SYSTEM",
            "createdAt": datetime.now().isoformat(),
            "applicationName": "Online Examination Platform",
            "databaseName": Config.DB_NAME,
            "databaseDumpFilename": f"database/{db_dump_filename}",
            "files": manifest_files,
            "totalUncompressedSize": total_uncompressed_size
        }
        
        manifest_path = os.path.join(temp_dir, "manifest.json")
        with open(manifest_path, "w") as mf:
            json.dump(manifest, mf, indent=2)
            
        files_to_zip.append((manifest_path, "manifest.json"))

        # 4. Create ZIP archive
        with zipfile.ZipFile(target_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for abs_path, zip_path in files_to_zip:
                zf.write(abs_path, arcname=zip_path)

        # 5. Finalize metadata
        file_size = os.path.getsize(target_path)
        checksum = calculate_checksum(target_path)
        
        execute(
            """UPDATE BackupHistory 
               SET status='COMPLETED', fileSize=%s, checksum=%s, verificationStatus='VERIFIED', verifiedAt=NOW() 
               WHERE backupId=%s""",
            (file_size, checksum, backup_id)
        )

        meta = get_backup_metadata(candidate_name)
        meta["backupId"] = backup_id
        return meta

    except Exception as e:
        if backup_id:
            try:
                execute("UPDATE BackupHistory SET status='FAILED', errorMessage=%s WHERE backupId=%s", (str(e), backup_id))
            except:
                pass
        raise e
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
        _backup_lock.release()

def verify_backup(backup_id: int) -> dict:
    """Verify the integrity of a backup by comparing SHA-256 checksums and deep inspection."""
    record = fetch_one("SELECT * FROM BackupHistory WHERE backupId = %s", (backup_id,))
    if not record:
        raise ValueError("Backup record not found.")

    if record["status"] != "COMPLETED":
        raise ValueError("Cannot verify an incomplete or failed backup.")

    filename = record["fileName"]
    try:
        target_path = _resolve_safe_path(filename)
    except ValueError as e:
        execute("UPDATE BackupHistory SET verificationStatus='FAILED' WHERE backupId=%s", (backup_id,))
        raise e

    if not os.path.isfile(target_path):
        execute("UPDATE BackupHistory SET verificationStatus='FAILED' WHERE backupId=%s", (backup_id,))
        raise FileNotFoundError(f"Backup file '{filename}' does not exist on disk.")

    current_checksum = calculate_checksum(target_path)
    stored_checksum = record["checksum"]

    if current_checksum != stored_checksum:
        execute("UPDATE BackupHistory SET verificationStatus='FAILED' WHERE backupId=%s", (backup_id,))
        return {"success": False, "message": "ZIP Checksum mismatch.", "valid": False, "reason": "ZIP Checksum mismatch", "file": filename}

    # If it's a standard database dump
    if record["backupType"] != "FULL_SYSTEM":
        execute("UPDATE BackupHistory SET verificationStatus='VERIFIED', verifiedAt=NOW() WHERE backupId=%s", (backup_id,))
        return {"success": True, "message": "Verification passed. Checksum matches.", "valid": True, "backupType": record["backupType"]}
        
    # Deep FULL_SYSTEM ZIP Verification
    try:
        with zipfile.ZipFile(target_path, "r") as zf:
            if "manifest.json" not in zf.namelist():
                execute("UPDATE BackupHistory SET verificationStatus='FAILED' WHERE backupId=%s", (backup_id,))
                return {"success": False, "message": "Missing manifest.json.", "valid": False, "reason": "Missing manifest.json", "file": "manifest.json"}
                
            try:
                with zf.open("manifest.json", "r") as mf:
                    manifest = json.loads(mf.read().decode('utf-8'))
            except Exception:
                execute("UPDATE BackupHistory SET verificationStatus='FAILED' WHERE backupId=%s", (backup_id,))
                return {"success": False, "message": "Invalid manifest JSON.", "valid": False, "reason": "Invalid manifest JSON", "file": "manifest.json"}
                
            manifest_files = manifest.get("files", [])
            db_dump_rel = manifest.get("databaseDumpFilename")
            
            if not db_dump_rel:
                execute("UPDATE BackupHistory SET verificationStatus='FAILED' WHERE backupId=%s", (backup_id,))
                return {"success": False, "message": "Missing databaseDumpFilename in manifest.", "valid": False, "reason": "Missing databaseDumpFilename", "file": "manifest.json"}
                
            db_included = False
            
            # Check all manifest files exist in zip and match checksum
            zip_members = set(zf.namelist())
            
            # Reject if there are files in zip not in manifest
            manifest_paths = {f["path"] for f in manifest_files}
            manifest_paths.add("manifest.json")
            for member in zip_members:
                if member not in manifest_paths:
                    # An unmanifested file exists in the zip
                    execute("UPDATE BackupHistory SET verificationStatus='FAILED' WHERE backupId=%s", (backup_id,))
                    return {"success": False, "message": f"Unmanifested file found in ZIP: {member}", "valid": False, "reason": "Unmanifested file", "file": member}
                    
                # Path safety verification for ALL members
                if ".." in member.split("/") or ".." in member.split("\\") or member.startswith("/") or os.path.isabs(member) or os.path.splitdrive(member)[0]:
                    execute("UPDATE BackupHistory SET verificationStatus='FAILED' WHERE backupId=%s", (backup_id,))
                    return {"success": False, "message": f"Unsafe path in ZIP: {member}", "valid": False, "reason": "Unsafe path", "file": member}

            for file_info in manifest_files:
                f_path = file_info["path"]
                if f_path == "manifest.json":
                    continue
                    
                basename = os.path.basename(f_path.rstrip("/"))
                is_restricted = (
                    basename in RESTRICTED_FILES or 
                    any(part in RESTRICTED_FILES for part in f_path.replace("\\", "/").split("/")) or
                    basename.endswith(".pem")
                )
                if is_restricted:
                    execute("UPDATE BackupHistory SET verificationStatus='FAILED' WHERE backupId=%s", (backup_id,))
                    return {"success": False, "message": f"Restricted file in manifest: {f_path}", "valid": False, "reason": "Restricted file", "file": f_path}

                # Must belong to managed directory or database/
                top_level = f_path.replace("\\", "/").split("/")[0]
                if top_level not in MANAGED_DIRECTORIES and top_level != "database":
                    execute("UPDATE BackupHistory SET verificationStatus='FAILED' WHERE backupId=%s", (backup_id,))
                    return {"success": False, "message": f"Path outside managed directories: {f_path}", "valid": False, "reason": "Path outside managed directories", "file": f_path}
                    
                if f_path not in zip_members:
                    execute("UPDATE BackupHistory SET verificationStatus='FAILED' WHERE backupId=%s", (backup_id,))
                    return {"success": False, "message": f"Manifest file missing from ZIP: {f_path}", "valid": False, "reason": "File missing from ZIP", "file": f_path}
                    
                # Verify inner checksum
                with zf.open(f_path, "r") as extracted_file_stream:
                    calc_checksum = calculate_checksum_stream(extracted_file_stream)
                
                if calc_checksum != file_info["checksum"]:
                    execute("UPDATE BackupHistory SET verificationStatus='FAILED' WHERE backupId=%s", (backup_id,))
                    return {"success": False, "message": f"Checksum mismatch for file: {f_path}", "valid": False, "reason": "Checksum mismatch", "file": f_path}
                    
                if f_path == db_dump_rel:
                    db_included = True

            if not db_included:
                execute("UPDATE BackupHistory SET verificationStatus='FAILED' WHERE backupId=%s", (backup_id,))
                return {"success": False, "message": "Database dump not found in verified files.", "valid": False, "reason": "Database dump missing", "file": db_dump_rel}

        execute("UPDATE BackupHistory SET verificationStatus='VERIFIED', verifiedAt=NOW() WHERE backupId=%s", (backup_id,))
        return {
            "success": True, 
            "message": "Full system verification passed.", 
            "valid": True, 
            "backupType": "FULL_SYSTEM", 
            "filesChecked": len(manifest_files), 
            "databaseIncluded": True
        }
    except Exception as e:
        execute("UPDATE BackupHistory SET verificationStatus='FAILED' WHERE backupId=%s", (backup_id,))
        return {"success": False, "message": f"Verification failed: {str(e)}", "valid": False, "reason": "Verification exception", "file": "unknown"}


def restore_database_backup(backup_id: int, user_id: int | None = None) -> dict:
    """
    Restore the database from a verified backup file using its database ID.
    Always creates an automatic pre-restore safety backup prior to restoration.
    """
    record = fetch_one("SELECT * FROM BackupHistory WHERE backupId = %s", (backup_id,))
    if not record:
        raise ValueError("Backup record not found.")

    filename = record["fileName"]
    target_path = _resolve_safe_path(filename)
    
    if not os.path.isfile(target_path):
        raise FileNotFoundError(f"Selected backup file '{filename}' was not found on disk.")

    if record["status"] != "COMPLETED":
        raise ValueError("Cannot restore an incomplete or failed backup.")

    # Integrity verification
    verification_result = verify_backup(backup_id)
    if not verification_result["success"]:
        raise ValueError(f"Integrity check failed: {verification_result['message']}")

    acquired = _backup_lock.acquire(blocking=False)
    if not acquired:
        raise RuntimeError("Another backup or restore operation is currently in progress.")

    try:
        # Create safety backup (will acquire the lock itself safely since it's an RLock)
        safety_meta = create_database_backup(is_safety_snapshot=True, user_id=user_id)

        execute("UPDATE BackupHistory SET status='RESTORING' WHERE backupId=%s", (backup_id,))
        
        # Step 2: Run mysql restore
        cmd = [
            Config.MYSQL_PATH,
            "-h", Config.DB_HOST,
            "-P", str(Config.DB_PORT),
            "-u", Config.DB_USER,
            Config.DB_NAME,
        ]
        sub_env = {**os.environ, "MYSQL_PWD": Config.DB_PASSWORD or ""}

        # Handle decompressed stream if .sql.gz
        if filename.lower().endswith(".sql.gz"):
            with gzip.open(target_path, "rb") as gz_in:
                res = subprocess.run(
                    cmd,
                    input=gz_in.read(),
                    stderr=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    env=sub_env,
                    shell=False,
                    timeout=300,
                )
        else:
            with open(target_path, "rb") as sql_in:
                res = subprocess.run(
                    cmd,
                    stdin=sql_in,
                    stderr=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    env=sub_env,
                    shell=False,
                    timeout=300,
                )

        if res.returncode != 0:
            stderr_text = res.stderr.decode("utf-8", errors="replace").strip()
            execute("UPDATE BackupHistory SET status='RESTORE_FAILED', errorMessage=%s WHERE backupId=%s", (stderr_text, backup_id))
            raise RuntimeError(
                f"MySQL restore failed (exit code {res.returncode}): {stderr_text}. "
                f"A pre-restore safety backup '{safety_meta['filename']}' was preserved for recovery."
            )

        # Step 3: Post-restore verification (connectivity and table count)
        tables = fetch_all(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = %s",
            (Config.DB_NAME,),
        )
        table_count = len(tables) if tables else 0

        if table_count < 28:
            execute("UPDATE BackupHistory SET status='RESTORE_FAILED', errorMessage='Incomplete restore (missing tables)' WHERE backupId=%s", (backup_id,))
            raise RuntimeError(
                f"Database restored but verification found only {table_count}/28 tables. "
                f"Safety snapshot '{safety_meta['filename']}' is available for manual rollback."
            )

        execute("UPDATE BackupHistory SET status='RESTORED', restoredAt=NOW(), restoredBy=%s WHERE backupId=%s", (user_id, backup_id))

        return {
            "success": True,
            "message": "Database restored and verified successfully.",
            "restored_from": filename,
            "safety_backup": safety_meta["filename"],
            "tables_verified": table_count,
            "recovery_notice": (
                f"Pre-restore safety backup '{safety_meta['filename']}' has been created and "
                "preserved. Automatic rollback is not performed; use the safety backup for manual recovery if required."
            ),
        }

    except Exception as e:
        execute("UPDATE BackupHistory SET status='RESTORE_FAILED', errorMessage=%s WHERE backupId=%s", (str(e), backup_id))
        raise e
    finally:
        _backup_lock.release()

def restore_full_system_backup(backup_id: int, user_id: int | None = None) -> dict:
    """
    Restore a full system backup (.zip). Restores both database and files deterministically.
    """
    record = fetch_one("SELECT * FROM BackupHistory WHERE backupId = %s", (backup_id,))
    if not record:
        raise ValueError("Backup record not found.")

    filename = record["fileName"]
    target_path = _resolve_safe_path(filename)
    
    if not os.path.isfile(target_path):
        raise FileNotFoundError(f"Selected backup file '{filename}' was not found on disk.")

    if record["status"] != "COMPLETED":
        raise ValueError("Cannot restore an incomplete or failed backup.")
    
    if record["backupType"] != "FULL_SYSTEM" or not filename.lower().endswith(".zip"):
        raise ValueError("Selected backup is not a FULL_SYSTEM .zip backup.")

    # 1. Integrity Verification FIRST
    verification_result = verify_backup(backup_id)
    if not verification_result["success"]:
        raise ValueError(f"Integrity check failed: {verification_result['message']}")

    acquired = _backup_lock.acquire(blocking=False)
    if not acquired:
        raise RuntimeError("Another backup or restore operation is currently in progress.")

    temp_dir = tempfile.mkdtemp()
    
    try:
        # Extract safely
        with zipfile.ZipFile(target_path, "r") as zf:
            safe_extract_zip(zf, temp_dir)
            
        manifest_path = os.path.join(temp_dir, "manifest.json")
        with open(manifest_path, "r") as mf:
            manifest = json.load(mf)
            
        # 2. Safety Backup
        # Now that zip, manifest, checksums, and paths are completely verified, we take a safety backup.
        safety_meta = create_database_backup(is_safety_snapshot=True, user_id=user_id)

        execute("UPDATE BackupHistory SET status='RESTORING' WHERE backupId=%s", (backup_id,))

        project_root = os.path.abspath(os.path.join(Config.BACKUP_DIR, "..", ".."))
        
        # 3. Restore Database
        db_dump_rel = manifest.get("databaseDumpFilename")
        db_dump_path = os.path.join(temp_dir, os.path.normpath(db_dump_rel))

        cmd = [
            Config.MYSQL_PATH,
            "-h", Config.DB_HOST,
            "-P", str(Config.DB_PORT),
            "-u", Config.DB_USER,
            Config.DB_NAME,
        ]
        sub_env = {**os.environ, "MYSQL_PWD": Config.DB_PASSWORD or ""}

        with open(db_dump_path, "rb") as sql_in:
            res = subprocess.run(
                cmd, stdin=sql_in, stderr=subprocess.PIPE,
                stdout=subprocess.PIPE, env=sub_env, shell=False, timeout=300
            )

        if res.returncode != 0:
            stderr_text = res.stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(f"MySQL restore failed (exit code {res.returncode}): {stderr_text}. Safety snapshot '{safety_meta['filename']}' preserved.")

        # Post-restore database verification
        tables = fetch_all("SELECT table_name FROM information_schema.tables WHERE table_schema = %s", (Config.DB_NAME,))
        table_count = len(tables) if tables else 0
        if table_count < 28:
            raise RuntimeError(f"Database restored but only found {table_count}/28 tables. Safety snapshot '{safety_meta['filename']}' is available for manual rollback.")

        # 4. Restore application files EXACTLY
        # A. Copy all managed files from backup
        backed_up_rel_paths = set()
        for file_info in manifest.get("files", []):
            if file_info["path"].startswith("database/") or file_info["path"] == "manifest.json":
                continue 
                
            src_path = os.path.join(temp_dir, os.path.normpath(file_info["path"]))
            dest_path = os.path.join(project_root, os.path.normpath(file_info["path"]))
            backed_up_rel_paths.add(file_info["path"].replace("\\", "/"))
            
            abs_dest = os.path.abspath(dest_path)
            os.makedirs(os.path.dirname(abs_dest), exist_ok=True)
            shutil.copy2(src_path, abs_dest)
            
        # B. Delete managed files NOT in backup (deterministic restore)
        for pdir in MANAGED_DIRECTORIES:
            dir_path = os.path.join(project_root, pdir)
            if os.path.isdir(dir_path):
                for root, dirs, files in os.walk(dir_path):
                    for f in files:
                        abs_file_path = os.path.join(root, f)
                        rel_path = os.path.relpath(abs_file_path, project_root).replace("\\", "/")
                        
                        if rel_path not in backed_up_rel_paths:
                            # It's inside a managed directory but wasn't in the backup.
                            # Delete it to ensure exact state mapping.
                            try:
                                os.remove(abs_file_path)
                            except OSError:
                                pass # Best effort

        execute("UPDATE BackupHistory SET status='RESTORED', restoredAt=NOW(), restoredBy=%s WHERE backupId=%s", (user_id, backup_id))

        return {
            "success": True,
            "message": "Full system backup restored successfully.",
            "restored_from": filename,
            "safety_backup": safety_meta["filename"],
            "tables_verified": table_count
        }

    except Exception as e:
        execute("UPDATE BackupHistory SET status='RESTORE_FAILED', errorMessage=%s WHERE backupId=%s", (str(e), backup_id))
        raise e
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
        _backup_lock.release()

def delete_database_backup(backup_id: int) -> dict:
    """
    Safely delete a backup file using its database ID.
    Prohibits deletion if only one backup remains on the system.
    Prohibits deletion of the newest pre-restore safety backup.
    """
    record = fetch_one("SELECT * FROM BackupHistory WHERE backupId = %s", (backup_id,))
    if not record:
        raise ValueError("Backup record not found.")

    filename = record["fileName"]
    target_path = _resolve_safe_path(filename)
    
    acquired = _backup_lock.acquire(blocking=False)
    if not acquired:
        raise RuntimeError("Another backup, restore, or delete operation is currently in progress.")

    try:
        all_backups = list_database_backups()

        if len(all_backups) <= 1:
            raise ValueError("Deletion prohibited: cannot delete the only remaining backup.")

        if "pre_restore_safety" in filename:
            safety_backups = [b for b in all_backups if b["is_safety_backup"]]
            if safety_backups and safety_backups[0]["filename"] == filename:
                raise ValueError(
                    "Deletion prohibited: The latest pre-restore safety backup is protected as a recovery safeguard."
                )

        if os.path.exists(target_path):
            os.remove(target_path)
            
        execute("DELETE FROM BackupHistory WHERE backupId = %s", (backup_id,))
        
        return {
            "success": True,
            "message": f"Backup '{filename}' was successfully deleted.",
            "filename": filename,
        }
    finally:
        _backup_lock.release()

def get_backup_system_status() -> dict:
    """Return system readiness, detected binary availability, and backup statistics."""
    os.makedirs(Config.BACKUP_DIR, exist_ok=True)
    mysqldump_ok = bool(Config.MYSQLDUMP_PATH and os.path.isfile(Config.MYSQLDUMP_PATH))
    mysql_ok = bool(Config.MYSQL_PATH and os.path.isfile(Config.MYSQL_PATH))

    backups = list_database_backups()
    total_size = sum(b["size"] for b in backups)

    return_val = {
        "status": "READY" if (mysqldump_ok and mysql_ok) else "DEGRADED",
        "mysqldump_available": mysqldump_ok,
        "mysql_available": mysql_ok,
        "backup_directory_ready": os.path.isdir(Config.BACKUP_DIR),
        "total_backups": len(backups),
        "total_size_bytes": total_size,
        "total_size_formatted": _format_size(total_size),
        "is_locked": not _backup_lock.acquire(blocking=False),
        "latest_backup": backups[0] if backups else None,
    }
    
    # Release the lock if we just acquired it for the status check
    if not return_val["is_locked"]:
        _backup_lock.release()
        
    return return_val
