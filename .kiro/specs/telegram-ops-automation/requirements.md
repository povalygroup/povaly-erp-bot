# Requirements Document

## Introduction

The Telegram Operations Automation System is a comprehensive enterprise-grade bot that manages task workflows, QA reviews, attendance tracking, and automated reporting for Povaly Group. The system uses Telegram's native reaction mechanism as the primary state engine, enabling seamless team coordination across multiple logical topic channels within a single Telegram group. The system supports 50-500 concurrent users and handles 1000+ daily operations with automated daily and weekly performance reporting.

All system configuration is managed through a .env file, providing complete flexibility to configure every aspect of the system without code changes. The system implements role-based access control with four user roles (Administrator, Manager, QA Reviewer, Regular User) and enforces granular permissions across all topics.

## Environment Configuration Reference

The system requires a comprehensive .env file with the following configuration parameters:

### Bot Configuration
- `TELEGRAM_BOT_TOKEN`: Telegram Bot API token (required)
- `TELEGRAM_GROUP_ID`: Telegram group ID where the bot operates (required)

### Database Configuration
- `DATABASE_TYPE`: Database type - sqlite, mongodb, or json (default: sqlite)
- `DATABASE_PATH`: Path to database file (default: ./data/povaly_bot.db)
- `DATABASE_BACKUP_TIME`: Daily backup time in HH:MM format GMT+6 (default: 23:00)

### Timezone
- `TIMEZONE`: System timezone (default: GMT+6)

### Topic IDs
All topic IDs are Telegram thread IDs (required):
- `TOPIC_OFFICIAL_DIRECTIVES`: Official announcements and directives
- `TOPIC_BRAND_REPOSITORY`: Brand assets and resources
- `TOPIC_TASK_ALLOCATION`: Task creation and assignment
- `TOPIC_CORE_OPERATIONS`: Work discussions and collaboration
- `TOPIC_QA_REVIEW`: Quality assurance submissions and reviews
- `TOPIC_CENTRAL_ARCHIVE`: Approved task archive
- `TOPIC_DAILY_SYNC`: Automated daily and weekly reports
- `TOPIC_ATTENDANCE_LEAVE`: Attendance tracking and leave requests
- `TOPIC_ADMIN_CONTROL_PANEL`: Management escalations and alerts
- `TOPIC_STRATEGIC_LOUNGE`: Strategic discussions and casual communication

### User Roles
Comma-separated Telegram user IDs:
- `ADMINISTRATORS`: Users with full system access
- `MANAGERS`: Users with elevated permissions and leave approval
- `QA_REVIEWERS`: Users authorized to approve/reject QA submissions
- `OWNERS`: Users with ownership-level privileges

### Inactivity Thresholds
All values in hours:
- `INACTIVITY_WARNING_HOURS`: Hours before warning (default: 18)
- `INACTIVITY_MARK_HOURS`: Hours before marking inactive (default: 24)
- `INACTIVITY_ESCALATE_HOURS`: Hours before manager escalation (default: 48)
- `INACTIVITY_CRITICAL_HOURS`: Hours before critical escalation (default: 72)

### Attendance Configuration
All times in HH:MM format GMT+6:
- `ATTENDANCE_LATE_CHECKIN_TIME`: Time after which check-in is considered late (default: 11:00)
- `ATTENDANCE_AUTO_CHECKOUT_TIME`: Time for automatic check-out (default: 23:59)
- `ATTENDANCE_EXPECTED_CHECKOUT_TIME`: Expected end of workday (default: 17:00)

### Report Scheduling
- `DAILY_REPORT_TIME`: Time for daily report generation in HH:MM format GMT+6 (default: 22:30)
- `WEEKLY_REPORT_DAY`: Day of week for weekly report (default: Sunday)
- `WEEKLY_REPORT_TIME`: Time for weekly report in HH:MM format GMT+6 (default: 22:30)

### Daily Summary Configuration
- `DAILY_SUMMARY_TIME`: Time for daily summary message in HH:MM format GMT+6 (default: 00:00)
- `FEATURE_DAILY_SUMMARY`: Enable/disable daily summary messages (default: true)

### Violation Handling
- `VIOLATION_AUTO_DELETE_MALFORMED`: Auto-delete malformed messages (default: true)
- `VIOLATION_REPEATED_THRESHOLD`: Violations per week before escalation (default: 3)
- `VIOLATION_REPEATED_ACTION`: Action for repeated violations - escalate_to_manager, log_only, or temporary_restriction (default: escalate_to_manager)

### Brand Codes
- `BRAND_CODES`: Comma-separated list of valid brand codes (e.g., PV,VB,XY,ZZ)

### Ticket Format Validation
- `TICKET_FORMAT_REGEX`: Regex pattern for ticket validation (default: ^[A-Z]{2}-\d{4}-\d+$)

### Notification Preferences
- `NOTIFICATION_SEND_DM`: Enable direct message notifications (default: true)
- `NOTIFICATION_SEND_TOPIC_ALERTS`: Enable topic-based alerts (default: true)
- `NOTIFICATION_INCLUDE_MESSAGE_LINKS`: Include clickable links in notifications (default: true)

### Performance Monitoring
- `PERFORMANCE_QA_REJECTION_THRESHOLD`: QA rejection rate threshold (default: 0.5 = 50%)
- `PERFORMANCE_DORMANCY_DAYS`: Days without task completion before dormancy alert (default: 7)
- `PERFORMANCE_LATE_CHECKIN_THRESHOLD`: Late check-ins per week before alert (default: 5)

### Security
- `DATABASE_ENCRYPTION_KEY`: Encryption key for sensitive data (required)
- `LOG_RETENTION_DAYS`: Days to retain log files (default: 30)
- `AUDIT_TRAIL_RETENTION_DAYS`: Days to retain audit trail records (default: 90)

### Feature Flags
- `FEATURE_AUTO_CHECKOUT`: Enable automatic check-out (default: true)
- `FEATURE_AUTO_REMEDIATION`: Enable automatic issue resolution (default: true)
- `FEATURE_PREDICTIVE_ALERTS`: Enable predictive performance alerts (default: true)
- `FEATURE_ANALYTICS_DASHBOARD`: Enable analytics dashboard (default: true)
- `FEATURE_DAILY_SUMMARY`: Enable daily summary messages (default: true)

## Topic Permission Matrix

The system enforces the following permission matrix across all topics:

| Topic | Regular Users | QA Reviewers | Managers | Admins/Owners |
|-------|--------------|--------------|----------|---------------|
| Official Directives | Read | Read | Read + Edit | Read + Edit |
| Brand Repository | Read | Read | Read + Edit | Read + Edit |
| Task Allocation | Read + Write | Read + Write | Read + Write | Read + Write + Delete |
| Core Operations | Read + Write | Read + Write | Read + Write | Read + Write + Delete |
| QA & Review | Read + Write | Read + Write + React | Read + Write + React | Full Control |
| Central Archive | Read | Read | Read + Edit | Read + Edit + Delete |
| Daily Sync | Read | Read | Read + Edit | Read + Edit + Delete |
| Attendance & Leave | Read + Write | Read + Write | Read + Write + Approve | Full Control |
| Admin Control Panel | No Access | No Access | Read + Write | Full Control |
| Strategic/Lounge | Read + Write | Read + Write | Read + Write | Read + Write |

**Permission Definitions:**
- **Read**: View messages and content
- **Write**: Post new messages
- **Edit**: Modify existing messages
- **Delete**: Remove messages
- **React**: Add emoji reactions for state transitions
- **Approve**: Approve leave requests and administrative actions
- **Full Control**: All permissions including configuration and user management

## Glossary

- **Bot**: The Telegram bot application that monitors messages, reactions, and generates reports
- **Topic**: A logical channel within the Telegram group (e.g., Task Allocation, QA & Review)
- **Task**: A work item identified by a unique TICKET identifier
- **TICKET**: A unique alphanumeric identifier for a task (e.g. PV-2404-1, VB-2404-1, format is BRAND-DDMM-unique number sequentially manually added)
- **BRAND**: A product or brand identifier within Povaly Group
- **ASSET**: A deliverable or work product (e.g., video, image, document)
- **Reaction**: A Telegram emoji reaction on a message (👍, ❤️, 👎)
- **State_Engine**: The component that tracks task state transitions based on reactions
- **QA_Submission**: A message in QA & Review topic following format [TICKET][BRAND][ASSET]
- **Reject_Feedback**: A structured message indicating QA rejection with format [TICKET][ISSUE_TYPE][PROBLEM][FIX_REQUIRED][ASSIGNEE]
- **Daily_Sync**: An automated report generated at 22:30 GMT+6 showing daily task progress per user
- **Weekly_Report**: An automated performance report generated on Sundays at 22:30 GMT+6
- **Assignee**: A user assigned to complete a task
- **QA_Reviewer**: A user authorized to approve or reject QA submissions
- **Archive**: The Central Archive topic containing only approved tasks
- **Attendance_Record**: A check-in or check-out timestamp for a user
- **Leave_Request**: A formal request for time off submitted through the system
- **Inactivity_Threshold**: The time period after which a task without 👍 reaction is marked INACTIVE
- **Database**: The persistent storage system (SQLite, MongoDB, or JSON) for all system data
- **Scheduler**: The cron job system that triggers automated reports and checks
- **Message_Parser**: The component that extracts structured data from Telegram messages
- **Reaction_Tracker**: The component that monitors and records reaction events in real-time
- **Administrator**: A user with full system access including configuration, security, and all topic permissions
- **Manager**: A user with elevated permissions including leave approval, performance review, and access to Admin Control Panel
- **Owner**: A user with ownership-level access equivalent to Administrator privileges
- **Regular_User**: A standard team member with basic read/write permissions in work topics
- **Violation_Event**: A detected breach of system rules including format violations, workflow violations, or permission violations
- **Audit_Trail**: A comprehensive log of all system events with full context for compliance and debugging
- **Admin_Control_Panel**: A dedicated topic for management escalations, security alerts, and administrative commands
- **Escalation**: A notification sent to managers or administrators for critical issues requiring intervention
- **Auto_Remediation**: Automated corrective actions taken by the system to resolve violations or conflicts
- **Performance_Metric**: A quantitative measure of user productivity including completion rate, QA approval rate, and response time
- **Inactivity_Warning**: A notification sent to a user when their task approaches the inactivity threshold
- **Progressive_Escalation**: A multi-tier alert system that increases in severity over time
- **Notification_Router**: The component that determines the appropriate delivery channel for each notification type
- **Direct_Message**: A private Telegram message sent to an individual user
- **Topic_Permission**: Access control rules defining read, write, edit, and delete permissions per topic and role
- **Violation_Detection_Engine**: The component that monitors system activity and identifies rule violations
- **Smart_Notification**: Context-aware notifications routed to the appropriate channel based on event type and audience
- **Daily_Summary_Message**: An automated message posted at midnight in Task Allocation topic showing the date, starting ticket ID, and incomplete tasks from previous days
- **Fire_Emoji_Exemption**: A 🔥 reaction added by authorized users (Administrator, Manager, or Owner) to exclude a task from appearing in daily carryover lists
- **Starting_Ticket_ID**: The first ticket ID that should be used for new tasks on a given day, calculated sequentially from the previous day's highest ticket number
- **Task_Carryover**: Incomplete tasks from previous days that are included in the Daily_Summary_Message
- **QA_Daily_Summary_Message**: An automated message posted at midnight in QA & Review topic showing pending QA submissions, rejected tasks needing rework, and QA review bottlenecks
- **Message_Link**: A clickable Telegram URL linking to a specific message in format `https://t.me/c/GROUP_ID/MESSAGE_ID`
- **Time_Ago_Format**: A human-readable relative time format (e.g., "2h ago", "3d ago", "1w ago")
- **Grouped_Message**: A message that organizes items by a common attribute (assignee, reviewer) for easy scanning

## Requirements

### Requirement 1: Task Creation and Assignment

**User Story:** As a project manager, I want to create and assign tasks in the Task Allocation topic, so that team members receive clear work assignments with unique identifiers.

#### Acceptance Criteria

1. WHEN a message containing a TICKET identifier is posted in Task Allocation topic, THE Bot SHALL create a new task record in the Database
2. THE Bot SHALL prevent duplicate task creation for the same TICKET identifier
3. WHEN a task is created, THE Bot SHALL extract the Assignee from the message content
4. THE Bot SHALL initialize the task state as ASSIGNED
5. WHEN a task is created, THE Bot SHALL record the creation timestamp and creator user ID

### Requirement 2: Reaction-Based State Transitions

**User Story:** As a team member, I want to use emoji reactions to update task status, so that I can quickly signal progress without typing status messages.

#### Acceptance Criteria

1. WHEN a 👍 reaction is added to a task message in Task Allocation topic, THE State_Engine SHALL transition the task state from ASSIGNED to STARTED
2. WHEN a ❤️ reaction is added to a QA_Submission message in QA & Review topic, THE State_Engine SHALL transition the task state to APPROVED
3. WHEN a 👎 reaction is added to a QA_Submission message in QA & Review topic, THE State_Engine SHALL transition the task state to REJECTED
4. THE Reaction_Tracker SHALL record the user ID, timestamp, and reaction type for every reaction event in Task Allocation topic only
5. WHEN multiple reactions of the same type are added, THE State_Engine SHALL use the first reaction timestamp as the transition time
6. THE State_Engine SHALL ignore reaction removals and only process reaction additions
7. THE Reaction_Tracker SHALL track 👍 reactions exclusively in Task Allocation topic where the task was originally created

### Requirement 3: QA Submission Validation

**User Story:** As a team member, I want to submit completed work for QA review using a structured format, so that reviewers can validate my deliverables.

#### Acceptance Criteria

1. WHEN a message matching format [TICKET][BRAND][ASSET] is posted in QA & Review topic, THE Message_Parser SHALL extract the TICKET, BRAND, and ASSET fields
2. THE Bot SHALL validate that the TICKET exists in the Database before accepting the QA_Submission
3. WHEN a valid QA_Submission is detected, THE Bot SHALL transition the task state to QA_SUBMITTED
4. THE Bot SHALL store only the latest QA_Submission per TICKET, overwriting previous submissions
5. WHEN a QA_Submission is created, THE Bot SHALL record the submitter user ID and submission timestamp
6. WHEN a QA_Submission is wrong format, that has not same pattern where bot can detect [] bracket and found the requirements that to make this as bot can use that for track, that will be deleted auto and send that user a personal message for that QA_Submission deletion and re-create with format ,with format template at the end of message.

### Requirement 4: QA Rejection with Structured Feedback

**User Story:** As a QA reviewer, I want to provide structured rejection feedback, so that assignees understand exactly what needs to be fixed.

#### Acceptance Criteria

1. WHEN a message matching format [TICKET][ISSUE_TYPE][PROBLEM][FIX_REQUIRED][ASSIGNEE] is posted in QA & Review topic after a 👎 reaction, THE Message_Parser SHALL extract all five fields
2. THE Bot SHALL link the Reject_Feedback to the corresponding TICKET in the Database
3. THE Bot SHALL notify the Assignee mentioned in the Reject_Feedback
4. WHEN Reject_Feedback is recorded, THE Bot SHALL transition the task state to REJECTED
5. THE Bot SHALL include Reject_Feedback details in the Daily_Sync report for the Assignee

### Requirement 5: Task Archival

**User Story:** As a project manager, I want approved tasks to be automatically archived, so that I have a permanent record of completed work.

#### Acceptance Criteria

1. WHEN a task transitions to APPROVED state, THE Bot SHALL copy the original task message and QA_Submission to the Central Archive topic
2. THE Bot SHALL include the Assignee name, completion timestamp, and QA_Reviewer name in the archive entry
3. THE Bot SHALL transition the task state to ARCHIVED after successful archival
4. THE Bot SHALL maintain a permanent record in the Archive table of the Database
5. WHEN archival fails, THE Bot SHALL retry up to three times before logging an error

### Requirement 6: Daily Sync Report Generation

**User Story:** As a team member, I want to receive an automated daily report of my task progress, so that I can track my productivity and identify pending work.

#### Acceptance Criteria

1. WHEN the Scheduler triggers at 22:30 GMT+6 daily, THE Bot SHALL generate a Daily_Sync report for each active user
2. THE Bot SHALL include sections for STARTED tasks, COMPLETED tasks, NOT TOUCHED tasks, and REJECTED tasks in the report
3. THE Bot SHALL calculate summary metrics including total tasks, completion count, and rejection count
4. THE Bot SHALL post each user's Daily_Sync report to the Daily Sync topic
5. THE Bot SHALL store the generated report in the Database for historical tracking
6. WHEN a user has no task activity, THE Bot SHALL omit that user from the Daily_Sync report
7. THE Bot SHALL include a link to the Daily_Summary_Message from Task Allocation topic at the beginning of each Daily_Sync report
8. THE Bot SHALL include a link to the QA_Daily_Summary_Message from QA & Review topic at the beginning of each Daily_Sync report
9. THE Daily_Sync report SHALL reference the Starting_Ticket_ID from the Daily_Summary_Message for context

### Requirement 7: Weekly Performance Report Generation

**User Story:** As a project manager, I want to receive a weekly performance report, so that I can identify top performers and address low performance issues.

#### Acceptance Criteria

1. WHEN the Scheduler triggers on Sunday at 22:30 GMT+6, THE Bot SHALL generate a Weekly_Report aggregating data from the past seven days
2. THE Bot SHALL calculate completion rate per user as (APPROVED tasks / total assigned tasks)
3. THE Bot SHALL calculate QA approval rate per user as (APPROVED on first submission / total QA submissions)
4. THE Bot SHALL rank users by completion rate to identify top performers
5. THE Bot SHALL flag users with completion rate below 50% as low performance warnings
6. THE Bot SHALL calculate inactivity score per user as (tasks without 👍 reaction / total assigned tasks)
7. THE Bot SHALL post the Weekly_Report to the Daily Sync topic
8. THE Bot SHALL store the Weekly_Report in the Database for historical analysis
9. THE Bot SHALL calculate average pending tasks per day from Daily_Summary_Messages over the past week
10. THE Bot SHALL calculate average rejected tasks per day from QA_Daily_Summary_Messages over the past week
11. THE Bot SHALL include daily summary statistics in the Weekly_Report showing trends in pending and rejected task counts

### Requirement 8: Inactivity Detection

**User Story:** As a project manager, I want to automatically detect inactive tasks, so that I can follow up on stalled work.

#### Acceptance Criteria

1. WHEN a task in ASSIGNED state has no 👍 reaction within the Inactivity_Threshold period, THE Bot SHALL mark the task as INACTIVE
2. THE Bot SHALL include INACTIVE tasks in the Daily_Sync report with a warning indicator
3. THE Bot SHALL notify the Assignee when their task is marked INACTIVE
4. WHEN a 👍 reaction is added to an INACTIVE task, THE Bot SHALL transition the task to STARTED and remove the INACTIVE flag
5. THE Bot SHALL include inactivity metrics in the Weekly_Report

### Requirement 9: Attendance Check-In and Check-Out

**User Story:** As a team member, I want to check in and check out through the bot, so that my work hours are automatically tracked.

#### Acceptance Criteria

1. WHEN a user adds their first 👍 reaction of the day to a task in Task Allocation topic, THE Bot SHALL record an Attendance_Record with that time as check-in timestamp
2. WHEN a user posts a check-out command in Attendance & Leave Control topic, THE Bot SHALL update the Attendance_Record with check-out timestamp
3. THE Bot SHALL prevent multiple check-ins without an intervening check-out
4. THE Bot SHALL calculate total work hours as (check-out timestamp - check-in timestamp)
5. THE Bot SHALL include attendance summary in the Weekly_Report
6. WHEN a user checks in or out, THE Bot SHALL confirm the action with a reply message
7. WHEN a user has not checked out by 23:59 GMT+6, THE Bot SHALL automatically record a check-out at that time

### Requirement 10: Leave Request Management

**User Story:** As a team member, I want to submit leave requests through the bot, so that my absences are formally recorded and approved.

#### Acceptance Criteria

1. WHEN a user posts a leave request with start date and end date in Attendance & Leave Control topic, THE Bot SHALL create a Leave_Request record
2. THE Bot SHALL assign the Leave_Request a PENDING status
3. WHEN an authorized manager reacts with ❤️ to a Leave_Request, THE Bot SHALL transition the status to APPROVED
4. WHEN an authorized manager reacts with 👎 to a Leave_Request, THE Bot SHALL transition the status to REJECTED
5. THE Bot SHALL notify the requester when their Leave_Request status changes
6. THE Bot SHALL include approved leave dates in the Weekly_Report

### Requirement 11: Message Parsing and Data Extraction

**User Story:** As a system administrator, I want the bot to accurately parse structured messages, so that data is correctly extracted and stored.

#### Acceptance Criteria

1. WHEN a message contains bracketed fields like [TICKET][BRAND][ASSET], THE Message_Parser SHALL extract each field as a separate string
2. THE Message_Parser SHALL handle whitespace variations within and between bracketed fields
3. WHEN a message does not match expected format, THE Message_Parser SHALL log a parsing error without creating invalid records
4. THE Message_Parser SHALL validate that TICKET identifiers match the pattern of alphanumeric characters with optional hyphens
5. THE Message_Parser SHALL extract user mentions (@username) from messages for Assignee identification

### Requirement 12: Database Schema and Persistence

**User Story:** As a system administrator, I want all system data to be persistently stored in a structured database, so that data is not lost and can be queried for reports.

#### Acceptance Criteria

1. THE Database SHALL include tables for Users, Tasks, Task_Reactions, QA_Submissions, Leave_Requests, Attendance, Archive, and Reports
2. THE Bot SHALL store task state transitions with timestamps in the Tasks table
3. THE Bot SHALL maintain referential integrity between Tasks and QA_Submissions using TICKET as the foreign key
4. THE Bot SHALL support concurrent read and write operations for up to 500 users
5. THE Bot SHALL perform database backups daily at 23:00 GMT+6
6. WHEN the Database is unavailable, THE Bot SHALL queue write operations and retry up to five times

### Requirement 13: Topic-Based Message Routing

**User Story:** As a system administrator, I want the bot to process messages differently based on the topic they are posted in, so that the correct automation logic is applied.

#### Acceptance Criteria

1. WHEN a message is received, THE Bot SHALL identify the Topic based on the Telegram thread ID
2. THE Bot SHALL apply task creation logic only to messages in Task Allocation topic
3. THE Bot SHALL apply QA validation logic only to messages in QA & Review topic
4. THE Bot SHALL apply attendance logic only to messages in Attendance & Leave Control topic
5. THE Bot SHALL route management escalations and security alerts to Admin Control Panel topic
6. THE Bot SHALL ignore messages in Official Directives, Brand Repository, Strategic, and Lounge topics for automation purposes
7. THE Bot SHALL log messages from Core Operations topic for discussion tracking without state changes

### Requirement 14: Scalability and Performance

**User Story:** As a system administrator, I want the bot to handle high message volume efficiently, so that the system remains responsive under load.

#### Acceptance Criteria

1. THE Bot SHALL process incoming messages within 500 milliseconds under normal load
2. THE Bot SHALL handle 1000+ daily operations without performance degradation
3. THE Bot SHALL support 50-500 concurrent users without message loss
4. WHEN message processing fails, THE Bot SHALL retry up to three times with exponential backoff
5. THE Bot SHALL use connection pooling for Database access to minimize latency
6. THE Bot SHALL log performance metrics including message processing time and Database query duration

### Requirement 15: Error Handling and Logging

**User Story:** As a system administrator, I want comprehensive error logging, so that I can diagnose and fix issues quickly.

#### Acceptance Criteria

1. WHEN an error occurs during message processing, THE Bot SHALL log the error with timestamp, user ID, message content, and stack trace
2. THE Bot SHALL continue processing subsequent messages after logging an error
3. THE Bot SHALL send critical error notifications to a designated admin user
4. THE Bot SHALL log all state transitions with before state, after state, trigger event, and timestamp
5. THE Bot SHALL maintain log files with daily rotation and 30-day retention

### Requirement 16: Configuration and Deployment

**User Story:** As a system administrator, I want to configure the bot through environment variables and a .env file, so that I can deploy to different environments without code changes and have full flexibility over all system parameters.

#### Acceptance Criteria

1. THE Bot SHALL read all configuration parameters from a .env file at startup
2. THE Bot SHALL validate all required environment variables at startup and exit with an error message if any are missing
3. THE Bot SHALL support configuration of bot credentials including TELEGRAM_BOT_TOKEN and TELEGRAM_GROUP_ID
4. THE Bot SHALL support configuration of database parameters including DATABASE_TYPE, DATABASE_PATH, and DATABASE_BACKUP_TIME
5. THE Bot SHALL support configuration of all topic IDs including TOPIC_OFFICIAL_DIRECTIVES, TOPIC_BRAND_REPOSITORY, TOPIC_TASK_ALLOCATION, TOPIC_CORE_OPERATIONS, TOPIC_QA_REVIEW, TOPIC_CENTRAL_ARCHIVE, TOPIC_DAILY_SYNC, TOPIC_ATTENDANCE_LEAVE, TOPIC_ADMIN_CONTROL_PANEL, and TOPIC_STRATEGIC_LOUNGE
6. THE Bot SHALL support configuration of user roles including ADMINISTRATORS, MANAGERS, QA_REVIEWERS, and OWNERS as comma-separated user IDs
7. THE Bot SHALL support configuration of inactivity thresholds including INACTIVITY_WARNING_HOURS, INACTIVITY_MARK_HOURS, INACTIVITY_ESCALATE_HOURS, and INACTIVITY_CRITICAL_HOURS
8. THE Bot SHALL support configuration of attendance parameters including ATTENDANCE_LATE_CHECKIN_TIME, ATTENDANCE_AUTO_CHECKOUT_TIME, and ATTENDANCE_EXPECTED_CHECKOUT_TIME
9. THE Bot SHALL support configuration of report scheduling including DAILY_REPORT_TIME, WEEKLY_REPORT_DAY, and WEEKLY_REPORT_TIME
10. THE Bot SHALL support configuration of violation handling including VIOLATION_AUTO_DELETE_MALFORMED, VIOLATION_REPEATED_THRESHOLD, and VIOLATION_REPEATED_ACTION
11. THE Bot SHALL support configuration of brand codes as BRAND_CODES comma-separated list
12. THE Bot SHALL support configuration of ticket format validation using TICKET_FORMAT_REGEX
13. THE Bot SHALL support configuration of notification preferences including NOTIFICATION_SEND_DM, NOTIFICATION_SEND_TOPIC_ALERTS, and NOTIFICATION_INCLUDE_MESSAGE_LINKS
14. THE Bot SHALL support configuration of performance monitoring thresholds including PERFORMANCE_QA_REJECTION_THRESHOLD, PERFORMANCE_DORMANCY_DAYS, and PERFORMANCE_LATE_CHECKIN_THRESHOLD
15. THE Bot SHALL support configuration of security parameters including DATABASE_ENCRYPTION_KEY, LOG_RETENTION_DAYS, and AUDIT_TRAIL_RETENTION_DAYS
16. THE Bot SHALL support configuration of feature flags including FEATURE_AUTO_CHECKOUT, FEATURE_AUTO_REMEDIATION, FEATURE_PREDICTIVE_ALERTS, and FEATURE_ANALYTICS_DASHBOARD
17. THE Bot SHALL support configuration of timezone as TIMEZONE with default GMT+6
18. THE Bot SHALL provide a comprehensive .env template file with all parameters documented with inline comments
19. WHEN a configuration parameter is missing and has a default value, THE Bot SHALL use the default value and log a warning
20. WHEN a configuration parameter is invalid, THE Bot SHALL exit with a descriptive error message indicating which parameter is invalid and why

### Requirement 17: Notification System

**User Story:** As a team member, I want to receive notifications through the appropriate channel based on the event type, so that I stay informed without being overwhelmed by bot messages in work topics.

#### Acceptance Criteria

1. WHEN a task is assigned to a user, THE Notification_Router SHALL send a Direct_Message to the Assignee
2. WHEN a task is rejected in QA, THE Notification_Router SHALL send a Direct_Message to the Assignee with the Reject_Feedback
3. WHEN a Leave_Request status changes, THE Notification_Router SHALL send a Direct_Message to the requester
4. WHEN a task is marked INACTIVE, THE Notification_Router SHALL send a Direct_Message to the Assignee
5. WHEN an Inactivity_Warning is triggered, THE Notification_Router SHALL send a Direct_Message to the Assignee
6. WHEN a Daily_Sync report is generated, THE Bot SHALL post it to the Daily Sync topic
7. WHEN a Weekly_Report is generated, THE Bot SHALL post it to the Daily Sync topic
8. WHEN a security violation is detected, THE Notification_Router SHALL post an alert to Admin Control Panel topic
9. WHEN a performance issue is flagged, THE Notification_Router SHALL post an alert to Admin Control Panel topic
10. WHEN a critical escalation occurs, THE Notification_Router SHALL post an alert to Admin Control Panel topic
11. THE Notification_Router SHALL keep Task Allocation, QA & Review, and Core Operations topics free of bot notification spam
12. THE Bot SHALL include a link to the original message in all Direct_Message notifications
13. WHEN a user has notification preferences disabled via NOTIFICATION_SEND_DM configuration, THE Bot SHALL respect that setting
14. WHEN NOTIFICATION_INCLUDE_MESSAGE_LINKS is enabled, THE Bot SHALL include clickable message links in all notifications

### Requirement 18: Parser and Pretty Printer for Configuration

**User Story:** As a system administrator, I want to manage bot configuration through structured files, so that I can version control and audit configuration changes.

#### Acceptance Criteria

1. WHEN a configuration file is provided, THE Parser SHALL parse it into a Configuration object containing all bot settings
2. WHEN an invalid configuration file is provided, THE Parser SHALL return a descriptive error indicating the line number and issue
3. THE Pretty_Printer SHALL format Configuration objects back into valid configuration files with consistent indentation and ordering
4. FOR ALL valid Configuration objects, parsing then printing then parsing SHALL produce an equivalent object (round-trip property)
5. THE Bot SHALL reload configuration when the configuration file is modified without requiring a restart

### Requirement 19: Analytics and Insights

**User Story:** As a project manager, I want to access historical analytics, so that I can identify trends and optimize team performance over time.

#### Acceptance Criteria

1. THE Bot SHALL calculate average task completion time per user over the past 30 days
2. THE Bot SHALL identify the most common ISSUE_TYPE values in Reject_Feedback for process improvement
3. THE Bot SHALL track QA approval rate trends over time per user
4. THE Bot SHALL generate a monthly summary report with completion trends, top performers, and improvement areas
5. THE Bot SHALL provide a command to query task statistics for a specific BRAND or time period

### Requirement 20: Security and Access Control

**User Story:** As a system administrator, I want to enforce role-based access control across all topics and operations, so that only authorized users can perform sensitive operations and access restricted content.

#### Acceptance Criteria

1. THE Bot SHALL maintain a list of authorized QA_Reviewer user IDs who can approve or reject QA submissions
2. THE Bot SHALL maintain a list of authorized Manager user IDs who can approve or reject Leave_Requests
3. THE Bot SHALL maintain a list of Administrator user IDs with full system access
4. THE Bot SHALL maintain a list of Owner user IDs with ownership-level privileges equivalent to Administrators
5. WHEN an unauthorized user attempts to approve or reject a QA_Submission, THE Bot SHALL ignore the reaction and log a security warning
6. WHEN an unauthorized user attempts to approve or reject a Leave_Request, THE Bot SHALL ignore the reaction and log a security warning
7. THE Bot SHALL validate that only the original Assignee can submit QA for their assigned tasks
8. THE Bot SHALL encrypt sensitive data in the Database including user contact information and leave reasons
9. THE Bot SHALL enforce read-only access for Regular_User in Central Archive topic
10. THE Bot SHALL enforce read-only access for Regular_User in Daily Sync topic
11. THE Bot SHALL restrict Admin Control Panel topic access to Managers, Administrators, and Owners only
12. THE Bot SHALL allow Administrators, Managers, and Owners to edit messages in Central Archive topic
13. THE Bot SHALL allow Administrators, Managers, and Owners to edit messages in Daily Sync topic
14. THE Bot SHALL allow Administrators and Owners to delete messages in any topic
15. THE Bot SHALL allow QA_Reviewers to react with ❤️ and 👎 in QA & Review topic
16. THE Bot SHALL allow Managers, Administrators, and Owners to approve or reject in Attendance & Leave Control topic
17. WHEN a Regular_User attempts to post in Admin Control Panel topic, THE Bot SHALL delete the message and send a Direct_Message explaining the restriction
18. THE Bot SHALL log all permission violations to the Audit_Trail with user ID, attempted action, and timestamp
19. THE Bot SHALL enforce Topic_Permission rules according to the role-based permission matrix
20. THE Bot SHALL validate user roles at startup by checking that all configured role user IDs are valid Telegram user IDs


### Requirement 21: Violation Detection and Enforcement

**User Story:** As a system administrator, I want the bot to automatically detect and handle rule violations, so that system integrity is maintained and users are guided to follow correct procedures.

#### Acceptance Criteria

1. WHEN a message in QA & Review topic does not match the required format [TICKET][BRAND][ASSET], THE Violation_Detection_Engine SHALL classify it as a format violation
2. WHEN a format violation is detected and VIOLATION_AUTO_DELETE_MALFORMED is enabled, THE Bot SHALL delete the malformed message
3. WHEN a format violation is detected, THE Bot SHALL send a Direct_Message to the user with the correct format template
4. WHEN a user attempts to submit QA for a task not assigned to them, THE Violation_Detection_Engine SHALL classify it as a workflow violation
5. WHEN a workflow violation is detected, THE Bot SHALL reject the submission and send a Direct_Message explaining the violation
6. WHEN a user attempts an action without proper permissions, THE Violation_Detection_Engine SHALL classify it as a permission violation
7. WHEN a permission violation is detected, THE Bot SHALL log the Violation_Event to the Audit_Trail
8. WHEN a user accumulates violations exceeding VIOLATION_REPEATED_THRESHOLD within a week, THE Bot SHALL escalate to Admin Control Panel topic
9. WHEN VIOLATION_REPEATED_ACTION is set to escalate_to_manager, THE Bot SHALL notify Managers in Admin Control Panel topic
10. WHEN VIOLATION_REPEATED_ACTION is set to temporary_restriction, THE Bot SHALL temporarily restrict the user's ability to post in work topics
11. WHEN a user checks in after ATTENDANCE_LATE_CHECKIN_TIME, THE Violation_Detection_Engine SHALL classify it as an attendance violation
12. WHEN an attendance violation is detected, THE Bot SHALL log it and include it in the Weekly_Report
13. WHEN a task remains in ASSIGNED state beyond INACTIVITY_CRITICAL_HOURS, THE Violation_Detection_Engine SHALL classify it as a performance violation
14. THE Bot SHALL store all Violation_Events in the Database with violation type, user ID, timestamp, and context
15. THE Bot SHALL include violation statistics in the Weekly_Report per user

### Requirement 22: Progressive Inactivity Management

**User Story:** As a project manager, I want a multi-tier escalation system for inactive tasks, so that issues are addressed before they become critical.

#### Acceptance Criteria

1. WHEN a task in ASSIGNED state reaches INACTIVITY_WARNING_HOURS without a 👍 reaction, THE Bot SHALL send an Inactivity_Warning Direct_Message to the Assignee
2. WHEN a task in ASSIGNED state reaches INACTIVITY_MARK_HOURS without a 👍 reaction, THE Bot SHALL mark the task as INACTIVE and include it in the Daily_Sync report
3. WHEN a task in ASSIGNED state reaches INACTIVITY_ESCALATE_HOURS without a 👍 reaction, THE Bot SHALL post an Escalation to Admin Control Panel topic mentioning the Assignee and task details
4. WHEN a task in ASSIGNED state reaches INACTIVITY_CRITICAL_HOURS without a 👍 reaction, THE Bot SHALL post a critical Escalation to Admin Control Panel topic and flag it in the Weekly_Report
5. THE Bot SHALL calculate inactivity duration as (current time - task creation timestamp)
6. WHEN a 👍 reaction is added to a task at any inactivity tier, THE Bot SHALL clear all inactivity flags and cancel pending escalations
7. THE Bot SHALL check for inactivity thresholds every hour using the Scheduler
8. THE Inactivity_Warning Direct_Message SHALL include the task TICKET, assignment date, and hours remaining until escalation
9. THE Escalation message in Admin Control Panel SHALL include the Assignee mention, task TICKET, and inactivity duration
10. THE Bot SHALL track inactivity escalation history in the Database for performance analysis

### Requirement 23: Admin Control Panel Topic

**User Story:** As a manager, I want a dedicated topic for administrative alerts and controls, so that I can monitor critical issues and take action without cluttering work topics.

#### Acceptance Criteria

1. THE Bot SHALL route all management escalations to Admin Control Panel topic
2. THE Bot SHALL route all security violation alerts to Admin Control Panel topic
3. THE Bot SHALL route all critical performance flags to Admin Control Panel topic
4. THE Bot SHALL route all repeated violation notifications to Admin Control Panel topic
5. THE Bot SHALL restrict posting in Admin Control Panel topic to Managers, Administrators, and Owners only
6. WHEN a Regular_User attempts to post in Admin Control Panel topic, THE Bot SHALL delete the message and send a Direct_Message explaining the restriction
7. THE Bot SHALL support administrative bot commands posted in Admin Control Panel topic including user statistics queries, violation history queries, and manual task reassignment
8. WHEN an Escalation is posted to Admin Control Panel, THE Bot SHALL include a clickable link to the original task message
9. THE Bot SHALL include context in all Admin Control Panel messages including user name, user ID, and relevant timestamps
10. THE Bot SHALL log all Admin Control Panel activity to the Audit_Trail for compliance tracking

### Requirement 24: Comprehensive Audit Trail

**User Story:** As a system administrator, I want a complete audit trail of all system events, so that I can debug issues, ensure compliance, and analyze system behavior.

#### Acceptance Criteria

1. THE Bot SHALL log every task state transition to the Audit_Trail with before state, after state, trigger event, user ID, and timestamp
2. THE Bot SHALL log every reaction event to the Audit_Trail with reaction type, message ID, user ID, and timestamp
3. THE Bot SHALL log every QA_Submission to the Audit_Trail with TICKET, submitter ID, and timestamp
4. THE Bot SHALL log every Violation_Event to the Audit_Trail with violation type, user ID, context, and timestamp
5. THE Bot SHALL log every permission check to the Audit_Trail with user ID, attempted action, result, and timestamp
6. THE Bot SHALL log every notification sent to the Audit_Trail with recipient ID, notification type, delivery channel, and timestamp
7. THE Bot SHALL log every configuration change to the Audit_Trail with parameter name, old value, new value, and timestamp
8. THE Bot SHALL log every database operation failure to the Audit_Trail with operation type, error message, and timestamp
9. THE Audit_Trail SHALL be queryable by user ID, event type, date range, and TICKET identifier
10. THE Bot SHALL retain Audit_Trail records for AUDIT_TRAIL_RETENTION_DAYS as configured in .env
11. THE Bot SHALL support exporting Audit_Trail data in JSON format for external analysis
12. THE Bot SHALL include full message context in Audit_Trail entries including message text, topic ID, and message ID
13. WHEN an Audit_Trail query is executed, THE Bot SHALL return results within 2 seconds for queries spanning up to 30 days
14. THE Bot SHALL automatically archive Audit_Trail records older than AUDIT_TRAIL_RETENTION_DAYS to compressed storage

### Requirement 25: Smart Notification Routing

**User Story:** As a team member, I want notifications delivered through the most appropriate channel, so that I receive important information without being overwhelmed by irrelevant messages.

#### Acceptance Criteria

1. WHEN a task is assigned, THE Notification_Router SHALL send a Direct_Message to the Assignee
2. WHEN a task is rejected, THE Notification_Router SHALL send a Direct_Message to the Assignee with Reject_Feedback
3. WHEN an Inactivity_Warning is triggered, THE Notification_Router SHALL send a Direct_Message to the Assignee
4. WHEN a Leave_Request status changes, THE Notification_Router SHALL send a Direct_Message to the requester
5. WHEN a format violation is detected, THE Notification_Router SHALL send a Direct_Message to the violating user
6. WHEN a Daily_Sync report is generated, THE Notification_Router SHALL post it to Daily Sync topic
7. WHEN a Weekly_Report is generated, THE Notification_Router SHALL post it to Daily Sync topic
8. WHEN an inactivity escalation reaches INACTIVITY_ESCALATE_HOURS, THE Notification_Router SHALL post to Admin Control Panel topic
9. WHEN a security violation is detected, THE Notification_Router SHALL post to Admin Control Panel topic
10. WHEN a performance flag is triggered, THE Notification_Router SHALL post to Admin Control Panel topic
11. WHEN repeated violations exceed VIOLATION_REPEATED_THRESHOLD, THE Notification_Router SHALL post to Admin Control Panel topic
12. THE Notification_Router SHALL NOT post bot notifications to Task Allocation topic
13. THE Notification_Router SHALL NOT post bot notifications to QA & Review topic
14. THE Notification_Router SHALL NOT post bot notifications to Core Operations topic
15. WHEN NOTIFICATION_SEND_DM is disabled, THE Notification_Router SHALL skip Direct_Message delivery and log the notification instead
16. WHEN NOTIFICATION_SEND_TOPIC_ALERTS is disabled, THE Notification_Router SHALL skip topic-based alerts and log them instead
17. THE Notification_Router SHALL batch multiple notifications to the same user within a 5-minute window into a single Direct_Message
18. THE Notification_Router SHALL prioritize critical notifications over informational notifications when batching

### Requirement 26: Performance Monitoring and Alerts

**User Story:** As a project manager, I want automated performance monitoring and alerts, so that I can identify and address productivity issues proactively.

#### Acceptance Criteria

1. THE Bot SHALL calculate QA rejection rate per user as (rejected QA submissions / total QA submissions)
2. WHEN a user's QA rejection rate exceeds PERFORMANCE_QA_REJECTION_THRESHOLD, THE Bot SHALL post a performance alert to Admin Control Panel topic
3. THE Bot SHALL track task dormancy as the number of days since a user's last task completion
4. WHEN a user's task dormancy exceeds PERFORMANCE_DORMANCY_DAYS, THE Bot SHALL post a dormancy alert to Admin Control Panel topic
5. THE Bot SHALL track late check-ins as the number of times a user checks in after ATTENDANCE_LATE_CHECKIN_TIME
6. WHEN a user's late check-in count exceeds PERFORMANCE_LATE_CHECKIN_THRESHOLD within a week, THE Bot SHALL post an attendance alert to Admin Control Panel topic
7. THE Bot SHALL calculate average task completion time per user as the mean duration from ASSIGNED to APPROVED state
8. WHEN a user's average task completion time exceeds 2x the team average, THE Bot SHALL flag it in the Weekly_Report
9. THE Bot SHALL identify bottlenecks by tracking tasks stuck in QA_SUBMITTED state for more than 48 hours
10. WHEN a bottleneck is detected, THE Bot SHALL post an alert to Admin Control Panel topic mentioning the QA_Reviewer
11. THE Bot SHALL track team-wide Performance_Metrics including total tasks completed, average completion time, and QA approval rate
12. THE Bot SHALL include Performance_Metrics in the Weekly_Report with trend indicators (improving, stable, declining)
13. THE Bot SHALL store historical Performance_Metrics in the Database for trend analysis
14. THE Bot SHALL support querying Performance_Metrics by user, date range, and BRAND

### Requirement 27: Auto-Remediation System

**User Story:** As a system administrator, I want the bot to automatically resolve common issues, so that manual intervention is minimized and system efficiency is maximized.

#### Acceptance Criteria

1. WHEN FEATURE_AUTO_CHECKOUT is enabled and a user has not checked out by ATTENDANCE_AUTO_CHECKOUT_TIME, THE Bot SHALL automatically record a check-out at that time
2. WHEN a format violation is detected and VIOLATION_AUTO_DELETE_MALFORMED is enabled, THE Bot SHALL automatically delete the malformed message
3. WHEN a task is approved, THE Bot SHALL automatically archive it to Central Archive topic without manual intervention
4. WHEN a duplicate task creation is attempted for an existing TICKET, THE Bot SHALL automatically reject the duplicate and notify the creator
5. WHEN a QA_Submission is detected for a non-existent TICKET, THE Bot SHALL automatically delete the submission and send a Direct_Message to the submitter
6. WHEN a user submits QA for a task not assigned to them, THE Bot SHALL automatically reject the submission and send a Direct_Message explaining the workflow
7. WHEN FEATURE_AUTO_REMEDIATION is enabled and a task has conflicting state transitions, THE Bot SHALL automatically resolve the conflict using the earliest timestamp
8. WHEN a Leave_Request is approved, THE Bot SHALL automatically mark the user as on leave for the specified date range
9. WHEN a user is marked as on leave, THE Bot SHALL automatically exclude them from inactivity checks and performance metrics for that period
10. WHEN a Database backup fails, THE Bot SHALL automatically retry up to three times with exponential backoff
11. WHEN a message parsing error occurs, THE Bot SHALL automatically log the error and continue processing subsequent messages
12. THE Bot SHALL log all Auto_Remediation actions to the Audit_Trail with action type, context, and timestamp
13. WHEN FEATURE_AUTO_REMEDIATION is disabled, THE Bot SHALL log remediation opportunities without taking action
14. THE Bot SHALL include Auto_Remediation statistics in the Weekly_Report showing total actions taken by type

### Requirement 28: Environment Configuration Template

**User Story:** As a system administrator, I want a comprehensive .env template file, so that I can easily configure all system parameters without reading source code.

#### Acceptance Criteria

1. THE Bot SHALL provide a .env.template file in the project root directory
2. THE .env.template file SHALL include all configuration parameters with descriptive inline comments
3. THE .env.template file SHALL include example values for all parameters
4. THE .env.template file SHALL group related parameters into logical sections with section headers
5. THE .env.template file SHALL include the following sections: Bot Configuration, Database Configuration, Timezone, Topic IDs, User Roles, Inactivity Thresholds, Attendance Configuration, Report Scheduling, Violation Handling, Brand Codes, Ticket Format Validation, Notification Preferences, Performance Monitoring, Security, and Feature Flags
6. THE .env.template file SHALL document the expected format for each parameter (e.g., comma-separated list, regex pattern, time in HH:MM format)
7. THE .env.template file SHALL indicate which parameters are required and which have default values
8. THE .env.template file SHALL include security warnings for sensitive parameters like TELEGRAM_BOT_TOKEN and DATABASE_ENCRYPTION_KEY
9. THE Bot SHALL validate that the actual .env file contains all required parameters at startup
10. WHEN a required parameter is missing from .env, THE Bot SHALL exit with an error message referencing the .env.template file

### Requirement 29: Topic Permission Matrix Enforcement

**User Story:** As a system administrator, I want granular permission control per topic and role, so that users can only perform actions appropriate to their role.

#### Acceptance Criteria

1. THE Bot SHALL enforce read-only access for Regular_User in Official Directives topic
2. THE Bot SHALL enforce read-only access for Regular_User in Brand Repository topic
3. THE Bot SHALL enforce read-only access for Regular_User in Central Archive topic
4. THE Bot SHALL enforce read-only access for Regular_User in Daily Sync topic
5. THE Bot SHALL enforce no access for Regular_User in Admin Control Panel topic
6. THE Bot SHALL allow Regular_User to read and write in Task Allocation topic
7. THE Bot SHALL allow Regular_User to read and write in Core Operations topic
8. THE Bot SHALL allow Regular_User to read and write in QA & Review topic
9. THE Bot SHALL allow Regular_User to read and write in Attendance & Leave Control topic
10. THE Bot SHALL allow Regular_User to read and write in Strategic and Lounge topics
11. THE Bot SHALL allow QA_Reviewer to read, write, and react in QA & Review topic
12. THE Bot SHALL allow Manager to read and edit in Official Directives, Brand Repository, Central Archive, and Daily Sync topics
13. THE Bot SHALL allow Manager to read and write in Admin Control Panel topic
14. THE Bot SHALL allow Manager to approve or reject in Attendance & Leave Control topic
15. THE Bot SHALL allow Administrator and Owner to perform all actions in all topics including delete
16. WHEN a user attempts an action not permitted by their role, THE Bot SHALL block the action and log a permission violation
17. THE Bot SHALL validate user permissions before processing any message, reaction, or command
18. THE Bot SHALL cache user role lookups for 5 minutes to minimize database queries
19. THE Bot SHALL reload user role configuration when the .env file is modified
20. THE Bot SHALL include a permission matrix reference in the system documentation

### Requirement 30: Daily Summary Messages with Smart Grouped Task Carryover

**User Story:** As a project manager, I want automated daily summary messages posted at midnight in Task Allocation topic as separate grouped messages with clickable links, so that I can easily filter/search for specific days and quickly navigate to pending tasks organized by assignee.

#### Acceptance Criteria

1. WHEN the Scheduler triggers at DAILY_SUMMARY_TIME (default 00:00 GMT+6), THE Bot SHALL post multiple separate messages to Task Allocation topic
2. THE Bot SHALL post a Day Marker message with format "📅 Day Start: [Month DD, YYYY] ([Day of Week])"
3. THE Day Marker message SHALL include a "Starting Ticket ID" section showing the next sequential ticket ID to be used
4. THE Bot SHALL calculate the Starting_Ticket_ID by querying the Database for the highest ticket number from the previous day and incrementing by 1
5. THE Bot SHALL query the Database for all tasks in ASSIGNED state without a 👍 reaction from previous days
6. WHEN a task has a 🔥 reaction from an Administrator, Manager, or Owner, THE Bot SHALL exclude that task from the Pending Tasks message
7. THE Bot SHALL validate that the 🔥 reaction was added by a user with Administrator, Manager, or Owner role before applying the Fire_Emoji_Exemption
8. WHEN pending tasks exist, THE Bot SHALL post a Pending Tasks message grouped by assignee
9. THE Pending Tasks message SHALL format each task as a clickable Message_Link with format `• [TICKET](https://t.me/c/GROUP_ID/MESSAGE_ID) - [time ago]`
10. THE Bot SHALL calculate time ago using Time_Ago_Format with rules: less than 1 hour as "Xm ago", less than 24 hours as "Xh ago", less than 7 days as "Xd ago", 7 days or more as "Xw ago"
11. THE Pending Tasks message SHALL group tasks by assignee with assignee name as section header
12. THE Pending Tasks message SHALL include a summary count at the bottom showing total pending tasks and total unique assignees
13. WHEN there are no pending tasks from previous days, THE Bot SHALL skip posting the Pending Tasks message
14. THE Bot SHALL post messages with a delay of 1 to 2 seconds between each message to avoid rate limiting
15. THE Bot SHALL store all Daily_Summary_Message IDs in the Database for historical reference
16. THE Day Marker message SHALL include the unique marker "📅 Day Start" to enable easy searching
17. WHEN a 🔥 reaction is added to a task by an unauthorized user, THE Bot SHALL ignore the reaction and not apply the Fire_Emoji_Exemption
18. THE Bot SHALL log all Fire_Emoji_Exemption applications to the Audit_Trail with task TICKET, user ID, and timestamp
19. THE Bot SHALL support configuration of the Daily_Summary_Message time via DAILY_SUMMARY_TIME in .env with default 00:00
20. WHERE FEATURE_DAILY_SUMMARY is enabled, THE Bot SHALL generate Daily_Summary_Messages according to the configured schedule
21. WHERE FEATURE_DAILY_SUMMARY is disabled, THE Bot SHALL skip Daily_Summary_Message generation
22. THE Bot SHALL include DAILY_SUMMARY_TIME and FEATURE_DAILY_SUMMARY in the .env template with inline documentation
23. THE Daily_Summary_Messages SHALL be referenced in Daily_Sync reports for context and cross-referencing
24. THE Bot SHALL store the Daily_Summary_Message IDs with a date index to enable efficient lookup by Daily_Sync report generation
25. THE Bot SHALL construct Message_Link URLs using the Telegram group ID and the original task message ID from the Database

### Requirement 31: Daily Summary Messages for QA & Review Topic with Smart Grouping

**User Story:** As a QA reviewer and team member, I want automated daily summary messages posted at midnight in QA & Review topic as separate grouped messages with clickable links, so that I can quickly navigate to pending submissions, rejected tasks, and bottlenecks organized by reviewer or assignee.

#### Acceptance Criteria

1. WHEN the Scheduler triggers at DAILY_SUMMARY_TIME, THE Bot SHALL post multiple separate messages to QA & Review topic
2. THE Bot SHALL post a QA Day Marker message with format "📅 QA Day Start: [Month DD, YYYY] ([Day of Week])"
3. THE Bot SHALL query the Database for all tasks in QA_SUBMITTED state
4. WHEN pending QA submissions exist, THE Bot SHALL post a Pending QA Submissions message grouped by QA_Reviewer
5. THE Pending QA Submissions message SHALL format each task as a clickable Message_Link with format `• [TICKET](https://t.me/c/GROUP_ID/MESSAGE_ID) by @assignee - [time ago]`
6. THE Bot SHALL calculate time ago using Time_Ago_Format with rules: less than 1 hour as "Xm ago", less than 24 hours as "Xh ago", less than 7 days as "Xd ago", 7 days or more as "Xw ago"
7. THE Pending QA Submissions message SHALL include a summary count at the bottom showing total pending QA submissions
8. WHEN there are no pending QA submissions, THE Bot SHALL skip posting the Pending QA Submissions message
9. THE Bot SHALL query the Database for all tasks in REJECTED state from previous days
10. WHEN rejected tasks exist, THE Bot SHALL post a Rejected Tasks message grouped by assignee
11. THE Rejected Tasks message SHALL format each task as a clickable Message_Link with format `• [TICKET](https://t.me/c/GROUP_ID/MESSAGE_ID) - [ISSUE_TYPE] - [time ago]`
12. THE Rejected Tasks message SHALL include a feedback snippet truncated to 50 characters followed by "..." for each task
13. THE Rejected Tasks message SHALL include a summary count at the bottom showing total rejected tasks
14. WHEN there are no rejected tasks, THE Bot SHALL skip posting the Rejected Tasks message
15. THE Bot SHALL query the Database for all tasks in QA_SUBMITTED state for more than 48 hours
16. WHEN QA bottlenecks exist, THE Bot SHALL post a QA Bottlenecks message listed chronologically without grouping
17. THE QA Bottlenecks message SHALL format each task as a clickable Message_Link with format `• [TICKET](https://t.me/c/GROUP_ID/MESSAGE_ID) by @assignee - Assigned to @reviewer - [X days in review]`
18. THE Bot SHALL calculate days in review as the number of days since the task entered QA_SUBMITTED state
19. THE QA Bottlenecks message SHALL include a summary count at the bottom showing total bottleneck tasks
20. WHEN there are no QA bottlenecks, THE Bot SHALL skip posting the QA Bottlenecks message
21. WHEN a task has a 🔥 reaction from an Administrator, Manager, or Owner, THE Bot SHALL exclude that task from all QA summary messages
22. THE Bot SHALL validate that the 🔥 reaction was added by an authorized user before applying the exemption
23. THE Bot SHALL post messages with a delay of 1 to 2 seconds between each message to avoid rate limiting
24. THE Bot SHALL store all QA_Daily_Summary_Message IDs in the Database for historical reference
25. THE QA Day Marker message SHALL include the unique marker "📅 QA Day Start" for easy searching
26. THE Bot SHALL log QA_Daily_Summary_Message generation to the Audit_Trail
27. WHERE FEATURE_DAILY_SUMMARY is enabled, THE Bot SHALL generate QA_Daily_Summary_Messages
28. WHERE FEATURE_DAILY_SUMMARY is disabled, THE Bot SHALL skip QA_Daily_Summary_Message generation
29. THE QA_Daily_Summary_Messages SHALL be referenced in Daily_Sync reports for context and cross-referencing
30. THE Bot SHALL store the QA_Daily_Summary_Message IDs with a date index to enable efficient lookup by Daily_Sync report generation
31. THE Bot SHALL construct Message_Link URLs using the Telegram group ID and the original message ID from the Database
