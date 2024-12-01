from .airtable import AirtableManager
from dotenv import load_dotenv
import os

load_dotenv()


class Environment:
    def __init__(self):
        self.slack_bot_token = os.environ.get("SLACK_BOT_TOKEN")
        self.slack_user_token = os.environ.get("SLACK_USER_TOKEN")
        self.slack_signing_secret = os.environ.get("SLACK_SIGNING_SECRET")
        self.slack_support_channel = os.environ.get("SLACK_SUPPORT_CHANNEL")
        self.slack_request_channel = os.environ.get("SLACK_REQUEST_CHANNEL")
        self.slack_ticket_creator = os.environ.get("SLACK_GH_TICKET_CREATOR")
        self.github_repo = os.environ.get("GITHUB_REPO")
        self.github_token = os.environ.get("GITHUB_TOKEN")
        self.threadlocker_api_url = os.environ.get("THREADLOCKER_API_URL")
        self.threadlocker_api_key = os.environ.get("THREADLOCKER_API_KEY")
        self.airtable_api_key = os.environ.get("AIRTABLE_API_KEY")
        self.airtable_base_id = os.environ.get("AIRTABLE_BASE_ID")
        self.sentry_dsn = os.environ.get("SENTRY_DSN")
        self.environment = os.environ.get("ENVIRONMENT", "development")

        self.port = int(os.environ.get("PORT", 3000))

        if not self.slack_bot_token:
            raise Exception("SLACK_BOT_TOKEN is not set")
        if not self.slack_user_token:
            raise Exception("SLACK_USER_TOKEN is not set")
        if not self.slack_signing_secret:
            raise Exception("SLACK_SIGNING_SECRET is not set")
        if not self.slack_support_channel:
            raise Exception("SLACK_SUPPORT_CHANNEL is not set")
        if not self.slack_request_channel:
            raise Exception("SLACK_REQUEST_CHANNEL is not set")
        if not self.slack_ticket_creator:
            raise Exception("SLACK_GH_TICKET_CREATOR is not set")
        if not self.github_repo:
            raise Exception("GITHUB_REPO is not set")
        if not self.github_token:
            raise Exception("GITHUB_TOKEN is not set")
        if not self.threadlocker_api_url:
            raise Exception("THREADLOCKER_API_URL is not set")
        if not self.threadlocker_api_key:
            raise Exception("THREADLOCKER_API_KEY is not set")
        if not self.airtable_api_key:
            raise Exception("AIRTABLE_API_KEY is not set")
        if not self.airtable_base_id:
            raise Exception("AIRTABLE_BASE_ID is not set")
        if not self.sentry_dsn and self.environment == "production":
            raise Exception("SENTRY_DSN is not set")

        self.airtable = AirtableManager(
            api_key=self.airtable_api_key, base_id=self.airtable_base_id
        )


env = Environment()
