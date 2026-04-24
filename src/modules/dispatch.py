import requests

class DispatchError(RuntimeError):
    pass

def build_dispatch_message(hotspot_name: str, coordinates: str, logistics_summary: dict) -> str:
    return (
        f"ALERT: Prioritize {hotspot_name} at {coordinates}. "
        f"Estimated trapped civilians: {logistics_summary['estimated_people_trapped']}. "
        f"Carry water: {logistics_summary['water_liters']}L, cots: "
        f"{logistics_summary['emergency_cots']}, medical kits: "
        f"{logistics_summary['medical_kits']}."
    )

def send_dispatch_sms(
    message: str,
    account_sid: str,
    auth_token: str,
    from_number: str,
    to_number: str,
) -> dict:
    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    
    payload = {
        "To": to_number,
        "From": from_number,
        "Body": message
    }
    
    response = requests.post(
        url,
        auth=(account_sid, auth_token),
        data=payload,
        timeout=15,
    )
    
    if not response.ok:
        raise DispatchError(f"Twilio API failed with status {response.status_code}: {response.text}")
        
    return response.json()
