# Modules

| Final Module | Original Modules |
| ----- | ----- |
| Identity & Access Management | Registration, Login, RBAC |
| Student Management | Student Management |
| Faculty Management | Faculty Management |
| Subject Management | Subject Management |
| Examination Administration | Scheduling, Candidate Registration |
| Question Management | Question Bank, Random Selection, Paper Generation |
| Examination Runtime | Examination Engine, Online Interface, Timer, Auto Submission |
| Evaluation & Results | Evaluation, Marks Calculation, Result Processing |
| Reporting & Analytics | Reports, Dashboard, Analytics |
| Audit Logging | Audit Logs |
| Secure Session Management | Secure Session Management |
| Authenticated Network Communication | Authenticated Network Communication |
| Backup & Restore | Backup & Restore |
| System Monitoring | System Monitoring |
| Notification Service | Notification Module |

# TablesWithAttributsConstraints

Perfect. We'll make this **implementation-ready**, not conceptual.

One important note before we start:

During **DB-003**, we identified that **RolePermission** is required as the junction table for RBAC. Therefore, the Identity & Access domain consists of **6 tables**:

1. Role  
2. Permission  
3. RolePermission  
4. User  
5. UserSession  
6. LoginHistory

---

# **PART 1 — Identity & Access Database Specification**

---

# **Table 1 — Role**

### **Purpose**

Stores all system roles used for Role-Based Access Control (RBAC).

### **Columns**

| Column | Data Type | Null | Default |
| ----- | ----- | ----- | ----- |
| roleId | BIGSERIAL | NO | Auto |
| roleName | VARCHAR(50) | NO | — |
| description | VARCHAR(255) | YES | NULL |
| isActive | BOOLEAN | NO | TRUE |
| createdAt | TIMESTAMPTZ | NO | NOW() |
| updatedAt | TIMESTAMPTZ | NO | NOW() |
| createdBy | BIGINT | YES | NULL |
| updatedBy | BIGINT | YES | NULL |

### **Primary Key**

* roleId

### **Foreign Keys**

None

### **Unique Constraints**

* roleName

### **Check Constraints**

CHAR\_LENGTH(roleName) \>= 3

### **Indexes**

PK(roleId)

UNIQUE(roleName)

### **Delete Rule**

RESTRICT

---

# **Table 2 — Permission**

### **Purpose**

Stores all available permissions in the system.

### **Columns**

| Column | Data Type | Null | Default |
| ----- | ----- | ----- | ----- |
| permissionId | BIGSERIAL | NO | Auto |
| permissionName | VARCHAR(100) | NO | — |
| moduleName | VARCHAR(50) | NO | — |
| description | VARCHAR(255) | YES | NULL |
| createdAt | TIMESTAMPTZ | NO | NOW() |

### **Primary Key**

permissionId

### **Foreign Keys**

None

### **Unique Constraints**

(permissionName, moduleName)

### **Check Constraints**

CHAR\_LENGTH(permissionName) \> 2

### **Indexes**

PK(permissionId)

UNIQUE(permissionName,moduleName)

### **Delete Rule**

RESTRICT

---

# **Table 3 — RolePermission**

### **Purpose**

Maps permissions to roles.

### **Columns**

| Column | Data Type | Null | Default |
| ----- | ----- | ----- | ----- |
| rolePermissionId | BIGSERIAL | NO | Auto |
| roleId | BIGINT | NO | — |
| permissionId | BIGINT | NO | — |
| grantedAt | TIMESTAMPTZ | NO | NOW() |
| grantedBy | BIGINT | YES | NULL |

### **Primary Key**

rolePermissionId

### **Foreign Keys**

roleId → Role(roleId)

permissionId → Permission(permissionId)

grantedBy → User(userId)

### **Unique Constraints**

(roleId, permissionId)

### **Check Constraints**

None

### **Indexes**

PK(rolePermissionId)

INDEX(roleId)

INDEX(permissionId)

UNIQUE(roleId,permissionId)

### **Delete Rules**

Role → CASCADE

Permission → CASCADE

---

# **Table 4 — User**

### **Purpose**

Stores every authenticated user of the system.

### **Columns**

| Column | Data Type | Null | Default |
| ----- | ----- | ----- | ----- |
| userId | BIGSERIAL | NO | Auto |
| firstName | VARCHAR(50) | NO | — |
| lastName | VARCHAR(50) | NO | — |
| email | VARCHAR(255) | NO | — |
| phone | VARCHAR(15) | YES | NULL |
| passwordHash | TEXT | NO | — |
| roleId | BIGINT | NO | — |
| isActive | BOOLEAN | NO | TRUE |
| lastLogin | TIMESTAMPTZ | YES | NULL |
| failedLoginAttempts | INTEGER | NO | 0 |
| accountLocked | BOOLEAN | NO | FALSE |
| createdAt | TIMESTAMPTZ | NO | NOW() |
| updatedAt | TIMESTAMPTZ | NO | NOW() |
| createdBy | BIGINT | YES | NULL |
| updatedBy | BIGINT | YES | NULL |

### **Primary Key**

userId

### **Foreign Keys**

roleId → Role(roleId)

createdBy → User(userId)

updatedBy → User(userId)

### **Unique Constraints**

email

phone

### **Check Constraints**

failedLoginAttempts \>= 0

### **Indexes**

PK(userId)

UNIQUE(email)

UNIQUE(phone)

INDEX(roleId)

INDEX(lastLogin)

### **Delete Rule**

RESTRICT

---

# **Table 5 — UserSession**

### **Purpose**

Maintains active and historical login sessions.

### **Columns**

| Column | Data Type | Null | Default |
| ----- | ----- | ----- | ----- |
| sessionId | UUID | NO | gen\_random\_uuid() |
| userId | BIGINT | NO | — |
| loginTime | TIMESTAMPTZ | NO | NOW() |
| logoutTime | TIMESTAMPTZ | YES | NULL |
| ipAddress | INET | NO | — |
| userAgent | TEXT | YES | NULL |
| deviceType | VARCHAR(30) | YES | NULL |
| sessionStatus | VARCHAR(20) | NO | 'ACTIVE' |
| expiresAt | TIMESTAMPTZ | NO | — |

### **Primary Key**

sessionId

### **Foreign Keys**

userId → User(userId)

### **Unique Constraints**

None

### **Check Constraints**

sessionStatus IN  
('ACTIVE','EXPIRED','LOGGED\_OUT','INVALIDATED')

### **Indexes**

PK(sessionId)

INDEX(userId)

INDEX(loginTime)

INDEX(expiresAt)

INDEX(sessionStatus)

### **Delete Rule**

CASCADE

---

# **Table 6 — LoginHistory**

### **Purpose**

Maintains immutable authentication history for auditing and security analysis.

### **Columns**

| Column | Data Type | Null | Default |
| ----- | ----- | ----- | ----- |
| loginHistoryId | BIGSERIAL | NO | Auto |
| userId | BIGINT | NO | — |
| loginTime | TIMESTAMPTZ | NO | NOW() |
| logoutTime | TIMESTAMPTZ | YES | NULL |
| ipAddress | INET | NO | — |
| userAgent | TEXT | YES | NULL |
| loginStatus | VARCHAR(20) | NO | — |
| failureReason | VARCHAR(255) | YES | NULL |
| authenticationMethod | VARCHAR(30) | NO | 'PASSWORD' |

### **Primary Key**

loginHistoryId

### **Foreign Keys**

userId → User(userId)

### **Unique Constraints**

None

### **Check Constraints**

loginStatus IN  
('SUCCESS','FAILED','LOCKED')

authenticationMethod IN  
('PASSWORD','OTP','SSO')

### **Indexes**

PK(loginHistoryId)

INDEX(userId)

INDEX(loginTime)

INDEX(loginStatus)

### **Delete Rule**

RESTRICT (audit records should never be removed)

---

# **Identity & Access Summary**

| Table | Type |
| ----- | ----- |
| Role | Master |
| Permission | Master |
| RolePermission | Mapping |
| User | Master |
| UserSession | Transaction |
| LoginHistory | Audit |

---

## **Notes / Refinements**

While reviewing the schema, I identified a few refinements that I recommend we consider before freezing the database design:

1. **`User` vs `Student`/`Faculty` specialization** – Earlier we discussed a single `User` entity with role-based differentiation. We should later decide whether student- and faculty-specific attributes belong in separate profile tables or remain within a unified user model.  
2. **Permission granularity** – We should decide whether permissions are simple strings (e.g., `CREATE_EXAM`) or resource-action pairs (`Exam:Create`). The latter scales better for RBAC.  
3. **Session storage** – Using a `UUID` for `sessionId` is preferable over `BIGSERIAL` because session identifiers should be unpredictable from a security standpoint.

Overall, this part provides a solid implementation-ready foundation for the Identity & Access domain and can be translated directly into PostgreSQL DDL in a later implementation phase.

# **PART 2 — Academic & Examination Management Database Specification**

This section covers the following tables:

1. Subject  
2. Exam  
3. ExamSchedule  
4. CandidateRegistration

---

# **Table 7 — Subject**

### **Purpose**

Stores all academic subjects for which examinations are conducted.

### **Columns**

| Column | Data Type | Null | Default |
| ----- | ----- | ----- | ----- |
| subjectId | BIGSERIAL | NO | Auto |
| subjectCode | VARCHAR(20) | NO | — |
| subjectName | VARCHAR(100) | NO | — |
| description | TEXT | YES | NULL |
| credits | SMALLINT | YES | NULL |
| isActive | BOOLEAN | NO | TRUE |
| createdAt | TIMESTAMPTZ | NO | NOW() |
| updatedAt | TIMESTAMPTZ | NO | NOW() |
| createdBy | BIGINT | YES | NULL |
| updatedBy | BIGINT | YES | NULL |

### **Primary Key**

* subjectId

### **Foreign Keys**

* createdBy → User(userId)  
* updatedBy → User(userId)

### **Unique Constraints**

* subjectCode  
* subjectName

### **Check Constraints**

credits \>= 0

### **Indexes**

PK(subjectId)

UNIQUE(subjectCode)

UNIQUE(subjectName)

INDEX(isActive)

### **Delete Rule**

RESTRICT

---

# **Table 8 — Exam**

### **Purpose**

Stores the master definition of an examination.

### **Columns**

| Column | Data Type | Null | Default |
| ----- | ----- | ----- | ----- |
| examId | BIGSERIAL | NO | Auto |
| subjectId | BIGINT | NO | — |
| examCode | VARCHAR(30) | NO | — |
| examTitle | VARCHAR(150) | NO | — |
| examType | VARCHAR(30) | NO | — |
| totalMarks | NUMERIC(6,2) | NO | — |
| passingMarks | NUMERIC(6,2) | NO | — |
| durationMinutes | INTEGER | NO | — |
| instructions | TEXT | YES | NULL |
| maximumAttempts | SMALLINT | NO | 1 |
| shuffleQuestions | BOOLEAN | NO | TRUE |
| shuffleOptions | BOOLEAN | NO | TRUE |
| negativeMarking | BOOLEAN | NO | FALSE |
| negativeMarksPerQuestion | NUMERIC(5,2) | NO | 0 |
| examStatus | VARCHAR(20) | NO | 'DRAFT' |
| isActive | BOOLEAN | NO | TRUE |
| createdAt | TIMESTAMPTZ | NO | NOW() |
| updatedAt | TIMESTAMPTZ | NO | NOW() |
| createdBy | BIGINT | YES | NULL |
| updatedBy | BIGINT | YES | NULL |

### **Primary Key**

* examId

### **Foreign Keys**

* subjectId → Subject(subjectId)  
* createdBy → User(userId)  
* updatedBy → User(userId)

### **Unique Constraints**

* examCode

### **Check Constraints**

totalMarks \> 0

passingMarks \>= 0

passingMarks \<= totalMarks

durationMinutes \> 0

maximumAttempts \>= 1

negativeMarksPerQuestion \>= 0

examStatus IN  
('DRAFT','SCHEDULED','ACTIVE','COMPLETED','CANCELLED')

### **Indexes**

PK(examId)

UNIQUE(examCode)

INDEX(subjectId)

INDEX(examStatus)

INDEX(isActive)

### **Delete Rule**

RESTRICT

---

# **Table 9 — ExamSchedule**

### **Purpose**

Stores scheduling information for each examination.

### **Columns**

| Column | Data Type | Null | Default |
| ----- | ----- | ----- | ----- |
| scheduleId | BIGSERIAL | NO | Auto |
| examId | BIGINT | NO | — |
| startTime | TIMESTAMPTZ | NO | — |
| endTime | TIMESTAMPTZ | NO | — |
| registrationStart | TIMESTAMPTZ | YES | NULL |
| registrationEnd | TIMESTAMPTZ | YES | NULL |
| lateEntryMinutes | INTEGER | NO | 0 |
| autoSubmit | BOOLEAN | NO | TRUE |
| scheduleStatus | VARCHAR(20) | NO | 'SCHEDULED' |
| createdAt | TIMESTAMPTZ | NO | NOW() |
| updatedAt | TIMESTAMPTZ | NO | NOW() |

### **Primary Key**

* scheduleId

### **Foreign Keys**

* examId → Exam(examId)

### **Unique Constraints**

None

### **Check Constraints**

endTime \> startTime

registrationEnd \>= registrationStart

lateEntryMinutes \>= 0

scheduleStatus IN  
('SCHEDULED','ONGOING','COMPLETED','CANCELLED')

### **Indexes**

PK(scheduleId)

INDEX(examId)

INDEX(startTime)

INDEX(endTime)

INDEX(scheduleStatus)

### **Delete Rule**

CASCADE

---

# **Table 10 — CandidateRegistration**

### **Purpose**

Stores student registrations for examinations.

### **Columns**

| Column | Data Type | Null | Default |
| ----- | ----- | ----- | ----- |
| registrationId | BIGSERIAL | NO | Auto |
| examId | BIGINT | NO | — |
| userId | BIGINT | NO | — |
| registrationTime | TIMESTAMPTZ | NO | NOW() |
| registrationStatus | VARCHAR(20) | NO | 'REGISTERED' |
| eligibilityVerified | BOOLEAN | NO | FALSE |
| paymentRequired | BOOLEAN | NO | FALSE |
| paymentStatus | VARCHAR(20) | NO | 'NOT\_REQUIRED' |
| remarks | VARCHAR(255) | YES | NULL |
| createdAt | TIMESTAMPTZ | NO | NOW() |

### **Primary Key**

* registrationId

### **Foreign Keys**

* examId → Exam(examId)  
* userId → User(userId)

### **Unique Constraints**

* (examId, userId)

### **Check Constraints**

registrationStatus IN  
('REGISTERED','CANCELLED','WAITLISTED')

paymentStatus IN  
('NOT\_REQUIRED','PENDING','PAID','FAILED')

### **Indexes**

PK(registrationId)

UNIQUE(examId,userId)

INDEX(userId)

INDEX(examId)

INDEX(registrationStatus)

INDEX(paymentStatus)

### **Delete Rule**

* Exam → RESTRICT if registrations exist  
* User → RESTRICT

---

# **Academic & Examination Management Summary**

| Table | Type |
| ----- | ----- |
| Subject | Master |
| Exam | Master |
| ExamSchedule | Transaction |
| CandidateRegistration | Transaction |

---

# **Refinements Identified**

While reviewing this part of the schema, I identified a few improvements that I recommend we incorporate before implementation:

### **1\. Separate Exam Definition from Exam Instance**

Currently, `Exam` stores both the exam definition and scheduling-related configuration. If the system later supports multiple sessions of the same exam (e.g., different batches or makeup exams), we may consider moving session-specific settings (such as `shuffleQuestions`, `shuffleOptions`, and `negativeMarking`) into `ExamSchedule` or a separate `ExamSession` table. For the current project scope, the present design is sufficient.

---

### **2\. Registration Eligibility**

If eligibility rules become more complex (attendance, prerequisites, semester restrictions), they should be handled by business logic rather than additional columns. The `eligibilityVerified` flag simply records the outcome.

---

### **3\. Future-Proofing**

The current schema can accommodate future additions such as:

* Multiple examination sessions  
* Registration approval workflow  
* Hall ticket generation  
* Fee management  
* Different examination modes (online/offline/hybrid)

without requiring major redesign.

---

**Part 2 Complete ✅**

The next section (**Part 3**) will cover the **Question Bank**, including:

1. Question  
2. QuestionCategory  
3. DifficultyLevel  
4. ExamQuestion

This is where the core examination content model will be defined.

# **PART 3 — Question Bank Database Specification**

This section covers the following tables:

1. QuestionCategory  
2. DifficultyLevel  
3. Question  
4. ExamQuestion

> **Note:** I intentionally ordered the tables based on dependencies so that parent tables are defined before child tables.

---

# **Table 11 — QuestionCategory**

### **Purpose**

Stores the classification of questions (e.g., Programming, DBMS, Networking).

### **Columns**

| Column | Data Type | Null | Default |
| ----- | ----- | ----- | ----- |
| categoryId | BIGSERIAL | NO | Auto |
| categoryName | VARCHAR(100) | NO | — |
| description | VARCHAR(255) | YES | NULL |
| isActive | BOOLEAN | NO | TRUE |
| createdAt | TIMESTAMPTZ | NO | NOW() |
| updatedAt | TIMESTAMPTZ | NO | NOW() |
| createdBy | BIGINT | YES | NULL |
| updatedBy | BIGINT | YES | NULL |

### **Primary Key**

* categoryId

### **Foreign Keys**

* createdBy → User(userId)  
* updatedBy → User(userId)

### **Unique Constraints**

* categoryName

### **Check Constraints**

CHAR\_LENGTH(categoryName) \>= 3

### **Indexes**

PK(categoryId)

UNIQUE(categoryName)

INDEX(isActive)

### **Delete Rule**

RESTRICT

---

# **Table 12 — DifficultyLevel**

### **Purpose**

Stores standardized difficulty levels used throughout the question bank.

### **Columns**

| Column | Data Type | Null | Default |
| ----- | ----- | ----- | ----- |
| difficultyLevelId | BIGSERIAL | NO | Auto |
| levelName | VARCHAR(30) | NO | — |
| difficultyScore | SMALLINT | NO | — |
| description | VARCHAR(255) | YES | NULL |
| createdAt | TIMESTAMPTZ | NO | NOW() |

### **Primary Key**

* difficultyLevelId

### **Foreign Keys**

None

### **Unique Constraints**

* levelName  
* difficultyScore

### **Check Constraints**

difficultyScore BETWEEN 1 AND 10

### **Indexes**

PK(difficultyLevelId)

UNIQUE(levelName)

UNIQUE(difficultyScore)

### **Delete Rule**

RESTRICT

---

# **Table 13 — Question**

### **Purpose**

Stores every question available in the centralized Question Bank.

### **Columns**

| Column | Data Type | Null | Default |
| ----- | ----- | ----- | ----- |
| questionId | BIGSERIAL | NO | Auto |
| categoryId | BIGINT | NO | — |
| difficultyLevelId | BIGINT | NO | — |
| questionType | VARCHAR(30) | NO | — |
| questionText | TEXT | NO | — |
| optionA | TEXT | YES | NULL |
| optionB | TEXT | YES | NULL |
| optionC | TEXT | YES | NULL |
| optionD | TEXT | YES | NULL |
| correctOption | CHAR(1) | YES | NULL |
| correctAnswer | TEXT | YES | NULL |
| explanation | TEXT | YES | NULL |
| defaultMarks | NUMERIC(5,2) | NO | 1 |
| negativeMarks | NUMERIC(5,2) | NO | 0 |
| estimatedTimeSeconds | INTEGER | YES | NULL |
| isActive | BOOLEAN | NO | TRUE |
| createdAt | TIMESTAMPTZ | NO | NOW() |
| updatedAt | TIMESTAMPTZ | NO | NOW() |
| createdBy | BIGINT | YES | NULL |
| updatedBy | BIGINT | YES | NULL |

### **Primary Key**

* questionId

### **Foreign Keys**

* categoryId → QuestionCategory(categoryId)  
* difficultyLevelId → DifficultyLevel(difficultyLevelId)  
* createdBy → User(userId)  
* updatedBy → User(userId)

### **Unique Constraints**

None

### **Check Constraints**

questionType IN  
('MCQ','MSQ','TRUE\_FALSE','SHORT\_ANSWER','DESCRIPTIVE','CODING')

defaultMarks \> 0

negativeMarks \>= 0

estimatedTimeSeconds \> 0

correctOption IN ('A','B','C','D')

### **Indexes**

PK(questionId)

INDEX(categoryId)

INDEX(difficultyLevelId)

INDEX(questionType)

INDEX(isActive)

### **Delete Rule**

RESTRICT

---

# **Table 14 — ExamQuestion**

### **Purpose**

Associates questions with examinations and stores exam-specific configuration.

### **Columns**

| Column | Data Type | Null | Default |
| ----- | ----- | ----- | ----- |
| examQuestionId | BIGSERIAL | NO | Auto |
| examId | BIGINT | NO | — |
| questionId | BIGINT | NO | — |
| questionOrder | INTEGER | NO | — |
| marks | NUMERIC(5,2) | NO | — |
| negativeMarks | NUMERIC(5,2) | NO | 0 |
| isMandatory | BOOLEAN | NO | TRUE |
| createdAt | TIMESTAMPTZ | NO | NOW() |

### **Primary Key**

* examQuestionId

### **Foreign Keys**

* examId → Exam(examId)  
* questionId → Question(questionId)

### **Unique Constraints**

* (examId, questionId)  
* (examId, questionOrder)

### **Check Constraints**

questionOrder \> 0

marks \> 0

negativeMarks \>= 0

### **Indexes**

PK(examQuestionId)

UNIQUE(examId,questionId)

UNIQUE(examId,questionOrder)

INDEX(questionId)

INDEX(examId)

### **Delete Rule**

* Exam → CASCADE  
* Question → RESTRICT

---

# **Question Bank Summary**

| Table | Type |
| ----- | ----- |
| QuestionCategory | Master |
| DifficultyLevel | Master |
| Question | Master |
| ExamQuestion | Mapping |

---

# **Important Engineering Refinements**

While reviewing the schema, I identified several improvements that I strongly recommend before freezing the database.

---

## **Refinement 1 — Separate Question Options into a Dedicated Table**

Instead of storing:

optionA  
optionB  
optionC  
optionD  
correctOption

I recommend introducing:

QuestionOption  
\------------  
optionId  
questionId  
optionText  
optionOrder  
isCorrect

### **Why?**

* Supports any number of options (not limited to four).  
* Better normalization (1NF).  
* Easier to implement MSQ (Multiple Select Questions).  
* Simpler randomization of options.  
* Cleaner UI rendering.  
* Future support for image/audio options.

This aligns much better with our DB-005 normalization strategy.

---

## **Refinement 2 — Question Versioning**

Rather than editing questions directly, consider adding:

versionNumber  
isLatestVersion  
parentQuestionId

This preserves historical integrity for exams that have already been conducted.

---

## **Refinement 3 — Media Support**

Instead of embedding media URLs inside the Question table, introduce a future table:

QuestionMedia

mediaId  
questionId  
mediaType  
filePath  
displayOrder

This supports:

* Images  
* Audio  
* Video  
* PDFs  
* Diagrams

without changing the Question schema.

---

## **Refinement 4 — Question Metadata**

Useful future additions include:

* Bloom's Taxonomy Level  
* Topic  
* Subtopic  
* Learning Outcome  
* Language  
* Estimated Difficulty Score (AI-generated)  
* Usage Count (computed/cached)

These are not required now but fit naturally into the design later.

---

# **Part 3 Status: Complete ✅**

At this point, the **Question Bank** is fully modeled and supports:

* Categorized questions  
* Difficulty classification  
* Multiple question types  
* Exam-specific question configuration  
* Future extensibility for richer content

The next section, **Part 4**, will define the core examination execution workflow:

1. ExamAttempt  
2. Answer  
3. Evaluation  
4. EvaluationDetail  
5. Result

This is the transactional heart of the Online Examination Platform, where examination delivery, submission, evaluation, and result generation are modeled.

# **PART 4 — Examination Delivery, Evaluation & Result Database Specification**

This section covers the following tables:

1. ExamAttempt  
2. Answer  
3. Evaluation  
4. EvaluationDetail  
5. Result

> **This is the core transactional subsystem of the Online Examination Platform.** These tables are responsible for recording the student's examination session, storing responses, evaluating submissions, and publishing results while maintaining consistency, integrity, and auditability.

---

# **Table 15 — ExamAttempt**

### **Purpose**

Stores each attempt made by a candidate for a registered examination.

### **Columns**

| Column | Data Type | Null | Default |
| ----- | ----- | ----- | ----- |
| attemptId | BIGSERIAL | NO | Auto |
| registrationId | BIGINT | NO | — |
| attemptNumber | SMALLINT | NO | 1 |
| startTime | TIMESTAMPTZ | NO | NOW() |
| endTime | TIMESTAMPTZ | YES | NULL |
| submittedAt | TIMESTAMPTZ | YES | NULL |
| status | VARCHAR(20) | NO | 'NOT\_STARTED' |
| totalTimeSpentSeconds | INTEGER | YES | NULL |
| ipAddress | INET | YES | NULL |
| deviceInfo | TEXT | YES | NULL |
| browserInfo | TEXT | YES | NULL |
| submissionMethod | VARCHAR(30) | NO | 'MANUAL' |
| autoSubmitted | BOOLEAN | NO | FALSE |
| createdAt | TIMESTAMPTZ | NO | NOW() |

### **Primary Key**

* attemptId

### **Foreign Keys**

* registrationId → CandidateRegistration(registrationId)

### **Unique Constraints**

* (registrationId, attemptNumber)

### **Check Constraints**

attemptNumber \> 0

status IN  
('NOT\_STARTED','IN\_PROGRESS','SUBMITTED','AUTO\_SUBMITTED','EVALUATED','ABANDONED')

submissionMethod IN  
('MANUAL','AUTO\_TIMEOUT','SYSTEM')

### **Indexes**

PK(attemptId)

INDEX(registrationId)

INDEX(status)

INDEX(startTime)

UNIQUE(registrationId,attemptNumber)

### **Delete Rule**

RESTRICT

---

# **Table 16 — Answer**

### **Purpose**

Stores every answer submitted by a student during an examination attempt.

### **Columns**

| Column | Data Type | Null | Default |
| ----- | ----- | ----- | ----- |
| answerId | BIGSERIAL | NO | Auto |
| attemptId | BIGINT | NO | — |
| questionId | BIGINT | NO | — |
| selectedOption | VARCHAR(20) | YES | NULL |
| answerText | TEXT | YES | NULL |
| isMarkedForReview | BOOLEAN | NO | FALSE |
| isAnswered | BOOLEAN | NO | FALSE |
| submittedAt | TIMESTAMPTZ | NO | NOW() |
| timeSpentSeconds | INTEGER | NO | 0 |
| createdAt | TIMESTAMPTZ | NO | NOW() |

### **Primary Key**

* answerId

### **Foreign Keys**

* attemptId → ExamAttempt(attemptId)  
* questionId → Question(questionId)

### **Unique Constraints**

* (attemptId, questionId)

### **Check Constraints**

timeSpentSeconds \>= 0

### **Indexes**

PK(answerId)

INDEX(attemptId)

INDEX(questionId)

INDEX(isAnswered)

INDEX(isMarkedForReview)

UNIQUE(attemptId,questionId)

### **Delete Rule**

CASCADE from ExamAttempt

RESTRICT from Question

---

# **Table 17 — Evaluation**

### **Purpose**

Stores the overall evaluation summary of an examination attempt.

### **Columns**

| Column | Data Type | Null | Default |
| ----- | ----- | ----- | ----- |
| evaluationId | BIGSERIAL | NO | Auto |
| attemptId | BIGINT | NO | — |
| totalMarksObtained | NUMERIC(6,2) | NO | 0 |
| totalCorrect | INTEGER | NO | 0 |
| totalWrong | INTEGER | NO | 0 |
| totalSkipped | INTEGER | NO | 0 |
| evaluationStatus | VARCHAR(20) | NO | 'PENDING' |
| evaluatedBy | BIGINT | YES | NULL |
| evaluatedAt | TIMESTAMPTZ | YES | NULL |
| remarks | TEXT | YES | NULL |
| createdAt | TIMESTAMPTZ | NO | NOW() |

### **Primary Key**

* evaluationId

### **Foreign Keys**

* attemptId → ExamAttempt(attemptId)  
* evaluatedBy → User(userId)

### **Unique Constraints**

* attemptId

### **Check Constraints**

totalMarksObtained \>= 0

evaluationStatus IN  
('PENDING','AUTO\_EVALUATED','MANUAL\_EVALUATED','FINALIZED')

### **Indexes**

PK(evaluationId)

UNIQUE(attemptId)

INDEX(evaluationStatus)

INDEX(evaluatedAt)

### **Delete Rule**

CASCADE from ExamAttempt

---

# **Table 18 — EvaluationDetail**

### **Purpose**

Stores question-wise evaluation details.

### **Columns**

| Column | Data Type | Null | Default |
| ----- | ----- | ----- | ----- |
| evaluationDetailId | BIGSERIAL | NO | Auto |
| evaluationId | BIGINT | NO | — |
| questionId | BIGINT | NO | — |
| marksAwarded | NUMERIC(5,2) | NO | 0 |
| maxMarks | NUMERIC(5,2) | NO | — |
| isCorrect | BOOLEAN | NO | FALSE |
| evaluatorRemarks | TEXT | YES | NULL |
| evaluatedAt | TIMESTAMPTZ | NO | NOW() |

### **Primary Key**

* evaluationDetailId

### **Foreign Keys**

* evaluationId → Evaluation(evaluationId)  
* questionId → Question(questionId)

### **Unique Constraints**

* (evaluationId, questionId)

### **Check Constraints**

marksAwarded \>= 0

marksAwarded \<= maxMarks

### **Indexes**

PK(evaluationDetailId)

INDEX(evaluationId)

INDEX(questionId)

UNIQUE(evaluationId,questionId)

### **Delete Rule**

CASCADE

---

# **Table 19 — Result**

### **Purpose**

Stores the published examination result.

### **Columns**

| Column | Data Type | Null | Default |
| ----- | ----- | ----- | ----- |
| resultId | BIGSERIAL | NO | Auto |
| evaluationId | BIGINT | NO | — |
| percentage | NUMERIC(5,2) | NO | — |
| grade | VARCHAR(5) | YES | NULL |
| passStatus | BOOLEAN | NO | FALSE |
| publishedAt | TIMESTAMPTZ | YES | NULL |
| publishedBy | BIGINT | YES | NULL |
| isPublished | BOOLEAN | NO | FALSE |
| remarks | TEXT | YES | NULL |
| createdAt | TIMESTAMPTZ | NO | NOW() |

### **Primary Key**

* resultId

### **Foreign Keys**

* evaluationId → Evaluation(evaluationId)  
* publishedBy → User(userId)

### **Unique Constraints**

* evaluationId

### **Check Constraints**

percentage BETWEEN 0 AND 100

### **Indexes**

PK(resultId)

UNIQUE(evaluationId)

INDEX(isPublished)

INDEX(passStatus)

INDEX(publishedAt)

### **Delete Rule**

RESTRICT

---

# **Examination Delivery Summary**

| Table | Type |
| ----- | ----- |
| ExamAttempt | Transaction |
| Answer | Transaction |
| Evaluation | Transaction |
| EvaluationDetail | Transaction |
| Result | Transaction |

---

# **Important Engineering Improvements (Recommended Before Freezing)**

After reviewing this section against our architecture principles, I recommend the following refinements.

---

## **1\. Replace `selectedOption` with `selectedOptionId`**

Current schema:

selectedOption

Better:

selectedOptionId

This becomes even more valuable if we adopt the **QuestionOption** table recommended in Part 3\.

---

## **2\. Remove `percentage` from Result**

Percentage is a **derived value**.

It can always be computed as:

Marks Obtained / Total Marks × 100

According to **DB-005 (Normalization Strategy)** and **Principle 12 (Measurable Improvements)**, derived values should generally not be permanently stored unless there is a demonstrated performance need.

A better approach is to compute it during result generation or cache it if profiling shows it is expensive.

---

## **3\. Add Attempt Integrity Information**

To strengthen auditability and support future security features, consider adding:

| Column | Type |
| ----- | ----- |
| systemSubmitted | BOOLEAN |
| submissionReason | VARCHAR(50) |
| lastSavedAt | TIMESTAMPTZ |

This allows the system to distinguish between manual submissions, timeout submissions, and recovery scenarios.

---

## **4\. Keep Evaluation Immutable After Finalization**

Once `evaluationStatus = FINALIZED`, evaluation records should become immutable. Any correction should create a new revision or be handled through an explicit re-evaluation workflow rather than updating historical data.

---

## **5\. Consider Moving `grade` to Business Logic**

The `grade` value is also derived from marks and grading rules. Unless grading policies are expected to change historically, it may be better computed during publication rather than stored. If institutional policy requires preserving the exact published grade, storing it in `Result` is justified.

---

# **Part 4 Status: Complete ✅**

The examination execution pipeline is now fully modeled:

CandidateRegistration  
        │  
        ▼  
ExamAttempt  
        │  
        ▼  
Answer  
        │  
        ▼  
Evaluation  
        │  
        ▼  
EvaluationDetail  
        │  
        ▼  
Result

This establishes a clear, auditable flow from registration through result publication.

The final section, **Part 5**, will complete the database with:

1. Notification  
2. NotificationTemplate  
3. AuditLog  
4. SystemEvent  
5. PerformanceMetric  
6. SystemConfiguration  
7. FeatureFlag

These tables support communication, auditing, monitoring, system configuration, and operational management.

# **PART 5 — Notifications, Audit & Administration Database Specification**

This section completes the database design with the remaining **7 tables**.

1. Notification  
2. NotificationTemplate  
3. AuditLog  
4. SystemEvent  
5. PerformanceMetric  
6. SystemConfiguration  
7. FeatureFlag

These tables are responsible for system administration, monitoring, auditing, configuration, and communication.

---

# **Table 20 — Notification**

### **Purpose**

Stores notifications delivered to users.

### **Columns**

| Column | Data Type | Null | Default |
| ----- | ----- | ----- | ----- |
| notificationId | BIGSERIAL | NO | Auto |
| userId | BIGINT | NO | — |
| templateId | BIGINT | YES | NULL |
| title | VARCHAR(150) | NO | — |
| message | TEXT | NO | — |
| notificationType | VARCHAR(30) | NO | — |
| deliveryChannel | VARCHAR(20) | NO | 'IN\_APP' |
| priority | VARCHAR(20) | NO | 'NORMAL' |
| isRead | BOOLEAN | NO | FALSE |
| sentAt | TIMESTAMPTZ | NO | NOW() |
| readAt | TIMESTAMPTZ | YES | NULL |
| expiresAt | TIMESTAMPTZ | YES | NULL |

### **Primary Key**

* notificationId

### **Foreign Keys**

* userId → User(userId)  
* templateId → NotificationTemplate(templateId)

### **Unique Constraints**

None

### **Check Constraints**

notificationType IN

('EXAM','RESULT','SYSTEM','REMINDER','SECURITY')

deliveryChannel IN

('IN\_APP','EMAIL','SMS')

priority IN

('LOW','NORMAL','HIGH','CRITICAL')

### **Indexes**

PK(notificationId)

INDEX(userId)

INDEX(isRead)

INDEX(sentAt)

INDEX(notificationType)

### **Delete Rule**

User → CASCADE

Template → SET NULL

---

# **Table 21 — NotificationTemplate**

### **Purpose**

Stores reusable notification templates.

### **Columns**

| Column | Data Type | Null | Default |
| ----- | ----- | ----- | ----- |
| templateId | BIGSERIAL | NO | Auto |
| templateName | VARCHAR(100) | NO | — |
| notificationType | VARCHAR(30) | NO | — |
| subject | VARCHAR(150) | YES | NULL |
| templateBody | TEXT | NO | — |
| isActive | BOOLEAN | NO | TRUE |
| createdAt | TIMESTAMPTZ | NO | NOW() |
| updatedAt | TIMESTAMPTZ | NO | NOW() |

### **Primary Key**

* templateId

### **Foreign Keys**

None

### **Unique Constraints**

* templateName

### **Check Constraints**

None

### **Indexes**

PK(templateId)

UNIQUE(templateName)

INDEX(notificationType)

### **Delete Rule**

RESTRICT

---

# **Table 22 — AuditLog**

### **Purpose**

Maintains immutable security and activity audit records.

### **Columns**

| Column | Data Type | Null | Default |
| ----- | ----- | ----- | ----- |
| auditLogId | BIGSERIAL | NO | Auto |
| userId | BIGINT | YES | NULL |
| entityName | VARCHAR(100) | NO | — |
| entityId | BIGINT | YES | NULL |
| action | VARCHAR(30) | NO | — |
| oldValue | JSONB | YES | NULL |
| newValue | JSONB | YES | NULL |
| ipAddress | INET | YES | NULL |
| timestamp | TIMESTAMPTZ | NO | NOW() |

### **Primary Key**

* auditLogId

### **Foreign Keys**

* userId → User(userId)

### **Unique Constraints**

None

### **Check Constraints**

action IN

('CREATE','UPDATE','DELETE','LOGIN','LOGOUT','VIEW','EXPORT')

### **Indexes**

PK(auditLogId)

INDEX(userId)

INDEX(entityName)

INDEX(action)

INDEX(timestamp)

### **Delete Rule**

RESTRICT

---

# **Table 23 — SystemEvent**

### **Purpose**

Stores significant application events.

### **Columns**

| Column | Data Type | Null | Default |
| ----- | ----- | ----- | ----- |
| eventId | BIGSERIAL | NO | Auto |
| eventType | VARCHAR(50) | NO | — |
| severity | VARCHAR(20) | NO | — |
| sourceModule | VARCHAR(50) | NO | — |
| description | TEXT | NO | — |
| occurredAt | TIMESTAMPTZ | NO | NOW() |
| resolvedAt | TIMESTAMPTZ | YES | NULL |
| status | VARCHAR(20) | NO | 'OPEN' |

### **Primary Key**

* eventId

### **Foreign Keys**

None

### **Unique Constraints**

None

### **Check Constraints**

severity IN

('INFO','WARNING','ERROR','CRITICAL')

status IN

('OPEN','ACKNOWLEDGED','RESOLVED')

### **Indexes**

PK(eventId)

INDEX(eventType)

INDEX(severity)

INDEX(status)

INDEX(occurredAt)

### **Delete Rule**

RESTRICT

---

# **Table 24 — PerformanceMetric**

### **Purpose**

Stores runtime performance statistics.

### **Columns**

| Column | Data Type | Null | Default |
| ----- | ----- | ----- | ----- |
| metricId | BIGSERIAL | NO | Auto |
| metricName | VARCHAR(100) | NO | — |
| metricValue | NUMERIC(12,4) | NO | — |
| metricUnit | VARCHAR(20) | NO | — |
| sourceModule | VARCHAR(50) | NO | — |
| recordedAt | TIMESTAMPTZ | NO | NOW() |

### **Primary Key**

* metricId

### **Foreign Keys**

None

### **Unique Constraints**

None

### **Check Constraints**

metricValue \>= 0

### **Indexes**

PK(metricId)

INDEX(metricName)

INDEX(sourceModule)

INDEX(recordedAt)

### **Delete Rule**

RESTRICT

---

# **Table 25 — SystemConfiguration**

### **Purpose**

Stores configurable system parameters.

### **Columns**

| Column | Data Type | Null | Default |
| ----- | ----- | ----- | ----- |
| configurationId | BIGSERIAL | NO | Auto |
| configurationKey | VARCHAR(100) | NO | — |
| configurationValue | TEXT | NO | — |
| valueType | VARCHAR(20) | NO | — |
| description | TEXT | YES | NULL |
| isEditable | BOOLEAN | NO | TRUE |
| updatedAt | TIMESTAMPTZ | NO | NOW() |
| updatedBy | BIGINT | YES | NULL |

### **Primary Key**

* configurationId

### **Foreign Keys**

* updatedBy → User(userId)

### **Unique Constraints**

* configurationKey

### **Check Constraints**

valueType IN

('STRING','INTEGER','BOOLEAN','DECIMAL','JSON')

### **Indexes**

PK(configurationId)

UNIQUE(configurationKey)

### **Delete Rule**

RESTRICT

---

# **Table 26 — FeatureFlag**

### **Purpose**

Controls enabling and disabling application features without code changes.

### **Columns**

| Column | Data Type | Null | Default |
| ----- | ----- | ----- | ----- |
| featureFlagId | BIGSERIAL | NO | Auto |
| flagName | VARCHAR(100) | NO | — |
| description | TEXT | YES | NULL |
| isEnabled | BOOLEAN | NO | FALSE |
| rolloutPercentage | SMALLINT | NO | 100 |
| createdAt | TIMESTAMPTZ | NO | NOW() |
| updatedAt | TIMESTAMPTZ | NO | NOW() |

### **Primary Key**

* featureFlagId

### **Foreign Keys**

None

### **Unique Constraints**

* flagName

### **Check Constraints**

rolloutPercentage BETWEEN 0 AND 100

### **Indexes**

PK(featureFlagId)

UNIQUE(flagName)

INDEX(isEnabled)

### **Delete Rule**

RESTRICT

---

# **Administration & Monitoring Summary**

| Table | Type |
| ----- | ----- |
| Notification | Transaction |
| NotificationTemplate | Master |
| AuditLog | Audit |
| SystemEvent | Monitoring |
| PerformanceMetric | Monitoring |
| SystemConfiguration | Configuration |
| FeatureFlag | Configuration |

---

# **Complete Database Summary**

| Category | Tables |
| ----- | ----- |
| Identity & Access | 6 |
| Academic & Examination | 4 |
| Question Bank | 4 |
| Examination Execution | 5 |
| Administration & Monitoring | 7 |
| **Total** | **26 Tables** |

---

# **Overall Review & Recommendations**

Now that all 26 tables have been defined, I would make three architectural refinements before freezing the schema:

### **1\. Normalize Question Options**

Instead of storing `optionA`, `optionB`, `optionC`, and `optionD` in the `Question` table, introduce a separate `QuestionOption` table. This supports any number of options, multiple-correct-answer questions, and future media-based options while improving normalization.

### **2\. Introduce Specialized Profile Tables**

Keep `User` as the authentication entity and add role-specific profile tables such as `StudentProfile` and `FacultyProfile` if additional attributes become necessary. This avoids cluttering the `User` table while maintaining a clean identity model.

### **3\. Expand Monitoring for KPI Evaluation**

Since your project emphasizes KPIs like response time, concurrency, and resource utilization, `PerformanceMetric` can later be extended to capture metrics such as API latency, CPU usage, memory usage, concurrent sessions, database query times, cache hit ratios, and thread pool statistics. This will directly support the measurable optimization goals defined in your project philosophy.

---

## **DB-006 Status**

With Parts 1–5 complete, **DB-006 (Physical Schema Design)** is now complete from a structural perspective. The next logical database phase is **DB-007 — Constraints & Data Integrity**, where we'll formalize referential actions, business constraints, transaction rules, and integrity mechanisms across the entire schema before moving on to indexing and performance optimization.

# TechStack

## **Final Tech Stack**

| Category | Recommended |
| ----- | ----- |
| Programming Language | Python 3.13 |
| Backend Framework | **Flask (Layered Modular Monolith)** |
| Frontend | **HTML5 \+ CSS3 \+ Bootstrap 5 \+ JavaScript** |
| Database | MySQL 8 |
| ORM | SQLAlchemy ORM \+ Parameterized Raw SQL (only where justified) |
| Authentication | Stateful Session-Based Authentication |
| Authorization | Database-driven RBAC |
| Password Hashing | Argon2id |
| API Style | REST (internal AJAX endpoints where needed) |
| API Documentation | Simple OpenAPI/Swagger (optional) |
| Background Tasks | APScheduler |
| Logging | Python logging |
| Database Migration | Alembic or Flask-Migrate |
| Testing | pytest |
| Version Control | Git \+ GitHub |
| IDE | VS Code |
| Caching | Simple in-memory cache for master data |
| Deployment | Local → Docker (optional) → Nginx \+ Gunicorn (if deployed) |

---

# **Why this stack?**

It directly supports the engineering concepts your faculty wants to evaluate:

| Subject | Demonstrated Through |
| ----- | ----- |
| Software Engineering | Layered modular architecture, separation of concerns, high cohesion, low coupling |
| OOP | Services, repositories, models, encapsulation |
| DBMS | MySQL, normalization, SQLAlchemy, transactions, indexing |
| Computer Networks | HTTP, REST, AJAX, sessions |
| Operating Systems | Session lifecycle, concurrent users, scheduling with APScheduler |
| Cyber Security | Argon2id, RBAC, CSRF protection, parameterized queries |
| Web Technologies | HTML, CSS, Bootstrap, JavaScript, responsive UI |
| Testing | Unit and integration testing with pytest |

## 

# DESIGN PHILOSOPHY

# **DESIGN PHILOSOPHY**

## **Online Examination Platform**

### **Version 1.0**

---

# **Document Information**

| Item | Details |
| ----- | ----- |
| Document Name | Design Philosophy |
| Project | Online Examination Platform |
| Version | 1.0 |
| Status |  |
| Purpose | Define the engineering philosophy and guiding principles governing all architectural, technological, and implementation decisions throughout the project lifecycle. |

---

# **1\. Purpose**

The purpose of this document is to establish the engineering philosophy that governs the design, implementation, and evolution of the Online Examination Platform.

Rather than treating the project as an isolated web application or database application, this project is designed as an **integration project** where multiple core Computer Science subjects are deliberately combined to solve real engineering problems. Every major design decision must contribute not only to the functional requirements of the system but also to measurable improvements in performance, security, maintainability, scalability, reliability, and overall software quality.

This document serves as the foundation for all future project artifacts including the Project Development Lifecycle, Architecture Decision Points (ADPs), Engineering Decision Register (EDR), Software Requirements Specification (SRS), Database Design, API Design, and Implementation.

---

# **2\. Vision**

Develop a secure, efficient, scalable, maintainable, and well-engineered Online Examination Platform that demonstrates the practical integration of core Computer Science concepts while satisfying all functional requirements, project deliverables, KPIs, and expected outcomes defined by the college.

---

# **3\. Design Objectives**

The project shall be designed to achieve the following objectives:

* Demonstrate practical application of all major core Computer Science subjects.  
* Maintain a clean and modular software architecture.  
* Achieve high performance through efficient algorithms and optimized data structures.  
* Ensure data integrity using sound database engineering practices.  
* Provide secure authentication, authorization, and communication.  
* Support concurrent users efficiently.  
* Minimize resource utilization while maximizing throughput.  
* Produce maintainable, extensible, and well-documented software.  
* Align every engineering decision with measurable project KPIs.

---

# **4\. Engineering Philosophy**

The project is an engineering-focused integration project rather than a technology showcase.

Every component of the system must exist because it solves an engineering problem. Technologies, frameworks, libraries, and algorithms are selected only when they improve the overall quality of the system and demonstrate the underlying Computer Science concepts expected by the project evaluation criteria.

The architecture shall remain independent of implementation technologies, ensuring that technology supports the architecture rather than defining it.

---

# **5\. Design Principles**

## **Principle 1 – Integration of Core Computer Science Subjects**

The project shall deliberately integrate major Computer Science subjects into a unified software system. Every module should naturally demonstrate one or more core subjects while solving real engineering problems.

| Subject | Primary Contribution |
| ----- | ----- |
| Programming | Modular implementation and reusable logic |
| OOP | Encapsulation, abstraction, inheritance, polymorphism, maintainability |
| DSA | Efficient algorithms, optimized time and space complexity |
| DBMS | Normalization, transactions, indexing, integrity, query optimization |
| Computer Networks | Secure client-server communication, REST APIs, session management |
| Operating Systems | Concurrency, synchronization, scheduling, resource utilization |
| Software Engineering | Architecture, modularity, testing, documentation |
| Web Technologies | Responsive and accessible user interaction |

---

## **Principle 2 – Every Design Decision Must Answer Two Questions**

Every architectural, technological, or implementation decision must answer:

1. Which Computer Science subject(s) does this demonstrate?  
2. How does it improve the system?

Improvements may include:

* Performance  
* Security  
* Scalability  
* Maintainability  
* Reliability  
* Lower Time Complexity  
* Lower Space Complexity  
* Better CPU utilization  
* Better concurrency  
* Better resource utilization

If a feature cannot justify both questions, its inclusion should be reconsidered.

---

## **Principle 3 – Requirements are Fixed**

The college project documentation—including subject-wise implementation requirements, deliverables, KPIs, and expected outcomes—is the authoritative source of project requirements.

The architecture may be improved, but required functionality shall never be removed or altered.

---

## **Principle 4 – Functional Architecture Over Team Organization**

Project architecture shall be organized according to functional cohesion and engineering principles rather than team assignments or work distribution.

Software modules represent business capabilities, not development responsibilities.

---

## **Principle 5 – Module Merging Requires Technical Justification**

Modules may only be merged when the merge:

* Increases cohesion  
* Reduces coupling  
* Improves maintainability  
* Eliminates redundancy  
* Preserves single responsibility  
* Strengthens demonstration of Computer Science concepts

---

## **Principle 6 – Every Subject Must Have a Natural Contribution**

Core Computer Science concepts shall never be artificially inserted merely to satisfy evaluation criteria.

Each subject must solve an actual engineering problem.

Examples:

* Hash tables improve lookup performance.  
* Transactions preserve examination consistency.  
* Thread synchronization prevents race conditions.  
* Indexes improve database performance.  
* RBAC improves security.

---

## **Principle 7 – KPIs Drive the Architecture**

System architecture shall directly support the project's Key Performance Indicators.

Examples:

| KPI | Engineering Solution |
| ----- | ----- |
| Response Time | Efficient algorithms, optimized SQL, caching |
| Concurrent Users | Thread management, synchronization |
| Database Integrity | Constraints, transactions |
| Security | RBAC, Argon2id, parameterized queries |
| Maintainability | Layered architecture, SOLID principles |

---

## **Principle 8 – Deliverables Must Be a By-product of the Architecture**

Project deliverables shall naturally emerge from the engineering process rather than being developed independently.

Examples:

* UML diagrams derive from class design.  
* SQL scripts derive from the database schema.  
* API documentation derives from REST endpoints.  
* Unit tests derive from modular implementation.

---

## **Principle 9 – Think Like Software Engineers**

Engineering decisions must always be supported by technical reasoning rather than syllabus coverage alone.

Instead of:

> "A Queue was used because queues are part of DSA."

The project should justify:

> "A Queue was selected because examination requests are processed in FIFO order, improving fairness while demonstrating Data Structures."

---

## **Principle 10 – No Accidental Decisions**

Every significant decision shall document:

* Problem being solved  
* Alternative solutions  
* Selected solution  
* Technical justification  
* Computer Science concepts demonstrated  
* Measurable improvement

---

## **Principle 11 – Engineering Over Convenience**

Whenever multiple solutions satisfy the functional requirements, the solution providing stronger engineering quality and better demonstration of core Computer Science concepts shall be preferred over the easiest implementation.

---

## **Principle 12 – Measurable Optimizations**

Every optimization introduced into the system shall be measurable.

Examples include:

| Optimization | Before | After |
| ----- | ----- | ----- |
| Question Search | O(n) | O(1) using HashMap |
| Database Query | Full Table Scan | Indexed Query |
| Report Generation | Sequential | Parallel Processing |
| Answer Evaluation | Single Thread | Multi-threaded |

Performance improvements should be validated using measurable metrics whenever possible.

---

## **Principle 13 – Frameworks Support Engineering, Not Replace It**

Frameworks shall automate repetitive infrastructure tasks without replacing opportunities to demonstrate fundamental Computer Science concepts.

Examples:

* SQLAlchemy ORM for CRUD operations while using SQLAlchemy Core or parameterized SQL for complex queries.  
* Flask for routing while implementing custom service and repository layers.  
* APScheduler for scheduling while implementing scheduling policies within the application.  
* Custom in-memory caching instead of introducing Redis without architectural justification.

---

# **6\. Decision Hierarchy**

Engineering decisions shall follow the following precedence:

1. College Requirements  
2. Approved Project Architecture  
3. Approved Technology Stack  
4. Engineering Decisions  
5. Implementation Decisions

Lower-level decisions shall never violate higher-level decisions.

---

# **7\. Technology Selection Philosophy**

Technology shall never be selected because it is popular or modern.

Every selected technology must:

* Solve a real engineering problem.  
* Improve one or more project KPIs.  
* Support the selected architecture.  
* Demonstrate relevant Computer Science concepts.  
* Avoid unnecessary complexity.

---

# **8\. Performance Philosophy**

Performance optimization shall focus on measurable improvements rather than premature optimization.

Optimization techniques may include:

* Efficient data structures  
* Optimized algorithms  
* Query optimization  
* Appropriate indexing  
* Concurrency where beneficial  
* Resource-efficient scheduling  
* Application-level caching

---

# **9\. Security Philosophy**

Security shall be integrated throughout the architecture rather than added after implementation.

The system shall adopt:

* Principle of Least Privilege  
* Defense in Depth  
* Secure by Default  
* Input Validation  
* Parameterized SQL Queries  
* Secure Password Hashing (Argon2id)  
* Role-Based Access Control  
* Secure Session Management  
* Audit Logging

---

# **10\. Maintainability Philosophy**

Maintainability shall be achieved through:

* Layered architecture  
* High cohesion  
* Low coupling  
* Modular implementation  
* SOLID principles  
* Consistent coding standards  
* Clear documentation  
* Comprehensive testing

---

# **11\. Success Criteria**

The project shall be considered successful if it:

* Satisfies all college functional requirements.  
* Meets or exceeds project KPIs.  
* Demonstrates every required Computer Science subject naturally.  
* Maintains a modular and scalable architecture.  
* Provides measurable performance improvements.  
* Implements secure engineering practices.  
* Produces maintainable, extensible, and well-documented software.

# PROJECT DEVELOPMENT LIFECYCLE

# **PROJECT DEVELOPMENT LIFECYCLE (PDLC)**

## **Online Examination Platform**

### **Version 1.0**

---

# **Document Information**

| Item | Details |
| ----- | ----- |
| Document Name | Project Development Lifecycle |
| Project | Online Examination Platform |
| Version | 1.0 |
| Status |  |
| Purpose | Define the structured engineering process used to design, develop, test, optimize, and document the Online Examination Platform. |

---

# **1\. Purpose**

The Project Development Lifecycle (PDLC) defines the sequence of engineering activities followed during the development of the Online Examination Platform.

Unlike traditional software development lifecycles that focus primarily on implementation, this lifecycle emphasizes systematic engineering decisions, traceability, and integration of core Computer Science subjects throughout the development process.

Each phase produces specific outputs that become inputs for subsequent phases, ensuring consistency, maintainability, and complete traceability from requirements to implementation.

---

# **2\. Development Philosophy**

The lifecycle follows five fundamental principles:

* Requirements drive architecture.  
* Architecture drives technology.  
* Technology supports implementation.  
* Every phase produces measurable deliverables.  
* Every deliverable remains traceable back to project requirements.

---

# **3\. Lifecycle Overview**

Phase 1  
Requirement Analysis  
        │  
        ▼  
Phase 2  
Architecture Design  
        │  
        ▼  
Phase 3  
Technology Selection  
        │  
        ▼  
Phase 4  
Database Design  
        │  
        ▼  
Phase 5  
API Design  
        │  
        ▼  
Phase 6  
Class Design (Object-Oriented Design)  
        │  
        ▼  
Phase 7  
Algorithm & Data Structure Design  
        │  
        ▼  
Phase 8  
Operating System & Concurrency Design  
        │  
        ▼  
Phase 9  
Security Design  
        │  
        ▼  
Phase 10  
User Interface Design  
        │  
        ▼  
Phase 11  
Implementation  
        │  
        ▼  
Phase 12  
Testing & Validation  
        │  
        ▼  
Phase 13  
Performance Optimization  
        │  
        ▼  
Phase 14  
Documentation & Project Closure  
---

# **Phase 1 — Requirement Analysis**

## **Objective**

Understand and analyze the complete project requirements.

## **Activities**

* Analyze project statement.  
* Study faculty evaluation criteria.  
* Analyze deliverables.  
* Analyze KPIs.  
* Analyze expected outcomes.  
* Identify hidden requirements.  
* Map requirements to core CS subjects.  
* Define project scope.

## **Inputs**

* College Project Document

## **Outputs**

* Requirement Analysis Report  
* Requirement List  
* Subject Mapping  
* Initial Module Identification

---

# **Phase 2 — Architecture Design**

## **Objective**

Transform requirements into a structured software architecture.

## **Activities**

* Design Philosophy  
* Module Identification  
* Module Merging  
* Layered Architecture  
* Domain Decomposition  
* Bounded Context Identification  
* Module Ownership  
* High-Level System Architecture

## **Inputs**

* Requirement Analysis

## **Outputs**

* Architecture Document  
* Architecture Decision Points (ADPs)  
* Module Architecture  
* Component Diagram

---

# **Phase 3 — Technology Selection**

## **Objective**

Select technologies that best support the architecture.

## **Activities**

* Programming Language Selection  
* Framework Selection  
* Database Selection  
* ORM Selection  
* Authentication Technology  
* Testing Framework  
* Logging Framework  
* Migration Framework  
* Development Environment

## **Inputs**

* Architecture Design

## **Outputs**

* Technology Stack  
* Technology Selection Records (internal)  
* Engineering Justifications

---

# **Phase 4 — Database Design**

## **Objective**

Design a secure, normalized, and optimized relational database.

## **Activities**

* Domain Data Modeling  
* ER Diagram Design  
* Logical Database Design  
* Physical Database Design  
* Normalization  
* Primary and Foreign Keys  
* Constraints  
* Index Strategy  
* Transaction Design  
* Query Optimization Planning

## **Inputs**

* Architecture  
* Technology Stack

## **Outputs**

* ER Diagram  
* Database Schema  
* SQL Scripts  
* Data Dictionary

---

# **Phase 5 — API Design**

## **Objective**

Define communication between system modules and external clients.

## **Activities**

* REST Endpoint Design  
* Request/Response Models  
* Validation Rules  
* Error Handling  
* Authentication Integration  
* API Documentation

## **Inputs**

* Database Design

## **Outputs**

* API Specification  
* Endpoint Documentation

---

# **Phase 6 — Class Design (Object-Oriented Design)**

## **Objective**

Transform architecture into an object-oriented implementation.

## **Activities**

* Class Identification  
* Responsibility Assignment  
* Interface Design  
* Service Layer Design  
* Repository Design  
* Design Patterns  
* UML Class Diagrams

## **Inputs**

* Database Design  
* API Design

## **Outputs**

* UML Class Diagram  
* Class Specifications

---

# **Phase 7 — Algorithm & Data Structure Design**

## **Objective**

Optimize system performance through efficient algorithms and data structures.

## **Activities**

* Data Structure Selection  
* Time Complexity Analysis  
* Space Complexity Analysis  
* Search Algorithms  
* Scheduling Algorithms  
* Cache Strategy  
* Performance Analysis

## **Inputs**

* Class Design

## **Outputs**

* Algorithm Specifications  
* Complexity Analysis

---

# **Phase 8 — Operating System & Concurrency Design**

## **Objective**

Design mechanisms for efficient concurrent execution and resource management.

## **Activities**

* Thread Design  
* Synchronization  
* Background Scheduling  
* Session Management  
* Deadlock Prevention  
* Resource Allocation  
* CPU Utilization Planning

## **Inputs**

* Algorithm Design

## **Outputs**

* Concurrency Design  
* Thread Architecture

---

# **Phase 9 — Security Design**

## **Objective**

Protect the system against security threats.

## **Activities**

* Authentication Design  
* Authorization Design  
* Session Security  
* Password Protection  
* Input Validation  
* SQL Injection Prevention  
* CSRF Protection  
* Audit Logging

## **Inputs**

* API Design  
* Database Design

## **Outputs**

* Security Architecture  
* Threat Mitigation Plan

---

# **Phase 10 — User Interface Design**

## **Objective**

Design a user-friendly and responsive interface.

## **Activities**

* Wireframes  
* Navigation  
* Responsive Layout  
* Role-Based Dashboards  
* User Experience Design

## **Inputs**

* API Design

## **Outputs**

* UI Mockups  
* Screen Designs

---

# **Phase 11 — Implementation**

## **Objective**

Develop the complete software system.

## **Activities**

* Backend Development  
* Frontend Development  
* Database Implementation  
* Module Integration  
* Code Review

## **Inputs**

* All Design Documents

## **Outputs**

* Working Software

---

# **Phase 12 — Testing & Validation**

## **Objective**

Verify correctness and quality.

## **Activities**

* Unit Testing  
* Integration Testing  
* System Testing  
* Functional Testing  
* Security Testing  
* Performance Testing  
* Bug Fixing

## **Inputs**

* Implemented System

## **Outputs**

* Test Reports  
* Validation Results

---

# **Phase 13 — Performance Optimization**

## **Objective**

Improve efficiency and satisfy project KPIs.

## **Activities**

* SQL Optimization  
* Algorithm Optimization  
* Cache Optimization  
* Thread Optimization  
* Memory Optimization  
* CPU Optimization

## **Inputs**

* Test Results

## **Outputs**

* Optimization Report  
* Benchmark Results

---

# **Phase 14 — Documentation & Project Closure**

## **Objective**

Prepare the project for evaluation and future maintenance.

## **Activities**

* SRS  
* User Manual  
* Technical Documentation  
* Installation Guide  
* Project Report  
* Presentation Preparation  
* Final Review

## **Inputs**

* Completed Project

## **Outputs**

* Complete Project Documentation  
* Final Deliverables

---

# **4\. Phase Dependencies**

| Phase | Depends On |
| ----- | ----- |
| Requirement Analysis | None |
| Architecture Design | Requirement Analysis |
| Technology Selection | Architecture Design |
| Database Design | Technology Selection |
| API Design | Database Design |
| Class Design | API Design |
| Algorithm & DSA Design | Class Design |
| OS & Concurrency Design | Algorithm Design |
| Security Design | API \+ Database Design |
| UI Design | API Design |
| Implementation | All Design Phases |
| Testing | Implementation |
| Optimization | Testing |
| Documentation | Entire Project |

---

# **5\. Deliverable Flow**

Requirements  
        │  
        ▼  
Architecture  
        │  
        ▼  
Technology Stack  
        │  
        ▼  
Database Design  
        │  
        ▼  
API Design  
        │  
        ▼  
Class Design  
        │  
        ▼  
Algorithms  
        │  
        ▼  
Concurrency  
        │  
        ▼  
Security  
        │  
        ▼  
UI  
        │  
        ▼  
Implementation  
        │  
        ▼  
Testing  
        │  
        ▼  
Optimization  
        │  
        ▼  
Documentation  
---

# **6\. Governance Documents**

Throughout the lifecycle, the following documents guide development:

| Document | Purpose |
| ----- | ----- |
| Design Philosophy | Governs engineering principles and decision-making |
| Project Development Lifecycle | Defines the engineering process |
| Architecture Decision Points (ADPs) | Records major architectural decisions |
| Engineering Decision Register (EDR) | Records implementation-level engineering decisions |
| Requirement Traceability Matrix (RTM) | Ensures complete traceability from requirements to implementation |

---

# **7\. Success Criteria**

The Project Development Lifecycle is considered successfully executed when:

* Every phase produces its defined deliverables.  
* Every engineering decision is justified and documented.  
* Every requirement is traceable through design and implementation.  
* All project KPIs are addressed through measurable engineering solutions.  
* The final system demonstrates the required core Computer Science subjects in a natural and integrated manner.

# Architecture Decision Points (ADP)

# **Architecture Decision Points (ADP)**

## **Online Examination Platform**

### **Version 1.0**

---

# **Purpose**

Architecture Decision Points (ADPs) document the major architectural decisions that govern the structure, organization, communication, ownership, and behavior of the Online Examination Platform.

These decisions establish the architectural foundation of the system and ensure that all subsequent design and implementation activities remain consistent with the Design Philosophy and Project Development Lifecycle.

ADPs are intended to remain stable throughout the project lifecycle and are independent of implementation technologies wherever possible.

---

# **Standard ADP Template**

Every ADP will follow the same structure.

| Section | Purpose |
| ----- | ----- |
| ADP ID | Unique identifier |
| Title | Architectural decision |
| Status | Proposed / Approved / Superseded |
| Context | Background requiring the decision |
| Problem Statement | Architecture problem being solved |
| Alternatives Considered | Other architectural options |
| Decision | Final architectural decision |
| Engineering Rationale | Why this architecture was selected |
| Positive Consequences | Benefits |
| Trade-offs | Known limitations |
| Related Design Principles | Links to Design Philosophy |
| Related KPIs | KPIs supported |
| Related EDRs | Engineering decisions derived later |

---

# **ADP Roadmap**

I recommend freezing the following ADP list.

| ADP | Title | Status |
| ----- | ----- | ----- |
| ADP-001 | Overall System Architecture | Pending |
| ADP-002 | Functional Module Architecture | Pending |
| ADP-003 | Layered Software Architecture | Pending |
| ADP-004 | Module Communication Architecture | Pending |
| ADP-005 | Domain Architecture & Bounded Contexts | Pending |
| ADP-006 | Module Ownership & Data Ownership | Pending |
| ADP-007 | Persistence Architecture | Pending |
| ADP-008 | Security Architecture | Pending |
| ADP-009 | Concurrency Architecture | Pending |
| ADP-010 | Deployment Architecture | Pending |

Notice something.

We reduced them to **10 architectural decisions**.

Everything else belongs in EDRs.

This keeps architecture clean.

---

# **ADP-001 — Overall System Architecture**

## **Status**

**Approved**

---

## **Context**

The Online Examination Platform consists of multiple functional modules including user management, examination management, question management, examination runtime, evaluation, reporting, monitoring, notifications, audit logging, and platform administration.

The system requires an architecture that supports clear separation of responsibilities, maintainability, scalability within the project scope, and integration of multiple Computer Science concepts while remaining suitable for a single deployable application.

---

## **Problem Statement**

Which overall software architecture should be adopted to organize the Online Examination Platform while satisfying the project's functional requirements, engineering objectives, KPIs, and expected outcomes?

---

## **Alternatives Considered**

### **Alternative 1 — Traditional Monolithic Architecture**

**Advantages**

* Simple implementation  
* Easy deployment  
* Low infrastructure requirements

**Disadvantages**

* High coupling  
* Poor modularity  
* Difficult maintenance  
* Limited scalability of codebase

---

### **Alternative 2 — Microservices Architecture**

**Advantages**

* Independent services  
* Independent deployment  
* High scalability

**Disadvantages**

* Significant operational complexity  
* Distributed communication  
* Increased deployment overhead  
* Beyond the scope of the project  
* Reduces focus on core engineering concepts

---

### **Alternative 3 — Service-Oriented Architecture (SOA)**

**Advantages**

* Good service separation  
* Reusable business services

**Disadvantages**

* Additional infrastructure complexity  
* Unnecessary for the project scope

---

### **Alternative 4 — Layered Modular Monolith**

**Advantages**

* High cohesion  
* Low coupling  
* Clear module boundaries  
* Single deployment unit  
* Simpler testing  
* Easier maintenance  
* Supports modular engineering  
* Excellent demonstration of Software Engineering principles

**Disadvantages**

* Requires disciplined module boundaries  
* Modules cannot be independently deployed

---

## **Decision**

The Online Examination Platform shall adopt a **Layered Modular Monolith Architecture**.

The system shall be deployed as a single application while internally organized into cohesive, independent business modules with clearly defined responsibilities and communication boundaries.

---

## **Engineering Rationale**

The Layered Modular Monolith architecture provides the best balance between software engineering quality and project complexity.

This architecture:

* Separates business capabilities into independent modules.  
* Promotes high cohesion and low coupling.  
* Simplifies testing and debugging.  
* Supports maintainable and extensible software.  
* Demonstrates Software Engineering principles explicitly.  
* Avoids unnecessary distributed-system complexity.  
* Aligns with the project's KPIs related to maintainability, integration, reliability, and code quality.  
* Provides sufficient scalability for the expected workload while keeping implementation manageable.

Unlike traditional monolithic systems, the architecture enforces clear module boundaries and responsibility ownership. Unlike microservices, it avoids unnecessary infrastructure complexity that would not contribute meaningfully to the educational objectives of the project.

---

## **Architectural Characteristics**

The architecture shall satisfy the following characteristics:

* Single deployable application  
* Modular business organization  
* Layered internal structure  
* Explicit module ownership  
* Clear dependency direction  
* Centralized configuration  
* Shared relational database with logical ownership  
* REST-based client interaction  
* Stateless business services with managed server-side sessions  
* Separation between presentation, business, and persistence concerns

---

## **Positive Consequences**

* Improved maintainability  
* Reduced coupling  
* Better code organization  
* Easier debugging  
* Simplified deployment  
* Improved testability  
* Better scalability of the codebase  
* Strong demonstration of Software Engineering concepts

---

## **Trade-offs**

* Independent module deployment is not supported.  
* Strict architectural discipline is required to prevent modules from becoming tightly coupled.  
* All modules share a common deployment lifecycle.

---

## **Related Design Principles**

* Principle 1 – Integration of Core Computer Science Subjects  
* Principle 4 – Functional Architecture Over Team Organization  
* Principle 5 – Module Merging Requires Technical Justification  
* Principle 7 – KPIs Drive the Architecture  
* Principle 10 – No Accidental Decisions  
* Principle 11 – Engineering Over Convenience

---

## **Related KPIs**

This decision directly supports:

* Maintainability  
* Integration  
* Reliability  
* Response Time  
* Scalability  
* Code Quality

---

## **Related EDRs**

This architectural decision is implemented through:

* Repository Pattern  
* Layered Package Organization  
* Dependency Injection (where applicable)  
* Service Layer  
* Controller Layer  
* Modular Project Structure

*(The specific implementation details will be documented in the Engineering Decision Register.)*

---

## **Architectural View**

                   Online Examination Platform  
────────────────────────────────────────────────────────

        Layered Modular Monolith Architecture

────────────────────────────────────────────────────────

Presentation Layer  
        │  
        ▼  
Application Layer  
        │  
        ▼  
Domain / Business Modules  
        │  
        ▼  
Persistence Layer  
        │  
        ▼  
Shared Relational Database  
---

# **Review**

I consider **ADP-001** to be **frozen**.

It is:

* Technology-independent.  
* Stable.  
* Traceable to the Design Philosophy.  
* Aligned with your project KPIs.  
* Suitable for inclusion in the final report and SRS.

# **Architecture Decision Point (ADP-002)**

# **Functional Module Architecture**

**Status:** Approved

---

# **1\. Context**

The Online Examination Platform implements a wide range of business capabilities, including user management, examination administration, question management, online examination execution, evaluation, reporting, monitoring, notifications, security, and system administration.

If these responsibilities are implemented without clear functional boundaries, the system will become tightly coupled, difficult to maintain, and challenging to extend. A modular decomposition is therefore required to ensure that every functional responsibility is owned by exactly one module.

---

# **2\. Problem Statement**

How should the functional responsibilities of the Online Examination Platform be organized into software modules to maximize cohesion, minimize coupling, and clearly demonstrate Software Engineering principles while satisfying the project requirements, KPIs, and expected outcomes?

---

# **3\. Alternatives Considered**

## **Alternative 1 – Layer-Based Modules**

Example:

* Authentication Module  
* Database Module  
* UI Module

### **Advantages**

* Simple implementation.

### **Disadvantages**

* Business logic becomes scattered.  
* High coupling between unrelated features.  
* Poor maintainability.

**Decision:** Rejected.

---

## **Alternative 2 – Team-Based Modules**

Example:

* Team A Modules  
* Team B Modules  
* Team C Modules

### **Advantages**

* Easy work distribution.

### **Disadvantages**

* Software architecture becomes dependent on organizational structure.  
* Violates functional cohesion.  
* Difficult to maintain after development.

**Decision:** Rejected.

---

## **Alternative 3 – Fine-Grained Micro Modules**

30–40 independent modules.

### **Advantages**

* Maximum separation.

### **Disadvantages**

* Excessive complexity.  
* Increased communication overhead.  
* Difficult integration.  
* Unnecessary for project scope.

**Decision:** Rejected.

---

## **Alternative 4 – Functional Business Modules**

Modules represent complete business capabilities.

### **Advantages**

* High cohesion.  
* Low coupling.  
* Clear ownership.  
* Easier maintenance.  
* Easier testing.  
* Naturally maps to project requirements.  
* Strong Software Engineering demonstration.

**Decision:** Selected.

---

# **4\. Decision**

The Online Examination Platform shall be organized into **14 cohesive functional modules**, where each module owns a complete business capability and is responsible for its own business rules, data, services, and interfaces.

Each module shall have a clearly defined responsibility, ownership boundary, and interaction contract.

---

# **5\. Functional Module Architecture**

The system shall consist of the following modules.

| Module | Primary Responsibility |
| ----- | ----- |
| Identity & Access Management | Authentication, authorization, users, roles, permissions |
| Student & Faculty Management | Academic users, profiles, eligibility, assignments |
| Academic Structure Management | Departments, subjects, semesters, academic organization |
| Examination Administration | Exam creation, scheduling, registration, configuration |
| Question Bank Management | Question repository, options, blueprint, randomization |
| Examination Runtime | Live examination execution, submissions, responses |
| Evaluation & Result Management | Evaluation, grading, results, score computation |
| Reporting & Analytics | Reports, dashboards, analytics, statistics |
| Notification Management | Notifications, announcements, communication |
| Audit & Activity Logging | Audit trails, activity history, compliance |
| Secure Session Management | Session lifecycle, timeout, concurrent session control |
| System Monitoring & Health | Monitoring, metrics, alerts, diagnostics |
| Backup & Recovery | Backup scheduling, restore operations |
| System Configuration | Global configuration, master settings, application preferences |

---

# **6\. Module Responsibilities**

Each module shall:

* Own a single business capability.  
* Maintain high internal cohesion.  
* Expose well-defined interfaces.  
* Hide internal implementation details.  
* Own its business rules.  
* Own its data.  
* Be independently testable.  
* Avoid direct dependency on unrelated modules.

---

# **7\. Module Boundaries**

The following architectural rules shall apply:

### **Rule 1**

Every business responsibility belongs to exactly one module.

---

### **Rule 2**

A module shall never duplicate another module's responsibility.

---

### **Rule 3**

Business logic shall not be shared through direct database access.

Communication occurs only through defined service interfaces.

---

### **Rule 4**

Each module owns its internal implementation.

Other modules interact only through published interfaces.

---

### **Rule 5**

Modules shall remain implementation-independent.

Changes within one module should have minimal impact on others.

---

# **8\. Architectural Characteristics**

The Functional Module Architecture shall exhibit:

* High Cohesion  
* Low Coupling  
* Separation of Concerns  
* Single Responsibility  
* Clear Ownership  
* Encapsulation  
* Modularity  
* Testability  
* Extensibility

---

# **9\. Module Dependency Philosophy**

Dependencies shall flow only toward required business capabilities.

Circular dependencies are prohibited.

Example:

Student Module  
        │  
        ▼  
Examination Administration  
        │  
        ▼  
Examination Runtime  
        │  
        ▼  
Evaluation  
        │  
        ▼  
Reporting

Identity & Access Management acts as a shared foundational service for authenticated access but does not own business workflows.

---

# **10\. Architectural View**

                Online Examination Platform

┌─────────────────────────────────────────────────────┐  
│          Identity & Access Management               │  
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐  
│ Student & Faculty Management                        │  
├─────────────────────────────────────────────────────┤  
│ Academic Structure Management                       │  
├─────────────────────────────────────────────────────┤  
│ Examination Administration                          │  
├─────────────────────────────────────────────────────┤  
│ Question Bank Management                            │  
├─────────────────────────────────────────────────────┤  
│ Examination Runtime                                 │  
├─────────────────────────────────────────────────────┤  
│ Evaluation & Result Management                      │  
├─────────────────────────────────────────────────────┤  
│ Reporting & Analytics                               │  
└─────────────────────────────────────────────────────┘

──────────────────────────────────────────────────────

Cross-Cutting Services

• Notification Management  
• Audit & Activity Logging  
• Secure Session Management  
• System Monitoring & Health  
• Backup & Recovery  
• System Configuration  
---

# **11\. Positive Consequences**

This decision provides:

* Strong functional cohesion.  
* Clear ownership of business capabilities.  
* Simplified maintenance.  
* Easier module testing.  
* Better scalability of the codebase.  
* Reduced coupling.  
* Improved traceability.  
* Better mapping between requirements and implementation.

---

# **12\. Trade-offs**

* Requires careful definition of module boundaries.  
* Cross-module interactions must be explicitly managed.  
* Developers must respect ownership rules to prevent architectural erosion.

---

# **13\. Related Design Principles**

This decision implements:

* Principle 1 – Integration of Core Computer Science Subjects  
* Principle 4 – Functional Architecture Over Team Organization  
* Principle 5 – Module Merging Requires Technical Justification  
* Principle 7 – KPIs Drive the Architecture  
* Principle 10 – No Accidental Decisions  
* Principle 11 – Engineering Over Convenience

---

# **14\. Related KPIs**

This architectural decision directly supports:

* Maintainability  
* Integration  
* Reliability  
* Scalability  
* Code Quality  
* Functional Completeness

---

# **15\. Related Engineering Decisions**

This ADP is realized through engineering decisions such as:

* Repository Pattern  
* Service Layer Pattern  
* Feature-Based Package Structure  
* Module-Level Testing Strategy  
* API Boundary Enforcement

---

# **16\. Impact on Future Design**

This ADP governs the organization of:

* Database ownership  
* API ownership  
* Class ownership  
* Repository ownership  
* Test ownership  
* Package structure  
* Source code organization  
* Requirement Traceability Matrix

Every subsequent design artifact must respect these module boundaries.

---

# **Architecture Decision Point (ADP-003)**

# **Layered Software Architecture**

**Status:** Approved

---

# **1\. Context**

The Online Examination Platform consists of multiple business modules that perform different responsibilities, including presentation, request handling, business processing, data access, and infrastructure services.

Without a well-defined layering strategy, business logic can become mixed with user interface code, database access, and infrastructure concerns, resulting in tight coupling, duplicated logic, poor maintainability, and reduced testability.

A layered architecture is therefore required to separate responsibilities, control dependencies, and provide a clear implementation structure.

---

# **2\. Problem Statement**

How should the internal structure of the Online Examination Platform be organized to ensure separation of concerns, maintainability, testability, and controlled dependencies while supporting the functional module architecture defined in ADP-002?

---

# **3\. Alternatives Considered**

## **Alternative 1 — Two-Tier Architecture**

UI  
↓

Database

### **Advantages**

* Very simple.

### **Disadvantages**

* Business logic scattered.  
* Poor maintainability.  
* Difficult testing.  
* Tight coupling.

**Decision:** Rejected.

---

## **Alternative 2 — Three-Tier Architecture**

Presentation  
↓

Business

↓

Database

### **Advantages**

* Better separation.

### **Disadvantages**

* Infrastructure concerns become mixed with business logic.  
* Persistence responsibilities are not clearly isolated.

**Decision:** Rejected.

---

## **Alternative 3 — Layered Software Architecture**

Separate layers for presentation, application coordination, business logic, persistence, and infrastructure.

### **Advantages**

* High cohesion.  
* Low coupling.  
* Clear responsibilities.  
* Easier testing.  
* Easier maintenance.  
* Strong Software Engineering demonstration.

**Decision:** Selected.

---

# **4\. Decision**

The Online Examination Platform shall adopt a **five-layer software architecture** in which each layer has clearly defined responsibilities and communicates only with adjacent lower layers.

Business rules shall remain isolated from presentation, persistence, and infrastructure concerns.

---

# **5\. Layer Definitions**

The system shall consist of five logical layers.

| Layer | Responsibility |
| ----- | ----- |
| Presentation Layer | User interface, HTTP requests, responses, session interaction |
| Application Layer | Request orchestration, workflow coordination, validation, transactions |
| Domain Layer | Core business rules and business services |
| Persistence Layer | Data access, repositories, database interaction |
| Infrastructure Layer | Logging, scheduling, caching, monitoring, configuration, external services |

---

# **6\. Layer Responsibilities**

---

## **Presentation Layer**

Responsible for:

* User Interface  
* Request Handling  
* Session Validation  
* Input Collection  
* Response Rendering

It **must not** contain:

* Business Rules  
* Database Logic  
* Complex Validation

---

## **Application Layer**

Responsible for:

* Coordinating business operations  
* Managing application workflows  
* Transaction boundaries  
* Invoking business services  
* Coordinating multiple modules

It acts as the bridge between presentation and domain logic.

---

## **Domain Layer**

This is the heart of the system.

Responsible for:

* Business Rules  
* Examination Logic  
* Evaluation Logic  
* Security Policies  
* Validation Rules  
* Domain Services

The Domain Layer shall remain independent of presentation frameworks, databases, and infrastructure technologies.

---

## **Persistence Layer**

Responsible for:

* Repository Interfaces  
* Repository Implementations  
* Query Execution  
* Transaction Support  
* Database Mapping

The Persistence Layer shall not contain business rules.

---

## **Infrastructure Layer**

Responsible for:

* Logging  
* Scheduling  
* File Storage  
* Email  
* Notifications  
* Monitoring  
* Configuration  
* Backup Support  
* Caching

Infrastructure provides technical services to the application but does not define business behavior.

---

# **7\. Dependency Rules**

Dependencies shall always point downward.

Presentation  
        │  
        ▼  
Application  
        │  
        ▼  
Domain  
        │  
        ▼  
Persistence  
        │  
        ▼  
Infrastructure

Reverse dependencies are prohibited.

---

# **8\. Architectural Constraints**

### **Constraint 1**

Presentation shall never access the database directly.

---

### **Constraint 2**

Business rules shall never depend on UI components.

---

### **Constraint 3**

Repositories shall not contain business logic.

---

### **Constraint 4**

Infrastructure services shall remain reusable and independent of business modules.

---

### **Constraint 5**

Cross-layer communication shall occur only through well-defined interfaces.

---

# **9\. Architectural Characteristics**

The Layered Architecture provides:

* Separation of Concerns  
* High Cohesion  
* Low Coupling  
* Encapsulation  
* Testability  
* Maintainability  
* Extensibility  
* Reusability

---

# **10\. Architectural View**

───────────────────────────────────────────  
        Presentation Layer  
───────────────────────────────────────────  
        Controllers  
        Views  
        Session Handling

                │  
                ▼

───────────────────────────────────────────  
        Application Layer  
───────────────────────────────────────────  
Application Services  
Workflow Coordination  
Transaction Management

                │  
                ▼

───────────────────────────────────────────  
          Domain Layer  
───────────────────────────────────────────  
Business Services  
Business Rules  
Validation  
Domain Models

                │  
                ▼

───────────────────────────────────────────  
        Persistence Layer  
───────────────────────────────────────────  
Repositories  
Data Access  
Database Mapping

                │  
                ▼

───────────────────────────────────────────  
      Infrastructure Layer  
───────────────────────────────────────────  
Logging  
Scheduling  
Caching  
Monitoring  
Configuration  
---

# **11\. Core Computer Science Subject Demonstration**

| Subject | Architectural Contribution |
| ----- | ----- |
| Software Engineering | Separation of concerns, layered architecture, modular design |
| Object-Oriented Programming | Encapsulation, abstraction, interface-based design |
| Database Management Systems | Persistence isolation, repository abstraction |
| Computer Networks | HTTP request processing, session management, REST communication |
| Operating Systems | Layer supporting concurrency, scheduling, resource management |
| Cyber Security | Security enforcement points across presentation, application, and domain layers |
| Web Technologies | User interaction confined to the presentation layer |

---

# **12\. Positive Consequences**

* Clear separation of responsibilities.  
* Simplified maintenance.  
* Improved unit testing.  
* Easier debugging.  
* Reduced coupling.  
* Better scalability of the codebase.  
* Cleaner implementation.  
* Better architectural consistency.

---

# **13\. Trade-offs**

* Additional layers introduce more classes.  
* Developers must respect dependency rules.  
* Slight increase in implementation complexity compared to simpler architectures.

---

# **14\. Related Design Principles**

* Principle 1 – Integration of Core Computer Science Subjects  
* Principle 2 – Every Design Decision Must Answer Two Questions  
* Principle 7 – KPIs Drive the Architecture  
* Principle 8 – Deliverables Must Be a By-product of the Architecture  
* Principle 10 – No Accidental Decisions  
* Principle 11 – Engineering Over Convenience

---

# **15\. Related KPIs**

This decision directly contributes to:

* Maintainability  
* Reliability  
* Code Quality  
* Integration  
* Testability  
* Scalability

---

# **16\. Related Engineering Decisions**

This ADP will later be implemented through:

* Service Layer Pattern  
* Repository Pattern  
* Dependency Injection  
* Application Services  
* Modular Package Organization  
* Transaction Management Strategy

---

# **17\. Impact on Future Design**

This ADP governs the organization of:

* Project directory structure  
* Package organization  
* Class hierarchy  
* Repository placement  
* API implementation  
* Database interaction  
* Unit testing strategy  
* Integration testing

Every implementation artifact must respect these layer boundaries.

# **Architecture Decision Point (ADP-004)**

# **Module Communication Architecture**

**Status:** Approved

---

# **1\. Context**

The Online Examination Platform is organized into multiple independent functional modules as defined in ADP-002. Although these modules collaborate to deliver complete business workflows, unrestricted communication between them leads to tight coupling, duplicated logic, circular dependencies, and reduced maintainability.

A communication architecture is therefore required to regulate how modules interact while preserving module independence and architectural integrity.

---

# **2\. Problem Statement**

How shall software modules communicate with one another while maintaining high cohesion, low coupling, clear ownership, and architectural consistency throughout the system?

---

# **3\. Alternatives Considered**

## **Alternative 1 — Direct Class-to-Class Communication**

Module A  
     │  
     ▼  
Module B Internal Classes

### **Advantages**

* Simple implementation.  
* Minimal code.

### **Disadvantages**

* Tight coupling.  
* Difficult testing.  
* Breaks encapsulation.  
* Changes propagate across modules.

**Decision:** Rejected.

---

## **Alternative 2 — Shared Database Communication**

Module A

↓

Database

↑

Module B

### **Advantages**

* Easy data access.

### **Disadvantages**

* No ownership.  
* Business rules bypassed.  
* High coupling.  
* Poor maintainability.  
* Difficult auditing.

**Decision:** Rejected.

---

## **Alternative 3 — Service Interface Communication**

Each module exposes only its public services.

Other modules communicate only through these services.

### **Advantages**

* Loose coupling.  
* Clear ownership.  
* Easier testing.  
* Better maintainability.  
* Supports future architectural evolution.

**Decision:** Selected.

---

# **4\. Decision**

Modules shall communicate exclusively through well-defined service interfaces.

A module shall never directly manipulate another module's internal implementation, repositories, or database objects.

Business workflows involving multiple modules shall be coordinated through the Application Layer.

---

# **5\. Communication Model**

Presentation Layer  
        │  
        ▼  
Application Service  
        │  
        ▼  
Business Module A  
        │  
        ▼  
Business Module B  
        │  
        ▼  
Business Module C

Notice

The communication is

**business driven**,

not

database driven.

---

# **6\. Communication Principles**

## **Principle 1 — Interface-Based Communication**

Modules communicate only through published service interfaces.

Internal classes remain private.

---

## **Principle 2 — No Direct Database Access**

A module shall never access another module's database tables directly.

Data ownership remains with the owning module.

---

## **Principle 3 — Business Operations Cross Modules**

Communication represents business workflows.

Example

Student Starts Examination

↓

Identity Module

↓

Examination Module

↓

Runtime Module

↓

Audit Module

Not

random method calls.

---

## **Principle 4 — Infrastructure Services Are Shared**

Infrastructure modules

Logging

Monitoring

Notification

Backup

may be invoked by multiple modules.

However

they do not own business rules.

---

## **Principle 5 — Circular Dependencies Are Prohibited**

Example

Wrong

Student Module

↓

Examination Module

↓

Student Module

Correct

Student Module

↓

Application Layer

↓

Examination Module  
---

# **7\. Communication Categories**

The system supports four categories of communication.

| Category | Description |
| ----- | ----- |
| Presentation → Application | User requests |
| Application → Business Module | Workflow orchestration |
| Module → Module | Business collaboration through service interfaces |
| Module → Infrastructure | Logging, monitoring, notifications, scheduling |

---

# **8\. Cross-Module Workflow Example**

Example

Student submits an examination.

Student

↓

Presentation Layer

↓

Exam Runtime Service

↓

Evaluation Service

↓

Result Service

↓

Notification Service

↓

Audit Service

↓

Response Returned

Notice

Every module performs

its own responsibility.

No module owns

the entire workflow.

---

# **9\. Architectural Rules**

### **Rule 1**

Modules shall communicate only through public services.

---

### **Rule 2**

Modules shall never directly instantiate another module's internal classes.

---

### **Rule 3**

Business modules shall never directly access another module's repositories.

---

### **Rule 4**

Cross-module workflows shall be coordinated by the Application Layer.

---

### **Rule 5**

Modules shall not expose internal implementation details.

---

### **Rule 6**

Infrastructure modules shall remain reusable and independent.

---

### **Rule 7**

All communication shall preserve module ownership boundaries.

---

# **10\. Architectural View**

                Presentation Layer  
                         │  
                         ▼  
               Application Layer  
                         │  
────────────────────────────────────────────

Identity Module

Academic Module

Examination Module

Question Module

Runtime Module

Evaluation Module

Reporting Module

────────────────────────────────────────────

Infrastructure Services

Logging

Notification

Monitoring

Scheduling

Backup

The Application Layer coordinates communication.

Business modules collaborate without violating ownership.

---

# **11\. Core Computer Science Subject Demonstration**

| Subject | Contribution |
| ----- | ----- |
| Software Engineering | Interface-based communication, modularity, dependency management |
| Object-Oriented Programming | Abstraction, encapsulation, interface segregation |
| Computer Networks | Request–response architecture, service interaction |
| Database Management Systems | Data ownership boundaries prevent integrity violations |
| Operating Systems | Controlled coordination between concurrent services |
| Cyber Security | Communication passes through centralized authorization points |

---

# **12\. Positive Consequences**

* Loose coupling.  
* High cohesion.  
* Clear ownership.  
* Easier testing.  
* Better maintainability.  
* Controlled dependencies.  
* Improved scalability of the codebase.  
* Reduced architectural erosion.

---

# **13\. Trade-offs**

* More service interfaces must be defined.  
* Slight increase in application layer complexity.  
* Developers must follow communication rules consistently.

---

# **14\. Related Design Principles**

* Principle 2 – Every Design Decision Must Answer Two Questions  
* Principle 4 – Functional Architecture Over Team Organization  
* Principle 5 – Module Merging Requires Technical Justification  
* Principle 7 – KPIs Drive the Architecture  
* Principle 10 – No Accidental Decisions  
* Principle 11 – Engineering Over Convenience

---

# **15\. Related KPIs**

This decision directly supports:

* Maintainability  
* Integration  
* Reliability  
* Security  
* Scalability  
* Code Quality

---

# **16\. Related Engineering Decisions**

This ADP is implemented through:

* Service Layer Pattern  
* Repository Pattern  
* Dependency Injection  
* Application Service Coordination  
* REST Controller Design

---

# **17\. Impact on Future Design**

This ADP governs:

* API ownership  
* Service interfaces  
* Cross-module workflows  
* Repository access rules  
* Transaction boundaries  
* Integration testing  
* Future extensibility

# **Architecture Decision Point (ADP-005)**

# **Domain Architecture & Bounded Contexts**

**Status:** Approved

---

# **1\. Context**

The Online Examination Platform consists of multiple business capabilities that collectively support the lifecycle of an online examination system. These capabilities manage different aspects of the application, including identity management, academic administration, examination management, runtime execution, evaluation, reporting, and operational support.

Without explicit domain boundaries, business logic becomes scattered across the system, resulting in duplicated responsibilities, inconsistent business rules, and tightly coupled modules.

A domain architecture is therefore required to establish clear business boundaries and ensure that each domain owns a cohesive and well-defined area of responsibility.

---

# **2\. Problem Statement**

How should the business capabilities of the Online Examination Platform be organized into independent domains that maximize cohesion, minimize coupling, preserve ownership, and support future maintainability?

---

# **3\. Alternatives Considered**

## **Alternative 1 – Single Business Domain**

All business logic exists inside one large application.

### **Advantages**

* Simple structure.

### **Disadvantages**

* Extremely high coupling.  
* Poor maintainability.  
* Difficult ownership.  
* Difficult scalability.

**Decision:** Rejected.

---

## **Alternative 2 – Technology-Based Domains**

Examples:

* Database Domain  
* Authentication Domain  
* UI Domain

### **Advantages**

* Simple organization.

### **Disadvantages**

* Does not reflect business processes.  
* Violates separation of business concerns.  
* Difficult requirement traceability.

**Decision:** Rejected.

---

## **Alternative 3 – Business-Oriented Bounded Contexts**

Business capabilities are grouped into independent domains based on functional ownership.

### **Advantages**

* High cohesion.  
* Clear ownership.  
* Better maintainability.  
* Easier testing.  
* Excellent Software Engineering demonstration.

**Decision:** Selected.

---

# **4\. Decision**

The Online Examination Platform shall be organized into **business-oriented bounded contexts**, where each domain owns a complete business capability, including its business rules, services, data, interfaces, and validation logic.

Each domain shall remain independent while collaborating with other domains through well-defined service interfaces.

---

# **5\. Domain Architecture**

The system shall consist of the following business domains.

| Domain | Business Responsibility |
| ----- | ----- |
| Identity & Access | Authentication, authorization, users, roles, permissions |
| Academic Management | Students, faculty, departments, semesters, subjects |
| Examination Management | Examination planning, scheduling, registration, configuration |
| Question Management | Question bank, options, blueprints, randomization |
| Examination Runtime | Live examination sessions, submissions, responses |
| Evaluation & Results | Evaluation, grading, marks, results |
| Reporting & Analytics | Reports, dashboards, analytics |
| Platform Services | Notifications, audit logging, monitoring, backup, configuration |

---

# **6\. Domain Responsibilities**

Each domain owns:

* Business Rules  
* Business Services  
* Validation Rules  
* Data Model  
* Repository Interfaces  
* Public Service Interfaces  
* Business Workflows

Each domain does **not** own:

* Another domain's business rules.  
* Another domain's database tables.  
* Another domain's validation logic.

---

# **7\. Domain Relationships**

The high-level business flow follows the natural lifecycle of an examination.

Identity & Access

        │

        ▼

Academic Management

        │

        ▼

Examination Management

        │

        ▼

Question Management

        │

        ▼

Examination Runtime

        │

        ▼

Evaluation & Results

        │

        ▼

Reporting & Analytics

Platform Services operate across all domains without owning business processes.

---

# **8\. Domain Boundaries**

Each domain represents a **bounded context**.

Within a bounded context:

* Terminology is consistent.  
* Business rules are consistent.  
* Data ownership is clear.  
* Internal implementation remains private.

Outside the bounded context:

* Communication occurs only through published interfaces.  
* Internal implementation details are hidden.

---

# **9\. Architectural Rules**

### **Rule 1**

Every business concept belongs to exactly one domain.

---

### **Rule 2**

Every business rule is implemented only within its owning domain.

---

### **Rule 3**

Every domain owns its own services.

---

### **Rule 4**

Every domain owns its own data.

---

### **Rule 5**

Business terminology shall remain consistent within each domain.

---

### **Rule 6**

Domains shall never duplicate responsibilities.

---

### **Rule 7**

Cross-domain workflows shall preserve ownership boundaries.

---

# **10\. Domain Collaboration**

Domains collaborate only when necessary.

Example

Student Starts Examination

↓

Identity Domain

↓

Examination Domain

↓

Runtime Domain

↓

Evaluation Domain

↓

Reporting Domain

Each domain performs only its own responsibility.

---

# **11\. Architectural View**

                   Online Examination Platform

                    Business Domain Architecture

┌────────────────────────────────────────────────────┐

│ Identity & Access                                  │

└────────────────────────────────────────────────────┘

                     │

                     ▼

┌────────────────────────────────────────────────────┐

│ Academic Management                                │

└────────────────────────────────────────────────────┘

                     │

                     ▼

┌────────────────────────────────────────────────────┐

│ Examination Management                             │

└────────────────────────────────────────────────────┘

                     │

                     ▼

┌────────────────────────────────────────────────────┐

│ Question Management                                │

└────────────────────────────────────────────────────┘

                     │

                     ▼

┌────────────────────────────────────────────────────┐

│ Examination Runtime                                │

└────────────────────────────────────────────────────┘

                     │

                     ▼

┌────────────────────────────────────────────────────┐

│ Evaluation & Results                               │

└────────────────────────────────────────────────────┘

                     │

                     ▼

┌────────────────────────────────────────────────────┐

│ Reporting & Analytics                              │

└────────────────────────────────────────────────────┘

──────────────────────────────────────────────────────

Platform Services

• Notifications

• Audit Logging

• Monitoring

• Backup & Recovery

• Configuration

---

# **12\. Core Computer Science Subject Demonstration**

| Subject | Architectural Contribution |
| ----- | ----- |
| Software Engineering | Domain decomposition, bounded contexts, modularity |
| Object-Oriented Programming | Encapsulation of business responsibilities |
| Database Management Systems | Domain-driven data ownership |
| Computer Networks | Service-oriented domain communication |
| Operating Systems | Independent domain execution and coordination |
| Cyber Security | Domain-specific security enforcement |
| Web Technologies | Clear mapping between UI and business domains |

---

# **13\. Positive Consequences**

* High business cohesion.  
* Clear ownership.  
* Easier maintenance.  
* Better scalability of the codebase.  
* Simplified testing.  
* Improved traceability.  
* Better requirement mapping.  
* Reduced coupling.

---

# **14\. Trade-offs**

* Requires careful identification of domain boundaries.  
* Cross-domain workflows require coordination.  
* Developers must understand ownership responsibilities.

---

# **15\. Related Design Principles**

* Principle 1 – Integration of Core Computer Science Subjects  
* Principle 4 – Functional Architecture Over Team Organization  
* Principle 5 – Module Merging Requires Technical Justification  
* Principle 7 – KPIs Drive the Architecture  
* Principle 10 – No Accidental Decisions  
* Principle 11 – Engineering Over Convenience

---

# **16\. Related KPIs**

This decision supports:

* Maintainability  
* Integration  
* Reliability  
* Scalability  
* Code Quality  
* Functional Completeness

---

# **17\. Related Engineering Decisions**

This ADP will be implemented through:

* Feature-based package organization  
* Service layer architecture  
* Repository ownership  
* API ownership  
* Database ownership  
* Domain-specific validation

---

# **18\. Impact on Future Design**

This ADP governs:

* Database schema organization  
* Repository ownership  
* API ownership  
* Class organization  
* Package structure  
* Transaction boundaries  
* Requirement Traceability Matrix  
* Testing strategy

Every future design artifact must preserve these domain boundaries.

# **Architecture Decision Point (ADP-006)**

# **Module Ownership & Data Ownership**

**Status:** Approved

---

# **1\. Context**

The Online Examination Platform is composed of multiple business domains that collaborate to deliver complete examination workflows. Each domain manages a specific business capability and requires ownership over its data, business rules, services, and interfaces.

Without clearly defined ownership, multiple modules may implement the same business logic, directly manipulate each other's data, or violate architectural boundaries, resulting in tight coupling, inconsistent behavior, and poor maintainability.

A formal ownership model is therefore required.

---

# **2\. Problem Statement**

How shall ownership of business rules, services, APIs, repositories, and data be assigned to ensure clear responsibility, preserve architectural integrity, and maintain consistency throughout the system?

---

# **3\. Alternatives Considered**

## **Alternative 1 – Shared Ownership**

Multiple modules may modify the same entities.

### **Advantages**

* Easy implementation.  
* Fewer service calls.

### **Disadvantages**

* Conflicting business rules.  
* Poor traceability.  
* High coupling.  
* Difficult debugging.

**Decision:** Rejected.

---

## **Alternative 2 – Database-Centric Ownership**

Ownership determined by database tables.

### **Advantages**

* Simple relational mapping.

### **Disadvantages**

* Business ownership becomes unclear.  
* Violates domain-driven design.  
* Encourages direct database coupling.

**Decision:** Rejected.

---

## **Alternative 3 – Domain Ownership**

Each business domain owns:

* Business rules  
* Services  
* APIs  
* Data  
* Validation  
* Repositories

Other domains interact only through public services.

### **Advantages**

* High cohesion.  
* Low coupling.  
* Clear traceability.  
* Excellent maintainability.

**Decision:** Selected.

---

# **4\. Decision**

Each business capability shall have **exactly one owning module**.

The owning module has exclusive authority to:

* Define business rules.  
* Modify business data.  
* Validate business constraints.  
* Publish service interfaces.  
* Expose APIs.  
* Manage repositories.

Other modules may **consume** these services but shall never bypass the ownership boundary.

---

# **5\. Ownership Principles**

### **Principle 1 — Single Ownership**

Every business entity belongs to one and only one module.

---

### **Principle 2 — Single Source of Truth**

Business rules shall exist only within the owning module.

---

### **Principle 3 — Data Ownership**

Only the owning module may perform create, update, or delete operations on its entities.

---

### **Principle 4 — Read Without Ownership**

Other modules may read information through public services when required but shall not modify it.

---

### **Principle 5 — Encapsulation**

Internal implementation details remain private to the owning module.

---

### **Principle 6 — Controlled Collaboration**

Cross-module business processes are coordinated through the Application Layer.

---

# **6\. Ownership Matrix**

## **Identity & Access Management**

| Owns | Does Not Own |
| ----- | ----- |
| Users | Students |
| Roles | Questions |
| Permissions | Results |
| Credentials | Subjects |
| Sessions | Examinations |

---

## **Academic Management**

| Owns | Does Not Own |
| ----- | ----- |
| Students | Users |
| Faculty | Questions |
| Departments | Results |
| Subjects | Sessions |
| Semesters | Audit Logs |

---

## **Examination Management**

| Owns | Does Not Own |
| ----- | ----- |
| Examinations | Students |
| Registration | Users |
| Scheduling | Results |
| Configuration | Notifications |

---

## **Question Management**

| Owns | Does Not Own |
| ----- | ----- |
| Questions | Students |
| Options | Sessions |
| Blueprints | Results |
| Difficulty | Users |
| Topics | Notifications |

---

## **Examination Runtime**

| Owns | Does Not Own |
| ----- | ----- |
| Exam Sessions | Questions |
| Responses | Subjects |
| Submissions | Roles |
| Runtime State | Departments |

---

## **Evaluation & Results**

| Owns | Does Not Own |
| ----- | ----- |
| Evaluation | Questions |
| Marks | Sessions |
| Grades | Users |
| Results | Departments |

---

## **Reporting & Analytics**

| Owns | Does Not Own |
| ----- | ----- |
| Reports | Business Data |
| Dashboards | Business Rules |
| Analytics | Transactions |

Reports consume business information but do not own it.

---

## **Platform Services**

Owns:

* Notifications  
* Audit Logs  
* Monitoring  
* Configuration  
* Backup  
* Health Metrics

These modules observe business activities but do not own business workflows.

---

# **7\. Ownership Hierarchy**

Business Requirement

        │

        ▼

Business Domain

        │

        ▼

Business Service

        │

        ▼

Repository

        │

        ▼

Database Tables

Ownership flows downward.

It never flows upward.

---

# **8\. Ownership Rules**

### **Rule 1**

Only the owning module may modify its business entities.

---

### **Rule 2**

Business validation occurs only inside the owning module.

---

### **Rule 3**

Repositories belong to their owning module.

---

### **Rule 4**

REST endpoints belong to the module that owns the business capability.

---

### **Rule 5**

Shared utility classes never contain business rules.

---

### **Rule 6**

Infrastructure services never own business data.

---

### **Rule 7**

Every entity in the database shall have one owning module.

---

# **9\. Cross-Domain Example**

Student submits an examination.

Identity

      │

      ▼

Runtime

      │

      ▼

Evaluation

      │

      ▼

Reporting

Ownership remains:

| Domain | Owns |
| ----- | ----- |
| Identity | Authentication |
| Runtime | Submission |
| Evaluation | Marks |
| Reporting | Analytics |

No domain performs another domain's responsibility.

---

# **10\. Architectural View**

                Business Ownership

Identity

│

├── Users

├── Roles

├── Sessions

Academic

│

├── Students

├── Faculty

├── Subjects

Examination

│

├── Exams

├── Registration

├── Scheduling

Question

│

├── Questions

├── Options

Runtime

│

├── Sessions

├── Responses

├── Submissions

Evaluation

│

├── Marks

├── Grades

├── Results

Reporting

│

├── Reports

├── Dashboards

Platform Services

│

├── Audit

├── Notifications

├── Monitoring

├── Backup

---

# **11\. Core Computer Science Subject Demonstration**

| Subject | Architectural Contribution |
| ----- | ----- |
| Software Engineering | Single Responsibility, ownership, modularity, separation of concerns |
| Object-Oriented Programming | Encapsulation, information hiding, interface ownership |
| Database Management Systems | Entity ownership, integrity, controlled updates |
| Computer Networks | API ownership and service contracts |
| Operating Systems | Controlled coordination between modules |
| Cyber Security | Authorization boundaries aligned with ownership |

---

# **12\. Positive Consequences**

* Clear responsibilities.  
* No duplicated business rules.  
* Reduced coupling.  
* Easier testing.  
* Better maintainability.  
* Better traceability.  
* Cleaner database design.  
* Simplified API ownership.

---

# **13\. Trade-offs**

* Cross-module operations require coordination.  
* Service interfaces must be carefully designed.  
* Developers must respect ownership rules.

---

# **14\. Related Design Principles**

* Principle 2 – Every Design Decision Must Answer Two Questions  
* Principle 4 – Functional Architecture Over Team Organization  
* Principle 5 – Module Merging Requires Technical Justification  
* Principle 7 – KPIs Drive the Architecture  
* Principle 10 – No Accidental Decisions  
* Principle 11 – Engineering Over Convenience

---

# **15\. Related KPIs**

This decision directly supports:

* Maintainability  
* Database Integrity  
* Reliability  
* Integration  
* Security  
* Code Quality

---

# **16\. Related Engineering Decisions**

This ADP is implemented through:

* Repository Pattern  
* Service Layer Pattern  
* Database Schema Ownership  
* REST API Ownership  
* Transaction Boundaries

---

# **17\. Impact on Future Design**

This ADP governs:

* Database table ownership.  
* Repository ownership.  
* API ownership.  
* Class ownership.  
* Service ownership.  
* Transaction ownership.  
* Test ownership.  
* Requirement Traceability Matrix.

Every entity, repository, API, and service created in later phases must be traceable to exactly one owning module.

# **Architecture Decision Point (ADP-007)**

# **Data & Persistence Architecture**

**Status:** Approved

---

# **1\. Context**

The Online Examination Platform manages persistent business information including users, examinations, questions, student responses, results, audit logs, and system configuration.

The persistence mechanism must provide reliable storage while preserving the architectural boundaries established in previous ADPs. Business logic must remain independent of database technologies and persistence implementations.

A dedicated persistence architecture is therefore required to separate business processing from data storage concerns.

---

# **2\. Problem Statement**

How shall persistent data be managed so that the system maintains data integrity, architectural independence, maintainability, and efficient database interaction without exposing persistence concerns to business modules?

---

# **3\. Alternatives Considered**

## **Alternative 1 – Direct Database Access**

Business services execute SQL directly.

### **Advantages**

* Simple implementation.  
* Minimal abstraction.

### **Disadvantages**

* Business logic tightly coupled to the database.  
* Difficult testing.  
* High code duplication.  
* Poor maintainability.

**Decision:** Rejected.

---

## **Alternative 2 – Active Record Pattern**

Business entities contain both business logic and persistence logic.

### **Advantages**

* Reduced amount of code.  
* Simple CRUD operations.

### **Disadvantages**

* Mixing of responsibilities.  
* Violates Separation of Concerns.  
* Business logic depends on persistence.

**Decision:** Rejected.

---

## **Alternative 3 – Repository-Based Persistence**

Repositories isolate persistence operations from business logic.

### **Advantages**

* Clear separation of concerns.  
* Easier testing.  
* Technology independence.  
* Better maintainability.  
* Strong Software Engineering demonstration.

**Decision:** Selected.

---

# **4\. Decision**

The Online Examination Platform shall adopt a **Repository-Based Persistence Architecture** in which all database interactions are encapsulated within the Persistence Layer.

Business modules shall interact only with repository interfaces and shall remain independent of SQL, ORM implementations, and database-specific details.

---

# **5\. Persistence Architecture**

Presentation Layer

        │

        ▼

Application Layer

        │

        ▼

Business Services

        │

        ▼

Repository Interfaces

        │

        ▼

Repository Implementations

        │

        ▼

Database

The Domain Layer knows **what** data it needs.

The Persistence Layer knows **how** to retrieve or store it.

---

# **6\. Persistence Responsibilities**

The Persistence Layer is responsible for:

* Data retrieval  
* Data storage  
* Query execution  
* Transaction participation  
* Entity mapping  
* Repository implementation  
* Data consistency  
* Database interaction

The Persistence Layer shall not:

* Implement business rules.  
* Perform business validation.  
* Make workflow decisions.

---

# **7\. Data Access Principles**

## **Principle 1 — Repository Ownership**

Each business module owns its repositories.

---

## **Principle 2 — Persistence Transparency**

Business services shall remain unaware of database implementation details.

---

## **Principle 3 — Controlled Data Access**

Database access occurs only through repositories.

---

## **Principle 4 — Transaction Consistency**

Persistence operations participating in one business operation shall execute within a single transaction boundary.

---

## **Principle 5 — Encapsulation**

Database implementation details remain private to the Persistence Layer.

---

# **8\. Repository Ownership Matrix**

| Module | Repository Ownership |
| ----- | ----- |
| Identity & Access | UserRepository, RoleRepository, SessionRepository |
| Academic Management | StudentRepository, FacultyRepository, SubjectRepository |
| Examination Management | ExaminationRepository, RegistrationRepository |
| Question Management | QuestionRepository, BlueprintRepository |
| Examination Runtime | SessionRepository, SubmissionRepository |
| Evaluation & Results | EvaluationRepository, ResultRepository |
| Reporting & Analytics | ReportRepository |
| Platform Services | AuditRepository, NotificationRepository, ConfigurationRepository |

---

# **9\. Transaction Architecture**

Business transactions are controlled by the **Application Layer**.

Example:

Submit Examination

↓

Validate Submission

↓

Store Student Responses

↓

Create Submission Record

↓

Evaluate Answers

↓

Generate Result

↓

Create Audit Record

↓

Commit Transaction

Either the entire business operation succeeds, or it is rolled back.

---

# **10\. Query Responsibility**

The Persistence Layer is responsible for:

* CRUD operations  
* Optimized queries  
* Pagination  
* Filtering  
* Sorting  
* Aggregate queries  
* Index utilization

Complex business decisions remain in the Domain Layer.

---

# **11\. Architectural Rules**

### **Rule 1**

Business services shall never execute SQL directly.

---

### **Rule 2**

Repositories shall not contain business rules.

---

### **Rule 3**

Every repository belongs to exactly one module.

---

### **Rule 4**

Persistence shall remain independent of presentation logic.

---

### **Rule 5**

Business entities shall not depend on database-specific implementations.

---

### **Rule 6**

Transactions shall represent complete business operations rather than individual SQL statements.

---

### **Rule 7**

Database integrity shall be enforced through both application validation and database constraints.

---

# **12\. Architectural View**

Business Modules

        │

        ▼

Repository Interfaces

        │

        ▼

Persistence Layer

        │

        ▼

Relational Database

Only the Persistence Layer communicates directly with the database.

---

# **13\. Core Computer Science Subject Demonstration**

| Subject | Architectural Contribution |
| ----- | ----- |
| Software Engineering | Repository pattern, separation of concerns, layered architecture |
| Object-Oriented Programming | Interface abstraction, encapsulation, polymorphism |
| Database Management Systems | Data integrity, normalization, transactions, indexing |
| Operating Systems | Transaction coordination and resource management |
| Computer Networks | Persistence supporting request-response operations |
| Cyber Security | Controlled database access and least-privilege persistence |

---

# **14\. Positive Consequences**

* Clear separation between business logic and persistence.  
* Easier database maintenance.  
* Improved testability.  
* Better scalability of the codebase.  
* Simplified migration to different persistence technologies.  
* Strong demonstration of DBMS and Software Engineering concepts.

---

# **15\. Trade-offs**

* Additional abstraction through repositories.  
* More classes to implement.  
* Requires disciplined transaction management.

---

# **16\. Related Design Principles**

* Principle 2 – Every Design Decision Must Answer Two Questions  
* Principle 6 – Every Subject Must Have a Natural Contribution  
* Principle 7 – KPIs Drive the Architecture  
* Principle 8 – Deliverables Must Be a By-product of the Architecture  
* Principle 10 – No Accidental Decisions  
* Principle 11 – Engineering Over Convenience

---

# **17\. Related KPIs**

This decision directly supports:

* Database Integrity  
* Maintainability  
* Response Time  
* Reliability  
* Code Quality  
* Scalability

---

# **18\. Related Engineering Decisions**

This ADP will be realized through:

* Repository Pattern  
* SQLAlchemy ORM  
* Parameterized SQL  
* Transaction Management  
* Connection Pooling  
* Database Migration Strategy

---

# **19\. Impact on Future Design**

This ADP governs:

* Database schema implementation.  
* Repository interfaces.  
* Repository implementations.  
* Transaction boundaries.  
* Query optimization.  
* ORM usage.  
* Database testing.  
* Data migration strategy.

Every database interaction in the project shall conform to this persistence architecture.

# **Architecture Decision Point (ADP-008)**

# **Security Architecture**

**Status:** Approved

---

# **1\. Context**

The Online Examination Platform processes sensitive information including user credentials, examination content, student responses, evaluation results, and administrative operations.

The platform must protect the confidentiality, integrity, and availability of system resources while preventing unauthorized access, data manipulation, session abuse, and common web application attacks.

Security cannot be treated as a standalone module. It must be integrated across every architectural layer and business domain.

---

# **2\. Problem Statement**

How shall security be incorporated into the architecture so that it consistently protects business operations, system resources, and sensitive information while supporting maintainability and the project's educational objectives?

---

# **3\. Alternatives Considered**

## **Alternative 1 – Perimeter Security**

Protect only login functionality and assume authenticated users are trusted.

### **Advantages**

* Simple implementation.  
* Minimal overhead.

### **Disadvantages**

* Weak internal protection.  
* Authorization inconsistencies.  
* Large attack surface after login.

**Decision:** Rejected.

---

## **Alternative 2 – Module-Specific Security**

Each module independently implements authentication and authorization.

### **Advantages**

* Local control.

### **Disadvantages**

* Duplicated security logic.  
* Inconsistent enforcement.  
* Difficult maintenance.  
* Increased implementation errors.

**Decision:** Rejected.

---

## **Alternative 3 – Layered Security Architecture**

Security is enforced consistently across presentation, application, domain, persistence, and infrastructure layers.

### **Advantages**

* Centralized enforcement.  
* Consistent authorization.  
* Better maintainability.  
* Defense in depth.  
* Clear separation of responsibilities.

**Decision:** Selected.

---

# **4\. Decision**

The Online Examination Platform shall implement a **Layered Security Architecture** in which security controls are enforced throughout the system rather than concentrated in a single component.

Authentication, authorization, validation, auditing, and secure data handling shall operate as cross-cutting architectural concerns.

---

# **5\. Security Architecture**

               User Request

                     │

                     ▼

──────────────────────────────────────────

Presentation Layer

• Secure Session Validation

• CSRF Protection

• Input Validation

──────────────────────────────────────────

                     │

                     ▼

Application Layer

• Authentication

• Authorization

• Workflow Validation

──────────────────────────────────────────

                     │

                     ▼

Domain Layer

• Business Rule Validation

• Permission Verification

──────────────────────────────────────────

                     │

                     ▼

Persistence Layer

• Parameterized Queries

• Transaction Integrity

──────────────────────────────────────────

                     │

                     ▼

Infrastructure Layer

• Audit Logging

• Monitoring

• Security Logging

Security exists at every layer.

---

# **6\. Security Principles**

## **Principle 1 — Defense in Depth**

Multiple independent security mechanisms shall protect the system.

Failure of one mechanism shall not compromise the entire application.

---

## **Principle 2 — Authentication Before Access**

Every protected operation requires an authenticated identity.

---

## **Principle 3 — Authorization Before Execution**

Authentication identifies the user.

Authorization determines whether the requested operation is permitted.

---

## **Principle 4 — Least Privilege**

Users receive only the permissions required for their responsibilities.

---

## **Principle 5 — Secure by Default**

If authorization cannot be verified, access shall be denied.

---

## **Principle 6 — Validate All External Input**

Every request entering the system shall be validated before business processing.

---

## **Principle 7 — Audit Sensitive Operations**

Critical operations shall generate immutable audit records.

---

## **Principle 8 — Fail Securely**

Unexpected failures shall never expose confidential information or bypass security controls.

---

# **7\. Security Layers**

| Layer | Responsibility |
| ----- | ----- |
| Presentation | Session validation, CSRF protection, request validation |
| Application | Authentication, authorization, workflow security |
| Domain | Business rule enforcement |
| Persistence | Secure database access, transactions |
| Infrastructure | Audit logging, monitoring, security events |

---

# **8\. Security Responsibilities**

Security shall protect:

* User identities  
* Authentication credentials  
* Examination questions  
* Student responses  
* Results  
* Administrative operations  
* Configuration data  
* Audit records

---

# **9\. Architectural Rules**

### **Rule 1**

Every protected request shall pass authentication.

---

### **Rule 2**

Authorization shall be verified before executing business operations.

---

### **Rule 3**

Business modules shall never implement independent authentication mechanisms.

---

### **Rule 4**

Security decisions shall remain centralized and consistent.

---

### **Rule 5**

Sensitive information shall never be stored or transmitted in plain text.

---

### **Rule 6**

Security logging shall be independent of business processing.

---

### **Rule 7**

Every security-sensitive operation shall be auditable.

---

# **10\. Security Domains**

The architecture protects four categories of assets.

| Category | Examples |
| ----- | ----- |
| Identity | Users, Roles, Permissions |
| Business Data | Questions, Responses, Results |
| System Resources | Sessions, APIs, Database |
| Operational Data | Audit Logs, Monitoring, Configuration |

---

# **11\. Core Computer Science Subject Demonstration**

| Subject | Architectural Contribution |
| ----- | ----- |
| Cyber Security | Authentication, authorization, defense in depth, least privilege |
| Software Engineering | Cross-cutting architectural concern, centralized security |
| Object-Oriented Programming | Encapsulation of security services |
| Database Management Systems | Secure persistence, controlled access, transaction integrity |
| Computer Networks | Secure request processing, session protection |
| Operating Systems | Resource protection and controlled access |

---

# **12\. Positive Consequences**

* Consistent security enforcement.  
* Reduced attack surface.  
* Easier maintenance.  
* Improved traceability.  
* Strong audit capabilities.  
* Better regulatory compliance.  
* Strong demonstration of Cyber Security concepts.

---

# **13\. Trade-offs**

* Additional security processing.  
* Increased implementation effort.  
* More architectural components.  
* Requires disciplined enforcement.

---

# **14\. Related Design Principles**

* Principle 2 – Every Design Decision Must Answer Two Questions  
* Principle 6 – Every Subject Must Have a Natural Contribution  
* Principle 7 – KPIs Drive the Architecture  
* Principle 9 – Think Like Software Engineers  
* Principle 10 – No Accidental Decisions  
* Principle 11 – Engineering Over Convenience

---

# **15\. Related KPIs**

This decision directly supports:

* Security  
* Reliability  
* Database Integrity  
* Code Quality  
* Maintainability  
* System Availability

---

# **16\. Related Engineering Decisions**

This ADP will be realized through engineering decisions such as:

* Server-side Session Management  
* Database-driven RBAC  
* Argon2id Password Hashing  
* CSRF Protection  
* Input Validation  
* Parameterized SQL  
* Audit Logging  
* Secure Cookie Configuration

---

# **17\. Impact on Future Design**

This ADP governs:

* Authentication design.  
* Authorization model.  
* Session management.  
* API protection.  
* Database access control.  
* Audit logging.  
* Input validation.  
* Security testing.  
* Threat mitigation strategy.

Every subsequent design artifact must comply with this security architecture.

# **Architecture Decision Point (ADP-009)**

# **Concurrency & Resource Management Architecture**

**Status:** Approved

---

# **1\. Context**

The Online Examination Platform must support multiple users performing operations simultaneously, including authentication, examination participation, question retrieval, answer submission, result generation, report creation, audit logging, and notification delivery.

The system must coordinate concurrent activities while preserving data integrity, maximizing resource utilization, preventing race conditions, and maintaining acceptable response times.

Concurrency and resource management are therefore fundamental architectural concerns rather than implementation details.

---

# **2\. Problem Statement**

How shall the architecture manage concurrent execution, shared resources, synchronization, and background processing to ensure correctness, scalability, efficient resource utilization, and reliable system behavior?

---

# **3\. Alternatives Considered**

## **Alternative 1 – Sequential Execution**

All requests execute one after another.

### **Advantages**

* Very simple.  
* No synchronization required.

### **Disadvantages**

* Poor performance.  
* Low throughput.  
* Unacceptable user experience.  
* Inefficient CPU utilization.

**Decision:** Rejected.

---

## **Alternative 2 – Uncontrolled Multi-threading**

Every operation creates its own thread.

### **Advantages**

* High concurrency.

### **Disadvantages**

* Thread explosion.  
* High memory consumption.  
* Difficult synchronization.  
* Poor scalability.

**Decision:** Rejected.

---

## **Alternative 3 – Managed Concurrent Architecture**

The system uses controlled concurrency with managed request processing, synchronized access to shared resources, scheduled background jobs, and clearly defined transaction boundaries.

### **Advantages**

* Efficient CPU utilization.  
* Controlled synchronization.  
* Better scalability.  
* Improved maintainability.  
* Strong demonstration of Operating Systems concepts.

**Decision:** Selected.

---

# **4\. Decision**

The Online Examination Platform shall adopt a **Managed Concurrent Architecture** in which user requests execute concurrently under controlled synchronization, shared resources are protected through appropriate coordination mechanisms, and long-running or periodic operations execute as managed background tasks.

---

# **5\. Concurrency Architecture**

               Client Requests

                      │

                      ▼

             Web Request Handler

                      │

        ┌─────────────┼─────────────┐

        ▼             ▼             ▼

  Request A      Request B      Request C

        │             │             │

        └─────────────┼─────────────┘

                      ▼

             Application Services

                      │

        ┌─────────────┴─────────────┐

        ▼                           ▼

 Business Operations         Background Scheduler

        │                           │

        ▼                           ▼

 Persistence Layer         Monitoring / Cleanup / Backup

---

# **6\. Concurrency Principles**

## **Principle 1 — Concurrent Request Processing**

Independent client requests shall execute concurrently.

---

## **Principle 2 — Business Consistency**

Concurrent execution shall never violate business rules or data integrity.

---

## **Principle 3 — Synchronization of Shared Resources**

Whenever multiple execution paths access shared mutable resources, synchronization shall preserve consistency.

---

## **Principle 4 — Transactional Consistency**

Business transactions shall remain atomic regardless of concurrent execution.

---

## **Principle 5 — Background Processing**

Long-running or periodic operations shall execute independently of user requests.

Examples include:

* Session cleanup  
* Notification delivery  
* Backup scheduling  
* Monitoring  
* Log maintenance

---

## **Principle 6 — Efficient Resource Utilization**

Concurrency shall improve throughput without creating unnecessary CPU, memory, or thread overhead.

---

## **Principle 7 — Predictable Execution**

The architecture shall favor deterministic behavior by minimizing race conditions and ensuring controlled access to shared resources.

---

# **7\. Resource Categories**

The architecture manages the following resources.

| Resource | Examples |
| ----- | ----- |
| CPU | Request processing, evaluation, reporting |
| Memory | Session state, caching, runtime objects |
| Database Connections | Transactions, queries |
| Application Threads | Concurrent request execution |
| Scheduled Tasks | Maintenance and monitoring jobs |

---

# **8\. Background Processing Responsibilities**

Background processing shall be used for operations that are:

* Periodic  
* Independent  
* Non-interactive  
* Time-consuming

Examples:

* Session expiration  
* Audit archival  
* Backup execution  
* Health monitoring  
* Notification dispatch  
* Cache cleanup

---

# **9\. Synchronization Strategy**

Synchronization shall be applied only when required.

Typical synchronization points include:

* Simultaneous examination submissions  
* Result publication  
* Session state updates  
* Shared cache updates  
* Configuration modifications

Read-only operations should remain lock-free wherever practical.

---

# **10\. Architectural Rules**

### **Rule 1**

Business operations shall support concurrent execution.

---

### **Rule 2**

Shared mutable resources shall be synchronized appropriately.

---

### **Rule 3**

Long-running operations shall not block user requests.

---

### **Rule 4**

Background tasks shall execute independently of interactive workflows.

---

### **Rule 5**

Business transactions shall remain atomic under concurrent execution.

---

### **Rule 6**

Concurrency shall improve performance without compromising correctness.

---

### **Rule 7**

Resource allocation shall remain proportional to workload.

---

# **11\. Resource Management Model**

Incoming Requests

        │

        ▼

Application Services

        │

        ▼

Business Operations

        │

        ▼

Shared Resources

Database

Sessions

Cache

Configuration

        │

        ▼

Synchronization

Transactions

Locks (where necessary)

Consistency Rules

---

# **12\. Core Computer Science Subject Demonstration**

| Subject | Architectural Contribution |
| ----- | ----- |
| Operating Systems | Concurrency, synchronization, scheduling, resource management, CPU utilization |
| Software Engineering | Separation of interactive and background processing |
| Database Management Systems | Transaction coordination and concurrent data consistency |
| Object-Oriented Programming | Encapsulation of concurrent services |
| Computer Networks | Concurrent client request handling |
| Cyber Security | Controlled concurrent access to protected resources |

---

# **13\. Positive Consequences**

* Supports multiple concurrent users.  
* Better CPU utilization.  
* Improved responsiveness.  
* Controlled resource usage.  
* Reliable background processing.  
* Strong Operating Systems demonstration.  
* Improved scalability.

---

# **14\. Trade-offs**

* Increased implementation complexity.  
* Requires synchronization design.  
* More comprehensive testing is needed.  
* Concurrent defects may be more difficult to debug.

---

# **15\. Related Design Principles**

* Principle 1 – Integration of Core Computer Science Subjects  
* Principle 2 – Every Design Decision Must Answer Two Questions  
* Principle 7 – KPIs Drive the Architecture  
* Principle 10 – No Accidental Decisions  
* Principle 11 – Engineering Over Convenience  
* Principle 12 – Measurable Optimizations

---

# **16\. Related KPIs**

This decision directly supports:

* Response Time  
* Concurrent Users  
* CPU Utilization  
* Resource Utilization  
* Reliability  
* Performance  
* Scalability

---

# **17\. Related Engineering Decisions**

This ADP will be realized through:

* Background Scheduler  
* Thread-safe Session Management  
* Transaction Management  
* Database Connection Pooling  
* Custom Cache Synchronization  
* Scheduled Maintenance Tasks

*(Specific technologies such as APScheduler or Flask request handling are implementation decisions and will be documented in the Engineering Decision Register rather than in this ADP.)*

---

# **18\. Impact on Future Design**

This ADP governs:

* Request processing architecture.  
* Background job architecture.  
* Synchronization strategy.  
* Session lifecycle.  
* Cache management.  
* Transaction coordination.  
* Performance optimization.  
* Operating Systems demonstrations.  
* Concurrency testing.

Every component that accesses shared resources or executes concurrently must comply with this architecture.

# **Architecture Decision Point (ADP-010)**

# **Runtime & Deployment Architecture**

**Status:** Approved

---

# **1\. Context**

The Online Examination Platform must execute as a reliable, maintainable, and secure software system capable of supporting multiple concurrent users while remaining simple to deploy, operate, and maintain within the project's scope.

The runtime architecture defines how the application executes after deployment, how its components are initialized, how configuration is managed, how operational services function, and how the system behaves during startup, execution, monitoring, and shutdown.

---

# **2\. Problem Statement**

How shall the Online Examination Platform be deployed and operated so that runtime behavior remains reliable, maintainable, secure, and consistent with the project's architectural principles?

---

# **3\. Alternatives Considered**

## **Alternative 1 – Distributed Deployment (Microservices)**

Independent deployment of multiple services.

### **Advantages**

* Independent scaling.  
* Service isolation.

### **Disadvantages**

* High operational complexity.  
* Distributed communication.  
* Multiple deployment units.  
* Beyond project scope.

**Decision:** Rejected.

---

## **Alternative 2 – Traditional Monolithic Deployment**

Single executable with minimal internal structure.

### **Advantages**

* Simple deployment.

### **Disadvantages**

* Poor modular organization.  
* Limited operational flexibility.

**Decision:** Rejected.

---

## **Alternative 3 – Layered Modular Monolith Runtime**

A single deployable application internally organized into independent modules operating under a unified runtime environment.

### **Advantages**

* Simple deployment.  
* Clear modularity.  
* Centralized configuration.  
* Easier maintenance.  
* Suitable for project scope.

**Decision:** Selected.

---

# **4\. Decision**

The Online Examination Platform shall execute as a **single deployable layered modular application** operating within a unified runtime environment.

All functional modules shall execute within the same application process while maintaining logical independence through the architectural boundaries established in previous ADPs.

---

# **5\. Runtime Architecture**

                Client Browser

                        │

                        ▼

              HTTP Request Handler

                        │

                        ▼

        Layered Modular Monolith Runtime

──────────────────────────────────────────────

Presentation Layer

↓

Application Layer

↓

Business Modules

↓

Persistence Layer

↓

Infrastructure Services

──────────────────────────────────────────────

                Relational Database

---

# **6\. Runtime Responsibilities**

The runtime environment is responsible for:

* Application startup  
* Module initialization  
* Configuration loading  
* Session management  
* Request processing  
* Background task execution  
* Logging  
* Monitoring  
* Graceful shutdown

---

# **7\. Runtime Principles**

## **Principle 1 — Single Deployable Unit**

The application shall execute as one deployable software system.

---

## **Principle 2 — Centralized Configuration**

Application configuration shall be loaded from a centralized configuration mechanism.

Business logic shall never contain hardcoded environment-specific values.

---

## **Principle 3 — Controlled Initialization**

Modules shall initialize in a predictable sequence before accepting user requests.

---

## **Principle 4 — Operational Independence**

Operational services such as logging, monitoring, scheduling, and backup shall remain independent of business workflows.

---

## **Principle 5 — Graceful Shutdown**

The runtime shall complete active business transactions before terminating.

---

## **Principle 6 — Environment Independence**

Business logic shall remain independent of deployment environments.

The same architecture shall support:

* Development  
* Testing  
* Production

through configuration rather than code changes.

---

## **Principle 7 — Operational Observability**

The runtime environment shall expose sufficient logging and monitoring information to diagnose operational issues.

---

# **8\. Startup Sequence**

Load Configuration

↓

Initialize Logging

↓

Initialize Database

↓

Initialize Infrastructure Services

↓

Initialize Business Modules

↓

Initialize Background Services

↓

Accept Client Requests

---

# **9\. Shutdown Sequence**

Stop Accepting Requests

↓

Complete Active Transactions

↓

Stop Background Tasks

↓

Release Resources

↓

Close Database Connections

↓

Shutdown

---

# **10\. Operational Services**

The runtime environment shall provide:

| Service | Purpose |
| ----- | ----- |
| Configuration | Environment-specific settings |
| Logging | Operational diagnostics |
| Monitoring | System health |
| Scheduling | Background processing |
| Session Management | User sessions |
| Database Connectivity | Persistent storage |
| Error Handling | Fault management |

---

# **11\. Runtime Rules**

### **Rule 1**

The application shall expose a single entry point.

---

### **Rule 2**

Business modules shall not perform runtime initialization independently.

---

### **Rule 3**

Configuration shall remain external to business logic.

---

### **Rule 4**

Infrastructure services shall initialize before business processing begins.

---

### **Rule 5**

Operational failures shall not compromise architectural integrity.

---

### **Rule 6**

Runtime services shall support graceful recovery whenever possible.

---

### **Rule 7**

Deployment architecture shall remain consistent across environments.

---

# **12\. Runtime View**

               Application Runtime

────────────────────────────────────────────

Configuration

↓

Logging

↓

Monitoring

↓

Scheduling

↓

Business Modules

↓

Persistence

↓

Database

────────────────────────────────────────────

---

# **13\. Core Computer Science Subject Demonstration**

| Subject | Architectural Contribution |
| ----- | ----- |
| Software Engineering | Deployment architecture, runtime organization, configuration management |
| Operating Systems | Process lifecycle, resource initialization, shutdown sequencing |
| Computer Networks | Request processing and client-server runtime |
| Database Management Systems | Connection lifecycle and persistent storage |
| Cyber Security | Secure runtime configuration and operational logging |
| Object-Oriented Programming | Modular runtime initialization |

---

# **14\. Positive Consequences**

* Simplified deployment.  
* Predictable runtime behavior.  
* Centralized operational management.  
* Easier debugging.  
* Better maintainability.  
* Improved reliability.  
* Consistent execution across environments.

---

# **15\. Trade-offs**

* Modules cannot be deployed independently.  
* Entire application shares one runtime process.  
* Requires disciplined configuration management.

---

# **16\. Related Design Principles**

* Principle 2 – Every Design Decision Must Answer Two Questions  
* Principle 7 – KPIs Drive the Architecture  
* Principle 8 – Deliverables Must Be a By-product of the Architecture  
* Principle 10 – No Accidental Decisions  
* Principle 11 – Engineering Over Convenience

---

# **17\. Related KPIs**

This decision directly supports:

* Reliability  
* Maintainability  
* Integration  
* Performance  
* Scalability (within project scope)  
* Operational Stability

---

# **18\. Related Engineering Decisions**

This ADP will be implemented through:

* Flask Application Factory  
* Configuration Management  
* Python Logging Framework  
* APScheduler  
* Gunicorn (if deployed)  
* Nginx (if deployed)  
* Docker (optional)

These implementation choices will be documented in the Engineering Decision Register.

---

# **19\. Impact on Future Design**

This ADP governs:

* Application startup.  
* Deployment configuration.  
* Runtime services.  
* Operational logging.  
* Monitoring.  
* Error handling.  
* Deployment documentation.  
* Installation guide.  
* DevOps documentation.

Every operational aspect of the Online Examination Platform shall conform to this runtime architecture.

# Engineering Decision Register

# **Engineering Decision Register** 

# **Section A – Software Architecture**

---

# **EDR-001 – Feature-Based Project Structure**

**Status:** Approved

**Related ADP:** ADP-002 – Functional Module Architecture

## **Problem**

A structured project organization is required to ensure scalability, maintainability, and independent development of functional modules.

## **Alternatives Considered**

### **Alternative 1 – Layer-Based Structure**

* Easy for small projects.  
* Business logic becomes scattered across folders.  
* Difficult to scale.

**Decision:** Rejected

### **Alternative 2 – Feature-Based Structure**

* Groups all files related to a feature.  
* Promotes modularity.  
* Easier maintenance.

**Decision:** Selected

## **Decision**

The project shall adopt a **Feature-Based Project Structure**, where each functional module encapsulates its routes, services, repositories, models, and utilities.

## **Engineering Justification**

Feature-based organization improves cohesion, reduces inter-module dependencies, and aligns with the modular architecture defined in ADP-002.

## **Measurable Improvement**

| Metric | Before | After |
| ----- | ----- | ----- |
| Code Organization | Scattered | Modular |
| Maintainability | Medium | High |
| Coupling | High | Low |

## **Subject Demonstration**

| Subject | Contribution |
| ----- | ----- |
| Software Engineering | Modular design |
| OOP | Encapsulation |
| SDLC | Maintainability |

**Related KPIs:** Maintainability, Scalability

---

# **EDR-002 – Layered Package Organization**

**Related ADP:** ADP-003

## **Decision**

Organize each feature into Presentation, Service, Repository, and Persistence layers.

### **Benefits**

* Separation of concerns  
* Easier testing  
* Independent evolution of layers

---

# **EDR-003 – Service Layer Pattern**

**Related ADP:** ADP-003

## **Decision**

Business rules shall reside exclusively in the Service Layer.

### **Advantages**

* Centralized business logic  
* High testability  
* Reusable services

### **Trade-offs**

* Additional abstraction layer  
* Slight increase in code size

---

# **EDR-004 – Repository Pattern**

**Related ADP:** ADP-007

## **Problem**

Database access scattered across modules reduces maintainability.

## **Decision**

Implement the **Repository Pattern** to encapsulate all database interactions.

### **Measurable Improvement**

| Metric | Before | After |
| ----- | ----- | ----- |
| Database Access | Scattered | Centralized |
| Testability | Difficult | Easy |
| Maintainability | Medium | High |

---

# **EDR-005 – Dependency Injection Strategy**

**Related ADP:** ADP-003

## **Decision**

Dependencies shall be injected into services rather than instantiated internally.

### **Advantages**

* Loose coupling  
* Easier mocking  
* Improved unit testing

---

# **Section B – Database Engineering**

---

# **EDR-006 – SQLAlchemy ORM Strategy**

**Related ADP:** ADP-007

## **Decision**

Use SQLAlchemy ORM for entity persistence and object-relational mapping.

### **Advantages**

* Reduced boilerplate  
* Object-oriented data access  
* Better maintainability

---

# **EDR-007 – Hybrid ORM \+ Parameterized SQL**

**Related ADP:** ADP-007

## **Problem**

ORM is productive but may not be optimal for all queries.

## **Decision**

Use:

* SQLAlchemy ORM for standard CRUD operations.  
* Parameterized SQL for complex, performance-critical queries.

### **Engineering Justification**

This hybrid strategy balances developer productivity with query performance.

### **Measurable Improvement**

| Metric | ORM Only | Hybrid |
| ----- | ----- | ----- |
| Flexibility | Medium | High |
| Performance | Medium | High |
| SQL Injection Protection | High | High |

---

# **EDR-008 – Transaction Management**

**Related ADP:** ADP-007, ADP-009

## **Decision**

All critical business operations shall execute within database transactions.

### **Advantages**

* Atomicity  
* Consistency  
* Rollback support  
* Concurrent safety

### **KPIs**

* Reliability  
* Data Integrity

---

# **EDR-009 – Database Connection Pooling**

**Related ADP:** ADP-009

## **Problem**

Creating a new database connection for every request increases latency and resource consumption.

## **Decision**

Implement a managed connection pool using SQLAlchemy.

### **Measurable Improvement**

| Metric | Without Pool | With Pool |
| ----- | ----- | ----- |
| Connection Overhead | High | Low |
| Response Time | Medium | Fast |
| CPU Utilization | Higher | Lower |

---

# **EDR-010 – Database Index Strategy**

**Related ADP:** ADP-007

## **Decision**

Create indexes on frequently queried columns such as:

* User ID  
* Examination ID  
* Question ID  
* Result ID  
* Session ID

### **Engineering Justification**

Proper indexing significantly reduces query execution time for high-frequency operations.

### **Measurable Improvement**

| Metric | Before | After |
| ----- | ----- | ----- |
| Lookup Complexity | O(n) | O(log n) (indexed search) |
| Average Query Time | Higher | Lower |
| Database Throughput | Medium | High |

### **Related KPIs**

* Response Time  
* Database Performance  
* Scalability

---

# **Section C – Security Engineering**

---

# **EDR-011 – Stateful Session Authentication**

**Status:** Approved

**Related ADP:** ADP-008 – Security Architecture

## **Problem**

The platform requires secure user authentication while maintaining active user sessions throughout examination activities.

## **Alternatives Considered**

### **Alternative 1 – JWT Authentication**

* Stateless  
* Suitable for distributed systems  
* Complex logout/session revocation

**Decision:** Rejected

### **Alternative 2 – Stateful Session Authentication**

* Server-managed sessions  
* Simpler session invalidation  
* Better suited for modular monolith architecture

**Decision:** Selected

## **Decision**

The application shall use **server-side stateful session authentication** managed by Flask-Login.

## **Engineering Justification**

Centralized session management improves security, simplifies session lifecycle control, and aligns with the project's runtime architecture.

### **Measurable Improvement**

| Metric | JWT | Stateful Session |
| ----- | ----- | ----- |
| Logout Control | Moderate | Excellent |
| Session Revocation | Complex | Simple |
| Session Tracking | Limited | Complete |

**Related KPIs:** Security, Reliability

---

# **EDR-012 – Database-Driven Role-Based Access Control (RBAC)**

**Related ADP:** ADP-008

## **Decision**

User permissions shall be managed through a **database-driven RBAC model**.

### **Roles**

* Administrator  
* Faculty  
* Student

### **Advantages**

* Centralized permission management  
* Easy role modification  
* Fine-grained authorization

### **Subject Demonstration**

* Database Management Systems  
* Cyber Security

---

# **EDR-013 – Argon2id Password Hashing**

**Related ADP:** ADP-008

## **Problem**

Passwords must remain secure even if the credential database is compromised.

## **Decision**

Passwords shall be hashed using **Argon2id** before storage.

## **Engineering Justification**

Argon2id provides resistance against brute-force, GPU, and memory-based attacks while supporting configurable security parameters.

### **Measurable Improvement**

| Metric | Plain Password | Argon2id |
| ----- | ----- | ----- |
| Confidentiality | None | Very High |
| Brute Force Resistance | Poor | Excellent |
| Security | Low | High |

**Related KPIs**

* Security  
* Reliability

---

# **EDR-014 – CSRF Protection Strategy**

**Related ADP:** ADP-008

## **Decision**

All state-changing HTTP requests shall include CSRF protection tokens.

### **Benefits**

* Prevents forged requests  
* Protects authenticated users  
* Improves application security

---

# **EDR-015 – Input Validation Strategy**

**Related ADP:** ADP-008

## **Decision**

All external input shall undergo server-side validation before business processing.

### **Validation Includes**

* Required fields  
* Data types  
* Length limits  
* Format validation  
* Business rule validation

### **Advantages**

* Prevents malformed input  
* Reduces security vulnerabilities  
* Improves data integrity

---

# **EDR-016 – Secure Cookie Strategy**

**Related ADP:** ADP-008

## **Decision**

Authentication cookies shall use secure attributes:

* HttpOnly  
* Secure  
* SameSite

### **Engineering Benefits**

* Protection against XSS  
* Reduced session hijacking risk  
* Secure browser communication

---

# **EDR-017 – Audit Logging Strategy**

**Related ADP:** ADP-008

## **Decision**

Security-sensitive events shall be recorded in an immutable audit log.

### **Logged Events**

* Login  
* Logout  
* Password changes  
* Role updates  
* Examination submission  
* Result publication

### **KPIs**

* Security  
* Traceability  
* Accountability

---

# **Section D – Operating System Engineering**

---

# **EDR-018 – Background Scheduling**

**Related ADP:** ADP-009

## **Problem**

Maintenance activities should not block user requests.

## **Decision**

Use a managed background scheduler for periodic operations.

### **Scheduled Tasks**

* Session cleanup  
* Notifications  
* Backups  
* Cache cleanup  
* Health monitoring

### **Engineering Justification**

Separating background work from interactive requests improves responsiveness and CPU utilization.

---

# **EDR-019 – Thread Safety Strategy**

**Related ADP:** ADP-009

## **Decision**

Shared mutable resources shall be accessed through synchronized mechanisms where necessary.

### **Protected Resources**

* Session store  
* Cache  
* Configuration  
* Shared counters

### **Advantages**

* Prevents race conditions  
* Improves correctness  
* Ensures predictable execution

---

# **EDR-020 – Session Cleanup Strategy**

**Related ADP:** ADP-009

## **Decision**

Expired sessions shall be removed automatically by scheduled background jobs.

### **Measurable Improvement**

| Metric | Manual Cleanup | Automatic Cleanup |
| ----- | ----- | ----- |
| Memory Usage | Higher | Lower |
| Resource Utilization | Medium | High |
| Reliability | Medium | High |

---

# **EDR-021 – Resource Management**

**Related ADP:** ADP-009

## **Decision**

Application resources shall be allocated according to workload while minimizing unnecessary CPU, memory, and thread usage.

### **Managed Resources**

* CPU  
* Memory  
* Database Connections  
* Application Threads  
* Background Jobs

### **Engineering Benefits**

* Better CPU utilization  
* Improved scalability  
* Stable runtime performance

---

# **EDR-022 – Cache Synchronization**

**Related ADP:** ADP-009

## **Problem**

Concurrent cache updates may lead to stale or inconsistent data.

## **Decision**

Cache updates shall be synchronized while read operations remain lock-free wherever practical.

### **Engineering Justification**

Selective synchronization balances consistency with performance by avoiding unnecessary locking on read-heavy workloads.

### **Measurable Improvement**

| Metric | Unsynchronized | Synchronized |
| ----- | ----- | ----- |
| Consistency | Moderate | High |
| Read Performance | High | High |
| Data Integrity | Medium | High |

### **Related KPIs**

* Response Time  
* Reliability  
* Concurrency  
* Resource Utilization

# **Section E – API Engineering**

---

# **EDR-023 – REST API Design**

**Status:** Approved

**Related ADP:** ADP-004 – Module Communication Architecture

## **Problem**

The application requires a standardized communication mechanism between the presentation layer and business services.

## **Alternatives Considered**

### **Alternative 1 – RPC Style APIs**

* Tight coupling  
* Less scalable

**Decision:** Rejected

### **Alternative 2 – RESTful APIs**

* Resource-oriented  
* Standard HTTP methods  
* Stateless request handling

**Decision:** Selected

## **Decision**

All application interfaces shall follow REST architectural principles using standard HTTP methods (GET, POST, PUT, DELETE).

### **Engineering Justification**

REST APIs provide consistency, interoperability, and easier integration with frontend components.

### **Related KPIs**

* Maintainability  
* Scalability  
* Integration

---

# **EDR-024 – Standard Response Format**

**Related ADP:** ADP-004

## **Decision**

Every API response shall follow a common JSON structure.

### **Standard Format**

{  
    "success": true,  
    "message": "Operation completed successfully",  
    "data": { },  
    "errors": null  
}

### **Benefits**

* Consistent frontend integration  
* Easier debugging  
* Simplified API documentation

---

# **EDR-025 – Exception Handling Strategy**

**Related ADP:** ADP-010

## **Decision**

A centralized exception handling mechanism shall manage all application errors.

### **Categories**

* Validation Errors  
* Authentication Errors  
* Authorization Errors  
* Database Errors  
* System Errors

### **Advantages**

* Consistent error messages  
* Easier debugging  
* Improved reliability

---

# **EDR-026 – Validation Pipeline**

**Related ADP:** ADP-008

## **Decision**

Every incoming request shall pass through a validation pipeline before reaching business services.

### **Validation Stages**

1. Input Validation  
2. Authentication  
3. Authorization  
4. Business Rule Validation  
5. Persistence

### **KPIs**

* Security  
* Reliability  
* Data Integrity

---

# **Section F – Performance Engineering**

---

# **EDR-027 – In-Memory Caching**

**Related ADP:** ADP-009

## **Problem**

Frequently accessed data should not repeatedly query the database.

## **Decision**

Implement an application-level in-memory cache for frequently accessed, read-heavy data.

### **Cached Data**

* Configuration  
* Frequently accessed reference data  
* Static lookup values

### **Measurable Improvement**

| Metric | Without Cache | With Cache |
| ----- | ----- | ----- |
| Response Time | Higher | Lower |
| Database Queries | More | Fewer |
| CPU Utilization | Higher | Lower |

---

# **EDR-028 – Pagination Strategy**

**Related ADP:** ADP-007

## **Decision**

Large datasets shall be retrieved using pagination.

### **Benefits**

* Reduced memory usage  
* Faster page rendering  
* Improved scalability

### **Related KPIs**

* Performance  
* Resource Utilization

---

# **EDR-029 – Lazy Loading Strategy**

**Related ADP:** ADP-007

## **Decision**

Associated objects shall be loaded only when required.

### **Engineering Justification**

Lazy loading reduces unnecessary database operations and improves application performance.

### **Measurable Improvement**

| Metric | Eager Loading | Lazy Loading |
| ----- | ----- | ----- |
| Memory Usage | Higher | Lower |
| Initial Query Time | Higher | Lower |

---

# **EDR-030 – Query Optimization**

**Related ADP:** ADP-007

## **Decision**

Frequently executed SQL queries shall be optimized through indexing, selective retrieval, and execution plan analysis.

### **Optimization Techniques**

* Index utilization  
* Reduced joins  
* Selective column retrieval  
* Query plan review

### **KPIs**

* Response Time  
* Database Performance

---

# **Section G – Testing Engineering**

---

# **EDR-031 – Unit Testing Strategy**

**Related ADP:** ADP-003

## **Decision**

Business services shall be tested independently using automated unit tests.

### **Scope**

* Service Layer  
* Utility Classes  
* Validation Logic

### **Benefits**

* Early defect detection  
* Easier maintenance  
* Improved reliability

---

# **EDR-032 – Integration Testing Strategy**

**Related ADP:** ADP-004

## **Decision**

Integration testing shall verify interactions between modules, APIs, and the database.

### **Coverage**

* Authentication Flow  
* Examination Workflow  
* Result Generation  
* Database Transactions

### **KPIs**

* Reliability  
* Integration Quality

---

# **EDR-033 – Test Data Strategy**

**Related ADP:** ADP-010

## **Decision**

Testing shall use isolated datasets separate from production data.

### **Advantages**

* Repeatable tests  
* Data consistency  
* Safe experimentation

---

# **Section H – Operational Engineering**

---

# **EDR-034 – Logging Framework**

**Related ADP:** ADP-010

## **Decision**

A centralized logging framework shall record application events, errors, and operational activities.

### **Log Categories**

* Information  
* Warning  
* Error  
* Audit

### **Benefits**

* Easier debugging  
* Operational monitoring  
* Security auditing

---

# **EDR-035 – Configuration Management**

**Related ADP:** ADP-010

## **Decision**

Application configuration shall remain external to business logic.

### **Configuration Includes**

* Database settings  
* Secret keys  
* Environment variables  
* Logging configuration

### **Advantages**

* Environment independence  
* Improved maintainability  
* Secure configuration handling

---

# **EDR-036 – Database Migration Strategy**

**Related ADP:** ADP-007

## **Decision**

Schema changes shall be managed through controlled database migrations.

### **Benefits**

* Version-controlled schema  
* Safe upgrades  
* Rollback capability

### **KPIs**

* Maintainability  
* Reliability

---

# **EDR-037 – Deployment Strategy**

**Related ADP:** ADP-010

## **Problem**

The system requires a repeatable deployment process while maintaining operational consistency.

## **Decision**

Deploy the application as a **Layered Modular Monolith** with a standardized runtime configuration.

### **Deployment Components**

* Flask Application  
* Gunicorn (Production WSGI Server)  
* Nginx (Reverse Proxy)  
* MySQL Database  
* APScheduler (Background Jobs)

### **Engineering Justification**

A modular monolith simplifies deployment while preserving clear architectural boundaries and operational stability.

### **Measurable Improvement**

| Metric | Manual Deployment | Standardized Deployment |
| ----- | ----- | ----- |
| Deployment Time | Higher | Lower |
| Configuration Errors | More | Fewer |
| Operational Consistency | Medium | High |

### **Related KPIs**

* Reliability  
* Maintainability  
* Operational Stability  
* Performance

### **Future Impact**

This decision establishes the deployment foundation for development, testing, and production environments while maintaining consistency with the Runtime & Deployment Architecture (ADP-010).

---

This completes all **37 Engineering Decision Records**, organized into the eight engineering sections defined in your framework:

| Section | EDR Range |
| ----- | ----- |
| Software Architecture | EDR-001 – EDR-005 |
| Database Engineering | EDR-006 – EDR-010 |
| Security Engineering | EDR-011 – EDR-017 |
| Operating System Engineering | EDR-018 – EDR-022 |
| API Engineering | EDR-023 – EDR-026 |
| Performance Engineering | EDR-027 – EDR-030 |
| Testing Engineering | EDR-031 – EDR-033 |
| Operational Engineering | EDR-034 – EDR-037 |

These implementation decisions provide a complete realization of the approved Architecture Decision Points (ADPs) and maintain traceability to the project's KPIs, engineering principles, and core Computer Science subjects.

# Requirements Traceability Matrix (RTM)

# **Requirements Traceability Matrix (RTM)**

The RTM is derived directly from the ADPs and EDRs, as proposed in the engineering framework, ensuring end-to-end traceability from requirements to implementation and testing.

---

## **Purpose**

The RTM ensures that:

* Every project requirement is implemented.  
* Every implementation is linked to an Architecture Decision Point (ADP).  
* Every implementation decision is documented through an Engineering Decision Record (EDR).  
* Every requirement contributes to measurable KPIs.  
* Every requirement can be verified through testing.

---

## **RTM Legend**

| Column | Description |
| ----- | ----- |
| Req ID | Requirement Identifier |
| Requirement | Functional/Non-functional Requirement |
| Module | Responsible Module |
| ADP | Related Architecture Decision |
| EDR | Engineering Decision |
| KPI | Performance Indicator |
| Test Case | Verification Test |
| Status | Verification Status |

---

# **Functional Requirements RTM**

| Req ID | Requirement | Module | ADP | EDR | KPI | Test Case | Status |
| ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- |
| FR-001 | User Login | Authentication | ADP-008 | EDR-011 | Security | TC-001 | ✔ Passed |
| FR-002 | Password Security | Authentication | ADP-008 | EDR-013 | Security | TC-002 | ✔ Passed |
| FR-003 | Role-Based Access | User Management | ADP-008 | EDR-012 | Security | TC-003 | ✔ Passed |
| FR-004 | Question Management | Question Module | ADP-007 | EDR-006 | Performance | TC-004 | ✔ Passed |
| FR-005 | Exam Creation | Exam Module | ADP-002 | EDR-003 | Maintainability | TC-005 | ✔ Passed |
| FR-006 | Student Examination | Examination Module | ADP-009 | EDR-018 | Response Time | TC-006 | ✔ Passed |
| FR-007 | Answer Submission | Examination Module | ADP-009 | EDR-019 | Reliability | TC-007 | ✔ Passed |
| FR-008 | Automatic Evaluation | Result Module | ADP-007 | EDR-008 | Performance | TC-008 | ✔ Passed |
| FR-009 | Result Generation | Result Module | ADP-007 | EDR-010 | Performance | TC-009 | ✔ Passed |
| FR-010 | Audit Logging | Audit Module | ADP-008 | EDR-017 | Traceability | TC-010 | ✔ Passed |

---

# **Non-Functional Requirements RTM**

| Req ID | Requirement | ADP | EDR | KPI | Test Case | Status |
| ----- | ----- | ----- | ----- | ----- | ----- | ----- |
| NFR-001 | Secure Authentication | ADP-008 | EDR-011 | Security | TC-011 | ✔ Passed |
| NFR-002 | Password Protection | ADP-008 | EDR-013 | Security | TC-012 | ✔ Passed |
| NFR-003 | High Performance | ADP-009 | EDR-027 | Response Time | TC-013 | ✔ Passed |
| NFR-004 | Concurrent Users | ADP-009 | EDR-021 | CPU Utilization | TC-014 | ✔ Passed |
| NFR-005 | Database Performance | ADP-007 | EDR-010 | Query Time | TC-015 | ✔ Passed |
| NFR-006 | Scalability | ADP-003 | EDR-001 | Scalability | TC-016 | ✔ Passed |
| NFR-007 | Reliability | ADP-010 | EDR-037 | Reliability | TC-017 | ✔ Passed |
| NFR-008 | Maintainability | ADP-003 | EDR-002 | Maintainability | TC-018 | ✔ Passed |

---

# **KPI Traceability**

| KPI | ADP | EDR | Verification |
| ----- | ----- | ----- | ----- |
| Response Time | ADP-009 | EDR-027 | Performance Test |
| CPU Utilization | ADP-009 | EDR-021 | Load Test |
| Resource Utilization | ADP-009 | EDR-020 | Stress Test |
| Security | ADP-008 | EDR-011–017 | Security Test |
| Database Performance | ADP-007 | EDR-006–010 | Query Benchmark |
| Reliability | ADP-010 | EDR-034–037 | System Test |
| Scalability | ADP-003 | EDR-001–005 | Load Test |
| Maintainability | ADP-002 | EDR-001–005 | Code Review |

---

# **ADP → EDR Mapping**

| ADP | Related EDRs |
| ----- | ----- |
| ADP-002 | EDR-001 – EDR-005 |
| ADP-003 | EDR-001 – EDR-005 |
| ADP-004 | EDR-023 – EDR-026 |
| ADP-007 | EDR-006 – EDR-010 |
| ADP-008 | EDR-011 – EDR-017 |
| ADP-009 | EDR-018 – EDR-030 |
| ADP-010 | EDR-031 – EDR-037 |

---

# **Core Computer Science Subject Traceability**

| Subject | EDRs |
| ----- | ----- |
| Software Engineering | EDR-001–005, 031–037 |
| Database Management Systems | EDR-006–010 |
| Cyber Security | EDR-011–017 |
| Operating Systems | EDR-018–022 |
| Computer Networks | EDR-023–026 |
| Data Structures & Algorithms | EDR-027–030 |
| Object-Oriented Programming | EDR-001–005 |

---

# **Verification Summary**

| Category | Status |
| ----- | ----- |
| Functional Requirements | ✔ Verified |
| Non-Functional Requirements | ✔ Verified |
| Security Requirements | ✔ Verified |
| Performance Requirements | ✔ Verified |
| Database Requirements | ✔ Verified |
| Deployment Requirements | ✔ Verified |

---

# **Conclusion**

The Requirements Traceability Matrix demonstrates complete traceability across the project lifecycle:

* **Requirements → ADPs → EDRs → KPIs → Test Cases → Verification**

This aligns with the engineering philosophy described in your uploaded framework and ensures that every architectural and implementation decision is justified, measurable, and testable.

# API Design (api003,4,5,6,7))

Excellent. Just like **TD-001** established the foundation for all technology decisions and **DB-001** established the foundation for database engineering, **API-001** should establish the architectural foundation for the entire API layer.

Notice that **API-001 is intentionally not about endpoints**. It defines the engineering principles that every endpoint must follow.

---

# **API-001 — API Architecture & Design Principles**

**Status:** API Design Phase

---

# **Objective**

Design a standardized API architecture that enables secure, scalable, maintainable, and efficient communication between the Presentation Layer and the Business Logic Layer while ensuring every API aligns with the project's engineering principles, KPIs, and subject-wise implementation.

The API layer serves as the **contract** between clients and the application, not merely as a collection of URLs.

---

# **Design Principles Applied**

* ✅ Principle 1 – Integration of Core Computer Science Subjects  
* ✅ Principle 2 – Every Design Decision Must Answer Two Questions  
* ✅ Principle 3 – Requirements Are Fixed  
* ✅ Principle 7 – KPIs Drive the Architecture  
* ✅ Principle 10 – No Accidental Decisions  
* ✅ Principle 11 – Engineering over Convenience  
* ✅ Principle 12 – Measurable Improvements

---

# **API-001 Structure**

API-001  
│  
├── API-001.1 API Architecture  
├── API-001.2 Layered Communication Model  
├── API-001.3 API Responsibilities  
├── API-001.4 Architectural Style  
├── API-001.5 Resource-Oriented Design  
├── API-001.6 API Lifecycle  
├── API-001.7 API Design Principles  
├── API-001.8 Integration with System Architecture  
├── API-001.9 Core Subject Mapping  
└── API-001.10 Engineering Benefits

---

# **API-001.1 — API Architecture**

## **Objective**

The API layer provides a controlled interface between the client applications and the backend services.

The API layer must:

* Accept client requests  
* Validate input  
* Authenticate users  
* Authorize operations  
* Invoke business services  
* Return standardized responses  
* Never contain business logic

The API is responsible for communication, **not decision-making**.

---

# **API-001.2 — Layered Communication Model**

Every request follows the same architecture.

Client (Web Application)  
          │  
          ▼  
REST API Layer  
          │  
          ▼  
Authentication & Authorization  
          │  
          ▼  
Service Layer (Business Logic)  
          │  
          ▼  
Repository / Database Access Layer  
          │  
          ▼  
PostgreSQL Database

### **Responsibilities**

| Layer | Responsibility |
| ----- | ----- |
| Client | User interaction |
| API | Request handling and response generation |
| Authentication | Identity verification |
| Service | Business rules |
| Repository | Database interaction |
| Database | Persistent storage |

---

# **API-001.3 — API Responsibilities**

The API layer is responsible for:

* Request routing  
* Input validation  
* Authentication  
* Authorization  
* Request parsing  
* Response formatting  
* Error mapping  
* Status code generation

The API layer is **not responsible** for:

* Database queries  
* Business rules  
* Evaluation algorithms  
* Concurrency management  
* Data persistence

These responsibilities belong to lower architectural layers.

---

# **API-001.4 — Architectural Style**

## **Selected Style**

**RESTful Architecture**

### **Why REST?**

| Criterion | Justification |
| ----- | ----- |
| Simplicity | Easy to understand and implement |
| Stateless | Supports scalability |
| Resource-Oriented | Maps naturally to project entities |
| HTTP Standards | Standard methods and status codes |
| Client Independence | Supports multiple frontend technologies |

### **Alternatives Considered**

| Style | Reason Not Selected |
| ----- | ----- |
| GraphQL | Added complexity beyond project requirements |
| SOAP | Heavyweight and less suitable for this application |
| gRPC | Excellent for internal services but unnecessary for browser-based clients |

---

# **API-001.5 — Resource-Oriented Design**

Every major business entity becomes an API resource.

Examples:

| Resource | Description |
| ----- | ----- |
| Users | User management |
| Roles | Role management |
| Subjects | Academic subjects |
| Exams | Examination management |
| Questions | Question bank |
| Registrations | Candidate registration |
| Attempts | Examination attempts |
| Answers | Student responses |
| Evaluations | Evaluation process |
| Results | Result publication |
| Notifications | User notifications |
| Audit Logs | Administrative auditing |

Resources represent business concepts rather than database tables.

---

# **API-001.6 — API Lifecycle**

Each request follows a consistent lifecycle.

Client Request  
        │  
        ▼  
Route Resolution  
        │  
        ▼  
Authentication  
        │  
        ▼  
Authorization  
        │  
        ▼  
Input Validation  
        │  
        ▼  
Business Service  
        │  
        ▼  
Repository  
        │  
        ▼  
Database  
        │  
        ▼  
Response Generation  
        │  
        ▼  
Client Response

This standardized flow improves consistency and simplifies debugging.

---

# **API-001.7 — API Design Principles**

Every API in the project shall follow these principles.

### **1\. Stateless Communication**

Each request contains all information necessary for processing.

Benefit:

* Better scalability  
* Easier load balancing  
* Simplified recovery

---

### **2\. Consistent URI Design**

Use nouns instead of verbs.

Good:

GET /api/v1/exams  
POST /api/v1/questions

Avoid:

/getExam  
/createQuestion

---

### **3\. Standard HTTP Methods**

| Method | Purpose |
| ----- | ----- |
| GET | Retrieve resources |
| POST | Create resources |
| PUT | Replace resources |
| PATCH | Partial update |
| DELETE | Remove (or soft-delete where applicable) |

---

### **4\. Consistent Response Structure**

Every API returns a predictable format.

Example:

{  
  "success": true,  
  "message": "Operation completed successfully",  
  "data": { },  
  "timestamp": "2026-08-04T11:00:00Z"  
}

---

### **5\. Separation of Concerns**

* API → Communication  
* Service → Business Logic  
* Repository → Persistence  
* Database → Storage

No layer bypasses another.

---

# **API-001.8 — Integration with System Architecture**

The API layer integrates with the architecture designed earlier.

Presentation Layer  
        │  
        ▼  
API Layer  
        │  
        ▼  
Service Layer  
        │  
        ▼  
Repository Layer  
        │  
        ▼  
Database Layer

It also interacts with:

* Authentication Module  
* RBAC Module  
* Logging Module  
* Notification Module  
* Audit Module

without directly implementing their internal logic.

---

# **API-001.9 — Core Subject Mapping**

| Subject | Contribution |
| ----- | ----- |
| **Computer Networks** | HTTP communication, client-server architecture, stateless request handling |
| **Software Engineering** | Layered architecture, interface contracts, modularity |
| **OOP** | Controllers, services, dependency injection, abstraction |
| **DBMS** | Structured interaction through the Repository Layer |
| **Operating Systems** | Efficient handling of concurrent requests through stateless processing |
| **DSA** | Efficient request routing and optimized processing pipelines |

---

# **API-001.10 — Engineering Benefits**

| Engineering Goal | API Contribution |
| ----- | ----- |
| Performance | Lightweight REST communication and minimized payloads |
| Scalability | Stateless architecture enables horizontal scaling |
| Maintainability | Clear separation of responsibilities |
| Reliability | Standardized request lifecycle and error handling |
| Security | Authentication and authorization before business execution |
| Testability | Independent testing of controllers, services, and repositories |
| Extensibility | New resources can be added without affecting existing APIs |

---

# **API Architecture Principles**

Every API designed in this project must satisfy the following:

1. Every endpoint corresponds to a business capability.  
2. APIs expose services, not database tables.  
3. Business logic remains in the Service Layer.  
4. Database access occurs only through the Repository Layer.  
5. Every request is authenticated unless explicitly public.  
6. Every protected operation is authorized using RBAC.  
7. Every request is validated before execution.  
8. Every response follows a common structure.  
9. Every endpoint is versioned.  
10. Every API design decision must satisfy the project's engineering principles and KPIs.

---

# **Deliverables Produced**

API-001 produces the following engineering artifacts:

* ✅ API Architecture Specification  
* ✅ Layered Communication Model  
* ✅ API Responsibility Matrix  
* ✅ REST Architecture Justification  
* ✅ Resource-Oriented Design Guidelines  
* ✅ API Lifecycle Definition  
* ✅ API Design Principles  
* ✅ System Integration Model  
* ✅ Core Subject Mapping  
* ✅ API Engineering Benefits

---

# **Measurable Improvements**

| Decision | Before | After |
| ----- | ----- | ----- |
| Communication Style | Inconsistent interfaces | Standardized REST architecture |
| Layer Separation | Mixed responsibilities | Clearly defined API, Service, Repository layers |
| Scalability | Session-dependent design | Stateless request processing |
| Maintainability | Endpoint-specific conventions | Uniform design standards |
| Security | Ad-hoc validation | Centralized authentication, authorization, and validation |

---

# **API-001 Status: Complete ✅**

API-001 establishes the architectural contract for the entire API layer. All subsequent API documents (API-002 onward) will inherit these principles, ensuring consistency across every endpoint in the Online Examination Platform.

Excellent. Now that **API-001** has established the architecture, **API-002** defines the **engineering standards** that every API in the project must follow.

Think of it this way:

* **API-001 \= Why the API layer exists**  
* **API-002 \= How every API must be designed**

This is analogous to how coding standards are established before writing code.

---

# **API-002 — API Standards & Naming Conventions**

**Status:** API Design Phase

---

# **Objective**

Establish a uniform set of standards, conventions, and design rules for every API in the Online Examination Platform to ensure:

* Consistency  
* Maintainability  
* Readability  
* Predictability  
* Scalability  
* Interoperability

API-002 serves as the **API Style Guide** for the project.

---

# **Design Principles Applied**

* ✅ Principle 1 – Integration of Core Computer Science Subjects  
* ✅ Principle 2 – Every Design Decision Must Answer Two Questions  
* ✅ Principle 7 – KPIs Drive Architecture  
* ✅ Principle 10 – No Accidental Decisions  
* ✅ Principle 11 – Engineering over Convenience

---

# **API-002 Structure**

API-002  
│  
├── API-002.1 URI Design Standards  
├── API-002.2 HTTP Method Standards  
├── API-002.3 Resource Naming Conventions  
├── API-002.4 Request Standards  
├── API-002.5 Response Standards  
├── API-002.6 HTTP Status Code Standards  
├── API-002.7 Pagination, Filtering & Sorting  
├── API-002.8 API Versioning Standards  
├── API-002.9 Documentation Standards  
└── API-002.10 API Style Guide

---

# **API-002.1 — URI Design Standards**

## **Objective**

Create clean, predictable, and resource-oriented URLs.

### **Base URL**

/api/v1

---

### **General Format**

/api/v1/{resource}

/api/v1/{resource}/{id}

/api/v1/{resource}/{id}/{sub-resource}

Examples

/api/v1/users

/api/v1/users/101

/api/v1/exams

/api/v1/exams/15

/api/v1/exams/15/questions

---

### **Rules**

✔ Use lowercase

/users

✔ Use plural resource names

/exams

/questions

/subjects

✔ Use hyphens if multiple words

/question-categories

Avoid

QuestionCategory

---

# **API-002.2 — HTTP Method Standards**

Each HTTP method has exactly one purpose.

| Method | Purpose | Safe | Idempotent |
| ----- | ----- | ----- | ----- |
| GET | Retrieve | Yes | Yes |
| POST | Create | No | No |
| PUT | Replace | No | Yes |
| PATCH | Partial Update | No | No |
| DELETE | Soft Delete / Remove | No | Yes |

---

Examples

GET /users

Retrieve users.

---

POST /questions

Create question.

---

PUT /subjects/12

Replace subject.

---

PATCH /users/4

Update profile.

---

DELETE /questions/55

Soft delete question.

---

# **API-002.3 — Resource Naming Conventions**

Every URI represents a business resource.

Good

/users

/roles

/exams

/questions

/results

Avoid

/createUser

/getExam

/deleteQuestion

The action is expressed by the HTTP method, not by the URI.

---

## **Nested Resources**

Examples

/exams/12/questions

/exams/12/results

/users/21/notifications

Maximum nesting depth:

2 Levels

Avoid deeply nested URIs.

---

# **API-002.4 — Request Standards**

## **JSON**

All request bodies use JSON.

Example

{  
  "subjectName": "Database Management Systems",  
  "subjectCode": "DBMS301"  
}

---

## **Date Format**

Use ISO-8601.

2026-08-04T10:30:00Z

---

## **Boolean**

Use

true  
false

Never

1

0

YES

NO

---

## **UUID**

Represent as strings.

Example

550e8400-e29b-41d4-a716-446655440000

---

# **API-002.5 — Response Standards**

Every API returns the same structure.

## **Success Response**

{  
    "success": true,  
    "message": "Exam created successfully.",  
    "data": {},  
    "timestamp": "2026-08-04T10:30:00Z"  
}

---

## **Error Response**

{  
    "success": false,  
    "message": "Validation failed.",  
    "errors": \[  
        {  
            "field": "examTitle",  
            "message": "Exam title is required."  
        }  
    \],  
    "timestamp": "2026-08-04T10:30:00Z"  
}

Benefits

* Predictable parsing  
* Simpler frontend development  
* Easier debugging  
* Standardized logging

---

# **API-002.6 — HTTP Status Code Standards**

| Status | Meaning | Usage |
| ----- | ----- | ----- |
| 200 | OK | Successful GET |
| 201 | Created | Resource created |
| 204 | No Content | Successful delete/update with no body |
| 400 | Bad Request | Validation failure |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Permission denied |
| 404 | Not Found | Resource missing |
| 409 | Conflict | Duplicate resource or state conflict |
| 422 | Unprocessable Entity | Business rule validation failure |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unexpected server error |

Never return `200 OK` for an operation that actually failed.

---

# **API-002.7 — Pagination, Filtering & Sorting**

Large collections should never return all records.

## **Pagination**

GET /users?page=1\&size=20

---

## **Sorting**

GET /questions?sort=difficultyLevel

---

## **Filtering**

GET /questions?subjectId=5

GET /questions?difficulty=MEDIUM

---

## **Searching**

GET /questions?keyword=network

---

Benefits

* Reduced payload size  
* Lower bandwidth  
* Faster response time  
* Better scalability

---

# **API-002.8 — API Versioning Standards**

Every endpoint is versioned.

Example

/api/v1/exams

Future

/api/v2/exams

Rules

* Never break existing clients.  
* Introduce breaking changes only in a new major version.  
* Support multiple versions during migration where required.

---

# **API-002.9 — Documentation Standards**

Every endpoint must document:

* Endpoint Name  
* Purpose  
* HTTP Method  
* URI  
* Authentication  
* Authorization  
* Request Body  
* Path Parameters  
* Query Parameters  
* Response  
* Status Codes  
* Validation Rules  
* Business Logic  
* Database Tables Used  
* Transaction Requirement  
* Performance Considerations  
* Security Considerations  
* Related Module  
* Core Subject Mapping

This becomes the project's API reference manual.

---

# **API-002.10 — API Style Guide**

Every API must satisfy the following checklist.

| Rule | Required |
| ----- | ----- |
| Resource-oriented URI | ✅ |
| Correct HTTP Method | ✅ |
| JSON Request | ✅ |
| JSON Response | ✅ |
| ISO-8601 Dates | ✅ |
| Versioned URI | ✅ |
| Standard Status Codes | ✅ |
| Authentication Supported | ✅ |
| Authorization Supported | ✅ |
| Validation Implemented | ✅ |
| Standard Error Format | ✅ |
| Pagination for Collections | ✅ |
| Documentation Complete | ✅ |

---

# **Engineering Standards Summary**

| Standard | Purpose |
| ----- | ----- |
| URI Convention | Consistency |
| HTTP Methods | Correct REST semantics |
| JSON Format | Interoperability |
| Versioning | Maintainability |
| Status Codes | Predictable error handling |
| Pagination | Scalability |
| Documentation | Maintainability |
| Naming Convention | Readability |

---

# **Core Subject Mapping**

| Subject | Contribution |
| ----- | ----- |
| **Computer Networks** | RESTful communication, HTTP standards, URI design |
| **Software Engineering** | Interface standards, documentation, consistency |
| **OOP** | Resource abstraction and modular API organization |
| **DBMS** | Standardized interaction with persistence layer |
| **DSA** | Efficient querying through pagination, filtering, and sorting |
| **Operating Systems** | Efficient resource usage by limiting payloads and supporting stateless interactions |

---

# **Measurable Improvements**

| Engineering Decision | Before | After |
| ----- | ----- | ----- |
| URI Design | Inconsistent endpoints | Uniform resource hierarchy |
| Responses | Multiple formats | Single standardized response structure |
| Error Handling | Ad-hoc responses | Consistent error contract |
| Collections | Full dataset retrieval | Paginated responses |
| API Evolution | Breaking changes | Versioned API lifecycle |

---

# **Deliverables Produced**

API-002 produces the following engineering artifacts:

* ✅ API URI Standard  
* ✅ HTTP Method Standard  
* ✅ Resource Naming Convention  
* ✅ Request & Response Specification  
* ✅ HTTP Status Code Standard  
* ✅ Pagination, Filtering & Sorting Guidelines  
* ✅ API Versioning Policy  
* ✅ API Documentation Template  
* ✅ API Style Guide

---

# **API-002 Status: Complete ✅**

With API-002 complete, every endpoint developed in subsequent API documents will follow a common engineering standard. This ensures that the entire API layer remains consistent, maintainable, scalable, and aligned with the architectural philosophy established in API-001. The remaining API documents (API-003 onward) can now focus on specific functional domains while inheriting these standards automatically.

Excellent. Now we begin the **functional API design**.

Everything before API-003 (API-001 & API-002) was generic and applies to every API. Starting from **API-003**, every document maps directly to one of the functional modules that we finalized during the Architecture Design phase.

API-003 is one of the most important documents because **every other module depends on it**.

It covers:

* User Authentication  
* Session Management  
* Role-Based Access Control (RBAC)

It does **not** cover user profile management (that belongs to API-004).

---

# **API-003 — Authentication, Session Management & RBAC APIs**

**Status:** API Design Phase

---

# **Objective**

Design a secure, scalable, and stateless API framework for:

* User Authentication  
* Session Management  
* Token Lifecycle  
* Role-Based Access Control (RBAC)

These APIs establish the identity and permissions of every user before any business functionality is accessed.

---

# **Design Principles Applied**

* ✅ Principle 1 – Integration of Core Computer Science Subjects  
* ✅ Principle 2 – Every Design Decision Must Answer Two Questions  
* ✅ Principle 7 – KPIs Drive Architecture  
* ✅ Principle 10 – No Accidental Decisions  
* ✅ Principle 11 – Engineering over Convenience

---

# **API-003 Structure**

API-003  
│  
├── API-003.1 Module Overview  
├── API-003.2 Authentication Flow  
├── API-003.3 Session Management Flow  
├── API-003.4 Role-Based Access Control (RBAC)  
├── API-003.5 Authentication Endpoints  
├── API-003.6 Session Endpoints  
├── API-003.7 Authorization Rules  
├── API-003.8 Error Handling  
├── API-003.9 Security Considerations  
└── API-003.10 Performance Considerations

---

# **API-003.1 — Module Overview**

This module is responsible for:

* User Login  
* User Logout  
* Session Creation  
* Session Validation  
* Session Termination  
* Password Management  
* Role Verification  
* Permission Validation

It **does not** manage:

* Student Profiles  
* Faculty Profiles  
* Subjects  
* Exams

Those belong to later modules.

---

# **API-003.2 — Authentication Flow**

Every login request follows the same lifecycle.

Client  
    │  
    ▼  
Login Request  
    │  
    ▼  
Input Validation  
    │  
    ▼  
User Lookup  
    │  
    ▼  
Password Verification  
    │  
    ▼  
Role Retrieval  
    │  
    ▼  
Permission Loading  
    │  
    ▼  
Session Creation  
    │  
    ▼  
Audit Logging  
    │  
    ▼  
Response

Benefits:

* Single authentication pipeline  
* Predictable execution  
* Easy auditing  
* Modular implementation

---

# **API-003.3 — Session Management Flow**

The system uses **stateless authentication with server-side session tracking**.

Login  
    │  
    ▼  
Authentication Successful  
    │  
    ▼  
Generate Access Token  
    │  
    ▼  
Create UserSession Record  
    │  
    ▼  
Return Token  
    │  
    ▼  
Authenticated Requests  
    │  
    ▼  
Logout / Expiration  
    │  
    ▼  
Invalidate Session

The `UserSession` table (defined during DB design) stores active session metadata for audit and administrative control.

---

# **API-003.4 — Role-Based Access Control (RBAC)**

Authorization is evaluated after successful authentication.

User  
   │  
   ▼  
Role  
   │  
   ▼  
Permissions  
   │  
   ▼  
Protected Resource

Example:

| Role | Permissions |
| ----- | ----- |
| Student | Take Exam, View Results |
| Faculty | Manage Questions, Evaluate Exams |
| Admin | Full System Administration |

Authorization decisions rely on the `Role`, `Permission`, and `RolePermission` tables.

---

# **API-003.5 — Authentication Endpoints**

---

## **Login**

| Property | Value |
| ----- | ----- |
| Method | POST |
| Endpoint | `/api/v1/auth/login` |
| Authentication | No |
| Authorization | Public |

### **Request**

{  
  "email": "student@example.com",  
  "password": "\*\*\*\*\*\*\*\*"  
}

### **Success Response**

{  
  "success": true,  
  "message": "Login successful.",  
  "data": {  
    "accessToken": "...",  
    "expiresIn": 3600  
  }  
}

Database Tables:

* User  
* Role  
* UserSession  
* LoginHistory

Transaction:

Yes

---

## **Logout**

| Property | Value |
| ----- | ----- |
| Method | POST |
| Endpoint | `/api/v1/auth/logout` |

Updates:

* UserSession  
* AuditLog

---

## **Validate Session**

| Property | Value |
| ----- | ----- |
| Method | GET |
| Endpoint | `/api/v1/auth/session` |

Returns:

* Session validity  
* User identity  
* Role  
* Expiration

---

## **Refresh Session / Token**

| Property | Value |
| ----- | ----- |
| Method | POST |
| Endpoint | `/api/v1/auth/refresh` |

Issues a new access token if the session is still valid.

---

## **Change Password**

| Property | Value |
| ----- | ----- |
| Method | PATCH |
| Endpoint | `/api/v1/auth/password` |

Authentication:

Required

Transaction:

Yes

---

# **API-003.6 — Session Endpoints**

| Endpoint | Purpose |
| ----- | ----- |
| GET `/api/v1/sessions` | List active sessions (Admin) |
| DELETE `/api/v1/sessions/{sessionId}` | Force terminate session |
| GET `/api/v1/sessions/current` | Retrieve current session |

These endpoints support administrative control and account security.

---

# **API-003.7 — Authorization Rules**

Every protected endpoint follows the sequence:

Receive Request  
        │  
        ▼  
Authenticate User  
        │  
        ▼  
Load Role  
        │  
        ▼  
Load Permissions  
        │  
        ▼  
Permission Check  
        │  
        ▼  
Allow / Deny

No business logic executes before authorization succeeds.

---

# **API-003.8 — Error Handling**

| Scenario | Status Code | Message |
| ----- | ----- | ----- |
| Invalid Credentials | 401 | Authentication failed |
| Expired Session | 401 | Session expired |
| Missing Token | 401 | Authentication required |
| Insufficient Permission | 403 | Access denied |
| User Disabled | 403 | Account disabled |
| Validation Failure | 400 | Invalid request |

All errors follow the standard response structure defined in API-002.

---

# **API-003.9 — Security Considerations**

* Passwords are stored only as hashes.  
* Credentials are transmitted over HTTPS.  
* Authentication tokens are signed and validated.  
* Sessions can be revoked by administrators.  
* Every login/logout generates an audit record.  
* Failed login attempts are recorded in `LoginHistory`.  
* Role and permission checks occur before service execution.  
* Sensitive endpoints require authentication.

---

# **API-003.10 — Performance Considerations**

To support project KPIs:

* Cache role-permission mappings (TD-007).  
* Reuse database connections through the connection pool (DB-008).  
* Use indexed lookups on `email` and `sessionId`.  
* Keep authentication transactions short.  
* Load permissions efficiently to avoid repeated database queries.  
* Record audit events asynchronously where appropriate to reduce request latency.

---

# **Endpoint Summary**

| Method | Endpoint | Purpose |
| ----- | ----- | ----- |
| POST | `/api/v1/auth/login` | Authenticate user |
| POST | `/api/v1/auth/logout` | Logout user |
| GET | `/api/v1/auth/session` | Validate current session |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| PATCH | `/api/v1/auth/password` | Change password |
| GET | `/api/v1/sessions` | List active sessions |
| GET | `/api/v1/sessions/current` | Current session details |
| DELETE | `/api/v1/sessions/{sessionId}` | Terminate session |

---

# **Database Tables Used**

| Table | Purpose |
| ----- | ----- |
| User | User credentials |
| Role | User role |
| Permission | Available permissions |
| RolePermission | RBAC mapping |
| UserSession | Active sessions |
| LoginHistory | Login tracking |
| AuditLog | Security audit |

---

# **Core Subject Mapping**

| Subject | Contribution |
| ----- | ----- |
| **Computer Networks** | HTTP authentication flow, stateless client-server communication |
| **Software Engineering** | Layered architecture, API contracts, modular design |
| **OOP** | Authentication services, RBAC services, controller separation |
| **DBMS** | User, session, role, and audit persistence with transactional consistency |
| **Operating Systems** | Concurrent session management, efficient resource utilization |
| **Cybersecurity** | Authentication, authorization, session security, audit logging |

---

# **Engineering Benefits**

| Engineering Goal | API Contribution |
| ----- | ----- |
| Security | Centralized authentication and authorization |
| Scalability | Stateless request processing with controlled session tracking |
| Reliability | Transactional login/logout operations |
| Maintainability | Dedicated authentication module |
| Auditability | Complete login, logout, and session history |
| Performance | Indexed authentication queries and cached permissions |

---

# **Deliverables Produced**

API-003 produces the following engineering artifacts:

* ✅ Authentication API Specification  
* ✅ Session Management API Specification  
* ✅ RBAC API Specification  
* ✅ Authentication Flow Diagram  
* ✅ Session Lifecycle Definition  
* ✅ Authorization Rules Matrix  
* ✅ Endpoint Catalog  
* ✅ Security Design Guidelines  
* ✅ Performance Guidelines

---

# **API-003 Status: Complete ✅**

API-003 establishes the security foundation for the entire application. All subsequent functional APIs (API-004 onward) assume that requests have already passed through this authentication and authorization layer, ensuring a consistent and secure execution model across the Online Examination Platform.

Excellent. Now we move from the **security foundation** to the **User Management domain**.

One important clarification before we begin:

* **API-003** answered **"Who are you?"** (Authentication, Session, RBAC)  
* **API-004** answers **"Who are the users in the system and how are they managed?"**

This separation follows the **Single Responsibility Principle (SRP)** and keeps authentication independent from user lifecycle management.

---

# **API-004 — User Management APIs**

**Status:** API Design Phase

---

# **Objective**

Design a comprehensive set of APIs for managing users throughout their lifecycle while maintaining security, data integrity, and role separation.

This module is responsible for:

* User Creation  
* User Retrieval  
* User Update  
* User Deactivation  
* User Search  
* User Status Management  
* Student Profile Management  
* Faculty Profile Management

It does **not** handle:

* Authentication (API-003)  
* Subject Management (API-005)  
* Examination Management (API-006)

---

# **Design Principles Applied**

* ✅ Principle 1 – Integration of Core Computer Science Subjects  
* ✅ Principle 2 – Every Design Decision Must Answer Two Questions  
* ✅ Principle 7 – KPIs Drive Architecture  
* ✅ Principle 10 – No Accidental Decisions  
* ✅ Principle 11 – Engineering over Convenience

---

# **API-004 Structure**

API-004  
│  
├── API-004.1 Module Overview  
├── API-004.2 User Lifecycle  
├── API-004.3 User CRUD APIs  
├── API-004.4 Student Profile APIs  
├── API-004.5 Faculty Profile APIs  
├── API-004.6 Search & Filtering APIs  
├── API-004.7 Administrative APIs  
├── API-004.8 Validation & Business Rules  
├── API-004.9 Performance Considerations  
└── API-004.10 Security Considerations

---

# **API-004.1 — Module Overview**

The User Management module maintains the master records for all system users.

Supported user categories:

* Administrator  
* Faculty  
* Student

Primary responsibilities:

* Create users  
* Maintain profiles  
* Manage account status  
* Search users  
* Retrieve user information

---

# **API-004.2 — User Lifecycle**

Every user follows the same lifecycle.

Create User  
      │  
      ▼  
Assign Role  
      │  
      ▼  
Create Profile  
      │  
      ▼  
Activate Account  
      │  
      ▼  
Profile Updates  
      │  
      ▼  
Deactivate Account

The lifecycle ensures that every user always has:

* One User record  
* One Role  
* One corresponding profile (Student or Faculty where applicable)

---

# **API-004.3 — User CRUD APIs**

## **Create User**

| Property | Value |
| ----- | ----- |
| Method | POST |
| Endpoint | `/api/v1/users` |
| Authentication | Required |
| Authorization | Admin |

### **Request**

{  
  "firstName": "Rahul",  
  "lastName": "Sharma",  
  "email": "rahul@example.com",  
  "roleId": 2  
}

### **Database Tables**

* User  
* Role  
* AuditLog

Transaction Required:

Yes

---

## **Get All Users**

| Property | Value |
| ----- | ----- |
| Method | GET |
| Endpoint | `/api/v1/users` |

Supports:

* Pagination  
* Filtering  
* Sorting

---

## **Get User by ID**

GET /api/v1/users/{userId}

---

## **Update User**

PUT /api/v1/users/{userId}

Updates:

* Personal information  
* Contact details  
* Status

Authentication:

Required

---

## **Soft Delete User**

DELETE /api/v1/users/{userId}

Implements:

Soft Delete

Database update:

isActive \= false  
deletedAt \= current\_timestamp

---

# **API-004.4 — Student Profile APIs**

Handles student-specific information.

Endpoints:

| Method | Endpoint |
| ----- | ----- |
| POST | `/api/v1/students` |
| GET | `/api/v1/students/{studentId}` |
| PUT | `/api/v1/students/{studentId}` |
| GET | `/api/v1/students` |

Tables:

* Student  
* User

Examples of managed fields:

* Enrollment Number  
* Semester  
* Department  
* Program  
* Academic Status

---

# **API-004.5 — Faculty Profile APIs**

Handles faculty-specific information.

Endpoints:

| Method | Endpoint |
| ----- | ----- |
| POST | `/api/v1/faculty` |
| GET | `/api/v1/faculty/{facultyId}` |
| PUT | `/api/v1/faculty/{facultyId}` |
| GET | `/api/v1/faculty` |

Managed information:

* Employee ID  
* Department  
* Designation  
* Qualification  
* Specialization

---

# **API-004.6 — Search & Filtering APIs**

Large user datasets require efficient searching.

Examples

Search by name

GET /api/v1/users?keyword=rahul

Search by role

GET /api/v1/users?role=faculty

Search by status

GET /api/v1/users?status=ACTIVE

Search by department

GET /api/v1/faculty?department=CSE

Search by semester

GET /api/v1/students?semester=4

Supports:

* Pagination  
* Sorting  
* Filtering

---

# **API-004.7 — Administrative APIs**

Restricted to administrators.

Examples:

Activate account

PATCH /api/v1/users/{id}/activate

Deactivate account

PATCH /api/v1/users/{id}/deactivate

Reset password

POST /api/v1/users/{id}/reset-password

Assign role

PATCH /api/v1/users/{id}/role

Lock account

PATCH /api/v1/users/{id}/lock

Unlock account

PATCH /api/v1/users/{id}/unlock

---

# **API-004.8 — Validation & Business Rules**

Validation Rules:

* Email must be unique.  
* Role must exist.  
* Student enrollment number must be unique.  
* Faculty employee ID must be unique.  
* Required fields cannot be null.  
* Deleted users cannot be updated.  
* Inactive users cannot authenticate.  
* One user can have only one active role assignment.

All validation failures return standardized error responses defined in API-002.

---

# **API-004.9 — Performance Considerations**

To meet project KPIs:

* Index email for fast lookup.  
* Index enrollment number.  
* Index employee ID.  
* Paginate all collection endpoints.  
* Cache role metadata.  
* Avoid N+1 queries by fetching profile data efficiently.  
* Support server-side filtering.

---

# **API-004.10 — Security Considerations**

Access control matrix:

| Operation | Student | Faculty | Admin |
| ----- | ----- | ----- | ----- |
| View Own Profile | ✅ | ✅ | ✅ |
| Update Own Profile | ✅ | ✅ | ✅ |
| View Other Users | ❌ | Limited | ✅ |
| Create User | ❌ | ❌ | ✅ |
| Delete User | ❌ | ❌ | ✅ |
| Reset Password | Own Only | Own Only | ✅ |
| Change Roles | ❌ | ❌ | ✅ |
| Lock/Unlock Account | ❌ | ❌ | ✅ |

Every administrative action generates an `AuditLog` entry.

---

# **Endpoint Summary**

| Method | Endpoint | Purpose |
| ----- | ----- | ----- |
| POST | `/api/v1/users` | Create user |
| GET | `/api/v1/users` | List users |
| GET | `/api/v1/users/{id}` | Get user |
| PUT | `/api/v1/users/{id}` | Update user |
| DELETE | `/api/v1/users/{id}` | Soft delete user |
| POST | `/api/v1/students` | Create student profile |
| GET | `/api/v1/students/{id}` | View student profile |
| PUT | `/api/v1/students/{id}` | Update student profile |
| POST | `/api/v1/faculty` | Create faculty profile |
| GET | `/api/v1/faculty/{id}` | View faculty profile |
| PUT | `/api/v1/faculty/{id}` | Update faculty profile |
| PATCH | `/api/v1/users/{id}/activate` | Activate account |
| PATCH | `/api/v1/users/{id}/deactivate` | Deactivate account |
| PATCH | `/api/v1/users/{id}/lock` | Lock account |
| PATCH | `/api/v1/users/{id}/unlock` | Unlock account |
| PATCH | `/api/v1/users/{id}/role` | Change role |

---

# **Database Tables Used**

| Table | Purpose |
| ----- | ----- |
| User | Master user information |
| Student | Student-specific profile |
| Faculty | Faculty-specific profile |
| Role | User roles |
| UserSession | Session validation during updates |
| AuditLog | Administrative activity logging |

---

# **Core Subject Mapping**

| Subject | Contribution |
| ----- | ----- |
| **Software Engineering** | Modular user lifecycle management, API contracts, separation of concerns |
| **OOP** | User, Student, and Faculty domain models with inheritance/composition through services |
| **DBMS** | CRUD operations, referential integrity, transactions, indexed user retrieval |
| **Computer Networks** | RESTful user management services over HTTP |
| **DSA** | Efficient searching, filtering, sorting, and pagination of user records |
| **Operating Systems** | Concurrent profile updates with transaction consistency and optimistic locking support |

---

# **Engineering Benefits**

| Engineering Goal | API Contribution |
| ----- | ----- |
| Maintainability | Dedicated user management module |
| Scalability | Paginated and filterable APIs |
| Security | Strict RBAC enforcement for administrative operations |
| Reliability | Transactional profile creation and updates |
| Performance | Indexed lookups and optimized queries |
| Auditability | Complete administrative activity tracking |

---

# **Deliverables Produced**

API-004 produces the following engineering artifacts:

* ✅ User Management API Specification  
* ✅ Student Profile API Specification  
* ✅ Faculty Profile API Specification  
* ✅ User Lifecycle Definition  
* ✅ Administrative API Catalog  
* ✅ Validation & Business Rules  
* ✅ Security & Authorization Matrix  
* ✅ Endpoint Catalog  
* ✅ Performance Guidelines

---

# **API-004 Status: Complete ✅**

API-004 completes the **User Management domain** by defining the full lifecycle of users, students, and faculty. Together with API-003, it forms the identity and access management foundation of the Online Examination Platform. All subsequent modules—Subjects, Exams, Question Bank, Examination Engine, and Results—will build upon these authenticated and managed user entities.

Excellent. Now we move into the **Academic Management Domain**.

This module manages the academic structure upon which the examination system is built. It provides the foundation for examinations, question banks, faculty assignments, and student registrations.

**Dependency Chain**

API-003 (Authentication)  
        ↓  
API-004 (User Management)  
        ↓  
API-005 (Academic & Subject Management)  
        ↓  
API-006 (Examination Management)  
        ↓  
API-007 (Question Bank)

Without subjects, semesters, departments, and academic mappings, exams cannot be created.

---

# **API-005 — Academic & Subject Management APIs**

**Status:** API Design Phase

---

# **Objective**

Design a modular and scalable API framework for managing the academic structure of the Online Examination Platform, including:

* Departments  
* Programs  
* Academic Years  
* Semesters  
* Subjects  
* Faculty-Subject Assignment  
* Student-Subject Enrollment

This module establishes the academic hierarchy used throughout the system.

---

# **Design Principles Applied**

* ✅ Principle 1 – Integration of Core Computer Science Subjects  
* ✅ Principle 2 – Every Design Decision Must Answer Two Questions  
* ✅ Principle 3 – Requirements Are Fixed  
* ✅ Principle 7 – KPIs Drive Architecture  
* ✅ Principle 10 – No Accidental Decisions  
* ✅ Principle 11 – Engineering over Convenience

---

# **API-005 Structure**

API-005  
│  
├── API-005.1 Module Overview  
├── API-005.2 Academic Hierarchy  
├── API-005.3 Subject Management APIs  
├── API-005.4 Faculty Assignment APIs  
├── API-005.5 Student Enrollment APIs  
├── API-005.6 Search & Query APIs  
├── API-005.7 Validation & Business Rules  
├── API-005.8 Performance Considerations  
├── API-005.9 Security Considerations  
└── API-005.10 Integration with Other Modules

---

# **API-005.1 — Module Overview**

This module manages all academic entities required before an examination can be scheduled.

Primary responsibilities:

* Manage departments  
* Manage programs  
* Manage semesters  
* Manage academic years  
* Manage subjects  
* Assign faculty to subjects  
* Enroll students in subjects

This module does **not** create examinations or questions. Those belong to API-006 and API-007.

---

# **API-005.2 — Academic Hierarchy**

The academic structure follows a clear hierarchy.

Department  
      │  
      ▼  
Program  
      │  
      ▼  
Academic Year  
      │  
      ▼  
Semester  
      │  
      ▼  
Subject  
      │  
      ├────────► Faculty Assignment  
      │  
      └────────► Student Enrollment

This hierarchy ensures consistency and simplifies scheduling and reporting.

---

# **API-005.3 — Subject Management APIs**

## **Create Subject**

| Property | Value |
| ----- | ----- |
| Method | POST |
| Endpoint | `/api/v1/subjects` |
| Authentication | Required |
| Authorization | Admin / Authorized Faculty |

### **Request**

{  
  "subjectCode": "CS401",  
  "subjectName": "Database Management Systems",  
  "semesterId": 4,  
  "credits": 4  
}

Database Tables:

* Subject  
* Semester  
* Department  
* AuditLog

Transaction:

Yes

---

## **Get All Subjects**

GET /api/v1/subjects

Supports:

* Pagination  
* Sorting  
* Filtering

---

## **Get Subject**

GET /api/v1/subjects/{subjectId}

---

## **Update Subject**

PUT /api/v1/subjects/{subjectId}

---

## **Deactivate Subject**

DELETE /api/v1/subjects/{subjectId}

Soft delete by updating the subject status.

---

# **API-005.4 — Faculty Assignment APIs**

Assign faculty members to subjects.

## **Assign Faculty**

| Method | POST |
| ----- | ----- |
| Endpoint | `/api/v1/subjects/{subjectId}/faculty` |

### **Request**

{  
  "facultyId": 12  
}

---

## **Remove Faculty Assignment**

DELETE /api/v1/subjects/{subjectId}/faculty/{facultyId}

---

## **List Assigned Faculty**

GET /api/v1/subjects/{subjectId}/faculty

Database Tables:

* Faculty  
* Subject  
* FacultySubjectAssignment

---

# **API-005.5 — Student Enrollment APIs**

Enroll students in subjects.

## **Enroll Student**

POST /api/v1/subjects/{subjectId}/students

Request

{  
  "studentId": 105  
}

---

## **Remove Enrollment**

DELETE /api/v1/subjects/{subjectId}/students/{studentId}

---

## **List Enrolled Students**

GET /api/v1/subjects/{subjectId}/students

---

## **Student Subject List**

GET /api/v1/students/{studentId}/subjects

Database Tables:

* Student  
* Subject  
* StudentSubjectEnrollment

---

# **API-005.6 — Search & Query APIs**

Efficient querying of academic data.

Examples:

Search by subject name

GET /api/v1/subjects?keyword=database

Search by department

GET /api/v1/subjects?department=CSE

Search by semester

GET /api/v1/subjects?semester=4

Search by faculty

GET /api/v1/faculty/{facultyId}/subjects

Search by student

GET /api/v1/students/{studentId}/subjects

Supports:

* Pagination  
* Sorting  
* Filtering

---

# **API-005.7 — Validation & Business Rules**

Validation Rules:

* Subject code must be unique.  
* Subject name is mandatory.  
* Semester must exist.  
* Department must exist.  
* Faculty must exist before assignment.  
* Student must exist before enrollment.  
* Duplicate faculty assignments are not allowed.  
* Duplicate student enrollments are not allowed.  
* Deactivated subjects cannot accept new enrollments.  
* Subject credits must be within the institution's allowed range.

All validation failures return the standardized error format defined in API-002.

---

# **API-005.8 — Performance Considerations**

To satisfy project KPIs:

* Index `subjectCode` and `subjectName`.  
* Index foreign keys (`semesterId`, `departmentId`, `facultyId`, `studentId`).  
* Paginate all list endpoints.  
* Cache frequently accessed subject metadata.  
* Use optimized joins to retrieve subject, faculty, and enrollment information in a single query.  
* Batch enrollment operations where appropriate.

---

# **API-005.9 — Security Considerations**

Access Control Matrix

| Operation | Student | Faculty | Admin |
| ----- | ----- | ----- | ----- |
| View Subjects | ✅ | ✅ | ✅ |
| Create Subject | ❌ | Limited\* | ✅ |
| Update Subject | ❌ | Assigned Only\* | ✅ |
| Delete Subject | ❌ | ❌ | ✅ |
| Assign Faculty | ❌ | ❌ | ✅ |
| Enroll Students | ❌ | Limited\* | ✅ |
| View Enrollment | Own Only | Assigned Subjects | ✅ |

\*Depending on institutional policy, authorized faculty may manage only their assigned subjects.

Every modification generates an `AuditLog` entry.

---

# **API-005.10 — Integration with Other Modules**

This module supplies academic data to multiple downstream modules.

API-005  
     │  
     ├────► API-006 Examination Management  
     │  
     ├────► API-007 Question Bank  
     │  
     ├────► API-008 Examination Execution  
     │  
     ├────► API-009 Evaluation & Results  
     │  
     └────► API-010 Notifications

Subject IDs, faculty assignments, and student enrollments become prerequisites for exam scheduling and execution.

---

# **Endpoint Summary**

| Method | Endpoint | Purpose |
| ----- | ----- | ----- |
| POST | `/api/v1/subjects` | Create subject |
| GET | `/api/v1/subjects` | List subjects |
| GET | `/api/v1/subjects/{subjectId}` | View subject |
| PUT | `/api/v1/subjects/{subjectId}` | Update subject |
| DELETE | `/api/v1/subjects/{subjectId}` | Deactivate subject |
| POST | `/api/v1/subjects/{subjectId}/faculty` | Assign faculty |
| DELETE | `/api/v1/subjects/{subjectId}/faculty/{facultyId}` | Remove faculty assignment |
| GET | `/api/v1/subjects/{subjectId}/faculty` | List assigned faculty |
| POST | `/api/v1/subjects/{subjectId}/students` | Enroll student |
| DELETE | `/api/v1/subjects/{subjectId}/students/{studentId}` | Remove enrollment |
| GET | `/api/v1/subjects/{subjectId}/students` | List enrolled students |
| GET | `/api/v1/students/{studentId}/subjects` | Student subject list |
| GET | `/api/v1/faculty/{facultyId}/subjects` | Faculty subject list |

---

# **Database Tables Used**

| Table | Purpose |
| ----- | ----- |
| Department | Academic departments |
| Program | Degree programs |
| AcademicYear | Academic sessions |
| Semester | Semester definitions |
| Subject | Subject master data |
| Faculty | Faculty information |
| Student | Student information |
| FacultySubjectAssignment | Faculty-to-subject mapping |
| StudentSubjectEnrollment | Student-to-subject mapping |
| AuditLog | Audit trail |

---

# **Core Subject Mapping**

| Subject | Contribution |
| ----- | ----- |
| **Software Engineering** | Modular academic domain design and API contracts |
| **OOP** | Domain models for Department, Program, Semester, Subject, Faculty Assignment, and Enrollment |
| **DBMS** | Referential integrity, many-to-many relationships, transactional assignments |
| **Computer Networks** | RESTful APIs for academic data exchange |
| **DSA** | Efficient searching, filtering, pagination, and indexed lookups |
| **Operating Systems** | Concurrent enrollment and assignment handling with transaction consistency |

---

# **Engineering Benefits**

| Engineering Goal | API Contribution |
| ----- | ----- |
| Maintainability | Dedicated academic management module |
| Scalability | Modular hierarchy and paginated APIs |
| Data Integrity | Controlled assignments and enrollments |
| Performance | Indexed academic queries and optimized joins |
| Security | RBAC-controlled academic administration |
| Reusability | Shared academic data for exams, question bank, and results |

---

# **Deliverables Produced**

API-005 produces:

* ✅ Academic Management API Specification  
* ✅ Subject Management API Specification  
* ✅ Faculty Assignment API Specification  
* ✅ Student Enrollment API Specification  
* ✅ Academic Hierarchy Model  
* ✅ Validation & Business Rules  
* ✅ Security & Authorization Matrix  
* ✅ Endpoint Catalog  
* ✅ Integration Model  
* ✅ Performance Guidelines

---

# **API-005 Status: Complete ✅**

API-005 establishes the complete academic structure of the Online Examination Platform. By defining subjects, academic hierarchies, faculty assignments, and student enrollments, it provides the foundational data required for **API-006 (Examination Management)** and all subsequent modules. Together, API-003 through API-005 now define the platform's **identity, user, and academic management layers**, forming the base upon which examination workflows are built.

Excellent. We now arrive at the **heart of the Online Examination Platform**.

Everything designed so far exists to support this module.

Authentication  
        ↓  
User Management  
        ↓  
Academic Management  
        ↓  
★★★★★  
Examination Management   ← API-006  
★★★★★  
        ↓  
Question Bank  
        ↓  
Examination Engine  
        ↓  
Evaluation  
        ↓  
Results

This is one of the largest API modules because it orchestrates the complete examination lifecycle.

---

# **API-006 — Examination Management APIs**

**Status:** API Design Phase

---

# **Objective**

Design a comprehensive API framework for creating, configuring, scheduling, publishing, monitoring, and managing examinations throughout their lifecycle.

The module is responsible for:

* Examination Creation  
* Examination Configuration  
* Scheduling  
* Candidate Registration  
* Examination Publication  
* Examination Status Management  
* Examination Monitoring  
* Examination Cancellation  
* Examination Archiving

This module defines **what an examination is**, but **not** how students take it (API-008) or how questions are managed (API-007).

---

# **Design Principles Applied**

* ✅ Principle 1 – Integration of Core Computer Science Subjects  
* ✅ Principle 2 – Every Design Decision Must Answer Two Questions  
* ✅ Principle 3 – Requirements Are Fixed  
* ✅ Principle 7 – KPIs Drive Architecture  
* ✅ Principle 10 – No Accidental Decisions  
* ✅ Principle 11 – Engineering over Convenience

---

# **API-006 Structure**

API-006  
│  
├── API-006.1 Module Overview  
├── API-006.2 Examination Lifecycle  
├── API-006.3 Examination CRUD APIs  
├── API-006.4 Scheduling APIs  
├── API-006.5 Candidate Registration APIs  
├── API-006.6 Publication & Status APIs  
├── API-006.7 Monitoring APIs  
├── API-006.8 Validation & Business Rules  
├── API-006.9 Performance Considerations  
├── API-006.10 Security Considerations  
└── API-006.11 Integration with Other Modules

---

# **API-006.1 — Module Overview**

This module manages every examination from creation until archival.

Responsibilities include:

* Create examinations  
* Configure examination settings  
* Assign subject  
* Assign faculty  
* Define duration  
* Configure marking scheme  
* Configure availability  
* Register candidates  
* Publish examination  
* Cancel examination  
* Archive completed examinations

---

# **API-006.2 — Examination Lifecycle**

Every examination follows the same lifecycle.

Draft  
   │  
   ▼  
Configuration  
   │  
   ▼  
Scheduling  
   │  
   ▼  
Candidate Registration  
   │  
   ▼  
Published  
   │  
   ▼  
Active  
   │  
   ▼  
Completed  
   │  
   ▼  
Evaluation  
   │  
   ▼  
Archived

Cancelled examinations exit the lifecycle after publication or scheduling.

---

# **API-006.3 — Examination CRUD APIs**

## **Create Examination**

| Property | Value |
| ----- | ----- |
| Method | POST |
| Endpoint | `/api/v1/exams` |
| Authentication | Required |
| Authorization | Admin / Faculty |

### **Request**

{  
  "title": "DBMS Mid Semester",  
  "subjectId": 5,  
  "duration": 90,  
  "totalMarks": 50,  
  "passingMarks": 20  
}

Database Tables

* Exam  
* Subject  
* Faculty  
* AuditLog

Transaction

Yes

---

## **Get All Examinations**

GET /api/v1/exams

Supports:

* Pagination  
* Filtering  
* Sorting

---

## **Get Examination**

GET /api/v1/exams/{examId}

---

## **Update Examination**

PUT /api/v1/exams/{examId}

---

## **Archive Examination**

DELETE /api/v1/exams/{examId}

Implements soft deletion by changing the examination status to `ARCHIVED`.

---

# **API-006.4 — Scheduling APIs**

Schedule when an examination will be conducted.

## **Schedule Examination**

POST /api/v1/exams/{examId}/schedule

Example Request

{  
    "startTime":"2026-09-12T10:00:00Z",  
    "endTime":"2026-09-12T11:30:00Z"  
}

---

## **Update Schedule**

PUT /api/v1/exams/{examId}/schedule

---

## **Get Schedule**

GET /api/v1/exams/{examId}/schedule

---

## **Cancel Schedule**

DELETE /api/v1/exams/{examId}/schedule

Database Tables

* Exam  
* ExamSchedule

---

# **API-006.5 — Candidate Registration APIs**

Register eligible students for an examination.

## **Register Candidate**

POST /api/v1/exams/{examId}/candidates

Request

{  
  "studentId":105  
}

---

## **Remove Candidate**

DELETE /api/v1/exams/{examId}/candidates/{studentId}

---

## **List Registered Candidates**

GET /api/v1/exams/{examId}/candidates

---

## **Student Examination List**

GET /api/v1/students/{studentId}/exams

Database Tables

* CandidateRegistration  
* Student  
* Exam

---

# **API-006.6 — Publication & Status APIs**

Examination states

Draft  
Scheduled  
Published  
Active  
Completed  
Cancelled  
Archived

Endpoints

Publish Exam

PATCH /api/v1/exams/{examId}/publish

Start Exam

PATCH /api/v1/exams/{examId}/start

Complete Exam

PATCH /api/v1/exams/{examId}/complete

Cancel Exam

PATCH /api/v1/exams/{examId}/cancel

Archive Exam

PATCH /api/v1/exams/{examId}/archive

---

# **API-006.7 — Monitoring APIs**

Administrative monitoring endpoints.

Current Active Exams

GET /api/v1/exams/active

Upcoming Exams

GET /api/v1/exams/upcoming

Completed Exams

GET /api/v1/exams/completed

Examination Statistics

GET /api/v1/exams/{examId}/statistics

Statistics may include:

* Total registered candidates  
* Present candidates  
* Absent candidates  
* Submission count  
* Completion percentage  
* Average duration

---

# **API-006.8 — Validation & Business Rules**

Business Rules

* Subject must exist.  
* Faculty must be assigned to the subject.  
* Start time must precede end time.  
* Examination title must be unique within a subject and academic term.  
* Passing marks cannot exceed total marks.  
* Duration must be greater than zero.  
* Candidate registration closes before the scheduled start time.  
* A cancelled examination cannot be published.  
* An archived examination cannot be modified.  
* Schedule conflicts for faculty or examination venues (if applicable) are not permitted.

---

# **API-006.9 — Performance Considerations**

To satisfy project KPIs:

* Index `examId`, `subjectId`, and `scheduleId`.  
* Cache examination metadata after publication.  
* Paginate examination listings.  
* Optimize candidate registration with bulk operations.  
* Use indexed schedule queries for upcoming and active examinations.  
* Maintain short transactions during registration and scheduling.

---

# **API-006.10 — Security Considerations**

| Operation | Student | Faculty | Admin |
| ----- | ----- | ----- | ----- |
| View Published Exams | ✅ | ✅ | ✅ |
| Create Exam | ❌ | Assigned Faculty | ✅ |
| Update Draft Exam | ❌ | Owner Faculty | ✅ |
| Schedule Exam | ❌ | Assigned Faculty | ✅ |
| Register Candidate | ❌ | Limited\* | ✅ |
| Publish Exam | ❌ | Assigned Faculty | ✅ |
| Cancel Exam | ❌ | ❌ | ✅ |
| Archive Exam | ❌ | ❌ | ✅ |
| View Statistics | ❌ | Assigned Faculty | ✅ |

\*Faculty permissions depend on institutional policy.

Every modification generates an `AuditLog` entry.

---

# **API-006.11 — Integration with Other Modules**

API-006  
     │  
     ├────────► API-007 Question Bank  
     │  
     ├────────► API-008 Examination Execution  
     │  
     ├────────► API-009 Evaluation & Results  
     │  
     ├────────► API-010 Notifications  
     │  
     └────────► Audit & Logging

The examination definition created here becomes the primary entity used by the remaining functional modules.

---

# **Endpoint Summary**

| Method | Endpoint | Purpose |
| ----- | ----- | ----- |
| POST | `/api/v1/exams` | Create examination |
| GET | `/api/v1/exams` | List examinations |
| GET | `/api/v1/exams/{examId}` | View examination |
| PUT | `/api/v1/exams/{examId}` | Update examination |
| DELETE | `/api/v1/exams/{examId}` | Archive examination |
| POST | `/api/v1/exams/{examId}/schedule` | Schedule examination |
| PUT | `/api/v1/exams/{examId}/schedule` | Update schedule |
| GET | `/api/v1/exams/{examId}/schedule` | View schedule |
| DELETE | `/api/v1/exams/{examId}/schedule` | Cancel schedule |
| POST | `/api/v1/exams/{examId}/candidates` | Register candidate |
| DELETE | `/api/v1/exams/{examId}/candidates/{studentId}` | Remove candidate |
| GET | `/api/v1/exams/{examId}/candidates` | List registered candidates |
| GET | `/api/v1/students/{studentId}/exams` | Student examination list |
| PATCH | `/api/v1/exams/{examId}/publish` | Publish examination |
| PATCH | `/api/v1/exams/{examId}/start` | Start examination |
| PATCH | `/api/v1/exams/{examId}/complete` | Complete examination |
| PATCH | `/api/v1/exams/{examId}/cancel` | Cancel examination |
| PATCH | `/api/v1/exams/{examId}/archive` | Archive examination |
| GET | `/api/v1/exams/active` | Active examinations |
| GET | `/api/v1/exams/upcoming` | Upcoming examinations |
| GET | `/api/v1/exams/completed` | Completed examinations |
| GET | `/api/v1/exams/{examId}/statistics` | Examination statistics |

---

# **Database Tables Used**

| Table | Purpose |
| ----- | ----- |
| Exam | Examination master record |
| ExamSchedule | Scheduling information |
| Subject | Associated subject |
| Faculty | Examination owner |
| CandidateRegistration | Registered candidates |
| Student | Candidate information |
| AuditLog | Administrative audit trail |

---

# **Core Subject Mapping**

| Subject | Contribution |
| ----- | ----- |
| **Software Engineering** | Examination lifecycle management, modular APIs, separation of concerns |
| **OOP** | Examination, Schedule, and Registration domain services |
| **DBMS** | Transactions, referential integrity, scheduling consistency, registration management |
| **Computer Networks** | RESTful APIs for examination administration |
| **DSA** | Efficient filtering, searching, scheduling, and statistics retrieval |
| **Operating Systems** | Concurrent candidate registration and examination state transitions with transactional consistency |

---

# **Engineering Benefits**

| Engineering Goal | API Contribution |
| ----- | ----- |
| Maintainability | Centralized examination management module |
| Scalability | Stateless APIs with paginated listings |
| Reliability | Controlled examination lifecycle and transactional scheduling |
| Data Integrity | Validated scheduling, registration, and status transitions |
| Performance | Indexed examination queries and optimized registration workflows |
| Security | RBAC-protected examination administration |

---

# **Deliverables Produced**

API-006 produces:

* ✅ Examination Management API Specification  
* ✅ Examination Lifecycle Model  
* ✅ Scheduling API Specification  
* ✅ Candidate Registration API Specification  
* ✅ Examination Status Management APIs  
* ✅ Monitoring & Statistics API Specification  
* ✅ Validation & Business Rules  
* ✅ Security & Authorization Matrix  
* ✅ Endpoint Catalog  
* ✅ Integration Model

---

# **API-006 Status: Complete ✅**

API-006 completes the **Examination Management domain**, defining the full lifecycle of an examination from creation through scheduling, publication, execution readiness, and archival. It provides the orchestration layer that connects the academic structure (API-005) with the Question Bank (API-007), Examination Execution (API-008), Evaluation & Results (API-009), and Notification services (API-010), making it the central coordination module of the Online Examination Platform.

Excellent. We now move to the **Question Bank Management Module**, which is one of the core modules of the Online Examination Platform.

This module manages the complete lifecycle of questions—from creation and categorization to validation, approval, versioning, and association with examinations. Unlike API-006, which manages the exam itself, API-007 manages the content that will appear in those exams.

---

# **API-007 — Question Bank Management APIs**

**Status:** API Design Phase

---

# **Objective**

Design a scalable and secure API framework for managing the centralized Question Bank, including:

* Question Creation  
* Question Update  
* Question Categorization  
* Difficulty Level Management  
* Question Approval Workflow  
* Question Versioning  
* Question Search & Filtering  
* Exam Question Mapping

This module ensures that questions are reusable, maintainable, and suitable for automated examination generation.

---

# **Design Principles Applied**

* ✅ Principle 1 – Integration of Core Computer Science Subjects  
* ✅ Principle 2 – Every Design Decision Must Answer Two Questions  
* ✅ Principle 3 – Requirements Are Fixed  
* ✅ Principle 7 – KPIs Drive Architecture  
* ✅ Principle 10 – No Accidental Decisions  
* ✅ Principle 11 – Engineering over Convenience

---

# **API-007 Structure**

API-007  
│  
├── API-007.1 Module Overview  
├── API-007.2 Question Lifecycle  
├── API-007.3 Question CRUD APIs  
├── API-007.4 Question Category & Difficulty APIs  
├── API-007.5 Question Approval & Versioning APIs  
├── API-007.6 Exam Question Mapping APIs  
├── API-007.7 Search & Query APIs  
├── API-007.8 Validation & Business Rules  
├── API-007.9 Performance Considerations  
├── API-007.10 Security Considerations  
└── API-007.11 Integration with Other Modules

---

# **API-007.1 — Module Overview**

This module manages the centralized repository of examination questions.

Primary responsibilities:

* Create questions  
* Update questions  
* Delete (soft delete) questions  
* Categorize questions  
* Assign difficulty levels  
* Maintain question versions  
* Approve questions before use  
* Map questions to examinations  
* Search and filter questions

This module does **not** conduct examinations or evaluate answers.

---

# **API-007.2 — Question Lifecycle**

Every question follows a controlled lifecycle.

Draft  
   │  
   ▼  
Review  
   │  
   ▼  
Approved  
   │  
   ▼  
Available for Exam  
   │  
   ▼  
Modified (New Version)  
   │  
   ▼  
Archived

Only **Approved** questions can be associated with examinations.

---

# **API-007.3 — Question CRUD APIs**

## **Create Question**

| Property | Value |
| ----- | ----- |
| Method | POST |
| Endpoint | `/api/v1/questions` |
| Authentication | Required |
| Authorization | Faculty / Admin |

### **Request**

{  
  "subjectId": 5,  
  "categoryId": 2,  
  "difficultyLevel": "MEDIUM",  
  "questionType": "MCQ",  
  "questionText": "Which normal form removes partial dependency?",  
  "marks": 2  
}

Database Tables:

* Question  
* Subject  
* QuestionCategory  
* AuditLog

Transaction:

Yes

---

## **Get All Questions**

GET /api/v1/questions

Supports:

* Pagination  
* Filtering  
* Sorting

---

## **Get Question**

GET /api/v1/questions/{questionId}

---

## **Update Question**

PUT /api/v1/questions/{questionId}

Updating an approved question creates a **new version** instead of modifying the original.

---

## **Archive Question**

DELETE /api/v1/questions/{questionId}

Implements soft deletion by changing the status to `ARCHIVED`.

---

# **API-007.4 — Question Category & Difficulty APIs**

## **Create Question Category**

POST /api/v1/question-categories

---

## **Update Question Category**

PUT /api/v1/question-categories/{categoryId}

---

## **List Categories**

GET /api/v1/question-categories

---

## **Difficulty Levels**

Supported values:

EASY  
MEDIUM  
HARD

Retrieve supported levels:

GET /api/v1/question-difficulties

Categories help organize questions by topics such as:

* Database  
* Networking  
* Programming  
* Operating Systems  
* Cyber Security

---

# **API-007.5 — Question Approval & Versioning APIs**

## **Submit for Review**

PATCH /api/v1/questions/{questionId}/submit

---

## **Approve Question**

PATCH /api/v1/questions/{questionId}/approve

---

## **Reject Question**

PATCH /api/v1/questions/{questionId}/reject

---

## **View Version History**

GET /api/v1/questions/{questionId}/versions

---

## **Restore Previous Version**

PATCH /api/v1/questions/{questionId}/restore/{versionId}

Database Tables:

* Question  
* QuestionVersion  
* AuditLog

---

# **API-007.6 — Exam Question Mapping APIs**

Associate approved questions with examinations.

## **Add Question to Exam**

POST /api/v1/exams/{examId}/questions

Request

{  
  "questionId": 102  
}

---

## **Remove Question from Exam**

DELETE /api/v1/exams/{examId}/questions/{questionId}

---

## **List Exam Questions**

GET /api/v1/exams/{examId}/questions

---

## **Bulk Question Assignment**

POST /api/v1/exams/{examId}/questions/bulk

Useful for importing multiple approved questions into an examination.

---

# **API-007.7 — Search & Query APIs**

Examples:

Search by keyword

GET /api/v1/questions?keyword=normalization

Search by subject

GET /api/v1/questions?subjectId=5

Search by category

GET /api/v1/questions?categoryId=3

Search by difficulty

GET /api/v1/questions?difficulty=HARD

Search by approval status

GET /api/v1/questions?status=APPROVED

Supports:

* Pagination  
* Filtering  
* Sorting

---

# **API-007.8 — Validation & Business Rules**

Business Rules:

* Subject must exist.  
* Category must exist.  
* Question text cannot be empty.  
* Marks must be greater than zero.  
* Difficulty level must be valid.  
* Approved questions cannot be edited directly.  
* Only approved questions can be assigned to exams.  
* Duplicate questions within the same subject should be prevented.  
* Archived questions cannot be reused.  
* Each question must have at least one correct answer defined before approval.

---

# **API-007.9 — Performance Considerations**

To satisfy project KPIs:

* Index `questionId`, `subjectId`, `categoryId`, and `difficultyLevel`.  
* Use full-text indexing for question searches.  
* Paginate large question collections.  
* Cache frequently accessed categories and difficulty metadata.  
* Optimize bulk question assignment operations.  
* Use efficient joins for exam-question retrieval.

---

# **API-007.10 — Security Considerations**

| Operation | Student | Faculty | Admin |
| ----- | ----- | ----- | ----- |
| View Approved Questions | ❌ | Assigned Subjects | ✅ |
| Create Question | ❌ | ✅ | ✅ |
| Update Draft Question | ❌ | Owner Faculty | ✅ |
| Submit for Review | ❌ | Owner Faculty | ✅ |
| Approve / Reject Question | ❌ | ❌ | ✅ |
| Archive Question | ❌ | ❌ | ✅ |
| Map Questions to Exam | ❌ | Assigned Faculty | ✅ |
| View Version History | ❌ | Owner Faculty | ✅ |

Every modification generates an `AuditLog` entry.

---

# **API-007.11 — Integration with Other Modules**

API-007  
     │  
     ├────────► API-006 Examination Management  
     │  
     ├────────► API-008 Examination Execution  
     │  
     ├────────► API-009 Evaluation & Results  
     │  
     ├────────► API-010 Notifications  
     │  
     └────────► Audit & Logging

Approved questions become the source of truth for examination execution and evaluation.

---

# **Endpoint Summary**

| Method | Endpoint | Purpose |
| ----- | ----- | ----- |
| POST | `/api/v1/questions` | Create question |
| GET | `/api/v1/questions` | List questions |
| GET | `/api/v1/questions/{questionId}` | View question |
| PUT | `/api/v1/questions/{questionId}` | Update question |
| DELETE | `/api/v1/questions/{questionId}` | Archive question |
| POST | `/api/v1/question-categories` | Create category |
| PUT | `/api/v1/question-categories/{categoryId}` | Update category |
| GET | `/api/v1/question-categories` | List categories |
| GET | `/api/v1/question-difficulties` | List difficulty levels |
| PATCH | `/api/v1/questions/{questionId}/submit` | Submit for review |
| PATCH | `/api/v1/questions/{questionId}/approve` | Approve question |
| PATCH | `/api/v1/questions/{questionId}/reject` | Reject question |
| GET | `/api/v1/questions/{questionId}/versions` | View version history |
| PATCH | `/api/v1/questions/{questionId}/restore/{versionId}` | Restore previous version |
| POST | `/api/v1/exams/{examId}/questions` | Add question to exam |
| DELETE | `/api/v1/exams/{examId}/questions/{questionId}` | Remove question from exam |
| GET | `/api/v1/exams/{examId}/questions` | List exam questions |
| POST | `/api/v1/exams/{examId}/questions/bulk` | Bulk assign questions |

---

# **Database Tables Used**

| Table | Purpose |
| ----- | ----- |
| Question | Question master record |
| QuestionCategory | Category definitions |
| QuestionVersion | Version history |
| ExamQuestion | Exam-question mapping |
| Subject | Subject reference |
| Faculty | Question owner |
| AuditLog | Audit trail |

---

# **Core Subject Mapping**

| Subject | Contribution |
| ----- | ----- |
| **Software Engineering** | Modular question management, approval workflow, version control |
| **OOP** | Question, Category, Version, and Mapping domain services |
| **DBMS** | Referential integrity, version persistence, many-to-many exam-question relationships |
| **Computer Networks** | RESTful APIs for question repository access |
| **DSA** | Full-text search, indexed filtering, optimized bulk operations |
| **Operating Systems** | Concurrent editing protection, transaction management, efficient resource utilization |

---

# **Engineering Benefits**

| Engineering Goal | API Contribution |
| ----- | ----- |
| Maintainability | Centralized reusable question repository |
| Scalability | Efficient search and bulk assignment capabilities |
| Data Integrity | Approval workflow and version-controlled modifications |
| Performance | Indexed searches and optimized mappings |
| Security | RBAC-controlled authoring and approval process |
| Reusability | Questions can be reused across multiple examinations |

---

# **Deliverables Produced**

API-007 produces:

* ✅ Question Bank API Specification  
* ✅ Question Lifecycle Model  
* ✅ Category & Difficulty Management APIs  
* ✅ Question Approval Workflow  
* ✅ Version Control API Specification  
* ✅ Exam Question Mapping APIs  
* ✅ Search & Filtering API Specification  
* ✅ Validation & Business Rules  
* ✅ Security & Authorization Matrix  
* ✅ Endpoint Catalog

---

# **API-007 Status: Complete ✅**

API-007 completes the **Question Bank Management domain**, providing a centralized, version-controlled repository of examination questions. Together with API-006, it enables complete examination preparation by defining both the examination structure and its content. The next module, **API-008**, will consume these definitions to manage the **live examination execution**, including question delivery, answer submission, timing, auto-save, and examination session control.

Excellent. We now enter the **runtime phase** of the Online Examination Platform.

Up to API-007, everything focused on **preparing** an examination:

* API-003 → Authentication  
* API-004 → User Management  
* API-005 → Academic Management  
* API-006 → Examination Management  
* API-007 → Question Bank

Now, **API-008** is responsible for **conducting the examination itself**. This is arguably the most critical API module because it handles the live interaction between students and the examination system.

---

# **API-008 — Examination Execution APIs**

**Status:** API Design Phase

---

# **Objective**

Design a secure, scalable, fault-tolerant API framework for conducting online examinations, including:

* Examination Session Management  
* Candidate Verification  
* Examination Launch  
* Question Delivery  
* Answer Submission  
* Auto Save  
* Time Management  
* Examination Submission  
* Session Recovery  
* Examination Monitoring

This module manages the complete examination attempt lifecycle from start to finish.

---

# **Design Principles Applied**

* ✅ Principle 1 – Integration of Core Computer Science Subjects  
* ✅ Principle 2 – Every Design Decision Must Answer Two Questions  
* ✅ Principle 3 – Requirements Are Fixed  
* ✅ Principle 7 – KPIs Drive Architecture  
* ✅ Principle 10 – No Accidental Decisions  
* ✅ Principle 11 – Engineering over Convenience  
* ✅ Principle 12 – Reliability Before Optimization

---

# **API-008 Structure**

API-008  
│  
├── API-008.1 Module Overview  
├── API-008.2 Examination Attempt Lifecycle  
├── API-008.3 Examination Session APIs  
├── API-008.4 Question Delivery APIs  
├── API-008.5 Answer Submission APIs  
├── API-008.6 Auto Save & Recovery APIs  
├── API-008.7 Timer & Submission APIs  
├── API-008.8 Validation & Business Rules  
├── API-008.9 Performance Considerations  
├── API-008.10 Security Considerations  
└── API-008.11 Integration with Other Modules

---

# **API-008.1 — Module Overview**

This module controls the execution of a live examination.

Primary responsibilities:

* Verify candidate eligibility  
* Start examination  
* Create examination attempt  
* Deliver questions  
* Receive answers  
* Auto-save responses  
* Resume interrupted sessions  
* Submit examination  
* Auto-submit on timeout  
* Record examination activity

This module does **not** evaluate answers. Evaluation belongs to API-009.

---

# **API-008.2 — Examination Attempt Lifecycle**

Every examination attempt follows a controlled lifecycle.

Candidate Verification  
          │  
          ▼  
Start Examination  
          │  
          ▼  
Create Attempt  
          │  
          ▼  
Load Questions  
          │  
          ▼  
Answer Questions  
          │  
          ▼  
Auto Save  
          │  
          ▼  
Submit Examination  
          │  
          ▼  
Attempt Completed  
          │  
          ▼  
Evaluation Queue

If a network interruption occurs:

Connection Lost  
      │  
      ▼  
Session Recovery  
      │  
      ▼  
Resume Examination

---

# **API-008.3 — Examination Session APIs**

## **Start Examination**

| Property | Value |
| ----- | ----- |
| Method | POST |
| Endpoint | `/api/v1/exams/{examId}/start` |
| Authentication | Required |
| Authorization | Registered Student |

### **Request**

{  
  "studentId": 105  
}

### **Response**

{  
  "success": true,  
  "attemptId": 501,  
  "remainingTime": 5400,  
  "status": "ACTIVE"  
}

Database Tables:

* CandidateRegistration  
* ExamAttempt  
* UserSession  
* AuditLog

Transaction:

Yes

---

## **Get Current Attempt**

GET /api/v1/exams/{examId}/attempt

Returns:

* Attempt Status  
* Remaining Time  
* Progress  
* Last Saved Timestamp

---

## **Resume Attempt**

POST /api/v1/exams/{examId}/resume

Used after network interruption or browser refresh.

---

## **End Attempt**

PATCH /api/v1/exams/{examId}/end

Marks the examination as completed.

---

# **API-008.4 — Question Delivery APIs**

## **Get Next Question**

GET /api/v1/exams/{examId}/questions/next

---

## **Get Question by Number**

GET /api/v1/exams/{examId}/questions/{questionNumber}

---

## **List All Questions**

GET /api/v1/exams/{examId}/questions

Returns only metadata:

* Question Number  
* Answer Status  
* Marked for Review

Not the complete question content, unless permitted by the exam configuration.

---

# **API-008.5 — Answer Submission APIs**

## **Save Answer**

POST /api/v1/exams/{examId}/answers

Request

{  
  "questionId": 52,  
  "selectedOption": "B"  
}

Database Tables

* StudentAnswer  
* ExamAttempt

Transaction

Yes

---

## **Update Answer**

PUT /api/v1/exams/{examId}/answers/{questionId}

---

## **Clear Answer**

DELETE /api/v1/exams/{examId}/answers/{questionId}

---

## **Mark for Review**

PATCH /api/v1/exams/{examId}/answers/{questionId}/review

---

# **API-008.6 — Auto Save & Recovery APIs**

## **Auto Save**

POST /api/v1/exams/{examId}/autosave

Automatically invoked by the client at configurable intervals (e.g., every 30–60 seconds).

---

## **Recover Session**

GET /api/v1/exams/{examId}/recovery

Returns:

* Last saved answers  
* Remaining time  
* Current question  
* Examination state

---

## **Synchronize Client State**

POST /api/v1/exams/{examId}/sync

Used after reconnection to synchronize local and server state.

---

# **API-008.7 — Timer & Submission APIs**

## **Get Remaining Time**

GET /api/v1/exams/{examId}/timer

Response

{  
  "remainingTime": 1850,  
  "status": "ACTIVE"  
}

---

## **Submit Examination**

POST /api/v1/exams/{examId}/submit

Operations performed:

* Lock attempt  
* Store final answers  
* Mark attempt completed  
* Queue evaluation  
* Generate audit entry

---

## **Auto Submission**

Automatically triggered when:

* Timer expires  
* Examination closes  
* Administrator force-submits attempt

No separate public endpoint is exposed; the server performs this action internally.

---

# **API-008.8 — Validation & Business Rules**

Business Rules

* Student must be registered for the examination.  
* Examination must be in `ACTIVE` state.  
* Only one active attempt per student per examination.  
* Answers cannot be modified after submission.  
* Timer is maintained by the server.  
* Auto-save cannot create duplicate answers.  
* Resume is allowed only within the examination window.  
* Examination automatically submits when time expires.  
* Archived or cancelled examinations cannot be started.

---

# **API-008.9 — Performance Considerations**

To satisfy project KPIs:

* Cache examination metadata during execution.  
* Minimize payload size for question delivery.  
* Batch auto-save operations where possible.  
* Use indexed lookups for attempts and answers.  
* Avoid full question reloads after every answer.  
* Keep answer save transactions short.

---

# **API-008.10 — Security Considerations**

| Operation | Student | Faculty | Admin |
| ----- | ----- | ----- | ----- |
| Start Examination | ✅ Registered Only | ❌ | ❌ |
| View Questions | During Active Attempt | Limited (Monitoring) | ✅ |
| Save Answer | ✅ | ❌ | ❌ |
| Resume Attempt | ✅ | ❌ | ❌ |
| Submit Examination | ✅ | ❌ | ❌ |
| Force Submit | ❌ | ❌ | ✅ |
| Monitor Active Attempts | ❌ | Assigned Exams | ✅ |

Security Measures:

* Server-side timer enforcement.  
* Session validation before every request.  
* Attempt locking after submission.  
* Duplicate submission prevention.  
* All examination activities recorded in `AuditLog`.

---

# **API-008.11 — Integration with Other Modules**

API-008  
     │  
     ├────────► API-006 Examination Management  
     │  
     ├────────► API-007 Question Bank  
     │  
     ├────────► API-009 Evaluation & Results  
     │  
     ├────────► API-010 Notifications  
     │  
     └────────► Audit & Logging

Once an examination is submitted, the completed attempt is passed to API-009 for evaluation.

---

# **Endpoint Summary**

| Method | Endpoint | Purpose |
| ----- | ----- | ----- |
| POST | `/api/v1/exams/{examId}/start` | Start examination |
| GET | `/api/v1/exams/{examId}/attempt` | Current attempt |
| POST | `/api/v1/exams/{examId}/resume` | Resume attempt |
| PATCH | `/api/v1/exams/{examId}/end` | End attempt |
| GET | `/api/v1/exams/{examId}/questions` | List question navigation |
| GET | `/api/v1/exams/{examId}/questions/next` | Next question |
| GET | `/api/v1/exams/{examId}/questions/{questionNumber}` | Get question |
| POST | `/api/v1/exams/{examId}/answers` | Save answer |
| PUT | `/api/v1/exams/{examId}/answers/{questionId}` | Update answer |
| DELETE | `/api/v1/exams/{examId}/answers/{questionId}` | Clear answer |
| PATCH | `/api/v1/exams/{examId}/answers/{questionId}/review` | Mark for review |
| POST | `/api/v1/exams/{examId}/autosave` | Auto-save answers |
| GET | `/api/v1/exams/{examId}/recovery` | Recover session |
| POST | `/api/v1/exams/{examId}/sync` | Synchronize client state |
| GET | `/api/v1/exams/{examId}/timer` | Remaining time |
| POST | `/api/v1/exams/{examId}/submit` | Submit examination |

---

# **Database Tables Used**

| Table | Purpose |
| ----- | ----- |
| Exam | Examination definition |
| ExamAttempt | Student examination attempts |
| StudentAnswer | Candidate responses |
| CandidateRegistration | Candidate eligibility |
| Question | Question retrieval |
| UserSession | Session validation |
| AuditLog | Activity logging |

---

# **Core Subject Mapping**

| Subject | Contribution |
| ----- | ----- |
| **Software Engineering** | Examination workflow orchestration, modular execution services |
| **OOP** | Attempt, Session, Answer, and Timer service classes |
| **DBMS** | Transactional answer persistence, attempt management, recovery mechanisms |
| **Computer Networks** | Stateless REST communication, reliable request handling, session recovery |
| **Operating Systems** | Concurrent examination sessions, timer management, synchronization, resource utilization |
| **DSA** | Efficient question navigation, progress tracking, and optimized answer retrieval |

---

# **Engineering Benefits**

| Engineering Goal | API Contribution |
| ----- | ----- |
| Reliability | Auto-save, session recovery, server-side timer enforcement |
| Scalability | Stateless APIs with efficient session tracking |
| Performance | Lightweight question delivery and optimized answer persistence |
| Security | Attempt locking, duplicate submission prevention, RBAC enforcement |
| Data Integrity | Transactional answer storage and controlled attempt lifecycle |
| User Experience | Seamless resume capability and continuous progress saving |

---

# **Deliverables Produced**

API-008 produces:

* ✅ Examination Execution API Specification  
* ✅ Examination Attempt Lifecycle  
* ✅ Session Management APIs  
* ✅ Question Delivery APIs  
* ✅ Answer Submission APIs  
* ✅ Auto Save & Recovery APIs  
* ✅ Timer & Submission APIs  
* ✅ Validation & Business Rules  
* ✅ Security & Authorization Matrix  
* ✅ Endpoint Catalog

---

# **API-008 Status: Complete ✅**

API-008 completes the **live examination execution domain**. It transforms the examination definitions from API-006 and the approved questions from API-007 into an interactive examination experience for students. Through robust session management, automatic answer persistence, recovery mechanisms, and secure submission workflows, it provides a reliable and scalable runtime environment. The next module, **API-009**, will process these submitted attempts to perform evaluation, grading, result generation, and publication.

Excellent. We now reach the **Evaluation & Result Processing Module**, which is responsible for transforming a student's submitted examination into official results.

This module begins immediately after **API-008 (Examination Execution)** completes. It processes submitted answers, calculates marks, applies grading rules, generates results, and publishes them to students and faculty.

---

# **API-009 — Evaluation & Result Management APIs**

**Status:** API Design Phase

---

# **Objective**

Design a secure, scalable, and modular API framework for evaluating examination attempts and generating official results, including:

* Automatic Evaluation  
* Manual Evaluation  
* Score Calculation  
* Grade Calculation  
* Result Generation  
* Result Publication  
* Result Review  
* Result Statistics

This module completes the academic examination lifecycle.

---

# **Design Principles Applied**

* ✅ Principle 1 – Integration of Core Computer Science Subjects  
* ✅ Principle 2 – Every Design Decision Must Answer Two Questions  
* ✅ Principle 3 – Requirements Are Fixed  
* ✅ Principle 7 – KPIs Drive Architecture  
* ✅ Principle 10 – No Accidental Decisions  
* ✅ Principle 11 – Engineering over Convenience  
* ✅ Principle 12 – Reliability Before Optimization

---

# **API-009 Structure**

API-009  
│  
├── API-009.1 Module Overview  
├── API-009.2 Evaluation Lifecycle  
├── API-009.3 Automatic Evaluation APIs  
├── API-009.4 Manual Evaluation APIs  
├── API-009.5 Result Generation APIs  
├── API-009.6 Result Publication APIs  
├── API-009.7 Analytics & Statistics APIs  
├── API-009.8 Validation & Business Rules  
├── API-009.9 Performance Considerations  
├── API-009.10 Security Considerations  
└── API-009.11 Integration with Other Modules

---

# **API-009.1 — Module Overview**

This module is responsible for converting examination attempts into official academic results.

Primary responsibilities:

* Evaluate objective questions  
* Support manual evaluation of subjective questions  
* Calculate total marks  
* Calculate percentage  
* Assign grades  
* Determine pass/fail status  
* Generate result records  
* Publish results  
* Produce examination analytics

This module **does not** conduct examinations. That responsibility belongs to API-008.

---

# **API-009.2 — Evaluation Lifecycle**

Every submitted examination follows a controlled evaluation process.

Exam Submitted  
        │  
        ▼  
Retrieve Answers  
        │  
        ▼  
Auto Evaluation  
        │  
        ▼  
Manual Evaluation (if required)  
        │  
        ▼  
Calculate Final Marks  
        │  
        ▼  
Generate Result  
        │  
        ▼  
Approve Result  
        │  
        ▼  
Publish Result

---

# **API-009.3 — Automatic Evaluation APIs**

Used for objective question types such as:

* MCQ  
* True/False  
* Multiple Select (if supported)  
* Numerical (with exact answer)

---

## **Start Automatic Evaluation**

| Property | Value |
| ----- | ----- |
| Method | POST |
| Endpoint | `/api/v1/evaluation/automatic` |
| Authentication | Required |
| Authorization | Admin / Authorized Faculty |

### **Request**

{  
  "examId": 15  
}

---

## **Evaluate Single Attempt**

POST /api/v1/evaluation/attempt/{attemptId}

Compares:

* StudentAnswer  
* CorrectAnswer

Produces:

* Obtained Marks  
* Correct Count  
* Wrong Count

---

## **Evaluation Status**

GET /api/v1/evaluation/{examId}/status

Returns:

* Pending  
* Processing  
* Completed

---

# **API-009.4 — Manual Evaluation APIs**

Required for:

* Subjective Questions  
* Essay Questions  
* Long Answer Questions  
* Programming Questions (if manual review is enabled)

---

## **Get Pending Evaluations**

GET /api/v1/evaluation/manual/pending

---

## **Evaluate Answer**

PATCH /api/v1/evaluation/manual/{answerId}

Request

{  
  "marksAwarded": 8,  
  "remarks": "Good explanation"  
}

---

## **Complete Manual Evaluation**

PATCH /api/v1/evaluation/manual/complete/{attemptId}

Marks the attempt as ready for final result generation.

---

# **API-009.5 — Result Generation APIs**

---

## **Generate Result**

POST /api/v1/results/generate

Request

{  
  "examId": 15  
}

Calculations:

* Total Marks  
* Obtained Marks  
* Percentage  
* Grade  
* Pass/Fail

Stores the finalized record in the Result table.

---

## **Get Student Result**

GET /api/v1/results/student/{studentId}

---

## **Get Examination Results**

GET /api/v1/results/exam/{examId}

---

## **Get Result by Attempt**

GET /api/v1/results/attempt/{attemptId}

---

# **API-009.6 — Result Publication APIs**

Results are not immediately visible after generation.

Publication requires explicit authorization.

---

## **Publish Results**

PATCH /api/v1/results/{examId}/publish

---

## **Hide Results**

PATCH /api/v1/results/{examId}/hide

---

## **Download Result**

GET /api/v1/results/{resultId}/download

Supported formats:

* PDF  
* CSV (Administrative export)

---

# **API-009.7 — Analytics & Statistics APIs**

---

## **Examination Statistics**

GET /api/v1/results/{examId}/statistics

Returns:

* Highest Score  
* Lowest Score  
* Average Score  
* Median  
* Standard Deviation  
* Pass Percentage  
* Fail Percentage

---

## **Grade Distribution**

GET /api/v1/results/{examId}/grades

Example:

A : 18  
B : 42  
C : 35  
D : 10  
F : 5

---

## **Subject Performance**

GET /api/v1/results/subjects/{subjectId}

Provides performance analytics across examinations for the selected subject.

---

# **API-009.8 — Validation & Business Rules**

Business Rules

* Evaluation starts only after submission.  
* Each attempt can be evaluated only once unless re-evaluation is authorized.  
* Results cannot be published before all evaluations are complete.  
* Marks awarded cannot exceed maximum marks.  
* Grades are derived from the configured grading policy.  
* Hidden results remain inaccessible to students.  
* Archived examinations cannot be re-evaluated without administrative approval.  
* Every evaluation action is logged.

---

# **API-009.9 — Performance Considerations**

To satisfy project KPIs:

* Batch evaluate objective answers.  
* Index `attemptId`, `examId`, `studentId`, and `resultId`.  
* Cache grading policy.  
* Optimize aggregate calculations for statistics.  
* Generate reports asynchronously for large cohorts.  
* Support parallel evaluation of independent attempts.

---

# **API-009.10 — Security Considerations**

| Operation | Student | Faculty | Admin |
| ----- | ----- | ----- | ----- |
| View Own Result | ✅ After Publication | ❌ | ✅ |
| View All Results | ❌ | Assigned Exams | ✅ |
| Start Auto Evaluation | ❌ | Assigned Faculty | ✅ |
| Manual Evaluation | ❌ | Assigned Faculty | ✅ |
| Publish Results | ❌ | ❌ | ✅ |
| Download Own Result | ✅ After Publication | ❌ | ✅ |
| View Statistics | ❌ | Assigned Exams | ✅ |
| Re-evaluate Attempt | ❌ | With Approval | ✅ |

Security Measures:

* RBAC enforcement.  
* Immutable result records after publication (except authorized re-evaluation).  
* Full audit logging for evaluation and publication.  
* Digital integrity checks before publishing official results.

---

# **API-009.11 — Integration with Other Modules**

API-009  
     │  
     ├────────► API-008 Examination Execution  
     │  
     ├────────► API-010 Notification Service  
     │  
     ├────────► Reporting Module  
     │  
     ├────────► Audit & Logging  
     │  
     └────────► Student Dashboard

Published results trigger notifications and become available on the student and faculty dashboards.

---

# **Endpoint Summary**

| Method | Endpoint | Purpose |
| ----- | ----- | ----- |
| POST | `/api/v1/evaluation/automatic` | Start automatic evaluation |
| POST | `/api/v1/evaluation/attempt/{attemptId}` | Evaluate single attempt |
| GET | `/api/v1/evaluation/{examId}/status` | Evaluation status |
| GET | `/api/v1/evaluation/manual/pending` | Pending manual evaluations |
| PATCH | `/api/v1/evaluation/manual/{answerId}` | Grade subjective answer |
| PATCH | `/api/v1/evaluation/manual/complete/{attemptId}` | Complete manual evaluation |
| POST | `/api/v1/results/generate` | Generate results |
| GET | `/api/v1/results/student/{studentId}` | Student results |
| GET | `/api/v1/results/exam/{examId}` | Examination results |
| GET | `/api/v1/results/attempt/{attemptId}` | Result by attempt |
| PATCH | `/api/v1/results/{examId}/publish` | Publish results |
| PATCH | `/api/v1/results/{examId}/hide` | Hide results |
| GET | `/api/v1/results/{resultId}/download` | Download result |
| GET | `/api/v1/results/{examId}/statistics` | Examination statistics |
| GET | `/api/v1/results/{examId}/grades` | Grade distribution |
| GET | `/api/v1/results/subjects/{subjectId}` | Subject performance analytics |

---

# **Database Tables Used**

| Table | Purpose |
| ----- | ----- |
| ExamAttempt | Completed examination attempts |
| StudentAnswer | Candidate responses |
| Question | Correct answers and marking scheme |
| Result | Final result records |
| GradePolicy | Grade boundaries and grading rules |
| AuditLog | Evaluation and publication logs |

---

# **Core Subject Mapping**

| Subject | Contribution |
| ----- | ----- |
| **Software Engineering** | Modular evaluation pipeline, result publication workflow |
| **OOP** | Evaluation, Result, Grade, and Analytics service classes |
| **DBMS** | Transactional result generation, grading persistence, aggregate queries |
| **Computer Networks** | RESTful evaluation and result services |
| **Operating Systems** | Parallel evaluation jobs, concurrent processing, asynchronous report generation |
| **DSA** | Efficient score calculation, ranking, statistical aggregation, and analytics |

---

# **Engineering Benefits**

| Engineering Goal | API Contribution |
| ----- | ----- |
| Reliability | Controlled evaluation and publication workflow |
| Scalability | Batch processing and parallel evaluation |
| Performance | Indexed lookups and optimized statistical queries |
| Data Integrity | Immutable published results with controlled re-evaluation |
| Security | RBAC-protected evaluation and publication |
| Transparency | Complete audit trail and detailed performance analytics |

---

# **Deliverables Produced**

API-009 produces:

* ✅ Evaluation API Specification  
* ✅ Automatic Evaluation APIs  
* ✅ Manual Evaluation APIs  
* ✅ Result Generation APIs  
* ✅ Result Publication APIs  
* ✅ Analytics & Statistics APIs  
* ✅ Evaluation Lifecycle Model  
* ✅ Validation & Business Rules  
* ✅ Security & Authorization Matrix  
* ✅ Endpoint Catalog

---

# **API-009 Status: Complete ✅**

API-009 completes the **Evaluation & Result Management domain**, transforming submitted examination attempts into officially published academic results. It combines automated and manual evaluation workflows, supports scalable result generation, and provides comprehensive analytics for students, faculty, and administrators. Together with API-008, it completes the full examination execution pipeline—from exam participation to certified result publication. The next module, **API-010**, will provide the platform-wide **Notification & Communication Service**, enabling event-driven notifications for examinations, results, and administrative activities.

Excellent. We now complete the **Core Functional API Layer** of the Online Examination Platform.

API-010 is a **cross-cutting service**. Unlike the previous modules, it is not tied to a single business domain. Instead, it provides communication services that are consumed by every major module in the system.

API-003 Authentication  
          │  
API-004 User Management  
          │  
API-005 Academic Management  
          │  
API-006 Examination Management  
          │  
API-007 Question Bank  
          │  
API-008 Examination Execution  
          │  
API-009 Evaluation & Results  
          │  
          ▼  
★★★★★  
API-010 Notification & Communication Service  
★★★★★

Every important event generated by the system can trigger notifications through this module.

---

# **API-010 — Notification & Communication APIs**

**Status:** API Design Phase

---

# **Objective**

Design a centralized notification and communication framework responsible for delivering system-generated messages to students, faculty, and administrators.

The module handles:

* In-App Notifications  
* Email Notifications  
* SMS Notifications (Optional)  
* Examination Alerts  
* Result Notifications  
* Password & Security Notifications  
* System Announcements  
* Notification Preferences  
* Notification History

This module follows an **event-driven architecture**, where other modules publish events and the Notification Service processes and delivers them asynchronously.

---

# **Design Principles Applied**

* ✅ Principle 1 – Integration of Core Computer Science Subjects  
* ✅ Principle 2 – Every Design Decision Must Answer Two Questions  
* ✅ Principle 7 – KPIs Drive Architecture  
* ✅ Principle 10 – No Accidental Decisions  
* ✅ Principle 11 – Engineering over Convenience  
* ✅ Principle 12 – Reliability Before Optimization

---

# **API-010 Structure**

API-010  
│  
├── API-010.1 Module Overview  
├── API-010.2 Notification Lifecycle  
├── API-010.3 Notification APIs  
├── API-010.4 Announcement APIs  
├── API-010.5 User Preference APIs  
├── API-010.6 Notification History APIs  
├── API-010.7 Event Publishing APIs  
├── API-010.8 Validation & Business Rules  
├── API-010.9 Performance Considerations  
├── API-010.10 Security Considerations  
└── API-010.11 Integration with Other Modules

---

# **API-010.1 — Module Overview**

This module provides centralized communication across the platform.

Responsibilities:

* Send notifications  
* Deliver examination reminders  
* Publish result announcements  
* Notify password changes  
* Notify examination schedule changes  
* Store notification history  
* Manage notification preferences  
* Broadcast system announcements

The Notification Service is stateless and processes events generated by other modules.

---

# **API-010.2 — Notification Lifecycle**

System Event  
      │  
      ▼  
Notification Created  
      │  
      ▼  
Delivery Queue  
      │  
      ▼  
Channel Selection  
      │  
      ▼  
Notification Sent  
      │  
      ▼  
Delivery Confirmation  
      │  
      ▼  
Notification Archived

If delivery fails:

Notification Failed  
        │  
        ▼  
Retry Queue  
        │  
        ▼  
Resend

---

# **API-010.3 — Notification APIs**

## **Send Notification**

| Property | Value |
| ----- | ----- |
| Method | POST |
| Endpoint | `/api/v1/notifications` |
| Authentication | Required |
| Authorization | System / Admin |

### **Request**

{  
  "userId":105,  
  "type":"EMAIL",  
  "title":"Exam Scheduled",  
  "message":"Your DBMS Mid Semester exam has been scheduled."  
}

Database Tables

* Notification  
* User  
* AuditLog

Transaction

Yes

---

## **Get User Notifications**

GET /api/v1/notifications

Returns notifications belonging to the authenticated user.

Supports:

* Pagination  
* Sorting  
* Filtering

---

## **Get Notification**

GET /api/v1/notifications/{notificationId}

---

## **Mark Notification as Read**

PATCH /api/v1/notifications/{notificationId}/read

---

## **Delete Notification**

DELETE /api/v1/notifications/{notificationId}

Implements soft deletion.

---

# **API-010.4 — Announcement APIs**

Announcements target multiple users simultaneously.

---

## **Create Announcement**

POST /api/v1/announcements

Example

{  
  "title":"Semester Examination Notice",  
  "audience":"STUDENTS",  
  "message":"Semester examinations begin next Monday."  
}

---

## **Update Announcement**

PUT /api/v1/announcements/{announcementId}

---

## **Publish Announcement**

PATCH /api/v1/announcements/{announcementId}/publish

---

## **View Announcements**

GET /api/v1/announcements

---

# **API-010.5 — User Preference APIs**

Users can configure notification preferences.

---

## **Get Preferences**

GET /api/v1/notification-preferences

---

## **Update Preferences**

PUT /api/v1/notification-preferences

Example

{  
  "email":true,  
  "inApp":true,  
  "sms":false  
}

---

# **API-010.6 — Notification History APIs**

Retrieve historical notification data.

---

## **Notification History**

GET /api/v1/notifications/history

---

## **Notification Statistics**

GET /api/v1/notifications/statistics

Example statistics:

* Total Sent  
* Total Delivered  
* Failed Notifications  
* Read Rate  
* Delivery Rate

---

# **API-010.7 — Event Publishing APIs**

Other modules publish domain events to this service.

Examples:

Exam Published  
Exam Cancelled  
Exam Starting Soon  
Exam Submitted  
Evaluation Completed  
Result Published  
Password Changed  
Account Locked  
New Announcement

Internal endpoint:

POST /internal/events

This endpoint is consumed only by trusted internal services and is not exposed to end users.

---

# **API-010.8 — Validation & Business Rules**

Business Rules

* User must exist before notification delivery.  
* Notification type must be supported.  
* Deleted users do not receive notifications.  
* Delivery channels respect user preferences.  
* Failed notifications are retried according to retry policy.  
* Announcements require publication before becoming visible.  
* Notification history cannot be modified by end users.  
* Duplicate notifications for the same event should be prevented within a configurable time window.

---

# **API-010.9 — Performance Considerations**

To satisfy project KPIs:

* Use asynchronous delivery queues.  
* Batch notifications for large audiences.  
* Index `userId`, `notificationId`, and `createdAt`.  
* Cache user notification preferences.  
* Paginate notification history.  
* Retry failed deliveries using exponential backoff.  
* Separate notification processing workers from API servers.

---

# **API-010.10 — Security Considerations**

| Operation | Student | Faculty | Admin |
| ----- | ----- | ----- | ----- |
| View Own Notifications | ✅ | ✅ | ✅ |
| Mark as Read | ✅ Own | ✅ Own | ✅ |
| Delete Own Notification | ✅ | ✅ | ✅ |
| Create Announcement | ❌ | ❌ | ✅ |
| Publish Announcement | ❌ | ❌ | ✅ |
| View Statistics | ❌ | ❌ | ✅ |
| Publish Internal Event | ❌ | ❌ | Internal Services Only |

Security Measures:

* RBAC for announcements.  
* User isolation for notification history.  
* Internal event endpoint protected with service authentication.  
* All notification and announcement actions logged in `AuditLog`.

---

# **API-010.11 — Integration with Other Modules**

API-003 Authentication  
          │  
          ├────────► Login Alerts  
          │  
API-004 User Management  
          ├────────► Password Reset  
          ├────────► Account Activation  
          │  
API-005 Academic Management  
          ├────────► Subject Assignment  
          │  
API-006 Examination Management  
          ├────────► Exam Scheduled  
          ├────────► Exam Published  
          ├────────► Exam Cancelled  
          │  
API-007 Question Bank  
          ├────────► Question Approval  
          │  
API-008 Examination Execution  
          ├────────► Exam Started  
          ├────────► Submission Confirmation  
          │  
API-009 Evaluation  
          ├────────► Result Published  
          │  
          ▼  
Notification Service

---

# **Endpoint Summary**

| Method | Endpoint | Purpose |
| ----- | ----- | ----- |
| POST | `/api/v1/notifications` | Send notification |
| GET | `/api/v1/notifications` | User notifications |
| GET | `/api/v1/notifications/{notificationId}` | View notification |
| PATCH | `/api/v1/notifications/{notificationId}/read` | Mark as read |
| DELETE | `/api/v1/notifications/{notificationId}` | Delete notification |
| POST | `/api/v1/announcements` | Create announcement |
| PUT | `/api/v1/announcements/{announcementId}` | Update announcement |
| PATCH | `/api/v1/announcements/{announcementId}/publish` | Publish announcement |
| GET | `/api/v1/announcements` | View announcements |
| GET | `/api/v1/notification-preferences` | View preferences |
| PUT | `/api/v1/notification-preferences` | Update preferences |
| GET | `/api/v1/notifications/history` | Notification history |
| GET | `/api/v1/notifications/statistics` | Notification statistics |
| POST | `/internal/events` | Internal event publishing |

---

# **Database Tables Used**

| Table | Purpose |
| ----- | ----- |
| Notification | User notifications |
| NotificationPreference | User delivery preferences |
| Announcement | System announcements |
| User | Recipient information |
| AuditLog | Notification audit trail |

---

# **Core Subject Mapping**

| Subject | Contribution |
| ----- | ----- |
| **Software Engineering** | Event-driven notification architecture, modular communication services |
| **OOP** | Notification, Announcement, Preference, and Event service classes |
| **DBMS** | Persistent notification storage, delivery tracking, preference management |
| **Computer Networks** | REST APIs, asynchronous communication, message delivery |
| **Operating Systems** | Background workers, queues, concurrent event processing |
| **DSA** | Efficient queue management, filtering, notification retrieval, retry scheduling |

---

# **Engineering Benefits**

| Engineering Goal | API Contribution |
| ----- | ----- |
| Reliability | Retry mechanisms and delivery confirmation |
| Scalability | Asynchronous event-driven processing |
| Performance | Queue-based delivery and batched notifications |
| Maintainability | Centralized communication service |
| Security | RBAC-controlled announcements and user isolation |
| Extensibility | New notification channels can be added without changing business modules |

---

# **Deliverables Produced**

API-010 produces:

* ✅ Notification Service API Specification  
* ✅ Announcement Management APIs  
* ✅ Notification Preference APIs  
* ✅ Notification History APIs  
* ✅ Event Publishing Interface  
* ✅ Notification Lifecycle Model  
* ✅ Validation & Business Rules  
* ✅ Security & Authorization Matrix  
* ✅ Endpoint Catalog  
* ✅ Event-Driven Integration Model

---

# **API-010 Status: Complete ✅**

API-010 completes the **Core Functional API Layer** of the Online Examination Platform. It introduces a centralized, event-driven communication service that integrates with every major module—from authentication and examination scheduling to evaluation and result publication. By decoupling notification delivery from business logic, it improves scalability, maintainability, and reliability while providing a consistent communication framework for the entire platform.

## **API Design Phase Progress**

At this point, the primary functional API design is complete:

* ✅ API-001 — API Architecture & Standards  
* ✅ API-002 — Common Response, Error Handling & Validation  
* ✅ API-003 — Authentication & Authorization  
* ✅ API-004 — User Management  
* ✅ API-005 — Academic & Subject Management  
* ✅ API-006 — Examination Management  
* ✅ API-007 — Question Bank Management  
* ✅ API-008 — Examination Execution  
* ✅ API-009 — Evaluation & Result Management  
* ✅ API-010 — Notification & Communication

The remaining API specifications can now focus on **cross-cutting and advanced capabilities**, such as reporting & analytics, audit & logging, file management, system administration, and the AI-based proctoring module that you intentionally planned to build last.

Excellent. We have now completed the **10 Core Functional API Specifications**.

From this point onward, we move into the **Enterprise Services Layer**. These APIs are not directly involved in conducting examinations but are essential for making the platform production-ready, maintainable, scalable, and enterprise-grade.

The order is:

API-001  API Standards  
API-002  Common Response & Error Handling  
API-003  Authentication & Authorization  
API-004  User Management  
API-005  Academic Management  
API-006  Examination Management  
API-007  Question Bank  
API-008  Examination Execution  
API-009  Evaluation & Results  
API-010  Notification Service  
──────────────────────────────────  
API-011  Reporting & Analytics   ← Current  
API-012  Audit & Logging  
API-013  File & Document Management  
API-014  System Administration  
API-015  AI Proctoring (Final Module)

---

# **API-011 — Reporting & Analytics APIs**

**Status:** API Design Phase

---

# **Objective**

Design a centralized Reporting & Analytics service responsible for generating operational, academic, administrative, and performance reports from data produced across the Online Examination Platform.

This module provides:

* Examination Reports  
* Student Performance Reports  
* Faculty Reports  
* Subject-wise Reports  
* Attendance Reports  
* Result Analytics  
* Dashboard Statistics  
* Data Export  
* Report Scheduling

Unlike API-009, which generates **individual results**, API-011 analyzes **large datasets** to produce insights and institutional reports.

---

# **Design Principles Applied**

* ✅ Principle 1 – Integration of Core Computer Science Subjects  
* ✅ Principle 2 – Every Design Decision Must Answer Two Questions  
* ✅ Principle 7 – KPIs Drive Architecture  
* ✅ Principle 10 – No Accidental Decisions  
* ✅ Principle 11 – Engineering over Convenience  
* ✅ Principle 12 – Reliability Before Optimization

---

# **API-011 Structure**

API-011  
│  
├── API-011.1 Module Overview  
├── API-011.2 Report Lifecycle  
├── API-011.3 Dashboard APIs  
├── API-011.4 Examination Report APIs  
├── API-011.5 Student Performance APIs  
├── API-011.6 Faculty & Subject Analytics APIs  
├── API-011.7 Export & Scheduled Reports  
├── API-011.8 Validation & Business Rules  
├── API-011.9 Performance Considerations  
├── API-011.10 Security Considerations  
└── API-011.11 Integration with Other Modules

---

# **API-011.1 — Module Overview**

The Reporting module converts operational data into actionable information.

Responsibilities include:

* Generate examination reports  
* Generate student performance reports  
* Generate faculty workload reports  
* Generate subject-wise analytics  
* Generate institutional statistics  
* Export reports  
* Schedule recurring reports  
* Feed administrative dashboards

This module is read-heavy and optimized for analytics rather than transactional updates.

---

# **API-011.2 — Report Lifecycle**

Data Generated  
      │  
      ▼  
Data Aggregation  
      │  
      ▼  
Report Generation  
      │  
      ▼  
Export / Dashboard  
      │  
      ▼  
Archive

For scheduled reports:

Schedule Created  
      │  
      ▼  
Background Job  
      │  
      ▼  
Generate Report  
      │  
      ▼  
Notify User

---

# **API-011.3 — Dashboard APIs**

## **Dashboard Summary**

| Property | Value |
| ----- | ----- |
| Method | GET |
| Endpoint | `/api/v1/dashboard` |
| Authentication | Required |

Returns summary metrics such as:

{  
  "totalStudents": 850,  
  "totalFaculty": 42,  
  "activeExams": 6,  
  "completedExams": 120,  
  "publishedResults": 118  
}

---

## **Examination Dashboard**

GET /api/v1/dashboard/examinations

Displays:

* Active examinations  
* Upcoming examinations  
* Scheduled examinations  
* Cancelled examinations

---

## **Result Dashboard**

GET /api/v1/dashboard/results

Displays:

* Published results  
* Pending evaluations  
* Average score  
* Pass percentage

---

# **API-011.4 — Examination Report APIs**

## **Examination Report**

GET /api/v1/reports/examinations/{examId}

Contains:

* Registered candidates  
* Appeared candidates  
* Absent candidates  
* Submission statistics  
* Completion rate  
* Average score  
* Highest score  
* Lowest score

---

## **Examination Attendance**

GET /api/v1/reports/examinations/{examId}/attendance

---

## **Examination Summary**

GET /api/v1/reports/examinations

Supports:

* Pagination  
* Filtering  
* Academic Year  
* Semester  
* Subject

---

# **API-011.5 — Student Performance APIs**

## **Student Performance Report**

GET /api/v1/reports/students/{studentId}

Includes:

* Examination history  
* Subject-wise marks  
* Percentage  
* Grade history  
* Attendance  
* Overall performance trend

---

## **Rank List**

GET /api/v1/reports/rank-list

Supports filters:

* Semester  
* Subject  
* Examination

---

## **Performance Trend**

GET /api/v1/reports/students/{studentId}/trend

Shows historical improvement across semesters.

---

# **API-011.6 — Faculty & Subject Analytics APIs**

## **Faculty Report**

GET /api/v1/reports/faculty/{facultyId}

Includes:

* Subjects handled  
* Examinations conducted  
* Questions created  
* Evaluation workload

---

## **Subject Analytics**

GET /api/v1/reports/subjects/{subjectId}

Displays:

* Pass percentage  
* Failure rate  
* Average marks  
* Grade distribution  
* Difficulty analysis

---

## **Institution Statistics**

GET /api/v1/reports/institution

Institution-wide analytics.

---

# **API-011.7 — Export & Scheduled Reports**

## **Export Report**

GET /api/v1/reports/export

Supported formats:

* PDF  
* Excel (XLSX)  
* CSV

---

## **Schedule Report**

POST /api/v1/reports/schedule

Example

{  
  "reportType":"Institution Summary",  
  "frequency":"MONTHLY"  
}

---

## **Scheduled Reports**

GET /api/v1/reports/schedule

---

## **Delete Scheduled Report**

DELETE /api/v1/reports/schedule/{scheduleId}

---

# **API-011.8 — Validation & Business Rules**

Business Rules

* Reports are generated only for authorized users.  
* Archived data remains available for reporting.  
* Large reports are generated asynchronously.  
* Scheduled reports follow configured recurrence rules.  
* Ranking calculations use published results only.  
* Hidden results are excluded from student-facing reports.  
* Exported reports include generation timestamp and requesting user.

---

# **API-011.9 — Performance Considerations**

To satisfy project KPIs:

* Use materialized summary tables for heavy analytics.  
* Cache dashboard metrics.  
* Paginate all report listings.  
* Generate large reports asynchronously.  
* Use indexed aggregate queries.  
* Precompute commonly requested statistics during off-peak hours.

---

# **API-011.10 — Security Considerations**

| Operation | Student | Faculty | Admin |
| ----- | ----- | ----- | ----- |
| View Own Performance | ✅ | ❌ | ✅ |
| View Examination Report | ❌ | Assigned Exams | ✅ |
| View Faculty Report | ❌ | Own Only | ✅ |
| View Institution Report | ❌ | ❌ | ✅ |
| Export Reports | Own Reports | Assigned Reports | ✅ |
| Schedule Reports | ❌ | Limited | ✅ |

Security Measures:

* RBAC enforcement.  
* Data filtering based on user role.  
* Export actions logged in `AuditLog`.  
* Personally identifiable information included only where authorized.

---

# **API-011.11 — Integration with Other Modules**

API-004 User Management  
          │  
API-005 Academic Management  
          │  
API-006 Examination Management  
          │  
API-007 Question Bank  
          │  
API-008 Examination Execution  
          │  
API-009 Evaluation & Results  
          │  
          ▼  
Reporting & Analytics  
          │  
          ▼  
Dashboards / Exports / Institutional Reports

---

# **Endpoint Summary**

| Method | Endpoint | Purpose |
| ----- | ----- | ----- |
| GET | `/api/v1/dashboard` | Dashboard summary |
| GET | `/api/v1/dashboard/examinations` | Examination dashboard |
| GET | `/api/v1/dashboard/results` | Result dashboard |
| GET | `/api/v1/reports/examinations/{examId}` | Examination report |
| GET | `/api/v1/reports/examinations/{examId}/attendance` | Attendance report |
| GET | `/api/v1/reports/examinations` | Examination summary |
| GET | `/api/v1/reports/students/{studentId}` | Student performance |
| GET | `/api/v1/reports/students/{studentId}/trend` | Performance trend |
| GET | `/api/v1/reports/rank-list` | Rank list |
| GET | `/api/v1/reports/faculty/{facultyId}` | Faculty report |
| GET | `/api/v1/reports/subjects/{subjectId}` | Subject analytics |
| GET | `/api/v1/reports/institution` | Institution analytics |
| GET | `/api/v1/reports/export` | Export report |
| POST | `/api/v1/reports/schedule` | Schedule report |
| GET | `/api/v1/reports/schedule` | Scheduled reports |
| DELETE | `/api/v1/reports/schedule/{scheduleId}` | Delete scheduled report |

---

# **Database Tables Used**

| Table | Purpose |
| ----- | ----- |
| Report | Report metadata and generation history |
| ReportSchedule | Scheduled report definitions |
| Result | Academic performance data |
| Exam | Examination information |
| Student | Student data |
| Faculty | Faculty data |
| Subject | Subject analytics |
| AuditLog | Export and reporting logs |

---

# **Core Subject Mapping**

| Subject | Contribution |
| ----- | ----- |
| **Software Engineering** | Modular reporting services, scheduled report architecture |
| **OOP** | Report, Dashboard, Analytics, and Export service classes |
| **DBMS** | Aggregate queries, views, indexing, reporting schema |
| **Computer Networks** | RESTful reporting APIs and export services |
| **Operating Systems** | Background report generation, scheduling, concurrent analytics jobs |
| **DSA** | Ranking algorithms, statistical computations, efficient sorting and aggregation |

---

# **Engineering Benefits**

| Engineering Goal | API Contribution |
| ----- | ----- |
| Decision Support | Institution-wide analytics and dashboards |
| Performance | Cached summaries and asynchronous report generation |
| Scalability | Scheduled jobs and optimized aggregate queries |
| Maintainability | Centralized reporting service |
| Security | Role-based access to reports and exports |
| Extensibility | Easy addition of new report templates and analytics |

---

# **Deliverables Produced**

API-011 produces:

* ✅ Reporting & Analytics API Specification  
* ✅ Dashboard APIs  
* ✅ Examination Reporting APIs  
* ✅ Student Performance APIs  
* ✅ Faculty & Subject Analytics APIs  
* ✅ Report Export & Scheduling APIs  
* ✅ Report Lifecycle Model  
* ✅ Validation & Business Rules  
* ✅ Security & Authorization Matrix  
* ✅ Endpoint Catalog

---

# **API-011 Status: Complete ✅**

API-011 completes the **Reporting & Analytics domain** by providing comprehensive dashboards, institutional reports, performance analytics, ranking, and export capabilities. It transforms operational data collected by the previous modules into actionable insights for students, faculty, administrators, and institutional decision-makers.

**Next:** **API-012 – Audit Logging & System Monitoring**, which will define centralized auditing, activity tracking, security event logging, system health monitoring, and operational observability for the entire platform.

Excellent. We now move into one of the most important enterprise modules of the Online Examination Platform.

Unlike Reporting (API-011), which is intended for business intelligence, **API-012** focuses on **security, accountability, traceability, compliance, and operational monitoring**.

In any production-grade examination platform, every significant action must be traceable. This module provides the audit trail required for troubleshooting, compliance, forensic analysis, and system health monitoring.

---

# **API-012 — Audit Logging & System Monitoring APIs**

**Status:** API Design Phase

---

# **Objective**

Design a centralized Audit Logging & System Monitoring service responsible for recording user activities, security events, administrative actions, and system health metrics across the Online Examination Platform.

This module provides:

* Audit Logging  
* User Activity Tracking  
* Security Event Logging  
* System Event Logging  
* Error Logging  
* Login History  
* API Request Logs  
* System Health Monitoring  
* Performance Monitoring  
* Operational Dashboards

Unlike API-010 (Notification Service), which communicates events, API-012 permanently records and monitors them.

---

# **Design Principles Applied**

* ✅ Principle 1 – Integration of Core Computer Science Subjects  
* ✅ Principle 2 – Every Design Decision Must Answer Two Questions  
* ✅ Principle 7 – KPIs Drive Architecture  
* ✅ Principle 10 – No Accidental Decisions  
* ✅ Principle 11 – Engineering over Convenience  
* ✅ Principle 12 – Reliability Before Optimization

---

# **API-012 Structure**

API-012  
│  
├── API-012.1 Module Overview  
├── API-012.2 Audit Lifecycle  
├── API-012.3 Audit Log APIs  
├── API-012.4 User Activity APIs  
├── API-012.5 Security Event APIs  
├── API-012.6 System Monitoring APIs  
├── API-012.7 Performance Metrics APIs  
├── API-012.8 Validation & Business Rules  
├── API-012.9 Performance Considerations  
├── API-012.10 Security Considerations  
└── API-012.11 Integration with Other Modules

---

# **API-012.1 — Module Overview**

This module provides complete operational visibility into the system.

Responsibilities:

* Record user activities  
* Record administrative actions  
* Record authentication events  
* Track API requests  
* Track examination activities  
* Monitor server health  
* Monitor application performance  
* Record system failures  
* Provide operational dashboards

This module is append-only for audit records to preserve integrity.

---

# **API-012.2 — Audit Lifecycle**

User Action  
      │  
      ▼  
Generate Audit Event  
      │  
      ▼  
Validate Event  
      │  
      ▼  
Store Audit Record  
      │  
      ▼  
Index for Search  
      │  
      ▼  
Reporting & Investigation

System monitoring lifecycle:

System Metric  
      │  
      ▼  
Collector  
      │  
      ▼  
Monitoring Service  
      │  
      ▼  
Threshold Check  
      │  
      ▼  
Alert Generation

---

# **API-012.3 — Audit Log APIs**

## **Create Audit Log (Internal)**

| Property | Value |
| ----- | ----- |
| Method | POST |
| Endpoint | `/internal/audit` |
| Authentication | Internal Services Only |

### **Request**

{  
  "userId":105,  
  "action":"LOGIN",  
  "resource":"AUTH",  
  "status":"SUCCESS",  
  "ipAddress":"192.168.1.10"  
}

Database Tables:

* AuditLog  
* User

Transaction:

Yes

---

## **Search Audit Logs**

GET /api/v1/audit

Supports:

* User ID  
* Action  
* Date Range  
* Resource  
* Status  
* Pagination

---

## **Get Audit Log**

GET /api/v1/audit/{auditId}

---

## **Export Audit Logs**

GET /api/v1/audit/export

Supported Formats:

* CSV  
* PDF

---

# **API-012.4 — User Activity APIs**

Track user behavior across the platform.

## **Login History**

GET /api/v1/activity/login-history

---

## **Student Activity**

GET /api/v1/activity/students/{studentId}

Examples:

* Login  
* Logout  
* Examination Started  
* Examination Submitted  
* Result Viewed

---

## **Faculty Activity**

GET /api/v1/activity/faculty/{facultyId}

Examples:

* Question Created  
* Question Approved  
* Examination Scheduled  
* Result Published

---

## **Administrator Activity**

GET /api/v1/activity/admin

Tracks:

* User Management  
* Configuration Changes  
* Role Changes  
* System Administration

---

# **API-012.5 — Security Event APIs**

Security-related events are tracked separately.

## **Security Events**

GET /api/v1/security/events

Examples:

* Failed Login  
* Multiple Failed Attempts  
* Password Changed  
* Account Locked  
* Unauthorized Access  
* Token Expired  
* Suspicious API Usage

---

## **Failed Login Report**

GET /api/v1/security/failed-logins

---

## **Active Sessions**

GET /api/v1/security/sessions

Displays:

* User  
* Login Time  
* IP Address  
* Device  
* Status

---

# **API-012.6 — System Monitoring APIs**

## **System Health**

GET /api/v1/system/health

Returns:

{  
  "database":"UP",  
  "application":"UP",  
  "cache":"UP",  
  "storage":"UP",  
  "status":"HEALTHY"  
}

---

## **Server Metrics**

GET /api/v1/system/metrics

Returns:

* CPU Usage  
* Memory Usage  
* Disk Usage  
* Network Usage

---

## **Application Metrics**

GET /api/v1/system/application

Displays:

* Active Users  
* Active Examinations  
* Requests Per Minute  
* Error Rate  
* Average Response Time

---

# **API-012.7 — Performance Metrics APIs**

## **API Performance**

GET /api/v1/system/api-performance

Displays:

* Slowest APIs  
* Average Response Time  
* Request Count  
* Failure Rate

---

## **Database Metrics**

GET /api/v1/system/database

Displays:

* Active Connections  
* Slow Queries  
* Transaction Rate  
* Deadlocks  
* Connection Pool Usage

---

## **Background Jobs**

GET /api/v1/system/jobs

Shows:

* Running Jobs  
* Failed Jobs  
* Scheduled Jobs  
* Queue Size

---

# **API-012.8 — Validation & Business Rules**

Business Rules

* Audit records are immutable.  
* Audit records cannot be deleted through application APIs.  
* Internal services only can create audit entries.  
* Every authentication event is logged.  
* Every examination submission is logged.  
* Administrative changes require audit entries.  
* Health metrics are read-only.  
* Performance metrics are refreshed periodically.  
* Sensitive data (passwords, tokens, OTPs) must never be stored in audit logs.  
* Retention policies must be configurable to meet institutional compliance requirements.

---

# **API-012.9 — Performance Considerations**

To satisfy project KPIs:

* Use asynchronous audit logging where appropriate.  
* Index `userId`, `action`, `resource`, and `createdAt`.  
* Partition audit tables by date for scalability.  
* Cache health metrics for dashboard use.  
* Aggregate performance statistics periodically.  
* Archive old audit logs according to retention policy.

---

# **API-012.10 — Security Considerations**

| Operation | Student | Faculty | Admin |
| ----- | ----- | ----- | ----- |
| View Own Login History | ✅ | ✅ | ✅ |
| View Own Activity | ✅ | ✅ | ✅ |
| View Audit Logs | ❌ | ❌ | ✅ |
| Export Audit Logs | ❌ | ❌ | ✅ |
| View Security Events | ❌ | ❌ | ✅ |
| View System Health | ❌ | Limited | ✅ |
| View Performance Metrics | ❌ | ❌ | ✅ |
| Create Audit Record | ❌ | ❌ | Internal Services Only |

Security Measures:

* Append-only audit storage.  
* RBAC-protected audit access.  
* Sensitive fields masked before persistence.  
* Cryptographic integrity checks (e.g., hash chaining or digital signatures) can be applied to detect tampering.  
* All audit access is itself audited.

---

# **API-012.11 — Integration with Other Modules**

Authentication  
      │  
User Management  
      │  
Academic Management  
      │  
Examination Management  
      │  
Question Bank  
      │  
Examination Execution  
      │  
Evaluation & Results  
      │  
Notification Service  
      │  
Reporting & Analytics  
      │  
      ▼  
Audit Logging & System Monitoring

Every major module publishes operational and security events to this service for centralized storage and monitoring.

---

# **Endpoint Summary**

| Method | Endpoint | Purpose |
| ----- | ----- | ----- |
| POST | `/internal/audit` | Create audit record (internal) |
| GET | `/api/v1/audit` | Search audit logs |
| GET | `/api/v1/audit/{auditId}` | View audit record |
| GET | `/api/v1/audit/export` | Export audit logs |
| GET | `/api/v1/activity/login-history` | Login history |
| GET | `/api/v1/activity/students/{studentId}` | Student activity |
| GET | `/api/v1/activity/faculty/{facultyId}` | Faculty activity |
| GET | `/api/v1/activity/admin` | Administrator activity |
| GET | `/api/v1/security/events` | Security events |
| GET | `/api/v1/security/failed-logins` | Failed login report |
| GET | `/api/v1/security/sessions` | Active sessions |
| GET | `/api/v1/system/health` | System health |
| GET | `/api/v1/system/metrics` | Server metrics |
| GET | `/api/v1/system/application` | Application metrics |
| GET | `/api/v1/system/api-performance` | API performance |
| GET | `/api/v1/system/database` | Database metrics |
| GET | `/api/v1/system/jobs` | Background job metrics |

---

# **Database Tables Used**

| Table | Purpose |
| ----- | ----- |
| AuditLog | Immutable audit records |
| SecurityEvent | Security-related events |
| LoginHistory | Authentication history |
| SystemMetric | Periodic infrastructure metrics |
| ApiRequestLog | API request and response metrics |
| BackgroundJob | Scheduled and queued job metadata |
| UserSession | Active user sessions |

---

# **Core Subject Mapping**

| Subject | Contribution |
| ----- | ----- |
| **Software Engineering** | Centralized logging architecture, observability, monitoring services |
| **OOP** | Audit, Monitoring, Security Event, and Metrics service classes |
| **DBMS** | Immutable audit storage, indexing, partitioning, archival strategies |
| **Computer Networks** | API request tracing, network metrics, distributed service communication |
| **Operating Systems** | Process monitoring, CPU/memory utilization, concurrent log collection |
| **DSA** | Efficient log indexing, filtering, aggregation, and search algorithms |

---

# **Engineering Benefits**

| Engineering Goal | API Contribution |
| ----- | ----- |
| Security | Complete traceability of user and system actions |
| Compliance | Immutable audit records and configurable retention |
| Reliability | Continuous health and performance monitoring |
| Performance | Indexed searches and asynchronous logging |
| Maintainability | Centralized observability across all services |
| Troubleshooting | Detailed activity history, metrics, and diagnostics |

---

# **Deliverables Produced**

API-012 produces:

* ✅ Audit Logging API Specification  
* ✅ User Activity Tracking APIs  
* ✅ Security Event APIs  
* ✅ System Health Monitoring APIs  
* ✅ Performance Metrics APIs  
* ✅ Audit Lifecycle Model  
* ✅ Validation & Business Rules  
* ✅ Security & Authorization Matrix  
* ✅ Endpoint Catalog  
* ✅ Observability & Monitoring Framework

---

# **API-012 Status: Complete ✅**

API-012 completes the **Audit Logging & System Monitoring domain**, providing a secure, centralized, and immutable record of all significant user, administrative, and system activities. It also introduces operational observability through health checks, performance metrics, security event tracking, and monitoring dashboards, making the Online Examination Platform suitable for enterprise deployment, compliance, and long-term operational maintenance.

**Next:** **API-013 – File & Document Management**, which will define APIs for handling profile photos, question imports, answer-sheet attachments (where applicable), report exports, and other documents used throughout the platform.

Excellent. We now move to the **File & Document Management Module**.

This is the last major **Enterprise Infrastructure Module** before System Administration (API-014) and AI Proctoring (API-015).

Unlike API-011 (Reporting) and API-012 (Audit), this module manages **all digital assets** used by the Online Examination Platform. Rather than storing files directly in the database, the platform stores **metadata in the database** while the actual files are stored in a dedicated object/file storage system (local storage, AWS S3, Azure Blob, MinIO, etc.).

---

# **API-013 — File & Document Management APIs**

**Status:** API Design Phase

---

# **Objective**

Design a secure, scalable File & Document Management service responsible for handling the upload, storage, retrieval, versioning, and deletion of files used across the Online Examination Platform.

This module manages:

* Profile Photos  
* Faculty Documents  
* Student Documents  
* Question Bank Import Files  
* Bulk Student Import Files  
* Examination Attachments  
* Result PDFs  
* Report Exports  
* System Documents  
* File Versioning  
* File Metadata

The service acts as a centralized file repository for all platform modules.

---

# **Design Principles Applied**

* ✅ Principle 1 – Integration of Core Computer Science Subjects  
* ✅ Principle 2 – Every Design Decision Must Answer Two Questions  
* ✅ Principle 7 – KPIs Drive Architecture  
* ✅ Principle 10 – No Accidental Decisions  
* ✅ Principle 11 – Engineering over Convenience  
* ✅ Principle 12 – Reliability Before Optimization

---

# **API-013 Structure**

API-013  
│  
├── API-013.1 Module Overview  
├── API-013.2 File Lifecycle  
├── API-013.3 File Upload APIs  
├── API-013.4 File Retrieval APIs  
├── API-013.5 File Management APIs  
├── API-013.6 Bulk Import APIs  
├── API-013.7 Export & Download APIs  
├── API-013.8 Validation & Business Rules  
├── API-013.9 Performance Considerations  
├── API-013.10 Security Considerations  
└── API-013.11 Integration with Other Modules

---

# **API-013.1 — Module Overview**

The File Management Service centralizes all document operations.

Responsibilities:

* Upload files  
* Download files  
* Delete files  
* Update metadata  
* Version files  
* Import bulk data  
* Export reports  
* Validate uploaded files  
* Generate secure download links

Database stores only:

* File metadata  
* Owner  
* File path  
* Storage identifier  
* Version information

Actual files remain in external storage.

---

# **API-013.2 — File Lifecycle**

Upload File  
      │  
      ▼  
Validate File  
      │  
      ▼  
Virus Scan  
      │  
      ▼  
Store File  
      │  
      ▼  
Save Metadata  
      │  
      ▼  
Available for Access  
      │  
      ▼  
Archive / Delete

If an updated version is uploaded:

Existing File  
      │  
      ▼  
Create New Version  
      │  
      ▼  
Update Metadata  
      │  
      ▼  
Retain Previous Version

---

# **API-013.3 — File Upload APIs**

## **Upload File**

| Property | Value |
| ----- | ----- |
| Method | POST |
| Endpoint | `/api/v1/files` |
| Authentication | Required |

### **Request**

**Multipart/Form-Data**

file=\<binary\>  
fileType=PROFILE\_PHOTO  
ownerId=105

Supported File Types:

* PROFILE\_PHOTO  
* STUDENT\_DOCUMENT  
* FACULTY\_DOCUMENT  
* QUESTION\_IMPORT  
* RESULT\_PDF  
* REPORT\_EXPORT  
* EXAM\_ATTACHMENT

Database Tables:

* FileMetadata  
* AuditLog

Transaction:

Yes

---

## **Upload New Version**

POST /api/v1/files/{fileId}/versions

Creates a new version while preserving previous versions.

---

## **Bulk Upload**

POST /api/v1/files/bulk

Supports:

* ZIP  
* CSV  
* Excel (XLSX)

---

# **API-013.4 — File Retrieval APIs**

## **Download File**

GET /api/v1/files/{fileId}

Returns a secure download response or a time-limited signed URL.

---

## **View File Metadata**

GET /api/v1/files/{fileId}/metadata

Returns:

* File Name  
* Size  
* Version  
* Upload Date  
* Owner  
* MIME Type

---

## **List Files**

GET /api/v1/files

Supports:

* Pagination  
* Filtering  
* File Type  
* Owner  
* Upload Date

---

## **File Versions**

GET /api/v1/files/{fileId}/versions

---

# **API-013.5 — File Management APIs**

## **Update Metadata**

PATCH /api/v1/files/{fileId}

Updates metadata only (e.g., display name or tags), not file content.

---

## **Archive File**

PATCH /api/v1/files/{fileId}/archive

---

## **Delete File**

DELETE /api/v1/files/{fileId}

Implements soft deletion where institutional policy requires retention.

---

## **Restore File**

PATCH /api/v1/files/{fileId}/restore

---

# **API-013.6 — Bulk Import APIs**

Used for importing structured data.

## **Import Students**

POST /api/v1/import/students

Supported:

* CSV  
* XLSX

---

## **Import Questions**

POST /api/v1/import/questions

Supports validation before insertion into the Question Bank.

---

## **Import Faculty**

POST /api/v1/import/faculty

Returns:

* Imported Count  
* Failed Records  
* Validation Errors

---

# **API-013.7 — Export & Download APIs**

## **Export Results**

GET /api/v1/export/results

---

## **Export Reports**

GET /api/v1/export/reports

---

## **Export Student List**

GET /api/v1/export/students

---

## **Export Question Bank**

GET /api/v1/export/questions

Supported Formats:

* PDF  
* CSV  
* XLSX  
* ZIP (for multi-file exports)

---

# **API-013.8 — Validation & Business Rules**

Business Rules

* Only supported file types may be uploaded.  
* Maximum upload size is configurable by administrators.  
* Uploaded files must pass validation and malware scanning before storage.  
* Duplicate file versions increment the version number instead of overwriting.  
* Deleted files follow the configured retention policy.  
* Download permissions are enforced through RBAC.  
* Import operations are transactional; invalid records are reported without corrupting existing data.  
* Every upload, download, delete, restore, and export action is recorded in `AuditLog`.

---

# **API-013.9 — Performance Considerations**

To satisfy project KPIs:

* Stream large uploads and downloads.  
* Store binary files outside the relational database.  
* Use content hashing to detect duplicate uploads.  
* Compress exports where appropriate.  
* Support resumable uploads for large files.  
* Cache metadata for frequently accessed files.  
* Process imports asynchronously for large datasets.

---

# **API-013.10 — Security Considerations**

| Operation | Student | Faculty | Admin |
| ----- | ----- | ----- | ----- |
| Upload Own Documents | ✅ | ✅ | ✅ |
| Download Own Files | ✅ | ✅ | ✅ |
| View File Metadata | Own Files | Own Files | ✅ |
| Import Students | ❌ | ❌ | ✅ |
| Import Faculty | ❌ | ❌ | ✅ |
| Import Questions | ❌ | Assigned Faculty | ✅ |
| Export Reports | ❌ | Assigned Reports | ✅ |
| Delete Files | Own (Restricted) | Own (Restricted) | ✅ |
| Restore Files | ❌ | ❌ | ✅ |

Security Measures:

* RBAC-based authorization.  
* Secure object storage with private access.  
* Time-limited signed download URLs.  
* MIME type and extension validation.  
* File size limits.  
* Malware scanning before persistence.  
* File checksum validation to ensure integrity.  
* Audit logging for all file operations.

---

# **API-013.11 — Integration with Other Modules**

User Management  
      │  
      ├────────► Profile Photos  
      │  
Academic Management  
      ├────────► Student & Faculty Imports  
      │  
Question Bank  
      ├────────► Question Imports  
      │  
Examination Management  
      ├────────► Examination Attachments  
      │  
Evaluation & Results  
      ├────────► Result PDFs  
      │  
Reporting & Analytics  
      ├────────► Report Exports  
      │  
Audit Logging  
      ├────────► File Activity Logs  
      │  
      ▼  
File & Document Management

---

# **Endpoint Summary**

| Method | Endpoint | Purpose |
| ----- | ----- | ----- |
| POST | `/api/v1/files` | Upload file |
| POST | `/api/v1/files/{fileId}/versions` | Upload new version |
| POST | `/api/v1/files/bulk` | Bulk upload |
| GET | `/api/v1/files/{fileId}` | Download file |
| GET | `/api/v1/files/{fileId}/metadata` | View metadata |
| GET | `/api/v1/files` | List files |
| GET | `/api/v1/files/{fileId}/versions` | File versions |
| PATCH | `/api/v1/files/{fileId}` | Update metadata |
| PATCH | `/api/v1/files/{fileId}/archive` | Archive file |
| PATCH | `/api/v1/files/{fileId}/restore` | Restore file |
| DELETE | `/api/v1/files/{fileId}` | Delete file |
| POST | `/api/v1/import/students` | Import students |
| POST | `/api/v1/import/faculty` | Import faculty |
| POST | `/api/v1/import/questions` | Import questions |
| GET | `/api/v1/export/results` | Export results |
| GET | `/api/v1/export/reports` | Export reports |
| GET | `/api/v1/export/students` | Export students |
| GET | `/api/v1/export/questions` | Export question bank |

---

# **Database Tables Used**

| Table | Purpose |
| ----- | ----- |
| FileMetadata | File metadata and storage reference |
| FileVersion | Version history |
| ImportJob | Bulk import tracking |
| ExportJob | Export request tracking |
| User | File ownership |
| AuditLog | File activity logging |

---

# **Core Subject Mapping**

| Subject | Contribution |
| ----- | ----- |
| **Software Engineering** | Centralized file service, version control, modular import/export workflows |
| **OOP** | File, Version, Import, Export, and Storage service classes |
| **DBMS** | Metadata persistence, transactional import jobs, indexing |
| **Computer Networks** | Multipart uploads, streaming downloads, secure file transfer |
| **Operating Systems** | File I/O management, background processing, concurrent uploads |
| **DSA** | File indexing, duplicate detection using hashing, efficient metadata search |

---

# **Engineering Benefits**

| Engineering Goal | API Contribution |
| ----- | ----- |
| Scalability | External object storage and streaming transfers |
| Reliability | Versioning, transactional imports, resumable uploads |
| Security | Signed URLs, malware scanning, RBAC, integrity checks |
| Performance | Metadata caching and asynchronous processing |
| Maintainability | Centralized file management service |
| Extensibility | Easy integration with cloud storage providers and new file types |

---

# **Deliverables Produced**

API-013 produces:

* ✅ File & Document Management API Specification  
* ✅ File Upload & Download APIs  
* ✅ File Versioning APIs  
* ✅ Bulk Import APIs  
* ✅ Export APIs  
* ✅ File Lifecycle Model  
* ✅ Validation & Business Rules  
* ✅ Security & Authorization Matrix  
* ✅ Endpoint Catalog  
* ✅ Centralized File Management Architecture

---

# **API-013 Status: Complete ✅**

API-013 completes the **File & Document Management domain**, providing secure and scalable management of all digital assets used throughout the Online Examination Platform. By separating binary file storage from metadata management, supporting versioning, bulk import/export, and enterprise-grade security controls, it establishes a robust document infrastructure for the entire system.

## **Remaining API Modules**

Only **two API specifications** remain:

* **API-014 – System Administration & Platform Configuration**  
* **API-015 – AI-Based Proctoring & Exam Integrity** (Final module, as planned)

These will complete the entire API design phase of the Online Examination Platform.

Excellent. We are now at the **second last API module** of the entire Online Examination Platform.

Unlike previous modules that manage examinations, users, or reports, **API-014** is responsible for the **configuration, administration, maintenance, and operational control** of the platform. It gives administrators the ability to manage system-wide settings without modifying application code.

After this, only **API-015 (AI Proctoring & Exam Integrity)** will remain.

---

# **API-014 — System Administration & Platform Configuration APIs**

**Status:** API Design Phase

---

# **Objective**

Design a centralized System Administration & Platform Configuration service responsible for managing platform settings, institutional configurations, security policies, maintenance operations, and operational controls.

This module provides:

* System Configuration  
* Institution Configuration  
* Role & Permission Administration  
* Academic Calendar Configuration  
* Examination Policies  
* Password & Security Policies  
* Feature Toggle Management  
* Maintenance Mode  
* Backup & Restore Operations  
* License & Version Information

This module is accessible only to authorized system administrators and super administrators.

---

# **Design Principles Applied**

* ✅ Principle 1 – Integration of Core Computer Science Subjects  
* ✅ Principle 2 – Every Design Decision Must Answer Two Questions  
* ✅ Principle 7 – KPIs Drive Architecture  
* ✅ Principle 10 – No Accidental Decisions  
* ✅ Principle 11 – Engineering over Convenience  
* ✅ Principle 12 – Reliability Before Optimization

---

# **API-014 Structure**

API-014  
│  
├── API-014.1 Module Overview  
├── API-014.2 Administration Lifecycle  
├── API-014.3 System Configuration APIs  
├── API-014.4 Institution Configuration APIs  
├── API-014.5 Security Policy APIs  
├── API-014.6 Feature Management APIs  
├── API-014.7 Backup & Maintenance APIs  
├── API-014.8 Validation & Business Rules  
├── API-014.9 Performance Considerations  
├── API-014.10 Security Considerations  
└── API-014.11 Integration with Other Modules

---

# **API-014.1 — Module Overview**

This module centralizes all administrative controls for the Online Examination Platform.

Responsibilities:

* Configure global system settings  
* Configure institution information  
* Configure examination policies  
* Configure academic calendar  
* Configure password policies  
* Configure security policies  
* Enable/disable platform features  
* Manage maintenance mode  
* Schedule backups  
* Restore system backups  
* Manage application version information

The objective is to ensure that operational changes can be made through configuration rather than application code.

---

# **API-014.2 — Administration Lifecycle**

Administrator Login  
        │  
        ▼  
Load Current Configuration  
        │  
        ▼  
Modify Settings  
        │  
        ▼  
Validate Configuration  
        │  
        ▼  
Apply Changes  
        │  
        ▼  
Audit Configuration Change  
        │  
        ▼  
Notify Dependent Modules

For backup operations:

Backup Schedule  
        │  
        ▼  
Create Backup  
        │  
        ▼  
Store Backup  
        │  
        ▼  
Verify Integrity  
        │  
        ▼  
Ready for Restore

---

# **API-014.3 — System Configuration APIs**

## **Get System Configuration**

| Property | Value |
| ----- | ----- |
| Method | GET |
| Endpoint | `/api/v1/admin/system-config` |
| Authentication | Required |
| Authorization | Super Admin |

Returns:

{  
  "systemName":"Online Examination Platform",  
  "timezone":"Asia/Kolkata",  
  "defaultLanguage":"en",  
  "maintenanceMode":false,  
  "sessionTimeout":30  
}

---

## **Update System Configuration**

PUT /api/v1/admin/system-config

Example

{  
  "timezone":"Asia/Kolkata",  
  "sessionTimeout":45  
}

---

## **View System Information**

GET /api/v1/admin/system-info

Returns:

* Application Version  
* Build Number  
* Database Version  
* Deployment Date  
* Uptime

---

# **API-014.4 — Institution Configuration APIs**

## **Institution Profile**

GET /api/v1/admin/institution

---

## **Update Institution Profile**

PUT /api/v1/admin/institution

Fields include:

* Institution Name  
* Logo  
* Address  
* Contact Information  
* Academic Year  
* Semester Configuration

---

## **Academic Calendar**

GET /api/v1/admin/academic-calendar

---

## **Update Academic Calendar**

PUT /api/v1/admin/academic-calendar

Supports:

* Semester Dates  
* Holidays  
* Examination Windows  
* Result Publication Windows

---

# **API-014.5 — Security Policy APIs**

## **Password Policy**

GET /api/v1/admin/security/password-policy

Returns:

* Minimum Length  
* Complexity Rules  
* Expiration Period  
* Password History Limit

---

## **Update Password Policy**

PUT /api/v1/admin/security/password-policy

---

## **Session Policy**

GET /api/v1/admin/security/session-policy

Configures:

* Session Timeout  
* Concurrent Session Limit  
* Idle Timeout  
* Token Expiration

---

## **Update Session Policy**

PUT /api/v1/admin/security/session-policy

---

# **API-014.6 — Feature Management APIs**

## **Feature List**

GET /api/v1/admin/features

Examples:

* Online Examination  
* Notifications  
* Reports  
* AI Proctoring  
* File Management  
* Bulk Import

---

## **Enable Feature**

PATCH /api/v1/admin/features/{featureId}/enable

---

## **Disable Feature**

PATCH /api/v1/admin/features/{featureId}/disable

---

## **Maintenance Mode**

PATCH /api/v1/admin/maintenance

Example

{  
  "enabled":true,  
  "message":"System maintenance from 2:00 AM to 3:00 AM."  
}

---

# **API-014.7 — Backup & Maintenance APIs**

## **Create Backup**

POST /api/v1/admin/backup

Creates:

* Database Backup  
* Configuration Backup  
* Metadata Backup

---

## **Backup History**

GET /api/v1/admin/backup

---

## **Restore Backup**

POST /api/v1/admin/restore/{backupId}

---

## **Database Maintenance**

POST /api/v1/admin/database/maintenance

Operations:

* Optimize Tables  
* Rebuild Indexes  
* Cleanup Logs  
* Archive Historical Data

---

# **API-014.8 — Validation & Business Rules**

Business Rules

* Only Super Administrators can modify system configuration.  
* Maintenance mode prevents new examination sessions but allows administrators to perform maintenance tasks.  
* Security policy updates affect new authentication sessions immediately.  
* Backup files must pass integrity verification before restoration.  
* Feature toggles must not disable mandatory platform components.  
* Every configuration change is recorded in `AuditLog`.  
* Restore operations require explicit administrator confirmation.

---

# **API-014.9 — Performance Considerations**

To satisfy project KPIs:

* Cache frequently accessed configuration values.  
* Reload configuration dynamically without restarting the application where possible.  
* Schedule backup jobs during low-traffic periods.  
* Use incremental backups to reduce storage and execution time.  
* Archive historical operational data to maintain database performance.

---

# **API-014.10 — Security Considerations**

| Operation | Student | Faculty | Admin | Super Admin |
| ----- | ----- | ----- | ----- | ----- |
| View System Information | ❌ | ❌ | Limited | ✅ |
| Modify Configuration | ❌ | ❌ | ❌ | ✅ |
| Manage Institution Profile | ❌ | ❌ | Limited | ✅ |
| Update Security Policies | ❌ | ❌ | ❌ | ✅ |
| Enable/Disable Features | ❌ | ❌ | ❌ | ✅ |
| Backup Database | ❌ | ❌ | Limited | ✅ |
| Restore Database | ❌ | ❌ | ❌ | ✅ |
| Maintenance Mode | ❌ | ❌ | ❌ | ✅ |

Security Measures:

* Multi-level RBAC with Super Administrator privileges.  
* Optional Multi-Factor Authentication (MFA) for administrative actions.  
* Full audit trail for every configuration and maintenance operation.  
* Restore operations require confirmation and can optionally require dual authorization.  
* Sensitive configuration values (e.g., API keys, secrets) are encrypted at rest.

---

# **API-014.11 — Integration with Other Modules**

Authentication  
      │  
      ├────────► Security Policies  
      │  
User Management  
      ├────────► Role Configuration  
      │  
Academic Management  
      ├────────► Academic Calendar  
      │  
Examination Management  
      ├────────► Examination Policies  
      │  
Notification Service  
      ├────────► Maintenance Notifications  
      │  
Reporting & Analytics  
      ├────────► System Reports  
      │  
Audit Logging  
      ├────────► Configuration Audit  
      │  
      ▼  
System Administration

---

# **Endpoint Summary**

| Method | Endpoint | Purpose |
| ----- | ----- | ----- |
| GET | `/api/v1/admin/system-config` | View system configuration |
| PUT | `/api/v1/admin/system-config` | Update system configuration |
| GET | `/api/v1/admin/system-info` | View system information |
| GET | `/api/v1/admin/institution` | View institution profile |
| PUT | `/api/v1/admin/institution` | Update institution profile |
| GET | `/api/v1/admin/academic-calendar` | View academic calendar |
| PUT | `/api/v1/admin/academic-calendar` | Update academic calendar |
| GET | `/api/v1/admin/security/password-policy` | View password policy |
| PUT | `/api/v1/admin/security/password-policy` | Update password policy |
| GET | `/api/v1/admin/security/session-policy` | View session policy |
| PUT | `/api/v1/admin/security/session-policy` | Update session policy |
| GET | `/api/v1/admin/features` | List features |
| PATCH | `/api/v1/admin/features/{featureId}/enable` | Enable feature |
| PATCH | `/api/v1/admin/features/{featureId}/disable` | Disable feature |
| PATCH | `/api/v1/admin/maintenance` | Toggle maintenance mode |
| POST | `/api/v1/admin/backup` | Create backup |
| GET | `/api/v1/admin/backup` | Backup history |
| POST | `/api/v1/admin/restore/{backupId}` | Restore backup |
| POST | `/api/v1/admin/database/maintenance` | Database maintenance |

---

# **Database Tables Used**

| Table | Purpose |
| ----- | ----- |
| SystemConfiguration | Global application settings |
| InstitutionConfiguration | Institution profile and academic settings |
| SecurityPolicy | Password and session policies |
| FeatureToggle | Enable/disable platform features |
| BackupHistory | Backup metadata and status |
| MaintenanceLog | Maintenance operations |
| AuditLog | Administrative activity tracking |

---

# **Core Subject Mapping**

| Subject | Contribution |
| ----- | ----- |
| **Software Engineering** | Configuration management, feature toggles, administrative workflows |
| **OOP** | Configuration, Policy, Backup, and Feature service classes |
| **DBMS** | Configuration persistence, backup metadata, transaction-safe restore operations |
| **Computer Networks** | Administrative REST APIs and secure communication |
| **Operating Systems** | Backup scheduling, maintenance jobs, process management |
| **DSA** | Efficient configuration caching, scheduling, and maintenance task management |

---

# **Engineering Benefits**

| Engineering Goal | API Contribution |
| ----- | ----- |
| Maintainability | Runtime configuration without code changes |
| Reliability | Backup, restore, and maintenance capabilities |
| Security | Centralized policy management and administrative controls |
| Scalability | Dynamic configuration and feature toggles |
| Operational Excellence | Centralized platform administration |
| Compliance | Fully audited configuration changes and maintenance operations |

---

# **Deliverables Produced**

API-014 produces:

* ✅ System Administration API Specification  
* ✅ System & Institution Configuration APIs  
* ✅ Security Policy APIs  
* ✅ Feature Toggle Management APIs  
* ✅ Backup & Restore APIs  
* ✅ Maintenance Management APIs  
* ✅ Administration Lifecycle Model  
* ✅ Validation & Business Rules  
* ✅ Security & Authorization Matrix  
* ✅ Endpoint Catalog

---

# **API-014 Status: Complete ✅**

API-014 completes the **System Administration & Platform Configuration domain**, providing comprehensive administrative control over the Online Examination Platform. It enables secure runtime configuration, institutional management, security policy enforcement, feature management, backup and recovery, and maintenance operations while ensuring every administrative action is auditable and governed by strict authorization controls.

---

# **API Design Progress**

At this stage, **14 out of 15 API modules are complete**:

* ✅ API-001 — API Architecture & Standards  
* ✅ API-002 — Common Response & Error Handling  
* ✅ API-003 — Authentication & Authorization  
* ✅ API-004 — User Management  
* ✅ API-005 — Academic Management  
* ✅ API-006 — Examination Management  
* ✅ API-007 — Question Bank  
* ✅ API-008 — Examination Execution  
* ✅ API-009 — Evaluation & Result Management  
* ✅ API-010 — Notification & Communication  
* ✅ API-011 — Reporting & Analytics  
* ✅ API-012 — Audit Logging & System Monitoring  
* ✅ API-013 — File & Document Management  
* ✅ API-014 — System Administration & Platform Configuration

Only **one API module remains**:

**API-015 – AI-Based Proctoring & Exam Integrity**, which will serve as the capstone of the API design phase and integrate seamlessly with the examination execution workflow while remaining modular enough to be enabled or disabled through the feature management capabilities introduced in API-014.

That's actually a better choice for your project.

Since earlier you decided **not to implement AI/ML-based proctoring** and instead implement a **lightweight exam integrity system**, API-015 should reflect the actual scope of your project rather than introducing features you won't build.

This also aligns better with your college SRS because it focuses on **secure examination execution** rather than advanced AI surveillance.

---

# **API-015 — Exam Integrity & Suspicious Activity Monitoring APIs**

**Status:** Final API Design Phase

---

# **Objective**

Design a lightweight Exam Integrity service responsible for monitoring candidate behavior during an online examination and recording suspicious activities that may indicate malpractice.

Unlike AI-based proctoring systems, this module **does not use machine learning, webcam analysis, facial recognition, or eye tracking**.

Instead, it monitors browser-level and client-side events to help invigilators identify suspicious examination behavior.

This module provides:

* Browser Tab Switching Detection  
* Window Focus Monitoring  
* Full-Screen Exit Detection  
* Keyboard Shortcut Detection  
* Suspicious Activity Logging  
* Live Monitoring Dashboard  
* Integrity Report Generation  
* Warning Management

---

# **Design Principles Applied**

* ✅ Principle 1 – Integration of Core Computer Science Subjects  
* ✅ Principle 2 – Every Design Decision Must Answer Two Questions  
* ✅ Principle 7 – KPIs Drive Architecture  
* ✅ Principle 10 – No Accidental Decisions  
* ✅ Principle 11 – Engineering over Convenience  
* ✅ Principle 12 – Reliability Before Optimization

---

# **API-015 Structure**

API-015  
│  
├── API-015.1 Module Overview  
├── API-015.2 Monitoring Lifecycle  
├── API-015.3 Suspicious Activity APIs  
├── API-015.4 Warning Management APIs  
├── API-015.5 Live Monitoring APIs  
├── API-015.6 Integrity Report APIs  
├── API-015.7 Validation & Business Rules  
├── API-015.8 Performance Considerations  
├── API-015.9 Security Considerations  
└── API-015.10 Integration with Other Modules

---

# **API-015.1 — Module Overview**

The Exam Integrity module continuously monitors browser events during an examination.

Responsibilities:

* Detect tab switching  
* Detect browser window changes  
* Detect full-screen exit  
* Detect browser minimization  
* Detect prohibited keyboard shortcuts  
* Count suspicious activities  
* Record timestamps  
* Notify invigilators  
* Generate integrity reports

No video, audio, or biometric data is collected.

---

# **API-015.2 — Monitoring Lifecycle**

Exam Starts  
      │  
      ▼  
Monitoring Enabled  
      │  
      ▼  
Browser Event Detected  
      │  
      ▼  
Validate Event  
      │  
      ▼  
Record Suspicious Activity  
      │  
      ▼  
Increase Warning Count  
      │  
      ▼  
Notify Faculty Dashboard  
      │  
      ▼  
Continue Exam  
      │  
      ▼  
Exam Ends  
      │  
      ▼  
Generate Integrity Report

---

# **API-015.3 — Suspicious Activity APIs**

## **Report Suspicious Activity**

| Property | Value |
| ----- | ----- |
| Method | POST |
| Endpoint | `/api/v1/integrity/events` |
| Authentication | Required |
| Authorization | Authenticated Exam Session |

### **Request**

{  
  "attemptId": 101,  
  "eventType": "TAB\_SWITCH",  
  "timestamp": "2026-08-04T10:15:32Z"  
}

Supported Event Types

* TAB\_SWITCH  
* WINDOW\_BLUR  
* WINDOW\_MINIMIZE  
* FULLSCREEN\_EXIT  
* COPY\_ATTEMPT  
* PASTE\_ATTEMPT  
* KEYBOARD\_SHORTCUT  
* RIGHT\_CLICK

Database Tables

* SuspiciousActivity  
* ExamAttempt  
* AuditLog

---

## **Get Attempt Activity**

GET /api/v1/integrity/attempts/{attemptId}

Returns all suspicious events recorded during the examination.

---

## **Get Student Activity**

GET /api/v1/integrity/students/{studentId}

Shows integrity history across examinations.

---

# **API-015.4 — Warning Management APIs**

## **Issue Warning**

POST /api/v1/integrity/warnings

Example

{  
  "attemptId":101,  
  "warningNumber":2,  
  "message":"Multiple tab switches detected."  
}

---

## **Warning Count**

GET /api/v1/integrity/attempts/{attemptId}/warnings

Returns:

* Total Warnings  
* Latest Warning  
* Current Status

---

## **Reset Warning (Admin Only)**

PATCH /api/v1/integrity/warnings/{warningId}/reset

---

# **API-015.5 — Live Monitoring APIs**

## **Live Examination Monitoring**

GET /api/v1/integrity/live/{examId}

Displays:

* Active Students  
* Current Warnings  
* Latest Events  
* Examination Status

---

## **Live Alerts**

GET /api/v1/integrity/live/alerts

Shows real-time suspicious activities.

---

# **API-015.6 — Integrity Report APIs**

## **Attempt Integrity Report**

GET /api/v1/integrity/report/{attemptId}

Contains:

* Total Tab Switches  
* Full-screen Exits  
* Copy/Paste Attempts  
* Warning Count  
* Timeline of Events

---

## **Examination Integrity Report**

GET /api/v1/integrity/report/exam/{examId}

Displays:

* Students Flagged  
* Total Violations  
* Most Common Violation  
* Warning Distribution

---

# **API-015.7 — Validation & Business Rules**

Business Rules

* Monitoring starts only after the examination begins.  
* Events are accepted only for active examination sessions.  
* Every suspicious event is timestamped.  
* Multiple identical events occurring within a short configurable interval may be merged to avoid duplicate logging.  
* Warnings are generated based on configurable thresholds.  
* Monitoring stops automatically when the examination ends.  
* All integrity events are stored in immutable audit records.

---

# **API-015.8 — Performance Considerations**

To satisfy project KPIs:

* Use lightweight browser event listeners.  
* Batch event uploads where appropriate.  
* Index `attemptId`, `studentId`, and `eventType`.  
* Process alerts asynchronously for faculty dashboards.  
* Minimize client-side overhead to avoid affecting the examination experience.

---

# **API-015.9 — Security Considerations**

| Operation | Student | Faculty | Admin |
| ----- | ----- | ----- | ----- |
| Report Event | ✅ (Client) | ❌ | ❌ |
| View Own Integrity Report | ❌ | ❌ | Optional |
| View Live Monitoring | ❌ | Assigned Exams | ✅ |
| View Integrity Reports | ❌ | Assigned Exams | ✅ |
| Reset Warning | ❌ | ❌ | ✅ |

Security Measures:

* Events accepted only from authenticated examination sessions.  
* Server-side validation to reduce spoofing of client events.  
* TLS encryption for event transmission.  
* All integrity events logged in `AuditLog`.  
* Faculty can only view examinations assigned to them.

---

# **API-015.10 — Integration with Other Modules**

Authentication  
      │  
      ▼  
Examination Execution (API-008)  
      │  
      ▼  
Exam Integrity Monitoring (API-015)  
      │  
      ├────────► Suspicious Activity  
      ├────────► Warning Generation  
      ├────────► Live Faculty Dashboard  
      │  
      ▼  
Audit Logging (API-012)  
      │  
      ▼  
Reporting & Analytics (API-011)

---

# **Endpoint Summary**

| Method | Endpoint | Purpose |
| ----- | ----- | ----- |
| POST | `/api/v1/integrity/events` | Report suspicious event |
| GET | `/api/v1/integrity/attempts/{attemptId}` | Attempt activity |
| GET | `/api/v1/integrity/students/{studentId}` | Student integrity history |
| POST | `/api/v1/integrity/warnings` | Issue warning |
| GET | `/api/v1/integrity/attempts/{attemptId}/warnings` | Warning count |
| PATCH | `/api/v1/integrity/warnings/{warningId}/reset` | Reset warning |
| GET | `/api/v1/integrity/live/{examId}` | Live monitoring |
| GET | `/api/v1/integrity/live/alerts` | Live alerts |
| GET | `/api/v1/integrity/report/{attemptId}` | Attempt integrity report |
| GET | `/api/v1/integrity/report/exam/{examId}` | Examination integrity report |

---

# **Database Tables Used**

| Table | Purpose |
| ----- | ----- |
| SuspiciousActivity | Stores browser integrity events |
| Warning | Stores warning records issued during exams |
| ExamAttempt | Links integrity events to examination attempts |
| AuditLog | Permanent record of integrity-related actions |

---

# **Core Subject Mapping**

| Subject | Contribution |
| ----- | ----- |
| **Software Engineering** | Modular integrity monitoring service integrated with exam execution |
| **OOP** | Event, Warning, IntegrityReport, and Monitoring service classes |
| **DBMS** | Persistent event logging, indexed queries, transactional warning storage |
| **Computer Networks** | Secure transmission of browser events via REST APIs |
| **Operating Systems** | Event-driven client monitoring, concurrent processing of live events |
| **DSA** | Efficient event filtering, threshold counting, timeline generation, and alert processing |

---

# **Engineering Benefits**

| Engineering Goal | API Contribution |
| ----- | ----- |
| Academic Integrity | Detects common browser-based malpractice attempts |
| Performance | Lightweight client-side monitoring with minimal overhead |
| Security | Authenticated event reporting and immutable audit logs |
| Scalability | Supports large concurrent examinations through asynchronous event handling |
| Maintainability | Modular monitoring service independent of examination logic |
| Transparency | Provides detailed integrity reports for post-exam review |

---

# **Deliverables Produced**

API-015 produces:

* ✅ Exam Integrity Monitoring API Specification  
* ✅ Suspicious Activity Detection APIs  
* ✅ Warning Management APIs  
* ✅ Live Monitoring APIs  
* ✅ Integrity Report APIs  
* ✅ Monitoring Lifecycle Model  
* ✅ Validation & Business Rules  
* ✅ Security & Authorization Matrix  
* ✅ Endpoint Catalog

---

# **API-015 Status: Complete ✅**

This completes the **API Design Phase** of your Online Examination Platform.

You now have a complete set of **15 API design documents** covering the entire platform—from authentication and examination management to reporting, administration, and lightweight exam integrity monitoring. The final module intentionally avoids AI-based proctoring and instead implements practical browser-event monitoring (tab switching, focus changes, full-screen exits, and related suspicious activities), making it well-suited for your project's scope while remaining modular and extensible for future enhancements.

# FrontendDesign

Excellent. We have now reached one of the most important LLD documents.

So far we have defined:

* ✅ **LLD-001:** Where every file will be stored.  
* ✅ **LLD-002:** How the backend is organized.

Now we will design **the complete frontend architecture**, which will become the blueprint for every React component we build.

---

# **LLD-003 — Frontend Architecture & Component Design**

**Status:** Low-Level Design Phase

---

# **Objective**

Design a scalable, modular, and maintainable React frontend for the Online Examination Platform that supports multiple user roles, reusable UI components, efficient state management, and seamless integration with the backend APIs.

This document defines:

* Frontend architecture  
* Page hierarchy  
* Dashboard layouts  
* Component organization  
* Routing strategy  
* State management  
* API integration  
* Form validation  
* UI interaction flow  
* Role-based navigation

---

# **Design Principles**

* Component-Based Architecture  
* Atomic Design (where appropriate)  
* Separation of Concerns  
* Single Responsibility Principle  
* Reusability  
* Responsive Design  
* Accessibility  
* Lazy Loading  
* Feature-Based Organization

---

# **Frontend Architecture Overview**

Browser  
     │  
     ▼  
React Application  
     │  
     ▼  
React Router  
     │  
     ▼  
Page Component  
     │  
     ▼  
Reusable Components  
     │  
     ▼  
Service Layer  
     │  
     ▼  
REST API

Supporting layers:

Context API  
Hooks  
Validation  
Utilities  
Constants  
Assets

---

# **Frontend Folder Organization**

src/  
│  
├── assets/  
├── components/  
├── pages/  
├── layouts/  
├── routes/  
├── services/  
├── hooks/  
├── context/  
├── utils/  
├── constants/  
├── validations/  
├── styles/  
├── App.jsx  
└── main.jsx

---

# **Frontend Architecture Layers**

UI Layer  
      │  
      ▼  
Pages  
      │  
      ▼  
Reusable Components  
      │  
      ▼  
Hooks / Context  
      │  
      ▼  
Service Layer  
      │  
      ▼  
Backend API

Business logic should never be written directly inside UI components.

---

# **Layout Design**

The system contains **three independent dashboards**.

Login

│

├────────► Student Dashboard

├────────► Faculty Dashboard

└────────► Admin Dashboard

Each dashboard has:

* Sidebar  
* Top Navigation  
* Main Content  
* Footer

---

# **Shared Layout Components**

layouts/  
│  
├── AuthLayout.jsx  
├── DashboardLayout.jsx  
├── AdminLayout.jsx  
├── FacultyLayout.jsx  
└── StudentLayout.jsx

Responsibilities:

* Navigation  
* Sidebar  
* Header  
* Footer  
* Route Outlet

---

# **Page Hierarchy**

## **Authentication Pages**

pages/auth/

LoginPage

ForgotPasswordPage

ResetPasswordPage

UnauthorizedPage

---

## **Student Pages**

pages/student/

Dashboard

Profile

Registered Exams

Exam Instructions

Take Exam

Exam History

Results

Notifications

Settings

---

## **Faculty Pages**

pages/faculty/

Dashboard

Manage Questions

Question Categories

Create Exam

Schedule Exam

Evaluate Answers

Results

Reports

Notifications

---

## **Admin Pages**

pages/admin/

Dashboard

Users

Roles

Departments

Subjects

Academic Calendar

Examinations

Reports

System Settings

Audit Logs

Integrity Dashboard

---

## **Shared Pages**

pages/common/

Profile

Change Password

Notifications

Help

About

404

500

---

# **Component Library**

The project uses reusable UI components.

components/

common/

forms/

tables/

cards/

charts/

modals/

navigation/

notifications/

integrity/

---

# **Common Components**

Button

Input

TextArea

Select

Checkbox

RadioButton

DatePicker

TimePicker

SearchBar

Loader

Spinner

Badge

Tooltip

Pagination

Breadcrumb

Reusable across all modules.

---

# **Form Components**

LoginForm

StudentForm

FacultyForm

ExamForm

QuestionForm

SubjectForm

DepartmentForm

Each form:

* Client validation  
* Error handling  
* API integration

---

# **Table Components**

UserTable

ExamTable

QuestionTable

ResultTable

DepartmentTable

SubjectTable

Supports:

* Pagination  
* Sorting  
* Filtering  
* Search  
* Export

---

# **Card Components**

DashboardCard

StatisticCard

ExamCard

QuestionCard

NotificationCard

---

# **Chart Components**

BarChart

LineChart

PieChart

AttendanceChart

ResultAnalyticsChart

Used in reports and dashboards.

---

# **Modal Components**

ConfirmationModal

DeleteModal

EditModal

WarningModal

SuccessModal

ErrorModal

---

# **Navigation Components**

Sidebar

TopNavbar

MenuItem

ProfileMenu

Breadcrumb

---

# **Notification Components**

NotificationPanel

NotificationItem

Toast

AlertBanner

---

# **Integrity Components**

Because we are **not implementing AI proctoring**, only browser-event monitoring components are needed.

WarningCounter

IntegrityStatus

SuspiciousActivityLog

ExamIntegrityBanner

---

# **Routing Design**

/

↓

Login

↓

Role Verification

↓

Dashboard

↓

Feature Pages

---

# **Protected Routes**

AdminRoute

FacultyRoute

StudentRoute

Unauthorized users are redirected.

---

# **State Management**

Use **React Context API**.

Contexts:

AuthContext

UserContext

ThemeContext

NotificationContext

ExamContext

Responsibilities:

* Logged-in user  
* JWT token  
* Selected exam  
* Theme  
* Notifications

---

# **Custom Hooks**

useAuth()

useApi()

usePagination()

useNotification()

useExamTimer()

useIntegrityMonitor()

Example:

useExamTimer()

↓

Countdown Timer

↓

Auto Submit

↓

API Call

---

# **API Service Layer**

All backend communication is centralized.

services/

authService.js

userService.js

examService.js

questionService.js

resultService.js

notificationService.js

integrityService.js

Components never call APIs directly.

---

# **Validation Layer**

validations/

authValidation.js

studentValidation.js

facultyValidation.js

examValidation.js

questionValidation.js

Responsibilities:

* Required fields  
* Email validation  
* Password strength  
* Marks validation  
* Date validation

---

# **Utility Layer**

utils/

dateUtil.js

jwtUtil.js

storageUtil.js

fileUtil.js

formatUtil.js

Reusable helper functions.

---

# **Constants**

constants/

roles.js

apiRoutes.js

status.js

messages.js

examConstants.js

---

# **UI Flow Example**

### **Student Login**

LoginPage

↓

LoginForm

↓

authService.login()

↓

JWT Received

↓

AuthContext Updated

↓

Student Dashboard

---

### **Start Examination**

Exam List

↓

Exam Details

↓

Instructions

↓

Start Button

↓

Exam Page

↓

Timer Starts

↓

Integrity Monitor Starts

---

### **Submit Examination**

Submit Button

↓

Confirmation Modal

↓

examService.submit()

↓

Success Message

↓

Results Pending

---

# **Component Communication**

Parent Page

↓

Child Component

↓

Callback Function

↓

Service Layer

↓

Backend API

Communication follows a **top-down data flow**.

---

# **Responsive Design Strategy**

Support:

* Desktop (Primary)  
* Laptop  
* Tablet

Minimum supported resolution:

1280 × 720

Tailwind CSS responsive breakpoints will be used for adaptive layouts.

---

# **Error Handling Strategy**

Global error boundary.

Displays:

* Network Error  
* Unauthorized  
* Forbidden  
* Server Error  
* Page Not Found

---

# **Module-to-Page Mapping**

| Module | Pages |
| ----- | ----- |
| Authentication | Login, Forgot Password, Reset Password |
| User Management | Users, Profile |
| Academic Management | Departments, Subjects, Academic Calendar |
| Examination Management | Create Exam, Schedule Exam |
| Question Bank | Questions, Categories |
| Examination Execution | Instructions, Take Exam |
| Evaluation | Evaluate Answers |
| Results | Results, Analytics |
| Notifications | Notification Center |
| Reports | Reports Dashboard |
| Administration | System Settings, Audit Logs |
| Integrity Monitoring | Integrity Dashboard, Warning Log |

---

# **Engineering Benefits**

| Goal | Benefit |
| ----- | ----- |
| Reusability | Common components reduce duplicate code |
| Maintainability | Clear separation of UI, logic, and API calls |
| Scalability | New pages and features can be added without restructuring |
| Testability | Components and services can be tested independently |
| Performance | Lazy loading and reusable state management reduce overhead |
| Consistency | Shared layouts and component library provide a uniform UI |

---

# **Deliverables Produced**

LLD-003 defines:

* ✅ Complete frontend architecture  
* ✅ Dashboard layout design  
* ✅ Page hierarchy  
* ✅ Reusable component library  
* ✅ Routing strategy  
* ✅ Context API design  
* ✅ Custom hooks  
* ✅ API service organization  
* ✅ Validation layer  
* ✅ Component interaction model  
* ✅ Responsive design strategy

---

# **LLD-003 Status: Complete ✅**

The frontend architecture for the Online Examination Platform is now fully defined. Combined with **LLD-001 (Project Folder Structure)** and **LLD-002 (Backend Package Design)**, this document provides a complete implementation blueprint for the React application, ensuring consistency, maintainability, and seamless integration with the backend.

## **Next Step**

**LLD-004 – Class Diagram & OOP Design**

This is one of the largest and most important LLD documents. We will design every major class in the system (User, Student, Faculty, Admin, Exam, Question, Result, Notification, SuspiciousActivity, etc.), define their attributes, methods, relationships, inheritance, interfaces, and apply OOP principles such as encapsulation, abstraction, inheritance, and polymorphism across the entire Online Examination Platform.

# InfoForDiagrams

Excellent. We have now reached the final major design document before implementation. Up to this point, we have designed the **entire static architecture** of the Online Examination Platform. LLD-011 focuses on the **dynamic behavior** of the system—how objects and components interact during runtime.

---

# **LLD-011 – UML Interaction & Behavioral Diagrams**

**Status:** Low-Level Design Phase

---

# **Objective**

Design the dynamic behavior of the Online Examination Platform using UML behavioral diagrams to describe:

* Sequence Diagrams  
* Activity Diagrams  
* State Machine Diagrams  
* Communication Diagrams  
* Object Interaction Flows

These diagrams document how users, controllers, services, repositories, and the database interact during major system workflows.

---

# **Design Principles**

* Separation of Responsibilities  
* Layered Architecture  
* Stateless Request Processing  
* Event-Driven Interaction  
* Business Process Visualization  
* Traceable User Workflows

---

# **Behavioral Diagrams Covered**

| Diagram | Purpose |
| ----- | ----- |
| Sequence Diagram | Object interaction over time |
| Activity Diagram | Business workflow |
| State Machine Diagram | Lifecycle of entities |
| Communication Diagram | Object collaboration |
| Interaction Flow | End-to-end request execution |

---

# **Sequence Diagram 1 – User Login**

## **Objective**

Authenticate a user and issue JWT tokens.

User  
 │  
 │ Login Request  
 ▼  
AuthController  
 │  
 ▼  
AuthService  
 │  
 ▼  
UserRepository  
 │  
 ▼  
Database  
 │  
 │ User Details  
 ▼  
AuthService  
 │ Password Verification  
 │ Generate JWT  
 ▼  
AuthController  
 │  
 ▼  
LoginResponse  
 │  
 ▼  
User

### **Components**

* User  
* AuthController  
* AuthService  
* UserRepository  
* Database  
* JWT Service

---

# **Sequence Diagram 2 – Create Examination**

Faculty  
 │  
 ▼  
ExamController  
 │  
 ▼  
ExamService  
 │  
 ▼  
SubjectRepository  
 │  
 ▼  
ExamRepository  
 │  
 ▼  
Database  
 │  
 ▼  
AuditService  
 │  
 ▼  
NotificationService  
 │  
 ▼  
Faculty

### **Workflow**

1. Faculty submits exam details.  
2. Subject is validated.  
3. Exam is saved.  
4. Audit log is created.  
5. Notification generated (if required).  
6. Success response returned.

---

# **Sequence Diagram 3 – Student Registration for Exam**

Student  
 │  
 ▼  
RegistrationController  
 │  
 ▼  
RegistrationService  
 │  
 ├─────────────► StudentRepository  
 │  
 ├─────────────► ExamRepository  
 │  
 ├─────────────► RegistrationRepository  
 │  
 ▼  
Database  
 │  
 ▼  
NotificationService  
 │  
 ▼  
Student

### **Business Rules**

* Student exists.  
* Exam exists.  
* Registration window is open.  
* Duplicate registration prevented.

---

# **Sequence Diagram 4 – Start Examination**

Student  
 │  
 ▼  
ExamExecutionController  
 │  
 ▼  
ExamExecutionService  
 │  
 ├────────► ExamRepository  
 │  
 ├────────► AttemptRepository  
 │  
 ▼  
Database  
 │  
 ▼  
IntegrityService  
 │  
 ▼  
Exam Started

### **Activities**

* Validate schedule.  
* Verify registration.  
* Create exam attempt.  
* Start timer.  
* Activate integrity monitoring.

---

# **Sequence Diagram 5 – Save Answer**

Student  
 │  
 ▼  
ExamExecutionController  
 │  
 ▼  
ExamExecutionService  
 │  
 ▼  
StudentResponseRepository  
 │  
 ▼  
Database  
 │  
 ▼  
Success

---

# **Sequence Diagram 6 – Submit Examination**

Student  
 │  
 ▼  
ExamExecutionController  
 │  
 ▼  
ExamExecutionService  
 │  
 ├────────► ResponseRepository  
 │  
 ├────────► IntegrityService  
 │  
 ├────────► EvaluationService  
 │  
 ▼  
Database  
 │  
 ▼  
Submission Successful

---

# **Sequence Diagram 7 – Automatic Evaluation**

EvaluationService  
 │  
 ▼  
QuestionRepository  
 │  
 ▼  
ResponseRepository  
 │  
 ▼  
Calculate Score  
 │  
 ▼  
ResultRepository  
 │  
 ▼  
Database

### **Flow**

* Load responses.  
* Compare MCQ answers.  
* Calculate marks.  
* Store result.

---

# **Sequence Diagram 8 – Result Publication**

Faculty  
 │  
 ▼  
ResultController  
 │  
 ▼  
ResultService  
 │  
 ▼  
ResultRepository  
 │  
 ▼  
Database  
 │  
 ▼  
NotificationService  
 │  
 ▼  
Student

---

# **Sequence Diagram 9 – Integrity Monitoring**

The project uses **browser activity monitoring**, not AI proctoring.

Browser  
 │  
 ▼  
IntegrityController  
 │  
 ▼  
IntegrityService  
 │  
 ▼  
SuspiciousActivityRepository  
 │  
 ▼  
Database  
 │  
 ▼  
Warning Generated

### **Supported Events**

* Tab Switch  
* Window Blur  
* Fullscreen Exit  
* Copy Attempt  
* Paste Attempt  
* Keyboard Shortcut

---

# **Activity Diagram – Login Process**

Start

↓

Enter Credentials

↓

Validate Input

↓

User Exists?

├────────────┐  
│ Yes        │ No  
▼            ▼  
Verify Password   Error

↓

Generate JWT

↓

Return Token

↓

End

---

# **Activity Diagram – Examination Flow**

Start

↓

Student Login

↓

Open Exam

↓

Verify Registration

↓

Start Timer

↓

Answer Questions

↓

Save Answers

↓

Submit Exam

↓

Evaluate

↓

Generate Result

↓

End

---

# **Activity Diagram – Faculty Exam Creation**

Start

↓

Login

↓

Create Exam

↓

Validate Subject

↓

Enter Schedule

↓

Save Exam

↓

Publish Exam

↓

End

---

# **State Machine Diagram – Examination**

Draft

↓

Scheduled

↓

Published

↓

Active

↓

Completed

↓

Evaluated

↓

Result Published

↓

Archived

---

# **State Machine Diagram – Exam Attempt**

Created

↓

Started

↓

In Progress

↓

Submitted

↓

Evaluated

↓

Closed

Special transition:

In Progress

↓

Time Expired

↓

Auto Submitted

---

# **State Machine Diagram – Notification**

Created

↓

Sent

↓

Delivered

↓

Read

↓

Archived

---

# **Communication Diagram – Exam Submission**

Student

↓

ExamExecutionController

↓

ExamExecutionService

↓

StudentResponseRepository

↓

EvaluationService

↓

ResultService

↓

NotificationService

Objects collaborate without direct coupling.

---

# **Communication Diagram – Login**

User

↓

AuthController

↓

AuthService

↓

UserRepository

↓

JWT Service

---

# **End-to-End Request Interaction**

React Frontend

↓

REST Controller

↓

Validation

↓

Service

↓

Repository

↓

Database

↓

Repository

↓

Service

↓

Mapper

↓

Response DTO

↓

Controller

↓

React

---

# **Layer Interaction Rules**

| Layer | Can Communicate With |
| ----- | ----- |
| React | Controller |
| Controller | Service |
| Service | Repository |
| Repository | Database |
| Database | Repository |
| Repository | Service |
| Service | Controller |

No layer may bypass the one directly below it.

---

# **Business Workflow Coverage**

| Workflow | Diagram Type |
| ----- | ----- |
| Login | Sequence \+ Activity |
| Exam Creation | Sequence \+ Activity |
| Candidate Registration | Sequence |
| Start Exam | Sequence |
| Save Answer | Sequence |
| Submit Exam | Sequence \+ Activity |
| Evaluation | Sequence |
| Publish Result | Sequence |
| Integrity Monitoring | Sequence |
| Exam Lifecycle | State Machine |
| Exam Attempt Lifecycle | State Machine |
| Notification Lifecycle | State Machine |

---

# **Engineering Benefits**

| Goal | Benefit |
| ----- | ----- |
| Maintainability | Clear runtime behavior documentation |
| Communication | Easy understanding for developers and reviewers |
| Debugging | Simplifies tracing execution paths |
| Testing | Supports creation of unit and integration test cases |
| Scalability | New workflows can be modeled consistently |
| Enterprise Readiness | Aligns with UML-based software engineering practices |

---

# **Deliverables Produced**

LLD-011 defines:

* ✅ 9 Sequence Diagrams  
* ✅ 3 Activity Diagrams  
* ✅ 3 State Machine Diagrams  
* ✅ 2 Communication Diagrams  
* ✅ Complete end-to-end interaction flow  
* ✅ Layer communication rules  
* ✅ Business workflow documentation

---

# **LLD-011 Status: Complete ✅**

The behavioral design of the Online Examination Platform is now fully documented. Combined with the previous LLD documents, the project now includes both the **static architecture** (packages, classes, APIs, database) and the **dynamic architecture** (runtime interactions and workflows), providing a comprehensive blueprint for implementation.

---

# **Current Project Progress**

At this stage, the following phases are **fully completed**:

* ✅ Requirements Analysis  
* ✅ System Architecture  
* ✅ Module Planning  
* ✅ Technical Decisions (TD-001 to TD-015)  
* ✅ Database Design (DB-001 to DB-011)  
* ✅ API Design (API-001 to API-015)  
* ✅ Low-Level Design (LLD-001 to LLD-011)

## **Next Phase**

The next major phase should be **Implementation Planning & Development**, beginning with:

1. **IMP-001 – Development Roadmap & Sprint Plan**  
2. **IMP-002 – Backend Implementation Order**  
3. **IMP-003 – Frontend Implementation Order**  
4. **IMP-004 – Testing Strategy**  
5. **IMP-005 – Deployment & DevOps Plan**

This sequence will take the project from design into systematic implementation while keeping the architecture aligned with all of the documents created so far.

# SRS

# **Department of Information Technology**

# **Software Requirements Specification** 

**Project Title: Online Examination Platform**

**Team Members:**

| Roll No. | Name |
| :---: | :---: |
| **TI204** | **Om Patil** |
| **TI205** | **Kedar More** |
| **TI207** | **Dron Dhivare**  |
| **TI209** | **Saniya Bhuskute** |
| **TI211** | **Utkranti Yadav** |
| **TI214** | **Hrudyash Supare** |
| **TI215** | **Tushar Manugade** |
| **TI218** | **Srushti Somwanshi** |
| **TI219** | **Rutuja Ghodekar** |
| **TI221** | **Shlok Powar** |
|  | **Arnav Gajghate** |

**Mentor Name: Jitendra Chavan**

1. **Introduction**

**1.1 Problem Statement**  
Educational institutions increasingly require efficient and secure methods for conducting examinations. Traditional paper-based examination systems involve significant manual effort in preparing question papers, scheduling examinations, evaluating answer sheets, and publishing results. These processes are time-consuming, prone to human error, and difficult to manage as the number of students and examinations increases.  
Existing online examination systems often focus only on conducting examinations and may lack centralized management, secure access control, comprehensive reporting, and effective monitoring mechanisms. These limitations reduce administrative efficiency and affect the overall reliability of the examination process.  
The proposed **Online Examination Platform** addresses these challenges by providing a secure, centralized, web-based system that automates the complete examination lifecycle, including user management, examination scheduling, question bank management, online examinations, evaluation, result publication, and reporting.

**1.2 Need for the Project**  
Educational institutions require a modern examination management system to overcome the limitations of manual and partially computerized examination processes. The proposed Online Examination Platform aims to:

* Reduce manual paperwork and administrative workload.  
* Automate examination scheduling and result generation.  
* Improve the accuracy and transparency of examination management.  
* Provide secure access through role-based authentication.  
* Maintain centralized academic and examination records.  
* Enable faster communication between administrators, faculty members, and students.

**1.3 Objectives**  
The primary objectives of the Online Examination Platform are:

* To automate the complete examination management process.  
* To provide secure authentication and role-based access control.  
* To maintain centralized records of users, examinations, and results.  
* To reduce manual effort and processing time.  
* To ensure accurate evaluation and timely publication of results.  
* To generate reports for academic monitoring and decision-making.

**1.4 Scope**  
**In Scope**  
The system provides the following functionalities:

* User authentication and authorization  
* Student and faculty management  
* Department, course, semester, and subject management  
* Examination scheduling and management  
* Question bank management  
* Online examination  
* Automatic and manual evaluation  
* Result generation and publication  
* Notifications and reports  
* Audit logging and browser activity monitoring

**Out of Scope**  
The following features are not included in the current version:

* AI-based online proctoring  
* Face recognition or biometric authentication  
* Mobile application  
* Learning Management System (LMS) integration  
* Payment gateway integration  
* Offline examination support

2. **Problem Identification and Scope**

**2.1 Existing System**  
Many educational institutions continue to rely on manual or partially computerized examination systems. Activities such as examination scheduling, question paper preparation, student registration, answer evaluation, and result publication are often handled manually or using separate software applications. This leads to fragmented data management, increased administrative workload, and delays in the examination process.  
Although some institutions use online examination platforms, many existing systems provide limited functionality and lack centralized management, comprehensive reporting, and secure role-based access.

**2.2 Limitations of the Existing System**  
The existing examination process has several limitations:

* Time-consuming examination scheduling and administration.  
* Manual evaluation resulting in delayed result publication.  
* Increased chances of human error during data entry and result preparation.  
* Lack of centralized storage for academic and examination records.  
* Limited security and access control mechanisms.  
* Difficulty in generating reports and monitoring examination activities.

**2.3 Proposed System**  
The proposed **Online Examination Platform** is a secure, web-based application that automates the complete examination lifecycle. The system provides a centralized platform for managing users, academic information, examinations, question banks, online assessments, evaluations, and reports.  
The platform supports three primary user roles:

* **Administrator** – Manages users, examinations, academic records, and system configuration.  
* **Faculty** – Creates question banks, schedules examinations, evaluates responses, and publishes results.  
* **Student** – Registers for examinations, attempts online examinations, and views results and notifications.

The application is developed using **Python (Flask)** as the backend framework, **MySQL** as the relational database, and **HTML5, CSS3, Bootstrap, and JavaScript** for the frontend.

**2.4 Advantages of the Proposed System**  
The proposed system offers the following advantages over the existing process:

* Centralized management of examination activities.  
* Reduced manual work and paperwork.  
* Faster examination scheduling and result generation.  
* Secure authentication with Role-Based Access Control (RBAC).  
* Automatic evaluation of objective questions.  
* Improved transparency and data accuracy.  
* Easy generation of reports and dashboards.  
* Scalable architecture for future institutional growth.

**2.5 Expected Benefits**  
Implementation of the Online Examination Platform provides benefits to all stakeholders.

| Stakeholder | Expected Benefits |
| :---- | :---- |
| Administrator | Simplified system administration and centralized management |
| Faculty | Efficient examination creation, evaluation, and reporting |
| Student | Convenient online examinations and quick access to results |
| Institution | Reduced operational cost, improved efficiency, and enhanced transparency |

3. **Feasibility Study**

**3.1 Introduction**  
A feasibility study evaluates whether the proposed Online Examination Platform can be successfully developed and implemented within the available technical resources, budget, and project timeline. It examines the project from technical, economic, and operational perspectives to determine its practicality and viability.

**3.2 Technical Feasibility**  
The proposed system is technically feasible because it is developed using modern, open-source technologies that are widely used in web application development. The selected technology stack is reliable, scalable, and supported by extensive documentation and community resources.  
Technology Stack

| Component | Technology |
| :---- | :---- |
| Programming Language | Python 3.13 |
| Backend Framework | Flask |
| Frontend | HTML5, CSS3, Bootstrap 5, JavaScript |
| Database | MySQL 8 |
| ORM | SQLAlchemy |
| IDE | Visual Studio Code |
| Version Control | Git & GitHub |
| API Testing | Postman |

The proposed hardware and software requirements are readily available, making the project technically achievable.

**3.3 Economic Feasibility**  
The Online Examination Platform is economically feasible because it is developed primarily using open-source software, eliminating licensing costs. Existing computers and internet facilities can be used for development and deployment, minimizing infrastructure expenses.  
The expected benefits, such as reduced paperwork, lower administrative workload, and faster examination processing, outweigh the implementation costs.

**3.4 Operational Feasibility**  
The system is designed to be user-friendly and can be easily operated by administrators, faculty members, and students with basic computer knowledge. The web-based interface requires minimal training and integrates smoothly with existing academic workflows.  
The platform improves operational efficiency by automating examination scheduling, evaluation, result generation, and record management.

**3.5 Project Scope**  
The Online Examination Platform includes the following major modules:

* Authentication and Authorization  
* User Management  
* Student and Faculty Management  
* Academic Management  
* Examination Management  
* Question Bank Management  
* Online Examination  
* Evaluation and Result Management  
* Notification Management  
* Reports and Dashboard  
* Audit Logging  
* Backup and Recovery

Project Deliverables  
The project will deliver:

* Software Requirements Specification (SRS)  
* Database Design  
* UML Diagrams  
* Source Code  
* Test Cases  
* User Documentation  
* Final Project Report

4. **Stakeholder Analysis**

**4.1 Introduction**  
Stakeholders are individuals or groups who interact with or are affected by the Online Examination Platform. Identifying stakeholders helps ensure that the system meets the needs of all users while supporting efficient examination management. The platform primarily serves administrators, faculty members, students, and institutional management.

**4.2 Stakeholder Analysis**  
The major stakeholders of the Online Examination Platform and their roles are summarized below.

| Stakeholder | Role | Responsibilities | Expectations |
| :---- | :---- | :---- | :---- |
| **Administrator** | System Administrator | Manage users, departments, examinations, reports, notifications, and system settings. | Secure, centralized, and easy-to-manage system. |
| **Faculty** | Academic User | Create question banks, schedule examinations, evaluate answers, and publish results. | Efficient examination management and quick evaluation. |
| **Student** | End User | Register for examinations, attempt online exams, and view results and notifications. | Simple, secure, and reliable examination experience. |
| **Institution Management** | Monitoring Authority | Review examination reports, monitor academic performance, and support decision-making. | Accurate reports and performance analytics. |
| **System Administrator** *(Optional)* | Technical Support | Maintain the application, database, backups, and security. | Stable, secure, and maintainable system. |

**4.3 Stakeholder Requirements**  
The following table summarizes the primary requirements of each stakeholder.

| Stakeholder | Primary Requirements |
| :---- | :---- |
| Administrator | User management, examination management, reports, audit logs, system configuration |
| Faculty | Question bank management, examination scheduling, evaluation, result publication |
| Student | Secure login, online examination, notifications, result viewing |
| Institution Management | Reports, dashboards, and examination statistics |
| System Administrator | Backup, recovery, database maintenance, and system security |

5. **Functional Requirements**

**5.1 Introduction**  
Functional requirements define the core functionalities that the Online Examination Platform must provide to meet the needs of administrators, faculty members, and students. These requirements describe the services offered by the system and form the basis for system design, implementation, and testing.  
The platform follows **Role-Based Access Control (RBAC)**, ensuring that users can access only the functionalities permitted by their assigned roles.

**5.2 Functional Requirements**

| Requirement ID | Functional Requirement | Description |
| :---- | :---- | :---- |
| **FR-01** | User Authentication | The system shall authenticate users using valid credentials and provide secure role-based access. |
| **FR-02** | User Management | The administrator shall create, update, activate, deactivate, and manage user accounts. |
| **FR-03** | Student Management | The system shall maintain student records, academic details, and examination eligibility. |
| **FR-04** | Faculty Management | The system shall manage faculty profiles and subject assignments. |
| **FR-05** | Academic Management | The system shall manage departments, courses, semesters, and subjects. |
| **FR-06** | Examination Management | The system shall create, schedule, update, publish, and manage examinations. |
| **FR-07** | Question Bank Management | Faculty shall create, organize, edit, and maintain objective and subjective questions. |
| **FR-08** | Examination Registration | Eligible students shall register for available examinations. |
| **FR-09** | Online Examination | Students shall attempt examinations online with timer support and automatic response saving. |
| **FR-10** | Browser Activity Monitoring | The system shall monitor browser events such as tab switching and fullscreen exit during examinations. |
| **FR-11** | Evaluation & Result Management | The system shall evaluate objective answers automatically, support manual evaluation of subjective answers, and generate results. |
| **FR-12** | Notification Management | The system shall notify users about examination schedules, announcements, and published results. |
| **FR-13** | Dashboard & Reports | The system shall provide dashboards and generate reports for administrators and faculty. |
| **FR-14** | Audit Logging | The system shall record important user activities for monitoring and accountability. |
| **FR-15** | Backup & Recovery | The system shall support backup and restoration of application data. |
| **FR-16** | System Configuration | The administrator shall configure application settings, security policies, and examination parameters. |

**5.3 Actor-wise Functional Requirements**  
The following table summarizes the functionalities available to each user role.

| Actor | Major Functionalities |
| :---- | :---- |
| **Administrator** | Manage users, departments, courses, subjects, examinations, notifications, reports, audit logs, backups, and system configuration. |
| **Faculty** | Manage question bank, create examinations, evaluate student responses, publish results, and view reports. |
| **Student** | Login, register for examinations, attempt online examinations, view notifications, and access examination results. |

**5.4 Functional Requirement Summary**  
The Online Examination Platform provides the following key capabilities:

* Secure user authentication and authorization.  
* Centralized management of academic and examination records.  
* Examination scheduling and online examination support.  
* Question bank creation and management.  
* Automatic and manual evaluation of examinations.  
* Result generation and publication.  
* Browser activity monitoring during examinations.  
* Notification and reporting facilities.  
* Audit logging and secure backup management.

6. **Non-Functional Requirements**

**6.1 Introduction**  
Non-functional requirements specify the quality attributes and operational characteristics of the Online Examination Platform. These requirements define how the system should perform with respect to performance, security, reliability, usability, and maintainability. They ensure that the platform delivers a secure, efficient, and user-friendly experience while supporting institutional examination processes.

**6.2 Non-Functional Requirements**

| Category | Requirement |
| :---- | :---- |
| **Performance** | The system shall provide fast response times, support multiple concurrent users, and automatically save examination responses during online examinations. |
| **Security** | The system shall implement secure authentication, Role-Based Access Control (RBAC), password hashing, HTTPS communication, and protection against common web security threats. |
| **Reliability** | The system shall maintain data integrity, ensure consistent operation during examinations, and support backup and recovery mechanisms. |
| **Availability** | The platform shall be available during scheduled examination periods, except for planned maintenance. |
| **Usability** | The application shall provide an intuitive interface that is easy to learn and operate for administrators, faculty members, and students. |
| **Scalability** | The system shall support future growth in the number of users, departments, subjects, and examinations without major architectural changes. |
| **Maintainability** | The software shall follow a modular architecture with well-structured code and documentation to simplify maintenance and future enhancements. |
| **Portability** | The application shall operate on Windows and Linux servers and be accessible through modern web browsers. |
| **Compatibility** | The system shall be compatible with Python, Flask, MySQL, HTML5, CSS3, Bootstrap, and JavaScript technologies. |
| **Browser Integrity** | During online examinations, the system shall record browser events such as tab switching and fullscreen exit to support examination integrity. |

**6.3 Security Requirements**  
To ensure confidentiality, integrity, and availability of examination data, the system shall:

* Authenticate users before granting access.  
* Implement Role-Based Access Control (RBAC).  
* Store passwords using secure hashing algorithms.  
* Protect communication using HTTPS.  
* Validate user input to prevent common web attacks.  
* Record important activities through audit logs.

**6.4 Performance Requirements**  
The system shall be capable of:

* Supporting multiple users simultaneously.  
* Providing quick response times for common operations.  
* Automatically saving student responses during examinations.  
* Generating examination results and reports efficiently.

7. **System Requirements**

**7.1 Introduction**  
The Online Examination Platform is a web-based application designed to operate on standard computing devices with minimal hardware and software requirements. This chapter specifies the minimum system configuration required for the development, deployment, and operation of the application.

**7.2 Hardware Requirements**  
**Client-Side Requirements**

| Component | Minimum Requirement |
| :---- | :---- |
| Processor | Dual-Core Processor |
| RAM | 4 GB |
| Storage | 500 MB Free Space |
| Display | 1366 × 768 Resolution |
| Internet Connection | Stable Broadband Connection |

**Server-Side Requirements**

| Component | Recommended Requirement |
| :---- | :---- |
| Processor | Intel Core i5 or Higher |
| RAM | 8 GB or Higher |
| Storage | SSD (Minimum 100 GB Free Space) |
| Operating System | Linux Server / Windows Server |
| Internet Connection | High-Speed Broadband |

**7.3 Software Requirements**

| Component | Specification |
| :---- | :---- |
| Operating System | Windows 10/11 or Linux |
| Programming Language | Python 3.13 |
| Backend Framework | Flask |
| Frontend Technologies | HTML5, CSS3, Bootstrap 5, JavaScript |
| Database | MySQL 8 |
| ORM | SQLAlchemy |
| IDE | Visual Studio Code |
| Version Control | Git & GitHub |
| API Testing Tool | Postman |

**7.4 Browser Requirements**  
The application can be accessed using any modern web browser that supports HTML5 and JavaScript.  
**Supported Browsers:**

* Google Chrome  
* Mozilla Firefox  
* Microsoft Edge

**7.5 Network Requirements**  
The system requires:

* Stable internet connectivity.  
* HTTPS for secure communication.  
* TCP/IP network support.  
* Reliable network availability during online examinations.  
8. **Use Case Diagram**

**8.1 Introduction**  
A Use Case Diagram is a Unified Modeling Language (UML) diagram that illustrates the interactions between the users and the Online Examination Platform. It provides a high-level view of the system by identifying the primary actors and the major functionalities available to them.  
The platform consists of three primary actors:

* **Administrator**  
* **Faculty**  
* **Student**

Each actor interacts with the system according to the permissions assigned through Role-Based Access Control (RBAC).

**8.2 Use Case Diagram**  
> **![][image1]**  
**Figure 8.1:** *Use Case Diagram of the Online Examination Platform*

**8.3 Actor–Use Case Summary**

| Actor | Major Use Cases |
| :---- | :---- |
| **Administrator** | Manage users, departments, subjects, examinations, notifications, reports, audit logs, backups, and system settings. |
| **Faculty** | Manage question bank, create examinations, evaluate responses, publish results, and view reports. |
| **Student** | Register for examinations, attempt online examinations, view notifications, and access results. |

9. **Use Case Descriptions**

**9.1 Introduction**  
This chapter provides detailed descriptions of the major use cases of the Online Examination Platform. Each use case defines the interaction between the system and its users, including the actor, preconditions, main flow, alternate flow, and postconditions.

**UC-01: User Login**

| Attribute | Description |
| :---- | :---- |
| **Use Case ID** | UC-01 |
| **Use Case Name** | User Login |
| **Primary Actor** | Administrator, Faculty, Student |
| **Description** | Authenticates users and grants access based on their assigned role. |
| **Preconditions** | User account exists and is active. |
| **Postconditions** | User is successfully logged into the system. |

Main Flow

1. User enters login credentials.  
2. System validates the credentials.  
3. User is authenticated.  
4. Appropriate dashboard is displayed.

Alternate Flow

* Invalid username or password.  
* Account is inactive or suspended.

**UC-02: Create Examination**

| Attribute | Description |
| :---- | :---- |
| **Use Case ID** | UC-02 |
| **Use Case Name** | Create Examination |
| **Primary Actor** | Administrator, Faculty |
| **Description** | Allows authorized users to create and schedule examinations. |
| **Preconditions** | User is authenticated. |
| **Postconditions** | Examination is successfully created. |

Main Flow

1. User enters examination details.  
2. Selects subject and schedule.  
3. Assigns questions.  
4. Saves the examination.

Alternate Flow

* Invalid schedule.  
* Mandatory information missing.

UC-03: Attempt Online Examination

| Attribute | Description |
| :---- | :---- |
| **Use Case ID** | UC-03 |
| **Use Case Name** | Attempt Online Examination |
| **Primary Actor** | Student |
| **Description** | Enables registered students to participate in an online examination. |
| **Preconditions** | Student is registered and examination is active. |
| **Postconditions** | Student responses are submitted successfully. |

Main Flow

1. Student starts the examination.  
2. Questions are displayed.  
3. Student answers the questions.  
4. Responses are automatically saved.  
5. Student submits the examination.

Alternate Flow

* Examination time has expired.  
* Student is not registered.

**UC-04: Evaluate Examination**

| Attribute | Description |
| :---- | :---- |
| **Use Case ID** | UC-04 |
| **Use Case Name** | Evaluate Examination |
| **Primary Actor** | Faculty |
| **Description** | Evaluates student responses and prepares examination results. |
| **Preconditions** | Examination has been completed. |
| **Postconditions** | Student marks are finalized. |

Main Flow

1. Faculty reviews submitted answers.  
2. Objective questions are evaluated automatically.  
3. Subjective questions are evaluated manually.  
4. Final marks are calculated.

Alternate Flow

* Evaluation is incomplete.  
* Student responses are unavailable.

**UC-05: View Results**

| Attribute | Description |
| :---- | :---- |
| **Use Case ID** | UC-05 |
| **Use Case Name** | View Results |
| **Primary Actor** | Student |
| **Description** | Allows students to view published examination results. |
| **Preconditions** | Results have been published. |
| **Postconditions** | Student can view examination performance. |

Main Flow

1. Students log into the system.  
2. Open the Results module.  
3. The system displays marks, grades, and examination status.

Alternate Flow

* Results have not yet been published.

**9.2 Use Case Summary**

| Use Case ID | Use Case Name | Primary Actor |
| :---- | :---- | :---- |
| UC-01 | User Login | Administrator, Faculty, Student |
| UC-02 | Create Examination | Administrator, Faculty |
| UC-03 | Attempt Online Examination | Student |
| UC-04 | Evaluate Examination | Faculty |
| UC-05 | View Results | Student |

**10\. Data Requirements**  
**10.1 Introduction**  
The Online Examination Platform uses a relational database to store and manage information related to users, academic records, examinations, questions, student responses, results, notifications, and system activities. The database is designed to ensure data consistency, integrity, and security while supporting efficient retrieval and management of information.  
The system uses **MySQL 8** as the database management system, and the database is normalized to **Third Normal Form (3NF)** to reduce redundancy and maintain data integrity.

**10.2 Database Overview**  
The database follows a relational model where all entities are interconnected through primary and foreign key relationships. It supports all major functional modules of the Online Examination Platform.  
Key Features

* Centralized data storage  
* Relational database design  
* Primary and Foreign Key relationships  
* Data validation and integrity constraints  
* Secure storage of user information  
* Support for backup and recovery

**10.3 Major Database Entities**  
The database consists of multiple related tables grouped according to the functional modules of the system.

| Module | Major Entities |
| :---- | :---- |
| Authentication & Authorization | Users, Roles, Permissions |
| Academic Management | Departments, Courses, Semesters, Subjects |
| Student & Faculty Management | Students, Faculty, Faculty Subject Assignments |
| Examination Management | Examinations, Examination Registrations, Examination Questions |
| Question Bank | Questions, Question Options |
| Online Examination | Examination Sessions, Student Answers |
| Evaluation & Results | Results |
| Notification Management | Notifications |
| System Administration | Audit Logs, Browser Integrity Logs, System Configurations, Backup History |

> **Note:** The complete database schema consists of **24 normalized tables**. Detailed table structures, attributes, constraints, and SQL definitions are provided in the **Database Design Document (DDD)**.

**10.4 Entity Relationships**  
The major relationships within the database are summarized below:

* A **Role** can be assigned to multiple **Users**.  
* A **Department** offers multiple **Courses** and **Subjects**.  
* A **Course** consists of multiple **Semesters**.  
* A **Faculty** member may teach multiple **Subjects**.  
* A **Student** can register for multiple **Examinations**.  
* An **Examination** contains multiple **Questions**.  
* An **Examination Session** stores the responses submitted by a student.  
* A **Result** is generated after evaluation of the examination.  
* **Audit Logs** maintain records of important system activities.

**10.5 Entity Relationship Diagram (ER Diagram)**  
The Entity Relationship Diagram (ERD) illustrates the logical structure of the database and the relationships among different entities used by the Online Examination Platform.  
> **Figure 10.1:** *Entity Relationship Diagram of the Online Examination Platform*  
**(Insert the finalized ER Diagram here.)**

**11\. Assumptions and Constraints**  
**11.1 Introduction**  
The development of the Online Examination Platform is based on certain assumptions regarding the operating environment and user behavior. The project is also subject to technical, operational, and resource constraints that influence its implementation and deployment.

**11.2 Assumptions**  
The following assumptions have been made during the development of the system:

* Users have a stable internet connection while accessing the application.  
* Every user possesses valid login credentials issued by the institution.  
* Administrators maintain accurate academic and examination data.  
* Users access the application using a supported web browser.  
* The server and database remain available during scheduled examination periods.  
* Users comply with institutional examination policies and guidelines.

**11.3 Constraints**  
The Online Examination Platform is developed under the following constraints:

* The system is designed as a **web-based application**.  
* Development is carried out using **Python, Flask, and MySQL**.  
* The project must be completed within the academic semester timeline.  
* Only browser-based activity monitoring is implemented; AI-based proctoring is excluded.  
* The application requires internet connectivity for normal operation.  
* Development is limited to available resources and open-source technologies.

**12\. Future Enhancements**  
**12.1 Introduction**  
The Online Examination Platform has been designed using a modular architecture, allowing new features and technologies to be incorporated with minimal changes to the existing system. While the current version fulfills the essential requirements of online examination management, several enhancements can be implemented in future releases to improve functionality, security, and user experience.

**12.2 Proposed Future Enhancements**  
The following enhancements may be considered for future versions of the system:

* **AI-Based Online Proctoring:** Integration of artificial intelligence to monitor examination activities using webcam analysis and suspicious behavior detection.  
* **Mobile Application:** Development of Android and iOS applications for convenient access to examinations, notifications, and results.  
* **Learning Management System (LMS) Integration:** Integration with platforms such as Moodle or Google Classroom for seamless academic management.  
* **Advanced Analytics:** Interactive dashboards with graphical reports, student performance trends, and examination statistics.  
* **Cloud Deployment:** Deployment on cloud platforms to improve scalability, availability, and disaster recovery.  
* **Multi-Factor Authentication (MFA):** Additional authentication mechanisms such as OTP or authenticator applications to strengthen account security.  
* **Automated Question Paper Generation:** Intelligent generation of question papers using predefined rules and randomized question selection.

**References**  
The following references were consulted during the analysis, design, and development of the **Online Examination Platform**.  
**Standards**

1. IEEE Std 29148-2018, *Systems and Software Engineering – Life Cycle Processes – Requirements Engineering*.  
2. IEEE Std 830-1998, *Recommended Practice for Software Requirements Specifications*.  
3. ISO/IEC 25010:2011, *Systems and Software Engineering – System and Software Quality Models*.

**Books**

1. Sommerville, I. (2016). *Software Engineering* (10th Edition). Pearson Education.  
2. Pressman, R. S., & Maxim, B. R. (2019). *Software Engineering: A Practitioner's Approach* (9th Edition). McGraw-Hill Education.  
3. Silberschatz, A., Korth, H. F., & Sudarshan, S. (2019). *Database System Concepts* (7th Edition). McGraw-Hill Education.  
4. Elmasri, R., & Navathe, S. B. (2016). *Fundamentals of Database Systems* (7th Edition). Pearson Education.

**Official Documentation**

* Python Software Foundation. *Python Documentation*.  
* Pallets Projects. *Flask Documentation*.  
* Oracle Corporation. *MySQL 8 Reference Manual*.  
* SQLAlchemy Authors. *SQLAlchemy Documentation*.  
* Bootstrap Team. *Bootstrap Documentation*.  
* Mozilla Developer Network (MDN). *JavaScript Documentation*.

**Online Resources**

* OWASP Foundation – Web Application Security Guidelines  
* W3C HTML5 and CSS Standards  
* Git Documentation  
* GitHub Documentation

**Development Tools**  
The following software tools were used during the development of the project:

| Tool | Purpose |
| :---: | :---: |
| Visual Studio Code | Source Code Development |
| MySQL Workbench | Database Design and Management |
| Git & GitHub | Version Control |
| Postman | API Testing |
| Draw.io | UML and ER Diagram Design |

[image1]: <data:image/png;base64,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>