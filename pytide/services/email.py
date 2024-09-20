"""
Functions for creating and sending emails
"""
import os
from email.message import EmailMessage
from email.utils import make_msgid
from smtplib import SMTP

from jinja2 import Environment, FileSystemLoader
from models.image import Image
from models.station import Station


def create_message(source_dir: str, stations: list[Station], save_html: bool, save_email: bool) -> EmailMessage:
    """
    Return one EmailMessage containing data from each station in stations.

    :param str source_dir: The root of the source code directory
    :param list[Station] stations: The list of stations used to populate the email
    :param bool save_html: Whether to save the email body HTML locally
    :param bool save_email: Whether to save the email message locally

    :returns: The email message without sender or recipient information
    :rtype: EmailMessage
    """
    logo_path = os.path.join(source_dir, 'assets', 'img', 'logo-192.png')

    with open(logo_path, 'rb') as file:
        logo_image = file.read()

    logo = Image(logo_image, make_msgid('pytide-logo'))

    plain_text_body = '\n\n'.join(str(station) for station in stations)

    html_body: str = __render_template(
        os.path.join(source_dir, 'templates'),
        'bootstrap-email-template.html',
        stations,
        logo.content_id)

    if save_html:
        output_path = os.path.join(source_dir, '..', 'message.html')

        with open(output_path, mode='wt', encoding='utf-8') as file:
            file.writelines(html_body)

    attachments = [logo]

    for station in stations:
        attachments.append(station.image)

    message = __compose_message('Your customized Pytide report', plain_text_body, html_body, attachments)

    if save_email:
        output_path = os.path.join(source_dir, '..', 'message.eml')

        with open(output_path, mode='wt', encoding='utf-8') as file:
            file.writelines(message.as_string())

    return message


def send_message(message: EmailMessage, recipients: set[str], smtp_settings: dict[str, str]) -> None:
    """
    Send message to each recipient in recipients using smtp_settings.

    :param EmailMessage message: The message to send
    :param set[str] recipients: The message recipients
    :param dict[str, str] smtp_settings: The user's email server settings
    """
    message['From'] = smtp_settings['sender']

    with SMTP(smtp_settings['host'], int(smtp_settings['port'])) as connection:
        # Enter TLS mode. Everything from here, on is encrypted.
        connection.starttls()
        connection.login(smtp_settings['user'], smtp_settings['password'])

        for address in recipients:
            if not message['To']:
                message['To'] = address
            else:
                message.replace_header('To', address)

            connection.send_message(message)


def __render_template(templates_path: str, template_name: str, stations: list[Station], logo_cid: str) -> str:
    """
    Return a rendered email template as an HTML string.

    :param str templates_path: The directory containing the template
    :param str template_name: The name of the template to render
    :param Station stations: The list of stations to render HTML for
    :param str logo_cid: The content ID of the logo

    :returns: The rendered HTML template
    :rtype: str
    """
    jinja_env = Environment(
        loader=FileSystemLoader(templates_path),  # sets the templates directory
        autoescape=True)  # prevents cross-site scripting

    email_template = jinja_env.get_template(template_name)

    html_body = email_template.render(tide_stations=stations, logo_cid=logo_cid)

    return html_body


def __compose_message(subject: str, plain_text: str, html_body: str, image_attachments: list[Image]) -> EmailMessage:
    """
    Return one EmailMessage containing data from each station in stations.

    :param str subject: The email subject
    :param str plain_text: The HTML-free, plain text body of the email
    :param str html_body: The HTML body of the email
    :param list[ImageAttachment] image_attachments: A collection of images to attach to the email

    :returns: The email message without sender or recipient information
    :rtype: EmailMessage
    """
    # The EmailMessage class is unnecessarily complicated, but behind the scenes, it automagically
    # sets header information and mutates the message structure to fit our needs.
    message = EmailMessage()
    message['Subject'] = subject
    message.set_content(plain_text)
    message.add_alternative(html_body, subtype='html')

    # Trust me here. Just give this method raw image bytes, ensure sure the string passed as cid has
    # angle brackets around it, and definitely make sure those angle brackets are stripped from the
    # cid in the HTML. Everything should be just fine.
    for image in image_attachments:
        message.add_attachment(image.image, maintype=image.maintype, subtype=image.subtype, cid=image.content_id)

    return message
