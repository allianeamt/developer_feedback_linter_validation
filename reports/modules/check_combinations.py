import sys
import os
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.yaml_utils import load_yaml, save_to_file

def get_check_combinations():
    data = load_yaml("../../results/combined_data.yml")
    unique_combos = defaultdict(lambda: {"count": 0, "repos": set()})

    for entry in data:
        repo = entry["repo"]
        checks = {check["check_id"] for check in entry.get("failed_checks", [])}

        key = tuple(sorted(checks))
        unique_combos[key]["count"] += 1
        unique_combos[key]["repos"].add(repo)

    result = []
    for checks, info in unique_combos.items():
        result.append({
            "checks": list(checks),
            "count": info["count"],
            "repos": sorted(info["repos"]),
        })

    save_to_file(result, "../check_combinations.yml")