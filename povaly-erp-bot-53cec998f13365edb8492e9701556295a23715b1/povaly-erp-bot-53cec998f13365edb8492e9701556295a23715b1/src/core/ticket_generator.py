"""Automatic ticket ID generator."""

import re
import logging
from datetime import datetime
from typing import Optional
from src.data.adapters.sqlite_adapter import SQLiteAdapter
from src.core.brand_mapper import BrandMapper

logger = logging.getLogger(__name__)


class TicketGenerator:
    """Generates unique ticket IDs automatically."""
    
    def __init__(self, db_adapter: SQLiteAdapter, brand_mapper: BrandMapper):
        """
        Initialize ticket generator.
        
        Args:
            db_adapter: Database adapter for checking existing tickets
            brand_mapper: Brand name to code mapper
        """
        self.db = db_adapter
        self.brand_mapper = brand_mapper
    
    async def generate_ticket_id(self, brand_name: str) -> str:
        """
        Generate next unique ticket ID for a brand.
        Format: [BRANDYYMM##]
        Example: [POV260401]
        
        - Brand: 3 characters (POV, VRB, GSM)
        - Year+Month: 4 digits (2604 = April 2026)
        - Serial: 2+ digits (01, 02, ..., 99, 100, ...)
        
        Sequential per month: POV260405 (April) → POV260501 (May, resets to 01)
        
        Args:
            brand_name: Full brand name (e.g., "VorosaBajar", "GSMAura", "Povaly")
        
        Returns:
            Generated ticket ID (e.g., "POV260401")
        """
        # Get brand code (3 characters)
        brand_code = self.brand_mapper.get_code(brand_name)
        if not brand_code:
            # Fallback: use first 3 letters
            brand_code = brand_name[:3].upper()
        
        logger.info(f"🎫 Generating ticket for brand '{brand_name}' -> code '{brand_code}'")
        # Ensure brand code is exactly 3 characters
        if len(brand_code) > 3:
            brand_code = brand_code[:3]
        elif len(brand_code) < 3:
            brand_code = brand_code.ljust(3, 'X')  # Pad with X if needed
        
        # Get current year-month (YYMM format)
        now = datetime.now()
        yymm = now.strftime("%y%m")  # e.g., "2604" for April 2026
        
        # Get the highest ticket number for this brand and month
        prefix = f"{brand_code}{yymm}"
        
        logger.info(f"🔍 Looking for tickets with prefix: {prefix}")
        
        # Query database for tickets with this prefix using proper database method
        try:
            # Ensure any pending transactions are committed before querying
            await self.db.conn.commit()
            
            # Use parameterized query to find the highest ticket number for this prefix
            # Get all tickets with this prefix and sort them numerically in Python
            query = "SELECT ticket FROM tasks WHERE ticket LIKE ? ORDER BY ticket DESC"
            
            # Execute query using the database adapter's connection
            async with self.db.conn.execute(query, (f"{prefix}%",)) as cursor:
                rows = await cursor.fetchall()
                
                if rows:
                    # Find the highest number by parsing all tickets
                    max_number = 0
                    last_ticket = None
                    
                    for row in rows:
                        ticket = row[0]
                        serial_part = ticket[len(prefix):]
                        try:
                            number = int(serial_part)
                            if number > max_number:
                                max_number = number
                                last_ticket = ticket
                        except ValueError:
                            logger.warning(f"Invalid serial number in ticket {ticket}: {serial_part}")
                            continue
                    
                    if last_ticket:
                        logger.info(f"📋 Found last ticket: {last_ticket}")
                        next_number = max_number + 1
                        logger.info(f"➕ Last number: {max_number}, Next number: {next_number}")
                    else:
                        # No valid tickets found
                        next_number = 1
                        logger.info(f"🆕 No valid tickets found, starting with 01")
                else:
                    # First ticket of the month for this brand
                    next_number = 1
                    logger.info(f"🆕 No existing tickets found, starting with 01")
                    
        except Exception as e:
            logger.error(f"Error querying tickets for prefix {prefix}: {e}", exc_info=True)
            # If query fails, try a different approach - get all tasks and filter
            try:
                # Get all tasks and find the highest number for this prefix
                all_tasks = await self._get_all_tasks_with_prefix(prefix)
                if all_tasks:
                    max_number = 0
                    for task_ticket in all_tasks:
                        serial_part = task_ticket[len(prefix):]
                        try:
                            number = int(serial_part)
                            max_number = max(max_number, number)
                        except ValueError:
                            continue
                    next_number = max_number + 1
                    logger.info(f"✅ Fallback query found max number: {max_number}, next: {next_number}")
                else:
                    next_number = 1
                    logger.info(f"🆕 Fallback query found no tickets, starting with 01")
            except Exception as e2:
                logger.error(f"Fallback query also failed: {e2}", exc_info=True)
                next_number = 1
        
        # Generate ticket ID with zero-padded number (minimum 2 digits)
        ticket_id = f"{brand_code}{yymm}{next_number:02d}"
        
        logger.info(f"✅ Generated ticket ID: {ticket_id} (brand: {brand_name}, prefix: {prefix}, next: {next_number})")
        return ticket_id
    
    async def _get_all_tasks_with_prefix(self, prefix: str) -> list:
        """
        Fallback method to get all tasks with a specific prefix.
        
        Args:
            prefix: Ticket prefix (e.g., "GSM2604")
            
        Returns:
            List of ticket IDs matching the prefix, sorted numerically by serial number
        """
        try:
            # Use parameterized query to safely get all tickets with this prefix
            query = "SELECT ticket FROM tasks WHERE ticket LIKE ?"
            async with self.db.conn.execute(query, (f"{prefix}%",)) as cursor:
                rows = await cursor.fetchall()
                tickets = [row[0] for row in rows]
                
                # Sort numerically by the serial number part
                def get_serial_number(ticket):
                    serial_part = ticket[len(prefix):]
                    try:
                        return int(serial_part)
                    except ValueError:
                        return 0
                
                # Sort in descending order (highest first)
                tickets.sort(key=get_serial_number, reverse=True)
                return tickets
        except Exception as e:
            logger.error(f"Error in fallback query: {e}", exc_info=True)
            return []
    
    def is_auto_ticket_placeholder(self, ticket_value: str) -> bool:
        """
        Check if ticket value is a placeholder for auto-generation.
        
        Args:
            ticket_value: The value from [TICKET] field
        
        Returns:
            True if it's a placeholder (empty, whitespace, or None)
        """
        # Handle None or empty values
        if not ticket_value:
            return True
            
        # Remove # symbol and whitespace
        cleaned = ticket_value.replace('#', '').strip()
        
        # Empty or just whitespace = auto-generate
        return len(cleaned) == 0
