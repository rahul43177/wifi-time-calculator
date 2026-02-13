"""
Task 7.7: Gamification Module

Minimal gamification system with:
- Streak counter (consecutive days meeting target)
- Basic achievements (Early Bird, Marathon Runner, Consistent)
- JSON file storage

Dependencies: Requires analytics module for historical data
"""

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from app.config import DATA_DIR


GAMIFICATION_FILE = DATA_DIR / "gamification.json"


class Achievement:
    """Achievement definition."""

    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        icon: str,
        condition_met: bool = False
    ):
        self.id = id
        self.name = name
        self.description = description
        self.icon = icon
        self.condition_met = condition_met


class GamificationService:
    """Service for managing streaks and achievements."""

    def __init__(self):
        self.data_file = GAMIFICATION_FILE
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        """Ensure gamification data file exists."""
        if not self.data_file.exists():
            initial_data = {
                "current_streak": 0,
                "longest_streak": 0,
                "last_streak_date": None,
                "achievements": [],
                "total_days_met_target": 0
            }
            self._save_data(initial_data)

    def _load_data(self) -> Dict:
        """Load gamification data from file."""
        try:
            with open(self.data_file, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._ensure_file_exists()
            with open(self.data_file, "r") as f:
                return json.load(f)

    def _save_data(self, data: Dict) -> None:
        """Save gamification data to file."""
        with open(self.data_file, "w") as f:
            json.dump(data, f, indent=2)

    def update_streak(self, date_str: str, target_met: bool) -> None:
        """
        Update streak counter based on whether target was met.

        Args:
            date_str: Date in YYYY-MM-DD format
            target_met: Whether the target was met on this date
        """
        data = self._load_data()

        if not target_met:
            # Target not met, don't update streak
            return

        # Increment total days met target
        data["total_days_met_target"] = data.get("total_days_met_target", 0) + 1

        last_streak_date = data.get("last_streak_date")

        if last_streak_date is None:
            # First streak day
            data["current_streak"] = 1
            data["last_streak_date"] = date_str
        else:
            # Check if this is consecutive
            last_date = datetime.strptime(last_streak_date, "%Y-%m-%d").date()
            current_date = datetime.strptime(date_str, "%Y-%m-%d").date()

            if (current_date - last_date).days == 1:
                # Consecutive day
                data["current_streak"] += 1
                data["last_streak_date"] = date_str
            elif current_date == last_date:
                # Same day, no change
                pass
            else:
                # Streak broken, restart
                data["current_streak"] = 1
                data["last_streak_date"] = date_str

        # Update longest streak
        if data["current_streak"] > data.get("longest_streak", 0):
            data["longest_streak"] = data["current_streak"]

        self._save_data(data)

    def check_achievements(
        self,
        sessions: List[Dict],
        total_days_met: int
    ) -> List[Achievement]:
        """
        Check and return earned achievements.

        Args:
            sessions: List of session dictionaries
            total_days_met: Total number of days target was met

        Returns:
            List of Achievement objects
        """
        data = self._load_data()
        earned_ids = set(data.get("achievements", []))
        achievements = []

        # Achievement 1: Early Bird (started before 9 AM)
        early_bird_earned = "early_bird" in earned_ids
        for session in sessions:
            if not early_bird_earned:
                start_time = session.get("start_time", "")
                if start_time and start_time < "09:00:00":
                    early_bird_earned = True
                    earned_ids.add("early_bird")
                    break

        achievements.append(Achievement(
            id="early_bird",
            name="Early Bird",
            description="Started work before 9 AM",
            icon="🌅",
            condition_met=early_bird_earned
        ))

        # Achievement 2: Marathon Runner (5+ hours in one session)
        marathon_earned = "marathon_runner" in earned_ids
        for session in sessions:
            if not marathon_earned:
                duration_min = session.get("duration_minutes", 0)
                if duration_min >= 300:  # 5 hours = 300 minutes
                    marathon_earned = True
                    earned_ids.add("marathon_runner")
                    break

        achievements.append(Achievement(
            id="marathon_runner",
            name="Marathon Runner",
            description="Worked 5+ hours in one session",
            icon="🏃",
            condition_met=marathon_earned
        ))

        # Achievement 3: Consistent (met target 5 days in a row)
        consistent_earned = "consistent" in earned_ids or data.get("current_streak", 0) >= 5

        if consistent_earned and "consistent" not in earned_ids:
            earned_ids.add("consistent")

        achievements.append(Achievement(
            id="consistent",
            name="Consistent",
            description="Met target 5 days in a row",
            icon="🔥",
            condition_met=consistent_earned
        ))

        # Achievement 4: Dedicated (total 10 days met target)
        dedicated_earned = "dedicated" in earned_ids or total_days_met >= 10

        if dedicated_earned and "dedicated" not in earned_ids:
            earned_ids.add("dedicated")

        achievements.append(Achievement(
            id="dedicated",
            name="Dedicated",
            description="Met target on 10+ different days",
            icon="⭐",
            condition_met=dedicated_earned
        ))

        # Save updated achievements
        data["achievements"] = list(earned_ids)
        self._save_data(data)

        return achievements

    def get_streak_info(self) -> Dict:
        """Get current streak information."""
        data = self._load_data()

        return {
            "current_streak": data.get("current_streak", 0),
            "longest_streak": data.get("longest_streak", 0),
            "total_days_met_target": data.get("total_days_met_target", 0)
        }

    def get_achievements(self, sessions: List[Dict] = None) -> List[Dict]:
        """
        Get all achievements with their status.

        Args:
            sessions: Optional list of recent sessions for checking

        Returns:
            List of achievement dictionaries
        """
        if sessions is None:
            sessions = []

        data = self._load_data()
        achievements = self.check_achievements(
            sessions,
            data.get("total_days_met_target", 0)
        )

        return [
            {
                "id": a.id,
                "name": a.name,
                "description": a.description,
                "icon": a.icon,
                "earned": a.condition_met
            }
            for a in achievements
        ]


# Global instance
gamification_service = GamificationService()
