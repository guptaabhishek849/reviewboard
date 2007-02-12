import re

from django.conf import settings

from reviewboard.scmtools.core import *

class PerforceTool(SCMTool):
    def __init__(self,
                 p4port = settings.P4_PORT,
                 p4user = settings.P4_USER,
                 p4password = settings.P4_PASSWORD):
        SCMTool.__init__(self, p4port)

        import p4
        self.p4 = p4.P4()
        self.p4.port = p4port
        self.p4.user = p4user
        self.p4.password = p4password
        self.connected = False

    def _connect(self):
        if not self.connected or self.p4.dropped():
            self.p4.connect()
            self.connected = True

    def get_pending_changesets(self, userid):
        self._connect()
        changes = self.p4.run_changes('-s', 'pending', '-u', userid)
        # XXX: This will need to parse the result
        return changes

    def get_changeset(self, changesetid):
        self._connect()
        return '\n'.join(self.p4.run_describe('-s', str(changesetid)))

    def get_file(self, path, revision=None):
        self._connect()

        file = path
        if revision:
            if revision == PRE_CREATION:
                file = '%s@0' % path
            elif revision == HEAD:
                pass
            else:
                file = '%s@%s' % (path, revision)

        return '\n'.join(self.p4.run_print(path))

    @staticmethod
    def parse_change_desc(changenum, changedesc):
        changeset = ChangeSet()
        changeset.changenum = changenum

        changedesc_keys = {
            'QA Notes': "",
            'Testing Done': "",
            'Documentation Notes': "",
            'Bug Number': "",
            'Reviewed by': "",
            'Approved by': "",
            'Breaks vmcore compatibility': "",
            'Breaks vmkernel compatibility': "",
            'Breaks vmkdrivers compatibility': "",
            'Mailto': "",
        }

        process_summary = False
        process_description = False
        process_files = False

        cur_key = None

        for line in changedesc.split("\n"):
            if line == "Description:":
                process_summary = True
                continue
            elif line == "Files:":
                process_files = True
                cur_key = None
                continue
            elif line.strip() == "":
                if process_summary:
                    process_summary = False
                    process_description = True
                    continue

                line = ""
            elif line.startswith("\t") or line.startswith("    "):
                line = line.lstrip()

                if process_files:
                    changeset.files.append(line)
                    continue
                elif line.find(':') != -1:
                    key, value = line.split(':', 2)

                    if changedesc_keys.has_key(key):
                        process_description = False
                        cur_key = key

                        changedesc_keys[key] = value.lstrip() + "\n"
                        continue

            line += "\n"

            if process_summary:
                changeset.summary += line
            elif process_description:
                changeset.description += line
            elif cur_key != None:
                changedesc_keys[cur_key] += line

        changeset.summary = changeset.summary.strip()
        changeset.description = changeset.description.strip()
        changeset.testing_done = changedesc_keys['Testing Done'].strip()
        changeset.bugs_closed = re.split(r"[, ]+",
                                         changedesc_keys['Bug Number'].strip())

        # This is gross.
        if len(changeset.files) > 0:
            parts = changeset.files[0].split('/')

            if parts[2] == "depot":
                changeset.branch = parts[4]

        return changeset
