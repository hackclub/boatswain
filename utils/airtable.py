import dataclasses
import json
from typing import Any, Dict, List
from pyairtable import Api


@dataclasses.dataclass
class Macro:
    name: str
    message: Dict[str, Any]
    close: bool


class AirtableManager:
    def __init__(self, api_key: str, base_id: str):
        api = Api(api_key)
        self.people_table = api.table(base_id, "people")
        self.hs_people_table = api.table(base_id, "hs_people")
        self.fraud_data_table = api.table(base_id, "fraud_data")
        self.help_table = api.table(base_id, "help")
        self.macro_table = api.table(base_id, "macro")
        print("Connected to Airtable")

    def ping(self):
        try:
            self.people_table.first()
            return True
        except Exception as e:
            print(f"Error pinging Airtable: {e}")
            return False

    def create_person(self, first_name: str, last_name: str, email: str, slack_id: str):
        self.people_table.create(
            {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "slack_id": slack_id,
                "preexisting_user": True,
            }
        )

    def get_person(self, user_id: str):
        user = self.people_table.first(formula=f'{{slack_id}} = "{user_id}"')
        return user
    
    def get_macros(self, user_id: str) -> List[Macro]:
        macros = self.macro_table.first(formula=f'{{slack_id}} = "{user_id}"')
        
        if macros is None:
            return []
        else:
            assert macros["fields"]["version"] == 1
            return [Macro(**x) for x in json.loads(macros["fields"]["data"])]
        
    def insert_macro(self, user_id: str, macro: Macro):
        macro_dict = dataclasses.asdict(macro)
        macros = self.macro_table.first(formula=f'{{slack_id}} = "{user_id}"')
        
        if macros is None:
            person = self.get_person(user_id)
            assert person
            
            self.macro_table.create(
                {
                    "slack_id": user_id,
                    "version": 1,
                    "data": json.dumps([macro_dict]),
                    "person": [person["id"]]
                }
            )
        else:
            assert macros["fields"]["version"] == 1
            self.macro_table.update(
                macros["id"],
                {
                    "version": 1,
                    "data": json.dumps([*json.loads(macros["fields"]["data"]), macro_dict])
                }
            )
    
    def delete_macro(self, user_id: str, macro_id: int):
        macros = self.macro_table.first(formula=f'{{slack_id}} = "{user_id}"')
        assert macros
        macros_list = json.loads(macros["fields"]["data"])
        
        self.macro_table.update(
            macros["id"],
            {
                "version": 1,
                "data": json.dumps([x for i, x in enumerate(macros_list) if i != macro_id])
            }
        )

    def get_request(
        self, pub_thread_ts: str | None = None, priv_thread_ts: str | None = None
    ):
        if pub_thread_ts:
            req = self.help_table.first(formula=f'{{identifier}} = "{pub_thread_ts}"')
        elif priv_thread_ts:
            req = self.help_table.first(
                formula=f'{{internal_thread}} = "{priv_thread_ts}"'
            )
        else:
            return None

        return req

    def create_request(
        self, pub_thread_ts: str, content: str, user_id: str, priv_thread_ts: str
    ):
        print(f"Creating help request for user: {user_id}")
        linked_record = self.get_person(user_id)
        if not linked_record:
            print("User not found in airtable - HANDLE THIS")
            return None

        self.help_table.create(
            {
                "identifier": pub_thread_ts,
                "content": content,
                "person": [linked_record["id"]],
                "internal_thread": priv_thread_ts,
            }
        )
        return True

    def update_request(
        self,
        pub_thread_ts: str | None = None,
        priv_thread_ts: str | None = None,
        **updates: dict,
    ):
        req = self.get_request(
            pub_thread_ts=pub_thread_ts, priv_thread_ts=priv_thread_ts
        )
        if not req:
            return
        req = self.help_table.update(req["id"], updates)
        return req

    def resolve_request(self, priv_thread_ts: str, resolver: str):
        resolver_item = self.get_person(resolver)
        if not resolver_item:
            return
        id = resolver_item.get("id")
        req = self.get_request(priv_thread_ts=priv_thread_ts)
        if not req:
            return
        return self.help_table.update(
            req["id"], {"resolver": [id], "status": "resolved"}
        )

    def delete_req(self, pub_thread_ts: str):
        req = self.get_request(pub_thread_ts)
        if not req:
            return
        self.help_table.delete(req["id"])

    def get_fraud_data(self, user_id: str):
        fraud_data = self.fraud_data_table.all(formula=f'{{Slack ID}} = "{user_id}"')
        return fraud_data
    
    def get_hs_user(self, user_id: str):
        user = self.hs_people_table.first(formula=f'{{slack_id}} = "{user_id}"')
        return user