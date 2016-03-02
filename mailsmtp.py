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

# constants
TLS = object()
STARTTLS = object()
PLAINTEXT = object()
PORT_25_OR_465 = object()

def mailsmtp(mail_from, mail_to, subject, mail_body, smtp_server, smtp_username, smtp_password, add_headers = dict(), attachments = [], mail_body_type = 'plain', smtp_security = TLS, smtp_check_certificate = True, smtp_port = PORT_25_OR_465, gpg_binary = 'gpg', gpg_options = [], gpg_recipient = [], gpg_sign = True) :
 
    if smtp_port == PORT_25_OR_465 :
        smtp_port = 465 if smtp_security == TLS else 25
    
    import sys
    import os
    import re
    import ssl
    
    from smtplib import SMTP_SSL       # this invokes the secure SMTP protocol (port 465, uses SSL)
    from smtplib import SMTP           # use this for standard SMTP protocol   (port 25, no encryption)
    
    from email.mime.audio import MIMEAudio
    from email.mime.base import MIMEBase
    from email.mime.image import MIMEImage
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from os.path import basename
    from email import encoders
    
    #For guessing MIME type based on file name extension
    import mimetypes
    
    import subprocess
    
    try:
        innerMsg = MIMEMultipart()
        innerMsg.attach(MIMEText(mail_body, mail_body_type))
    
        for path in attachments or []:
            # Guess the mail_body type based on the file's extension.  Encoding
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
                    attachinnerMsg = MIMEText(fp.read(), _subtype=subtype)
            elif maintype == 'image':
                with open(path, 'rb') as fp:
                    attachinnerMsg = MIMEImage(fp.read(), _subtype=subtype)
            elif maintype == 'audio':
                with open(path, 'rb') as fp:
                    attachinnerMsg = MIMEAudio(fp.read(), _subtype=subtype)
            else:
                with open(path, 'rb') as fp:
                    attachinnerMsg = MIMEBase(maintype, subtype)
                    attachinnerMsg.set_payload(fp.read())
                # Encode the payload using Base64
                encoders.encode_base64(attachinnerMsg)
        
            # Set the filename parameter
            attachinnerMsg.add_header('Content-Disposition', 'attachment', filename=basename(path))
            innerMsg.attach(attachinnerMsg)
    
        if gpg_recipient : 
            gpg_cmdline = [ gpg_binary ] + gpg_options + [ '--armor', '--encrypt' ] + ( [ '--sign' ] if gpg_sign else [] )
            for recipient in gpg_recipient :
                gpg_cmdline += ['--recipient', recipient]
            gpgProg = subprocess.Popen(gpg_cmdline, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
            gpgOut = gpgProg.communicate(innerMsg.as_bytes())
            if len(gpgOut[1]) > 0:
                raise Exception('GPG-call failed: ' + gpgOut[1].decode('utf-8'));
    
            outerMsg = MIMEMultipart(_subtype='encrypted', protocol="application/pgp-encrypted")
    
            encryptedMsgHeader = MIMEBase('application', 'pgp-encrypted')
            encryptedMsgHeader.set_payload('Version 1\n')
            outerMsg.attach(encryptedMsgHeader);
    
            encryptedMsg = MIMEBase('application', 'octet-stream',name="encrypted.asc")
            encryptedMsg.set_payload(gpgOut[0].decode('utf-8'))
            encryptedMsg.add_header('Content-Disposition', 'inline', filename='encrypted.asc')
    
            outerMsg.attach(encryptedMsg);
        else : # If there are no gpg-recipients given, the message in not encrypted and the inner message coincides with the outer message
            outerMsg = innerMsg
    
        outerMsg['From'] = mail_from
        outerMsg['Subject'] = subject
        outerMsg['To'] = ', '.join(mail_to);
        for header,value in add_headers.items() :
            outerMsg.add_header(header, value)
    
        ssl_context = ssl.create_default_context() if smtp_check_certificate else None
        if smtp_security == TLS :
            conn = SMTP_SSL(host=smtp_server, port=smtp_port, context=ssl_context)
        else :
            conn = SMTP(host=smtp_server, port=smtp_port)
            if smtp_security == STARTTLS :
                conn.starttls(context=ssl_context)
            elif smtp_security == PLAINTEXT :
                pass 
            else :
                raise ValueError("unknown value of argument 'smtp_security'")
    
        conn.set_debuglevel(False)
        conn.login(smtp_username, smtp_password)
        try:
            conn.sendmail(mail_from, mail_to, outerMsg.as_string())
        finally:
            conn.close()
    except Exception as exc:
        sys.exit( "mailsmtp failed; %s" % str(exc) ) # give a error message
