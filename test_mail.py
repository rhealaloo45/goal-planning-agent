import os, smtplib, ssl
from dotenv import load_dotenv
load_dotenv()

server = os.getenv("SMTP_SERVER")
port = int(os.getenv("SMTP_PORT", 465))
user = os.getenv("SMTP_USER")
passwd = os.getenv("SMTP_PASSWORD")

print(f"Testing {server}:{port} as {user}...")

try:
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(server, port, context=context) as s:
        s.login(user, passwd)
        print("LOGIN SUCCESS!")
        s.sendmail(user, user, "Subject: Test\n\nTesting from script.")
        print("MAIL SENT!")
except Exception as e:
    print(f"TEST FAILED: {e}")
