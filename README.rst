This is a set of tools for backing up files to a Google Docs account.
It's primarily for my own consumption at this point.  The parts are:

- gdbackup -- create multivolume incremental backups using tar
- gdrestore -- restore form same
- gdocs.py -- a python class for interacting with google docs
- upload.py -- a script for uploading files to google docs.

Caveats:

- upload.py doesn't really work because Google does not allow
  uploading of arbitrary files via the API (you need to use the web
  interface).

- The whole thing isn't really useful unless you've purchased
  additional space for your google docs account.

