"""All SQLAlchemy models.

Importing every model here ensures Alembic autogenerate can discover all tables
via Base.metadata. The import order respects foreign-key dependencies, though
SQLAlchemy resolves these at mapper-configuration time regardless of order.
"""

from __future__ import annotations

from .base import Base

# Group 1 — Auth & System
from .system import (
    AgentAction,
    AuthAttempt,
    LLMConfig,
    NotificationConfig,
)

# Group 2 — Workouts & Exercises
from .workouts import (
    ExerciseTemplate,
    SyncState,
    Workout,
    WorkoutExercise,
    WorkoutSet,
)

# Group 3 — Targets & Context
from .targets import (
    ExerciseTarget,
    ProgramSplit,
    TrainingContext,
)

# Group 4 — Analysis
from .analysis import (
    ExerciseAnalysis,
    MonthlyStats,
    PersonalRecord,
    WeeklyStats,
)

# Group 5 — Health
from .health import (
    HealthMarker,
    HealthMetric,
)

# Group 6 — Coaching
from .coaching import (
    Challenge,
    NutritionPlan,
    WorkoutSuggestion,
)

# Group 7 — Gamification
from .gamification import (
    Mission,
    Streak,
    UserLevel,
    XPLog,
)

# Group 8 — Memory & Chat
from .chat import (
    AgentMemory,
    Conversation,
    Message,
)

__all__ = [
    "Base",
    # Group 1
    "LLMConfig",
    "NotificationConfig",
    "AuthAttempt",
    "AgentAction",
    # Group 2
    "ExerciseTemplate",
    "Workout",
    "WorkoutExercise",
    "WorkoutSet",
    "SyncState",
    # Group 3
    "TrainingContext",
    "ExerciseTarget",
    "ProgramSplit",
    # Group 4
    "PersonalRecord",
    "ExerciseAnalysis",
    "WeeklyStats",
    "MonthlyStats",
    # Group 5
    "HealthMetric",
    "HealthMarker",
    # Group 6
    "WorkoutSuggestion",
    "NutritionPlan",
    "Challenge",
    # Group 7
    "Mission",
    "XPLog",
    "UserLevel",
    "Streak",
    # Group 8
    "AgentMemory",
    "Conversation",
    "Message",
]
