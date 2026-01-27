from typing import NamedTuple


class Image(NamedTuple):
    image: bytes
    content_id: str
    maintype: str = 'image'
    subtype: str = 'png'

    @property
    def content_id_normalized(self) -> str:
        return self.content_id.strip('<>')
