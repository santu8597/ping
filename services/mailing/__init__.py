import re
import traceback
from config_env import CONFIG
from services.mailing.mailer import Mailer
from services.mailing.sendgrid import SendGrid
from django.template.loader import render_to_string

class Mailing:
    def __init__(self, email_type: str = 'document', from_email=None, email_address: str = None, cc=None, bcc=None,
                 attachments=None, content:dict=None):
        self.email_type = email_type
        self.mailer: Mailer | SendGrid = None
        self.cc = cc or []
        self.bcc = bcc or []
        self.attachments = attachments or []
        self.content = content
        self.email_address = email_address
        self.email_content = self.prepare_email_content()
        self.from_email = from_email

        self.init_mailer()

    def init_mailer(self):
        try:
            if CONFIG.EMAIL_SERVER == 'SMTP':
                self.mailer = Mailer(from_email=self.from_email)  # Initialize the Mailer instance
            elif CONFIG.EMAIL_SERVER == 'SENDGRID':
                self.mailer = SendGrid()
                
        
        except Exception as e:
            raise TypeError("Unable to initialize mailer!") from e


    def prepare_email_content(self):
        """
        Prepare the email content based on email_type and the user object.
        """
        if self.content and self.content.get("subject") and self.content.get("html_content"):
            subject = self.content.get("subject")
            html_content = self.content.get("html_content")
        else:
            # Call get_template_for_email_type only if needed
            subject, html_content = self.get_template_for_email_type()

        # Use the provided content if available, otherwise the rendered template
        subject = self.content.get("subject") if self.content and self.content.get("subject") else subject

        html_content = self.content.get("html_content") if self.content and self.content.get(
            "html_content") else html_content
        # print("template data......................", subject)
        return {
            "recipient": self.email_address,
            "subject": subject,  # Extracted directly from template
            "html_content": html_content,  # Rendered HTML content
            "cc": self.cc,
            "bcc": self.bcc,
            "attachments": self.attachments
        }

    def get_template_for_email_type(self):
        """
        Return the subject and the HTML content based on the email type.
        The subject and content are extracted directly from the HTML template.
        """
        template_map = {
            'document': ('Your Document is Ready', 'document_template.html'),
            'reset': ('Password Reset Request', 'reset_template.html'),
            'welcome': ('Welcome to AIORI Service Portal', 'welcome_template.html'),
            'otp': ('Your OTP Code', 'email/otp_template.html'),

        }

        # Retrieve the template and subject for the given email type
        template = template_map.get(self.email_type, ('Notification', 'default_template.html'))
        subject = template[0]
        template_name = template[1]
        # Render the HTML content using the template (you can adjust as necessary)
        # html_content = render_template(template_name, user=self.user)
        # Prepare context dynamically based on email type
        context = {}
        if self.email_type == 'otp':
            otp = self.content.get('otp')  # Add OTP only for 'otp' email type
            subject = f'AIORI Service Portal | Your One Time Password | {otp}'
            context['otp'] = otp
            html_content = render_to_string(template_name, context)

        else:
            html_content = "<p> This is test </p>"

        return subject, html_content

    def send_email(self):
        """
        Send the email after the content is prepared.
        """
        try:
            # Send the email using the Mailer instance
            self.mailer.send(
                data=self.email_content,  # This will use the prepared email content
                recipients=[self.email_content['recipient']],  # Recipient from the prepared data
                cc=self.email_content['cc'],  # CC from the prepared data
                bcc=self.email_content['bcc']  # BCC from the prepared data
            )
            print('email sent')
            return {"status": "success", "message": "Email sent successfully."}
        except Exception as e:
            traceback.print_exc()
            raise e 
            # return {"status": "error", "message": f"Failed to send email: {str(e)}"}
