#!/usr/bin/python

# feed = client.GetDocList(uri='/feeds/default/private/full/-/{http://schemas.google.com/g/2005#kind}application/msword')

import os
import sys
import optparse
import urllib
import httplib

import gdata.service
import gdata.docs.client
import gdata.docs.service

from configdict.configdict import ConfigDict

GOOGLE_MIME_TYPE_SCHEMA = '{http://schemas.google.com/g/2005#kind}'

def parse_args():
    p = optparse.OptionParser()
    p.add_option('-c', '--config')
    p.add_option('-u', '--user')
    p.add_option('-p', '--password', '--pass')
    p.add_option('-f', '--folder')
    p.add_option('-t', '--type', action='append',
            help='Retrieve only documents of type TYPE.  ')
    p.add_option('-q', '--query')
    p.add_option('-d', '--destination', default='.')
    p.add_option('-D', '--download', action='store_true')

    return p.parse_args()

def main():
    opts,args = parse_args()

    if opts.download and not os.path.isdir(opts.destination):
        print >>sys.stderr, 'Destination "%s" does not exist.' % opts.destination
        sys.exit(1)

    cf = ConfigDict()
    query = \
    gdata.docs.service.DocumentQuery(feed='/feeds/default')

    if opts.config:
        cf.parse(opts.config)

    if opts.user is None:
        opts.user = cf['google']['user']

    if opts.password is None:
        opts.password = cf['google']['pass']

    if opts.user is None or opts.password is None:
        print >>sys.stderr, 'Missing required authentication information.'
        sys.exit(1)

    client = gdata.docs.client.DocsClient()
    client.ClientLogin(opts.user, opts.password, client.source)

    if opts.folder:
        f_query = \
        gdata.docs.service.DocumentQuery(feed='/feeds/default')
        f_query['title'] = opts.folder
        f_query['title-exact'] = 'true'
        f_query['showfolders'] = 'true'
        docs = client.GetEverything(uri=f_query.ToUri())

        if len(docs) != 1:
            print >>sys.stderr, 'Unable to find a folder name "%s".' % opts.folder
            sys.exit(1)

        uri = docs[0].content.src
        query = gdata.service.Query(uri)

    if opts.type:
        for t in opts.type:
            if '/' in t:
                t = '%s%s' % (GOOGLE_MIME_TYPE_SCHEMA, t)

            query.categories.append(t)

    if opts.query:
        query.text_query = opts.query

    print 'URI:', query.ToUri()

    feed = client.GetDocList()
    print >>open('feed.xml', 'w'), feed
    
    docs = client.GetEverything(uri=query.ToUri())
    for doc in docs:
        print doc.title.text, doc.GetDocumentType()
        if opts.download:
            print '[downloading %s]' % doc.title.text
            dst = os.path.join(opts.destination, '%s' % doc.title.text)
            while True:
                try:
                    client.Download(doc, dst)
                    break
                except httplib.IncompleteRead, detail:
                    tries += 1
                    if tries > opts.maxretry:
                        raise

if __name__ == '__main__':
    client = main()

