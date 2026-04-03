import pytest
from unittest.mock import MagicMock, patch
from email_service import EmailSender
import pandas as pd

@pytest.fixture
def email_sender():
    return EmailSender("test@gmail.com", "pass123")

def test_format_content_success(email_sender):
    row = pd.Series({'Name': 'John', 'Role': 'Engineer'})
    template = "Hi {{Name}}, role: {{Role}}"
    subject = "For {{Name}}"
    placeholders = ['Name', 'Role']

    fmt_subj, fmt_html = email_sender.format_content(row, template, subject, placeholders)
    
    assert fmt_subj == "For John"
    assert fmt_html == "Hi John, role: Engineer"

def test_format_content_missing_placeholder(email_sender):
    row = pd.Series({'Name': 'John', 'Role': ''})
    template = "Hi {{Name}}, role: {{Role}}"
    subject = "For {{Name}}"
    placeholders = ['Name', 'Role']

    fmt_subj, fmt_html = email_sender.format_content(row, template, subject, placeholders)
    
    assert fmt_subj is None
    assert fmt_html is None

@patch('smtplib.SMTP')
def test_connect(mock_smtp, email_sender):
    mock_instance = MagicMock()
    mock_smtp.return_value = mock_instance
    
    email_sender.connect()
    
    mock_smtp.assert_called_with('smtp.gmail.com', 587)
    mock_instance.starttls.assert_called_once()
    mock_instance.login.assert_called_with('test@gmail.com', 'pass123')

@patch('smtplib.SMTP')
def test_send_email(mock_smtp, email_sender):
    mock_instance = MagicMock()
    mock_smtp.return_value = mock_instance
    email_sender.connect()
    
    email_sender.send_email("target@test.com", "Subj", "<html>hi</html>")
    
    mock_instance.sendmail.assert_called_once()
    args, _ = mock_instance.sendmail.call_args
    assert args[0] == "test@gmail.com"
    assert args[1] == "target@test.com"
