from slack_sdk.web.async_client import AsyncWebClient

from typing import Any, Dict

from utils.env import env
from events.mark_resolved import handle_mark_resolved


async def handle_direct_to_faq(body: Dict[str, Any], client: AsyncWebClient):
    req = env.airtable.get_request(priv_thread_ts=body["message"]["ts"])
    await client.chat_postMessage(
        channel=env.slack_support_channel,
        thread_ts=req["fields"]["identifier"],
        text=f"hey, this question is answered in the FAQ! You can <https://hack.club/high-seas-faq|check it out here>!\nif you have any more questions, feel free to make a new post in <#{env.slack_support_channel}>",
        unfurl_links=True,
        unfurl_media=True
    )

    await handle_mark_resolved(ts=body["message"]["ts"], resolver_id=body["user"]["id"], client=client, message=False)
