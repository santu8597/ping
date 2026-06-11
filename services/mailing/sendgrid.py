import base64
import os
import traceback
from typing import List
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition, Personalization, Cc, Bcc, To

from config_env import CONFIG

class SendGrid:

    def __init__(self) -> None:
        self.sg: SendGridAPIClient = None
        self.mail: Mail = None


        self.init_sg()

    def init_sg(self):
        self.from_email = CONFIG.SMTP_FROM
        if not self.from_email:
            raise ValueError(f"No send address found please set a send address")

        self.sg = SendGridAPIClient(CONFIG.SENDGRID_API_KEY)

    def prepare_mail(self,  email_data, recipient, cc:List[str]=[], bcc:List[str]=[], attachments:List[dict]=[] ):
        mail = Mail(
        from_email= self.from_email,
        

        subject=email_data.get('subject'),
        # to_emails=recipient,
        html_content=email_data.get('html_content'))
        # print(email_data)
        per = Personalization()
        per.add_to(To(recipient))

        for cc_address in cc:
            per.add_cc(Cc(cc_address))

        for bcc_address in bcc:
            per.add_bcc(Bcc(bcc_address))

        for attach in attachments:
            self.attach_file(message=mail, attach=attach)

        mail.add_personalization(per)
        self.mail = mail

    def send(self, data, recipients, cc:List[str]=[], bcc:List[str]=[], attachments:List[dict]=[]):
        """
        email_data: dict, keys subject, html_content
        recipient: email address
        cc: list of email address
        bcc: list of email address
        attachments: list of dict containing file information
        """
        response = None
        try:
            # print(recipients)
            self.prepare_mail(email_data=data, recipient=recipients, cc=cc, bcc=bcc, attachments=attachments)
            # print("Raw Email Data", self.mail)
            response = self.sg.send(self.mail)
            self.mail = None
        except Exception as e:
            print("Sendgrid Response", response)
            traceback.print_exc()
            raise


    def attach_file(self, message: Mail, attach:dict):
        file_path = attach['path']
        file_name = attach['name']
        file_type = attach.get('type', 'pdf')
        if not os.path.isfile(file_path):
            raise FileNotFoundError(
                f'File not found on system path {file_path}')

        with open(file_path, 'rb') as f:
            data = f.read()
            f.close()
            encoded_file = base64.b64encode(data).decode()

            attached_file = Attachment(
                FileContent(encoded_file),
                FileName(file_name),
                FileType(f'application/{file_type}'),
                Disposition('attachment')
            )
            message.attachment = attached_file
    
    def log_email(self):
        pass