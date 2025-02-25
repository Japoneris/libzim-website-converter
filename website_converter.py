"""
Given a `_site/` with all pages / assets in, create .zim

a webpage should refer to style / assets using `href=/assets/`.
Otherwise, it should handle page relativity itself.
"""

import argparse
import os
from datetime import datetime


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

    load_path = args.site_path
    save_path = args.output_path
    os.makedirs(save_path, exist_ok=True)


    if load_path.endswith("/") == False:
        load_path = load_path + "/"
        
    l = len(load_path)

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
    
    info = None
    lst_unknown = [] # for unknown mime-type to add
    
    with Creator(os.path.join(save_path, filename + ".zim")).config_indexing(True, lang) as creator:
        # Assume main entry page is index.html
        creator.set_mainpath( "index.html")
        creator.add_illustration(48, illustration) # Add icon
        
        cnt = 0
        for subpath, _, files in os.walk(load_path):
            # Path, directories, files
            for file in files:
                cnt += 1
                filepath = os.path.join(subpath, file)
                relpath = filepath[l:] # Relative path within the website
                depth = relpath.count("/")
                title = file.rsplit(".", 1)[0]
                ext = relpath.rsplit(".", 1)[-1]

                
                if args.verbose:
                    print("Depth: {} \t{}".format(depth, relpath))
                    
                else:
                    # One line - progress
                    print("Processed {} files".format(cnt), end="\r")
                    
                item = None

                
                if ext in dic_mime:
                    mime = dic_mime[ext]
                    item = MyItem(title=title,
                         path=relpath,
                         fpath=filepath,
                        mimetype=mime)
                    
                elif filepath.endswith(".html") | filepath.endswith(".htm"):
                    # HTML file
                    data = None
                    with open(filepath, "r") as fp:
                        data = fp.read()

                    # Replace absolute reference by relative reference to get access to sources
                    data = data.replace('href="/', 'href="{}'.format("../" * depth))
                    data = data.replace('src="/', 'src="{}'.format("../" * depth))
                    data = data.replace('url(/', 'url({}'.format("../" * depth))
                    data = data.replace('url("/', 'url("{}'.format("../" * depth))

                    item = MyItem(title=title,
                           path=relpath,
                           content=data)
                else:
                    print("Unknown mimetype:", relpath)
                    lst_unknown.append(relpath.rsplit(".", 1)[-1])
                    
                    item = MyItem(title=title,
                            path=relpath,
                            fpath=filepath) # will be considered as html
                
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
