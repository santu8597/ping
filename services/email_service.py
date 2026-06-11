from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from config_env import CONFIG
from django.utils.html import strip_tags

# Import your custom User model from the 'user' app
from backend.users.models import CustomUser

class EmailHelper:
    def __init__(self, user: CustomUser, email_type: str = 'document', email_address: str = None, cc=None, bcc=None,
                 attachments=None, content: dict = None):
        """
        Initialize the EmailHelper class.
        :param user: CustomUser instance to use in the email (needed for dynamic content)
        :param email_type: Type of email (like OTP, welcome, password reset, etc.)
        :param email_address: The recipient email address
        :param cc: CC recipients
        :param bcc: BCC recipients
        :param attachments: Attachments to be sent
        :param content: Dictionary containing custom content for subject and body
        """
        self.user = user
        self.email_type = email_type
        self.cc = cc or []
        self.bcc = bcc or []
        self.attachments = attachments or []
        self.content = content

        if not self.user and email_address is None:
            raise ValueError("User or email address must be provided!")

        self.email_address = email_address or user.email
        self.email_content = self.prepare_email_content()

    def prepare_email_content(self):
        """
        Prepares email content based on the email type or provided custom content.
        :return: Dictionary with the email subject, body, and recipients
        """
        subject, html_content = self.get_template_for_email_type()

        # Custom content override
        if self.content and self.content.get("subject") and self.content.get("html_content"):
            subject = self.content.get("subject")
            html_content = self.content.get("html_content")

        plain_text_content = strip_tags(html_content)

        return {
            "recipient": self.email_address,
            "subject": subject,
            "html_content": html_content,
            "plain_text_content": plain_text_content,
            "cc": self.cc,
            "bcc": self.bcc,
            "attachments": self.attachments
        }

    def get_template_for_email_type(self):
        """
        Returns the subject and HTML content based on email type (like OTP, reset, etc.)
        """
        template_map = {
            'document': ('Your Document is Ready', 'email/document_template.html'),
            'reset': ('Password Reset Request', 'email/reset_template.html'),
            'welcome': ('Welcome to AIORI services portal', 'email/welcome_template.html'),
            'student_welcome': ('Welcome to AIORI services portal', 'email/student_welcome_template.html'),
            'otp': ('Your OTP Code', 'email/otp_template.html'),
            'reply_notification':("New Reply to Your Comment","email/reply_notification_template.html")
        }

        # Fetch the template and subject for the given email type
        template_name = template_map.get(self.email_type, ('Notification', 'email/default_template.html'))

        # Prepare context dynamically based on email type
        context = {'user': self.user}
        if self.email_type == 'otp':
            context['otp'] = self.content.get('otp')  # Add OTP only for 'otp' email type
        elif self.email_type == 'welcome':
            # Dynamically set the dashboard link
            current_host = CONFIG.HOST_URL or 'http://localhost:8000'  # Use environment variable or fallback to localhost
            context.update({
                'user_name': self.user.username,
                'dashboard_link': current_host,  # Use the dynamically determined host
                'user_email': self.user.email,
            })
        elif self.email_type == 'student_welcome':
            # Dynamically set the dashboard link
            current_host = CONFIG.HOST_URL or 'http://localhost:8000'  # Use environment variable or fallback to localhost
            context.update({
                'user_name': self.user.username,
                'dashboard_link': current_host,  # Use the dynamically determined host
                'user_email': self.user.email,
                'faculty': self.content.get('faculty_name', ''),
                # 'content': self.content.get('student_password', ''),
                'reset_link': self.content.get('reset_link', '')
            })
        elif self.email_type == 'reset':
            # Expecting 'reset_link' in content dict when email_type='reset'
            context['reset_link'] = self.content.get('reset_link')
        elif self.email_type == 'reply_notification':
            # Expecting 'reset_link' in content dict when email_type='reset'
            print("reply_notification_template_selected", self.content.get('reply'))
            context.update({
            'comment_owner_name': self.user.get_name(),
            'reply' : self.content.get('reply'),
            'discussion_link':"#"
            })

        # Render the HTML content using the template
        html_content = render_to_string(template_name[1], context)

        return template_name[0], html_content

    def send_email(self):
        """
        Sends the email after the content is prepared.
        """
        try:
            email = EmailMessage(
                self.email_content['subject'],  # Subject
                self.email_content['html_content'],  # HTML Body
                CONFIG.DEFAULT_FROM_EMAIL,
                [self.email_content['recipient']],  # To email address
                self.email_content['cc'],  # CC
                self.email_content['bcc'],  # BCC
            )

            # Attachments
            for attachment in self.email_content['attachments']:
                email.attach(attachment['name'], attachment['content'], attachment['mime_type'])

            email.content_subtype = "html"  # Set email type to HTML

            # Send email
            email.send()

            return {"status": "success", "message": "Email sent successfully."}
        except Exception as e:
            return {"status": "error", "message": f"Failed to send email: {str(e)}"}
