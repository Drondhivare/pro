"""Data access layer for User, Role, Permission, UserSession, and LoginHistory."""
from database import fetch_all, fetch_one, execute


def get_user_by_email(email: str) -> dict | None:
    return fetch_one(
        """SELECT u.userId, u.firstName, u.lastName, u.email, u.phone, u.passwordHash,
                  u.isActive, u.accountLocked, u.failedLoginAttempts,
                  u.roleId, r.roleName
           FROM User u JOIN Role r ON r.roleId = u.roleId
           WHERE u.email = %s""",
        (email,),
    )


def get_user_by_id(user_id: int | str) -> dict | None:
    return fetch_one(
        """SELECT u.userId, u.firstName, u.lastName, u.email, u.phone,
                  u.isActive, u.accountLocked, u.lastLogin, r.roleName
           FROM User u JOIN Role r ON r.roleId = u.roleId
           WHERE u.userId = %s""",
        (user_id,),
    )


def get_user_profile(user_id: int | str) -> dict | None:
    return fetch_one(
        """SELECT u.userId, u.firstName, u.lastName, u.email, u.phone,
                  u.lastLogin, r.roleName
           FROM User u JOIN Role r ON r.roleId = u.roleId
           WHERE u.userId = %s""",
        (user_id,),
    )


def list_users() -> list[dict]:
    return fetch_all(
        """SELECT u.userId, u.firstName, u.lastName, u.email, u.phone,
                  u.isActive, u.accountLocked, u.failedLoginAttempts, u.lastLogin, r.roleName
           FROM User u JOIN Role r ON r.roleId = u.roleId
           ORDER BY u.userId"""
    )


def create_user(first_name, last_name, email, phone, password_hash, role_id, is_active=True):
    user_id, _ = execute(
        """INSERT INTO User (firstName, lastName, email, phone, passwordHash, roleId, isActive)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (first_name, last_name, email, phone, password_hash, role_id, is_active),
    )
    return user_id


def update_user_fields(user_id: int | str, fields_dict: dict):
    if not fields_dict:
        return 0
    cols = []
    params = []
    for k, v in fields_dict.items():
        cols.append(f"{k} = %s")
        params.append(v)
    params.append(user_id)
    _, rowcount = execute(f"UPDATE User SET {', '.join(cols)} WHERE userId = %s", params)
    return rowcount


def deactivate_user(user_id: int | str):
    _, rowcount = execute("UPDATE User SET isActive = FALSE WHERE userId = %s", (user_id,))
    return rowcount


def get_user_login_history(user_id: int | str):
    return fetch_all(
        "SELECT * FROM LoginHistory WHERE userId = %s ORDER BY loginTime DESC LIMIT 100", (user_id,)
    )


def list_roles():
    return fetch_all("SELECT * FROM Role ORDER BY roleId")


def list_permissions():
    return fetch_all("SELECT * FROM Permission ORDER BY permissionId")


def get_role_permissions(role_id: int | str):
    return fetch_all(
        """SELECT p.* FROM RolePermission rp
           JOIN Permission p ON p.permissionId = rp.permissionId
           WHERE rp.roleId = %s""",
        (role_id,),
    )


def update_role_permissions(role_id: int | str, permission_ids: list):
    execute("DELETE FROM RolePermission WHERE roleId = %s", (role_id,))
    for pid in permission_ids:
        execute("INSERT INTO RolePermission (roleId, permissionId) VALUES (%s, %s)", (role_id, pid))


def list_sessions():
    return fetch_all(
        """SELECT s.sessionId, s.userId, s.ipAddress, s.userAgent, s.deviceType,
                  s.sessionStatus, s.loginTime, s.loginTime AS lastActivityTime, s.logoutTime, s.expiresAt,
                  u.firstName, u.lastName, u.email, r.roleName
           FROM UserSession s
           JOIN User u ON u.userId = s.userId
           JOIN Role r ON r.roleId = u.roleId
           ORDER BY s.loginTime DESC
           LIMIT 150"""
    )


def revoke_session(session_id: str):
    _, rowcount = execute(
        "UPDATE UserSession SET sessionStatus = 'INVALIDATED', logoutTime = NOW() WHERE sessionId = %s",
        (session_id,),
    )
    return rowcount


def logout_user_sessions(user_id: int | str):
    return execute(
        """UPDATE UserSession SET sessionStatus = 'LOGGED_OUT', logoutTime = NOW()
           WHERE userId = %s AND sessionStatus = 'ACTIVE'""",
        (user_id,),
    )


def record_login_failure(user_id: int, new_failed: int, account_locked: bool, ip_address: str, user_agent: str):
    execute("UPDATE User SET failedLoginAttempts = %s, accountLocked = %s WHERE userId = %s",
            (new_failed, account_locked, user_id))
    execute(
        """INSERT INTO LoginHistory (userId, ipAddress, userAgent, loginStatus, failureReason)
           VALUES (%s, %s, %s, 'FAILED', 'Invalid credentials')""",
        (user_id, ip_address, user_agent[:255]),
    )


def record_login_success(user_id: int, session_id: str, ip_address: str, user_agent: str):
    execute(
        """INSERT INTO UserSession (sessionId, userId, ipAddress, userAgent, deviceType, sessionStatus, expiresAt)
           VALUES (%s, %s, %s, %s, 'Desktop', 'ACTIVE', DATE_ADD(NOW(), INTERVAL 2 HOUR))""",
        (session_id, user_id, ip_address, user_agent[:255]),
    )
    execute("UPDATE User SET lastLogin = NOW(), failedLoginAttempts = 0 WHERE userId = %s", (user_id,))
    execute(
        """INSERT INTO LoginHistory (userId, ipAddress, userAgent, loginStatus)
           VALUES (%s, %s, %s, 'SUCCESS')""",
        (user_id, ip_address, user_agent[:255]),
    )


def reset_password(user_id: int | str, pw_hash: str):
    return execute(
        "UPDATE User SET passwordHash = %s, failedLoginAttempts = 0, accountLocked = FALSE WHERE userId = %s",
        (pw_hash, user_id)
    )
