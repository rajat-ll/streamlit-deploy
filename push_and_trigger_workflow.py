import os
import requests
import json
import subprocess
import snowflake.connector
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import Completer, Completion
from collections import OrderedDict

class HistoryCompleter(Completer):
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        history = session.history.get_strings()
        unique_matches = OrderedDict()

        for entry in reversed(history):
            if entry.startswith(text):
                unique_matches[entry] = None

        for match in unique_matches:
            yield Completion(match, start_position=-len(text))

session = PromptSession(history=FileHistory('commit_message_history.txt'),
                        auto_suggest=AutoSuggestFromHistory(),
                        completer=HistoryCompleter())

def push_first():
    print("Checking for changes to commit...")
    if os.getenv("CI"):
        # Running in a CI environment
        commit_message = os.getenv("COMMIT_MESSAGE", "Automated commit")
    else:
        commit_message = session.prompt("Enter commit message: ")

    try:
        # Check for changes
        result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        print(f"Git status result: {result.stdout.strip()}")
        if not result.stdout.strip():
            print("No changes to commit.")
            return

        print("Adding changes to git...")
        subprocess.run(["git", "add", "."], check=True)
        print("Committing changes...")
        result = subprocess.run(["git", "commit", "-m", commit_message], check=True, capture_output=True, text=True)
        print(result.stdout)
        print("Pushing changes to remote repository...")
        subprocess.run(["git", "push"], check=True)
        print("Git push successful.")
    except subprocess.CalledProcessError as e:
        print(f"Error executing Git commands: {e}")
        exit(1)

def deploy_to_snowflake():
    print("Deploying to Snowflake...")
    SNOWFLAKE_ACCOUNT = os.getenv('SNOWFLAKE_ACCOUNT')
    SNOWFLAKE_USER = os.getenv('SNOWFLAKE_USER')
    SNOWFLAKE_PASSWORD = os.getenv('SNOWFLAKE_PASSWORD')
    SNOWFLAKE_ROLE = os.getenv('SNOWFLAKE_ROLE')

    if not all([SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PASSWORD, SNOWFLAKE_ROLE]):
        print("Error: Snowflake environment variables are not set properly.")
        return

    try:
        conn = snowflake.connector.connect(
            user=SNOWFLAKE_USER,
            password=SNOWFLAKE_PASSWORD,
            account=SNOWFLAKE_ACCOUNT,
            role=SNOWFLAKE_ROLE
        )
        cursor = conn.cursor()
        print("Connected to Snowflake. Running SQL commands...")
        # Example of running a simple query. Replace with your actual deployment commands.
        cursor.execute("SELECT CURRENT_VERSION()")
        result = cursor.fetchone()
        print(f"Snowflake current version: {result[0]}")
        cursor.close()
        conn.close()
        print("Snowflake deployment completed successfully.")
    except Exception as e:
        print(f"Snowflake deployment failed: {e}")

def trigger_workflow():
    print("Loading environment variables from GitHub Secrets...")

    SNOWFLAKE_ACCOUNT = os.getenv('SNOWFLAKE_ACCOUNT')
    SNOWFLAKE_USER = os.getenv('SNOWFLAKE_USER')
    SNOWFLAKE_PASSWORD = os.getenv('SNOWFLAKE_PASSWORD')
    SNOWFLAKE_ROLE = os.getenv('SNOWFLAKE_ROLE')
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

    print("Environment variables loaded:")
    print(f"SNOWFLAKE_ACCOUNT: {SNOWFLAKE_ACCOUNT}")
    print(f"SNOWFLAKE_USER: {SNOWFLAKE_USER}")
    print(f"SNOWFLAKE_PASSWORD: {'***' if SNOWFLAKE_PASSWORD else 'Not Set'}")
    print(f"SNOWFLAKE_ROLE: {SNOWFLAKE_ROLE}")
    print(f"GITHUB_TOKEN: {'***' if GITHUB_TOKEN else 'Not Set'}")

    if not all([SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PASSWORD, SNOWFLAKE_ROLE, GITHUB_TOKEN]):
        print("Error: Not all required environment variables are set.")
        return  # Exit the function instead of exiting the script

    REPO_OWNER = "rajat-ll"
    REPO_NAME = "streamlit-deploy"

    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/workflows/deploy.yml/dispatches"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {GITHUB_TOKEN}"
    }
    data = {
        "ref": "main"
    }

    print(f"Triggering workflow for {REPO_OWNER}/{REPO_NAME} at {url}")
    print(f"Headers: {json.dumps(headers, indent=2)}")
    print(f"Data: {json.dumps(data, indent=2)}")

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        print(f"Response status code: {response.status_code}")
        print(f"Response text: {response.text}")

        if response.status_code == 204:
            print("Workflow triggered successfully.")
        else:
            print(f"Failed to trigger workflow: {response.status_code}")
            print(response.text)
    except requests.exceptions.RequestException as e:
        print(f"Error triggering workflow: {e}")

def main():
    print("Starting push_first")
    push_first()
    print("Finished push_first, now deploying to Snowflake")
    deploy_to_snowflake()
    print("Finished deploying to Snowflake, now triggering workflow")
    trigger_workflow()
    print("Finished triggering workflow")

if __name__ == "__main__":
    main()
