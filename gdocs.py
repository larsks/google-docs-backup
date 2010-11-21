#!/usr/bin/python

import os
import sys
import urllib
import httplib
import types

import atom.data
import gdata.service
import gdata.docs.client
import gdata.docs.service
import gdata.docs.data

from configdict.configdict import ConfigDict

GOOGLE_MIME_TYPE_SCHEMA = '{http://schemas.google.com/g/2005#kind}'
CREATE_SESSION_URI = '/feeds/upload/create-session/default/private/full'
DEFAULT_UPLOAD_CHUNK_SIZE   = 10485760

class GoogleDocsError (Exception):
    pass

class AuthenticationError(GoogleDocsError):
    pass

class AuthenticationRequired(GoogleDocsError):
    pass

def authenticated(f):
    def _ (self, *args, **kwargs):
        if not self.authenticated:
            raise AuthenticationRequired()
        return f(self, *args, **kwargs)

    return _

class GoogleDocs (object):
    source = 'GoogleDocs Module (python)'

    def __init__ (self, credentials=None, upload_chunk_size=None):
        self.authenticated = False
        if credentials is not None:
            self.credentials = credentials

        if upload_chunk_size is None:
            self.upload_chunk_size = DEFAULT_UPLOAD_CHUNK_SIZE
        else:
            self.upload_chunk_size = upload_chunk_size

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
    def list(self, folder=None, uri=None):
        if folder is not None:
            uri = folder.content.src

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

    @authenticated
    def update(self, entry):
        return self.client.Update(entry)

    @authenticated
    def upload(self, pathname, mimetype='text/plain', folder=None,
            title=None, convert=False):
        f = open(pathname)
        f_size = os.path.getsize(f.name)

        if title is None:
            title = os.path.basename(f.name)

        if isinstance(folder, types.StringTypes):
            folder = self.title(folder)

        uploader = gdata.client.ResumableUploader(
                self.client, f, mimetype, f_size, self.upload_chunk_size,
                desired_class=gdata.docs.data.DocsEntry)

        if convert:
            uri = '%s' % CREATE_SESSION_URI
        else:
            uri = '%s?convert=false' % CREATE_SESSION_URI

        print 'URI:', uri

        entry = gdata.docs.data.DocsEntry(title=atom.data.Title(text=title))
        new_entry = uploader.UploadFile(uri, entry=entry)

        if folder:
            new_entry = self.client.Move(new_entry, folder)

        return new_entry

    @authenticated
    def create_folder(self, name):
        new_folder = self.client.Create(gdata.docs.data.FOLDER_LABEL, name)
        return new_folder

if __name__ == '__main__':
    import configdict

    cf = configdict.ConfigDict('auth.conf')
    g = GoogleDocs(credentials=cf['google'])
    g.login()

