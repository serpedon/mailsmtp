#!/usr/bin/python3
# This work is licensed under CC BY-SA 3.0, https://creativecommons.org/licenses/by-sa/3.0/
# Author: Michael Walz <code@serpedon.de>, © 2016
# Originally based on material from (a) the python software foundation and (b) Vencent Marcetti:
# (a) Based on the email example of the python documention
#   https://docs.python.org/3.4/library/email-examples.html
#   license: PYTHON SOFTWARE FOUNDATION LICENSE VERSION 2, https://www.python.org/download/releases/3.4.0/license/
# (b) Based on an answer by Vincent Marchetti on stackoverflow.com
#   http://stackoverflow.com/questions/64505/sending-mail-from-python-using-smtp#64890
#   license: CC BY-SA 3.0, https://creativecommons.org/licenses/by-sa/3.0/


SMTPserver = 'smtprelaypool.ispgateway.de'
PORT = 465
sender =     'XXXXXXXX@XXXXXXXXXX.XX'
destination = ['XXXXXXXXXXXX@XXXX.XX', 'XXXXXXX@XXXXXXXX.XX' ]

USERNAME = "XXXXXXXX@XXXXXXXXXX.XX"
PASSWORD = "XXXXXXXX"

# typical values for text_subtype are plain, html, xml
text_subtype = 'plain'


content="""\
Test message from Michael
Gruß
Michael
"""

subject="This is a test-Mail"

attach=['mail.asc' ] 

attach = ['mail.py', 'encrypt' ]


import sys
import os
import re
import ssl

from smtplib import SMTP_SSL       # this invokes the secure SMTP protocol (port 465, uses SSL)
# from smtplib import SMTP                  # use this for standard SMTP protocol   (port 25, no encryption)

from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from os.path import basename
from email.utils import COMMASPACE
from email import encoders

#For guessing MIME type based on file name extension
import mimetypes

import subprocess

try:
    pgpMsg = MIMEMultipart()
    pgpMsg.attach(MIMEText(content, text_subtype))

    for path in attach or []:
        # Guess the content type based on the file's extension.  Encoding
        # will be ignored, although we should check for simple things like
        # gzip'd or compressed files.
        ctype, encoding = mimetypes.guess_type(path)
        if ctype is None or encoding is not None:
            # No guess could be made, or the file is encoded (compressed), so
            # use a generic bag-of-bits type.
            ctype = 'application/octet-stream'
        
        maintype, subtype = ctype.split('/', 1)
        if maintype == 'text':
            with open(path) as fp:
                # Note: we should handle calculating the charset
                attachpgpMsg = MIMEText(fp.read(), _subtype=subtype)
        elif maintype == 'image':
            with open(path, 'rb') as fp:
                attachpgpMsg = MIMEImage(fp.read(), _subtype=subtype)
        elif maintype == 'audio':
            with open(path, 'rb') as fp:
                attachpgpMsg = MIMEAudio(fp.read(), _subtype=subtype)
        else:
            with open(path, 'rb') as fp:
                attachpgpMsg = MIMEBase(maintype, subtype)
                attachpgpMsg.set_payload(fp.read())
            # Encode the payload using Base64
            encoders.encode_base64(attachpgpMsg)
    
        # Set the filename parameter
        attachpgpMsg.add_header('Content-Disposition', 'attachment', filename=basename(path))
        pgpMsg.attach(attachpgpMsg)

    gpgProg = subprocess.Popen('gpg --homedir /home/michael/Sicherheit/GnuPGKeys --sign --encrypt --armor -r 0xFE01CFB7'.split(), shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    gpgOut = gpgProg.communicate(pgpMsg.as_bytes())


    msg = MIMEMultipart(_subtype='encrypted', protocol="application/pgp-encrypted")
    msg['From'] = sender
    msg['Subject'] = subject
    msg['To'] = COMMASPACE.join(destination);

    encryptedMsg = MIMEBase('application', 'pgp-encrypted')
    encryptedMsg.set_payload('Version 1\n')
    msg.attach(encryptedMsg);

    encryptedMsg = MIMEBase('application', 'octet-stream',name="encrypted.asc")
    encryptedMsg.set_payload(gpgOut[0].decode('utf-8'))
    encryptedMsg.add_header('Content-Disposition', 'inline', filename='encrypted.asc')

    msg.attach(encryptedMsg);

    context = ssl.create_default_context()
    conn = SMTP_SSL(host=SMTPserver, port=PORT, context=context)
    conn.set_debuglevel(False)
    conn.login(USERNAME, PASSWORD)
    try:
        conn.sendmail(sender, destination, msg.as_string())
    finally:
        conn.close()

except Exception as exc:
    sys.exit( "mail failed; %s" % str(exc) ) # give a error message
