"""Smart task routing service for auto-assignment based on workload and expertise."""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple
from src.data.models.task import TaskState

logger = logging.getLogger(__name__)


class TaskRoutingService:
    """Service for intelligent task routing and auto-assignment."""
    
    def __init__(self, task_service, user_repo, db_adapter, config):
        """Initialize routing service."""
        self.task_service = task_service
        self.user_repo = user_repo
        self.db_adapter = db_adapter
        self.config = config
    
    async def calculate_workload(self, user_id: int) -> Dict:
        """
        Calculate current workload for a user.
        
        Returns:
            {
                'user_id': int,
                'active_tasks': int,
                'pending_qa': int,
                'total_active': int,
                'workload_score': float (0-100)
            }
        """
        try:
            # Get active tasks (not completed/archived)
            active_states = [
                TaskState.ASSIGNED,
                TaskState.STARTED,
                TaskState.QA_SUBMITTED,
                TaskState.REJECTED
            ]
            
            active_tasks = []
            for state in active_states:
                tasks = await self.task_service.task_repo.get_tasks_by_assignee(user_id, state)
                active_tasks.extend(tasks)
            
            # Count tasks in each state
            assigned_count = len([t for t in active_tasks if t.state == TaskState.ASSIGNED])
            started_count = len([t for t in active_tasks if t.state == TaskState.STARTED])
            qa_count = len([t for t in active_tasks if t.state == TaskState.QA_SUBMITTED])
            rejected_count = len([t for t in active_tasks if t.state == TaskState.REJECTED])
            
            total_active = len(active_tasks)
            
            # Calculate workload score (0-100)
            # Weights: ASSIGNED=1, STARTED=2, QA_SUBMITTED=1.5, REJECTED=2
            weighted_score = (
                assigned_count * 1 +
                started_count * 2 +
                qa_count * 1.5 +
                rejected_count * 2
            )
            
            # Normalize to 0-100 scale (assuming max 20 weighted tasks = 100%)
            workload_score = min(100, (weighted_score / 20) * 100)
            
            return {
                'user_id': user_id,
                'assigned': assigned_count,
                'started': started_count,
                'qa_submitted': qa_count,
                'rejected': rejected_count,
                'total_active': total_active,
                'workload_score': workload_score
            }
        
        except Exception as e:
            logger.error(f"Error calculating workload for user {user_id}: {e}")
            return {
                'user_id': user_id,
                'assigned': 0,
                'started': 0,
                'qa_submitted': 0,
                'rejected': 0,
                'total_active': 0,
                'workload_score': 0
            }
    
    async def get_brand_expertise(self, user_id: int, brand: str) -> Dict:
        """
        Get expertise level for a user in a specific brand.
        
        Returns:
            {
                'user_id': int,
                'brand': str,
                'completed_count': int,
                'expertise_score': float (0-100)
            }
        """
        try:
            # Get all completed tasks for this user in this brand
            all_tasks = await self.task_service.task_repo.get_tasks_by_assignee(user_id)
            
            completed_tasks = [
                t for t in all_tasks
                if t.state == TaskState.APPROVED and t.brand.upper() == brand.upper()
            ]
            
            completed_count = len(completed_tasks)
            
            # Expertise score: 0-100 based on completed tasks
            # 1-5 tasks = 20, 6-10 = 40, 11-20 = 60, 21-50 = 80, 50+ = 100
            if completed_count == 0:
                expertise_score = 0
            elif completed_count <= 5:
                expertise_score = 20
            elif completed_count <= 10:
                expertise_score = 40
            elif completed_count <= 20:
                expertise_score = 60
            elif completed_count <= 50:
                expertise_score = 80
            else:
                expertise_score = 100
            
            return {
                'user_id': user_id,
                'brand': brand,
                'completed_count': completed_count,
                'expertise_score': expertise_score
            }
        
        except Exception as e:
            logger.error(f"Error calculating expertise for user {user_id} in brand {brand}: {e}")
            return {
                'user_id': user_id,
                'brand': brand,
                'completed_count': 0,
                'expertise_score': 0
            }
    
    async def find_best_assignee(self, brand: str, exclude_user_ids: List[int] = None) -> Optional[int]:
        """
        Find the best user to assign a task to based on workload and expertise.
        
        Args:
            brand: Task brand
            exclude_user_ids: List of user IDs to exclude from consideration
        
        Returns:
            Best user ID or None if no suitable user found
        """
        try:
            if exclude_user_ids is None:
                exclude_user_ids = []
            
            # Get all active employees (not admins/managers/owners)
            all_users = await self.user_repo.get_all_users()
            
            # Filter to regular employees only, excluding those on leave
            eligible_users = [
                u for u in all_users
                if u.user_id not in exclude_user_ids and
                   u.user_id not in self.config.ADMINISTRATORS and
                   u.user_id not in self.config.MANAGERS and
                   u.user_id not in self.config.OWNERS and
                   not u.is_on_leave  # Exclude users on leave
            ]
            
            if not eligible_users:
                logger.warning(f"No eligible users found for task assignment (brand: {brand})")
                return None
            
            # Calculate scores for each user
            user_scores = []
            
            for user in eligible_users:
                try:
                    workload = await self.calculate_workload(user.user_id)
                    expertise = await self.get_brand_expertise(user.user_id, brand)
                    
                    # Combined score calculation
                    # Lower workload is better (100 - workload_score)
                    # Higher expertise is better
                    # Weights: 60% workload, 40% expertise
                    
                    workload_component = (100 - workload['workload_score']) * 0.6
                    expertise_component = expertise['expertise_score'] * 0.4
                    
                    combined_score = workload_component + expertise_component
                    
                    user_scores.append({
                        'user_id': user.user_id,
                        'username': user.username,
                        'workload_score': workload['workload_score'],
                        'expertise_score': expertise['expertise_score'],
                        'combined_score': combined_score,
                        'total_active': workload['total_active']
                    })
                
                except Exception as e:
                    logger.warning(f"Error calculating score for user {user.user_id}: {e}")
                    continue
            
            if not user_scores:
                logger.warning(f"Could not calculate scores for any users (brand: {brand})")
                return None
            
            # Sort by combined score (highest first)
            user_scores.sort(key=lambda x: x['combined_score'], reverse=True)
            
            best_user = user_scores[0]
            logger.info(f"Best assignee for {brand}: User {best_user['user_id']} (@{best_user['username']}) - Score: {best_user['combined_score']:.1f} (Workload: {best_user['workload_score']:.1f}, Expertise: {best_user['expertise_score']:.1f})")
            
            return best_user['user_id']
        
        except Exception as e:
            logger.error(f"Error finding best assignee for brand {brand}: {e}", exc_info=True)
            return None
    
    async def auto_assign_task(self, ticket: str, brand: str, creator_id: int) -> Tuple[bool, Optional[int], str]:
        """
        Automatically assign a task to the best available user.
        
        Args:
            ticket: Task ticket ID
            brand: Task brand
            creator_id: User who created the task
        
        Returns:
            (success: bool, assigned_user_id: Optional[int], message: str)
        """
        try:
            # Check if auto-assign is enabled
            if not getattr(self.config, 'ENABLE_AUTO_ASSIGN', False):
                return False, None, "Auto-assign is disabled"
            
            # Find best assignee (exclude creator)
            best_user_id = await self.find_best_assignee(brand, exclude_user_ids=[creator_id])
            
            if not best_user_id:
                return False, None, "No eligible users found for auto-assignment"
            
            # Get the task
            task = await self.task_service.get_task(ticket)
            if not task:
                return False, None, f"Task {ticket} not found"
            
            # Update task assignee
            task.assignee_id = best_user_id
            await self.task_service.task_repo.db.conn.execute(
                "UPDATE tasks SET assignee_id = ? WHERE ticket = ?",
                (best_user_id, ticket)
            )
            await self.task_service.task_repo.db.conn.commit()
            
            # Get user info
            user = await self.user_repo.get_user(best_user_id)
            username = user.username if user else f"User {best_user_id}"
            
            message = f"Auto-assigned to @{username}"
            logger.info(f"✅ Auto-assigned task {ticket} to user {best_user_id} (@{username})")
            
            return True, best_user_id, message
        
        except Exception as e:
            logger.error(f"Error auto-assigning task {ticket}: {e}", exc_info=True)
            return False, None, f"Error: {str(e)}"
    
    async def get_team_workload_summary(self) -> List[Dict]:
        """
        Get workload summary for all team members.
        
        Returns:
            List of workload dicts sorted by workload score (highest first)
        """
        try:
            all_users = await self.user_repo.get_all_users()
            
            # Filter to regular employees only
            employees = [
                u for u in all_users
                if u.user_id not in self.config.ADMINISTRATORS and
                   u.user_id not in self.config.MANAGERS and
                   u.user_id not in self.config.OWNERS
            ]
            
            workload_summary = []
            
            for user in employees:
                try:
                    workload = await self.calculate_workload(user.user_id)
                    workload['username'] = user.username
                    workload_summary.append(workload)
                except Exception as e:
                    logger.warning(f"Error getting workload for user {user.user_id}: {e}")
                    continue
            
            # Sort by workload score (highest first)
            workload_summary.sort(key=lambda x: x['workload_score'], reverse=True)
            
            return workload_summary
        
        except Exception as e:
            logger.error(f"Error getting team workload summary: {e}", exc_info=True)
            return []
