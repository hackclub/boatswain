from slack_sdk.web.async_client import AsyncWebClient
from typing import Dict, Any


from events.macros import handle_execute_macro
from utils.env import env
from utils.queue import add_message_to_delete_queue

async def handle_message(body: Dict[str, Any], client: AsyncWebClient, say):
    if body["event"]["channel"] not in [
        env.slack_support_channel,
        env.slack_request_channel,
    ]:
        return

    subtype = body["event"].get("subtype")
    if body["event"].get("subtype", None) not in [
        None,
        "message_changed",
        "message_deleted",
        "file_share",
    ]:
        return

    match body["event"]["channel"]:
        case env.slack_support_channel:
            match subtype:
                case None | "file_share":
                    if body["event"].get("thread_ts"):
                        await handle_new_support_response(body, client)
                    else:
                        await handle_new_message(body, client)
                case "message_changed":
                    if body["event"].get("previous_message").get("thread_ts"):
                        await handle_edited_message(
                            body,
                            client,
                            ts=body["event"]["previous_message"]["thread_ts"],
                        )
                case "message_deleted":
                    await handle_deleted_message(body, client)

        case env.slack_request_channel:
            match subtype:
                case None | "file_share":
                    if body["event"].get("thread_ts"):
                        await handle_new_request_message(body, client)
                case "message_changed":
                    if body["event"].get("previous_message").get("thread_ts"):
                        await handle_edited_message(
                            body,
                            client,
                            ts=body["event"]["previous_message"]["thread_ts"],
                        )


async def handle_new_support_response(body: Dict[str, Any], client: AsyncWebClient):
    req = env.airtable.get_request(body["event"]["thread_ts"])
    if not req:
        return

    if req["fields"]["status"] == "resolved":
        return

    req_msg = await client.conversations_history(
        channel=env.slack_request_channel,
        latest=req["fields"]["internal_thread"],
        oldest=req["fields"]["internal_thread"],
        limit=1,
        inclusive=True,
    )

    if not req_msg or not req_msg.get("messages"):
        return

    user = await client.users_info(user=body["event"]["user"])
    text = body["event"].get("text", "")

    if body["event"].get("files"):
        files = body["event"]["files"]
        for file in files:
            filename = file["name"]
            if files.index(file) > 0:
                text += f", <{file['permalink']}|{filename}>"
            else:
                text += f"\n<{file['permalink']}|{filename}>"

    await client.chat_postMessage(
        channel=env.slack_request_channel,
        thread_ts=req["fields"]["internal_thread"],
        text=text,
        username=user["user"]["profile"]["display_name"] or user["user"]["real_name"],
        icon_url=user["user"]["profile"]["image_48"],
        unfurl_links=True,
        unfurl_media=True
    )


async def handle_new_message(body: Dict[str, Any], client: AsyncWebClient):
    user = await client.users_info(user=body["event"]["user"])

    airtable_user = env.airtable.get_person(user["user"]["id"])
    if not airtable_user:
        forename = user["user"]["profile"]["first_name"]
        surname = user["user"]["profile"]["last_name"]
        slack_id = user["user"]["id"]
        email = user["user"]["profile"].get("email")
        env.airtable.create_person(forename, surname, email, slack_id)
        count = 0
    else:
        count = len(airtable_user.get("fields", {}).get("help_requests", []))

    await client.reactions_add(
        channel=env.slack_support_channel,
        name="thinking_face",
        timestamp=body["event"]["ts"],
    )

    if count == 0:
        await client.chat_postMessage(
            channel=env.slack_support_channel,
            thread_ts=body["event"]["ts"],
            text=f"hey there {user["user"]["profile"]["display_name"] or user["user"]["real_name"]}! it looks like this is your first time in the support channel. We've recieved your question and will get back to you as soon as possible. In the meantime, feel free to check out our <https://hack.club/high-seas-faq|FAQ> for answers to common questions. If you have any more questions, please make a new post in <#{env.slack_support_channel}> so we can help you quicker!",
            unfurl_links=True,
            unfurl_media=True
        )

    thread_url = f"https://hackclub.slack.com/archives/{env.slack_support_channel}/p{body['event']['ts'].replace('.', '')}"
    new_blocks = [
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Submitted by <@{user['user']['id']}>. They have {count} other help requests. <{thread_url}|Go to thread>",
                }
            ],
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Use Macro"},
                    "value": "use-macro",
                    "action_id": "use-macro",
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Open Ticket"},
                    "value": "mark-bug",
                    "action_id": "mark-bug",
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Mark Resolved"},
                    "style": "primary",
                    "value": "mark-resolved",
                    "action_id": "mark-resolved",
                },
            ],
        },
    ]

    msg = await client.chat_postMessage(
        channel=env.slack_request_channel,
        blocks=new_blocks,
        text="",
        username=user["user"]["profile"]["display_name"] or user["user"]["real_name"],
        icon_url=user["user"]["profile"]["image_48"],
        unfurl_links=True,
        unfurl_media=True
    )

    env.airtable.create_request(
        pub_thread_ts=body["event"]["ts"],
        content=body["event"]["text"],
        user_id=body["event"]["user"],
        priv_thread_ts=msg["ts"],
    )
    
    hs_user = env.airtable.get_hs_user(body["event"]["user"]) or {}
    fraud_data = env.airtable.get_fraud_data(body["event"]["user"]) or {}
    
    stage = hs_user.get("fields", {}).get("stage", "unknown").replace("_", " ").title()
    verification_status = hs_user.get("fields", {}).get("verification_status", "unknown")[0]
    
    doubloons_paid = hs_user.get("fields", {}).get("doubloons_paid", 0)
    doubloons_spent = hs_user.get("fields", {}).get("doubloons_spent", 0)
    doubloons_balance = hs_user.get("fields", {}).get("doubloons_balance", 0)
    doubloons_granted = hs_user.get("fields", {}).get("doubloons_granted", 0)
    
    unique_vote_count = hs_user.get("fields", {}).get("unique_vote_count", 0)
    vote_count = hs_user.get("fields", {}).get("vote_count", 0)
    total_ships = hs_user.get("fields", {}).get("total_ships", 0)
    
    has_ordered_free_stickers = hs_user.get("fields", {}).get("has_ordered_free_stickers", False)
    
    waka_total_hours_logged = hs_user.get("fields", {}).get("waka_total_hours_logged", 0)
    
    disciplinary_status = hs_user.get("fields", {}).get("disciplinary_status", "None")
    
    total_cases = len(fraud_data)
    open_cases = 0
    for case in fraud_data:
        if case["fields"]["Status"] not in ["Resolved", "Duplicate Case"]:
            open_cases += 1
    
    data_blocks = [
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"""
*:face_with_monocle: User Data:*
*Stage:* {stage}\n
*Verification Status:* {verification_status}\n
*Disciplinary Status:* {disciplinary_status}\n
*Open Fraud Cases:* {open_cases}/{total_cases}

*:doubloon: Doubloons:*
*Paid:* {doubloons_paid}\n
*Spent:* {doubloons_spent}\n
*Granted:* {doubloons_granted}\n
*Balance:* {doubloons_balance}\n

*:ship: Shippy Stats:*
*Unique Votes:* {unique_vote_count}/{vote_count}\n
*Total Ships:* {total_ships}\n
*Ordered Free Stickers:* {has_ordered_free_stickers}\n
*Total Hours Logged*: {waka_total_hours_logged}
                    """
                },
            ]
        }
    ]
    
    await client.chat_postMessage(
        channel=env.slack_request_channel,
        thread_ts=msg["ts"],
        blocks=data_blocks,
        unfurl_links=True,
        unfurl_media=True
    )


async def handle_edited_message(body: Dict[str, Any], client: AsyncWebClient, ts: str):
    return  # Will be implemented later
    if body["event"]["channel"] == env.slack_support_channel:
        req = env.airtable.get_request(pub_thread_ts=ts)
    else:
        req = env.airtable.get_request(priv_thread_ts=ts)

    if not req:
        print("no req")
        return

    text: str = body["event"]["message"]["text"]
    if ":shushing_face:" in text or text.startswith("!"):
        return

    user_id = body.get("event", {}).get("message", {}).get("user")
    print(user_id)
    user = await client.users_info(user="U054VC2KM9P")

    if body["event"]["message"].get("files"):
        files = body["event"]["message"]["files"]
        for file in files:
            filename = file["name"]
            if files.index(file) > 0:
                text += f", <{file['permalink']}|{filename}>"
            else:
                text += f"\n<{file['permalink']}|{filename}>"

    await client.chat_update(
        channel=(
            env.slack_request_channel
            if body["event"]["channel"] == env.slack_support_channel
            else env.slack_support_channel
        ),
        ts=(
            req["fields"]["internal_thread"]
            if body["event"]["channel"] == env.slack_support_channel
            else req["fields"]["identifier"]
        ),
        text=text,
        username=user["user"]["profile"]["display_name"],
        icon_url=user["user"]["profile"]["image_48"],
    )


async def handle_deleted_message(body: Dict[str, Any], client: AsyncWebClient):
    if body["event"].get("previous_message", {}).get("thread_ts"):
        return
    
    env.airtable.delete_req(body["event"]["previous_message"]["ts"])
    msg = await client.conversations_history(
        channel=env.slack_request_channel,
        latest=body["event"]["previous_message"]["ts"],
        limit=1,
        inclusive=True,
    )
    if msg:
        add_message_to_delete_queue(
            channel_id=env.slack_request_channel, message_ts=msg["messages"][0]["ts"]
        )


async def handle_new_request_message(body: Dict[str, Any], client: AsyncWebClient):
    req = env.airtable.get_request(priv_thread_ts=body["event"]["thread_ts"])
    if not req:
        return

    text: str = body["event"]["text"]
    if ":shushing_face:" in text or text.startswith("!"):
        return
    elif text.startswith("?"):
        try:
            macro = next(iter(x for x in env.airtable.get_macros(body["event"]["user"]) if x.name.lower() == text.lstrip("?").strip().lower()))
            await handle_execute_macro(body["event"]["user"], macro, body["event"]["thread_ts"], client)
        except StopIteration:
            await client.chat_postMessage(
                channel=env.slack_request_channel,
                thread_ts=body["event"]["thread_ts"],
                text=f"Couldn't find that macro <@{body["event"]["user"]}>",
            )
        return

    user = await client.users_info(user=body["event"]["user"])
    text = body["event"].get("text", "")

    if body["event"].get("files"):
        files = body["event"]["files"]
        for file in files:
            filename = file["name"]
            if files.index(file) > 0:
                text += f", <{file['permalink']}|{filename}>"
            else:
                text += f"\n<{file['permalink']}|{filename}>"

    await client.chat_postMessage(
        channel=env.slack_support_channel,
        thread_ts=req["fields"]["identifier"],
        text=text,
        username=user["user"]["profile"]["display_name"] or user["user"]["real_name"],
        icon_url=user["user"]["profile"]["image_48"],
        unfurl_links=True,
        unfurl_media=True
    )
