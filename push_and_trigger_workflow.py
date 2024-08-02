import os
from dotenv import load_dotenv
import requests
import json
import subprocess
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
    if os.getenv("CI"):
        # Running in a CI environments
        commit_message = os.getenv("COMMIT_MESSAGE", "Automated commit")
    else:
        commit_message = session.prompt("Enter commit message: ")

    try:
        # Check for changes
        result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if not result.stdout.strip():
            print("No changes to commit.")
            return

        subprocess.run(["git", "add", "."], check=True)
        result = subprocess.run(["git", "commit", "-m", commit_message], check=True, capture_output=True, text=True)
        print(result.stdout)
        subprocess.run(["git", "push"], check=True)
        print("Git push successful.")
    except subprocess.CalledProcessError as e:
        print(f"Error executing Git commands: {e}")
        exit(1)

def trigger_workflow():
    load_dotenv()

    SNOWFLAKE_ACCOUNT = os.getenv('SNOWFLAKE_ACCOUNT')
    SNOWFLAKE_USER = os.getenv('SNOWFLAKE_USER')
    SNOWFLAKE_PASSWORD = os.getenv('SNOWFLAKE_PASSWORD')
    SNOWFLAKE_ROLE = os.getenv('SNOWFLAKE_ROLE')
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

    if not all([SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PASSWORD, SNOWFLAKE_ROLE, GITHUB_TOKEN]):
        print("Please set your credentials in the .env file.")
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
    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 204:
        print("Workflow triggered successfully.")
    else:
        print(f"Failed to trigger workflow: {response.status_code}")
        print(response.text)

def main():
    push_first()
    trigger_workflow()

if __name__ == "__main__":
    main()
