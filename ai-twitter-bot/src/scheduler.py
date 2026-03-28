"""Scheduling functionality for automated daily posting."""

import asyncio
import random
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import schedule
from loguru import logger



# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from main import main as run_agent
from config import config

class TwitterScheduler:
    """Scheduler for automated Twitter posting."""
    
    def __init__(self):
        """Initialize scheduler."""
        self.is_running = False
        self.last_post_date: Optional[datetime] = None
    
    def schedule_daily_post(self) -> None:
        """Schedule daily tweet posting with randomization."""
        base_time = f"{config.post_time_hour:02d}:{config.post_time_minute:02d}"
        
        logger.info(f"Scheduling daily posts around {base_time} with ±{config.random_delay_minutes}min variation")
        
        # Schedule the job
        schedule.every().day.at(base_time).do(self._post_with_delay)
        
        logger.info("Daily posting schedule configured")
    
    def _post_with_delay(self) -> None:
        """Execute posting with random delay for human-like behavior."""
        try:
            # Check if we already posted today
            today = datetime.now().date()
            if self.last_post_date == today:
                logger.info("Already posted today, skipping")
                return
            
            # Add random delay
            delay_minutes = random.randint(-config.random_delay_minutes, config.random_delay_minutes)
            delay_seconds = delay_minutes * 60
            
            if delay_seconds > 0:
                logger.info(f"Adding random delay of {delay_minutes} minutes")
                time.sleep(delay_seconds)
            elif delay_seconds < 0:
                logger.info(f"Posting {abs(delay_minutes)} minutes early")
            
            # Run the main agent
            logger.info("Starting scheduled tweet posting")
            asyncio.run(run_agent())
            
            # Update last post date
            self.last_post_date = today
            logger.success("Scheduled posting completed")
            
        except Exception as e:
            logger.error(f"Error in scheduled posting: {e}")
    
    def run_scheduler(self) -> None:
        """Run the scheduler continuously."""
        self.is_running = True
        logger.info("Starting Twitter posting scheduler")
        
        # Schedule the daily posts
        self.schedule_daily_post()
        
        # Show next scheduled run
        next_run = schedule.next_run()
        logger.info(f"Next scheduled post: {next_run}")
        
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
        finally:
            self.is_running = False
            logger.info("Scheduler stopped")
    
    def stop_scheduler(self) -> None:
        """Stop the scheduler."""
        self.is_running = False
        logger.info("Stopping scheduler...")
    
    def get_next_run_time(self) -> Optional[datetime]:
        """Get the next scheduled run time.
        
        Returns:
            Next run datetime or None if no jobs scheduled
        """
        return schedule.next_run()
    
    def clear_schedule(self) -> None:
        """Clear all scheduled jobs."""
        schedule.clear()
        logger.info("All scheduled jobs cleared")

def main() -> None:
    """Main scheduler entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Twitter Agent Scheduler")
    parser.add_argument(
        "--run-now", 
        action="store_true", 
        help="Run the agent once immediately instead of scheduling"
    )
    parser.add_argument(
        "--test-schedule", 
        action="store_true", 
        help="Test the schedule without actually posting"
    )
    
    args = parser.parse_args()
    
    if args.run_now:
        asyncio.run(run_agent())
    elif args.test_schedule:
        scheduler = TwitterScheduler()
        scheduler.schedule_daily_post()
        next_run = scheduler.get_next_run_time()
        print(f"Next scheduled run would be: {next_run}")
    else:
        # Run the scheduler
        scheduler = TwitterScheduler()
        try:
            scheduler.run_scheduler()
        except KeyboardInterrupt:
            scheduler.stop_scheduler()

if __name__ == "__main__":
    main()