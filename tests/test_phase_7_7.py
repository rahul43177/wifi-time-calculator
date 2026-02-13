"""
Task 7.7: Gamification Elements — Test Suite

Tests for streaks, achievements, and gamification integration.

Acceptance Criteria:
- Streak counter tracking consecutive days meeting target
- Achievement badges (Early Bird, Marathon Runner, Consistent, Dedicated)
- JSON file persistence for gamification data
- API endpoint for gamification data
- Frontend UI displaying streaks and achievements
"""

import json
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch


@pytest.fixture
def project_root():
    """Return project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def gamification_module(project_root):
    """Import gamification module."""
    import sys
    sys.path.insert(0, str(project_root))
    from app.gamification import GamificationService, Achievement
    return GamificationService, Achievement


@pytest.fixture
def temp_gamification_file(tmp_path):
    """Create temporary gamification file."""
    return tmp_path / "gamification.json"


@pytest.fixture
def gamification_service(gamification_module, temp_gamification_file, monkeypatch):
    """Create gamification service with temporary file."""
    GamificationService, _ = gamification_module
    # Monkeypatch the _get_gamification_file function to return temp file
    monkeypatch.setattr("app.gamification._get_gamification_file", lambda: temp_gamification_file)
    return GamificationService()


# --- Backend Tests: Streak Tracking ---

def test_gamification_service_initializes_file(gamification_service, temp_gamification_file):
    """Test that gamification service creates initial data file."""
    assert temp_gamification_file.exists()

    with open(temp_gamification_file) as f:
        data = json.load(f)

    assert data["current_streak"] == 0
    assert data["longest_streak"] == 0
    assert data["total_days_met_target"] == 0
    assert data["last_streak_date"] is None
    assert data["achievements"] == []


def test_update_streak_first_day(gamification_service, temp_gamification_file):
    """Test streak update on first day meeting target."""
    gamification_service.update_streak("2025-01-15", target_met=True)

    with open(temp_gamification_file) as f:
        data = json.load(f)

    assert data["current_streak"] == 1
    assert data["longest_streak"] == 1
    assert data["total_days_met_target"] == 1
    assert data["last_streak_date"] == "2025-01-15"


def test_update_streak_consecutive_days(gamification_service):
    """Test streak increments on consecutive days."""
    gamification_service.update_streak("2025-01-15", target_met=True)
    gamification_service.update_streak("2025-01-16", target_met=True)
    gamification_service.update_streak("2025-01-17", target_met=True)

    streak_info = gamification_service.get_streak_info()
    assert streak_info["current_streak"] == 3
    assert streak_info["longest_streak"] == 3
    assert streak_info["total_days_met_target"] == 3


def test_update_streak_broken(gamification_service):
    """Test streak resets when broken."""
    gamification_service.update_streak("2025-01-15", target_met=True)
    gamification_service.update_streak("2025-01-16", target_met=True)
    # Day gap - streak broken
    gamification_service.update_streak("2025-01-20", target_met=True)

    streak_info = gamification_service.get_streak_info()
    assert streak_info["current_streak"] == 1
    assert streak_info["longest_streak"] == 2  # Previous streak was longer


def test_update_streak_same_day(gamification_service):
    """Test that updating same day doesn't increment streak or total days."""
    gamification_service.update_streak("2025-01-15", target_met=True)
    gamification_service.update_streak("2025-01-15", target_met=True)

    streak_info = gamification_service.get_streak_info()
    assert streak_info["current_streak"] == 1
    assert streak_info["total_days_met_target"] == 1  # Same day doesn't increment total


def test_update_streak_target_not_met(gamification_service):
    """Test that streak doesn't update when target not met."""
    gamification_service.update_streak("2025-01-15", target_met=False)

    streak_info = gamification_service.get_streak_info()
    assert streak_info["current_streak"] == 0
    assert streak_info["total_days_met_target"] == 0


# --- Backend Tests: Achievements ---

def test_achievement_early_bird(gamification_service):
    """Test Early Bird achievement (started before 9 AM)."""
    sessions = [
        {"start_time": "08:30:00", "duration_minutes": 240}
    ]

    achievements = gamification_service.check_achievements(sessions, total_days_met=0)
    early_bird = next(a for a in achievements if a.id == "early_bird")

    assert early_bird.condition_met is True
    assert early_bird.name == "Early Bird"
    assert early_bird.icon == "🌅"


def test_achievement_early_bird_not_earned(gamification_service):
    """Test Early Bird not earned when starting after 9 AM."""
    sessions = [
        {"start_time": "09:30:00", "duration_minutes": 240}
    ]

    achievements = gamification_service.check_achievements(sessions, total_days_met=0)
    early_bird = next(a for a in achievements if a.id == "early_bird")

    assert early_bird.condition_met is False


def test_achievement_marathon_runner(gamification_service):
    """Test Marathon Runner achievement (5+ hours in one session)."""
    sessions = [
        {"start_time": "09:00:00", "duration_minutes": 300}  # 5 hours
    ]

    achievements = gamification_service.check_achievements(sessions, total_days_met=0)
    marathon = next(a for a in achievements if a.id == "marathon_runner")

    assert marathon.condition_met is True
    assert marathon.name == "Marathon Runner"
    assert marathon.icon == "🏃"


def test_achievement_marathon_runner_not_earned(gamification_service):
    """Test Marathon Runner not earned with less than 5 hours."""
    sessions = [
        {"start_time": "09:00:00", "duration_minutes": 299}  # Just under 5 hours
    ]

    achievements = gamification_service.check_achievements(sessions, total_days_met=0)
    marathon = next(a for a in achievements if a.id == "marathon_runner")

    assert marathon.condition_met is False


def test_achievement_handles_none_duration(gamification_service):
    """Test that achievements gracefully handle None duration (active sessions)."""
    sessions = [
        {"start_time": "09:00:00", "duration_minutes": None},  # Active session
        {"start_time": "08:00:00", "duration_minutes": 180}   # Completed session
    ]

    # Should not raise TypeError
    achievements = gamification_service.check_achievements(sessions, total_days_met=0)

    # Early bird should be earned (started before 9 AM)
    early_bird = next(a for a in achievements if a.id == "early_bird")
    assert early_bird.condition_met is True

    # Marathon runner should not be earned (no session with 5+ hours)
    marathon = next(a for a in achievements if a.id == "marathon_runner")
    assert marathon.condition_met is False


def test_achievement_consistent(gamification_service):
    """Test Consistent achievement (5 day streak)."""
    # Build 5-day streak
    for i in range(5):
        date = (datetime(2025, 1, 15) + timedelta(days=i)).strftime("%Y-%m-%d")
        gamification_service.update_streak(date, target_met=True)

    achievements = gamification_service.check_achievements([], total_days_met=0)
    consistent = next(a for a in achievements if a.id == "consistent")

    assert consistent.condition_met is True
    assert consistent.name == "Consistent"
    assert consistent.icon == "🔥"


def test_achievement_consistent_not_earned(gamification_service):
    """Test Consistent not earned with less than 5 day streak."""
    for i in range(4):
        date = (datetime(2025, 1, 15) + timedelta(days=i)).strftime("%Y-%m-%d")
        gamification_service.update_streak(date, target_met=True)

    achievements = gamification_service.check_achievements([], total_days_met=0)
    consistent = next(a for a in achievements if a.id == "consistent")

    assert consistent.condition_met is False


def test_achievement_dedicated(gamification_service):
    """Test Dedicated achievement (10+ days met target)."""
    achievements = gamification_service.check_achievements([], total_days_met=10)
    dedicated = next(a for a in achievements if a.id == "dedicated")

    assert dedicated.condition_met is True
    assert dedicated.name == "Dedicated"
    assert dedicated.icon == "⭐"


def test_achievement_dedicated_not_earned(gamification_service):
    """Test Dedicated not earned with less than 10 days."""
    achievements = gamification_service.check_achievements([], total_days_met=9)
    dedicated = next(a for a in achievements if a.id == "dedicated")

    assert dedicated.condition_met is False


def test_achievement_persistence(gamification_service, temp_gamification_file):
    """Test that earned achievements are persisted."""
    sessions = [
        {"start_time": "08:30:00", "duration_minutes": 300}  # Early Bird + Marathon
    ]

    gamification_service.check_achievements(sessions, total_days_met=0)

    with open(temp_gamification_file) as f:
        data = json.load(f)

    assert "early_bird" in data["achievements"]
    assert "marathon_runner" in data["achievements"]


# --- Backend Tests: API Integration ---

def test_gamification_api_endpoint_exists(project_root):
    """Test that /api/gamification endpoint exists."""
    import sys
    sys.path.insert(0, str(project_root))
    from app.main import app

    # Check endpoint is registered
    routes = [route.path for route in app.routes]
    assert "/api/gamification" in routes


def test_gamification_api_response_model(project_root):
    """Test that gamification API has correct response model."""
    import sys
    sys.path.insert(0, str(project_root))
    from app.main import GamificationResponse, AchievementResponse

    # Verify response models exist
    assert GamificationResponse is not None
    assert AchievementResponse is not None

    # Verify response model fields
    assert hasattr(GamificationResponse, "model_fields")
    fields = GamificationResponse.model_fields
    assert "current_streak" in fields
    assert "longest_streak" in fields
    assert "total_days_met_target" in fields
    assert "achievements" in fields


def test_session_manager_updates_streak(project_root):
    """Test that session manager calls gamification service on completion."""
    import sys
    sys.path.insert(0, str(project_root))

    # Read session_manager.py to verify integration
    session_manager_file = project_root / "app" / "session_manager.py"
    content = session_manager_file.read_text()

    assert "from app.gamification import gamification_service" in content
    assert "gamification_service.update_streak" in content
    assert "mark_session_completed" in content


# --- Frontend Tests: HTML Structure ---

def test_html_has_gamification_section(project_root):
    """Test that index.html has gamification section."""
    html_file = project_root / "templates" / "index.html"
    html_content = html_file.read_text()

    assert "gamification-section" in html_content
    assert "Task 7.7" in html_content or "Gamification" in html_content


def test_html_has_streak_display(project_root):
    """Test that HTML has streak counter elements."""
    html_file = project_root / "templates" / "index.html"
    html_content = html_file.read_text()

    assert "current-streak" in html_content
    assert "longest-streak" in html_content
    assert "total-days-met" in html_content
    assert "Current Streak" in html_content
    assert "Longest Streak" in html_content


def test_html_has_achievements_grid(project_root):
    """Test that HTML has achievements grid."""
    html_file = project_root / "templates" / "index.html"
    html_content = html_file.read_text()

    assert "achievements-grid" in html_content
    assert 'role="list"' in html_content or 'aria-label="Achievements"' in html_content


def test_html_has_all_achievements(project_root):
    """Test that HTML includes all 4 achievements."""
    html_file = project_root / "templates" / "index.html"
    html_content = html_file.read_text()

    assert "early_bird" in html_content
    assert "marathon_runner" in html_content
    assert "consistent" in html_content
    assert "dedicated" in html_content

    assert "Early Bird" in html_content
    assert "Marathon Runner" in html_content
    assert "Consistent" in html_content
    assert "Dedicated" in html_content


def test_html_achievements_have_icons(project_root):
    """Test that achievements have emoji icons."""
    html_file = project_root / "templates" / "index.html"
    html_content = html_file.read_text()

    # Check for achievement icons
    assert "🌅" in html_content  # Early Bird
    assert "🏃" in html_content  # Marathon Runner
    assert "🔥" in html_content  # Consistent
    assert "⭐" in html_content  # Dedicated


def test_html_achievements_have_descriptions(project_root):
    """Test that achievements have descriptions."""
    html_file = project_root / "templates" / "index.html"
    html_content = html_file.read_text()

    assert "Started work before 9 AM" in html_content
    assert "Worked 5+ hours" in html_content or "5+ hours" in html_content
    assert "Met target 5 days in a row" in html_content
    assert "Met target on 10+" in html_content or "10+ different days" in html_content


# --- Frontend Tests: CSS Styling ---

def test_css_has_gamification_styles(project_root):
    """Test that style.css has gamification styles."""
    css_file = project_root / "static" / "style.css"
    css_content = css_file.read_text()

    assert "gamification-section" in css_content
    assert "Task 7.7" in css_content


def test_css_has_streak_display_styles(project_root):
    """Test that CSS has streak display styles."""
    css_file = project_root / "static" / "style.css"
    css_content = css_file.read_text()

    assert ".streak-display" in css_content
    assert ".streak-item" in css_content
    assert ".streak-value" in css_content


def test_css_has_achievements_grid_styles(project_root):
    """Test that CSS has achievements grid styles."""
    css_file = project_root / "static" / "style.css"
    css_content = css_file.read_text()

    assert ".achievements-grid" in css_content
    assert ".achievement" in css_content


def test_css_has_earned_achievement_styles(project_root):
    """Test that CSS differentiates earned vs locked achievements."""
    css_file = project_root / "static" / "style.css"
    css_content = css_file.read_text()

    assert ".achievement.earned" in css_content
    assert ".locked" in css_content
    assert "opacity" in css_content or "filter" in css_content


def test_css_has_hover_effects(project_root):
    """Test that achievements have hover effects."""
    css_file = project_root / "static" / "style.css"
    css_content = css_file.read_text()

    assert ".achievement:hover" in css_content or ".streak-item:hover" in css_content


# --- Frontend Tests: JavaScript Integration ---

def test_js_has_gamification_endpoint(project_root):
    """Test that JavaScript has gamification endpoint constant."""
    js_file = project_root / "static" / "app.js"
    js_content = js_file.read_text()

    assert "GAMIFICATION_ENDPOINT" in js_content
    assert "/api/gamification" in js_content


def test_js_has_gamification_dom_elements(project_root):
    """Test that JavaScript caches gamification DOM elements."""
    js_file = project_root / "static" / "app.js"
    js_content = js_file.read_text()

    assert "currentStreak" in js_content
    assert "longestStreak" in js_content
    assert "totalDaysMet" in js_content
    assert "achievementsGrid" in js_content


def test_js_has_gamification_state(project_root):
    """Test that JavaScript state includes gamification."""
    js_file = project_root / "static" / "app.js"
    js_content = js_file.read_text()

    assert "gamification:" in js_content or "gamification :" in js_content


def test_js_fetches_gamification_data(project_root):
    """Test that JavaScript fetches gamification data."""
    js_file = project_root / "static" / "app.js"
    js_content = js_file.read_text()

    # Should fetch gamification in sync function
    assert "fetchJson(GAMIFICATION_ENDPOINT)" in js_content or \
           'fetchJson("/api/gamification")' in js_content


def test_js_has_apply_gamification_function(project_root):
    """Test that JavaScript has applyGamification function."""
    js_file = project_root / "static" / "app.js"
    js_content = js_file.read_text()

    assert "applyGamification" in js_content


def test_js_has_render_gamification_function(project_root):
    """Test that JavaScript has renderGamification function."""
    js_file = project_root / "static" / "app.js"
    js_content = js_file.read_text()

    assert "renderGamification" in js_content


def test_js_render_gamification_called(project_root):
    """Test that renderGamification is called in renderAll."""
    js_file = project_root / "static" / "app.js"
    js_content = js_file.read_text()

    # Find renderAll function and check if renderGamification is called
    render_all_start = js_content.find("function renderAll()")
    if render_all_start != -1:
        render_all_section = js_content[render_all_start:render_all_start + 500]
        assert "renderGamification" in render_all_section


def test_js_updates_achievement_classes(project_root):
    """Test that JavaScript updates achievement earned/locked classes."""
    js_file = project_root / "static" / "app.js"
    js_content = js_file.read_text()

    # renderGamification should add/remove 'earned' and 'locked' classes
    render_gamification_match = js_content.find("function renderGamification")
    if render_gamification_match != -1:
        render_section = js_content[render_gamification_match:render_gamification_match + 2000]
        assert "classList.add" in render_section
        assert "earned" in render_section
        assert "locked" in render_section


# --- Integration Tests ---

def test_gamification_complete_flow(gamification_service):
    """Test complete gamification flow from streak to achievements."""
    # Day 1: Start streak, earn Early Bird
    gamification_service.update_streak("2025-01-15", target_met=True)
    sessions = [{"start_time": "08:30:00", "duration_minutes": 240}]
    achievements = gamification_service.check_achievements(sessions, total_days_met=1)

    early_bird = next(a for a in achievements if a.id == "early_bird")
    assert early_bird.condition_met is True

    # Days 2-5: Build streak to 5, earn Consistent
    for i in range(1, 5):
        date = (datetime(2025, 1, 15) + timedelta(days=i)).strftime("%Y-%m-%d")
        gamification_service.update_streak(date, target_met=True)

    achievements = gamification_service.check_achievements([], total_days_met=5)
    consistent = next(a for a in achievements if a.id == "consistent")
    assert consistent.condition_met is True

    streak_info = gamification_service.get_streak_info()
    assert streak_info["current_streak"] == 5
    assert streak_info["total_days_met_target"] == 5


def test_gamification_data_format(gamification_service):
    """Test that get_achievements returns correct data format."""
    gamification_service.update_streak("2025-01-15", target_met=True)
    sessions = [{"start_time": "08:30:00", "duration_minutes": 300}]

    achievements = gamification_service.get_achievements(sessions)

    # Should return list of dicts
    assert isinstance(achievements, list)
    assert len(achievements) == 4  # All 4 achievements

    for ach in achievements:
        assert "id" in ach
        assert "name" in ach
        assert "description" in ach
        assert "icon" in ach
        assert "earned" in ach
        assert isinstance(ach["earned"], bool)


# --- Summary Test: All Acceptance Criteria ---

def test_all_acceptance_criteria_met(project_root, gamification_service):
    """Meta-test: Verify all Task 7.7 acceptance criteria."""

    # 1. Streak counter tracking
    gamification_service.update_streak("2025-01-15", target_met=True)
    streak_info = gamification_service.get_streak_info()
    assert "current_streak" in streak_info
    assert "longest_streak" in streak_info
    assert "total_days_met_target" in streak_info

    # 2. Achievement badges
    achievements = gamification_service.get_achievements([])
    assert len(achievements) == 4
    achievement_ids = [a["id"] for a in achievements]
    assert "early_bird" in achievement_ids
    assert "marathon_runner" in achievement_ids
    assert "consistent" in achievement_ids
    assert "dedicated" in achievement_ids

    # 3. JSON persistence (verified by file existence in fixtures)
    # 4. API endpoint
    import sys
    sys.path.insert(0, str(project_root))
    from app.main import app
    routes = [route.path for route in app.routes]
    assert "/api/gamification" in routes

    # 5. Frontend UI
    html_file = project_root / "templates" / "index.html"
    html_content = html_file.read_text()
    assert "gamification-section" in html_content
    assert "achievements-grid" in html_content

    css_file = project_root / "static" / "style.css"
    css_content = css_file.read_text()
    assert ".gamification-section" in css_content

    js_file = project_root / "static" / "app.js"
    js_content = js_file.read_text()
    assert "renderGamification" in js_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
