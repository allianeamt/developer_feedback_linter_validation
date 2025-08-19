import os
import sys
import re

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.logger import log

FORM_LINKS = {
    "61": "https://forms.gle/fbABPxtqeirbcQ8F8",
    "61_804": "https://forms.gle/J5b8wJyYwJb83ZuH9",
    "805": "https://forms.gle/LoLAimD3gZhBdEC58",
    "807": "https://forms.gle/6gXNCmRDy8SeA5b48",
    "805_807": "https://forms.gle/FUGYfN2QK4rV8cGv7",
    "61_801_803_804": "https://forms.gle/KXtXmKRJL43yMVDV6",
    "61_801_802": "https://forms.gle/9Xsv15EPdWmE8Sb88",
    "61_801_802_803_804": "https://forms.gle/MpX2wwJmneJC1r519",
    "803": "https://forms.gle/KW2Str5yYF1mthrX9",
    "61_801_803": "https://forms.gle/Fk6DAuKhkCNq1SAw9",
    "61_801_802_803": "https://forms.gle/DGoaAQMtjDPCuir38",
    "61_801_802_804": "https://forms.gle/2sCReoQ4PQ4pGEd69",
    "805_806": "https://forms.gle/VwzA2JHcn3iDJeAw6",
    "805_806_807": "https://forms.gle/WNqfyKohGbtPsHhB7",
    "806": "https://forms.gle/SaqbendkYcZZvJhs8",
    "801": "https://forms.gle/5AGovnZJWXanMEdR9",
    "801_802": "https://forms.gle/VhsjYGBiQPCjyp219",
    "61_801": "https://forms.gle/7NBiM3bJxCZEjxE29"
}

def associate_forms(data):
    for entry in data:
        check_ids = set()
        for check in entry.get("failed_checks", []):
            check_id = check.get("check_id", "")
            if check_id:
                match = re.search(r'(\d+)$', check_id)
                if match:
                    check_ids.add(match.group(1))

        sorted_check_ids = sorted(check_ids, key=lambda x: int(x))
        key = "_".join(sorted_check_ids)

        if key in FORM_LINKS:
            form_link = FORM_LINKS[key]
            entry["form_link"] = form_link
        else:
            entry["form_link"] = None
            log(f"Form link not found for key: {key}", "logs.txt")
