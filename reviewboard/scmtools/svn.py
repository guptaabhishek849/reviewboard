import pysvn

from reviewboard.scmtools.core import SCMException, FileNotFoundException, SCMTool
from reviewboard.scmtools.core import HEAD, PRE_CREATION

class SVNTool(SCMTool):
    def __init__(self, repopath):
        if repopath[-1] == '/':
            repopath = repopath[:-1]

        SCMTool.__init__(self, repopath)
        self.client = pysvn.Client()


    def get_file(self, path, revision=HEAD):
        if not path:
            raise FileNotFoundException(path, revision)

        if revision == HEAD:
            r = pysvn.Revision(pysvn.opt_revision_kind.head)
        elif revision == PRE_CREATION:
            raise FileNotFoundException(path, revision)
        else:
            r = pysvn.Revision(pysvn.opt_revision_kind.number, str(revision))

        try:
            return self.client.cat(self.__normalize_path(path), r)
        except pysvn.ClientError, e:
            raise FileNotFoundException(path, revision, str(e))


    def parse_diff_revision(self, file_str, revision_str):
        if revision_str == "(working copy)":
            return HEAD
        elif revision_str.startswith("(revision "):
            revision = revision_str.split()[1][:-1]

            if revision == "0":
                revision = PRE_CREATION

            return file_str, revision
        else:
            raise SCMException("Unable to parse diff revision header '%s'" %
                               revision_str)


    def __normalize_path(self, path):
        if path.startswith(self.repopath):
            return path
        elif path[0] == '/':
            return self.repopath + path
        else:
            return self.repopath + "/" + path
