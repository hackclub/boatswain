from slack_sdk.web.async_client import AsyncWebClient
from events.mark_resolved import handle_mark_resolved
from typing import Dict, Any
from utils.env import env


async def handle_reaction(body: Dict[str, Any], client: AsyncWebClient):
    print(body)
    if body["event"]["reaction"] == "white_check_mark":
        help_event = env.airtable.get_request(pub_thread_ts=body["event"]["item"]["ts"])
        try:
            if help_event["fields"]["status"] == "resolved":
                return
        except KeyError:
            pass
        ts = help_event["fields"]["internal_thread"]
        resolver_id = body["event"]["user"]
        OG_slack_asker_airtable_id = help_event["fields"]["person"][0]
        OG_slack_asker = env.airtable.get_person_by_id(OG_slack_asker_airtable_id)
        if OG_slack_asker:
            OG_slack_asker_slackid = OG_slack_asker["fields"]["slack_id"]
        else:
            OG_slack_asker_slackid = None
        if OG_slack_asker_slackid == resolver_id:
            await handle_mark_resolved(ts, resolver_id, client)
        else:
            await client.chat_postMessage(
            channel=env.slack_support_channel,
            thread_ts=body["event"]["item"]["ts"],
            text=f"Hey <@{OG_slack_asker_slackid}>, <@{resolver_id}> belives they have resolved this issue. If you believe this issue is resolved, please react with :white_check_mark: to confirm on the original thread (the one with the :thinking_face:).",
            unfurl_links=True,
            unfurl_media=True
        )