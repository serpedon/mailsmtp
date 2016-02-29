#!/usr/bin/python3
import mailsmtp

smtp_server = 'smtp@example.com'
smtp_username = "testmail@example.com"
smtp_password = "pass"

mail_from = 'testmail@example.com'
mail_to = ['friend1@example.com', 'friend2@example.com' ]
subject="This is a test-Mail"
mail_body="""\
Test message from Michael
Best
Michael
"""
#mail_body_type = 'plain' # typical values for mail_body_type are plain, html, xml
attachments = ['Mailsmtp.py', 'mailsmtp-example.py' ]

gpg_recipient = [ '0x12345678', '0x01234567' ]

mailsmtp.mailsmtp(mail_from=mail_from, mail_to=mail_to, subject=subject, mail_body=mail_body, smtp_server=smtp_server, smtp_username=smtp_username, smtp_password=smtp_password, attachments=attachments, gpg_recipient=gpg_recipient )
 

