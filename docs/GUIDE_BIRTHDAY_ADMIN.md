# 🎂 Birthday System - Admin Guide

**Version 1.0.0** | Povaly Operations Bot | Administrator Documentation

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Configuration](#configuration)
4. [Admin Commands](#admin-commands)
5. [Managing Employee Information](#managing-employee-information)
6. [Custom Birthday Wishes](#custom-birthday-wishes)
7. [Monitoring & Reports](#monitoring--reports)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)

---

## 🎯 Overview

The Birthday System provides automated birthday celebrations with:

- **Automatic Wishes**: Sent daily at 9:00 AM
- **Reminders**: Sent to users and admins at 6:00 PM (1 day before)
- **Custom Messages**: Admins can send personalized wishes
- **Multi-Channel**: DM + Official Directives announcements
- **Employee Profiles**: Complete employee information management

---

## 🏗️ System Architecture

### Components

```
┌─────────────────────────────────────────────┐
│         Birthday System Architecture         │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │     Employee Info Service            │  │
│  │  - Parse employee information        │  │
│  │  - Validate fields                   │  │
│  │  - Save to database                  │  │
│  └──────────────────────────────────────┘  │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │     Birthday Service                 │  │
│  │  - Check daily birthdays             │  │
│  │  - Send automatic wishes             │  │
│  │  - Send reminders                    │  │
│  │  - Handle custom wishes              │  │
│  └──────────────────────────────────────┘  │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │     Birthday Scheduler               │  │
│  │  - 9:00 AM: Birthday wishes          │  │
│  │  - 6:00 PM: Birthday reminders       │  │
│  └──────────────────────────────────────┘  │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │     Database                         │  │
│  │  - users table (27 new fields)       │  │
│  │  - birthday_wishes table             │  │
│  │  - birthday_reminders table          │  │
│  └──────────────────────────────────────┘  │
│                                             │
└─────────────────────────────────────────────┘
```

### Data Flow

```
User sends [EMPLOYEE_INFO]
         ↓
Message Handler detects format
         ↓
Employee Info Service parses & validates
         ↓
Save to database
         ↓
Send confirmation DM
         ↓
Daily at 9:00 AM: Birthday Service checks
         ↓
Send wishes (DM + Official Directives)
         ↓
Log in birthday_wishes table
```

---

## ⚙️ Configuration

### Environment Variables (.env)

```env
# ============================================
# Employee Information Collection
# ============================================

# Ask for employee info on first signup
EMPLOYEE_INFO_ASK_ON_SIGNUP=true

# Required fields (comma-separated)
EMPLOYEE_INFO_REQUIRED_FIELDS=NAME,BIRTHDAY,EMAIL,PHONE,DEPARTMENT,POSITION

# Optional fields (comma-separated)
EMPLOYEE_INFO_OPTIONAL_FIELDS=JOIN_DATE,EMERGENCY_CONTACT,BLOOD_GROUP,ADDRESS,SKILLS,NOTES

# Allow users to update their own info
EMPLOYEE_INFO_USER_CAN_UPDATE=true

# ============================================
# Birthday Feature Configuration
# ============================================

# Enable/disable birthday feature
FEATURE_BIRTHDAY_WISHES=true

# Time to check and send automatic birthday wishes (HH:MM format, GMT+6)
BIRTHDAY_CHECK_TIME=09:00

# Time to send birthday reminders (1 day before, HH:MM format, GMT+6)
BIRTHDAY_REMINDER_TIME=18:00

# Send DM to birthday person
BIRTHDAY_SEND_DM=true

# Send announcement in Official Directives topic
BIRTHDAY_SEND_GROUP=true

# Include age in message (only if birth year provided)
BIRTHDAY_INCLUDE_AGE=false

# ============================================
# Birthday Reminder Configuration
# ============================================

# Send reminder to birthday user (1 day before)
BIRTHDAY_REMINDER_SEND_TO_USER=true

# Send reminder DM to admin DM receivers
BIRTHDAY_REMINDER_SEND_TO_ADMIN_DM=true

# Send reminder to Admin Control Panel topic
BIRTHDAY_REMINDER_SEND_TO_ADMIN_PANEL=true

# Handle multiple birthdays on same day
BIRTHDAY_REMINDER_GROUP_MULTIPLE=true
```

### Configuration Options Explained

| Variable | Default | Description |
|----------|---------|-------------|
| `EMPLOYEE_INFO_ASK_ON_SIGNUP` | `true` | Send welcome DM to new users |
| `EMPLOYEE_INFO_REQUIRED_FIELDS` | See above | Fields that must be filled |
| `EMPLOYEE_INFO_OPTIONAL_FIELDS` | See above | Fields that are optional |
| `EMPLOYEE_INFO_USER_CAN_UPDATE` | `true` | Users can update their own info |
| `FEATURE_BIRTHDAY_WISHES` | `true` | Enable birthday system |
| `BIRTHDAY_CHECK_TIME` | `09:00` | When to send birthday wishes |
| `BIRTHDAY_REMINDER_TIME` | `18:00` | When to send reminders |
| `BIRTHDAY_SEND_DM` | `true` | Send DM to birthday person |
| `BIRTHDAY_SEND_GROUP` | `true` | Post in Official Directives |
| `BIRTHDAY_INCLUDE_AGE` | `false` | Show age in messages |
| `BIRTHDAY_REMINDER_SEND_TO_USER` | `true` | Remind user 1 day before |
| `BIRTHDAY_REMINDER_SEND_TO_ADMIN_DM` | `true` | Send admin DM reminders |
| `BIRTHDAY_REMINDER_SEND_TO_ADMIN_PANEL` | `true` | Post in Admin Control Panel |
| `BIRTHDAY_REMINDER_GROUP_MULTIPLE` | `true` | Group multiple birthdays |

---

## 🛠️ Admin Commands

### View Employee Information

**Command:** `/viewinfo @username`

**Purpose:** View complete employee profile

**Example:**
```
/viewinfo @john
```

**Response:**
```
📋 Employee Information for @john

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 Name: John Michael Doe
🎂 Birthday: May 15, 1990 (Age: 36)
📧 Email: john.doe@povaly.com
📱 Phone: +1234567890
🏢 Department: Development
💼 Position: Senior Developer
📅 Join Date: January 1, 2024
🚨 Emergency: Jane Doe: +0987654321
🩸 Blood Group: A+
📍 Address: 123 Main St, City
🎯 Skills: Python, JavaScript, React
📝 Notes: Prefers morning shifts
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 Set by: self
🕐 Last updated: 2026-05-03 10:30
```

---

### Set Employee Information

**Command:** `/setinfo @username`

**Purpose:** Set or update user's employee information

**Example:**
```
/setinfo @john
```

**Response:**
```
📋 Setting employee info for @john

Reply with employee information in this format:

[EMPLOYEE_INFO]
[NAME] Full Name
[BIRTHDAY] DD-MM-YYYY
[EMAIL] email@example.com
[PHONE] +1234567890
[DEPARTMENT] Department
[POSITION] Job Title
[JOIN_DATE] DD-MM-YYYY
[EMERGENCY_CONTACT] Name: Phone
[BLOOD_GROUP] A+
[ADDRESS] Address (optional)
[SKILLS] Skills (optional)
[NOTES] Notes (optional)

The user will be notified of the update.
```

**Then reply with:**
```
[EMPLOYEE_INFO]
[NAME] John Michael Doe
[BIRTHDAY] 15-05-1990
[EMAIL] john.doe@povaly.com
[PHONE] +1234567890
[DEPARTMENT] Development
[POSITION] Senior Developer
[JOIN_DATE] 01-01-2024
[EMERGENCY_CONTACT] Jane Doe: +0987654321
[BLOOD_GROUP] A+
[ADDRESS] 123 Main St, City, Country
[SKILLS] Python, JavaScript, React
[NOTES] Prefers morning shifts
```

---

### Send Custom Birthday Wish

**Command:** `/birthday @username Your custom message`

**Purpose:** Send personalized birthday wish (overrides automatic wish)

**Example:**
```
/birthday @john Happy Birthday John! You've been an incredible asset to our team this year. Your dedication and creativity inspire us all. Here's to another amazing year! 🎉
```

**What Happens:**
1. Custom DM sent to user
2. Custom announcement in Official Directives
3. Automatic wish is prevented for today
4. Logged as "custom" wish in database

**Custom DM Format:**
```
🎉🎂 SPECIAL BIRTHDAY MESSAGE 🎂🎉

Dear John,

Happy Birthday John! You've been an incredible 
asset to our team this year. Your dedication and 
creativity inspire us all. Here's to another 
amazing year! 🎉

🎈🎁🎊

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sent with love by: Manager Name
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### View Upcoming Birthdays

**Command:** `/birthdays`

**Purpose:** See all birthdays in next 30 days

**Example:**
```
/birthdays
```

**Response:**
```
🎂 Upcoming Birthdays (Next 30 Days)

• John Michael Doe @john
  📅 May 15, 1990 - ⏳ In 12 days
  🏢 Development

• Sarah Johnson @sarah
  📅 May 20th - ⏳ In 17 days
  🏢 Marketing

• Mike Wilson @mike
  📅 June 1st - 🎈 Tomorrow
  🏢 QA
```

---

### View Today's Birthdays

**Command:** `/birthdaytoday`

**Purpose:** Check who has birthdays today

**Example:**
```
/birthdaytoday
```

**Response:**
```
🎂 Birthdays Today! 🎉

🎉 John Michael Doe @john
   🎈 Turning 36 today!
   💼 Senior Developer
   🏢 Development

🎉 Sarah Johnson @sarah
   💼 Marketing Manager
   🏢 Marketing

Don't forget to wish them! 🎁
```

---

## 📊 Managing Employee Information

### Employee Info Fields

| Field | Required | Format | Example |
|-------|----------|--------|---------|
| NAME | Yes | Full name | John Michael Doe |
| BIRTHDAY | Yes | DD-MM-YYYY or DD-MM | 15-05-1990 or 15-05 |
| EMAIL | Yes | email@domain.com | john.doe@povaly.com |
| PHONE | Yes | +country code | +1234567890 |
| DEPARTMENT | Yes | Department name | Development |
| POSITION | Yes | Job title | Senior Developer |
| JOIN_DATE | Optional | DD-MM-YYYY | 01-01-2024 |
| EMERGENCY_CONTACT | Optional | Name: Phone | Jane Doe: +0987654321 |
| BLOOD_GROUP | Optional | A+/A-/B+/B-/AB+/AB-/O+/O- | A+ |
| ADDRESS | Optional | Full address | 123 Main St, City |
| SKILLS | Optional | Comma-separated | Python, JavaScript |
| NOTES | Optional | Any text | Prefers morning shifts |

### Validation Rules

**Email:**
- Must be valid email format
- Pattern: `name@domain.com`

**Phone:**
- Must contain at least 7 digits
- Can include: +, spaces, hyphens, parentheses
- Example: `+1 (234) 567-8900`

**Blood Group:**
- Must be one of: A+, A-, B+, B-, AB+, AB-, O+, O-
- Case insensitive

**Birthday:**
- Format 1: `DD-MM-YYYY` (with year, shows age)
- Format 2: `DD-MM` (without year, no age)
- Day: 1-31
- Month: 1-12
- Year: 1900-current year

**Join Date:**
- Format: `DD-MM-YYYY` only
- Must be valid date

### Bulk Employee Setup

For setting up multiple employees:

1. Prepare employee info in the format
2. Use `/setinfo @username` for each employee
3. Reply with their information
4. Repeat for all employees

**Tip:** Keep a spreadsheet with employee info and copy-paste into the format.

---

## 🎁 Custom Birthday Wishes

### When to Use Custom Wishes

Use custom wishes for:
- ✅ Special milestones (5 years with company, etc.)
- ✅ Exceptional performance recognition
- ✅ Personal touch from leadership
- ✅ Team-specific celebrations

### Custom Wish Best Practices

**DO:**
- ✅ Be genuine and personal
- ✅ Mention specific achievements
- ✅ Keep it professional but warm
- ✅ Send early in the day (before 9 AM to prevent auto-wish)

**DON'T:**
- ❌ Use generic templates
- ❌ Make it too long
- ❌ Include sensitive information
- ❌ Send after auto-wish (causes duplicate)

### Custom Wish Examples

**For Long-Term Employee:**
```
/birthday @john Happy Birthday John! 🎉 Five years with Povaly - what an incredible journey! Your leadership in the Development team has been invaluable. Thank you for your dedication and innovation. Here's to many more years together! 🎂
```

**For New Employee:**
```
/birthday @sarah Happy Birthday Sarah! 🎈 We're so glad you joined our Marketing team this year. Your fresh ideas and enthusiasm have made a real impact. Wishing you a wonderful day and an amazing year ahead! 🎉
```

**For Team Lead:**
```
/birthday @mike Happy Birthday Mike! 🎂 Your guidance and mentorship in QA have elevated our entire quality process. The team is lucky to have you. Enjoy your special day - you've earned it! 🎁
```

---

## 📈 Monitoring & Reports

### Birthday Reminders (Admin)

**When:** 6:00 PM daily (1 day before birthdays)

**Admin DM:**
```
🎂 Birthday Reminder - Tomorrow

The following team members have birthdays tomorrow:

1️⃣ John Michael Doe @john
   💼 Senior Developer | 🏢 Development
   📅 Birthday: May 15th
   🎈 Turning 36

2️⃣ Sarah Johnson @sarah
   💼 Marketing Manager | 🏢 Marketing
   📅 Birthday: May 15th

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 Total: 2 birthdays tomorrow
🎉 Automatic wishes will be sent at 9:00 AM

You can send custom wishes with:
/birthday @john Your custom message
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Admin Control Panel:**
```
🎂 BIRTHDAY REMINDER - TOMORROW

📅 Date: May 15, 2026

Team members with birthdays tomorrow:

1️⃣ @john - John Michael Doe
   💼 Senior Developer | 🏢 Development
   🎈 Age: 36

2️⃣ @sarah - Sarah Johnson
   💼 Marketing Manager | 🏢 Marketing

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 Total: 2 birthdays
⏰ Auto wishes: 9:00 AM tomorrow
📢 Announcement: Official Directives
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Custom wishes: /birthday @username Message
```

### Database Logs

**birthday_wishes table:**
- Tracks all wishes sent (auto and custom)
- Fields: user_id, wish_date, wish_type, custom_message, sent_by_user_id, dm_sent, group_sent

**birthday_reminders table:**
- Tracks all reminders sent
- Fields: user_id, reminder_date, birthday_date, user_dm_sent, admin_dm_sent, group_sent

**Query Examples:**
```sql
-- Get all wishes sent this month
SELECT * FROM birthday_wishes 
WHERE wish_date LIKE '2026-05%';

-- Get users who received custom wishes
SELECT * FROM birthday_wishes 
WHERE wish_type = 'custom';

-- Get reminder statistics
SELECT COUNT(*) FROM birthday_reminders 
WHERE reminder_date = '2026-05-03';
```

---

## 🔧 Troubleshooting

### Issue: Birthday wishes not sent

**Possible Causes:**
1. Bot was offline at 9:00 AM
2. User doesn't have birthday set
3. Birthday format is invalid
4. Feature disabled in config

**Solution:**
1. Check bot logs: `data/logs/telegram_bot.log`
2. Verify user birthday: `/viewinfo @username`
3. Check config: `FEATURE_BIRTHDAY_WISHES=true`
4. Manually send: `/birthday @username Message`

---

### Issue: Reminders not received

**Possible Causes:**
1. Bot was offline at 6:00 PM
2. Admin DM recipients not configured
3. Reminder features disabled

**Solution:**
1. Check config: `BIRTHDAY_REMINDER_SEND_TO_ADMIN_DM=true`
2. Verify `ADMIN_DM_RECIPIENTS` in .env
3. Check Admin Control Panel topic ID
4. Review logs for errors

---

### Issue: User can't update their info

**Possible Causes:**
1. `EMPLOYEE_INFO_USER_CAN_UPDATE=false`
2. Invalid format
3. Validation errors

**Solution:**
1. Check config setting
2. Verify format matches exactly
3. Check validation errors in DM
4. Admin can update with `/setinfo`

---

### Issue: Duplicate birthday wishes

**Possible Causes:**
1. Custom wish sent after auto wish
2. Bot restarted and re-sent wishes

**Solution:**
1. Send custom wishes before 9:00 AM
2. System prevents duplicates on same day
3. Check `birthday_wishes_sent` field in database

---

### Issue: Age not showing

**Possible Causes:**
1. Birthday format doesn't include year
2. `BIRTHDAY_INCLUDE_AGE=false`

**Solution:**
1. Use `DD-MM-YYYY` format (not `DD-MM`)
2. Set `BIRTHDAY_INCLUDE_AGE=true` in config
3. Update user's birthday with year

---

## ✅ Best Practices

### For Admins

**DO:**
- ✅ Review upcoming birthdays weekly
- ✅ Send custom wishes for special occasions
- ✅ Keep employee info up to date
- ✅ Monitor birthday logs
- ✅ Respond to admin reminders
- ✅ Encourage team participation

**DON'T:**
- ❌ Ignore birthday reminders
- ❌ Send generic custom wishes
- ❌ Forget to update employee info
- ❌ Disable features without notice
- ❌ Share employee info publicly

### For System Maintenance

**Weekly:**
- Check upcoming birthdays
- Review employee info completeness
- Monitor birthday logs

**Monthly:**
- Audit employee information
- Review birthday statistics
- Update documentation if needed

**Quarterly:**
- Review configuration settings
- Analyze birthday participation
- Gather feedback from team

### Security & Privacy

**Employee Information:**
- Only admins can view full employee info
- Users can only see their own info
- Birthday announcements are public
- Keep emergency contacts confidential

**Data Protection:**
- Employee info stored in encrypted database
- Regular backups maintained
- Access logs tracked
- GDPR compliant

---

## 📞 Support

**Technical Issues:**
- Check logs: `data/logs/telegram_bot.log`
- Check errors: `data/logs/errors.log`
- Review configuration: `.env`
- Restart bot if needed

**Feature Requests:**
- Document in Core Operations
- Tag development team
- Provide use case details

**Questions:**
- Refer to this guide
- Check user guide
- Contact system administrator

---

## 🎉 Summary

The Birthday System automates team celebrations while allowing personal touches through custom wishes. Proper configuration and monitoring ensure everyone feels valued on their special day.

**Key Points:**
- ✅ Automatic wishes at 9:00 AM
- ✅ Reminders at 6:00 PM (1 day before)
- ✅ Custom wishes override automatic
- ✅ Multi-channel delivery (DM + group)
- ✅ Complete employee profiles
- ✅ Comprehensive logging

---

**Document Version:** 1.0.0  
**Last Updated:** May 3, 2026  
**System:** Povaly Operations Bot  
**Audience:** Administrators & Managers
