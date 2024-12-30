import asyncio
from slack_sdk.web.async_client import AsyncWebClient
from typing import Any, Dict

from utils.airtable import Macro
from utils.env import env
from events.mark_resolved import handle_mark_resolved


async def handle_execute_macro(
    user_id: str, macro: Macro, ts: str, client: AsyncWebClient
):
    user_info_fut = asyncio.create_task(client.users_info(user=user_id))

    user = await user_info_fut
    user_name = user["user"]["profile"]["display_name"] or user["user"]["real_name"]

    await client.chat_postMessage(
        channel=env.slack_request_channel,
        thread_ts=ts,
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{user_name} executed {macro.name} on this thread:",
                },
            },
            macro.message,
        ],
        unfurl_links=True,
        unfurl_media=True
    )
    
    req = env.airtable.get_request(priv_thread_ts=ts)
    if not req:
        await client.chat_postMessage(
            channel=env.slack_ticket_creator,
            text=f"Something went wrong with fetching `{ts}` from Airtable.",
        )
        return

    await client.chat_postMessage(
        channel=env.slack_support_channel,
        thread_ts=req["fields"]["identifier"],
        blocks=[macro.message],
        username=user_name,
        icon_url=user["user"]["profile"]["image_48"],
        unfurl_links=True,
        unfurl_media=True
    )

    if macro.close:
        await handle_mark_resolved(
            ts,
            user_id,
            client,
        )


async def create_macro(user_id: str, name: str, message: Dict[str, Any], close: bool):
    env.airtable.insert_macro(user_id, Macro(name, message, close))
