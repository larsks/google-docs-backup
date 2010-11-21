#!/usr/bin/python

import os
import sys
import optparse

from configdict import ConfigDict
import gdocs

def parse_args():
    p = optparse.OptionParser()
    p.add_option('-c', '--config')
    p.add_option('-u', '--user')
    p.add_option('-p', '--password', '--pass')
    p.add_option('-f', '--folder')
    p.add_option('-k', '--create', action='store_true')
    p.add_option('--convert', action='store_true')
    p.add_option('-t', '--mime-type',
            default='text/plain')
    p.add_option('--include-dotfiles', action='store_true')
    return p.parse_args()

def upload_file (g, opts, src, folder=None):

    print 'Uploading', src
    res = g.upload(src, mimetype=opts.mime_type, folder=folder,
            convert=opts.convert)

def upload_dir (g, opts, src, folder=None):
    for dirpath, dirnames, filenames in os.walk(src):
        for filename in filenames:
            if filename.startswith('.') and not opts.include_dotfiles:
                continue

            filepath = os.path.join(dirpath, filename)
            upload_file(g, opts, filepath, folder=folder)

        for dirname in dirnames[:]:
            if dirname.startswith('.') and not opts.include_dotfiles:
                dirnames.remove(dirname)

def main():
    opts, args = parse_args()

    cf = ConfigDict()

    if opts.config:
        cf.parse(opts.config)

    if opts.user is None:
        opts.user = cf['google']['user']

    if opts.password is None:
        opts.password = cf['google']['pass']

    if opts.user is None or opts.password is None:
        print >>sys.stderr, 'Missing required authentication information.'
        sys.exit(1)

    g = gdocs.GoogleDocs(credentials={
        'user': opts.user,
        'pass': opts.password,
        })

    g.login()

    folder = None
    if opts.folder:
        try:
            folder = g.title(opts.folder)
        except KeyError:
            if opts.create:
                folder = g.create_folder(opts.folder)
            else:
                print >>sys.stderr, 'ERROR: Destination folder ' \
                    '"%s" does not exist."' % opts.folder
                sys.exit(1)

    for src in args:
        if os.path.isdir(src):
            upload_dir(g, opts, src, folder=folder)
        else:
            upload_file(g, opts, src, folder=folder)

if __name__ == '__main__':
    main()

