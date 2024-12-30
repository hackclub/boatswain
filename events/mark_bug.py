from slack_sdk.web.async_client import AsyncWebClient
from typing import Any, Dict

from utils.env import env
from events.mark_resolved import handle_mark_resolved

import aiohttp

async def handle_mark_bug(body: Dict[str, Any], client: AsyncWebClient):
    view = body["view"]
    ts = view["blocks"][-1]["block_id"]
    blocks = view["blocks"]


    req = env.airtable.update_request(
        priv_thread_ts=ts,
        updates={
            "status": "responded",
            "bug_report": True,
        },
    )

    if not req:
        await client.chat_postMessage(
            channel=env.slack_ticket_creator,
            text=f"Something went wrong with fetching `{ts}` from Airtable.\n```{blocks}```",
        )
        return
    
    pub_thread_ts = req["fields"]["identifier"]

    issue_title = view["state"]["values"]["title"]["title"]["value"]
    issue_body = view["state"]["values"]["body"]["body"]["value"]
    issue_labels = view["state"]["values"]["labels"]["labels"]["selected_options"]

    footer = f"\n\n---\n\n_This issue was created automatically by the support team. See the appropriate thread [here](https://hackclub.slack.com/archives/{env.slack_support_channel}/p{pub_thread_ts})_"

    data = {
        'title': issue_title,
        'body': issue_body + footer,
        'labels': [label['value'] for label in issue_labels],
    }

    url = f'https://api.github.com/repos/{env.github_repo}/issues'

    headers = {
        'Accept': 'application/vnd.github+json',
        'Authorization': f'Bearer {env.github_token}',
        'X-GitHub-API-Version': '2022-11-28',
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as resp:
            if resp.status != 201:
                await client.chat_postMessage(
                    channel=env.slack_ticket_creator,
                    text=f"Error creating issue for `{ts}`: {resp.status}\n```{await resp.text()}```",
                )


    await handle_mark_resolved(
        ts=ts,
        resolver_id=body["user"]["id"],
        client=client,
        custom_response=f"Thanks for reporting this! It's been logged and the team will try and get it fixed as soon as possible!\nIf you have any more questions, please make a new post in <#{env.slack_support_channel}> and we'll be happy to help you out!",
    )
