# 🎂 Birthday System - User Guide

**Version 1.0.0** | Povaly Operations Bot

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Adding Your Birthday](#adding-your-birthday)
4. [Viewing Your Birthday](#viewing-your-birthday)
5. [Updating Your Information](#updating-your-information)
6. [How Birthday Wishes Work](#how-birthday-wishes-work)
7. [Birthday Reminders](#birthday-reminders)
8. [Commands Reference](#commands-reference)
9. [FAQ](#faq)

---

## 🎯 Overview

The Birthday System automatically celebrates team members' birthdays with:

- **🎉 Automatic Birthday Wishes** - Sent at 9:00 AM on your birthday
- **📢 Public Announcements** - Posted in Official Directives topic
- **💌 Personal Messages** - Direct message to you
- **⏰ Reminders** - Sent 1 day before to you and admins
- **🎁 Custom Wishes** - Admins can send personalized messages

---

## 🚀 Getting Started

### First-Time Setup

When you first join the group and send a message, Pova will:

1. **Create your account** automatically
2. **Send you a welcome DM** with instructions
3. **Ask for your employee information** (including birthday)

**Example Welcome Message:**
```
👋 Welcome to Povaly Operations!

To complete your employee profile, please provide your information...

[EMPLOYEE_INFO]
[NAME] Your Full Name
[BIRTHDAY] DD-MM-YYYY
[EMAIL] your.email@example.com
...
```

### Why Provide Your Birthday?

- ✅ Receive birthday wishes from the team
- ✅ Get celebrated in Official Directives
- ✅ Team knows when to wish you
- ✅ Optional: Show your age (configurable)

---

## 📝 Adding Your Birthday

### Method 1: During First-Time Setup

Reply to Pova's welcome message with your information:

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
```

**Birthday Format:**
- **With year**: `DD-MM-YYYY` (e.g., `15-05-1990`)
  - Shows your age in birthday messages
- **Without year**: `DD-MM` (e.g., `15-05`)
  - Age not shown

### Method 2: Update Later

If you skipped the initial setup, use `/updateinfo`:

1. Type `/updateinfo` in the group or DM
2. Pova sends you the format
3. Reply with your complete information
4. Pova confirms and saves

### Method 3: Update Only Birthday

Use `/updateinfo` and provide all fields, but you can keep existing values and just change the birthday.

---

## 👀 Viewing Your Birthday

### Check Your Birthday

Type `/mybirthday` anywhere in the group or in DM with Pova.

**Example Response:**
```
🎂 Your Birthday Information

📅 Birthday: May 15, 1990 (Age: 36)
⏳ Days until birthday: 42

Update with /updateinfo
```

### View All Your Info

Type `/myinfo` to see your complete employee profile including birthday.

**Example Response:**
```
📋 Your Employee Information

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 Name: John Michael Doe
🎂 Birthday: May 15, 1990 (Age: 36)
📧 Email: john.doe@povaly.com
📱 Phone: +1234567890
🏢 Department: Development
💼 Position: Senior Developer
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Update with /updateinfo
```

---

## 🔄 Updating Your Information

### Update Your Birthday

1. Type `/updateinfo` in the group or DM
2. Pova shows your current information
3. Reply with updated information in the same format
4. Pova validates and saves

**Example:**
```
[EMPLOYEE_INFO]
[NAME] John Michael Doe
[BIRTHDAY] 20-06-1990  ← Changed birthday
[EMAIL] john.doe@povaly.com
[PHONE] +1234567890
[DEPARTMENT] Development
[POSITION] Senior Developer
```

### Skip Initial Setup

If you don't want to provide information right away:

1. Type `/skip` in response to the welcome message
2. You can add information later with `/updateinfo`

---

## 🎉 How Birthday Wishes Work

### Automatic Birthday Wishes

**When:** Every day at **9:00 AM** (GMT+6)

**What Happens:**

1. **Pova checks** for birthdays today
2. **Sends you a DM** with birthday wishes
3. **Posts announcement** in Official Directives topic
4. **Team sees** and can wish you

### Birthday DM (Direct Message)

You receive a personal message like:

```
🎉🎂 HAPPY BIRTHDAY, John! 🎂🎉

Wishing you a fantastic birthday filled with joy, 
success, and wonderful moments! 🌟

May this special day bring you happiness and may 
the year ahead be filled with great achievements 
and prosperity! 🎊

You're turning 36 today! 🎈

Thank you for being an amazing part of our team! 💙

Enjoy your special day! 🥳

With warm wishes,
The Pova Team 🎈

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Your Profile:
💼 Position: Senior Developer
🏢 Department: Development
📅 With us since: January 1, 2024
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Public Announcement (Official Directives)

The team sees:

```
🎉🎂 BIRTHDAY CELEBRATION 🎂🎉

Today is a special day! Let's all wish a very 
Happy Birthday to:

👤 John Michael Doe @john
💼 Senior Developer | 🏢 Development
🎈 Turning 36 today!

🎊 Join us in celebrating their special day!

Drop your wishes below! 👇
🎈🎁🥳🎉

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 With Povaly since: January 1, 2024
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Multiple Birthdays

If multiple people have birthdays on the same day:
- Each person gets their own DM
- Each person gets their own announcement
- All celebrations are posted separately

---

## ⏰ Birthday Reminders

### User Reminder (1 Day Before)

**When:** 6:00 PM the day before your birthday

**You receive:**
```
🎂 Birthday Reminder

Hi John! 👋

Just a friendly reminder that tomorrow is your 
birthday! 🎉

📅 Date: May 15th
🎈 We'll be celebrating your special day!

Get ready for some birthday wishes! 🥳

Have a wonderful day! ✨
```

### Admin Reminders

Admins and managers receive reminders about upcoming birthdays:

**Admin DM:**
```
🎂 Birthday Reminder - Tomorrow

The following team members have birthdays tomorrow:

1️⃣ John Michael Doe @john
   💼 Senior Developer | 🏢 Development
   📅 Birthday: May 15th
   🎈 Turning 36

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 Total: 1 birthday tomorrow
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

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 Total: 1 birthday
⏰ Auto wishes: 9:00 AM tomorrow
📢 Announcement: Official Directives
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Custom wishes: /birthday @john Message
```

---

## 📚 Commands Reference

### User Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/updateinfo` | Update your employee information | `/updateinfo` |
| `/myinfo` | View your complete employee profile | `/myinfo` |
| `/mybirthday` | View your birthday information | `/mybirthday` |
| `/skip` | Skip employee info setup | `/skip` |
| `/birthdays` | View upcoming birthdays (30 days) | `/birthdays` |
| `/birthdaytoday` | View today's birthdays | `/birthdaytoday` |

### Admin Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/setinfo @user` | Set user's employee information | `/setinfo @john` |
| `/viewinfo @user` | View user's employee information | `/viewinfo @john` |
| `/birthday @user msg` | Send custom birthday wish | `/birthday @john Happy Birthday!` |

---

## ❓ FAQ

### Q: Is my birthday information private?

**A:** Your birthday is visible to:
- You (in your profile)
- Admins and managers
- All team members on your birthday (via announcement)

Your full employee information is only visible to you and admins.

---

### Q: Can I hide my age?

**A:** Yes! When adding your birthday:
- Use `DD-MM-YYYY` format → Age will be shown
- Use `DD-MM` format → Age will NOT be shown

Example:
- `15-05-1990` → Shows "Turning 36"
- `15-05` → No age shown

---

### Q: What if I don't want birthday wishes?

**A:** You can:
1. Not provide your birthday (skip the field)
2. Contact an admin to remove your birthday
3. Use `/updateinfo` and omit the birthday field

---

### Q: Can I change my birthday after setting it?

**A:** Yes! Use `/updateinfo` anytime to update your birthday or any other information.

---

### Q: What time are birthday wishes sent?

**A:** 
- **Birthday wishes**: 9:00 AM (GMT+6) on your birthday
- **Reminders**: 6:00 PM (GMT+6) the day before

---

### Q: Will I get wishes if I'm on leave?

**A:** Yes! Birthday wishes are sent regardless of leave status. The team will still celebrate you! 🎉

---

### Q: What if multiple people have the same birthday?

**A:** Each person gets:
- Their own personal DM
- Their own announcement in Official Directives
- All celebrations happen separately

---

### Q: Can admins send custom birthday messages?

**A:** Yes! Admins can use:
```
/birthday @username Your custom birthday message here
```

This sends a personalized message instead of the automatic one.

---

### Q: What if my birthday is February 29 (leap year)?

**A:** The system handles leap years:
- On leap years: Celebrated on Feb 29
- On non-leap years: Celebrated on Feb 28

---

### Q: Can I see who has birthdays coming up?

**A:** Yes! Use `/birthdays` to see all birthdays in the next 30 days.

---

### Q: What if I made a mistake in my birthday?

**A:** Simply use `/updateinfo` to correct it. The system will update immediately.

---

### Q: Do I need to provide my birth year?

**A:** No, it's optional:
- **With year**: System can calculate and show your age
- **Without year**: Birthday is celebrated, but age not shown

---

### Q: What happens if the bot is offline on my birthday?

**A:** When the bot comes back online:
- It checks for missed birthdays
- Sends wishes if they haven't been sent yet
- You won't miss your celebration!

---

## 🎁 Tips

✅ **DO:**
- Provide accurate birthday information
- Use the correct format (DD-MM-YYYY or DD-MM)
- Update your info if it changes
- Check `/birthdays` to see upcoming celebrations
- Wish your teammates on their birthdays!

❌ **DON'T:**
- Provide fake birthdays
- Delete birthday announcement messages
- Ignore the welcome message (add your info!)

---

## 📞 Support

**Need Help?**
- Type `/help` for general bot help
- Contact your manager or admin
- Check this guide for answers

**Found a Bug?**
- Report in Core Operations topic
- Use `/newissue` command
- Tag an admin

---

## 🎉 Enjoy Your Celebration!

The Birthday System is designed to make everyone feel special on their day. Make sure to add your birthday and celebrate with the team! 🎂🎈

---

**Document Version:** 1.0.0  
**Last Updated:** May 3, 2026  
**System:** Povaly Operations Bot
