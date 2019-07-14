#!/usr/bin/python

##########################################################################
# Get data from Launchpad project and put into a CSV file for further
# processing. Record Important fields about bugs
##########################################################################

import sys
import csv
import os
import datetime
import xlsxwriter

from launchpadlib.launchpad import Launchpad

WORK_DIR = os.getcwd()

ALL_STATUSES = [
    'New',
    'Incomplete',
    'Triaged',
    'Opinion',
    'Confirmed',
    'In Progress']

fieldnames = \
    'Bug ID Number', 'Title', 'Importance', \
    'Status', 'Assignee', 'Reporter', 'Tags', \
    'Web Link', 'Link to Duplicates of bug', \
    'Private', 'Security Related', 'Created Time', \
    'Last Updated Time', 'Date Triaged', 'Severity', \
    'Reproducible', 'Repro Rate', 'Workaround', 'Comments'

# in the workbook, multiple worksheets will be created
# for each of these tags:
targetTags = ['stx.2.0', 'stx.distro.openstack', 'stx.distro.other', \
              'stx.containers', 'stx.networking', 'stx.upstream']

def limit_time_str(aDateTime):
    """Limit datetime string to remove Milliseconds and Seconds"""
    return None if aDateTime is None else aDateTime.strftime(
        '%Y-%m-%d %H:%M UTC')

def get_bug_info_tuple(a_bug):
    """
    Get a tuple of information needed from bug

    This tuple is ordered as listed in the fieldnames tuple, defined previously
    """
    bugInfo = a_bug.bug
    bugInfoId = bugInfo.id
    bugInfoTitle = bugInfo.title.encode('utf-8')
    bugImportance = a_bug.importance.encode('utf-8')
    bugStatus = a_bug.status.encode('utf-8')
    try:
        bugAssignee = a_bug.assignee.name.encode('utf-8')
    except:
        bugAssignee = u'Not Assigned'
    try:
        bugReporter = a_bug.owner.name.encode('utf-8')
    except:
        bugReporter = a_bug.owner.encode('utf-8')
    bugInfoTags = bugInfo.tags
    bugWebLink = a_bug.web_link.encode('utf-8')
    #bugIsComplete = a_bug.is_complete
    bugDuplicateOfLink = bugInfo.duplicate_of_link
    bugPrivate = bugInfo.private
    bugSecurityRelated = bugInfo.security_related
    if bugPrivate is True:
        if bugSecurityRelated is True:
            bugInfoTitle = None
    bugLastUpdatedDate = limit_time_str(bugInfo.date_last_updated)
    #bugAssignedDate = limit_time_str(a_bug.date_assigned)
    #bugClosedDate = limit_time_str(a_bug.date_closed)
    #bugConfirmedDate = limit_time_str(a_bug.date_confirmed)
    bugCreatedDate = limit_time_str(a_bug.date_created)
    #bugDateFixCommitted = limit_time_str(a_bug.date_fix_committed)
    #bugDateFixReleased = limit_time_str(a_bug.date_fix_committed)
    #bugDateInProgress = limit_time_str(a_bug.date_in_progress)
    #bugDateIncomplete = limit_time_str(a_bug.date_incomplete)
    #bugDateLeftClosed = limit_time_str(a_bug.date_left_closed)
    #bugDateLeftNew = limit_time_str(a_bug.date_left_new)
    bugDateTriaged = limit_time_str(a_bug.date_triaged)

    # Extended Columns
    bugSeverity = 'TBD'
    bugReproducible = 'TBD (Yes or No)'
    bugReproduceRate = 'TBD (%)'
    bugWorkaround = 'TBD (Yes or No)'
    bugComments = 'Other Comments'
    # Create string with info and write
    # match tuple data with 'fieldnames'
    string = \
        bugInfoId, bugInfoTitle, bugImportance, \
        bugStatus, bugAssignee, bugReporter, str(bugInfoTags), \
        bugWebLink, bugDuplicateOfLink, \
        bugPrivate, bugSecurityRelated, bugCreatedDate, \
        bugLastUpdatedDate, bugDateTriaged, bugSeverity, \
        bugReproducible, bugReproduceRate, bugWorkaround, bugComments
    return string


def query_yes_no(question, default="no"):
    """
    Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")


def use_cred():
    """Get a boolean value on whether to use credentials"""
    prompt = "Use Credentials? (N for Anonymous)"
    return query_yes_no(question=prompt, default="no")


def bugs_to_csv(promptArgs=False):
    """
    Get bugs from project[starlingx], extract relevant information
    and write to a csv file, if a csv file has been previously made on
    the same date then prompt the user on whether to overwrite it

    :param promptArgs: A Boolean which is used to determine whether
    to use authorized credentials or anonymous access to the project
    """
    username = os.environ['USER']
    cachedir = "/tmp/" + username + "/.cache/.launchpadlib"
    anon_or_auth = 'anon_'

    if promptArgs is False:
        launchpad = Launchpad.login_anonymously(
            'anonymously', 'production', cachedir, version='devel')

    # Clear credentials if they already existed and check for X11 forwarding
    elif promptArgs is True:
        def no_credential():
            print("Can't proceed without Launchpad credential.")
            sys.exit()

        if os.path.isfile(cachedir+'/auth.txt'):
            os.remove(cachedir+'/auth.txt')

        try:
            os.environ['DISPLAY']
        except KeyError:
            raise ValueError('X11 Disabled (or) and DISPLAY Variable unset')

        launchpad = Launchpad.login_with(
            'authorize', 'production', cachedir,
            credentials_file=cachedir + '/auth.txt',
            credential_save_failed=no_credential, version='devel')
        anon_or_auth = 'authorized_'
    else:
        raise ValueError("Prompt argument was not a boolean")

    # Try to get bugs and place to csv file, if stopped midway or finishes,
    # delete authentication credentials (if used)
    try:
        project = launchpad.projects['starlingx']

        bugs = project.searchTasks(status=ALL_STATUSES, omit_duplicates=False)
        currentDate = datetime.datetime.now().strftime('%Y-%m-%d-%H')
        """
        file_n = 'launchpad-bugs-' + anon_or_auth + currentDate + '.csv'
        print('Destination file is: ' + WORK_DIR + file_n)

        if os.path.isfile(DEST_DIR + file_n):
            updateFileQuestion = "File Exists, do you want to overwrite it?"
            overWriteFile = query_yes_no(updateFileQuestion, "no")
            if overWriteFile is False:
                raise ValueError("Overwrite existing file is False")
        with open(DEST_DIR + file_n, 'wb') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(fieldnames)
            for each_bug in bugs:
                bugInfoString = get_bug_info_tuple(each_bug)
                writer.writerow(bugInfoString)
        """
        # create my workbook
        workbook_filename = 'stx_lp_workbook-' + anon_or_auth + currentDate + '.xlsx'
        workbook = xlsxwriter.Workbook(WORK_DIR + "/"+ workbook_filename)
        print "Starting write LP data to worksheets according to the tag ......"
        for tag in targetTags:
            worksheet = workbook.add_worksheet(tag)
            # with each of sheets (named under targeted tag),
            # loop all bugs to find the bug with such a tag,
            # and wite the bug one by one into this sheeet.
            row = 1;
            worksheet.write_row('A'+str(row), list(fieldnames))
            #worksheet = stx_lp_workbook.get_worksheet_by_name(tag)
            for each_bug in bugs:
                if tag in each_bug.bug.tags:
                    row += 1
                    bugId = str(each_bug.bug.id)
                    print "writting LP " + bugId + " at row #" + str (row) + " into sheet: " + tag
                    bugInfoString = get_bug_info_tuple(each_bug)
                    worksheet.write_row('A'+str(row), list(bugInfoString))

        print "Complete writting worksheets and closed workbook!"
        workbook.close()

    except BaseException as e:
        print e.message, e.args

    finally:
        workbook.close()
        if anon_or_auth == 'authorized_':
            os.remove(cachedir + '/auth.txt')


if __name__ == "__main__":
    boolCred = use_cred()
    bugs_to_csv(boolCred)

