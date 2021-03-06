#!/usr/bin/env python

import cookielib
import mimetools
import os
import getpass
import re
import simplejson
import socket
import subprocess
import sys
import urllib2
from optparse import OptionParser
from tempfile import mkstemp
from urlparse import urljoin, urlparse


###
# Default configuration -- user-settable variables follow.
###

# The following settings usually aren't needed, but if your Review
# Board crew has specific preferences and doesn't want to express
# them with command line switches, set them here and you're done.
# In particular, setting the REVIEWBOARD_URL variable will allow
# you to make it easy for people to submit reviews regardless of
# their SCM setup.

# Reviewboard URL.
#
# Set this if you wish to hard-code a default server to always use.
# It's generally recommended to set this on your SCM repository instead
# for those that support it (currently only SVN and Git).
#
# For example, on SVN:
#   $ svn propset reviewboard:url http://reviewboard.example.com .
#
# Or with Git:
#   $ git config reviewboard.url http://reviewboard.example.com
#
# If this is not a concern, setting the value here will let you get started
# quickly.
REVIEWBOARD_URL = None

# Default submission arguments.  These are all optional; run this
# script with --help for descriptions of each argument.
TARGET_GROUPS   = None
TARGET_PEOPLE   = None
SUBMIT_AS       = None
PUBLISH         = False
OPEN_BROWSER    = False

# Debugging.  For development...
DEBUG           = False

###
# End user-settable variables.
###


VERSION = "0.7"

user_config = None
tempfiles = []
options = None


class APIError(Exception):
    pass


class RepositoryInfo:
    """
    A representation of a source code repository.
    """
    def __init__(self, path=None, base_path=None, supports_changesets=False):
        self.path = path
        self.base_path = base_path
        self.supports_changesets = supports_changesets

    def __str__(self):
        return "Path: %s, Base path: %s, Supports changesets: %s" % \
            (self.path, self.base_path, self.supports_changesets)


class ReviewBoardHTTPPasswordMgr(urllib2.HTTPPasswordMgr):
    """
    Adds HTTP authentication support for URLs.

    Python 2.4's password manager has a bug in http authentication when the
    target server uses a non-standard port.  This works around that bug on
    Python 2.4 installs. This also allows post-review to prompt for passwords
    in a consistent way.

    See: http://bugs.python.org/issue974757
    """
    def __init__(self, reviewboard_url):
        self.passwd  = {}
        self.rb_url  = reviewboard_url
        self.rb_user = None
        self.rb_pass = None

    def find_user_password(self, realm, uri):
        if uri.startswith(self.rb_url):
            if self.rb_user is None or self.rb_pass is None:
                print "==> HTTP Authentication Required"
                print 'Enter username and password for "%s" at %s' % \
                    (realm, urlparse(uri)[1])
                self.rb_user = raw_input('Username: ')
                self.rb_pass = getpass.getpass('Password: ')

            return self.rb_user, self.rb_pass
        else:
            # If this is an auth request for some other domain (since HTTP
            # handlers are global), fall back to standard password management.
            return urllib2.HTTPPasswordMgr.find_user_password(self, realm, uri)


class ReviewBoardServer:
    """
    An instance of a Review Board server.
    """
    def __init__(self, url, info, cookie_file):
        self.url = url
        self.info = info
        self.cookie_file = cookie_file
        self.cookie_jar  = cookielib.MozillaCookieJar(self.cookie_file)

        # Set up the HTTP libraries to support all of the features we need.
        cookie_handler = urllib2.HTTPCookieProcessor(self.cookie_jar)
        password_mgr   = ReviewBoardHTTPPasswordMgr(self.url)
        auth_handler   = urllib2.HTTPBasicAuthHandler(password_mgr)

        opener = urllib2.build_opener(cookie_handler, auth_handler)
        opener.addheaders = [('User-agent', 'post-review/' + VERSION)]
        urllib2.install_opener(opener)

    def login(self, username=None, password=None):
        """
        Logs in to a Review Board server, prompting the user for login
        information if needed.
        """
        if self.has_valid_cookie():
            return

        print "==> Review Board Login Required"
        print "Enter username and password for Review Board at %s" % self.url
        if not username:
          username = raw_input('Username: ')

        if not password:
          password = getpass.getpass('Password: ')

        debug('Logging in with username "%s"' % username)
        try:
            self.api_post('/api/json/accounts/login/', {
                'username': username,
                'password': password,
            })
        except APIError, e:
            rsp, = e.args

            die("Unable to log in: %s (%s)" % (rsp["err"]["msg"],
                                               rsp["err"]["code"]))

        debug("Logged in.")

    def has_valid_cookie(self):
        """
        Load the user's cookie file and see if they have a valid
        'sessionid' cookie for the current Review Board server.  Returns
        true if so and false otherwise.
        """
        try:
            parsed_url = urlparse(self.url)
            host = parsed_url[1]
            path = parsed_url[2] or '/'

            # Cookie files don't store port numbers, unfortunately, so
            # get rid of the port number if it's present.
            host = host.split(":")[0]

            debug("Looking for '%s %s' cookie in %s" % \
                  (host, path, self.cookie_file))
            self.cookie_jar.load(self.cookie_file, ignore_expires=True)

            try:
                cookie = self.cookie_jar._cookies[host][path]['rbsessionid']

                if not cookie.is_expired():
                    debug("Loaded valid cookie -- no login required")
                    return True

                debug("Cookie file loaded, but cookie has expired")
            except KeyError:
                debug("Cookie file loaded, but no cookie for this server")
        except IOError, error:
            debug("Couldn't load cookie file: %s" % error)

        return False

    def new_review_request(self, changenum, submit_as=None):
        """
        Creates a review request on a Review Board server, updating an
        existing one if the changeset number already exists.

        If submit_as is provided, the specified user name will be recorded as
        the submitter of the review request (given that the logged in user has
        the appropriate permissions).
        """
        try:
            debug("Attempting to create review request for %s" % changenum)
            data = { 'repository_path': self.info.path }

            if changenum:
                data['changenum'] = changenum

            if submit_as:
                debug("Submitting the review request as %s" % submit_as)
                data['submit_as'] = submit_as

            rsp = self.api_post('/api/json/reviewrequests/new/', data)
        except APIError, e:
            rsp, = e.args

            if not options.diff_only:
                if rsp['err']['code'] == 204: # Change number in use
                    debug("Review request already exists. Updating it...")
                    rsp = self.api_post(
                        '/api/json/reviewrequests/%s/update_from_changenum/' %
                        rsp['review_request']['id'])
                else:
                    raise e

        debug("Review request created")
        return rsp['review_request']

    def set_review_request_field(self, review_request, field, value):
        """
        Sets a field in a review request to the specified value.
        """
        rid = review_request['id']

        debug("Attempting to set field '%s' to '%s' for review request '%s'" %
              (field, value, rid))

        self.api_post('/api/json/reviewrequests/%s/draft/set/' % rid, {
            field: value,
        })

    def get_review_request(self, rid):
        """
        Returns the review request with the specified ID.
        """
        rsp = self.api_get('/api/json/reviewrequests/%s/' % rid)
        return rsp['review_request']

    def save_draft(self, review_request):
        """
        Saves a draft of a review request.
        """
        self.api_post("/api/json/reviewrequests/%s/draft/save/" %
                      review_request['id'])
        debug("Review request draft saved")

    def upload_diff(self, review_request, diff_content):
        """
        Uploads a diff to a Review Board server.
        """
        debug("Uploading diff, size: %d" % (len(diff_content),))
        fields = {}

        if self.info.base_path:
            fields['basedir'] = self.info.base_path

        self.api_post('/api/json/reviewrequests/%s/diff/new/' %
                      review_request['id'], fields,
                      {'path': {'filename': 'diff',
                                'content': diff_content}})

    def publish(self, review_request):
        """
        Publishes a review request.
        """
        debug("Publishing")
        self.http_post(path='/r/%s/publish/' % review_request['id'],
                       fields = {})

    def process_json(self, data):
        """
        Loads in a JSON file and returns the data if successful. On failure,
        APIError is raised.
        """
        rsp = simplejson.loads(data)

        if rsp['stat'] == 'fail':
            raise APIError, rsp

        return rsp

    def http_get(self, path):
        """
        Performs an HTTP GET on the specified path, storing any cookies that
        were set.
        """
        debug('HTTP GETting %s' % path)

        url = self._make_url(path)

        try:
            rsp = urllib2.urlopen(url).read()
            self.cookie_jar.save(self.cookie_file)
            return rsp
        except urllib2.HTTPError, e:
            print "Unable to access %s (%s). The host path may be invalid" % \
                (url, e.code)
            try:
                debug(e.read())
            except AttributeError:
                pass
            die()

    def _make_url(self, path):
        """Given a path on the server returns a full http:// style url"""
        url = urljoin(self.url, path)
        if not url.startswith('http'):
            url = 'http://%s' % url
        return url

    def api_get(self, path):
        """
        Performs an API call using HTTP GET at the specified path.
        """
        return self.process_json(self.http_get(path))

    def http_post(self, path, fields, files=None):
        """
        Performs an HTTP POST on the specified path, storing any cookies that
        were set.
        """
        if fields:
            debug_fields = fields.copy()
        else:
            debug_fields = {}

        if 'password' in debug_fields:
            debug_fields["password"] = "**************"
        url = self._make_url(path)
        debug('HTTP POSTing to %s: %s' % (url, debug_fields))

        content_type, body = self._encode_multipart_formdata(fields, files)
        headers = {
            'Content-Type': content_type,
            'Content-Length': str(len(body))
        }

        try:
            r = urllib2.Request(url, body, headers)
            data = urllib2.urlopen(r).read()
            self.cookie_jar.save(self.cookie_file)
            return data
        except urllib2.URLError, e:
            try:
                debug(e.read())
            except AttributeError:
                pass

            die("Unable to access %s. The host path may be invalid\n%s" % \
                (url, e))
        except urllib2.HTTPError, e:
            die("Unable to access %s (%s). The host path may be invalid\n%s" % \
                (url, e.code, e.read()))

    def api_post(self, path, fields=None, files=None):
        """
        Performs an API call using HTTP POST at the specified path.
        """
        return self.process_json(self.http_post(path, fields, files))

    def _encode_multipart_formdata(self, fields, files):
        """
        Encodes data for use in an HTTP POST.
        """
        BOUNDARY = mimetools.choose_boundary()
        content = ""

        fields = fields or {}
        files = files or {}

        for key in fields:
            content += "--" + BOUNDARY + "\r\n"
            content += "Content-Disposition: form-data; name=\"%s\"\r\n" % key
            content += "\r\n"
            content += fields[key] + "\r\n"

        for key in files:
            filename = files[key]['filename']
            value = files[key]['content']
            content += "--" + BOUNDARY + "\r\n"
            content += "Content-Disposition: form-data; name=\"%s\"; " % key
            content += "filename=\"%s\"\r\n" % filename
            content += "\r\n"
            content += value + "\r\n"

        content += "--" + BOUNDARY + "--\r\n"
        content += "\r\n"

        content_type = "multipart/form-data; boundary=%s" % BOUNDARY

        return content_type, content


class SCMClient(object):
    """
    A base representation of an SCM tool for fetching repository information
    and generating diffs.
    """
    def get_repository_info(self):
        return None

    def scan_for_server(self, repository_info):
        """
        Scans the current directory on up to find a .reviewboard file
        containing the server path.
        """
        server_url = self._get_server_from_config(user_config, repository_info)
        if server_url:
            return server_url

        for path in walk_parents(os.getcwd()):
            filename = os.path.join(path, ".reviewboardrc")
            if os.path.exists(filename):
                config = load_config_file(filename)
                server_url = self._get_server_from_config(config,
                                                          repository_info)
                if server_url:
                    return server_url

        return None

    def diff(self, args):
        return None

    def diff_between_revisions(self, revision_range):
        return None

    def add_options(self, parser):
        """
        Adds options to an OptionParser.
        """
        pass

    def _get_server_from_config(self, config, repository_info):
        if 'REVIEWBOARD_URL' in config:
            return config['REVIEWBOARD_URL']
        elif 'TREES' in config:
            trees = config['TREES']
            if not isinstance(trees, dict):
                die("Warning: 'TREES' in config file is not a dict!")

            if repository_info.path in trees and \
               'REVIEWBOARD_URL' in trees[repository_info.path]:
                return trees[repository_info.path]['REVIEWBOARD_URL']

        return None


class SVNClient(SCMClient):
    """
    A wrapper around the svn Subversion tool that fetches repository
    information and generates compatible diffs.
    """
    def get_repository_info(self):
        if not check_install('svn help'):
            return None

        data = execute('svn info', ignore_errors=True)

        m = re.search(r'^Repository Root: (.+)$', data, re.M)
        if not m:
            return None

        path = m.group(1)

        m = re.search(r'^URL: (.+)$', data, re.M)
        if not m:
            return None

        base_path = m.group(1)[len(path):]

        return RepositoryInfo(path=path, base_path=base_path)

    def scan_for_server(self, repository_info):
        # Scan first for dot files, since it's faster and will cover the
        # user's $HOME/.reviewboardrc
        server_url = super(SVNClient, self).scan_for_server(repository_info)
        if server_url:
            return server_url

        return self.scan_for_server_property(repository_info)

    def scan_for_server_property(self, repository_info):
        def get_url_prop(path):
            url = execute("svn propget reviewboard:url %s" % path).strip()
            return url or None

        for path in walk_parents(os.getcwd()):
            if not os.path.exists(os.path.join(path, ".svn")):
                break

            prop = get_url_prop(path)
            if prop:
                return prop

        return get_url_prop(repository_info.path)

    def diff(self, files):
        """
        Performs a diff across all modified files in a Subversion repository.
        """
        return execute('svn diff --diff-cmd=diff %s' % ' '.join(files))

    def diff_between_revisions(self, revision_range):
        """
        Performs a diff between 2 revisions of a Subversion repository.
        """
        return execute('svn diff --diff-cmd=diff -r %s' % revision_range)


class PerforceClient(SCMClient):
    """
    A wrapper around the p4 Perforce tool that fetches repository information
    and generates compatible diffs.
    """
    def getPendingCLs(self, expensive=None):
      if not check_install('p4 help'):
        print "P4 is not correctly installed"
        return [] # p4 isn't installed, so we don't have any CLs to view
      cmd = 'p4 changes -u %s -s pending' % self.username
      f = os.popen(cmd, 'r')
      data = f.readlines()
      f.close()
      cls = []
      for a in data:
        info = re.search("Change (.*) on (.*) \*pending\* '(.*)'", a)
        if not info:
          continue
        num = info.group(1)
        desc = info.group(3)
        file_zone = False
        full = ""
        file = ""
        if expensive:
					cmd = 'p4 describe -s %s' % num
					f = os.popen(cmd, 'r')
					descrInfo = f.readlines()
					f.close()
					lines = 0
					for l in descrInfo:
						l = l.strip()
						if "Affected files ..." in l:
							file_zone = True
						if file_zone:
							file += l + "\n"
						else:
							full += l + "\n"
					desc = full.split('\n')[2]
        cls.append((num, desc, full, file))
      return cls

    def get_repository_info(self):
        if not check_install('p4 help'):
            return None

        data = execute('p4 info', ignore_errors=True)

        m = re.search(r'^User name: (.+)$', data, re.M)
        if m:
          self.username = m.group(1).strip()
        m = re.search(r'^Server address: (.+)$', data, re.M)
        if not m:
            return None

        repository_path = m.group(1).strip()

        try:
            hostname, port = repository_path.split(":")
            info = socket.gethostbyaddr(hostname)
            repository_path = "%s:%s" % (info[0], port)
        except (socket.gaierror, socket.herror):
            pass

        return RepositoryInfo(path=repository_path, supports_changesets=True)


    def diff(self, args):
        """
        Goes through the hard work of generating a diff on Perforce in order
        to take into account adds/deletes and to provide the necessary
        revision information.
        """
        if len(args) != 1:
            print "Specify the change number of a pending changeset"
            sys.exit(1)

        changenum = args[0]

        cl_is_pending = False

        try:
            changenum = int(changenum)
        except ValueError:
            die("You must enter a valid change number")

        debug("Generating diff for changenum %s" % changenum)

        description = execute('p4 describe -s %d' % changenum).splitlines()
        if '*pending*' in description[0]:
            cl_is_pending = True

        # Get the file list
        for line_num, line in enumerate(description):
            if 'Affected files ...' in line:
                break
        else:
            # Got to the end of all the description lines and didn't find
            # what we were looking for.
            die("Couldn't find any affected files for this change.")

        description = description[line_num+2:]

        cwd = os.getcwd()
        diff_lines = []


        empty_filename = make_tempfile()
        tmp_diff_from_filename = make_tempfile()
        tmp_diff_to_filename = make_tempfile()

        for line in description:
            line = line.strip()
            if not line:
                continue

            m = re.search(r'\.\.\. ([^#]+)#(\d+) (add|edit|delete|integrate|branch)', line)
            if not m:
                die("Unsupported line from p4 opened: %s" % line)

            depot_path = m.group(1)
            base_revision = int(m.group(2))
            if not cl_is_pending:
                # If the changelist is pending our base revision is the one that's
                # currently in the depot. If we're not pending the base revision is
                # actually the revision prior to this one
                base_revision -= 1

            changetype = m.group(3)

            debug('Processing %s of %s' % (changetype, depot_path))

            local_name = m.group(1)

            old_file = new_file = empty_filename
            old_depot_path = new_depot_path = None
            changetype_short = None

            if changetype == 'edit' or changetype == 'integrate':
                # A big assumption
                new_revision = base_revision + 1

                # We have an old file, get p4 to take this old version from the
                # depot and put it into a plain old temp file for us
                old_depot_path = "%s#%s" % (depot_path, base_revision)
                self._write_file(old_depot_path, tmp_diff_from_filename)
                old_file = tmp_diff_from_filename

                # Also print out the new file into a tmpfile
                if cl_is_pending:
                    new_file = self._depot_to_local(depot_path)
                else:
                    new_depot_path = "%s#%s" %(depot_path, new_revision)
                    self._write_file(new_depot_path, tmp_diff_to_filename)
                    new_file = tmp_diff_to_filename

                changetype_short = "M"

            elif changetype == 'add' or changetype == 'branch':
                # We have a new file, get p4 to put this new file into a pretty
                # temp file for us. No old file to worry about here.
                if cl_is_pending:
                    new_file = self._depot_to_local(depot_path)
                else:
                    self._write_file(depot_path, tmp_diff_to_filename)
                    new_file = tmp_diff_to_filename
                changetype_short = "A"

            elif changetype == 'delete':
                # We've deleted a file, get p4 to put the deleted file into  a temp
                # file for us. The new file remains the empty file.
                old_depot_path = "%s#%s" % (depot_path, base_revision)
                self._write_file(old_depot_path, tmp_diff_from_filename)
                old_file = tmp_diff_from_filename
                changetype_short = "D"
            else:
                die("Unknown change type '%s' for %s" % (changetype, depot_path))


            diff_cmd = 'diff -urNp "%s" "%s"' % (old_file, new_file)
            # Diff returns "1" if differences were found.
            dl = execute(diff_cmd, extra_ignore_errors=(1,)).splitlines(True)

            if local_name.startswith(cwd):
                local_path = local_name[len(cwd) + 1:]
            else:
                local_path = local_name

            # Special handling for the output of the diff tool on binary files:
            #     diff outputs "Files a and b differ"
            # and the code below expects the outptu to start with
            #     "Binary files "
            if len(dl) == 1 and \
               dl[0] == ('Files %s and %s differ'% (old_file, new_file)):
                dl = ['Binary files %s and %s differ'% (old_file, new_file)]


            if dl == [] or dl[0].startswith("Binary files "):
                if dl == []:
                    print "Warning: %s in your changeset is unmodified" % \
                        local_path

                dl.insert(0, "==== %s#%s ==%s== %s ====\n" % \
                    (depot_path, base_revision, changetype_short, local_path))
            else:

                m = re.search(r'(\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d)', dl[1])
                if m:
                    timestamp = m.group(1)
                else:
                    # Thu Sep  3 11:24:48 2007
                    m = re.search(r'(\w+)\s+(\w+)\s+(\d+)\s+(\d\d:\d\d:\d\d)\s+(\d\d\d\d)', dl[1])
                    if not m:
                        die("Unable to parse diff header: %s" % dl[1])

                    month_map = {
                        "Jan": "01",
                        "Feb": "02",
                        "Mar": "03",
                        "Apr": "04",
                        "May": "05",
                        "Jun": "06",
                        "Jul": "07",
                        "Aug": "08",
                        "Sep": "09",
                        "Oct": "10",
                        "Nov": "11",
                        "Dec": "12",
                    }
                    month = month_map[m.group(2)]
                    day = m.group(3)
                    timestamp = m.group(4)
                    year = m.group(5)

                    timestamp = "%s-%s-%s %s" % (year, month, day, timestamp)

                dl[0] = "--- %s\t%s#%s\n" % (local_path, depot_path, base_revision)
                dl[1] = "+++ %s\t%s\n" % (local_path, timestamp)

            diff_lines += dl


        os.unlink(empty_filename)
        os.unlink(tmp_diff_from_filename)
        os.unlink(tmp_diff_to_filename)

        return ''.join(diff_lines)

    def _write_file(self, depot_path, tmpfile):
        """
        Grabs a file from Perforce and writes it to a temp file. We do this
        wrather than telling p4 print to write it out in order to work around
        a permissions bug on Windows.
        """
        debug('Writing "%s" to "%s"' % (depot_path, tmpfile))
        data = execute('p4 print -q "%s"' % depot_path)

        f = open(tmpfile, "w")
        f.write(data)
        f.close()

    def _depot_to_local(self, depot_path):
        """
        Given a path in the depot return the path on the local filesystem to
        the same file.
        """
        # $ p4 where //user/bvanzant/main/testing
        # //user/bvanzant/main/testing //bvanzant:test05:home/testing /home/bvanzant/home-versioned/testing
        cmd = 'p4 where "%s"' % (depot_path,)
        where_output = execute(cmd).splitlines()
        # Take only the last line from the where command.  If you have a
        # multi-line view mapping with exclusions, Perforce will display
        # the exclusions in order, with the last line showing the actual
        # location.
        last_line = where_output[-1]

        # XXX: This breaks on filenames with spaces.
        return last_line.split(' ')[2]


class MercurialClient(SCMClient):
    """
    A wrapper around the hg Mercurial tool that fetches repository
    information and generates compatible diffs.
    """
    def get_repository_info(self):
        if not check_install('hg --help'):
            return None

        data = execute('hg root', ignore_errors=True)
        if data.startswith('abort:'):
            # hg aborted => no mercurial repository here.
            return None

        # Elsewhere, hg root output give us the repository path.

        # We save data here to use it as a fallback. See below
        local_data = data.strip()

        # We are going to search .hg/hgrc for the default path.
        file_name = os.path.join(local_data,'.hg', 'hgrc')
        if not  os.path.exists(file_name):
            return RepositoryInfo(path=local_data, base_path='/')

        f = open(file_name)
        data = f.read()
        f.close()

        m = re.search(r'^default\s+=\s+(.+)$', data, re.M)
        if not m:
            # Return the local path, if no default value is found.
            return RepositoryInfo(path=local_data, base_path='/')

        path = m.group(1).strip()

        return RepositoryInfo(path=path, base_path='')

    def diff(self, files):
        """
        Performs a diff across all modified files in a Mercurial repository.
        """
        return execute('hg diff %s' % ' '.join(files))

    def diff_between_revisions(self, revision_range):
        """
        Performs a diff between 2 revisions of a Mercurial repository.
        """
        r1, r2 = revision_range.split(':')
        return execute('hg diff -r %s -r %s' % (r1, r2))


class GitClient(SCMClient):
    """
    A wrapper around git that fetches repository information and generates
    compatible diffs. This will attempt to generate a diff suitable for the
    remote repository, whether git, SVN or Perforce.
    """
    def get_repository_info(self):
        if not check_install('git --help'):
            return None

        git_dir = execute('git rev-parse --git-dir', ignore_errors=True).strip()

        if git_dir.startswith("fatal:") or not os.path.isdir(git_dir):
            return None

        # We know we have something we can work with. Let's find out
        # what it is. We'll try SVN first.
        data = execute("git svn info", ignore_errors=True)

        m = re.search(r'^Repository Root: (.+)$', data, re.M)
        if m:
            path = m.group(1)
            m = re.search(r'^URL: (.+)$', data, re.M)

            if m:
                base_path = m.group(1)[len(path):]
                self.type = "svn"
                return RepositoryInfo(path=path, base_path=base_path)

        # Okay, maybe Perforce.
        # TODO

        # Nope, it's git then.
        # TODO
        return None

    def scan_for_server(self, repository_info):
        # Scan first for dot files, since it's faster and will cover the
        # user's $HOME/.reviewboardrc

        # TODO: Maybe support a server per remote later? Is that useful?
        url = execute("git config --get reviewboard.url").strip()
        if url:
            return url

        if self.type == "svn":
            # Try using the reviewboard:url property on the SVN repo, if it
            # exists.
            prop = SVNClient().scan_for_server_property(repository_info)

            if prop:
                return prop

        return None

    def diff(self, args):
        """
        Performs a diff across all modified files in the branch.
        """
        if len(args) == 0:
            branch_against = "master"
        elif len(args) == 1:
            branch_against = args[0]
        else:
            print "No more than one branch can be supplied."
            sys.exit(1)

        diff_lines = execute("git diff --no-color --no-prefix -r -u %s.." %
                             branch_against,
                             split_lines=True)

        if self.type == "svn":
            return self.make_svn_diff(branch_against, diff_lines)

        return None


    def make_svn_diff(self, branch_against, diff_lines):
        """
        Formats the output of git diff such that it's in a form that
        svn diff would generate. This is needed so the SVNTool in Review
        Board can properly parse this diff.
        """
        rev = execute("git-svn find-rev %s" % branch_against).strip()

        if not rev:
            return None

        diff_data = ""
        filename = ""
        revision = ""
        newfile = False

        for line in diff_lines:
            if line.startswith("diff "):
                # Grab the filename and then filter this out.
                # This will be in the format of:
                #
                # diff --git a/path/to/file b/path/to/file
                info = line.split(" ")
                diff_data += "Index: %s\n" % info[2]
                diff_data += "=" * 63
                diff_data += "\n"
            elif line.startswith("index "):
                # Filter this out.
                pass
            elif line.strip() == "--- /dev/null":
                # New file
                newfile = True
            elif line.startswith("--- "):
                newfile = False
                diff_data += "--- %s\t(revision %s)\n" % \
                             (line[4:].strip(), rev)
            elif line.startswith("+++ "):
                filename = line[4:].strip()
                if newfile:
                    diff_data += "--- %s\t(revision 0)\n" % filename
                    diff_data += "+++ %s\t(revision 0)\n" % filename
                else:
                    # We already printed the "--- " line.
                    diff_data += "+++ %s\t(working copy)\n" % filename
            else:
                diff_data += line

        return diff_data

    def diff_between_revisions(self, revision_range):
        pass


def debug(s):
    """
    Prints debugging information if post-review was run with --debug
    """
    if options.debug:
        print ">>> %s" % s


def make_tempfile():
    """
    Creates a temporary file and returns the path. The path is stored
    in an array for later cleanup.
    """
    fd, tmpfile = mkstemp()
    os.close(fd)
    tempfiles.append(tmpfile)
    return tmpfile


def check_install(command):
    """
    Try executing an external command and return a boolean indicating whether
    that command is installed or not.  The 'command' argument should be
    something that executes quickly, without hitting the network (for
    instance, 'svn help' or 'git --version').
    """
    try:
        p = subprocess.Popen(command.split(' '),
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        return True
    except OSError:
        return False


def execute(command, split_lines=False, ignore_errors=False,
            extra_ignore_errors=()):
    """
    Utility function to execute a command and return the output.
    """
    if sys.platform.startswith('win'):
        p = subprocess.Popen(command,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT,
                             shell=True)
    else:
        p = subprocess.Popen(command,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT,
                             shell=True,
                             close_fds=True)
    if split_lines:
        data = p.stdout.readlines()
    else:
        data = p.stdout.read()
    rc = p.wait()
    if rc and not ignore_errors and rc not in extra_ignore_errors:
        die('Failed to execute command: %s\n%s' % (command, data))

    return data


def die(msg=None):
    """
    Cleanly exits the program with an error message. Erases all remaining
    temporary files.
    """
    for tmpfile in tempfiles:
        try:
            os.unlink(tmpfile)
        except:
            pass

    if msg:
        print msg

    sys.exit(1)


def walk_parents(path):
    """
    Walks up the tree to the root directory.
    """
    while os.path.splitdrive(path)[1] != os.sep:
        yield path
        path = os.path.dirname(path)


def load_config_file(filename):
    """
    Loads data from a config file.
    """
    config = {
        'TREES': {},
    }

    if os.path.exists(filename):
        try:
            execfile(filename, config)
        except:
            pass

    return config


def tempt_fate(server, tool, changenum, diff_content=None, submit_as=None):
    """
    Attempts to create a review request on a Review Board server and upload
    a diff. On success, the review request path is displayed.
    """

    try:
        save_draft = False

        if options.rid:
            review_request = server.get_review_request(options.rid)
        else:
            review_request = server.new_review_request(changenum, submit_as)

        if options.target_groups:
            server.set_review_request_field(review_request, 'target_groups',
                                            options.target_groups)
            save_draft = True

        if options.target_people:
            server.set_review_request_field(review_request, 'target_people',
                                            options.target_people)
            save_draft = True

        if options.summary:
            server.set_review_request_field(review_request, 'summary',
                                            options.summary)
            save_draft = True

        if options.description:
            server.set_review_request_field(review_request, 'description',
                                            options.description)
            save_draft = True

        if save_draft:
            server.save_draft(review_request)
    except APIError, e:
        rsp, = e.args
        if rsp['err']['code'] == 103: # Not logged in
            server.login()
            tempt_fate(server, tool, changenum, diff_content, submit_as)
            return

        if options.rid:
            die("Error getting review request %s: %s (code %s)" % \
                (options.rid, rsp['err']['msg'], rsp['err']['code']))
        else:
            die("Error creating review request: %s (code %s)" % \
                (rsp['err']['msg'], rsp['err']['code']))


    if not server.info.supports_changesets or not options.change_only:
        try:
            server.upload_diff(review_request, diff_content)
        except APIError, e:
            rsp, = e.args
            print "Error uploading diff: %s (%s)" % (rsp['err']['msg'],
                                                     rsp['err']['code'])
            debug(rsp)
            die("Your review request still exists, but the diff is not " +
                "attached.")

    if options.publish:
        server.publish(review_request)

    review_url = '%s/%s/%s/' % (server.url, "r", review_request['id'])

    if not review_url.startswith('http'):
        review_url = 'http://%s' % review_url

    print "Review request #%s posted." % (review_request['id'],)
    print
    print review_url

    return review_url


def parse_options(tool, repository_info, args):
    parser = OptionParser(usage="%prog [-pond] [-r review_id] [changenum]",
                          version="%prog " + VERSION)

    parser.add_option("-p", "--publish",
                      dest="publish", action="store_true", default=PUBLISH,
                      help="publish the review request immediately after " +
                           "submitting")
    parser.add_option("-r", "--review-request-id",
                      dest="rid", metavar="ID", default=None,
                      help="existing review request ID to update")
    parser.add_option("-o", "--open",
                      dest="open_browser", action="store_true",
                      default=OPEN_BROWSER,
                      help="open a web browser to the review request page")
    parser.add_option("-n", "--output-diff",
                      dest="output_diff_only", action="store_true",
                      default=False,
                      help="outputs a diff to the console and exits. " +
                           "Does not post")
    parser.add_option("--server",
                      dest="server", default=REVIEWBOARD_URL,
                      metavar="SERVER",
                      help="specify a different Review Board server " +
                           "to use")
    parser.add_option("--diff-only",
                      dest="diff_only", action="store_true", default=False,
                      help="uploads a new diff, but does not update " +
                           "info from changelist")
    parser.add_option("--target-groups",
                      dest="target_groups", default=TARGET_GROUPS,
                      help="names of the groups who will perform " +
                           "the review")
    parser.add_option("--target-people",
                      dest="target_people", default=TARGET_PEOPLE,
                      help="names of the people who will perform " +
                           "the review")
    parser.add_option("--summary",
                      dest="summary", default=None,
                      help="summary of the review ")
    parser.add_option("--description",
                      dest="description", default=None,
                      help="description of the review ")
    parser.add_option("--revision-range",
                      dest="revision_range", default=None,
                      help="generate the diff for review based on given " +
                           "revision range")
    parser.add_option("--submit-as",
                      dest="submit_as", default=SUBMIT_AS, metavar="USERNAME",
                      help="user name to be recorded as the author of the "
                           "review request, instead of the logged in user")

    if repository_info:
        if repository_info.supports_changesets:
            parser.add_option("--change-only",
                              dest="change_only", action="store_true",
                              default=False,
                              help="updates info from changelist, but does " +
                                   "not upload a new diff")

        tool.add_options(parser)


    parser.add_option("-d", "--debug",
                      action="store_true", dest="debug", default=DEBUG,
                      help="display debug output")

    (globals()["options"], args) = parser.parse_args(args)

    return args


def main(args):
    if 'USERPROFILE' in os.environ:
        homepath = os.path.join(os.environ["USERPROFILE"], "Local Settings",
                                "Application Data")
    else:
        homepath = os.environ["HOME"]

    # Load the config and cookie files
    globals()['user_config'] = \
        load_config_file(os.path.join(homepath, ".reviewboardrc"))
    cookie_file = os.path.join(homepath, ".post-review-cookies.txt")

    # Try to find the SCM Client we're going to be working with
    repository_info = None
    tool = None

    for tool in (SVNClient(), MercurialClient(), GitClient(), PerforceClient()):
        repository_info = tool.get_repository_info()

        if repository_info:
            break

    args = parse_options(tool, repository_info, args)

    if not repository_info:
        print "The current directory does not contain a checkout from a"
        print "supported source code repository."
        sys.exit(1)

    debug("Repository info '%s'" % repository_info)

    # Try to find a valid Review Board server to use.
    if options.server:
        server_url = options.server
    else:
        server_url = tool.scan_for_server(repository_info)

    if not server_url:
        print "Unable to find a Review Board server for this source code tree."
        sys.exit(1)

    server = ReviewBoardServer(server_url, repository_info, cookie_file)

    if repository_info.supports_changesets:
        if len(args) < 1:
            print "You must include a change set number"
            sys.exit(1)

        changenum = args[0]
    else:
        changenum = None

    if options.revision_range:
        diff = tool.diff_between_revisions(options.revision_range)
    else:
        diff = tool.diff(args)

    if options.output_diff_only:
        print diff
        sys.exit(0)

    # Let's begin.
    server.login()

    review_url = tempt_fate(server, tool, changenum, diff_content=diff,
                            submit_as=options.submit_as)

    # Load the review up in the browser if requested to:
    if options.open_browser:
        try:
            import webbrowser
            if 'open_new_tab' in dir(webbrowser):
                # open_new_tab is only in python 2.5+
                webbrowser.open_new_tab(review_url)
            elif 'open_new' in dir(webbrowser):
                webbrowser.open_new(review_url)
            else:
                os.system( 'start %s' % review_url )
        except:
            print 'Error opening review URL: %s' % review_url


if __name__ == "__main__":
    main(sys.argv[1:])
