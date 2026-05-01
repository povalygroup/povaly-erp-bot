-- ============================================================================
-- COMPREHENSIVE DATABASE SCHEMA FOR TICKET LIFECYCLE TRACKING
-- ============================================================================
-- This schema tracks every aspect of a ticket from creation through completion
-- Supporting multiple assignees, handlers, reviewers, and complete audit trail
-- ============================================================================

-- ============================================================================
-- CORE TABLES (Enhanced)
-- ============================================================================

-- TASKS: Main task record with complete lifecycle tracking
CREATE TABLE IF NOT EXISTS tasks (
    -- Primary Key
    ticket TEXT PRIMARY KEY,
    
    -- Basic Information
    brand TEXT NOT NULL,
    task_title TEXT,
    
    -- People
    creator_id INTEGER NOT NULL,
    
    -- Timestamps - Complete Lifecycle
    created_at TEXT NOT NULL,
    started_at TEXT,
    submitted_to_qa_at TEXT,
    completed_at TEXT,
    trashed_at TEXT,
    
    -- Telegram References
    message_id INTEGER NOT NULL,
    topic_id INTEGER NOT NULL,
    
    -- Task State
    state TEXT NOT NULL DEFAULT 'CREATED',
    -- States: CREATED, ACKNOWLEDGED, IN_PROGRESS, SUBMITTED_TO_QA, COMPLETED, TRASHED, ARCHIVED
    
    -- Fire Exemption
    has_fire_exemption INTEGER DEFAULT 0,
    fire_exemption_by INTEGER,
    fire_exemption_at TEXT,
    
    -- Metadata
    deadline TEXT,
    resources TEXT,
    
    -- Tracking
    last_updated_at TEXT NOT NULL,
    last_updated_by INTEGER
);

-- ISSUES: Issues linked to tasks with complete lifecycle
CREATE TABLE IF NOT EXISTS issues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket TEXT NOT NULL,
    
    -- Issue Details
    issue_title TEXT NOT NULL,
    issue_details TEXT,
    priority TEXT NOT NULL,  -- LOW, MEDIUM, HIGH, CRITICAL
    
    -- People
    creator_id INTEGER NOT NULL,
    
    -- Telegram References
    message_id INTEGER NOT NULL,
    topic_id INTEGER NOT NULL,
    
    -- Issue State
    state TEXT NOT NULL DEFAULT 'CREATED',
    -- States: CREATED, CLAIMED, IN_PROGRESS, RESOLVED, INVALID, ESCALATED
    
    -- Timestamps
    created_at TEXT NOT NULL,
    claimed_at TEXT,
    resolved_at TEXT,
    escalated_at TEXT,
    
    -- Tracking
    last_updated_at TEXT NOT NULL,
    last_updated_by INTEGER,
    
    FOREIGN KEY(ticket) REFERENCES tasks(ticket)
);

-- QA_SUBMISSIONS: QA submissions with complete lifecycle
CREATE TABLE IF NOT EXISTS qa_submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket TEXT NOT NULL,
    
    -- Submission Details
    asset TEXT NOT NULL,
    submission_notes TEXT,
    
    -- People
    submitter_id INTEGER NOT NULL,
    
    -- Telegram References
    message_id INTEGER NOT NULL,
    topic_id INTEGER NOT NULL,
    
    -- QA State
    state TEXT NOT NULL DEFAULT 'SUBMITTED',
    -- States: SUBMITTED, QA_PROCESSING, APPROVED, REJECTED, RESUBMITTED
    
    -- Timestamps
    submitted_at TEXT NOT NULL,
    qa_started_at TEXT,
    reviewed_at TEXT,
    
    -- Tracking
    submission_number INTEGER,  -- 1st, 2nd, 3rd submission for same ticket
    last_updated_at TEXT NOT NULL,
    
    FOREIGN KEY(ticket) REFERENCES tasks(ticket)
);

-- ============================================================================
-- TRACKING TABLES (New) - Support Multiple Participants
-- ============================================================================

-- TASK_ASSIGNEES: Multiple assignees per task with individual status
CREATE TABLE IF NOT EXISTS task_assignees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket TEXT NOT NULL,
    assignee_id INTEGER NOT NULL,
    
    -- Individual Status
    status TEXT NOT NULL DEFAULT 'ASSIGNED',
    -- Statuses: ASSIGNED, ACKNOWLEDGED, IN_PROGRESS, SUBMITTED, COMPLETED
    
    -- Timestamps
    assigned_at TEXT NOT NULL,
    acknowledged_at TEXT,
    started_at TEXT,
    submitted_at TEXT,
    completed_at TEXT,
    
    -- Tracking
    is_primary INTEGER DEFAULT 0,  -- First assignee
    
    UNIQUE(ticket, assignee_id),
    FOREIGN KEY(ticket) REFERENCES tasks(ticket)
);

-- ISSUE_HANDLERS: Multiple handlers per issue with individual status
CREATE TABLE IF NOT EXISTS issue_handlers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    issue_id INTEGER NOT NULL,
    handler_id INTEGER NOT NULL,
    
    -- Handler Status
    status TEXT NOT NULL DEFAULT 'CLAIMED',
    -- Statuses: CLAIMED, IN_PROGRESS, RESOLVED
    
    -- Timestamps
    claimed_at TEXT NOT NULL,
    started_at TEXT,
    resolved_at TEXT,
    
    -- Tracking
    is_primary INTEGER DEFAULT 0,  -- First handler
    
    UNIQUE(issue_id, handler_id),
    FOREIGN KEY(issue_id) REFERENCES issues(id)
);

-- QA_REVIEWERS: Multiple reviewers per QA submission with individual status
CREATE TABLE IF NOT EXISTS qa_reviewers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    qa_submission_id INTEGER NOT NULL,
    reviewer_id INTEGER NOT NULL,
    
    -- Review Status
    status TEXT NOT NULL DEFAULT 'ASSIGNED',
    -- Statuses: ASSIGNED, REVIEWING, APPROVED, REJECTED
    
    -- Timestamps
    assigned_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    
    -- Rejection Details (if rejected)
    rejection_reason TEXT,
    rejection_feedback TEXT,
    
    -- Tracking
    is_primary INTEGER DEFAULT 0,
    
    UNIQUE(qa_submission_id, reviewer_id),
    FOREIGN KEY(qa_submission_id) REFERENCES qa_submissions(id)
);

-- ============================================================================
-- REACTION TABLES (New) - Track All Reactions
-- ============================================================================

-- TASK_REACTIONS: All reactions on task messages
CREATE TABLE IF NOT EXISTS task_reactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket TEXT NOT NULL,
    message_id INTEGER NOT NULL,
    
    -- Reaction Details
    reaction TEXT NOT NULL,  -- 👍, ❤️, 👎, 🔥
    user_id INTEGER NOT NULL,
    
    -- Context
    context TEXT,  -- 'TASK_ACKNOWLEDGED', 'TASK_COMPLETED', etc.
    
    -- Timestamps
    reacted_at TEXT NOT NULL,
    removed_at TEXT,  -- If reaction was removed
    
    FOREIGN KEY(ticket) REFERENCES tasks(ticket)
);

-- ISSUE_REACTIONS: All reactions on issue messages
CREATE TABLE IF NOT EXISTS issue_reactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    issue_id INTEGER NOT NULL,
    message_id INTEGER NOT NULL,
    
    -- Reaction Details
    reaction TEXT NOT NULL,  -- 👍, ❤️, 👎
    user_id INTEGER NOT NULL,
    
    -- Context
    context TEXT,  -- 'ISSUE_CLAIMED', 'ISSUE_RESOLVED', 'ISSUE_INVALID'
    
    -- Timestamps
    reacted_at TEXT NOT NULL,
    removed_at TEXT,
    
    FOREIGN KEY(issue_id) REFERENCES issues(id)
);

-- QA_REACTIONS: All reactions on QA submission messages
CREATE TABLE IF NOT EXISTS qa_reactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    qa_submission_id INTEGER NOT NULL,
    message_id INTEGER NOT NULL,
    
    -- Reaction Details
    reaction TEXT NOT NULL,  -- 👍, ❤️, 👎
    user_id INTEGER NOT NULL,
    
    -- Context
    context TEXT,  -- 'QA_PROCESSING', 'QA_APPROVED', 'QA_REJECTED'
    
    -- Timestamps
    reacted_at TEXT NOT NULL,
    removed_at TEXT,
    
    FOREIGN KEY(qa_submission_id) REFERENCES qa_submissions(id)
);

-- ============================================================================
-- AUDIT & METADATA TABLES (New)
-- ============================================================================

-- TICKET_AUDIT_TRAIL: Complete audit log of every change
CREATE TABLE IF NOT EXISTS ticket_audit_trail (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket TEXT NOT NULL,
    
    -- Change Details
    action TEXT NOT NULL,
    -- Actions: CREATED, STATE_CHANGED, ASSIGNEE_ADDED, ASSIGNEE_REMOVED, 
    --          ACKNOWLEDGED, SUBMITTED_TO_QA, ISSUE_CREATED, ISSUE_RESOLVED,
    --          QA_SUBMITTED, QA_APPROVED, QA_REJECTED, TRASHED, ARCHIVED
    
    old_value TEXT,
    new_value TEXT,
    
    -- Who Made Change
    changed_by INTEGER NOT NULL,
    
    -- Timestamps
    changed_at TEXT NOT NULL,
    
    -- Context
    context TEXT,  -- Additional context (e.g., issue_id, qa_submission_id)
    
    FOREIGN KEY(ticket) REFERENCES tasks(ticket)
);

-- TICKET_METADATA: Stores additional metadata and custom fields
CREATE TABLE IF NOT EXISTS ticket_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket TEXT NOT NULL,
    
    -- Metadata
    key TEXT NOT NULL,
    value TEXT,
    
    -- Timestamps
    set_at TEXT NOT NULL,
    set_by INTEGER,
    
    UNIQUE(ticket, key),
    FOREIGN KEY(ticket) REFERENCES tasks(ticket)
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Task Indexes
CREATE INDEX IF NOT EXISTS idx_tasks_state ON tasks(state);
CREATE INDEX IF NOT EXISTS idx_tasks_creator ON tasks(creator_id);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);
CREATE INDEX IF NOT EXISTS idx_tasks_state_created ON tasks(state, created_at);

-- Issue Indexes
CREATE INDEX IF NOT EXISTS idx_issues_ticket ON issues(ticket);
CREATE INDEX IF NOT EXISTS idx_issues_state ON issues(state);
CREATE INDEX IF NOT EXISTS idx_issues_creator ON issues(creator_id);
CREATE INDEX IF NOT EXISTS idx_issues_priority ON issues(priority);
CREATE INDEX IF NOT EXISTS idx_issues_ticket_state ON issues(ticket, state);

-- QA Submission Indexes
CREATE INDEX IF NOT EXISTS idx_qa_submissions_ticket ON qa_submissions(ticket);
CREATE INDEX IF NOT EXISTS idx_qa_submissions_state ON qa_submissions(state);
CREATE INDEX IF NOT EXISTS idx_qa_submissions_submitter ON qa_submissions(submitter_id);
CREATE INDEX IF NOT EXISTS idx_qa_submissions_ticket_state ON qa_submissions(ticket, state);

-- Task Assignees Indexes
CREATE INDEX IF NOT EXISTS idx_task_assignees_ticket ON task_assignees(ticket);
CREATE INDEX IF NOT EXISTS idx_task_assignees_assignee ON task_assignees(assignee_id);
CREATE INDEX IF NOT EXISTS idx_task_assignees_status ON task_assignees(status);
CREATE INDEX IF NOT EXISTS idx_task_assignees_ticket_status ON task_assignees(ticket, status);

-- Issue Handlers Indexes
CREATE INDEX IF NOT EXISTS idx_issue_handlers_issue ON issue_handlers(issue_id);
CREATE INDEX IF NOT EXISTS idx_issue_handlers_handler ON issue_handlers(handler_id);
CREATE INDEX IF NOT EXISTS idx_issue_handlers_status ON issue_handlers(status);

-- QA Reviewers Indexes
CREATE INDEX IF NOT EXISTS idx_qa_reviewers_submission ON qa_reviewers(qa_submission_id);
CREATE INDEX IF NOT EXISTS idx_qa_reviewers_reviewer ON qa_reviewers(reviewer_id);
CREATE INDEX IF NOT EXISTS idx_qa_reviewers_status ON qa_reviewers(status);

-- Reaction Indexes
CREATE INDEX IF NOT EXISTS idx_task_reactions_ticket ON task_reactions(ticket);
CREATE INDEX IF NOT EXISTS idx_task_reactions_user ON task_reactions(user_id);
CREATE INDEX IF NOT EXISTS idx_issue_reactions_issue ON issue_reactions(issue_id);
CREATE INDEX IF NOT EXISTS idx_issue_reactions_user ON issue_reactions(user_id);
CREATE INDEX IF NOT EXISTS idx_qa_reactions_submission ON qa_reactions(qa_submission_id);
CREATE INDEX IF NOT EXISTS idx_qa_reactions_user ON qa_reactions(user_id);

-- Audit Trail Indexes
CREATE INDEX IF NOT EXISTS idx_audit_trail_ticket ON ticket_audit_trail(ticket);
CREATE INDEX IF NOT EXISTS idx_audit_trail_action ON ticket_audit_trail(action);
CREATE INDEX IF NOT EXISTS idx_audit_trail_changed_at ON ticket_audit_trail(changed_at);
CREATE INDEX IF NOT EXISTS idx_audit_trail_changed_by ON ticket_audit_trail(changed_by);
CREATE INDEX IF NOT EXISTS idx_audit_trail_ticket_action ON ticket_audit_trail(ticket, action);

-- Metadata Indexes
CREATE INDEX IF NOT EXISTS idx_metadata_ticket ON ticket_metadata(ticket);
CREATE INDEX IF NOT EXISTS idx_metadata_key ON ticket_metadata(key);
CREATE INDEX IF NOT EXISTS idx_metadata_ticket_key ON ticket_metadata(ticket, key);

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- View: Complete Ticket Status
CREATE VIEW IF NOT EXISTS v_ticket_status AS
SELECT 
    t.ticket,
    t.brand,
    t.task_title,
    t.state as task_state,
    COUNT(DISTINCT ta.assignee_id) as assignee_count,
    COUNT(DISTINCT i.id) as issue_count,
    COUNT(DISTINCT qs.id) as qa_submission_count,
    t.created_at,
    t.completed_at,
    CASE 
        WHEN t.state = 'COMPLETED' THEN 
            CAST((julianday(t.completed_at) - julianday(t.created_at)) * 24 AS INTEGER)
        ELSE 
            CAST((julianday('now') - julianday(t.created_at)) * 24 AS INTEGER)
    END as hours_elapsed
FROM tasks t
LEFT JOIN task_assignees ta ON t.ticket = ta.ticket
LEFT JOIN issues i ON t.ticket = i.ticket
LEFT JOIN qa_submissions qs ON t.ticket = qs.ticket
GROUP BY t.ticket;

-- View: Task Assignee Status
CREATE VIEW IF NOT EXISTS v_task_assignee_status AS
SELECT 
    ta.ticket,
    ta.assignee_id,
    ta.status,
    ta.assigned_at,
    ta.acknowledged_at,
    ta.started_at,
    ta.submitted_at,
    ta.completed_at,
    CASE 
        WHEN ta.status = 'COMPLETED' THEN 
            CAST((julianday(ta.completed_at) - julianday(ta.assigned_at)) * 24 AS INTEGER)
        ELSE 
            CAST((julianday('now') - julianday(ta.assigned_at)) * 24 AS INTEGER)
    END as hours_assigned
FROM task_assignees ta;

-- View: Issue Status
CREATE VIEW IF NOT EXISTS v_issue_status AS
SELECT 
    i.id,
    i.ticket,
    i.issue_title,
    i.priority,
    i.state,
    COUNT(DISTINCT ih.handler_id) as handler_count,
    i.created_at,
    i.resolved_at,
    CASE 
        WHEN i.state = 'RESOLVED' THEN 
            CAST((julianday(i.resolved_at) - julianday(i.created_at)) * 24 AS INTEGER)
        ELSE 
            CAST((julianday('now') - julianday(i.created_at)) * 24 AS INTEGER)
    END as hours_open
FROM issues i
LEFT JOIN issue_handlers ih ON i.id = ih.issue_id
GROUP BY i.id;

-- View: QA Submission Status
CREATE VIEW IF NOT EXISTS v_qa_submission_status AS
SELECT 
    qs.id,
    qs.ticket,
    qs.submission_number,
    qs.state,
    COUNT(DISTINCT qr.reviewer_id) as reviewer_count,
    qs.submitted_at,
    qs.reviewed_at,
    CASE 
        WHEN qs.state IN ('APPROVED', 'REJECTED') THEN 
            CAST((julianday(qs.reviewed_at) - julianday(qs.submitted_at)) * 24 AS INTEGER)
        ELSE 
            CAST((julianday('now') - julianday(qs.submitted_at)) * 24 AS INTEGER)
    END as hours_in_qa
FROM qa_submissions qs
LEFT JOIN qa_reviewers qr ON qs.id = qr.qa_submission_id
GROUP BY qs.id;

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
