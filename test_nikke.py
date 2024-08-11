import os
import base64
import pytest
from unittest.mock import patch, Mock
import httpx
from bs4 import BeautifulSoup
from datetime import datetime
from email.mime.text import MIMEText
from nikke import (fetch_page, parse_page, extract_items,
                   extract_date_from_item, check_date_in_current_month,
                   check_and_send_email, create_email_message,
                   send_email_message)


def test_fetch_page():
    url = "http://example.com"
    content = fetch_page(url)
    assert isinstance(content, bytes), "Fetched content is not in bytes"


def test_parse_page():
    html_content = '''
    <div id="CardList">
        <div class="layui-colla-item"></div>
    </div>
    '''
    card_list = parse_page(html_content)
    assert card_list is not None, "CardList element not found"


def test_extract_items():
    html_content = '''
    <div id="CardList">
        <div class="layui-colla-item">Item 1</div>
        <div class="layui-colla-item">Item 2</div>
    </div>
    '''
    card_list = parse_page(html_content)
    items = extract_items(card_list)
    assert len(items) == 2, "Incorrect number of items extracted"


def test_extract_date_from_item():
    html_content = '''
    <div class="layui-colla-item">
        <button>Button 1</button>
        <button>Button 2</button>
        <button>Button 3</button>
        <button> 2024年08月15日01时26分36秒 </button>
    </div>
    '''
    soup = BeautifulSoup(html_content, 'html.parser')
    item = soup.find("div", class_="layui-colla-item")
    date_text = extract_date_from_item(item)
    assert date_text == "2024年08月15日01时26分36秒", "Date extraction failed"


def test_check_date_in_current_month():
    current_month = datetime.now().strftime("%Y年%m月%d日%H时%M分%S秒")
    assert check_date_in_current_month(current_month) is True

    if datetime.now().month == 1:
        last_month = (datetime.now().replace(month=12,
                                             year=datetime.now().year -
                                             1)).strftime("%Y年%m月%d日%H时%M分%S秒")
    else:
        last_month = (datetime.now().replace(month=datetime.now().month -
                                             1)).strftime("%Y年%m月%d日%H时%M分%S秒")

    assert check_date_in_current_month(last_month) is False


@patch.dict(os.environ, {
    "EMAIL_USER": "test@example.com",
    "EMAIL_PASSWORD": "test_password"
})
def test_create_email_message():
    to_email = "recipient@example.com"
    date_text = "2024年08月15日01时26分36秒"
    url = "http://example.com"

    from_email, to_email_result, msg = create_email_message(
        to_email, date_text, url)

    assert from_email == "test@example.com"
    assert to_email_result == to_email
    assert msg['Subject'] == "New Entry Notification"

    encoded_body = msg.get_payload()

    if isinstance(encoded_body, str):
        decoded_body = base64.b64decode(encoded_body).decode('utf-8')
        assert url in decoded_body, "URL not found in the email body"
    else:
        raise ValueError("Email body is not a string or cannot be decoded.")
    assert url in decoded_body, "URL not found in the email body"


@patch.dict(os.environ, {
    "EMAIL_USER": "test@example.com",
    "EMAIL_PASSWORD": "test_password"
})
@patch('smtplib.SMTP_SSL')
def test_send_email_message(mock_smtp_ssl):
    from_email = os.getenv("EMAIL_USER")
    to_email = "recipient@example.com"
    msg = MIMEText("Test message")
    msg['Subject'] = "Test"

    send_email_message(from_email, to_email, msg)

    instance = mock_smtp_ssl.return_value
    instance.login.assert_called_once_with(from_email, "test_password")
    instance.sendmail.assert_called_once_with(from_email, to_email,
                                              msg.as_string())


@patch('httpx.get')
@patch.dict(os.environ, {
    "EMAIL_USER": "test@example.com",
    "EMAIL_PASSWORD": "test_password"
})
def test_check_and_send_email(mock_httpx_get):
    mock_response = Mock()
    mock_response.content = '''
    <div id="CardList">
        <div class="layui-colla-item">
            <button>Button 1</button>
            <button>Button 2</button>
            <button>Button 3</button>
            <button> 2024年08月15日01时26分36秒 </button>
        </div>
    </div>
    '''
    mock_httpx_get.return_value = mock_response

    with patch('nikke.send_email_message') as mock_send_email_message:
        check_and_send_email()
        mock_send_email_message.assert_called_once()


if __name__ == "__main__":
    pytest.main()
