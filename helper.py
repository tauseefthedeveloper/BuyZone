import threading

def send_email_async(email_message):
    try:
        email_message.send(fail_silently=False)
    except Exception as e:
        print("EMAIL ERROR:", e)