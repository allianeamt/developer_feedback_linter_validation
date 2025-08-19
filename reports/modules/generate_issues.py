import sys
import os
import requests
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.logger import log
from utils.yaml_utils import load_yaml, add_to_file

def generate_issue_message_survey(entry):
    check = entry["example_check"]
    issues_count = entry["failed_checks_count"]
    files_count = entry["files_count"]
    check_name = check["check_name"]
    check_description = check["check_description"]
    resource = check["resource"]
    file_path = check["file_path"]
    if issues_count > 1:
        resource_file_block = f"⚙️ **Resource:** `{resource}`  \n🔎 **File:** `{file_path}`"
    else:
        resource_file_block = ""

    message = f"""
Hi there! 👋

I’m a master’s student researching **cost considerations in cloud infrastructure**. As part of this project, we ran a static analysis tool (linter) on your repository to identify potential cost-related misconfigurations.

We found **{issues_count} potential issue{'s' if issues_count != 1 else ''}** across **{files_count} file{'s' if files_count != 1 else ''}**. Here’s an example:

✔️ **Issue:** {check_name}  
📃 **Description:** {check_description}  
{resource_file_block}

Are you interested in **more linter results**? Reply here. We’ll send **the report along with a short follow-up survey** (~5 min) to evaluate our tool and better understand cost considerations in open-source projects for our research. All data will be treated confidentially.

If you’re curious about our work, we are investigating how developers approach cost in cloud infrastructure, specifically Terraform and AWS CloudFormation. Our goal is to identify **patterns and anti-patterns** to help developers make **more cost-aware infrastructure decisions**. You can check out what we’ve discovered so far here: [https://search-rug.github.io/iac-cost-patterns/](https://search-rug.github.io/iac-cost-patterns/). If you have any questions or would like to discuss our research, don’t hesitate to reach out!

Thank you for your time and support! 🤗

Allia Neamt, MSc Student (Computing Science)  
Faculty of Science and Engineering  
Rijksuniversiteit, Groningen
"""
    return message.strip()

def generate_issue_message_survey_plain(entry):
    issues_count = entry["failed_checks_count"]
    files_count = entry["files_count"]

    message = f"""
Hi there! 👋

I’m a master’s student researching **cost considerations in cloud infrastructure**. As part of this project, we ran a static analysis tool (linter) on your repository to identify cost-related misconfigurations.

We found **{issues_count} potential issue{'s' if issues_count != 1 else ''}** across **{files_count} file{'s' if files_count != 1 else ''}**, {'some of ' if issues_count != 1 else ''}which might **significantly affect the cloud costs** of your project.

Are you interested in the **linter results**? Reply here. We’ll send **the report along with a short follow-up survey** (~5 min) to evaluate our tool and better understand cost considerations in open-source projects for our research. All data will be treated confidentially.

If you’re curious about our work, we are investigating how developers approach cost in cloud infrastructure, specifically Terraform and AWS CloudFormation. Our goal is to identify **patterns and anti-patterns** to help developers make **more cost-aware infrastructure decisions**. You can check out what we’ve discovered so far here: [https://search-rug.github.io/iac-cost-patterns/](https://search-rug.github.io/iac-cost-patterns/). If you have any questions or would like to discuss our research, don’t hesitate to reach out!

Thank you for your time and support! 🤗

Allia Neamt, MSc Student (Computing Science)  
Faculty of Science and Engineering  
Rijksuniversiteit, Groningen
"""
    return message.strip()

def generate_issue_message_example(entry):
    check = entry["example_check"]
    issues_count = entry["failed_checks_count"]
    files_count = entry["files_count"]
    check_name = check["check_name"]
    check_description = check["check_description"]
    resource = check["resource"]
    file_path = check["file_path"]
    line_range = check["file_line_range"]

    message = f"""
Hi there! 👋

I’m a master’s student researching **cost considerations in cloud infrastructure**. As part of this project, we ran a static analysis tool (linter) on your repository and found the following potential misconfiguration that could lead to unnecessary costs:

✔️ **Issue:** {check_name}  
📃 **Description:** {check_description}  
⚙️ **Resource:** `{resource}`  
🔎 **File:** `{file_path}`
📍 **Line Range:** `{line_range}`

Please let me know if this is helpful or if it makes sense for your project. If you have any questions or would like to discuss this further, feel free to reach out! Thanks for your time! 🤗

Allia Neamt, MSc Student (Computing Science)  
Faculty of Science and Engineering  
Rijksuniversiteit, Groningen
"""
    return message.strip()

def repo_url_to_owner_repo(repo_url):
    # Extract owner and repo name from URL
    parts = repo_url.rstrip('/').split('/')
    owner = parts[-2]
    repo = parts[-1]
    return owner, repo

def open_issues(filename, message_type="survey"):
    log(f"Opening issues from {filename} with message type '{message_type}'", "../logs.txt")
    data = load_yaml(filename)
    opened_issues = []
    not_opened_issues = []

    for entry in data:
        owner, repo = repo_url_to_owner_repo(entry["repo"])
        issue_title = f"Cost-Related Misconfigurations Findings"
        if message_type == "survey":
            issue_body = generate_issue_message_survey(entry)
        elif message_type == "survey_plain":
            issue_body = generate_issue_message_survey_plain(entry)
        elif message_type == "example":
            issue_body = generate_issue_message_example(entry)
        github_token = os.getenv("GITHUB_TOKEN")

        try:
            url = f"https://api.github.com/repos/{owner}/{repo}/issues"
            headers = {
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github+json"
            }

            response = requests.post(url, json={
                "title": issue_title,
                "body": issue_body
            }, headers=headers)

            if response.status_code == 201:
                log(f"\tIssue created successfully for {entry['repo']}", "data/gh_issues/logs.txt")
                opened_issues.append(entry["repo"])
            else:
                log(f"\tFailed to create issue for {entry['repo']}: {response.status_code} - {response.text}", "data/gh_issues/logs.txt")
                not_opened_issues.append({
                    "repo": entry["repo"],
                    "error": "Issues disabled" if response.status_code == 410 else response.text
                })
        except Exception as e:
            log(f"Error creating issue for {entry['repo']}: {str(e)}", "data/gh_issues/logs.txt")

    if opened_issues:
        add_to_file(opened_issues, "../gh_issues/issues_opened.yml")
    if not_opened_issues:
        add_to_file(not_opened_issues, "../gh_issues/issues_not_opened.yml")
    log("\n", "../logs.txt")