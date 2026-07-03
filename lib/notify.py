from twilio.rest import Client

ACCOUNT_SID = "YOUR_SID"
AUTH_TOKEN = "YOUR_TOKEN"

client = Client(ACCOUNT_SID, AUTH_TOKEN)

TWILIO_WHATSAPP = "whatsapp:+14155238886"


def send_whatsapp(number, message):
    # number MUST include country code
    return client.messages.create(
        from_=TWILIO_WHATSAPP,
        body=message,
        to=f"whatsapp:{number}"
    )


def send_sms(number, message):
    return client.messages.create(
        from_="+1234567890",
        body=message,
        to=number
    )