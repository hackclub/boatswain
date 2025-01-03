# Boatswain

Boatswain is a Slack app for #high-seas-help in the Hack Club Slack. It's built for us to quickly answer as many help questions as possible whilst also being human. 

## Features

- **Thread System** - Users can create support threads by messaging in #high-seas-help and it gets sent to a private relay channel where the support team (lifeguards) can respond.
- **Macros** - Lifeguards can create their own macros to quickly respond to common questions.
- **Airtable Integration** - All support threads are logged in an Airtable base for easy tracking and analytics.
- **GitHub Issue Creation** - If a support thread is deemed to be a bug, a GitHub issue can be created directly from the thread by clicking a button to open a modal.
- **Resolving** - Once a thread is resolved, the lifeguard can mark it as resolved and it will be logged in Airtable as such and all traces will be deleted from the private channel.
- **User Information** - When a new request is created, Boatswain will automatically send a message in the thread with information about the users votes, ships, any fraud cases, doubloons and more.

The goal is that the private channel remains empty, meaning there are no more questions to respond to.

## Development

1. `python3 -m venv .venv`
2. `source .venv/bin/activate`
3. `python3 -m pip install -r requirements.txt`
4. `python3 main.py`

The following environment variables are required:

- `SLACK_BOT_TOKEN` - _Get this from Slack app dash_
- `SLACK_USER_TOKEN` - _Get this from Slack app dash_
- `SLACK_SIGNING_SECRET` - _Get this from Slack app dash_
- `SLACK_SUPPORT_CHANNEL` - _Get this from the channel link_
- `SLACK_REQUEST_CHANNEL` - _Get this from the channel link_
- `SLACK_GH_TICKET_CREATOR` - _User ID. Set this to yourself if you're running the app_
- `AIRTABLE_API_KEY` - _Get this from the [Airtable Builder Hub](https://airtable.com/create/tokens)_
- `AIRTABLE_BASE_ID` - _Get this from the Airtable Base URL (app...)_
- `GITHUB_REPO` - _Get this from the GitHub repository URL (hackclub/boatswain)_
- `GITHUB_TOKEN` - _Get this from the [GitHub Developer Settings](https://github.com/settings/tokens)_

The following environment variables are optional:
- `PORT` - _Defaults to 3000 if not specified_

## Deployment

Add notes on gunicorn (Don't use the dev server)