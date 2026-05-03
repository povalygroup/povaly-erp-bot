# 📘 Pova System - Employee User Guide

**Version 1.0.0** | Povaly Inc. Administrative Automation System

Welcome to Pova, your intelligent administrative automation system! This guide will help you understand how to work efficiently within our Telegram-based workspace.

---

## 📋 Table of Contents

1. [Getting Started](#getting-started)
2. [Understanding the Workspace](#understanding-the-workspace)
3. [Daily Workflow](#daily-workflow)
4. [Task Management](#task-management)
5. [Quality Assurance](#quality-assurance)
6. [Issue Reporting](#issue-reporting)
7. [Attendance & Leave](#attendance--leave)
8. [Meetings](#meetings)
9. [Commands Reference](#commands-reference)
10. [Best Practices](#best-practices)
11. [Troubleshooting](#troubleshooting)

---

## 🚀 Getting Started

### Step 1: Join the Workspace

You should have received an invitation to join the **Povaly Operations** Telegram group. If not, contact your manager.

### Step 2: Activate Pova Notifications

**IMPORTANT:** To receive direct message (DM) notifications from Pova, you must:

1. **Search for Pova** in Telegram:
   - Open Telegram search
   - Search for `@YourBotUsername` (ask your admin for the exact username)
   - Or click the Pova profile in the group

2. **Send `/start` command**:
   - Open the chat with Pova
   - Type `/start` and send
   - You'll receive a welcome message

3. **Verify activation**:
   - You should see: "✅ Welcome! You're now registered with Pova."
   - You'll now receive DM notifications for task updates, approvals, and alerts

**Why is this important?**
- Pova sends you personal notifications about your tasks, QA reviews, and approvals
- Without activating, you won't receive these important updates
- All notifications auto-delete after a few seconds to keep your DMs clean

### Step 3: Understand Your Role

Your access level determines what you can do in the system:

- **👤 Employee** - Create tasks, submit work, report issues, track attendance
- **🎯 QA Reviewer** - All employee permissions + approve/reject quality reviews
- **👔 Manager** - All QA permissions + approve leave, view team workload
- **👑 Admin** - Full system access + manage users and configurations

---

## 🏢 Understanding the Workspace

Our Telegram group is organized into **12 specialized topics**. Each topic serves a specific purpose:

### 📢 1. Official Directives
**Purpose:** Company announcements and official communications  
**Who can post:** Admins and Managers only  
**What you do:** Read important announcements  
**Restrictions:** No casual conversations, no questions here

### 🎨 2. Brand Repository
**Purpose:** Brand assets, logos, guidelines, and resources  
**Who can post:** Admins and Managers only  
**What you do:** Download brand assets when needed  
**Restrictions:** Read-only for employees

### 📋 3. Task Allocation
**Purpose:** Your main workspace for task management  
**Who can post:** Everyone  
**What you do:**
- Receive task assignments
- Start working (react with 👍)
- Confirm completion (react with ❤️)
- View task status

**How it works:**
- Tasks appear as formatted messages
- Use reactions (👍 ❤️) to update status
- Never delete or edit task messages
- Use `/mytasks` to see your task list

### 🐛 4. Core Operations
**Purpose:** Report and resolve issues  
**Who can post:** Everyone  
**What you do:**
- Report bugs, blockers, or problems
- Claim issues you can fix (react with 👍)
- Mark issues as resolved (react with ❤️)

**When to use:**
- Technical problems
- Blockers preventing task completion
- System errors
- Process issues

### ✅ 5. QA & Review
**Purpose:** Submit completed work for quality review  
**Who can post:** Everyone  
**What you do:**
- Submit your completed work
- Wait for QA reviewer approval
- Fix issues if rejected

**Workflow:**
1. Complete your task
2. Post QA submission with deliverable link
3. QA reviewer claims (👍) and reviews
4. Approved (❤️) or Rejected (👎)
5. If approved, confirm completion on task

### 📦 6. Central Archive
**Purpose:** Completed tasks archive  
**Who can post:** System only (automatic)  
**What you do:** View completed work history  
**Restrictions:** Read-only, no posting

### 📊 7. Daily Sync
**Purpose:** Daily reports and team statistics  
**Who can post:** System only (automatic)  
**What you do:** Review daily summaries and performance  
**Restrictions:** Read-only, no posting

### ⏰ 8. Attendance & Leave
**Purpose:** Track work hours and manage time off  
**Who can post:** Everyone  
**What you do:**
- Check-in/check-out (usually automatic)
- Track breaks
- Request leave
- View attendance records

### 👑 9. Admin Control Panel
**Purpose:** System alerts and admin notifications  
**Who can post:** System only (automatic)  
**What you do:** N/A (Admin only)  
**Restrictions:** Admins and Managers only

### 📅 10. Boardroom
**Purpose:** Meeting coordination and notes  
**Who can post:** Everyone  
**What you do:**
- View meeting invitations
- RSVP with reactions
- Review meeting notes
- Track action items

### 💡 11. Strategic Lounge
**Purpose:** Open discussions and brainstorming  
**Who can post:** Everyone  
**What you do:**
- Discuss ideas
- Share suggestions
- Collaborate on strategy
- Ask questions

### 🗑️ 12. Trash
**Purpose:** Deleted messages archive  
**Who can post:** System only (automatic)  
**What you do:** N/A  
**Restrictions:** Admins only

---

## 📅 Daily Workflow

### Morning Routine (9:00 AM - 10:00 AM)

**1. Check-in (Automatic)**
- When you start your first task of the day, Pova automatically checks you in
- If you arrive after 10:00 AM, you'll be marked as late
- Manual check-in: `/checkin` in Attendance & Leave topic

**2. Review Your Tasks**
- Go to Task Allocation topic
- Type `/mytasks` to see your assigned tasks
- Pova will send you a DM with your task list (auto-deletes in 120 seconds)

**3. Check Notifications**
- Review any DMs from Pova
- Check Official Directives for announcements
- Review Daily Sync for yesterday's summary

### During Work (10:00 AM - 6:00 PM)

**4. Start Working on Tasks**
- Find your task in Task Allocation topic
- React with 👍 to mark as STARTED
- Pova confirms in DM (auto-deletes in 60 seconds)

**5. Take Breaks**
- Type `/breakstart` when starting break
- Type `/breakend` when returning
- Maximum 90 minutes total breaks per day
- Maximum 5 breaks per day

**6. Report Issues**
- If you encounter blockers, go to Core Operations
- Type `/newissue` and fill in the details
- Include task ticket, issue description, and priority

**7. Submit Completed Work**
- When task is done, go to QA & Review topic
- Type `/newqa` and select your task
- Provide deliverable link
- Wait for QA approval

### Evening Routine (6:00 PM - 7:00 PM)

**8. Confirm Completed Tasks**
- After QA approval, go to Task Allocation
- Find your approved task
- React with ❤️ to confirm completion

**9. Check-out**
- Type `/checkout` in Attendance & Leave topic
- Or let Pova auto-checkout at 11:59 PM

**10. Review Tomorrow**
- Check `/mytasks` for pending work
- Review any meeting invitations in Boardroom

---

## 📋 Task Management

### Understanding Task States

Your tasks go through 7 states:

1. **🆕 ASSIGNED** - Task assigned to you, not started yet
2. **🔵 STARTED** - You're working on it (after 👍 reaction)
3. **🔍 QA_SUBMITTED** - Submitted for quality review
4. **❌ REJECTED** - QA rejected, needs fixes
5. **✅ APPROVED** - QA approved, ready for completion
6. **🎉 COMPLETED** - You confirmed completion (after ❤️ reaction)
7. **📦 ARCHIVED** - Automatically archived after 24 hours

### How to Work with Tasks

**Starting a Task:**
```
1. Find your task in Task Allocation topic
2. Read the task details carefully
3. React with 👍 on the task message
4. Status changes: ASSIGNED → STARTED
5. You receive DM confirmation
6. If it's your first task today, you're auto-checked-in
```

**While Working:**
- You can react with 👍 multiple times (it's just a marker/reminder)
- No notifications spam - Pova is smart about reaction changes
- Check task details anytime with `/task #TICKET`
- View all your tasks with `/mytasks`

**Submitting for QA:**
```
1. Complete your work
2. Go to QA & Review topic
3. Type /newqa
4. Select your task from the list
5. Enter format:
   [TICKET] POV260501
   [BRAND] #Povaly
   [ASSET] https://link-to-your-deliverable
6. Submit and wait for review
```

**After QA Approval:**
```
1. You receive DM: "QA Approved" (auto-deletes in 90s)
2. Go to Task Allocation topic
3. Find your task (now shows APPROVED)
4. React with ❤️ to confirm completion
5. Status changes: APPROVED → COMPLETED
6. Task will auto-archive in 24 hours
```

### Task Commands

```bash
/mytasks              # View your tasks (DM, auto-deletes in 120s)
/tasksbystate STARTED # View tasks by specific state
/overduetasks         # View overdue tasks
/task #POV260501      # View specific task details
/taskhelp             # Quick reference guide
```

### Task Reactions Explained

**👍 Thumbs Up:**
- **On ASSIGNED task:** Start working (ASSIGNED → STARTED)
- **On STARTED/QA_SUBMITTED/REJECTED:** Use as marker/reminder (no action)
- **On APPROVED task:** ❌ Not allowed (use ❤️ instead)
- **On COMPLETED task:** ❌ Not allowed (already done)

**❤️ Heart:**
- **On APPROVED task:** Confirm completion (APPROVED → COMPLETED)
- **On other states:** Not applicable

**🔥 Fire:**
- Admin only - marks task as urgent

### Important Rules

✅ **DO:**
- React with 👍 to start tasks
- Submit QA when work is 100% complete
- React with ❤️ after QA approval to confirm completion
- Check `/mytasks` regularly
- Report blockers immediately

❌ **DON'T:**
- Delete or edit task messages
- Submit incomplete work for QA
- React with ❤️ before QA approval
- Ignore deadline reminders
- Work on tasks not assigned to you

---

## ✅ Quality Assurance

### QA Submission Process

**When to Submit:**
- Task is 100% complete
- All deliverables are ready
- You've tested your work
- All requirements are met

**How to Submit:**

1. **Go to QA & Review topic**

2. **Type `/newqa`**

3. **Select your task** from the list Pova shows

4. **Enter submission details:**
```
[TICKET] POV260501
[BRAND] #Povaly
[ASSET] https://drive.google.com/your-deliverable-link
```

5. **Submit** - Your QA submission is created

6. **Wait for review** - You'll get DM when reviewer starts

### QA Review States

- **🟡 PENDING** - Waiting for reviewer to claim
- **🔵 IN_REVIEW** - Reviewer is evaluating
- **✅ APPROVED** - QA passed! Confirm completion on task
- **❌ REJECTED** - QA failed, needs fixes

### What Happens During Review

**Reviewer Claims (👍):**
- You receive DM: "QA Review Started" (auto-deletes in 60s)
- Reviewer is now evaluating your work

**Reviewer Approves (❤️):**
- You receive DM: "QA Approved" (auto-deletes in 90s)
- Task status changes to APPROVED
- Go to Task Allocation and react ❤️ to confirm completion

**Reviewer Rejects (👎):**
- You receive DM: "QA Rejected" with reason (auto-deletes in 90s)
- Task status changes to REJECTED
- Check the QA thread for feedback
- Fix the issues
- Resubmit with `/reopenqa #TICKET`

### QA Commands

```bash
/newqa                # Submit work for QA
/myqa                 # View your QA submissions
/qa #POV260501        # View specific QA details
/reopenqa #POV260501  # Resubmit after rejection
/qahelp               # QA quick reference
```

### QA Best Practices

✅ **DO:**
- Submit only when 100% complete
- Include clear deliverable links
- Test your work before submitting
- Respond quickly to rejection feedback
- Provide context in submission

❌ **DON'T:**
- Submit incomplete work
- Submit without testing
- Ignore rejection feedback
- Resubmit without fixing issues
- React to your own QA submissions

---

## 🐛 Issue Reporting

### When to Report an Issue

Report issues in **Core Operations** topic when you encounter:

- **Technical Problems:** Bugs, errors, system failures
- **Blockers:** Things preventing task completion
- **Process Issues:** Workflow problems, unclear requirements
- **Resource Issues:** Missing access, tools, or information

### How to Report an Issue

**Method 1: Using Command (Recommended)**

1. **Go to Core Operations topic**

2. **Type `/newissue`**

3. **Fill in the template:**
```
[TICKET] POV260501
[ISSUE] Brief description of the problem
[DETAILS] Detailed explanation of what's wrong
[PRIORITY] HIGH
```

**Priority Levels:**
- **LOW** - Minor issue, doesn't block work
- **MEDIUM** - Moderate issue, workaround available
- **HIGH** - Serious issue, blocking work
- **CRITICAL** - System down, urgent attention needed

**Method 2: Manual Format**

Post in Core Operations topic:
```
[TICKET] #POV260501
[ISSUETICKET] #POV260501-I1 (optional - auto-generated)
[ISSUE] Database connection timeout
[DETAILS] Getting timeout errors when trying to save data. 
Error message: "Connection timeout after 30 seconds"
Happens consistently on save action.
[PRIORITY] HIGH
[ASSIGNEE] @tech.lead (optional)
```

### Issue Lifecycle

**1. Issue Created**
- Issue appears in Core Operations
- Auto-generated ticket: #POV260501-I1
- Status: 🔴 OPEN

**2. Someone Claims (👍)**
- Handler reacts with 👍
- Status: 🟡 IN_PROGRESS
- You receive DM: "Issue Claimed"

**3. Issue Resolved (❤️)**
- Handler reacts with ❤️
- Status: ✅ RESOLVED
- You receive DM: "Issue Resolved"

**4. Issue Invalid (👎)**
- Handler reacts with 👎
- Status: ❌ INVALID
- You receive DM: "Issue Rejected"

### Issue Commands

```bash
/newissue             # Create new issue
/myissues             # View issues you created
/myclaimedissues      # View issues you're handling
/openissues           # View all unresolved issues
/issue #POV260501-I1  # View issue details
/issuehelp            # Issue tracking guide
```

### Issue Best Practices

✅ **DO:**
- Provide clear, detailed descriptions
- Include error messages and screenshots
- Set appropriate priority
- Link to related task
- Follow up on resolution

❌ **DON'T:**
- Report non-issues (use Strategic Lounge for questions)
- Exaggerate priority
- Create duplicate issues
- Delete issue messages
- Ignore resolution updates

---

## ⏰ Attendance & Leave

### Attendance Tracking

**Auto Check-in:**
- When you start your first task of the day
- Pova automatically checks you in
- On-time: Before 10:00 AM
- Late: After 10:00 AM

**Manual Check-in:**
```
1. Go to Attendance & Leave topic
2. Type /checkin
3. Pova confirms check-in with timestamp
```

**Check-out:**
```
1. Go to Attendance & Leave topic
2. Type /checkout
3. Pova calculates total work hours
4. Or auto-checkout at 11:59 PM
```

### Break Management

**Starting a Break:**
```
1. Type /breakstart in Attendance & Leave
2. Break timer starts
3. Work hour counting pauses
```

**Ending a Break:**
```
1. Type /breakend in Attendance & Leave
2. Break timer stops
3. Work hour counting resumes
```

**Break Limits:**
- Maximum 90 minutes total per day
- Maximum 5 breaks per day
- Exceeding limits triggers alerts

### Leave Requests

**How to Request Leave:**

1. **Go to Attendance & Leave topic**

2. **Type the command:**
```
/requestleave 2026-05-15 2026-05-20 Family vacation @replacement_user
```

**Format:**
```
/requestleave START_DATE END_DATE REASON @REPLACEMENT
```

**Example:**
```
/requestleave 2026-06-01 2026-06-05 Medical leave @john.doe
```

3. **Wait for approval:**
- Manager reviews your request
- Manager reacts ❤️ to approve or 👎 to reject
- You receive DM with decision

4. **If approved:**
- Your tasks are automatically reassigned to replacement
- You're marked as ON_LEAVE
- Replacement receives DM notification

### Attendance Commands

```bash
/checkin              # Manual check-in
/checkout             # Manual check-out
/breakstart           # Start break
/breakend             # End break
/mybreaks             # View today's breaks
/myattendance         # View your attendance this month
/myattendance 2026-05 # View specific month
/attendancedetails 2026-05-03 # Detailed day view
/attendancehelp       # Attendance guide
```

### Leave Commands

```bash
/requestleave START END REASON @REPLACEMENT
/myleave              # View your leave requests
```

### Attendance Best Practices

✅ **DO:**
- Check-in on time (before 10:00 AM)
- Track breaks accurately
- Request leave in advance
- Specify replacement for leave
- Check-out at end of day

❌ **DON'T:**
- Forget to check-in
- Exceed break limits
- Request leave without replacement
- Work during approved leave
- Manipulate attendance records

---

## 📅 Meetings

### Meeting Invitations

**How Meetings Work:**
- Meetings are posted in Boardroom topic
- You receive invitation with details
- RSVP with reactions
- Receive reminders (24h, 1h, 15m before)

**Meeting Invitation Format:**
```
📅 MEETING INVITATION

[MEETING_ID] MTG260501
[MEETING_INVITE] Q2 Planning Session
[DATE] 2026-05-15
[TIME] 10:00 - 11:30 GMT+6
[DURATION] 1.5 hours
[LOCATION] Zoom: https://zoom.us/j/123456789
[ORGANIZER] @manager
[ATTENDEES] @all
[AGENDA]
• Q2 goals review
• Resource allocation
• Timeline planning
[PRIORITY] HIGH
```

### RSVP with Reactions

**👍 I will attend**
- Confirms your attendance
- You'll receive reminders

**❤️ I will attend and I'm prepared**
- Confirms attendance
- Shows you've reviewed agenda

**👎 I cannot attend**
- Declines invitation
- Organizer is notified

**🔥 I have an urgent conflict**
- Urgent decline
- Requires immediate attention

### Meeting Notes

After meetings, notes are posted in Boardroom:

```
📝 MEETING NOTES

[MEETING] Q2 Planning Session
[DATE] 2026-05-15
[TIME] 10:00 - 11:30
[ATTENDEES] @ceo, @manager1, @lead.dev
[AGENDA] Q2 goals, resources, timeline
[DECISIONS]
• Focus on mobile development
• Hire 2 developers
• Launch by June 30
[ACTION_ITEMS]
• @manager1: Hiring plan by May 20
• @lead.dev: Tech roadmap by May 18
• @ceo: Budget approval by May 15
[NEXT_MEETING] 2026-06-01
```

### Action Items

**Track Your Action Items:**
```
1. Type /myactions in Boardroom
2. View your assigned action items
3. Update status with reactions:
   👍 = Acknowledged
   🔄 = In Progress
   ❤️ = Completed
   👎 = Blocked
```

### Meeting Commands

```bash
/meetings             # View all upcoming meetings
/mymeetings           # View meetings you're invited to
/meeting MTG260501    # View meeting details
/myactions            # View your action items
/meetinghelp          # Meeting guide
```

### Meeting Best Practices

✅ **DO:**
- RSVP promptly
- Attend on time
- Review agenda beforehand
- Complete action items
- Update action item status

❌ **DON'T:**
- Ignore meeting invitations
- Skip without notice
- Arrive late
- Ignore action items
- Miss deadlines

---

## 📚 Commands Reference

### Quick Command List

**Task Management:**
```bash
/mytasks              # View your tasks
/tasksbystate STATE   # Filter tasks by state
/overduetasks         # View overdue tasks
/task #TICKET         # View task details
/taskhelp             # Task guide
```

**QA & Review:**
```bash
/newqa                # Submit for QA
/myqa                 # View your QA submissions
/qa #TICKET           # View QA details
/reopenqa #TICKET     # Resubmit after rejection
/qahelp               # QA guide
```

**Issue Tracking:**
```bash
/newissue             # Report new issue
/myissues             # View your issues
/myclaimedissues      # View issues you're handling
/openissues           # View all open issues
/issue #TICKET        # View issue details
/issuehelp            # Issue guide
```

**Attendance:**
```bash
/checkin              # Check-in
/checkout             # Check-out
/breakstart           # Start break
/breakend             # End break
/myattendance         # View attendance
/attendancehelp       # Attendance guide
```

**Leave:**
```bash
/requestleave START END REASON @REPLACEMENT
/myleave              # View leave requests
```

**Meetings:**
```bash
/meetings             # View all meetings
/mymeetings           # View your meetings
/myactions            # View action items
/meetinghelp          # Meeting guide
```

**General:**
```bash
/start                # Activate Pova notifications
/help                 # General help
/commands             # All available commands
/guide                # Topic guides
```

### Command Tips

- Commands work in their respective topics
- Most commands send DM responses (auto-delete)
- Use `/help` if you forget a command
- Commands are case-insensitive
- Some commands require parameters

---

## 💡 Best Practices

### Communication

✅ **DO:**
- Use appropriate topics for different purposes
- Keep messages professional and clear
- Use reactions to update status
- Respond to DM notifications promptly
- Ask questions in Strategic Lounge

❌ **DON'T:**
- Post in wrong topics
- Have casual conversations in work topics
- Ignore system notifications
- Delete or edit system messages
- Spam reactions

### Task Management

✅ **DO:**
- Start tasks promptly (react 👍)
- Submit QA when 100% complete
- Confirm completion after QA approval (react ❤️)
- Report blockers immediately
- Meet deadlines

❌ **DON'T:**
- Leave tasks in ASSIGNED state
- Submit incomplete work
- Ignore QA rejection feedback
- Miss deadlines without notice
- Work on unassigned tasks

### Time Management

✅ **DO:**
- Check-in on time (before 10:00 AM)
- Track breaks accurately
- Request leave in advance
- Specify replacement for leave
- Check-out at end of day

❌ **DON'T:**
- Arrive late consistently
- Exceed break limits
- Take leave without approval
- Forget to check-out
- Work during approved leave

### Quality

✅ **DO:**
- Test your work before QA submission
- Provide clear deliverables
- Fix issues promptly after rejection
- Follow brand guidelines
- Maintain high standards

❌ **DON'T:**
- Submit untested work
- Ignore QA feedback
- Rush through tasks
- Skip quality checks
- Compromise standards

---

## 🔧 Troubleshooting

### Common Issues

**Issue: Not receiving DM notifications**

**Solution:**
1. Search for Pova in Telegram
2. Open chat with Pova
3. Send `/start` command
4. Verify you see welcome message
5. Test with `/mytasks` command

---

**Issue: Can't see my tasks**

**Solution:**
1. Go to Task Allocation topic
2. Type `/mytasks`
3. Check DM from Pova (auto-deletes in 120s)
4. If empty, you have no assigned tasks
5. Contact manager if you should have tasks

---

**Issue: Reaction not working**

**Solution:**
1. Verify you're reacting to correct message
2. Check if you're in correct topic
3. Ensure task is in correct state
4. Remove and re-add reaction
5. Check DM for error message

---

**Issue: QA submission failed**

**Solution:**
1. Verify task is in STARTED state
2. Check format is correct
3. Ensure deliverable link is valid
4. Try `/newqa` command instead
5. Contact QA reviewer if persists

---

**Issue: Check-in not working**

**Solution:**
1. Go to Attendance & Leave topic
2. Type `/checkin` manually
3. Verify you see confirmation
4. Check if already checked in today
5. Contact admin if persists

---

**Issue: Command not responding**

**Solution:**
1. Verify command spelling
2. Check if in correct topic
3. Wait a few seconds and retry
4. Check DM for error message
5. Use `/help` to verify command

---

### Getting Help

**For Technical Issues:**
- Report in Core Operations topic
- Use `/newissue` command
- Set appropriate priority
- Include error details

**For Questions:**
- Ask in Strategic Lounge topic
- Check this guide first
- Use `/help` for quick reference
- Contact your manager

**For Urgent Issues:**
- Contact admin directly
- Mark issue as CRITICAL
- Provide detailed information
- Follow up promptly

---

## 📞 Support Contacts

**System Issues:**
- Report in Core Operations topic
- Tag: @admin

**Leave Requests:**
- Post in Attendance & Leave topic
- Manager will review

**General Questions:**
- Ask in Strategic Lounge topic
- Team will help

**Urgent Matters:**
- Contact manager directly
- Or tag @admin in relevant topic

---

## 🎯 Quick Start Checklist

- [ ] Joined Povaly Operations group
- [ ] Searched for Pova in Telegram
- [ ] Sent `/start` to Pova
- [ ] Received welcome message
- [ ] Read this guide
- [ ] Checked `/mytasks` for assignments
- [ ] Understood task workflow
- [ ] Know how to submit QA
- [ ] Know how to report issues
- [ ] Understand attendance tracking
- [ ] Bookmarked this guide

---

## 📝 Summary

**Remember:**
1. **Activate Pova** - Send `/start` to receive notifications
2. **Use Reactions** - 👍 to start, ❤️ to complete
3. **Submit QA** - Only when 100% complete
4. **Report Issues** - Use Core Operations topic
5. **Track Time** - Check-in, breaks, check-out
6. **Stay Organized** - Use correct topics
7. **Communicate** - Respond to notifications
8. **Ask Questions** - Use Strategic Lounge

**Your Daily Routine:**
1. Check-in (automatic on first task)
2. Review `/mytasks`
3. Start tasks (react 👍)
4. Submit QA when complete
5. Confirm completion after approval (react ❤️)
6. Report any issues
7. Check-out at end of day

---

**Welcome to efficient workflow with Pova! 🚀**

*For questions or support, contact your manager or post in Strategic Lounge.*

---

**Document Version:** 1.0.0  
**Last Updated:** May 3, 2026  
**Maintained by:** Povaly Inc. Administration
