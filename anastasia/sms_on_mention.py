import smtplib
import os

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv



load_dotenv()
SMS_EMAIL = os.getenv("SMS_EMAIL")
SMS_PASS = os.getenv("SMS_PASS")

def send_text(phone, carrier_gateway, body):
    email = SMS_EMAIL
    pas = SMS_PASS
    # email = os.getenv("SMS_EMAIL")
    # pas = os.getenv("SMS_PASS")
    smtp = "smtp.gmail.com"
    port = 587
    sms_gateway = "{}{}".format(phone, carrier_gateway)
    server = smtplib.SMTP(smtp, port)
    server.starttls()
    server.login(email, pas)
    # now we use the MIME module to structure our message.
    msg = MIMEMultipart()
    msg['From'] = email
    msg['To'] = sms_gateway
    # Make sure you add a new line in the subject
    msg['Subject'] = "vidyagaymers\n"
    wrapped_body = "{}\n".format(body)
    # wrapped_body = textwrap.fill(body,width=15)
    # and then attach that body furthermore you can also send html content
    msg.attach(MIMEText(wrapped_body, 'plain'))
    sms = msg.as_string()
    server.sendmail(email, sms_gateway, sms)
    # quit the server
    server.quit()

