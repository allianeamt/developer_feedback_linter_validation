import sys
import os
import random
import copy
from collections import defaultdict
import requests
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.logger import log
from utils.yaml_utils import load_yaml, save_to_file, add_to_file
from utils.usage import extract_repo
from modules.associate_forms import associate_forms

CHECK_ID_TO_NAME = {
    "CKV_AWS_801": "DynamoDB On-Demand Billing",
    "CKV_AWS_802": "DynamoDB Overprovisioned r/w Capacity",
    "CKV_AWS_803": "DynamoDB GSIs",
    "CKV_AWS_804": "Deprecated Instance/Volume Types",
    "CKV2_AWS_61": "S3 Lifecycle Configurations",
    "CKV_AWS_805": "S3 Lifecycle Configurations",
    "CKV_AWS_806": "DynamoDB On-Demand Billing",
    "CKV_AWS_807": "Deprecated Instance/Volume Types",
}

CHECK_ID_TO_DESCRIPTION = {
    "CKV_AWS_801": "Detects DynamoDB tables that do not use PAY_PER_REQUEST (on-demand) billing. This can lead to over-provisioning, unnecessary costs, or throttling if usage exceeds limits.",
    "CKV_AWS_802": "Detects DynamoDB tables that use provisioned capacity (read_capacity/write_capacity > 1). Provisioned settings can cause higher costs if not properly tuned.",
    "CKV_AWS_803": "Flags DynamoDB tables that define Global Secondary Indexes (GSIs). GSIs add unnecessary costs and complexity if not carefully optimized.",
    "CKV_AWS_804": "Detects use of outdated EC2 instance or EBS volume types (e.g., t2, m4, gp2). Older generations might be less efficient, slower, and more expensive.",
    "CKV2_AWS_61": "Verifies that aws_s3_bucket resources have lifecycle configurations defined via lifecycle_rules or as a linked aws_s3_bucket_lifecycle_configuration. Missing rules may lead to data retention in expensive storage indefinitely, thus increasing costs.",
    "CKV_AWS_805": "Verifies that S3 buckets have lifecycle configurations with at least one rule defined. Missing rules may lead to data retention in expensive storage indefinitely, thus increasing costs.",
    "CKV_AWS_806": "Detects DynamoDB tables that do not use PAY_PER_REQUEST (on-demand) billing. This can lead to over-provisioning, unnecessary costs, or throttling if usage exceeds limits.",
    "CKV_AWS_807": "Detects use of outdated types (e.g., t2, m3, m4, c4) for EC2, RDS and SageMaker instances. Older generations might be less efficient, slower, and more expensive.",
}

LOGS_FILE = "logs.txt"

def check_duplicates():
    baseline_tf = load_yaml("../results/baseline_tf/checkov/results.yml")
    baseline_tf_repos = extract_repo(baseline_tf)

    baseline_cf = load_yaml("../results/baseline_cf/checkov/results.yml")
    baseline_cf_repos = extract_repo(baseline_cf)

    extended_tf = load_yaml("../results/extended_tf/checkov/results.yml")
    extended_tf_repos = extract_repo(extended_tf)

    extended_cf = load_yaml("../results/extended_cf/checkov/results.yml")
    extended_cf_repos = extract_repo(extended_cf)

    all_datasets = baseline_tf_repos + baseline_cf_repos + extended_tf_repos + extended_cf_repos
    unique_datasets = set()

    duplicates = set()
    for dataset in all_datasets:
        if dataset in unique_datasets:
            duplicates.add(dataset)
        else:
            unique_datasets.add(dataset)
    if duplicates:
        log("Duplicates found:", LOGS_FILE)
        for dup in duplicates:
            log(f"\t{dup}", LOGS_FILE)
            # Find out which datasets the duplicate appears in
            sources = []
            if dup in baseline_tf_repos:
                sources.append("baseline_tf")
            if dup in baseline_cf_repos:    
                sources.append("baseline_cf")
            if dup in extended_tf_repos:
                sources.append("extended_tf")
            if dup in extended_cf_repos:
                sources.append("extended_cf")
            log(f"\t\tAppears in: {', '.join(sources)}", LOGS_FILE)

            # remove the duplicate from the extended datasets
            if dup in extended_tf_repos:
                # remove the first entry with that ['repo'] from the extended_tf dataset
                for i, entry in enumerate(extended_tf):
                    if entry['repo'] == dup:
                        extended_tf.pop(i)
                        break

            if dup in extended_cf_repos:
                # remove the first entry with that ['repo'] from the extended_cf dataset
                for i, entry in enumerate(extended_cf):
                    if entry['repo'] == dup:
                        extended_cf.pop(i)
                        break            

        log("Duplicates removed from extended datasets.", LOGS_FILE)
        save_to_file(baseline_tf, "raw_data/baseline_tf.yml")
        save_to_file(baseline_cf, "raw_data/baseline_cf.yml")
        save_to_file(extended_tf, "raw_data/extended_tf.yml")
        save_to_file(extended_cf, "raw_data/extended_cf.yml")

    else:
        log("No duplicates found across datasets.", LOGS_FILE)

def clean_data(data, tool, dataset, keywords_dataset):
    cleaned_data = []
    aware_repos = {entry["repo"] for entry in keywords_dataset}

    for entry in data:
        failed_checks = entry.get("checks", {}).get("failed_checks", [])
        if not failed_checks:
            continue

        for check in failed_checks:
            check_id = check.get("check_id")
            check["check_name"] = CHECK_ID_TO_NAME.get(check_id, "Unknown Check")

        failed_checks_count = len(failed_checks)
        unique_files = set(check.get("file_path") for check in failed_checks if "file_path" in check)
        unique_files_count = len(unique_files)

        preferred_checks = [check for check in failed_checks if check["check_id"] in {"CKV_AWS_801", "CKV_AWS_806"}]
        example_check = random.choice(preferred_checks if preferred_checks else failed_checks)
        example_check_decopy = copy.deepcopy(example_check)

        example_check_decopy["check_description"] = CHECK_ID_TO_DESCRIPTION.get(example_check["check_id"], "No description available")

        repo_url = entry.get("repo")
        cost_awareness = "aware" if repo_url in aware_repos else "unaware"

        cleaned_entry = {
            "repo": entry.get("repo"),
            "tool": tool,
            "dataset": dataset,
            "failed_checks": failed_checks,
            "failed_checks_count": failed_checks_count,
            "files_count": unique_files_count,
            "example_check": example_check_decopy,
            "cost_awareness": cost_awareness,
        }

        cleaned_data.append(cleaned_entry)

    return cleaned_data

def clean_datasets():
    log("Cleaning datasets...", LOGS_FILE)

    baseline_tf = load_yaml("raw_data/baseline_tf.yml")
    baseline_cf = load_yaml("raw_data/baseline_cf.yml")
    extended_tf = load_yaml("raw_data/extended_tf.yml")
    extended_cf = load_yaml("raw_data/extended_cf.yml")

    keywords_baseline_tf = load_yaml("../results/baseline_tf/activity/keywords_12m/keywords_repos.yml")
    keywords_baseline_cf = load_yaml("../results/baseline_cf/activity/keywords_12m/keywords_repos.yml")
    keywords_extended_tf = load_yaml("../results/extended_tf/activity/keywords_12m/keywords_repos.yml")
    keywords_extended_cf = load_yaml("../results/extended_cf/activity/keywords_12m/keywords_repos.yml")

    cleaned_baseline_tf = clean_data(baseline_tf, "terraform", "baseline", keywords_baseline_tf)
    cleaned_baseline_cf = clean_data(baseline_cf, "cloudformation", "baseline", keywords_baseline_cf)
    cleaned_extended_tf = clean_data(extended_tf, "terraform", "extended", keywords_extended_tf)
    cleaned_extended_cf = clean_data(extended_cf, "cloudformation", "extended", keywords_extended_cf)

    save_to_file(cleaned_baseline_tf, "data/cleaned_baseline_tf.yml")
    save_to_file(cleaned_baseline_cf, "data/cleaned_baseline_cf.yml")
    save_to_file(cleaned_extended_tf, "data/cleaned_extended_tf.yml")
    save_to_file(cleaned_extended_cf, "data/cleaned_extended_cf.yml")

    # combine all cleaned datasets into one
    combined_cleaned_data = cleaned_baseline_tf + cleaned_baseline_cf + cleaned_extended_tf + cleaned_extended_cf
    save_to_file(combined_cleaned_data, "data/combined_data.yml")