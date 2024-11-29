from typing import Any, Dict
from slack_sdk.web.async_client import AsyncWebClient
from utils.env import env
from utils.views import views


async def handle_custom_response_btn(body: Dict[str, Any], client: AsyncWebClient):
    req = env.airtable.get_request(priv_thread_ts=body["message"]["ts"])

    msg = await client.conversations_history(
        channel=env.slack_request_channel,
        latest=body["message"]["ts"],
        limit=1,
        inclusive=True,
    )
    blocks = msg["messages"][0]["blocks"]
    for block in blocks:
        if block["type"] == "context":
            text = (
                block["elements"][0]["text"]
                + f" <@{body['user']['id']}> is responding."
            )
            block["elements"][0]["text"] = text
            blocks[blocks.index(block)] = block

    msg_text = msg.get("messages", [{}])[0].get("text")

    await client.chat_update(
        channel=env.slack_request_channel,
        ts=body["message"]["ts"],
        blocks=blocks,
        text=msg_text,
    )

    await client.views_open(
        trigger_id=body["trigger_id"],
        view=views.custom_response(
            req["fields"]["content"], req["fields"]["identifier"]
        ),
    )


async def handle_custom_response(body: Dict[str, Any], client: AsyncWebClient):
    view = body["view"]

    req = env.airtable.get_request(pub_thread_ts=view["blocks"][0]["block_id"])
    env.airtable.update_request(
        pub_thread_ts=req["fields"]["identifier"],
        **{
            "status": "responded",
        },
    )

    msg = await client.conversations_history(
        channel=env.slack_request_channel,
        latest=req["fields"]["internal_thread"],
        limit=1,
        inclusive=True,
    )

    blocks = msg["messages"][0]["blocks"]

    for block in blocks:
        if block["type"] == "context":
            text = block["elements"][0]["text"].replace(
                f" <@{body['user']['id']}> is responding.",
                f'<@{body["user"]["id"]}> has responded.',
            )
            block["elements"][0]["text"] = text
            blocks[blocks.index(block)] = block

    await client.chat_update(
        channel=env.slack_request_channel,
        ts=req["fields"]["internal_thread"],
        blocks=blocks,
        text=msg["messages"][0]["text"],
    )

    user = await client.users_info(user=body["user"]["id"])

    for block in view["blocks"]:
        if block["block_id"] == "custom-response-input":
            await client.chat_postMessage(
                channel=env.slack_support_channel,
                text=view["state"]["values"]["custom-response-input"][
                    "custom-response-input"
                ]["value"],
                thread_ts=req["fields"]["identifier"],
                username=user["user"]["profile"]["display_name"]
                or user["user"]["real_name"],
                icon_url=user["user"]["profile"]["image_48"],
                unfurl_links=True
            )
            break
