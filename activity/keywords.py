from github import Github
import datetime

from utils.yaml_utils import load_yaml, save_to_file
from utils.github_utils import github_limit
from utils.logger import log
from utils.usage import extract_repo_name

KEYWORDS = ['bill', 'cheap', 'cost', 'efficient', 'expens', 'pay', 'overprovisioned', 'PAY_PER_REQUEST', 'r/w', 'lifecycle', 'old generation']

def search_keywords(github_client, file_path, log_file, keywords_file, no_keywords_file, search="commits", months=12):

    if search == "commits":
        log(f"Searching for keywords in the last 10,000 commits", log_file)
    else:
        log(f"Searching for keywords in the last {months} months", log_file)

    repositories = load_yaml(file_path)

    since = datetime.datetime.now() - datetime.timedelta(days=30 * months)
    keyword_repos = []
    no_keyword_repos = []

    for repo in repositories:
        repo_url = repo["repo"]
        repo_name = extract_repo_name(repo_url)
        try:
            github_limit(github_client, log_file)
            log(f"\tProcessing repo: {repo_url}", log_file)
            repository = github_client.get_repo(repo_name)

            if search == "commits":
                commits = repository.get_commits()
            else:
                commits = repository.get_commits(since=since)

            found_keywords = set()
            for i, commit in enumerate(commits):
                if i >= 10000:
                    break

                try:
                    full_commit = repository.get_commit(commit.sha)
                    files_changed = [file.filename for file in full_commit.files]
                except Exception as e:
                    log(f"\t\tCould not fetch files for commit {commit.sha}: {e}", log_file)
                    continue

                # Check for .tf file changes
                if not any(f.endswith('.tf') for f in files_changed):
                    continue

                commit_message = commit.commit.message.lower()
                for keyword in KEYWORDS:
                    if keyword in commit_message:
                        found_keywords.add(keyword)
                        log(f"\t\tFound keyword '{keyword}' in commit: {commit.html_url}", log_file)

                # As soon as we find at least one keyword in a commit that changes .tf files, we can stop
                if found_keywords:
                    break

            if found_keywords:
                repo["keywords"] = list(found_keywords)
                keyword_repos.append(repo)
            else:
                no_keyword_repos.append(repo)
                log(f"\t\tNo keywords found in repo: {repo_name}", log_file)

        except Exception as e:
            log(f"\tError processing repo {repo_name}: {e}", log_file)

    log(f"Found {len(keyword_repos)} repos with keywords and {len(no_keyword_repos)} without keywords.", log_file)
    save_to_file(keyword_repos, keywords_file)
    save_to_file(no_keyword_repos, no_keywords_file)
