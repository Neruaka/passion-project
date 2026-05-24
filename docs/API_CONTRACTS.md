# API CONTRACTS — Personal AI Operating System

> Complete REST + WebSocket API contracts for the PASSION project.
>
> **Version:** 1.0
> **Date:** May 2026
> **Base URL:** `/api/v1`
> **Auth:** JWT (cookie httpOnly or Bearer header), Tailscale-only network access

---

## CONVENTIONS

### HTTP methods
| Method | Usage |
|---|---|
| GET | Read (list or detail) |
| POST | Create or trigger action |
| PUT | Full replace |
| PATCH | Partial update |
| DELETE | Remove |

### HTTP status codes
| Code | Meaning |
|---|---|
| 200 | OK (GET, PATCH) |
| 201 | Created (POST) |
| 202 | Accepted (async job queued) |
| 204 | No Content (DELETE, logout) |
| 400 | Bad Request (invalid input) |
| 401 | Unauthorized (not authenticated) |
| 403 | Forbidden (authenticated, not authorized) |
| 404 | Not Found |
| 413 | Payload Too Large |
| 422 | Unprocessable Entity (Pydantic validation failed) |
| 429 | Too Many Requests (rate limit) |
| 500 | Internal Server Error |
| 503 | Service Unavailable (LLM down → fallback) |

### Versioning
All endpoints prefixed with `/api/v1`. Future breaking changes go to `/api/v2`.

### Authentication levels
- **public**: no auth (login only)
- **user**: requires valid JWT
- **system**: requires JWT + system unlock (2nd password)

---

## DOMAINS OVERVIEW

```
🔐 AUTH          /api/v1/auth/*           — authentication
📊 DASHBOARD     /api/v1/dashboard/*      — main dashboard data
💪 WORKOUTS      /api/v1/workouts/*       — workout history & sync
📈 ANALYSIS      /api/v1/analysis/*       — PRs, plateaus, stats, targets
🥗 NUTRITION     /api/v1/nutrition/*      — nutrition plans & suggestions
🩺 HEALTH        /api/v1/health/*         — health metrics & markers
🧠 COACH         /api/v1/coach/*          — LLM coaching
💬 CHAT          /api/v1/chat/* + /ws/chat — real-time chat
🎮 GAMIFICATION  /api/v1/gamification/*   — streaks, missions, XP
⚙️ SYSTEM         /api/v1/system/*         — admin (system password)
🔔 NOTIFICATIONS /api/v1/notifications/*  — notification config
```

---

## 🔐 AUTH

### POST /api/v1/auth/login `[public]`

**Request**
```python
class LoginRequest(BaseModel):
    password: str = Field(min_length=1, max_length=200)
```

**Response 200**
```python
class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
```

Sets httpOnly Secure SameSite=Strict cookie. Errors: 401 (wrong password), 429 (rate limit 5/15min).

### POST /api/v1/auth/logout `[user]`
Response 204. Invalidates session + clears cookie.

### GET /api/v1/auth/me `[user]`
```python
class MeResponse(BaseModel):
    authenticated: bool
    session_expires_at: datetime
    system_access_granted: bool
```

### POST /api/v1/auth/system-unlock `[user]`
```python
class SystemUnlockRequest(BaseModel):
    system_password: str = Field(min_length=1, max_length=200)

class SystemUnlockResponse(BaseModel):
    system_access_granted: bool
    expires_at: datetime  # ~1h
```
Errors: 401 (wrong), 429 (3 fails → 1h lockout).

---

## 📊 DASHBOARD

### GET /api/v1/dashboard/overview `[user]`
```python
class DashboardOverview(BaseModel):
    agent_status: AgentStatus  # idle/thinking/executing/error/sleeping
    current_cycle: int
    queue_size: int
    uptime_seconds: int
    last_action_at: datetime | None
    today_missions: list[MissionSummary]
    daily_briefing: BriefingSummary | None
    health_snapshot: HealthSnapshot
    user_level: str
    current_xp: int
    xp_to_next_level: int

class HealthSnapshot(BaseModel):
    sleep_hours_last_night: float | None
    resting_hr: int | None
    hrv_rmssd: float | None
    hrv_delta_7d: float | None
    steps_today: int
    neat_kcal_today: int | None
```

### GET /api/v1/dashboard/system-matrix `[user]`
```python
class SystemMatrix(BaseModel):
    systems: list[SystemStatus]

class SystemStatus(BaseModel):
    code: str          # "FIT", "COD", etc.
    name: str
    status: Literal["online", "offline", "degraded"]
    detail: str
    last_activity_at: datetime | None
```

---

## 💪 WORKOUTS

### GET /api/v1/workouts `[user]`
Query: `page`, `page_size` (max 100), `from_date`, `to_date`, `muscle_group`, `exercise`.
```python
class WorkoutListResponse(BaseModel):
    items: list[WorkoutSummary]
    total: int
    page: int
    page_size: int
    has_next: bool

class WorkoutSummary(BaseModel):
    id: UUID
    hevy_id: str
    title: str
    start_time: datetime
    duration_minutes: int
    exercise_count: int
    total_volume_kg: float
    has_prs: bool
```

### GET /api/v1/workouts/{workout_id} `[user]`
```python
class WorkoutDetail(BaseModel):
    id: UUID
    hevy_id: str
    title: str
    description: str | None
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    notes: str | None
    exercises: list[ExerciseDetail]
    total_volume_kg: float

class ExerciseDetail(BaseModel):
    title: str
    exercise_template_id: str
    order_index: int
    notes: str | None
    primary_muscle_group: str
    secondary_muscle_groups: list[str]
    sets: list[SetDetail]

class SetDetail(BaseModel):
    order_index: int
    set_type: Literal["warmup", "normal", "failure", "dropset"]
    weight_kg: float | None
    reps: int | None
    rpe: float | None
    is_pr: bool
    pr_type: str | None
```
Errors: 404 (not found).

### POST /api/v1/workouts/sync `[user]`
Triggers on-demand sync. Response 202:
```python
class SyncTriggeredResponse(BaseModel):
    job_id: str
    status: Literal["queued"]
    message: str
```
Errors: 429 (sync < 30s ago). Real status via WebSocket.

---

## 📈 ANALYSIS

### GET /api/v1/analysis/prs `[user]`
Query: `page`, `page_size`, `pr_type`, `exercise`, `from_date`, `to_date`.
```python
class PRRecord(BaseModel):
    id: UUID
    exercise_title: str
    pr_type: Literal["one_rep_max", "reps_at_load", "session_volume", "muscle_group_volume"]
    new_value: float
    old_value: float | None
    gain: float
    bucket: str | None
    achieved_at: datetime
    workout_id: UUID
```

**Example response**
```json
{
  "items": [{
    "id": "a3f1c8e2-...",
    "exercise_title": "Bench Press (Barbell)",
    "pr_type": "one_rep_max",
    "new_value": 84.0, "old_value": 80.5, "gain": 3.5,
    "bucket": null,
    "achieved_at": "2026-05-19T08:14:00Z",
    "workout_id": "b4e2d9f3-..."
  }],
  "total": 1
}
```

### GET /api/v1/analysis/plateaus `[user]`
```python
class PlateauAnalysis(BaseModel):
    id: UUID
    exercise_title: str
    analysis_type: Literal["plateau_official", "plateau_stalled", "regression", "behind_schedule"]
    severity: Literal["minor", "moderate", "major"] | None
    details: dict
    status: Literal["active", "resolved"]
    created_at: datetime
```

### GET /api/v1/analysis/targets `[user]`
```python
class TargetProgress(BaseModel):
    id: UUID
    exercise_title: str
    workout_day: str
    baseline: TargetPoint
    current: TargetPoint
    target: TargetRange
    progress_pct: float
    weeks_elapsed: int
    weeks_estimated_max: int
    status: Literal["on_track", "behind_schedule", "ahead_of_schedule", "achieved", "expired"]

class TargetPoint(BaseModel):
    weight_kg: float | None
    reps: int | None
    one_rm_estimate: float | None

class TargetRange(BaseModel):
    weight_kg_min: float | None
    weight_kg_max: float | None
    reps: int | None
    one_rm_estimate: float | None
```

### GET /api/v1/analysis/muscle-status `[user]`
```python
class MuscleStatus(BaseModel):
    muscle_group: str
    recovery_state: Literal["ready", "recovering", "heavy_fatigue", "neglected"]
    days_since_last_trained: float
    recovery_left_days: float
    volume_last_7d: float
    frequency_last_30d: int
    flag: Literal["normal", "neglected", "high_load"] | None
```

### GET /api/v1/analysis/stats `[user]`
Query: `period=week|month`, `ref_date`.
```python
class StatsResponse(BaseModel):
    period: Literal["week", "month"]
    period_start: date
    period_end: date
    total_sessions: int
    session_target: int
    total_duration_minutes: int
    total_volume_kg: float
    pr_count: int
    volume_by_muscle: dict[str, float]
    sessions_by_day: dict[str, int]
    deltas: StatsDeltas
    top_exercises: list[TopExercise]

class StatsDeltas(BaseModel):
    volume_pct: float
    sessions_diff: int
    pr_diff: int
```

### GET /api/v1/analysis/exercise/{exercise_id}/progression `[user]`
```python
class ProgressionResponse(BaseModel):
    exercise_title: str
    data_points: list[ProgressionPoint]
    target_zone: TargetRange
    expected_trajectory: list[TrajectoryPoint]
    plateaus: list[dict]
    prs: list[dict]

class ProgressionPoint(BaseModel):
    date: date
    one_rm_estimate: float
    volume_kg: float

class TrajectoryPoint(BaseModel):
    date: date
    expected_1rm: float
    expected_1rm_adjusted: float
```

---

## 🥗 NUTRITION

### GET /api/v1/nutrition/today `[user]`
```python
class NutritionTodayResponse(BaseModel):
    plan: NutritionPlan
    logged: NutritionLogged
    remaining: NutritionRemaining

class NutritionPlan(BaseModel):
    is_training_day: bool
    daily_kcal_target: int
    daily_protein_target_g: int
    daily_carbs_target_g: int
    daily_fats_target_g: int
    hydration_target_l: float
    timing_strategy: str
    meal_distribution: list[MealSlot]
    supplements_today: list[SupplementSlot]

class NutritionLogged(BaseModel):
    kcal_consumed: int
    protein_g: float
    carbs_g: float
    fats_g: float
    hydration_l: float
    meals_logged_count: int
    last_sync_at: datetime

class NutritionRemaining(BaseModel):
    kcal_remaining: int
    protein_g_remaining: float
    compliance_pct: float
```

### POST /api/v1/nutrition/suggest-meal `[user]`
```python
class SuggestMealRequest(BaseModel):
    context: Literal["next_meal", "post_workout", "snack"] = "next_meal"

class MealSuggestion(BaseModel):
    title: str
    type: Literal["quick", "batch_cook", "restaurant"]
    kcal: int
    protein_g: float
    carbs_g: float
    fats_g: float
    ingredients: list[str]
    prep_minutes: int | None
    rationale: str
```

---

## 🩺 HEALTH

### POST /api/v1/health/ingest `[ingest-token]`
Called by Tasker. Header: `X-Ingest-Token`.
```python
class HealthIngestRequest(BaseModel):
    device: str
    captured_at: datetime
    window_start: datetime
    window_end: datetime
    records: list[HealthRecord]

class HealthRecord(BaseModel):
    source_record_id: str
    metric_type: str
    recorded_at: datetime
    duration_seconds: int | None
    numeric_value: float | None
    unit: str | None
    metadata: dict | None

class HealthIngestResponse(BaseModel):
    count_records: int
    count_new: int
    count_skipped: int
    duration_ms: int
```
Errors: 400 (schema), 401 (token), 413 (>5MB).

### GET /api/v1/health/today `[user]`
```python
class HealthTodayResponse(BaseModel):
    date: date
    sleep: SleepSummary | None
    resting_hr: int | None
    hrv_rmssd: float | None
    hrv_delta_7d: float | None
    steps: int
    neat_kcal: int | None
    statuses: dict[str, Literal["green", "yellow", "red"]]
    data_freshness: DataFreshness

class SleepSummary(BaseModel):
    total_hours: float
    deep_hours: float | None
    rem_hours: float | None
    light_hours: float | None
    quality_score: int | None

class DataFreshness(BaseModel):
    last_sync_at: datetime | None
    is_stale: bool
    missing_days: list[date]
```

### GET /api/v1/health/trends `[user]`
Query: `metric`, `period=7d|30d|90d`.
```python
class HealthTrendsResponse(BaseModel):
    metric: str
    period: str
    data_points: list[TrendPoint]
    target_min: float | None
    target_max: float | None

class TrendPoint(BaseModel):
    date: date
    value: float | None
```

### POST /api/v1/health/markers `[user]`
```python
class HealthMarkerRequest(BaseModel):
    measurement_date: date
    measurement_type: Literal["blood_panel", "body_composition", "other"]
    source: str | None
    fasting_state: bool | None
    values: dict[str, float]
    notes: str | None

class NormalizedMarker(BaseModel):
    metric_key: str
    value: float
    unit: str
    status: Literal["low", "normal", "high", "out_of_range"]
    ref_range_low: float | None
    ref_range_high: float | None
```

---

## 🧠 COACH

### POST /api/v1/coach/suggest-workout `[user]`
```python
class SuggestWorkoutRequest(BaseModel):
    constraints: WorkoutConstraints | None = None

class WorkoutConstraints(BaseModel):
    time_available_minutes: int | None
    injury_flags: list[str] | None
    force_workout_type: str | None

class SuggestWorkoutResponse(BaseModel):
    id: UUID
    recommendation: str
    reasoning: str
    workout_type: str
    exercises: list[SuggestedExercise]
    expected_duration_min: int
    warnings: list[str]
    alternative_if_tired: str | None
    generated_at: datetime

class SuggestedExercise(BaseModel):
    name: str
    sets: int
    reps_range: str
    weight_suggestion_kg: float | None
    notes: str | None
```
Errors: 402/503 (budget exhausted → fallback template).

### POST /api/v1/coach/suggestion/{id}/respond `[user]`
```python
class SuggestionResponseRequest(BaseModel):
    action: Literal["accept", "modify", "reject"]
    modifications: dict | None = None
    reject_reason: str | None = None

class SuggestionResponseResult(BaseModel):
    status: str
    new_suggestion: SuggestWorkoutResponse | None
```

### POST /api/v1/coach/nutrition-plan `[user]`
Regenerates today's nutrition plan. Returns `NutritionPlan`.

---

## 💬 CHAT

### GET /api/v1/chat/conversations `[user]`
```python
class ConversationSummary(BaseModel):
    id: UUID
    type: Literal["direct_line", "coach_fitness"]
    started_at: datetime
    last_message_at: datetime
    message_count: int
    preview: str
```

### GET /api/v1/chat/conversations/{id}/messages `[user]`
```python
class ChatMessage(BaseModel):
    id: UUID
    role: Literal["user", "assistant", "system"]
    content: str
    created_at: datetime
```

### POST /api/v1/chat/conversations `[user]`
```python
class CreateConversationRequest(BaseModel):
    type: Literal["direct_line", "coach_fitness"]

class CreateConversationResponse(BaseModel):
    id: UUID
    type: str
    started_at: datetime
```

### WS /ws/chat `[user]`
Query: `conversation_id`, `token`.

**Client → Server**
```python
class WSUserMessage(BaseModel):
    type: Literal["user_message"]
    content: str

class WSStopGeneration(BaseModel):
    type: Literal["stop_generation"]

class WSQuickAction(BaseModel):
    type: Literal["quick_action"]
    action: str
```

**Server → Client**
```python
class WSThinking(BaseModel):
    type: Literal["thinking"]

class WSTokenChunk(BaseModel):
    type: Literal["token"]
    content: str

class WSMessageComplete(BaseModel):
    type: Literal["message_complete"]
    message_id: UUID
    full_content: str
    quick_actions: list[QuickActionButton]

class WSError(BaseModel):
    type: Literal["error"]
    message: str
    recoverable: bool

class QuickActionButton(BaseModel):
    label: str
    action: str
```

**Example WebSocket session**
```json
// client → server
{"type": "user_message", "content": "j'ai mal dormi, je m'entraine quand meme ?"}

// server → client (streaming)
{"type": "thinking"}
{"type": "token", "content": "Hey,"}
{"type": "token", "content": " ok donc..."}
{"type": "message_complete", "message_id": "...", "full_content": "...", "quick_actions": [{"label": "Voir le workout allégé", "action": "show_today_workout"}]}
```

---

## 🎮 GAMIFICATION

### GET /api/v1/gamification/streaks `[user]`
```python
class StreaksResponse(BaseModel):
    workout: StreakDetail
    nutrition: StreakDetail
    sleep: StreakDetail

class StreakDetail(BaseModel):
    current: int
    best: int
    frozen_until: date | None
    freezes_remaining_this_month: int
```

### POST /api/v1/gamification/streaks/{type}/freeze `[user]`
```python
class FreezeStreakRequest(BaseModel):
    days: int = Field(ge=1, le=7)

class FreezeStreakResponse(BaseModel):
    frozen_until: date
    freezes_remaining_this_month: int
```

### GET /api/v1/gamification/missions `[user]`
```python
class MissionDetail(BaseModel):
    id: UUID
    title: str
    description: str
    mission_type: str
    xp_reward: int
    status: Literal["pending", "in_progress", "completed", "failed", "expired"]
    completed_at: datetime | None
```

### GET /api/v1/gamification/challenges `[user]`
```python
class ChallengeDetail(BaseModel):
    id: UUID
    title: str
    description: str
    challenge_type: str
    xp_reward: int
    status: Literal["active", "completed", "failed", "expired"]
    progress: dict
    deadline: datetime
```

### GET /api/v1/gamification/level `[user]`
```python
class LevelResponse(BaseModel):
    current_level: str
    current_xp: int
    xp_to_next_level: int
    next_level: str
    progress_pct: float
    total_xp_earned: int
```

---

## ⚙️ SYSTEM `[system]`

All require `system_access_granted=true`.

### GET /api/v1/system/llm-config
```python
class LLMConfigResponse(BaseModel):
    navichat_model: str
    daily_call_budget: int
    daily_cost_budget_eur: float
    routing_enabled: bool
    usage_today: LLMUsageToday

class LLMUsageToday(BaseModel):
    total_calls: int
    total_cost_eur: float
    pct_of_budget: float
    by_model: dict[str, int]
    by_agent: dict[str, float]
```

### PATCH /api/v1/system/llm-config
```python
class LLMConfigUpdate(BaseModel):
    navichat_model: str | None = None
    daily_call_budget: int | None = None
    daily_cost_budget_eur: float | None = None
```

### GET /api/v1/system/memory
Query: `page`, `page_size`, `tag`, `type`.
```python
class MemoryEntry(BaseModel):
    id: UUID
    content: str
    tags: list[str]
    source: Literal["explicit", "implicit", "manual"]
    created_at: datetime
    is_obsolete: bool
```

### DELETE /api/v1/system/memory/{id}
Response 204.

### GET /api/v1/system/activity-log
Query: `page`, `page_size`, `agent`, `action_type`, `status`, `from_date`, `to_date`.
```python
class ActivityEntry(BaseModel):
    id: UUID
    agent_name: str
    action_type: str
    status: Literal["success", "error", "partial"]
    tokens_used: int | None
    cost_eur: float | None
    duration_ms: int
    created_at: datetime
```

### GET /api/v1/system/activity-log/{id}
```python
class ActivityDetail(ActivityEntry):
    input: dict
    output: dict
    prompt_sent: str | None
    llm_response_raw: str | None
    error_message: str | None
```

---

## 🔔 NOTIFICATIONS

### GET /api/v1/notifications/config `[user]`
```python
class NotificationConfigResponse(BaseModel):
    email_enabled: bool
    push_enabled: bool
    briefing_hour: str
    recipient_email: str
```

### PATCH /api/v1/notifications/config `[user]`
```python
class NotificationConfigUpdate(BaseModel):
    email_enabled: bool | None = None
    push_enabled: bool | None = None
    briefing_hour: str | None = None
```

### POST /api/v1/notifications/test `[user]`
```python
class TestNotificationRequest(BaseModel):
    channel: Literal["email", "push", "both"]

class TestNotificationResponse(BaseModel):
    sent: bool
    channels_reached: list[str]
```

---

## ENDPOINT SUMMARY

```
AUTH          : 4 endpoints
DASHBOARD     : 2 endpoints
WORKOUTS      : 3 endpoints
ANALYSIS      : 6 endpoints
NUTRITION     : 2 endpoints
HEALTH        : 4 endpoints
COACH         : 3 endpoints
CHAT          : 3 REST + 1 WebSocket
GAMIFICATION  : 5 endpoints
SYSTEM        : 6 endpoints
NOTIFICATIONS : 3 endpoints
─────────────────────────────
TOTAL         : ~41 REST endpoints + 1 WebSocket
```

---

*Document generated May 2026 — Frederick × Claude*
*Version 1.0 — All API contracts defined, ready for DB schema finalization*
