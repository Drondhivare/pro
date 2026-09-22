"""Environment-driven configuration for the backend."""
import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))
load_dotenv()


class Config:
    # --- Database (matches schema.sql -> online_exam_db) ---
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", 3306))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "online_exam_db")
    SCHEMA_PATH = os.path.join(BASE_DIR, "schema.sql")

    # --- Auth ---
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-secret-in-.env")
    JWT_ACCESS_TOKEN_EXPIRES_MIN = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MIN", 120))

    # --- Backup & Restore ---
    BACKUP_DIR = os.getenv("BACKUP_DIR", os.path.join(BASE_DIR, "backups"))

    @staticmethod
    def _detect_binary(env_var: str, binary_name: str, fallback_candidates: list[str]) -> str:
        """Find executable from environment variable, PATH, or known directories."""
        env_val = os.getenv(env_var)
        if env_val and os.path.isfile(env_val):
            return env_val
        import shutil
        found = shutil.which(binary_name)
        if found:
            return found
        for candidate in fallback_candidates:
            if os.path.isfile(candidate):
                return candidate
        return binary_name

    MYSQLDUMP_PATH = _detect_binary(
        "MYSQLDUMP_PATH",
        "mysqldump",
        [
            r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe",
            r"C:\Program Files\MySQL\MySQL Server 8.4\bin\mysqldump.exe",
            r"C:\Program Files\MySQL\MySQL Server 8.1\bin\mysqldump.exe",
            r"C:\xampp\mysql\bin\mysqldump.exe",
            "/usr/bin/mysqldump",
            "/usr/local/bin/mysqldump",
        ],
    )

    MYSQL_PATH = _detect_binary(
        "MYSQL_PATH",
        "mysql",
        [
            r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe",
            r"C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe",
            r"C:\Program Files\MySQL\MySQL Server 8.1\bin\mysql.exe",
            r"C:\xampp\mysql\bin\mysql.exe",
            "/usr/bin/mysql",
            "/usr/local/bin/mysql",
        ],
    )


# Automatically create the backup directory if it does not exist
os.makedirs(Config.BACKUP_DIR, exist_ok=True)
