import os
import httpx
from bs4 import BeautifulSoup
from datetime import datetime
import smtplib
from email.mime.text import MIMEText


def fetch_page(url):
    response = httpx.get(url)
    response.raise_for_status()
    return response.content


def parse_page(content):
    soup = BeautifulSoup(content, 'html.parser')
    return soup.find(id="CardList")


def extract_items(card_list):
    return card_list.find_all("div", class_="layui-colla-item")


def extract_date_from_item(item):
    buttons = item.find_all("button")
    if len(buttons) >= 4:
        return buttons[3].get_text().strip()
    return None


def check_date_in_current_month(date_text):
    try:
        date = datetime.strptime(date_text, "%Y年%m月%d日%H时%M分%S秒")
        now = datetime.now()
        return date.year == now.year and date.month == now.month
    except ValueError:
        return False


def create_email_message(to_email, date_text, url):
    from_email = os.getenv("EMAIL_USER")
    subject = "New Entry Notification"
    body = f"A new entry was created this month: {date_text}\n\nYou can check it here: {url}"

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email

    return from_email, to_email, msg


def send_email_message(from_email, to_email, msg):
    password = os.getenv("EMAIL_PASSWORD", "")
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(from_email, password)
        server.sendmail(from_email, to_email, msg.as_string())
        server.quit()
        print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")


def check_and_send_email():
    my_mail = os.getenv("EMAIL_USER")
    url = "http://1.12.63.131/12/index.php?m=Index&a=search&search=&order=xfkq&dq=&jsk%5B0%5D=161&jsk%5B2%5D=163"

    print("Starting the email check and send process...")

    content = fetch_page(url)
    card_list = parse_page(content)
    if not card_list:
        print("No CardList found on the page.")
        return

    items = extract_items(card_list)
    for item in items:
        date_text = extract_date_from_item(item)
        if date_text and check_date_in_current_month(date_text):
            from_email, to_email, msg = create_email_message(my_mail, date_text, url)
            send_email_message(from_email, to_email, msg)
            print("Process completed successfully.")
            return

    print("No matching dates found. No email was sent.")
