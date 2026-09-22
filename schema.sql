-- ================================================================
-- ONLINE EXAMINATION SYSTEM
-- PHYSICAL DATABASE DESIGN
-- FINAL EXECUTABLE MYSQL 8 SCHEMA
--
-- Target DBMS : MySQL 8.x
-- Engine      : InnoDB
-- Normal Form : 3NF
-- Tables      : 27
-- ================================================================

CREATE DATABASE IF NOT EXISTS online_exam_db;

USE online_exam_db;

SET FOREIGN_KEY_CHECKS = 0;
-- ================================================================
-- SECTION 1 : SCHEMA CREATION
-- ================================================================

-- ================================================================
-- DOMAIN A — IDENTITY & ACCESS MANAGEMENT
-- ================================================================
-- ================================================================
-- 1. ROLE
-- ================================================================

CREATE TABLE IF NOT EXISTS Role (
    roleId BIGINT AUTO_INCREMENT PRIMARY KEY,
    roleName VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(255) NULL,
    isActive BOOLEAN NOT NULL DEFAULT TRUE,
    createdAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    createdBy BIGINT NULL,
    updatedBy BIGINT NULL,
    CONSTRAINT chk_role_name_len CHECK (CHAR_LENGTH(roleName) >= 3)
) ENGINE=InnoDB;


-- ================================================================
-- 2. PERMISSION
-- ================================================================

CREATE TABLE IF NOT EXISTS Permission (
    permissionId BIGINT AUTO_INCREMENT PRIMARY KEY,
    permissionName VARCHAR(100) NOT NULL,
    moduleName VARCHAR(50) NOT NULL,
    description VARCHAR(255) NULL,
    createdAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_perm_module UNIQUE (permissionName, moduleName),
    CONSTRAINT chk_perm_name_len CHECK (CHAR_LENGTH(permissionName) > 2)
) ENGINE=InnoDB;

-- ================================================================
-- 3. ROLE_PERMISSION
-- ================================================================

CREATE TABLE IF NOT EXISTS RolePermission (
    rolePermissionId BIGINT AUTO_INCREMENT PRIMARY KEY,
    roleId BIGINT NOT NULL,
    permissionId BIGINT NOT NULL,
    grantedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    grantedBy BIGINT NULL,
    CONSTRAINT uq_role_perm UNIQUE (roleId, permissionId),
    CONSTRAINT fk_rp_role FOREIGN KEY (roleId) REFERENCES Role(roleId) ON DELETE CASCADE,
    CONSTRAINT fk_rp_perm FOREIGN KEY (permissionId) REFERENCES Permission(permissionId) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ================================================================
-- 4. USER
-- ================================================================

CREATE TABLE IF NOT EXISTS User (
    userId BIGINT AUTO_INCREMENT PRIMARY KEY,
    firstName VARCHAR(50) NOT NULL,
    lastName VARCHAR(50) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(15) NULL UNIQUE,
    passwordHash TEXT NOT NULL,
    roleId BIGINT NOT NULL,
    isActive BOOLEAN NOT NULL DEFAULT TRUE,
    lastLogin DATETIME NULL,
    failedLoginAttempts INT NOT NULL DEFAULT 0,
    accountLocked BOOLEAN NOT NULL DEFAULT FALSE,
    createdAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    createdBy BIGINT NULL,
    updatedBy BIGINT NULL,
    CONSTRAINT chk_failed_attempts CHECK (failedLoginAttempts >= 0),
    CONSTRAINT fk_user_role FOREIGN KEY (roleId) REFERENCES Role(roleId) ON DELETE RESTRICT,
    CONSTRAINT fk_user_created FOREIGN KEY (createdBy) REFERENCES User(userId) ON DELETE SET NULL,
    CONSTRAINT fk_user_updated FOREIGN KEY (updatedBy) REFERENCES User(userId) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ================================================================
-- 5. UserSession 
-- ================================================================

CREATE TABLE IF NOT EXISTS UserSession (
    sessionId VARCHAR(36) PRIMARY KEY,
    userId BIGINT NOT NULL,
    loginTime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    logoutTime DATETIME NULL,
    ipAddress VARCHAR(45) NOT NULL,
    userAgent TEXT NULL,
    deviceType VARCHAR(30) NULL,
    sessionStatus VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    expiresAt DATETIME NOT NULL,
    CONSTRAINT chk_session_status CHECK (sessionStatus IN ('ACTIVE', 'EXPIRED', 'LOGGED_OUT', 'INVALIDATED')),
    CONSTRAINT fk_session_user FOREIGN KEY (userId) REFERENCES User(userId) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ================================================================
-- 6. LoginHistory
-- ================================================================

CREATE TABLE IF NOT EXISTS LoginHistory (
    loginHistoryId BIGINT AUTO_INCREMENT PRIMARY KEY,
    userId BIGINT NOT NULL,
    loginTime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    logoutTime DATETIME NULL,
    ipAddress VARCHAR(45) NOT NULL,
    userAgent TEXT NULL,
    loginStatus VARCHAR(20) NOT NULL,
    failureReason VARCHAR(255) NULL,
    authenticationMethod VARCHAR(30) NOT NULL DEFAULT 'PASSWORD',
    CONSTRAINT chk_login_status CHECK (loginStatus IN ('SUCCESS', 'FAILED', 'LOCKED')),
    CONSTRAINT chk_auth_method CHECK (authenticationMethod IN ('PASSWORD', 'OTP', 'SSO')),
    CONSTRAINT fk_login_user FOREIGN KEY (userId) REFERENCES User(userId) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ================================================================
-- DOMAIN B — ACADEMIC & EXAMINATION MANAGEMENT
-- ================================================================

-- ================================================================
-- 7. Subject
-- ===============================================================
CREATE TABLE IF NOT EXISTS Subject (
    subjectId BIGINT AUTO_INCREMENT PRIMARY KEY,
    subjectCode VARCHAR(20) NOT NULL UNIQUE,
    subjectName VARCHAR(100) NOT NULL UNIQUE,
    description TEXT NULL,
    credits SMALLINT NULL,
    isActive BOOLEAN NOT NULL DEFAULT TRUE,
    createdAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    createdBy BIGINT NULL,
    updatedBy BIGINT NULL,
    CONSTRAINT chk_credits CHECK (credits >= 0),
    CONSTRAINT fk_sub_created FOREIGN KEY (createdBy) REFERENCES User(userId) ON DELETE SET NULL,
    CONSTRAINT fk_sub_updated FOREIGN KEY (updatedBy) REFERENCES User(userId) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ================================================================
-- 8. Exam
-- ================================================================
CREATE TABLE IF NOT EXISTS Exam (
    examId BIGINT AUTO_INCREMENT PRIMARY KEY,
    subjectId BIGINT NOT NULL,
    examCode VARCHAR(30) NOT NULL UNIQUE,
    examTitle VARCHAR(150) NOT NULL,
    examType VARCHAR(30) NOT NULL,
    totalMarks DECIMAL(6,2) NOT NULL,
    passingMarks DECIMAL(6,2) NOT NULL,
    durationMinutes INT NOT NULL,
    instructions TEXT NULL,
    maximumAttempts SMALLINT NOT NULL DEFAULT 1,
    shuffleQuestions BOOLEAN NOT NULL DEFAULT TRUE,
    shuffleOptions BOOLEAN NOT NULL DEFAULT TRUE,
    negativeMarking BOOLEAN NOT NULL DEFAULT FALSE,
    negativeMarksPerQuestion DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    examStatus VARCHAR(20) NOT NULL DEFAULT 'DRAFT',
    isActive BOOLEAN NOT NULL DEFAULT TRUE,
    createdAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    createdBy BIGINT NULL,
    updatedBy BIGINT NULL,
    CONSTRAINT chk_exam_marks CHECK (totalMarks > 0 AND passingMarks >= 0 AND passingMarks <= totalMarks),
    CONSTRAINT chk_exam_duration CHECK (durationMinutes > 0),
    CONSTRAINT chk_exam_attempts CHECK (maximumAttempts >= 1),
    CONSTRAINT chk_exam_neg_marks CHECK (negativeMarksPerQuestion >= 0),
    CONSTRAINT chk_exam_status CHECK (examStatus IN ('DRAFT', 'SCHEDULED', 'ACTIVE', 'COMPLETED', 'CANCELLED')),
    CONSTRAINT fk_exam_subject FOREIGN KEY (subjectId) REFERENCES Subject(subjectId) ON DELETE RESTRICT,
    CONSTRAINT fk_exam_created FOREIGN KEY (createdBy) REFERENCES User(userId) ON DELETE SET NULL,
    CONSTRAINT fk_exam_updated FOREIGN KEY (updatedBy) REFERENCES User(userId) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ================================================================
-- 9.  ExamSchedule
-- ================================================================

CREATE TABLE IF NOT EXISTS ExamSchedule (
    scheduleId BIGINT AUTO_INCREMENT PRIMARY KEY,
    examId BIGINT NOT NULL,
    startTime DATETIME NOT NULL,
    endTime DATETIME NOT NULL,
    registrationStart DATETIME NULL,
    registrationEnd DATETIME NULL,
    lateEntryMinutes INT NOT NULL DEFAULT 0,
    autoSubmit BOOLEAN NOT NULL DEFAULT TRUE,
    scheduleStatus VARCHAR(20) NOT NULL DEFAULT 'SCHEDULED',
    createdAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_sched_times CHECK (endTime > startTime),
    CONSTRAINT chk_sched_reg_times CHECK (registrationEnd IS NULL OR registrationStart IS NULL OR registrationEnd >= registrationStart),
    CONSTRAINT chk_sched_late_entry CHECK (lateEntryMinutes >= 0),
    CONSTRAINT chk_sched_status CHECK (scheduleStatus IN ('SCHEDULED', 'ONGOING', 'COMPLETED', 'CANCELLED')),
    CONSTRAINT fk_sched_exam FOREIGN KEY (examId) REFERENCES Exam(examId) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ================================================================
-- 10.CandidateRegistration
-- ================================================================


CREATE TABLE IF NOT EXISTS CandidateRegistration (
    registrationId BIGINT AUTO_INCREMENT PRIMARY KEY,
    examId BIGINT NOT NULL,
    userId BIGINT NOT NULL,
    registrationTime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    registrationStatus VARCHAR(20) NOT NULL DEFAULT 'REGISTERED',
    eligibilityVerified BOOLEAN NOT NULL DEFAULT FALSE,
    paymentRequired BOOLEAN NOT NULL DEFAULT FALSE,
    paymentStatus VARCHAR(20) NOT NULL DEFAULT 'NOT_REQUIRED',
    remarks VARCHAR(255) NULL,
    createdAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_exam_user UNIQUE (examId, userId),
    CONSTRAINT chk_reg_status CHECK (registrationStatus IN ('REGISTERED', 'CANCELLED', 'WAITLISTED')),
    CONSTRAINT chk_pay_status CHECK (paymentStatus IN ('NOT_REQUIRED', 'PENDING', 'PAID', 'FAILED')),
    CONSTRAINT fk_cand_exam FOREIGN KEY (examId) REFERENCES Exam(examId) ON DELETE RESTRICT,
    CONSTRAINT fk_cand_user FOREIGN KEY (userId) REFERENCES User(userId) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ================================================================
-- DOMAIN c — QUESTION BANK
-- ================================================================

-- ================================================================
-- 11.  QuestionCategory
-- ================================================================
CREATE TABLE IF NOT EXISTS QuestionCategory (
    categoryId BIGINT AUTO_INCREMENT PRIMARY KEY,
    categoryName VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(255) NULL,
    isActive BOOLEAN NOT NULL DEFAULT TRUE,
    createdAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    createdBy BIGINT NULL,
    updatedBy BIGINT NULL,
    CONSTRAINT chk_cat_name_len CHECK (CHAR_LENGTH(categoryName) >= 3),
    CONSTRAINT fk_cat_created FOREIGN KEY (createdBy) REFERENCES User(userId) ON DELETE SET NULL,
    CONSTRAINT fk_cat_updated FOREIGN KEY (updatedBy) REFERENCES User(userId) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ================================================================
-- 12.DifficultyLevel
-- ================================================================
CREATE TABLE IF NOT EXISTS DifficultyLevel (
    difficultyLevelId BIGINT AUTO_INCREMENT PRIMARY KEY,
    levelName VARCHAR(30) NOT NULL UNIQUE,
    difficultyScore SMALLINT NOT NULL UNIQUE,
    description VARCHAR(255) NULL,
    createdAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_diff_score CHECK (difficultyScore BETWEEN 1 AND 10)
) ENGINE=InnoDB;

-- ================================================================
-- 13.Question
-- ================================================================
CREATE TABLE IF NOT EXISTS Question (
    questionId BIGINT AUTO_INCREMENT PRIMARY KEY,
    categoryId BIGINT NOT NULL,
    difficultyLevelId BIGINT NOT NULL,
    questionType VARCHAR(30) NOT NULL,
    questionText TEXT NOT NULL,
    correctAnswer TEXT NULL,
    explanation TEXT NULL,
    defaultMarks DECIMAL(5,2) NOT NULL DEFAULT 1.00,
    negativeMarks DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    estimatedTimeSeconds INT NULL,
    isActive BOOLEAN NOT NULL DEFAULT TRUE,
    createdAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    createdBy BIGINT NULL,
    updatedBy BIGINT NULL,
    CONSTRAINT chk_q_type CHECK (questionType IN ('MCQ', 'MSQ', 'TRUE_FALSE', 'SHORT_ANSWER', 'DESCRIPTIVE', 'CODING')),
    CONSTRAINT chk_q_marks CHECK (defaultMarks > 0 AND negativeMarks >= 0),
    CONSTRAINT chk_q_time CHECK (estimatedTimeSeconds IS NULL OR estimatedTimeSeconds > 0),
    CONSTRAINT fk_q_cat FOREIGN KEY (categoryId) REFERENCES QuestionCategory(categoryId) ON DELETE RESTRICT,
    CONSTRAINT fk_q_diff FOREIGN KEY (difficultyLevelId) REFERENCES DifficultyLevel(difficultyLevelId) ON DELETE RESTRICT,
    CONSTRAINT fk_q_created FOREIGN KEY (createdBy) REFERENCES User(userId) ON DELETE SET NULL,
    CONSTRAINT fk_q_updated FOREIGN KEY (updatedBy) REFERENCES User(userId) ON DELETE SET NULL
) ENGINE=InnoDB;
-- ================================================================
-- 14.QuestionOption
-- ================================================================
CREATE TABLE IF NOT EXISTS QuestionOption (
    optionId BIGINT AUTO_INCREMENT PRIMARY KEY,
    questionId BIGINT NOT NULL,
    optionText TEXT NOT NULL,
    optionOrder INT NOT NULL DEFAULT 1,
    isCorrect BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT fk_opt_q FOREIGN KEY (questionId) REFERENCES Question(questionId) ON DELETE CASCADE
) ENGINE=InnoDB;
-- ================================================================
-- 15.ExamQuestion
-- ================================================================
CREATE TABLE IF NOT EXISTS ExamQuestion (
    examQuestionId BIGINT AUTO_INCREMENT PRIMARY KEY,
    examId BIGINT NOT NULL,
    questionId BIGINT NOT NULL,
    questionOrder INT NOT NULL,
    marks DECIMAL(5,2) NOT NULL,
    negativeMarks DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    isMandatory BOOLEAN NOT NULL DEFAULT TRUE,
    createdAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_eq_exam_q UNIQUE (examId, questionId),
    CONSTRAINT uq_eq_exam_order UNIQUE (examId, questionOrder),
    CONSTRAINT chk_eq_order CHECK (questionOrder > 0),
    CONSTRAINT chk_eq_marks CHECK (marks > 0 AND negativeMarks >= 0),
    CONSTRAINT fk_eq_exam FOREIGN KEY (examId) REFERENCES Exam(examId) ON DELETE CASCADE,
    CONSTRAINT fk_eq_q FOREIGN KEY (questionId) REFERENCES Question(questionId) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ================================================================
-- DOMAIN D—  EXAMINATION EXECUTION & RESULTS
-- ================================================================

-- ================================================================
-- 16.  ExamAttempt
-- ================================================================
CREATE TABLE IF NOT EXISTS ExamAttempt (
    attemptId BIGINT AUTO_INCREMENT PRIMARY KEY,
    registrationId BIGINT NOT NULL,
    attemptNumber SMALLINT NOT NULL DEFAULT 1,
    startTime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    endTime DATETIME NULL,
    submittedAt DATETIME NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'NOT_STARTED',
    totalTimeSpentSeconds INT NULL,
    ipAddress VARCHAR(45) NULL,
    deviceInfo TEXT NULL,
    browserInfo TEXT NULL,
    submissionMethod VARCHAR(30) NOT NULL DEFAULT 'MANUAL',
    autoSubmitted BOOLEAN NOT NULL DEFAULT FALSE,
    violationCount INT NOT NULL DEFAULT 0,
    submissionReason VARCHAR(100) NULL,
    createdAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_attempt_reg_num UNIQUE (registrationId, attemptNumber),
    CONSTRAINT chk_attempt_num CHECK (attemptNumber > 0),
    CONSTRAINT chk_attempt_status CHECK (status IN ('NOT_STARTED', 'IN_PROGRESS', 'SUBMITTED', 'AUTO_SUBMITTED', 'EVALUATED', 'ABANDONED')),
    CONSTRAINT chk_sub_method CHECK (submissionMethod IN ('MANUAL', 'AUTO_TIMEOUT', 'SYSTEM')),
    CONSTRAINT fk_attempt_reg FOREIGN KEY (registrationId) REFERENCES CandidateRegistration(registrationId) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ================================================================
-- 16b. ExamSecurityEvent
-- ================================================================
CREATE TABLE IF NOT EXISTS ExamSecurityEvent (
    securityEventId BIGINT AUTO_INCREMENT PRIMARY KEY,
    attemptId BIGINT NOT NULL,
    userId BIGINT NOT NULL,
    eventType VARCHAR(50) NOT NULL,
    warningNumber INT NOT NULL,
    details VARCHAR(255) NULL,
    ipAddress VARCHAR(45) NULL,
    createdAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_sec_attempt FOREIGN KEY (attemptId) REFERENCES ExamAttempt(attemptId) ON DELETE CASCADE,
    CONSTRAINT fk_sec_user FOREIGN KEY (userId) REFERENCES User(userId) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ================================================================
-- 17.  Answer
-- ================================================================

CREATE TABLE IF NOT EXISTS Answer (
    answerId BIGINT AUTO_INCREMENT PRIMARY KEY,
    attemptId BIGINT NOT NULL,
    questionId BIGINT NOT NULL,
    selectedOptionId BIGINT NULL,
    answerText TEXT NULL,
    isMarkedForReview BOOLEAN NOT NULL DEFAULT FALSE,
    isAnswered BOOLEAN NOT NULL DEFAULT FALSE,
    submittedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    timeSpentSeconds INT NOT NULL DEFAULT 0,
    createdAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_ans_attempt_q UNIQUE (attemptId, questionId),
    CONSTRAINT chk_ans_time CHECK (timeSpentSeconds >= 0),
    CONSTRAINT fk_ans_attempt FOREIGN KEY (attemptId) REFERENCES ExamAttempt(attemptId) ON DELETE CASCADE,
    CONSTRAINT fk_ans_q FOREIGN KEY (questionId) REFERENCES Question(questionId) ON DELETE RESTRICT,
    CONSTRAINT fk_ans_opt FOREIGN KEY (selectedOptionId) REFERENCES QuestionOption(optionId) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ================================================================
-- 18.  Evaluation
-- ================================================================
CREATE TABLE IF NOT EXISTS Evaluation (
    evaluationId BIGINT AUTO_INCREMENT PRIMARY KEY,
    attemptId BIGINT NOT NULL UNIQUE,
    totalMarksObtained DECIMAL(6,2) NOT NULL DEFAULT 0.00,
    totalCorrect INT NOT NULL DEFAULT 0,
    totalWrong INT NOT NULL DEFAULT 0,
    totalSkipped INT NOT NULL DEFAULT 0,
    evaluationStatus VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    evaluatedBy BIGINT NULL,
    evaluatedAt DATETIME NULL,
    remarks TEXT NULL,
    createdAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_eval_status CHECK (evaluationStatus IN ('PENDING', 'AUTO_EVALUATED', 'MANUAL_EVALUATED', 'FINALIZED')),
    CONSTRAINT fk_eval_attempt FOREIGN KEY (attemptId) REFERENCES ExamAttempt(attemptId) ON DELETE CASCADE,
    CONSTRAINT fk_eval_user FOREIGN KEY (evaluatedBy) REFERENCES User(userId) ON DELETE SET NULL
) ENGINE=InnoDB;
-- ================================================================
-- 19. EvaluationDetail
-- ================================================================
CREATE TABLE IF NOT EXISTS EvaluationDetail (
    evaluationDetailId BIGINT AUTO_INCREMENT PRIMARY KEY,
    evaluationId BIGINT NOT NULL,
    questionId BIGINT NOT NULL,
    marksAwarded DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    maxMarks DECIMAL(5,2) NOT NULL,
    isCorrect BOOLEAN NOT NULL DEFAULT FALSE,
    evaluatorRemarks TEXT NULL,
    evaluatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_eval_detail_q UNIQUE (evaluationId, questionId),
    CONSTRAINT chk_eval_detail_marks CHECK (marksAwarded >= 0 AND marksAwarded <= maxMarks),
    CONSTRAINT fk_ed_eval FOREIGN KEY (evaluationId) REFERENCES Evaluation(evaluationId) ON DELETE CASCADE,
    CONSTRAINT fk_ed_q FOREIGN KEY (questionId) REFERENCES Question(questionId) ON DELETE RESTRICT
) ENGINE=InnoDB;
-- ================================================================
-- 20. Result
-- ================================================================
CREATE TABLE IF NOT EXISTS Result (
    resultId BIGINT AUTO_INCREMENT PRIMARY KEY,
    evaluationId BIGINT NOT NULL UNIQUE,
    percentage DECIMAL(5,2) NOT NULL,
    grade VARCHAR(5) NULL,
    passStatus BOOLEAN NOT NULL DEFAULT FALSE,
    publishedAt DATETIME NULL,
    publishedBy BIGINT NULL,
    isPublished BOOLEAN NOT NULL DEFAULT FALSE,
    remarks TEXT NULL,
    createdAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_res_percentage CHECK (percentage BETWEEN 0 AND 100),
    CONSTRAINT fk_res_eval FOREIGN KEY (evaluationId) REFERENCES Evaluation(evaluationId) ON DELETE RESTRICT,
    CONSTRAINT fk_res_user FOREIGN KEY (publishedBy) REFERENCES User(userId) ON DELETE SET NULL
) ENGINE=InnoDB;
-- ================================================================
-- DOMAIN E—   NOTIFICATIONS & ADMINISTRATION
-- ================================================================

-- ================================================================
-- 21.NotificationTemplate
-- ================================================================
CREATE TABLE IF NOT EXISTS NotificationTemplate (
    templateId BIGINT AUTO_INCREMENT PRIMARY KEY,
    templateName VARCHAR(100) NOT NULL UNIQUE,
    notificationType VARCHAR(30) NOT NULL,
    subject VARCHAR(150) NULL,
    templateBody TEXT NOT NULL,
    isActive BOOLEAN NOT NULL DEFAULT TRUE,
    createdAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;
-- ================================================================
-- 22. Notification
-- ================================================================
CREATE TABLE IF NOT EXISTS Notification (
    notificationId BIGINT AUTO_INCREMENT PRIMARY KEY,
    userId BIGINT NOT NULL,
    templateId BIGINT NULL,
    title VARCHAR(150) NOT NULL,
    message TEXT NOT NULL,
    notificationType VARCHAR(30) NOT NULL,
    deliveryChannel VARCHAR(20) NOT NULL DEFAULT 'IN_APP',
    priority VARCHAR(20) NOT NULL DEFAULT 'NORMAL',
    isRead BOOLEAN NOT NULL DEFAULT FALSE,
    sentAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    readAt DATETIME NULL,
    expiresAt DATETIME NULL,
    CONSTRAINT chk_notif_type CHECK (notificationType IN ('EXAM', 'RESULT', 'SYSTEM', 'REMINDER', 'SECURITY')),
    CONSTRAINT chk_notif_channel CHECK (deliveryChannel IN ('IN_APP', 'EMAIL', 'SMS')),
    CONSTRAINT chk_notif_priority CHECK (priority IN ('LOW', 'NORMAL', 'HIGH', 'CRITICAL')),
    CONSTRAINT fk_notif_user FOREIGN KEY (userId) REFERENCES User(userId) ON DELETE CASCADE,
    CONSTRAINT fk_notif_tpl FOREIGN KEY (templateId) REFERENCES NotificationTemplate(templateId) ON DELETE SET NULL
) ENGINE=InnoDB;
-- ================================================================
-- 23. AuditLog
-- ================================================================
CREATE TABLE IF NOT EXISTS AuditLog (
    auditLogId BIGINT AUTO_INCREMENT PRIMARY KEY,
    userId BIGINT NULL,
    entityName VARCHAR(100) NOT NULL,
    entityId BIGINT NULL,
    action VARCHAR(30) NOT NULL,
    oldValue JSON NULL,
    newValue JSON NULL,
    ipAddress VARCHAR(45) NULL,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_audit_action CHECK (action IN ('CREATE', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT', 'VIEW', 'EXPORT')),
    CONSTRAINT fk_audit_user FOREIGN KEY (userId) REFERENCES User(userId) ON DELETE SET NULL
) ENGINE=InnoDB;
-- ================================================================
-- 24.SystemEvent
-- ================================================================
CREATE TABLE IF NOT EXISTS SystemEvent (
    eventId BIGINT AUTO_INCREMENT PRIMARY KEY,
    eventType VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    sourceModule VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    occurredAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolvedAt DATETIME NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'OPEN',
    CONSTRAINT chk_event_severity CHECK (severity IN ('INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    CONSTRAINT chk_event_status CHECK (status IN ('OPEN', 'ACKNOWLEDGED', 'RESOLVED'))
) ENGINE=InnoDB;
-- ================================================================
-- 25. PerformanceMetric
-- ================================================================
CREATE TABLE IF NOT EXISTS PerformanceMetric (
    metricId BIGINT AUTO_INCREMENT PRIMARY KEY,
    metricName VARCHAR(100) NOT NULL,
    metricValue DECIMAL(12,4) NOT NULL,
    metricUnit VARCHAR(20) NOT NULL,
    sourceModule VARCHAR(50) NOT NULL,
    recordedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_metric_val CHECK (metricValue >= 0)
) ENGINE=InnoDB;
-- ================================================================
-- 26.  SystemConfiguration
-- ================================================================
CREATE TABLE IF NOT EXISTS SystemConfiguration (
    configurationId BIGINT AUTO_INCREMENT PRIMARY KEY,
    configurationKey VARCHAR(100) NOT NULL UNIQUE,
    configurationValue TEXT NOT NULL,
    valueType VARCHAR(20) NOT NULL,
    description TEXT NULL,
    isEditable BOOLEAN NOT NULL DEFAULT TRUE,
    updatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    updatedBy BIGINT NULL,
    CONSTRAINT chk_config_type CHECK (valueType IN ('STRING', 'INTEGER', 'BOOLEAN', 'DECIMAL', 'JSON')),
    CONSTRAINT fk_config_user FOREIGN KEY (updatedBy) REFERENCES User(userId) ON DELETE SET NULL
) ENGINE=InnoDB;
-- ================================================================
-- 27.FeatureFlag
-- ================================================================
CREATE TABLE IF NOT EXISTS FeatureFlag (
    featureFlagId BIGINT AUTO_INCREMENT PRIMARY KEY,
    flagName VARCHAR(100) NOT NULL UNIQUE,
    description TEXT NULL,
    isEnabled BOOLEAN NOT NULL DEFAULT FALSE,
    rolloutPercentage SMALLINT NOT NULL DEFAULT 100,
    createdAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_flag_rollout CHECK (rolloutPercentage BETWEEN 0 AND 100)
) ENGINE=InnoDB;

-- ================================================================
-- 28. BackupHistory
-- ================================================================
CREATE TABLE IF NOT EXISTS BackupHistory (
    backupId BIGINT AUTO_INCREMENT PRIMARY KEY,
    fileName VARCHAR(255) NOT NULL UNIQUE,
    fileSize BIGINT NOT NULL,
    createdAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    createdBy BIGINT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'CREATING',
    checksum VARCHAR(64) NULL,
    backupType VARCHAR(30) NOT NULL DEFAULT 'MANUAL',
    verificationStatus VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    verifiedAt DATETIME NULL,
    restoredAt DATETIME NULL,
    restoredBy BIGINT NULL,
    errorMessage TEXT NULL,
    CONSTRAINT chk_backup_status CHECK (status IN ('CREATING', 'COMPLETED', 'FAILED', 'RESTORING', 'RESTORED', 'RESTORE_FAILED')),
    CONSTRAINT chk_backup_type CHECK (backupType IN ('MANUAL', 'AUTOMATED', 'PRE_RESTORE', 'UPLOADED', 'FULL_SYSTEM')),
    CONSTRAINT chk_verify_status CHECK (verificationStatus IN ('PENDING', 'VERIFIED', 'FAILED')),
    CONSTRAINT fk_backup_created FOREIGN KEY (createdBy) REFERENCES User(userId) ON DELETE SET NULL,
    CONSTRAINT fk_backup_restored FOREIGN KEY (restoredBy) REFERENCES User(userId) ON DELETE SET NULL
) ENGINE=InnoDB;


-- ================================================================
-- SECTION 2 :  DATA INSERTION
-- ================================================================

-- ================================================================
-- 1. IDENTITY & ACCESS DATA
-- ================================================================
INSERT IGNORE INTO Role (roleId, roleName, description, isActive) VALUES
(1, 'Admin', 'Full platform administrative control', TRUE),
(2, 'Faculty', 'Creates questions, designs exams, and evaluates submissions', TRUE),
(3, 'Student', 'Registers for and takes online examinations', TRUE);

INSERT IGNORE INTO Permission (permissionId, permissionName, moduleName, description) VALUES
(1, 'CREATE_EXAM', 'ExamModule', 'Allows creating new exam templates'),
(2, 'PUBLISH_RESULT', 'EvaluationModule', 'Allows publishing finalized results'),
(3, 'TAKE_EXAM', 'ExecutionModule', 'Allows attempting scheduled exams');

INSERT IGNORE INTO RolePermission (rolePermissionId, roleId, permissionId) VALUES
(1, 1, 1), (2, 1, 2), (3, 1, 3),
(4, 2, 1), (5, 2, 2),
(6, 3, 3);

INSERT IGNORE INTO User (userId, firstName, lastName, email, phone, passwordHash, roleId, isActive) VALUES
(1, 'System', 'Admin', 'admin@platform.com', '9876543210', 'scrypt:32768:8:1$6AtYRS8qVgabYrDr$e03515fcf16abf333e75a24083333517b059bb95166af78770981a4091810e9c06d4bd21cedc9463a39828df7301c88e678b2f11001311ee1151e0e24eec80c8', 1, TRUE),
(2, 'Dr. Rajesh', 'Sharma', 'rajesh.sharma@college.edu', '9876543211', 'scrypt:32768:8:1$6AtYRS8qVgabYrDr$e03515fcf16abf333e75a24083333517b059bb95166af78770981a4091810e9c06d4bd21cedc9463a39828df7301c88e678b2f11001311ee1151e0e24eec80c8', 2, TRUE),
(3, 'Rutuja', 'Ghodekar', 'rutuja.student@college.edu', '9876543212', 'scrypt:32768:8:1$6AtYRS8qVgabYrDr$e03515fcf16abf333e75a24083333517b059bb95166af78770981a4091810e9c06d4bd21cedc9463a39828df7301c88e678b2f11001311ee1151e0e24eec80c8', 3, TRUE);

INSERT IGNORE INTO UserSession (sessionId, userId, ipAddress, userAgent, deviceType, sessionStatus, expiresAt) VALUES
('550e8400-e29b-41d4-a716-446655440000', 3, '192.168.1.15', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', 'Desktop', 'ACTIVE', DATE_ADD(NOW(), INTERVAL 2 HOUR));

INSERT IGNORE INTO LoginHistory (loginHistoryId, userId, ipAddress, userAgent, loginStatus, authenticationMethod) VALUES
(1, 3, '192.168.1.15', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', 'SUCCESS', 'PASSWORD');
-- ================================================================
-- 2. ACADEMIC & EXAMINATION DATA
-- ================================================================

INSERT IGNORE INTO Subject (subjectId, subjectCode, subjectName, description, credits, createdBy) VALUES
(1, 'CS101', 'Database Management Systems', 'Core relational database principles and SQL', 4, 1),
(2, 'CS102', 'Full Stack Web Development', 'MERN stack and modern web application development', 4, 1);

INSERT IGNORE INTO Exam (examId, subjectId, examCode, examTitle, examType, totalMarks, passingMarks, durationMinutes, createdBy) VALUES
(1, 1, 'EXAM-DBMS-MID', 'DBMS Mid-Term Assessment', 'OBJECTIVE', 100.00, 40.00, 60, 2);

INSERT IGNORE INTO ExamSchedule (scheduleId, examId, startTime, endTime, registrationStart, registrationEnd, scheduleStatus) VALUES
(1, 1, DATE_SUB(NOW(), INTERVAL 1 HOUR), DATE_ADD(NOW(), INTERVAL 1 HOUR), DATE_SUB(NOW(), INTERVAL 7 DAY), DATE_SUB(NOW(), INTERVAL 1 DAY), 'ONGOING');

INSERT IGNORE INTO CandidateRegistration (registrationId, examId, userId, registrationStatus, eligibilityVerified) VALUES
(1, 1, 3, 'REGISTERED', TRUE);

-- ================================================================
-- 3. QUESTION BANK DATA
-- ================================================================

INSERT IGNORE INTO QuestionCategory (categoryId, categoryName, description, createdBy) VALUES
(1, 'SQL Queries', 'Relational query construction and syntax', 2),
(2, 'Database Concepts', 'Normalization, ACID properties, and indexing', 2);

INSERT IGNORE INTO DifficultyLevel (difficultyLevelId, levelName, difficultyScore, description) VALUES
(1, 'Easy', 1, 'Basic syntax and conceptual recognition'),
(2, 'Medium', 5, 'Intermediate query building and problem solving');

INSERT IGNORE INTO Question (questionId, categoryId, difficultyLevelId, questionType, questionText, correctAnswer, defaultMarks, negativeMarks, createdBy) VALUES
(1, 1, 1, 'MCQ', 'Which SQL clause is used to filter records in a SELECT statement?', NULL, 50.00, 0.00, 2),
(2, 2, 2, 'MSQ', 'Which of the following are ACID properties in DBMS? (Select all that apply)', NULL, 50.00, 0.00, 2);

INSERT IGNORE INTO QuestionOption (optionId, questionId, optionText, optionOrder, isCorrect) VALUES
(1, 1, 'WHERE', 1, TRUE),
(2, 1, 'GROUP BY', 2, FALSE),
(3, 1, 'ORDER BY', 3, FALSE),
(4, 1, 'HAVING', 4, FALSE),
(5, 2, 'Atomicity', 1, TRUE),
(6, 2, 'Consistency', 2, TRUE),
(7, 2, 'Availability', 3, FALSE),
(8, 2, 'Durability', 4, TRUE);

INSERT IGNORE INTO ExamQuestion (examQuestionId, examId, questionId, questionOrder, marks, negativeMarks) VALUES
(1, 1, 1, 1, 50.00, 0.00),
(2, 1, 2, 2, 50.00, 0.00);

-- ================================================================
-- 4. EXAM EXECUTION DATA
-- ================================================================
INSERT IGNORE INTO ExamAttempt (attemptId, registrationId, attemptNumber, startTime, status, ipAddress) VALUES
(1, 1, 1, DATE_SUB(NOW(), INTERVAL 45 MINUTE), 'IN_PROGRESS', '192.168.1.15');

INSERT IGNORE INTO Answer (answerId, attemptId, questionId, selectedOptionId, isAnswered, timeSpentSeconds) VALUES
(1, 1, 1, 1, TRUE, 120),
(2, 1, 2, 5, TRUE, 180);

INSERT IGNORE INTO Evaluation (evaluationId, attemptId, totalMarksObtained, totalCorrect, totalWrong, totalSkipped, evaluationStatus, evaluatedBy, evaluatedAt) VALUES
(1, 1, 100.00, 2, 0, 0, 'AUTO_EVALUATED', 2, NOW());

INSERT IGNORE INTO EvaluationDetail (evaluationDetailId, evaluationId, questionId, marksAwarded, maxMarks, isCorrect) VALUES
(1, 1, 1, 50.00, 50.00, TRUE),
(2, 1, 2, 50.00, 50.00, TRUE);

INSERT IGNORE INTO Result (resultId, evaluationId, percentage, grade, passStatus, isPublished, publishedBy, publishedAt) VALUES
(1, 1, 100.00, 'A+', TRUE, TRUE, 2, NOW());

-- ================================================================
-- 5. NOTIFICATION & ADMINISTRATION DATA
-- ================================================================

INSERT IGNORE INTO NotificationTemplate (templateId, templateName, notificationType, subject, templateBody) VALUES
(1, 'RESULT_PUBLISHED', 'RESULT', 'Exam Result Available', 'Dear {{student_name}}, your result for {{exam_title}} is now available.');

INSERT IGNORE INTO Notification (notificationId, userId, templateId, title, message, notificationType, deliveryChannel, isRead) VALUES
(1, 3, 1, 'Exam Result Available', 'Dear Student, your result for DBMS Mid-Term Assessment is now available.', 'RESULT', 'IN_APP', FALSE);

INSERT IGNORE INTO AuditLog (auditLogId, userId, entityName, entityId, action, newValue, ipAddress) VALUES
(1, 2, 'Result', 1, 'CREATE', '{"status": "PUBLISHED", "score": 100.00}', '192.168.1.10');

INSERT IGNORE INTO SystemEvent (eventId, eventType, severity, sourceModule, description, status) VALUES
(1, 'SCHEDULE_TRIGGER', 'INFO', 'SchedulerModule', 'Automated exam completion worker executed successfully.', 'RESOLVED');

INSERT IGNORE INTO PerformanceMetric (metricId, metricName, metricValue, metricUnit, sourceModule) VALUES
(1, 'DB_QUERY_LATENCY', 12.4500, 'MS', 'DatabaseEngine');

INSERT IGNORE INTO SystemConfiguration (configurationId, configurationKey, configurationValue, valueType, description, updatedBy) VALUES
(1, 'MAX_EXAM_CONCURRENCY', '500', 'INTEGER', 'Maximum allowed active student exam attempts simultaneously', 1);

INSERT IGNORE INTO FeatureFlag (featureFlagId, flagName, description, isEnabled, rolloutPercentage) VALUES
(1, 'AUTO_EVALUATION_MSQ', 'Enables automated grading algorithms for multi-select choice questions', TRUE, 100);


