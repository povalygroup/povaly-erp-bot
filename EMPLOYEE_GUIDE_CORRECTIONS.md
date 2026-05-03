# Employee Guide Corrections Based on Actual Codebase

## Critical Corrections Needed:

### 1. Bot Information
- **Bot Username:** `@povaly_erp_bot` ✅
- **/start Response:** 
  ```
  👋 Welcome to Povaly Operations Bot!
  
  Use /commands to see all available commands.
  ```

### 2. User Roles (Only 4 Roles)
Based on `src/data/models/user.py` and `src/security/access_control.py`:

- **👤 REGULAR** - Default role for all users
- **🎯 QA_REVIEWER** - Can approve/reject QA submissions
- **👔 MANAGER** - Can approve leave, view team workload
- **👑 ADMIN** - Full system access (includes OWNERS from config)

**Note:** OWNER in config is treated as ADMIN in the system.

### 3. Task Creation Permission
Based on `src/bot/handlers/command_handler.py` line 4214:
- **EVERYONE can create tasks** - No permission check in `/newtask` command
- Any user in the group can use `/newtask` to create tasks
- This is NOT restricted to admins/managers

### 4. Who Can Post Where
Based on access control code:

**Everyone Can Post:**
- Task Allocation (create tasks, react to tasks)
- Core Operations (create issues, react to issues)
- QA & Review (submit QA, react if QA reviewer)
- Attendance & Leave (check-in, request leave)
- Boardroom (meetings, RSVP)
- Strategic Lounge (discussions)

**Restricted (Admin/Manager Only):**
- Official Directives
- Brand Repository (posting)
- Central Archive (system only)
- Daily Sync (system only)
- Admin Control Panel (admin only)
- Trash (system only)

### 5. Bot Running in Multiple Places
**IMPORTANT:** A Telegram bot token can only be used by ONE running instance at a time.

- If you run the bot on your local machine, it works there
- If you then run it on the server, the local instance stops working
- Only the LAST started instance will receive and respond to messages
- This is a Telegram API limitation, not a bug

**What happens:**
1. Bot running on Server A - works fine
2. Start bot on Server B with same token - Server B takes over
3. Server A stops receiving messages (Telegram sends to Server B now)
4. Stop bot on Server B - neither works until you restart one

**Solution:** Only run ONE instance at a time with the same token.

### 6. Actual Permissions Matrix

| Action | Regular | QA Reviewer | Manager | Admin |
|--------|---------|-------------|---------|-------|
| Create Task | ✅ | ✅ | ✅ | ✅ |
| Start Task (👍) | ✅ | ✅ | ✅ | ✅ |
| Submit QA | ✅ | ✅ | ✅ | ✅ |
| Approve QA (❤️) | ❌ | ✅ | ✅ | ✅ |
| Reject QA (👎) | ❌ | ✅ | ✅ | ✅ |
| Report Issue | ✅ | ✅ | ✅ | ✅ |
| Claim Issue (👍) | ✅ | ✅ | ✅ | ✅ |
| Check-in/out | ✅ | ✅ | ✅ | ✅ |
| Request Leave | ✅ | ✅ | ✅ | ✅ |
| Approve Leave | ❌ | ❌ | ✅ | ✅ |
| View Team Workload | ❌ | ❌ | ✅ | ✅ |
| Bulk Assign | ❌ | ❌ | ✅ | ✅ |
| Edit Messages | ❌ | ❌ | ❌ | ✅ |
| System Config | ❌ | ❌ | ❌ | ✅ |

### 7. Configuration Roles
From `src/config.py`:

```python
ADMINISTRATORS = [list of user IDs]  # Treated as ADMIN role
MANAGERS = [list of user IDs]        # MANAGER role
QA_REVIEWERS = [list of user IDs]    # QA_REVIEWER role
OWNERS = [list of user IDs]          # Also treated as ADMIN role
```

**Everyone else** = REGULAR role (default)

### 8. Late Check-in Time
From config: **11:00 AM** (not 10:00 AM as stated in guide)
- On-time: Before 11:00 AM
- Late: After 11:00 AM

### 9. Auto Checkout Time
From config: **23:59** (11:59 PM)

### 10. Break Limits
From config:
- Maximum 90 minutes total per day
- Maximum 5 breaks per day

## Summary of Changes Needed in Employee Guide:

1. ✅ Keep bot username as `@povaly_erp_bot`
2. ✅ Keep /start response as shown above
3. ❌ REMOVE "Employee" role - use "Regular User" or just describe as "default"
4. ❌ REMOVE "Owner" as separate role - it's same as Admin
5. ✅ CHANGE: Everyone can create tasks (not just admins)
6. ✅ ADD: Explanation about bot running in only one place at a time
7. ✅ CHANGE: Late check-in is after 11:00 AM (not 10:00 AM)
8. ✅ UPDATE: Permission matrix to match actual code

## Recommended Role Description:

**Your Role in Pova:**

Pova has 4 user roles:

1. **Regular User** (Default)
   - Create and work on tasks
   - Submit work for QA review
   - Report and resolve issues
   - Track your attendance
   - Request leave
   - Participate in meetings

2. **QA Reviewer**
   - All Regular User permissions
   - Approve or reject QA submissions
   - Review quality of work

3. **Manager**
   - All QA Reviewer permissions
   - Approve or reject leave requests
   - View team workload and statistics
   - Bulk assign tasks
   - Access management reports

4. **Administrator**
   - All Manager permissions
   - Full system access
   - Edit any message
   - Configure system settings
   - Manage users and roles
   - Access all administrative functions

**Note:** Your role is configured by system administrators in the backend. Contact your manager if you believe your role should be different.
