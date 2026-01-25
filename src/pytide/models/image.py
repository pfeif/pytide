"""
Class for image data
"""

from typing import NamedTuple


class Image(NamedTuple):
    """An image attachment for an email"""

    image: bytes
    content_id: str
    maintype: str = 'image'
    subtype: str = 'png'
