"""
Given a `_site/` with all pages / assets in, create .zim

a webpage should refer to style / assets using `href=/assets/`.
Otherwise, it should handle page relativity itself.


"""

import argparse
import re
from datetime import datetime
from pathlib import Path

from libzim.writer import Creator, Item, StringProvider, FileProvider, Hint



# Class provided in python openzim documentation
class MyItem(Item):
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
        return self.mimetype #"text/html"

    def get_contentprovider(self):
        if self.fpath is not None:
            return FileProvider(self.fpath)
            
        return StringProvider(self.content)

    def get_hints(self):
        return {Hint.FRONT_ARTICLE: True}


# Get the list here if necessary:
# https://developer.mozilla.org/fr/docs/Web/HTTP/MIME_types/Common_types

dic_mime = {
    "bin": "application/octet-stream",
    "bmp": "image/bmp",
    "bz":  "application/x-bzip",
    "bz2": "application/x-bzip2",
    "pdf": "application/pdf",
    "css": "text/css",
    "csv": "text/csv",
    "doc": "application/msword",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "epub": "application/epub+zip",
    "gif": "image/gif",
    "ico": "image/x-icon",
    "ics": "text/calendar",
    "jar": "application/java-archive",
    "js":  "application/javascript",
    "json": "application/json",
    "mid": "audio/midi",
    "midi": "audio/midi",
    "mpeg": "video/mpeg",
    "mp4": "video/mp4",
    "odp": "application/vnd.oasis.opendocument.presentation",
    "ods": "application/vnd.oasis.opendocument.spreadsheet",
    "odt": "application/vnd.oasis.opendocument.text",
    "otf": "font/otf",
    "ppt": "application/vnd.ms-powerpoint",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "rar": "application/x-rar-compressed",
    "scss": "text/x-scss",
    "sh": "application/x-sh",
    "svg": "image/svg+xml",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "xml": "application/xml",
    "tif": "image/tiff",
    "tif": "image/tiff",
    "txt": "text/plain",
    "ts":  "application/typescript",
    "ttf": "font/ttf",
    "wav": "audio/x-wav",
    "webp": "image/webp",
    "xls": "application/vnd.ms-excel",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "xml": "application/xml",
    "zip": "application/zip",
    
    
}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("site_path", help="Path to the compiled website. Assume it ends with '/'")
    parser.add_argument("--output_path", default="zim", help="Path to the compiled website. Assume it ends with '/'")
    parser.add_argument("--icon", default="icons/comment.png", help="Path to zim icon.") # easier than using `input()`
    parser.add_argument("--verbose", action="store_true", default=False, help="If turn on, print all files.") # easier than using `input()`
    args = parser.parse_args()

    load_path = Path(args.site_path)
    save_path = Path(args.output_path)
    save_path.mkdir(parents=True, exist_ok=True)

    filename = input("zim name? \t") or "test"

    print("For language code, see https://documentation.abes.fr/guide/html/formats/CodesLanguesISO639-3.htm") 
    lang = input("language? (eng | fra): \t") or "eng"

    creator = input("Creator? \t") or "unkown"
    description = input("Description? \t") or "This is a test or the field was left empty"
    title = input("Title?  \t") or "ABC-Test"

    current_date = datetime.today().strftime('%Y-%m-%d')

    illustration = None
    with open(args.icon, "rb") as fp:
        illustration = fp.read()
    
    dic_metadata = {
            "creator": creator,
            "description": description,
            "name": "my-blog-test",
            "publisher": "You",
            "title": title,
            "language": lang,
            "date": current_date,
        }
    
    print("=== Building ===")

    lst_unknown = [] # for unknown mime-type to add
    lst_missing_index = [] # for links ending with / but no index.html exists
    
    with Creator(str(save_path / f"{filename}.zim")).config_indexing(True, lang) as creator:
        # Assume main entry page is index.html
        creator.set_mainpath( "index.html")
        creator.add_illustration(48, illustration) # Add icon
        
        cnt = 0
        for filepath in load_path.rglob("*"):
            # Skip directories, only process files
            if not filepath.is_file():
                continue

            cnt += 1
            relpath = str(filepath.relative_to(load_path))
            depth = relpath.count("/")
            title = filepath.stem
            ext = filepath.suffix.lstrip(".")

            if args.verbose:
                print("Depth: {} \t{}".format(depth, relpath))
            else:
                # One line - progress
                print("Processed {} files".format(cnt), end="\r")

            # experimental
            ext = ext.lower()

            if ext in dic_mime:
                mime = dic_mime[ext]
                item = MyItem(title=title,
                     path=relpath,
                     fpath=str(filepath),
                    mimetype=mime)

            elif str(filepath).endswith(".html") or str(filepath).endswith(".htm"):
                # HTML file
                with open(filepath, "r", encoding="utf-8", errors="replace") as fp:
                    data = fp.read()

                # Replace absolute reference by relative reference to get access to sources
                data = data.replace('href="/', 'href="{}'.format("../" * depth))
                data = data.replace('src="/', 'src="{}'.format("../" * depth))
                data = data.replace('url(/', 'url({}'.format("../" * depth))
                data = data.replace('url("/', 'url("{}'.format("../" * depth))

                # Check and replace links ending with / to /index.html only if index.html exists
                def check_and_replace_index(match):
                    link = match.group(1)  # Get the path before the /"
                    # Construct the absolute path to check
                    index_path = load_path / link.lstrip('/') / 'index.html'

                    if index_path.exists():
                        return link + '/index.html"'
                    else:
                        # Collect warning for missing index
                        warning_msg = f"{relpath} -> Link '{link}/' has no index.html"
                        if warning_msg not in lst_missing_index:
                            lst_missing_index.append(warning_msg)
                        return link + '/"'  # Keep original link

                # Replace only verified index pages
                data = re.sub(r'((?:href="|src=")(?:\.\./)*[^"]*/)(?=")', check_and_replace_index, data)

                item = MyItem(title=title,
                       path=relpath,
                       content=data)
            else:
                print("Unknown mimetype:", relpath)
                lst_unknown.append(relpath.rsplit(".", 1)[-1])

                item = MyItem(title=title,
                        path=relpath,
                        fpath=str(filepath)) # will be considered as html

            creator.add_item(item)

        print("=== Add metadata ===")
        # metadata
        for name, value in dic_metadata.items():
            creator.add_metadata(name.title(), value)
            # .title() fx just uppercase the first letter

        print("== Quit ==> Compiling (This operation takes time, more than just looking at files) ==")

    print("== Done ! ==")
    print("Missing mimetypes:")
    print(", ".join(sorted(set(lst_unknown))))

    if lst_missing_index:
        print("\n=== WARNING: Links ending with / but no index.html found ===")
        for warning in lst_missing_index:
            print(warning)
