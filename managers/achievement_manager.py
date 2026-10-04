"""Achievement definitions and persistence-backed unlock tracking."""

ACHIEVEMENTS = (
    {
        "key": "first_contact",
        "title": "First Contact",
        "description": "Defeat your first enemy.",
        "metric": "enemies_killed",
        "target": 1,
    },
    {
        "key": "boss_breaker",
        "title": "Boss Breaker",
        "description": "Defeat your first boss.",
        "metric": "bosses_defeated",
        "target": 1,
    },
    {
        "key": "four_of_a_kind",
        "title": "Four of a Kind",
        "description": "Defeat all four boss designs.",
        "metric": "boss_types",
        "target": 4,
    },
    {
        "key": "unstoppable",
        "title": "Unstoppable",
        "description": "Reach wave 10.",
        "metric": "highest_level",
        "target": 10,
    },
    {
        "key": "sharpshooter",
        "title": "Sharpshooter",
        "description": "Finish a run with at least 80% accuracy after 20 shots.",
        "metric": "best_accuracy",
        "target": 80,
    },
    {
        "key": "bulletstorm",
        "title": "Bulletstorm",
        "description": "Fire 500 shots across all runs.",
        "metric": "shots_fired",
        "target": 500,
    },
    {
        "key": "clean_sweep",
        "title": "Clean Sweep",
        "description": "Clear an enemy wave without taking damage.",
        "metric": "clean_waves",
        "target": 1,
    },
    {
        "key": "boss_hunter",
        "title": "Boss Hunter",
        "description": "Defeat five bosses.",
        "metric": "bosses_defeated",
        "target": 5,
    },
    {
        "key": "fully_loaded",
        "title": "Fully Loaded",
        "description": "Collect all five power-up types in one run.",
        "metric": "best_run_powerup_types",
        "target": 5,
    },
    {
        "key": "lifesaver",
        "title": "Lifesaver",
        "description": "Collect a heart power-up.",
        "metric": "heart_powerups",
        "target": 1,
    },
    {
        "key": "power_surge",
        "title": "Power Surge",
        "description": "Collect ten power-ups across all runs.",
        "metric": "powerups_collected",
        "target": 10,
    },
    {
        "key": "veteran_pilot",
        "title": "Veteran Pilot",
        "description": "Complete ten runs.",
        "metric": "games_played",
        "target": 10,
    },
    {
        "key": "score_legend",
        "title": "Score Legend",
        "description": "Earn 100,000 points across all runs.",
        "metric": "score_earned",
        "target": 100_000,
    },
    {
        "key": "invasion_eraser",
        "title": "Invasion Eraser",
        "description": "Defeat 1,000 enemies across all runs.",
        "metric": "enemies_killed",
        "target": 1_000,
    },
    {
        "key": "combo_master",
        "title": "Combo Master",
        "description": "Reach a 25-hit combo in a run.",
        "metric": "best_combo",
        "target": 25,
    },
    {
        "key": "untouchable",
        "title": "Untouchable",
        "description": "Defeat a boss without taking damage during its fight.",
        "metric": "bosses_defeated_without_damage",
        "target": 1,
    },
    {
        "key": "cache_collector",
        "title": "Cache Collector",
        "description": "Collect 50 power-ups across all runs.",
        "metric": "powerups_collected",
        "target": 50,
    },
    {
        "key": "titan_slayer",
        "title": "Titan Slayer",
        "description": "Defeat ten bosses.",
        "metric": "bosses_defeated",
        "target": 10,
    },
    {
        "key": "true_aim",
        "title": "True Aim",
        "description": "Finish a run with at least 95% accuracy after 100 shots.",
        "metric": "best_accuracy",
        "target": 95,
    },
)


class AchievementManager:
    """Record player milestones and return newly unlocked achievements."""

    def __init__(self, db, player_id):
        self.db = db
        self.player_id = player_id
        self.run_powerup_types = set()
        self.best_combo = 0

    def _unlocked(self, key):
        if not self.db or not self.db.connected or not self.player_id:
            return []
        definition = next(item for item in ACHIEVEMENTS if item["key"] == key)
        if self.db.unlock_achievement(self.player_id, key):
            return [definition]
        return []

    def _check_progress(self, metric, progress):
        unlocked = []
        for achievement in ACHIEVEMENTS:
            if achievement["metric"] == metric and progress >= achievement["target"]:
                unlocked.extend(self._unlocked(achievement["key"]))
        return unlocked

    def seed_existing_stats(self, stats):
        """Backfill lifetime milestones from player totals that predate achievements."""
        unlocked = []
        seeded_metrics = {
            "games_played": stats.get("total_games_played", 0),
            "score_earned": stats.get("total_score", 0),
            "enemies_killed": stats.get("total_enemies_killed", 0),
            "powerups_collected": stats.get("total_powerups_collected", 0),
        }
        for metric, value in seeded_metrics.items():
            progress = self.db.set_achievement_progress(self.player_id, metric, value)
            if progress is not None:
                unlocked.extend(self._check_progress(metric, progress))
        return unlocked

    def record_progress(self, metric, amount=1):
        if not self.db or not self.db.connected or not self.player_id:
            return []
        progress = self.db.increment_achievement_progress(self.player_id, metric, amount)
        if progress is None:
            return []
        return self._check_progress(metric, progress)

    def record_boss_defeat(self, boss_number):
        unlocked = self.record_progress("bosses_defeated")
        metric = f"boss_type_{boss_number}"
        if self.db and self.db.connected and self.player_id:
            progress = self.db.set_achievement_progress(self.player_id, metric, 1)
            if progress is not None:
                boss_types = self.db.get_achievement_progress(self.player_id)
                distinct_types = sum(
                    boss_types.get(f"boss_type_{number}", 0) > 0
                    for number in range(1, 5)
                )
                unlocked.extend(self._check_progress("boss_types", distinct_types))
        return unlocked

    def record_level_reached(self, level):
        if not self.db or not self.db.connected or not self.player_id:
            return []
        progress = self.db.set_achievement_progress(self.player_id, "highest_level", level)
        if progress is None:
            return []
        return self._check_progress("highest_level", progress)

    def record_powerup_collected(self, kind):
        self.run_powerup_types.add(kind)
        unlocked = self.record_progress("powerups_collected")
        if kind == "heart":
            unlocked.extend(self.record_progress("heart_powerups"))
        if self.db and self.db.connected and self.player_id:
            progress = self.db.set_achievement_progress(
                self.player_id, "best_run_powerup_types", len(self.run_powerup_types)
            )
            if progress is not None:
                unlocked.extend(self._check_progress("best_run_powerup_types", progress))
        return unlocked

    def record_run_accuracy(self, shots_fired, shots_hit):
        if shots_fired < 20:
            return []
        if not self.db or not self.db.connected or not self.player_id:
            return []
        accuracy = int(shots_hit / shots_fired * 100)
        progress = self.db.set_achievement_progress(self.player_id, "best_accuracy", accuracy)
        if progress is None:
            return []
        return self._check_progress("best_accuracy", progress)

    def record_combo(self, combo):
        if combo <= self.best_combo or not self.db or not self.db.connected or not self.player_id:
            return []
        self.best_combo = combo
        progress = self.db.set_achievement_progress(self.player_id, "best_combo", combo)
        if progress is None:
            return []
        return self._check_progress("best_combo", progress)

    def record_boss_defeat_without_damage(self):
        return self.record_progress("bosses_defeated_without_damage")
