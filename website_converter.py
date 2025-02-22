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
    "pdf": "application/pdf",
    "css": "text/css",
    "svg": "image/svg+xml",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "xml": "application/xml",
}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("site_path", help="Path to the compiled website. Assume it ends with '/'")
    parser.add_argument("--output_path", default="zim", help="Path to the compiled website. Assume it ends with '/'")
    args = parser.parse_args()

    load_path = args.site_path
    save_path = args.output_path
    os.makedirs(save_path, exist_ok=True)


    if load_path.endswith("/") == False:
        load_path = load_path + "/"
        
    l = len(load_path)

    filename = input("zim name? ") or "test"

    print("For language code, see https://documentation.abes.fr/guide/html/formats/CodesLanguesISO639-3.htm") 
    lang = input("language? (eng | fra): ") or "eng"

    creator = input("Creator? ") or "unkown"
    description = input("Description?" ) or "This is a test or the field was left empty"
    title = input("Title? ") or "ABC-Test"

    current_date = datetime.today().strftime('%Y-%m-%d')
    
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
    with Creator(os.path.join(save_path, filename + ".zim")).config_indexing(True, lang) as creator:
        # Assume main entry page is index.html
        creator.set_mainpath( "index.html")
        for subpath, _, files in os.walk(load_path):
            # Path, directories, files
            for file in files:
                filepath = os.path.join(subpath, file)
                relpath = filepath[l:] # Relative path within the website
                depth = relpath.count("/")
                title = file.rsplit(".", 1)[0]
                ext = relpath.rsplit(".", 1)[-1]
                
                print("Depth: {} \t{}".format(depth, relpath))
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
                    data = data.replace('href="/', 'href="{}./'.format("../" * depth))

                    item = MyItem(title=title,
                           path=relpath,
                           content=data)
                else:
                    print("Unknown mimetype:", relpath)
                    
                    item = MyItem(title=title,
                            path=relpath,
                            fpath=filepath) # will be considered as html
                
                creator.add_item(item)
                
        print("== Add metadata ==")
        # metadata
        for name, value in dic_metadata.items():
            creator.add_metadata(name.title(), value)
            # .title() fx just uppercase the first letter
            
        print("== Quit ==")
    
