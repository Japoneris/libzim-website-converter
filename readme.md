# Transform a static website into a ZIM file

Here, we use [python libzim](https://github.com/openzim/python-libzim) to create a zim file, which use `openzim` under the hood.

## How to use?

Simple:

1. `pip install libzim` (no `requirements.txt` for a single file)
2. `python3 website_converter <path/to/_site/>`. The script will ask you additional metadata to create the zim file.
3. Next, you can add the zim file to [`kiwix`](https://kiwix.org/)

## Target websites: 

Static websites, as it can be generated with [jekyll](https://jekyllrb.com/)


## Why not using libzim directly?

Viewer/hoster like `kiwix` uses relative path.
For instance, if a webpage asks for `<site_base_path>/assets/myfile.txt`, it is transformed into `<kiwix_url>/myzimfilename/content/assets/myfile.txt`. 

Therefore, there are two options (at least):

- when coding the website, access to resources using relative path only
- convert all absolute paths to relative path based on document depth (the option we follow)

# TODO / Warnings

- [ ] Support for linux path OK, Windows KO
- [ ] Does not support permalinks (i.e., if `/about/` maps to `about.html`, the redirect is likely to fail (due to the zim hoster)
- [ ] **MIMETypes**: By default, `text/hml`. In the script, there is a dictionary `dic_mime` where you can add new mimetype. Currently, we support `css,  jpg, html, pdf, png, svg, xml`. The script will tell you which extensions were not recognized.
- [ ] See how to add an icon as metadata / illustration
