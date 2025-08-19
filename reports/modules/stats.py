import sys
import os
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.yaml_utils import load_yaml, save_to_file

def get_awareness_stats(data):
    awareness_stats = defaultdict(lambda: {"aware": 0, "unaware": 0})

    for entry in data:
        awareness_stats[entry["tool"]][entry["cost_awareness"]] += 1

    result = []
    for tool, stats in awareness_stats.items():
        result.append({
            "tool": tool,
            "aware": stats["aware"],
            "unaware": stats["unaware"],
        })

    save_to_file(result, "../awareness_stats_tool.yml")

    # Calculate awareness stats for each dataset
    dataset_stats = defaultdict(lambda: {"aware": 0, "unaware": 0})

    for entry in data:
        key = (entry["tool"], entry["dataset"])
        dataset_stats[key][entry["cost_awareness"]] += 1
    
    result = []
    for (tool, dataset), stats in dataset_stats.items():
        result.append({
            "tool": tool,
            "dataset": dataset,
            "aware": stats["aware"],
            "unaware": stats["unaware"],
        })

    save_to_file(result, "../awareness_stats_dataset.yml")

def aggregate_totals(data):

    stats = defaultdict(lambda: {
        "total_checks": 0,
        "unique_files": 0,
        "total_repos": 0,
    })

    for entry in data:
        key = (entry["tool"], entry["dataset"])
        stats[key]["total_checks"] += entry.get("failed_checks_count", 0)
        stats[key]["unique_files"] += entry.get("files_count", 0)
        stats[key]["total_repos"] += 1

    result = []
    for (tool, dataset), values in stats.items():
        result.append({
            "tool": tool,
            "dataset": dataset,
            "total_checks": values["total_checks"],
            "unique_files": values["unique_files"],
            "total_repos": values["total_repos"],
        })

    save_to_file(result, "aggregated_totals.yml")