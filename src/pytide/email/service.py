from email.message import EmailMessage
from email.utils import make_msgid
from pathlib import Path
from smtplib import SMTP

from jinja2 import Environment, FileSystemLoader

from pytide.models.image import Image
from pytide.models.station import Station


def create_message(stations: list[Station], save_html: bool, save_email: bool) -> EmailMessage:
    current_folder = Path(__file__).parent

    with open(current_folder / 'assets' / 'img' / 'logo-192.png', 'rb') as file:
        logo_image = file.read()

    logo = Image(logo_image, make_msgid('pytide-logo'))

    plain_text_body = '\n\n'.join(str(station) for station in stations)

    html_body: str = __render_template(
        current_folder / 'templates',
        'bootstrap-email-template.html',
        stations,
        logo,
    )

    project_root = current_folder.parents[2]

    if save_html:
        output_path = project_root / 'message.html'
        output_path.write_text(html_body, encoding='utf-8')

    attachments = [logo]

    for station in stations:
        attachments.append(station.map_image)

    message = __compose_message('Daily Tide Report', plain_text_body, html_body, attachments)

    if save_email:
        output_path = project_root / 'message.eml'
        output_path.write_text(message.as_string(), encoding='utf-8')

    return message


def send_message(message: EmailMessage, recipients: set[str], smtp_settings: dict[str, str]) -> None:
    message['From'] = smtp_settings['sender']

    with SMTP(smtp_settings['host'], int(smtp_settings['port'])) as connection:
        connection.starttls()
        connection.login(smtp_settings['user'], smtp_settings['password'])

        for address in recipients:
            if not message['To']:
                message['To'] = address
            else:
                message.replace_header('To', address)

            connection.send_message(message)


def __render_template(templates_path: Path, template_name: str, stations: list[Station], logo: Image) -> str:
    jinja_env = Environment(loader=FileSystemLoader(templates_path), autoescape=True)

    email_template = jinja_env.get_template(template_name)

    return email_template.render(tide_stations=stations, logo=logo)


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
