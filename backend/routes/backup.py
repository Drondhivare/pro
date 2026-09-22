"""
Backup and Restore management endpoints.
All endpoints require Administrator role privileges (@role_required("Admin")).
"""
from datetime import datetime
import os

from flask import Blueprint, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename

from auth_utils import role_required
from config import Config
from database import log_audit, execute, fetch_one
from services.backup_service import (
    create_database_backup,
    delete_database_backup,
    get_backup_metadata,
    get_backup_system_status,
    list_database_backups,
    restore_database_backup,
    validate_backup_file,
    verify_backup,
    calculate_checksum,
    VALID_EXTENSIONS,
    create_full_system_backup,
    restore_full_system_backup,
)
from utils.helpers import get_auth_user, get_client_ip, get_user_agent

backup_bp = Blueprint("backup_bp", __name__)

MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100 MB


@backup_bp.get("/system/backup/status")
@role_required("Admin")
def backup_status():
    """Return operational readiness and status of backup binaries and storage."""
    try:
        status_info = get_backup_system_status()
        return jsonify(status_info), 200
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve backup system status: {str(e)}"}), 500


@backup_bp.get("/system/backups")
@role_required("Admin")
def list_backups():
    """List all available backup snapshots with metadata and validation status."""
    try:
        backups = list_database_backups()
        return jsonify({"backups": backups}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve backups list: {str(e)}"}), 500


@backup_bp.post("/system/backups")
@role_required("Admin")
def trigger_backup():
    """Trigger an immediate full database snapshot."""
    user_id, _ = get_auth_user()
    try:
        backup_meta = create_database_backup(is_safety_snapshot=False, user_id=user_id)
        log_audit(
            user_id=user_id,
            entity_name="DatabaseBackup",
            entity_id=backup_meta.get("backupId", 0),
            action="EXPORT",
            new_val={"filename": backup_meta["filename"], "size": backup_meta["size"]},
            ip_address=get_client_ip(),
            user_agent=get_user_agent(),
        )
        return jsonify({
            "success": True,
            "message": "Database backup created successfully.",
            "backup": backup_meta,
        }), 201
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 409
    except Exception as e:
        print(f"[ERROR] Backup operation failed: {e}")
        return jsonify({"error": "Backup operation failed due to a server-side filesystem or database error."}), 500


@backup_bp.post("/system/backups/full")
@role_required("Admin")
def trigger_full_backup():
    """Trigger an immediate full system snapshot (.zip)."""
    user_id, _ = get_auth_user()
    try:
        backup_meta = create_full_system_backup(user_id=user_id)
        log_audit(
            user_id=user_id,
            entity_name="DatabaseBackup",
            entity_id=backup_meta.get("backupId", 0),
            action="EXPORT",
            new_val={"filename": backup_meta["filename"], "size": backup_meta["size"], "type": "FULL_SYSTEM"},
            ip_address=get_client_ip(),
            user_agent=get_user_agent(),
        )
        return jsonify({
            "success": True,
            "message": "Full system backup created successfully.",
            "backup": backup_meta,
        }), 201
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 409
    except Exception as e:
        print(f"[ERROR] Full Backup operation failed: {e}")
        return jsonify({"error": "Backup operation failed due to a server-side filesystem or database error."}), 500



@backup_bp.get("/system/backups/<int:backup_id>/download")
@role_required("Admin")
def download_backup(backup_id):
    """Download a verified database backup file securely."""
    record = fetch_one("SELECT fileName FROM BackupHistory WHERE backupId = %s", (backup_id,))
    if not record:
        return jsonify({"error": "Backup record not found."}), 404

    filename = record["fileName"]
    target_path = os.path.join(Config.BACKUP_DIR, os.path.basename(filename))
    if not os.path.isfile(target_path):
        return jsonify({"error": f"Backup file '{filename}' was not found."}), 404

    user_id, _ = get_auth_user()
    log_audit(
        user_id=user_id,
        entity_name="DatabaseBackup",
        entity_id=backup_id,
        action="EXPORT",
        new_val={"filename": filename, "event": "DOWNLOAD"},
        ip_address=get_client_ip(),
        user_agent=get_user_agent(),
    )
    return send_from_directory(Config.BACKUP_DIR, os.path.basename(filename), as_attachment=True)


@backup_bp.post("/system/backups/upload")
@role_required("Admin")
def upload_backup():
    """
    Upload a .sql or .sql.gz backup file.
    Does not automatically restore the file.
    Validates structure, calculates checksum and assigns a server-generated safe filename.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file part in the multipart request."}), 400

    file = request.files["file"]
    if not file or not file.filename:
        return jsonify({"error": "No file selected for upload."}), 400

    original_filename = secure_filename(file.filename)
    lower_name = original_filename.lower()
    ext = None
    if lower_name.endswith(".sql.gz"):
        ext = ".sql.gz"
    elif lower_name.endswith(".sql"):
        ext = ".sql"

    if not ext:
        return jsonify({
            "error": "Unsupported file format. Only .sql and .sql.gz files are permitted."
        }), 400

    user_id, _ = get_auth_user()
    
    # Generate an isolated safe filename with collision-protection loop
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    counter = 1
    safe_filename = f"online_exam_db_uploaded_{timestamp}{ext}"
    dest_path = os.path.join(Config.BACKUP_DIR, safe_filename)

    # Atomic exclusive reservation loop to prevent simultaneous upload collisions
    while True:
        try:
            fd = os.open(dest_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            break
        except FileExistsError:
            safe_filename = f"online_exam_db_uploaded_{timestamp}_{counter}{ext}"
            dest_path = os.path.join(Config.BACKUP_DIR, safe_filename)
            counter += 1

    backup_id = None
    try:
        file.save(dest_path)
    except Exception as e:
        if os.path.exists(dest_path):
            try:
                os.remove(dest_path)
            except OSError:
                pass
        print(f"[ERROR] Failed to save uploaded file: {e}")
        return jsonify({"error": "Upload failed due to a server-side filesystem error."}), 500

    # Validate file size
    if not os.path.exists(dest_path) or os.path.getsize(dest_path) == 0:
        if os.path.exists(dest_path):
            try:
                os.remove(dest_path)
            except OSError:
                pass
        return jsonify({"error": "Uploaded file is empty (0 bytes)."}), 400

    if os.path.getsize(dest_path) > MAX_UPLOAD_SIZE:
        try:
            os.remove(dest_path)
        except OSError:
            pass
        return jsonify({"error": f"Uploaded file exceeds maximum limit of {MAX_UPLOAD_SIZE // (1024*1024)} MB."}), 400

    # Preliminary validation of SQL/gzip structure
    is_valid, msg = validate_backup_file(safe_filename)
    if not is_valid:
        try:
            os.remove(dest_path)
        except OSError:
            pass
        return jsonify({"error": f"Uploaded file failed preliminary validation: {msg}"}), 400

    file_size = os.path.getsize(dest_path)
    checksum = calculate_checksum(dest_path)

    # Insert into BackupHistory
    backup_id, _ = execute(
        """INSERT INTO BackupHistory (fileName, fileSize, createdBy, status, checksum, backupType, verificationStatus, verifiedAt)
           VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())""",
        (safe_filename, file_size, user_id, 'COMPLETED', checksum, 'UPLOADED', 'VERIFIED')
    )

    log_audit(
        user_id=user_id,
        entity_name="DatabaseBackup",
        entity_id=backup_id,
        action="EXPORT",
        new_val={"filename": safe_filename, "original_filename": original_filename, "event": "UPLOAD"},
        ip_address=get_client_ip(),
        user_agent=get_user_agent(),
    )

    meta = get_backup_metadata(safe_filename)
    meta["backupId"] = backup_id
    
    return jsonify({
        "success": True,
        "message": "Backup uploaded and verified successfully.",
        "backup": meta,
    }), 201


@backup_bp.post("/system/backups/<int:backup_id>/verify")
@role_required("Admin")
def trigger_verify_backup(backup_id):
    """Verify the integrity of a database backup file."""
    user_id, _ = get_auth_user()
    try:
        result = verify_backup(backup_id)
        
        log_audit(
            user_id=user_id,
            entity_name="DatabaseBackup",
            entity_id=backup_id,
            action="UPDATE",
            new_val={"event": "VERIFY", "success": result["success"]},
            ip_address=get_client_ip(),
            user_agent=get_user_agent(),
        )
        return jsonify(result), 200
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        return jsonify({"error": "Verification failed due to a server-side error."}), 500


@backup_bp.post("/system/backups/<int:backup_id>/restore")
@role_required("Admin")
def restore_backup(backup_id):
    """
    Restore database from selected backup file.
    Requires explicit JSON body {"confirm": true}.
    Automatically generates a pre-restore safety snapshot before restoring.
    """
    data = request.get_json(silent=True) or {}
    if data.get("confirm") is not True:
        return jsonify({
            "error": "Explicit confirmation required. Body must contain 'confirm': true to execute database restoration."
        }), 400

    user_id, _ = get_auth_user()

    try:
        log_audit(
            user_id=user_id,
            entity_name="DatabaseBackup",
            entity_id=backup_id,
            action="UPDATE",
            new_val={"event": "RESTORE_STARTED"},
            ip_address=get_client_ip(),
            user_agent=get_user_agent(),
        )
        
        record = fetch_one("SELECT backupType FROM BackupHistory WHERE backupId = %s", (backup_id,))
        if not record:
            return jsonify({"error": "Backup record not found."}), 404
            
        if record["backupType"] == "FULL_SYSTEM":
            result = restore_full_system_backup(backup_id, user_id=user_id)
        else:
            result = restore_database_backup(backup_id, user_id=user_id)
        
        log_audit(
            user_id=user_id,
            entity_name="DatabaseBackup",
            entity_id=backup_id,
            action="UPDATE",
            new_val={
                "event": "RESTORE_COMPLETED",
                "restored_from": result.get("restored_from"),
                "safety_backup": result.get("safety_backup"),
                "tables_verified": result.get("tables_verified"),
            },
            ip_address=get_client_ip(),
            user_agent=get_user_agent(),
        )
        return jsonify(result), 200
    except FileNotFoundError as e:
        log_audit(user_id=user_id, entity_name="DatabaseBackup", entity_id=backup_id, action="UPDATE", new_val={"event": "RESTORE_FAILED", "error": str(e)}, ip_address=get_client_ip(), user_agent=get_user_agent())
        return jsonify({"error": str(e)}), 404
    except ValueError as e:
        log_audit(user_id=user_id, entity_name="DatabaseBackup", entity_id=backup_id, action="UPDATE", new_val={"event": "RESTORE_FAILED", "error": str(e)}, ip_address=get_client_ip(), user_agent=get_user_agent())
        return jsonify({"error": str(e)}), 400
    except RuntimeError as e:
        log_audit(user_id=user_id, entity_name="DatabaseBackup", entity_id=backup_id, action="UPDATE", new_val={"event": "RESTORE_FAILED", "error": str(e)}, ip_address=get_client_ip(), user_agent=get_user_agent())
        return jsonify({"error": str(e)}), 409
    except Exception as e:
        print(f"[ERROR] Restoration failed: {e}")
        log_audit(user_id=user_id, entity_name="DatabaseBackup", entity_id=backup_id, action="UPDATE", new_val={"event": "RESTORE_FAILED", "error": "Internal server error"}, ip_address=get_client_ip(), user_agent=get_user_agent())
        return jsonify({"error": "Restoration failed due to a server-side filesystem or database error."}), 500


@backup_bp.delete("/system/backups/<int:backup_id>")
@role_required("Admin")
def delete_backup(backup_id):
    """Safely delete a database backup file."""
    user_id, _ = get_auth_user()

    try:
        result = delete_database_backup(backup_id)
        log_audit(
            user_id=user_id,
            entity_name="DatabaseBackup",
            entity_id=backup_id,
            action="DELETE",
            old_val={"filename": result.get("filename")},
            ip_address=get_client_ip(),
            user_agent=get_user_agent(),
        )
        return jsonify(result), 200
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 409
    except Exception as e:
        print(f"[ERROR] Deletion failed: {e}")
        return jsonify({"error": "Deletion failed due to a server-side error."}), 500
