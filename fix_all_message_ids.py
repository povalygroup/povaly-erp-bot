"""
Comprehensive script to fix all message_ids in database.

This script is useful when:
- Messages were edited/replaced and message_ids got out of sync
- After bot restart when message_ids need to be verified
- When reactions aren't working due to message_id mismatch

This script:
1. Gets all tasks from database
2. Scans a range of message IDs in the task allocation topic
3. Copies each message to trash to read its content
4. Extracts the ticket from the message
5. Updates the database with correct message_id
6. Cleans up copied messages from trash

Usage:
    python fix_all_message_ids.py

Note: Adjust the message ID range (1900-1960) based on your needs.
"""

import asyncio
import sqlite3
import re
import os
from dotenv import load_dotenv
from telegram import Bot

async def fix_all_message_ids():
    """Fix all message_ids by scanning Telegram messages."""
    
    # Load environment
    load_dotenv()
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = int(os.getenv('TELEGRAM_GROUP_ID'))
    topic_task = int(os.getenv('TOPIC_TASK_ALLOCATION'))
    topic_trash = int(os.getenv('TOPIC_TRASH'))
    
    bot = Bot(token=bot_token)
    
    # Connect to database
    conn = sqlite3.connect('data/povaly_bot.db')
    cursor = conn.cursor()
    
    # Get all non-archived tasks
    cursor.execute("SELECT ticket, message_id, state FROM tasks WHERE state != 'ARCHIVED' ORDER BY created_at DESC")
    db_tasks = cursor.fetchall()
    
    print(f"📊 Found {len(db_tasks)} tasks in database")
    print(f"🔍 Scanning message IDs from 1900 to 1960...")
    
    # Map to store found tickets and their message_ids
    found_tickets = {}
    trash_messages = []  # Track messages we copy to trash for cleanup
    
    # Scan message range
    for msg_id in range(1900, 1961):
        try:
            # Copy message to trash to read it
            copied = await bot.copy_message(
                chat_id=chat_id,
                from_chat_id=chat_id,
                message_id=msg_id,
                message_thread_id=topic_trash
            )
            
            trash_messages.append(copied.message_id)
            
            # Get the copied message to read its text
            copied_msg = await bot.forward_message(
                chat_id=chat_id,
                from_chat_id=chat_id,
                message_id=copied.message_id
            )
            
            # Extract ticket from message text
            if copied_msg.text:
                # Look for [TICKET] #TICKETID pattern
                match = re.search(r'\[TICKET\]\s*#?([A-Z]{3}\d{6})', copied_msg.text)
                if match:
                    ticket = match.group(1)
                    found_tickets[ticket] = msg_id
                    print(f"  ✅ Found {ticket} at message {msg_id}")
            
            # Delete the forwarded message
            await copied_msg.delete()
            
            # Small delay to avoid rate limiting
            await asyncio.sleep(0.1)
            
        except Exception as e:
            # Message doesn't exist or can't be accessed
            pass
    
    print(f"\n📊 Found {len(found_tickets)} tickets in Telegram")
    
    # Update database
    updated_count = 0
    for ticket, message_id in found_tickets.items():
        # Check if this ticket exists in database
        cursor.execute("SELECT message_id FROM tasks WHERE ticket = ?", (ticket,))
        row = cursor.fetchone()
        
        if row:
            old_message_id = row[0]
            if old_message_id != message_id:
                cursor.execute("UPDATE tasks SET message_id = ? WHERE ticket = ?", (message_id, ticket))
                print(f"  🔄 Updated {ticket}: {old_message_id} -> {message_id}")
                updated_count += 1
            else:
                print(f"  ✓ {ticket}: message_id already correct ({message_id})")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Updated {updated_count} tasks")
    
    # Clean up trash
    print(f"\n🗑️ Cleaning up {len(trash_messages)} copied messages from trash...")
    for trash_msg_id in trash_messages:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=trash_msg_id)
        except:
            pass
    
    print("✅ Cleanup complete")

if __name__ == "__main__":
    asyncio.run(fix_all_message_ids())
