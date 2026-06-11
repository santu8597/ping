# encoding: utf-8
import smtplib
import ssl
import socket
from email.message import EmailMessage
from smtplib import (SMTP, SMTP_SSL, SMTPException, SMTPRecipientsRefused,
                     SMTPSenderRefused, SMTPServerDisconnected)

from email.headerregistry import Address
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config_env import CONFIG
from services.mailing.mailer.exception import MessageFailedException, TransportExhaustedException, TransportFailedException


class Mailer(object):
    def __init__(self, from_email=None):
        # self.host = app.config['SMTP_SERVER']
        # self.port = app.config['SMTP_PORT']
        # self.username = app.config['SMTP_USERNAME']
        # self.password = app.config['SMTP_PASSWORD']
        self.host = CONFIG.EMAIL_HOST
        self.port = CONFIG.EMAIL_PORT
        self.username = CONFIG.EMAIL_HOST_USER
        self.password = CONFIG.EMAIL_HOST_PASSWORD
        self.from_email = from_email if from_email else CONFIG.DEFAULT_FROM_EMAIL
        self.connection = None
        if not self.connected:
            self.connect()

    def disconnect(self):
        if self.connected:
            try:
                self.connection.quit()
            except SMTPServerDisconnected:
                pass
            except (SMTPException, socket.error):
                raise SMTPException
            finally:
                self.connection = None

    # def connect(self):
    #     ssl_context = ssl.create_default_context()
    #     print(f'host: {self.host}......port: {self.port}.......data: {ssl_context}')
    #     connection = SMTP_SSL(
    #         host=self.host, port=self.port, context=ssl_context)
    #     connection.ehlo()
    #     connection.login(self.username, self.password)
    #     self.connection = connection

    def connect(self):
        """
        Connect to the Mailtrap SMTP server using STARTTLS.
        """
        ssl_context = ssl.create_default_context()  # Create a secure SSL context
        # print(f'Connecting to {self.host} on port {self.port} using STARTTLS...')

        try:
            # Use smtplib.SMTP to connect to the server
            self.connection = smtplib.SMTP(self.host, self.port)

            # Start the TLS encryption (secure connection)
            self.connection.starttls(context=ssl_context)

            # Login to the server with the provided credentials
            self.connection.login(self.username, self.password)
            print(f'Successfully connected to {self.host} with STARTTLS.')

        except smtplib.SMTPAuthenticationError as e:
            print(f"Authentication failed: {e}")
            raise  # Re-raise the exception for further handling
        except Exception as e:
            print(f"Error occurred while connecting: {e}")
            raise

    @property
    def connected(self):
        return getattr(self.connection, 'sock', None) is not None

    def send(self, data, recipients: list = [], cc: list = [], bcc: list = []):
        if not self.connected:
            self.connect()

        try:
            self.send_with_smtp(data, recipients, cc=cc, bcc=bcc)
        except Exception:
            raise TransportExhaustedException()

    def send_with_smtp(self, data, recipients: list = [], cc: list = [], bcc: list = []):
        try:
            # if 'recipient' in data:
            #     print("data.............", data)
            #     if len(data['recipient'])>1:
            #         recipient = data['recipient']
            #         recipients.append(recipient)
            #

            message = MIMEMultipart("alternative")
            message['Subject'] = data.get('subject')
            message['From'] = self.from_email
            message['To'] = ','.join(recipients)
            message['CC'] = ','.join(cc) if cc else ''
            message['BCC'] = ','.join(bcc) if bcc else ''
            # message.attach(MIMEText(data.get('plain_content'), 'plain'))
            message.attach(MIMEText(data.get('html_content'), 'html'))
            if cc:
                recipients.extend(cc)
            self.connection.sendmail(
                from_addr=self.from_email, to_addrs=recipients, msg=message.as_string())

        except SMTPSenderRefused as e:
            raise MessageFailedException(str(e))

        except SMTPRecipientsRefused as e:
            raise MessageFailedException(str(e))

        except SMTPServerDisconnected as e:
            raise TransportFailedException()

        except Exception as e:
            cls_name = e.__class__.__name__
            raise TransportFailedException()
