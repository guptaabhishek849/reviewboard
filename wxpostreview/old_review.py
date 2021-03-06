#!/usr/bin/env python

###########################################################################
# TO BE REMOVED!!
###########################################################################

###########################################################################
# Configuration
###########################################################################

# Server host
# REVIEWBOARD_HOST = 'http://reviews.mydomain.com'
REVIEWBOARD_HOST = None

###########################################################################
# Don't touch beyond this line!
###########################################################################

import httplib, mimetypes, mimetools, urllib2, cookielib, os, sys, getpass
import re
import simplejson
import time
from optparse import OptionParser
from tempfile import mkstemp

VERSION = "0.5"

def setCookies():
	# Who stole the cookies from the cookie jar?
	# Was it you?
	# >:(
	if os.environ.has_key("USERPROFILE"):
	    cookiepath = os.path.join(os.environ["USERPROFILE"], "UserData")
	else:
	    cookiepath = os.environ["HOME"]

	cj = cookielib.MozillaCookieJar()
	cookiefile = os.path.join(cookiepath, ".post-review-cookies.txt")

	opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
	opener.addheaders = [('User-agent', 'post-review/' + VERSION)]
	urllib2.install_opener(opener)
	# Huge hack
	globals()["cj"] = cj
	globals()["cookiefile"] = cookiefile

tempfiles = []
options = None


class APIError(Exception):
    pass


def debug(s):
    #if options.debug:
    #    print ">>> %s" % s
    pass


def make_tempfile():
    fd, tmpfile = mkstemp()
    os.close(fd)
    tempfiles.append(tmpfile)
    return tmpfile


def die(msg=None):
    for tmpfile in tempfiles:
        try:
            os.unlink(tmpfile)
        except:
            pass

    if msg:
        print msg

    sys.exit(1)


def encode_multipart_formdata(fields, files):
    BOUNDARY = mimetools.choose_boundary()
    content = ""

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


def process_json(data):
    rsp = simplejson.loads(data)

    if rsp['stat'] == 'fail':
        raise APIError, rsp

    return rsp


def http_get(path):
    debug('HTTP GETting %s' % path)

    url = REVIEWBOARD_HOST + path

    try:
        rsp = urllib2.urlopen(url).read()
        cj.save(cookiefile)
        return rsp
    except urllib2.HTTPError, e:
        print "Unable to access %s (%s). The host path may be invalid" % \
            (url, e.code)
        debug(e.data)
        die()


def api_get(path):
    return process_json(http_get(path))


def http_post(path, fields, files={}):
    debug_fields = fields.copy()
    if debug_fields.has_key("password"):
        debug_fields["password"] = "**************"
    debug('HTTP POSTing to %s: %s' % (path, debug_fields))

    url = REVIEWBOARD_HOST + path
    content_type, body = encode_multipart_formdata(fields, files)
    headers = {
        'Content-Type': content_type,
        'Content-Length': str(len(body))
    }

    try:
        r = urllib2.Request(REVIEWBOARD_HOST + path, body, headers)
        data = urllib2.urlopen(r).read()
        cj.save(cookiefile)
        return data
    except urllib2.URLError, e:
        debug(e.read())
        die("Unable to access %s. The host path may be invalid\n%s" % \
            (url, e))
    except urllib2.HTTPError, e:
        die("Unable to access %s (%s). The host path may be invalid\n%s" % \
            (url, e.code, e.read()))


def api_post(path, fields={}, files={}):
    return process_json(http_post(path, fields, files))


def get_content_type(filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'


def login():
    raise 'Login'

def create_review_request(changenum, repository_path):
    try:
        debug("Attempting to create review request for %s" % changenum)
        rsp = api_post('/api/json/reviewrequests/new/', {
            'changenum': changenum,
            'repository_path': repository_path,
        })
    except APIError, e:
        rsp, = e.args

        if rsp['err']['code'] == 204: # Change number in use
            debug("Review request already exists. Updating it...")
            rsp = api_post(
                '/api/json/reviewrequests/%s/update_from_changenum/' %
                rsp['review_request']['id'])
        else:
            raise e

    debug("Review request created")
    return rsp['review_request']


def get_repository_paths():
    f = os.popen('p4 info', 'r')
    data = f.read()
    f.close()

    m = re.search(r'^Server address: (.+)$', data, re.M)
    if m == None:
        die("Unable to get the server repository.")

    repository_path = m.group(1)

    try:
        import socket
        hostname, port = repository_path.split(":")
        info = socket.gethostbyaddr(hostname)
        repository_path = "%s:%s" % (info[0], port)
    except socket.gaierror:
        pass

    debug("Repository path '%s'" % repository_path)

    return repository_path, ""


def write_file_from_perforce(depot_path, tmpfile):
    """
    Grabs a file from Perforce and writes it to a temp file. We do this
    wrather than telling p4 print to write it out in order to work around
    a permissions bug on Windows.
    """
    debug('Writing "%s" to "%s"' % (depot_path, tmpfile))

    f = os.popen('p4 print -q "%s"' % depot_path)
    data = f.read()
    f.close()

    f = open(tmpfile, "w")
    f.write(data)
    f.close()


def generate_diff(changenum):
    debug("Generating diff for changenum %s" % changenum)

    f = os.popen('p4 change -o %s' % changenum, 'r')
    data = f.read()
    f.close()

    client = None

    # Get the status and client of the change list.
    m = re.search(r'^Client:\t(.+)$', data, re.M)
    if m == None:
        die("Unable to get the client for this change list.")
    else:
        client = m.group(1)

    m = re.search(r'^Status:\t(.+)$', data, re.M)
    if m == None:
        die("Unable to get the status of this change list.")
    else:
        if m.group(1) != "pending":
            die("The change number %s is not pending." % changenum)

    # Get the file list
    f = os.popen('p4 -c %s opened -c %s' % (client, changenum), 'r')
    lines = f.readlines()
    f.close()

    cwd = os.getcwd()
    diff_lines = []

    fd, empty_file = mkstemp()
    os.close(fd)

    fd, tmpfile1 = mkstemp()
    os.close(fd)

    fd, tmpfile2 = mkstemp()
    os.close(fd)

    for line in lines:
        m = re.search(r'^([^#]+)#(\d+) - (\w+) (default )?change', line)
        if not m:
            die("Unsupported line from p4 opened: %s" % line)

        depot_path = m.group(1)
        revision = m.group(2)
        changetype = m.group(3)

        f = os.popen('p4 -c %s where "%s"' % (client, depot_path))
        where_info = f.read()
        f.close()

        m = re.match(r'%s \/\/.+ (.+)$' % depot_path, where_info)
        if not m:
            die("Unsupported line from p4 where: %s" % where_info)

        local_name = m.group(1)

        old_file = new_file = empty_file
        old_depot_path = new_depot_path = None
        changetype_short = None

        if changetype == 'edit' or changetype == 'integrate':
            old_depot_path = "%s#%s" % (depot_path, revision)
            new_file = local_name
            changetype_short = "M"
        elif changetype == 'add' or changetype == 'branch':
            new_file = local_name
            changetype_short = "A"
        elif changetype == 'delete':
            old_depot_path = "%s#%s" % (depot_path, revision)
            changetype_short = "D"
        else:
            die("Unknown change type '%s' for %s" % (changetype, depot_path))

        if old_depot_path:
            write_file_from_perforce(old_depot_path, tmpfile1)
            old_file = tmpfile1

        if new_depot_path:
            write_file_from_perforce(new_depot_path, tmpfile2)
            new_file = tmpfile2

        try:
					new_file_date = time.ctime(os.stat(new_file).st_mtime)
        except :
					new_file_date = time.ctime()

        debug('diff -urNp "%s" "%s"' % (old_file, new_file))
        f = os.popen('diff -urNp "%s" "%s"' % (old_file, new_file), 'r')
        dl = f.readlines()
        f.close()

        if local_name.startswith(cwd):
            local_path = local_name[len(cwd) + 1:]
        else:
            local_path = local_name
        if dl == [] or dl[0].startswith("Binary files ") \
          or dl[0].endswith("No such file or directory") \
          or len(dl) <= 1:
            if dl == []:
                print "Warning: %s in your changeset is unmodified" % \
                    local_path

            dl.insert(0, "==== %s#%s ==%s== %s ====\n" % \
                (depot_path, revision, changetype_short, local_path))
        else:
            debug(dl[1])
            m = re.search(r'(\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d)', dl[1])
            if not m:
                die("Unable to parse diff header: %s" % dl[1])

            timestamp = str(new_file_date) #m.group(1)

            dl[0] = "--- %s  %s#%s\n" % (local_path, depot_path, revision)
            dl[1] = "+++ %s  %s\n" % (local_path, timestamp)

        diff_lines += dl


    os.unlink(empty_file)
    os.unlink(tmpfile1)
    os.unlink(tmpfile2)

    return ''.join(diff_lines)


def upload_diff(review_request, changenum):
    diff_content = generate_diff(changenum)

    debug("Uploading diff")
    rsp = api_post('/api/json/reviewrequests/%s/diff/new/' %
                   review_request['id'], {},
                   {'path': {'filename': 'diff', 'content': diff_content}})



def tempt_fate(changenum, repository_path, client_root):
    try:
        review_request = create_review_request(changenum, repository_path)
    except APIError, e:
        rsp, = e.args
        if rsp['err']['code'] == 103: # Not logged in
            login()
            return tempt_fate(changenum, repository_path, client_root)

        die("Error creating review request: %s (code %s)" % \
            (rsp['err']['msg'], rsp['err']['code']))


    try:
        upload_diff(review_request, changenum)
    except APIError, e:
        rsp, = e.args
        print "Error uploading diff: %s (%s)" % (rsp['err']['msg'],
                                                 rsp['err']['code'])
        die("Your review request still exists, but the diff is not attached.")

    print 'Review request posted.'
    print
    print 'URL: %s/r/%s/' % (REVIEWBOARD_HOST, review_request['id'])
    return review_request


def getUsername():
    f = os.popen('p4 info', 'r')
    data = f.read()
    f.close()
    
    m = re.search(r'^User name: (.+)$', data, re.M)
    return m.group(1)

def getPendingCLs(username):
    cmd = 'p4 changes -u %s -s pending' % username
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
	    cls.append((num, desc))
	    #print "%s: %s" % (num, desc)
    return cls

def line_count(changenum):
	lines = generate_diff(changenum).split("\n")
	add = 0
	sub = 0
	for l in lines:
		if l.startswith("+"):
			add += 1
		elif l.startswith("-"):
			sub += 1
	diff = add - sub
	return (add, sub)

def try_post(changenum):
    try:
        cj.load(cookiefile)
    except IOError:
        login()
    repository_path, client_root = get_repository_paths()
    return tempt_fate(changenum, repository_path, client_root)

def main():
    if REVIEWBOARD_HOST == None:
        print "post-review has not been configured. Please edit post-review"
        print "and modify the Configuration section at the top of the script."
        sys.exit(1)

    parser = OptionParser(usage="%prog [-p] [-o] changenum",
                          version="%prog " + VERSION)
    #parser.add_option("-p", "--publish",
    #                  action="store_true", dest="publish", default=False,
    #                  help="publish the review request immediately after submitting")
    #parser.add_option("-o", "--open",
    #                  action="store_true", dest="open_browser", default=False,
    #                  help="open a web browser to the review request page")
    parser.add_option("--output-diff",
                      action="store_true", dest="output_diff_only",
                      default=False,
                      help="outputs a diff to the console and exits. Does not post")
    parser.add_option("--line-count",
                      action="store_true", dest="output_line_count",
                      default=False,
                      help="outputs a count of lines changed")
    parser.add_option("--list-cl",
		      action="store_true", dest="output_list_cl",
		      default=False,
		      help="Outputs current users outstanding CLs")
    parser.add_option("--server", dest="server",
                      metavar="SERVER",
                      help="specify a different Review Board server to use")
    parser.add_option("-d", "--debug", action="store_true",
                      dest="debug", default=False, help="display debug output")

    (globals()["options"], args) = parser.parse_args()


    if options.output_list_cl:
    	for c in getPendingCLs(getUsername()):
		print "%s: %s" % c
	sys.exit(0)

    if len(args) != 1:
        parser.error("specify the change number of a pending changeset")

    changenum = args[0]

    if options.server:
        globals()["REVIEWBOARD_HOST"] = options.server

    if options.output_diff_only:
        print generate_diff(changenum)
        sys.exit(0)

    if options.output_line_count:
	lines = generate_diff(changenum).split("\n")
	add = 0
	sub = 0
	for l in lines:
		if l.startswith("+"):
			add += 1
		elif l.startswith("-"):
			sub += 1
	diff = add - sub
	print "%s Line(s) Added" % add
	print "%s Line(s) Removed" % sub
	if diff < 0:
		print "File reduced by %s Line(s)" % -diff
	else:
		print "File expanded by %s Line(s)" % diff
	sys.exit(0)

    # Let's begin.
    try:
        cj.load(cookiefile)
    except IOError:
        login()

    repository_path, client_root = get_repository_paths()
    tempt_fate(changenum, repository_path, client_root)


if __name__ == "__main__":
    main()
