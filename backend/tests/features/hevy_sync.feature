# Gherkin acceptance criteria for US-008 (Hevy sync), executable via pytest-bdd.
# These scenarios are the literal acceptance criteria from SPECIFICATIONS.md.

Feature: Hevy workout synchronization
  As Frederick, I want my workouts synced from Hevy every 30 minutes
  so my data is up to date without manual entry.

  Scenario: Incremental sync (nominal)
    Given the agent is started with a valid Hevy API key
    And the last successful sync was at T-30min
    When the scheduler triggers sync_hevy_workouts
    Then the agent requests workout events since the last sync
    And each workout is upserted by hevy_id
    And last_successful_sync is updated

  Scenario: Deduplication on re-sync
    Given a workout "workout_abc123" already exists
    When a new sync returns that same workout
    Then it is updated, not duplicated

  Scenario: Hevy API unavailable
    Given the Hevy API returns a 5xx error
    When the sync job runs
    Then it retries 3 times with exponential backoff
    And last_successful_sync is NOT updated
    And an ntfy alert is sent if all retries fail
