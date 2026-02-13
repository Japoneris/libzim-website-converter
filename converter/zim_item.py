"""
ZIM Item wrapper class for libzim.
"""

from libzim.writer import Item, StringProvider, FileProvider, Hint, Blob


class MyItem(Item):
    """Custom Item implementation for ZIM archive creation."""

    def __init__(self, title, path, content="", fpath=None, mimetype="text/html"):
        super().__init__()
        self.path = path
        self.title = title
        self.content = content
        self.fpath = fpath
        self.mimetype = mimetype

    def get_path(self):
        return self.path

    def get_title(self):
        return self.title

    def get_mimetype(self):
        return self.mimetype

    def get_contentprovider(self):
        if self.fpath is not None:
            return FileProvider(self.fpath)

        if isinstance(self.content, bytes):
            return Blob(self.content)
        return StringProvider(self.content)

    def get_hints(self):
        return {Hint.FRONT_ARTICLE: True}
