import logging
from enum import Enum
from collections import defaultdict
from typing import Dict, Any, List, Tuple

class Metric(str, Enum):
    """Defines the primary categories for metrics collection."""
    RESULT = "result"
    COMBAT = "combat"
    HUNT = "hunt"
    PATROL = "patrol"
    PROMOTION = "promotion"
    INJURY = "injury"
    STARCLAN = "starclan"

    def __str__(self):
        return self.value

class StatsCollector:
    """
    A generic class to collect and aggregate statistics from game simulations.
    It can track simple counts and calculate averages for various metrics.
    """
    def __init__(self):
        """Initializes the data structures for storing metrics."""
        # For aggregate_count: {primary_key: {secondary_key: count}}
        # e.g., {'result': {'ThunderClan_wins': 10}}
        self.counts: Dict[Metric, Dict[Any, int]] = defaultdict(lambda: defaultdict(int))

        # For aggregate_average: {primary_key: {secondary_key: [sum_of_values, number_of_values]}}
        # e.g., {'hunt': {'prey_caught_per_hunt': [50.0, 25]}} -> avg = 2.0
        self.averages: Dict[Metric, Dict[Any, List[float]]] = defaultdict(lambda: defaultdict(lambda: [0.0, 0]))

    def aggregate_count(self, primary_key: Metric, secondary_key: Any):
        """
        Increments a counter for a given primary and secondary key pair.

        Args:
            primary_key: The main category of the metric (e.g., Metric.PROMOTION).
            secondary_key: The specific item being counted (e.g., a ClanName or Rank).
        """
        self.counts[primary_key][secondary_key] += 1

    def aggregate_average(self, primary_key: Metric, secondary_key: Any, value: float):
        """
        Adds a value to a list for a given primary and secondary key pair,
        which will be used to calculate an average.

        Args:
            primary_key: The main category of the metric (e.g., Metric.HUNT).
            secondary_key: The specific item being measured (e.g., "prey_caught_per_hunt").
            value: The numerical value of the data point to add.
        """
        self.averages[primary_key][secondary_key][0] += value
        self.averages[primary_key][secondary_key][1] += 1

    def get_summary(self) -> str:
        """
        Generates a formatted string summarizing all collected statistics.
        """
        summary_lines = ["\n--- AGGREGATED SIMULATION STATISTICS ---"]

        # Process and format counts
        if self.counts:
            summary_lines.append("\n[Counts]")
            for primary_key, secondary_dict in sorted(self.counts.items()):
                summary_lines.append(f"  Category: {primary_key.value}")
                for secondary_key, count in sorted(secondary_dict.items()):
                    summary_lines.append(f"    - {secondary_key}: {count}")
        else:
            summary_lines.append("\n[Counts]\n  No count data collected.")

        # Process and format averages
        if self.averages:
            summary_lines.append("\n[Averages]")
            for primary_key, secondary_dict in sorted(self.averages.items()):
                summary_lines.append(f"  Category: {primary_key.value}")
                for secondary_key, (total, count) in sorted(secondary_dict.items()):
                    if count > 0:
                        average = total / count
                        summary_lines.append(f"    - {secondary_key}: {average:.2f} (from {count} data points)")
                    else:
                        summary_lines.append(f"    - {secondary_key}: No data")
        else:
            summary_lines.append("\n[Averages]\n  No average data collected.")
        
        summary_lines.append("\n--- END OF STATISTICS ---")
        return "\n".join(summary_lines)

    def log_summary(self):
        """
        Prints the formatted summary of all collected statistics to the logger.
        """
        logging.info(self.get_summary())

    def clear(self):
        """Resets all collected data."""
        self.counts.clear()
        self.averages.clear()
        logging.info("Statistics Collector has been cleared.")
