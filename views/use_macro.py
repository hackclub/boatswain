import itertools
from typing import Any, Dict
from utils.env import env

PAGE_SIZE = 15


def get_modal(ts: str, user_id: str, page: int = 0) -> Dict[str, Any]:
    macros = env.airtable.get_macros(user_id)
    current_page = macros[page*PAGE_SIZE:(page+1)*PAGE_SIZE]
    is_end_page = len(macros) < (page+1)*PAGE_SIZE
    is_first_page = page == 0

    return {
        "type": "modal",
        "title": {"type": "plain_text", "text": "Execute a macro", "emoji": True},
        "close": {"type": "plain_text", "text": "Cancel", "emoji": True},
        "blocks": [
            {"type": "header", "text": {"type": "plain_text", "text": "Your macros"}},
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Showing {(page*PAGE_SIZE)+1}-{(page*PAGE_SIZE)+len(current_page)} of {len(macros)}"
                    }
                ],
            },
            *([{
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": ":arrow_left: Previous page",
                            "emoji": True,
                        },
                        "value": f"{page-1};{ts}",
                        "action_id": "use-macro-pagination",
                    } if not is_first_page else {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": ":see_no_evil: (no previous page)",
                            "emoji": True,
                        },
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Next page :arrow_right:",
                            "emoji": True,
                        },
                        "value": f"{page+1};{ts}",
                        "action_id": "use-macro-pagination",
                    } if not is_end_page else {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "(no next page) :see_no_evil:",
                            "emoji": True,
                        },
                    },
                ],
            }] if not (is_end_page and is_first_page) else []),
            *itertools.chain.from_iterable(
                [
                    [
                        {
                            "type": "section",
                            "text": {"type": "mrkdwn", "text": f"*{macro.name}*"},
                        },
                        macro.message,
                        {
                            "type": "context",
                            "elements": [
                                {
                                    "type": "mrkdwn",
                                    "text": ":no_entry: Closes thread"
                                    if macro.close
                                    else ":white_check_mark: Leaves thread open",
                                }
                            ],
                        },
                        {
                            "type": "actions",
                            "elements": [
                                {
                                    "type": "button",
                                    "text": {
                                        "type": "plain_text",
                                        "text": f"Execute{" and close" if macro.close else ""}",
                                        "emoji": True,
                                    },
                                    "value": f"{i};{ts}",
                                    "action_id": "execute-macro",
                                },
                                {
                                    "type": "button",
                                    "text": {
                                        "type": "plain_text",
                                        "text": "Delete macro",
                                        "emoji": True,
                                    },
                                    "style": "danger",
                                    "value": f"{i};{ts}",
                                    "action_id": "delete-macro",
                                    "confirm": {
                                        "title": {
                                            "type": "plain_text",
                                            "text": "Confirm",
                                        },
                                        "text": {
                                            "type": "plain_text",
                                            "text": f"Do you want to delete {macro.name}?",
                                        },
                                        "confirm": {
                                            "type": "plain_text",
                                            "text": "Go on",
                                        },
                                        "deny": {
                                            "type": "plain_text",
                                            "text": "Nevermind actually",
                                        },
                                    },
                                },
                            ],
                        },
                        {"type": "divider"},
                    ]
                    for i, macro in enumerate(current_page)
                ]
            ),
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Create a new macro",
                            "emoji": True,
                        },
                        "value": "love you slack",
                        "style": "primary",
                        "action_id": "create-macro",
                    }
                ],
            },
        ],
    }
