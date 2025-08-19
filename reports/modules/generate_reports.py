import os
import sys
import zipfile
import re
from urllib.parse import urlparse

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(root_dir)
from utils.logger import log
from utils.yaml_utils import load_yaml, save_to_file, add_to_file


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

CHECK_TO_RECOMMENDATIONS = {
    "CKV_AWS_801": [
        "Set billing_mode=PAY_PER_REQUEST in your DynamoDB table configuration.",
        "Avoid setting read_capacity and write_capacity."
    ],
    "CKV_AWS_802": [
        "Remove read_capacity and write_capacity.",
        "Set billing_mode=PAY_PER_REQUEST in your DynamoDB table configuration."
    ],
    "CKV_AWS_803": [
        "Avoid using GSIs unless absolutely necessary for query performance."
    ],
    "CKV_AWS_804": [
        "Use newer instance types (e.g., t3, m5).",
        "Use newer volume types (e.g., gp3, io2).",
        "Review AWS documentation for the latest instance and volume types."
    ],
    "CKV2_AWS_61": [
        "Add a lifecycle_rule block inside the S3 bucket for a compact definition of simple rules.",
        "Link the S3 bucket to a separate aws_s3_bucket_lifecycle_configuration resource for complex or interdependent rules."
    ],
    "CKV_AWS_805": [
        "Define LifecycleConfiguration in the Properties section of the bucket.",
        "Include a non-empty Rules list with expiration/transition logic."
    ],
    "CKV_AWS_806": [
        "Set BillingMode:PAY_PER_REQUEST in your DynamoDB table configuration.",
        "Avoid setting the read/write capacity."
    ],
    "CKV_AWS_807": [
        "Use newer types (e.g., t3, m5).",
        "Review AWS documentation for the latest instance and volume types."
    ],
}


def sanitize_repo_url(repo_url):
    return re.sub(r'[:/\\]+', '_', repo_url)

def generate_report(repo, file='../data/combined_data.yml', output_dir='../generated_reports'):
    data = load_yaml(file)
    entry = next((item for item in data if item.get('repo') == repo), None)
    if not entry:
        log(f"Repository {repo} not found in data.", "../generated_reports/logs.txt")
        return
    
    repo_folder_name = sanitize_repo_url(repo)
    output_path = os.path.join(output_dir, repo_folder_name)

    if os.path.exists(output_path):
        log(f"Output directory {output_path} already exists.", "../generated_reports/logs.txt")
        return
    os.makedirs(output_path, exist_ok=True)

    linter_report_data = {
        'linter_report': [
            {
                'repo': entry['repo'],
                'failed_checks': entry['failed_checks'],
                'failed_checks_count': entry['failed_checks_count'],
                'files_count': entry['files_count'],
            }
        ]
    }

    linter_report_path = os.path.join(output_path, 'linter_report.yml')
    save_to_file(linter_report_data, linter_report_path)

    unique_check_ids = {check['check_id'] for check in entry['failed_checks']}
    check_definitions_list = []

    for check_id in unique_check_ids:
        check_name = CHECK_ID_TO_NAME.get(check_id, "Unknown Check Name")
        description = CHECK_ID_TO_DESCRIPTION.get(check_id, "No description available.")
        recommendations = CHECK_TO_RECOMMENDATIONS.get(check_id, ["Review and remediate according to your organization’s best practices."])

        check_definitions_list.append({
            'check_id': check_id,
            'check_name': check_name,
            'description': description,
            'recommendations': recommendations
        })

    check_definitions_data = {'check_definitions': check_definitions_list}
    check_definitions_path = os.path.join(output_path, 'check_definitions.yml')
    save_to_file(check_definitions_data, check_definitions_path)

    zip_path = os.path.join(output_path, 'report.zip')
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        zipf.write(linter_report_path, arcname='linter_report.yml')
        zipf.write(check_definitions_path, arcname='check_definitions.yml')

    # save the repo URL and the form_link in info.txt
    info_path = os.path.join(output_path, 'info.txt')
    with open(info_path, 'w') as info_file:
        info_file.write(f"Repository: {repo}\n")
        info_file.write(f"Form Link: {entry.get('form_link', 'No form link available')}\n")

if __name__ == "__main__":
    if sys.argv[1:]:
        repo = sys.argv[1]
        generate_report(repo)