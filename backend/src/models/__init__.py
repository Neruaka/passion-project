"""All SQLAlchemy models.

Importing every model here ensures Alembic autogenerate can discover all tables
via Base.metadata. The import order respects foreign-key dependencies, though
SQLAlchemy resolves these at mapper-configuration time regardless of order.
"""

from __future__ import annotations

# Group 4 — Analysis
from .analysis import (
    ExerciseAnalysis,
    MonthlyStats,
    PersonalRecord,
    WeeklyStats,
)
from .base import Base

# Group 8 — Memory & Chat
from .chat import (
    AgentMemory,
    Conversation,
    Message,
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

# Group 5 — Health
from .health import (
    HealthMarker,
    HealthMetric,
)

# Group 1 — Auth & System
from .system import (
    AgentAction,
    AuthAttempt,
    LLMConfig,
    NotificationConfig,
)

# Group 3 — Targets & Context
from .targets import (
    ExerciseTarget,
    ProgramSplit,
    TrainingContext,
)

# Group 2 — Workouts & Exercises
from .workouts import (
    ExerciseTemplate,
    SyncState,
    Workout,
    WorkoutExercise,
    WorkoutSet,
)

__all__ = [
    "AgentAction",
    "AgentMemory",
    "AuthAttempt",
    "Base",
    "Challenge",
    "Conversation",
    "ExerciseAnalysis",
    "ExerciseTarget",
    "ExerciseTemplate",
    "HealthMarker",
    "HealthMetric",
    "LLMConfig",
    "Message",
    "Mission",
    "MonthlyStats",
    "NotificationConfig",
    "NutritionPlan",
    "PersonalRecord",
    "ProgramSplit",
    "Streak",
    "SyncState",
    "TrainingContext",
    "UserLevel",
    "WeeklyStats",
    "Workout",
    "WorkoutExercise",
    "WorkoutSet",
    "WorkoutSuggestion",
    "XPLog",
]
