#!/usr/bin/python

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

class GDocsError (Exception):
    pass

class AuthenticationError(GDocsError):
    pass

class AuthenticationRequired(GDocsError):
    pass

def authenticated(f):
    def _ (self, *args, **kwargs):
        if not self.authenticated:
            raise AuthenticationRequired()
        return f(self, *args, **kwargs)

    return _

class GDocs (object):
    source = 'GDdocs (python)'

    def __init__ (self, credentials=None):
        self.authenticated = False
        if credentials is not None:
            self.credentials = credentials

    def set_credentials(self, credentials):
        self.credentials = credentials

    def login(self, credentials=None):
        if credentials is None:
            credentials = self.credentials
            if self.credentials is None or ('user' not in credentials or
                    'pass' not in credentials):
                raise AuthenticationError('missing credentials')

        self.client = gdata.docs.client.DocsClient()
        self.client.ClientLogin(credentials['user'],
                credentials['pass'],
                self.source)
        self.authenticated = True

    @authenticated
    def list(self, uri=None):
        feed = self.client.GetDocList(uri=uri, limit=50)
        while True:
            for entry in feed.entry:
                yield entry

            if feed.GetNextLink() is None:
                break

            feed = self.client.GetDocList(feed.GetNextLink().href,
                    limit=50)

    def query(self):
        return gdata.docs.service.DocumentQuery(feed='/feeds/default')

    @authenticated
    def title(self, title):
        q = self.query()
        q['title'] = title
        q['title-exact'] = 'true'
        q['showfolders'] = 'true'

        feed = self.client.GetDocList(uri=q.ToUri())
        if len(feed.entry) != 1:
            raise KeyError(title)

        return feed.entry[0]

    @authenticated
    def contents_query(self, folder):
        folder = self.title(folder)
        return gdata.service.Query(folder.content.src)

def parse_args():
    p = optparse.OptionParser()
    p.add_option('-c', '--config')
    p.add_option('-u', '--user')
    p.add_option('-p', '--password', '--pass')
    p.add_option('-f', '--folder')
    p.add_option('-t', '--type', action='append',
            help='Retrieve only documents of type TYPE.  ')
    p.add_option('-m', '--maxretry', default='5')
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
    query = gdata.docs.service.DocumentQuery(feed='/feeds/default')

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
            dst = os.path.join(opts.destination, '%s' % doc.title.text)

            if os.path.exists(dst) and os.path.getsize(dst) > 0:
                print '%s: exists, skipping' % doc.title.text
                continue

            tries = 0
            while True:
                try:
                    print '%s [%d]: downloading...' % (doc.title.text,
                            tries)
                    client.Download(doc, dst)
                    break
                except gdata.client.RequestError, detail:
                    print >>sys.stderr, 'Download failed: %s' % detail.status
                    tries += 1
                    if tries > int(opts.maxretry):
                        raise

                except Exception, detail:
                    print >>sys.stderr, 'Download failed: %s' % detail
                    tries += 1
                    if tries > int(opts.maxretry):
                        raise

if __name__ == '__main__':
    client = main()

