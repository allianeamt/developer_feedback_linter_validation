import sys
import os
import random
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.yaml_utils import load_yaml, save_to_file

def sample(data_file, save_file, size=4):
    data = load_yaml(data_file)

    # Filter only baseline + terraform/cloudformation + more than 1 failed check
    filtered = [
        entry for entry in data
        if (
            # entry['dataset'] == 'baseline' and
            entry['tool'] in ['terraform', 'cloudformation'] and
            len(entry.get('failed_checks', [])) > 1
        )
    ]

    # Create buckets by (tool, awareness)
    buckets = {
        ('terraform', 'aware'): [],
        ('terraform', 'unaware'): [],
        ('cloudformation', 'aware'): [],
        ('cloudformation', 'unaware'): [],
    }

    for entry in filtered:
        key = (entry['tool'], entry['cost_awareness'])
        if key in buckets:
            buckets[key].append(entry)

    eligible_buckets = {
        key: entries for key, entries in buckets.items() if len(entries) >= 10
    }

    if not eligible_buckets:
        print("No buckets with at least 10 entries found.")
        return
    
        # Distribute `size` samples fairly among eligible buckets
    buckets_to_sample = list(eligible_buckets.keys())
    num_buckets = len(buckets_to_sample)

    # Calculate fair base samples per bucket
    base_per_bucket = size // num_buckets
    remainder = size % num_buckets

    # Assign samples per bucket
    samples_per_bucket = {key: base_per_bucket for key in buckets_to_sample}

    # Distribute the remainder fairly
    for key in random.sample(buckets_to_sample, remainder):
        samples_per_bucket[key] += 1

    selected_sample = {}
    sampled_count = 0

    for key in buckets_to_sample:
        entries = eligible_buckets[key]
        sample_count = min(samples_per_bucket[key], len(entries))
        samples = random.sample(entries, sample_count)
        for i, entry in enumerate(samples):
            label = f"{key[0]}_{key[1]}_{i}"
            selected_sample[label] = entry
            data.remove(entry)
            sampled_count += 1

    # Remove the sample from the original data
    for entry in selected_sample.values():
        if entry in data:
            data.remove(entry)

    save_to_file(selected_sample, save_file)
    save_to_file(data, data_file)