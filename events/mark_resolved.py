import asyncio
from slack_sdk.errors import SlackApiError
from slack_sdk.web.async_client import AsyncWebClient

from utils.env import env
from utils.queue import add_message_to_delete_queue


async def delete_task(ts: str, client: AsyncWebClient):
    messages = await client.conversations_replies(
        channel=env.slack_request_channel, ts=ts
    )
    for message in messages["messages"]:
        add_message_to_delete_queue(
            channel_id=env.slack_request_channel, message_ts=message["ts"]
        )


async def handle_mark_resolved(
    ts,
    resolver_id,
    client: AsyncWebClient,
    message: bool = True,
    custom_response: str | None = None,
):
    # channel_name = await client.conversations_info(channel=env.slack_support_channel)
    # if not channel_name["channel"]["is_channel"]:
    #     return
    # channel_name = channel_name["channel"]["name"]

    task = asyncio.create_task(delete_task(ts, client))

    res = env.airtable.resolve_request(ts, resolver_id)
    if not res:
        return
    
    try:
        await client.reactions_remove(
            channel=env.slack_support_channel,
            name="thinking_face",
            timestamp=res["fields"]["identifier"],
        )
    except SlackApiError as e:
        if e.response["error"] in ("no_reaction", "message_not_found"):
            pass
        
        raise e
    
    try:
        await client.reactions_add(
            channel=env.slack_support_channel,
            name="white_check_mark",
            timestamp=res["fields"]["identifier"],
        )
    except SlackApiError as e:
        if e.response["error"] in ("already_reacted", "message_not_found", "too_many_emoji", "too_many_reactions"):
            pass

    if message:
        await client.chat_postMessage(
            channel=env.slack_support_channel,
            thread_ts=res["fields"]["identifier"],
            text=custom_response
            or f"This post has been marked as resolved by <@{resolver_id}>!\nIf you have any more questions, please make a new post in <#{env.slack_support_channel}> and we'll be happy to help you out!",
            unfurl_links=True
        )
    
    await task
