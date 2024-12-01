from slack_bolt.async_app import AsyncApp
from slack_sdk.web.async_client import AsyncWebClient
from slack_bolt.adapter.starlette.async_handler import AsyncSlackRequestHandler
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse
import sentry_sdk

from threading import Thread
from typing import Callable, Dict, Any

from events.macros import create_macro, handle_execute_macro
from utils.env import env
from utils.queue import process_queue
from events.on_message import handle_message
from events.mark_resolved import handle_mark_resolved
from events.direct_to_faq import handle_direct_to_faq
from events.mark_bug import handle_mark_bug
from events.custom_response import handle_custom_response_btn, handle_custom_response
from views.create_bug import get_modal as create_bug_modal
from views.use_macro import get_modal as create_macro_modal
from views.create_macro import get_modal as create_create_macro_modal

sentry_sdk.init(env.sentry_dsn, traces_sample_rate=1.0)
sentry_sdk.profiler.start_profiler()
app = AsyncApp(token=env.slack_bot_token, signing_secret=env.slack_signing_secret)


async def ping(request):
    airtable_up = env.airtable.ping()
    if not airtable_up:
        return JSONResponse(
            {"status": "ERROR", "message": "Cannot reach Airtable"}
        )
    return JSONResponse({
        "status": "OK",
        "message": "App is running"
    })


@app.event("message")
async def handle_message_events(body: Dict[str, Any], client: AsyncWebClient, say):
    await handle_message(body, client, say)


@app.action("mark-resolved")
async def handle_mark_resolved_button(
    ack: Callable[[], None], body: Dict[str, Any], client: AsyncWebClient
):
    await ack()

    ts = body["message"]["ts"]
    resolver = body["user"]["id"]

    await handle_mark_resolved(ts=ts, resolver_id=resolver, client=client)


@app.action("direct-to-faq")
async def handle_direct_to_faq_button(
    ack: Callable[[], None], body: Dict[str, Any], client: AsyncWebClient
):
    await ack()

    await handle_direct_to_faq(body, client)


@app.action("mark-bug")
async def handle_mark_bug_button(
    ack: Callable[[], None], body: Dict[str, Any], client: AsyncWebClient
):
    await ack()

    await client.views_open(view=create_bug_modal(body["message"]["ts"]), trigger_id=body["trigger_id"])


@app.view("create_issue")
async def handle_create_bug_view(
    ack: Callable[[], None], body: Dict[str, Any], client: AsyncWebClient
):
    await ack()

    await handle_mark_bug(body, client)


@app.action("custom-response")
async def handle_custom_response_button(
    ack: Callable[[], None], body: Dict[str, Any], client: AsyncWebClient
):
    await ack()

    await handle_custom_response_btn(body, client)


@app.view("custom_response_view")
async def handle_custom_response_view(
    ack: Callable[[], None], body: Dict[str, Any], client: AsyncWebClient
):
    await ack()

    await handle_custom_response(body, client)


@app.action("use-macro")
async def handle_use_macro_button(
    ack: Callable[[], None], body: Dict[str, Any], client: AsyncWebClient
):
    await ack()

    view = create_macro_modal(body["message"]["ts"], body["user"]["id"])
    await client.views_open(view=view, trigger_id=body["trigger_id"])


@app.action("use-macro-pagination")
async def handle_use_macro_pagination_button(
    ack: Callable[[], None], body: Dict[str, Any], client: AsyncWebClient
):
    await ack()
    
    [page, ts] = body["actions"][0]["value"].split(";", 1)
    view = create_macro_modal(ts, body["user"]["id"], int(page))
    await client.views_update(view=view, trigger_id=body["trigger_id"], view_id=body["view"]["root_view_id"])


@app.action("execute-macro")
async def handle_execute_macro_view(
    ack: Callable[[], None], body: Dict[str, Any], client: AsyncWebClient
):
    await ack()

    user_id: str = body["user"]["id"]
    block_value: str = body["actions"][0]["value"]
    [macro_id, ts] = block_value.split(";", 1)
    macro = env.airtable.get_macros(user_id)[int(macro_id)]

    await handle_execute_macro(user_id, macro, ts, client)


@app.action("create-macro")
async def handle_create_macro_view(
    ack: Callable[[], None], body: Dict[str, Any], client: AsyncWebClient
):
    await ack()
    await client.views_push(view=create_create_macro_modal(), trigger_id=body["trigger_id"])


@app.action("delete-macro")
async def handle_delete_macro_view(
    ack: Callable[[], None], body: Dict[str, Any], client: AsyncWebClient
):
    await ack()
    
    user_id: str = body["user"]["id"]
    block_value: str = body["actions"][0]["value"]
    [macro_id, ts] = block_value.split(";", 1)
    
    env.airtable.delete_macro(user_id, int(macro_id))
    view = create_macro_modal(ts, user_id)
    await client.views_update(view=view, trigger_id=body["trigger_id"], view_id=body["view"]["root_view_id"])


@app.view_submission("create_macro")
async def handle_create_macro_view_submission(
    ack: Callable[[], None], body: Dict[str, Any], client: AsyncWebClient
):
    await ack(response_action="clear")
    await create_macro(
        body["user"]["id"],
        body["view"]["state"]["values"]["name"]["name"]["value"],
        body["view"]["state"]["values"]["message"]["message"]["rich_text_value"],
        body["view"]["state"]["values"]["behaviour"]["behaviour"]["selected_option"]["value"] == "close"
    )


app_handler = AsyncSlackRequestHandler(app)

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.routing import Route

async def endpoint(req: Request):
    return await app_handler.handle(req)

queue_thread = Thread(target=process_queue, daemon=True).start()
api = Starlette(debug=True, routes=[Route("/slack/events", endpoint=endpoint, methods=["POST"]), Route("/ping", endpoint=ping, methods=['GET'])])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:api", host='0.0.0.0', port=env.port, log_level="info")
