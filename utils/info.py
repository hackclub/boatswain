from utils.env import env

def get_user_info(user_id: str):
    hs_user = env.airtable.get_hs_user(user_id) or {}
    fraud_data = env.airtable.get_fraud_data(user_id) or {}
    
    stage = hs_user.get("fields", {}).get("stage", "unknown").replace("_", " ").title()
    verification_status = hs_user.get("fields", {}).get("verification_status", ["Not submitted"])[0]
    
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
    
    return [
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"""
*:face_with_monocle: User Data for <@{user_id}>:*
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