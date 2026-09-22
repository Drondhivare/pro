"""Data access layer for AuditLog, Notification, SystemConfiguration, and FeatureFlags."""
from database import fetch_all, fetch_one, execute


def list_notifications(user_id):
    return fetch_all(
        "SELECT * FROM Notification WHERE userId = %s ORDER BY sentAt DESC LIMIT 100", (user_id,)
    )


def create_notification(user_id, template_id, title, message, notif_type="SYSTEM", channel="IN_APP", priority="NORMAL"):
    notif_id, _ = execute(
        """INSERT INTO Notification (userId, templateId, title, message, notificationType,
                                      deliveryChannel, priority)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (user_id, template_id, title, message, notif_type, channel, priority),
    )
    return notif_id


def mark_notification_read(notification_id, user_id):
    _, rowcount = execute(
        "UPDATE Notification SET isRead = TRUE, readAt = NOW() WHERE notificationId = %s AND userId = %s",
        (notification_id, user_id),
    )
    return rowcount


def mark_all_notifications_read(user_id):
    _, rowcount = execute(
        "UPDATE Notification SET isRead = TRUE, readAt = NOW() WHERE userId = %s AND isRead = FALSE",
        (user_id,)
    )
    return rowcount


def list_audit_logs(user_filter=None, entity_filter=None, action_filter=None, limit=200):
    query = """SELECT al.*, u.firstName, u.lastName, u.email
               FROM AuditLog al
               LEFT JOIN User u ON u.userId = al.userId
               WHERE 1=1"""
    params = []

    if user_filter:
        query += " AND al.userId = %s"
        params.append(user_filter)
    if entity_filter:
        query += " AND al.entityName = %s"
        params.append(entity_filter)
    if action_filter:
        query += " AND al.action = %s"
        params.append(action_filter)

    query += " ORDER BY al.timestamp DESC LIMIT %s"
    params.append(limit)
    return fetch_all(query, params)


def list_system_config():
    return fetch_all("SELECT * FROM SystemConfiguration ORDER BY configurationKey")


def update_system_config(config_key, config_value, user_id):
    old_row = fetch_one("SELECT * FROM SystemConfiguration WHERE configurationKey = %s", (config_key,))
    if not old_row:
        return None
    execute(
        "UPDATE SystemConfiguration SET configurationValue = %s, updatedBy = %s, updatedAt = NOW() WHERE configurationKey = %s",
        (str(config_value), user_id, config_key),
    )
    return old_row


def list_feature_flags():
    return fetch_all("SELECT * FROM FeatureFlag ORDER BY flagName")


def update_feature_flag(flag_id, is_enabled, description):
    old_flag = fetch_one("SELECT * FROM FeatureFlag WHERE flagId = %s", (flag_id,))
    if not old_flag:
        return None
    execute("UPDATE FeatureFlag SET isEnabled = %s, description = %s WHERE flagId = %s",
            (is_enabled, description, flag_id))
    return old_flag


def list_metrics(limit=200):
    return fetch_all(f"SELECT * FROM PerformanceMetric ORDER BY recordedAt DESC LIMIT {limit}")


def list_system_events(limit=50):
    return fetch_all(
        f"""SELECT al.auditLogId AS logId, al.action, al.entityName, al.entityId, al.timestamp, al.ipAddress,
                  u.email, u.firstName, u.lastName
           FROM AuditLog al
           LEFT JOIN User u ON u.userId = al.userId
           ORDER BY al.timestamp DESC LIMIT {limit}"""
    )
