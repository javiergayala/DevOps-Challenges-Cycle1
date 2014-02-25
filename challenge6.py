#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: javiergayala
# @Date:   2014-02-19 14:15:21
# @Last Modified by:   javiergayala
# @Last Modified time: 2014-02-25 09:54:33

"""challenge6.py"""

__appname__ = "challenge6.py"
__author__ = "javiergayala"
__version__ = "0.0"
__license__ = "GNU GPL 3.0 or later"

import logging
import argparse
import getpass
import pyrax
import pyrax.exceptions as exc
import pyrax.utils as utils
import os
import sys
log = logging.getLogger(__name__)

credsFile = os.path.expanduser('~') + '/.rackspace_cloud_credentials'


class CloudDB(object):
    """Class for connecting and manipulating CloudDB for Challenge 6.

    Instance Variables:
    self.credsFile -- Location of the credentials file
    self.dbInst -- Name of the Cloud DB Instance to connect to
    self.dbName -- Name of the Cloud DB Database to use
    self.dbUser -- Name of the Cloud DB User to use
    self.bu_name -- Name of the backup
    self.bu_desc -- Description of the backup
    self.cdb -- pyrax.cloud_databases connection object
    self.cdbinst -- Cloud DB Instance object
    self.dbObj -- Cloud DB Database object
    self.userObj -- Cloud DB User object
    self.backup -- Cloud DB Backup instance

    Methods:
    self.authenticate() -- Authenticate with Rackspace Cloud
    self.raxLoginPrompt() -- Prompt for user credentials
    self.connect_instance() -- Connect to a Cloud DB Instance
    self.create_backup() -- Create a Cloud DB Backup

    """

    def __init__(self, credsFile, bu_name, bu_desc, dbInst=None, dbName=None,
                 dbUser=None):
        """Initialize the class

        Arguments:
        credsFile -- Location of the credentials file
        dbInst -- Name of the Cloud DB Instance to connect to
        dbName -- Name of the Cloud DB Database to use
        dbUser -- Name of the Cloud DB User to use
        bu_name -- Name of the backup
        bu_desc -- Description of the backup

        """
        super(CloudDB, self).__init__()
        self.credsFile = credsFile
        self.dbInst = dbInst
        self.dbName = dbName
        self.dbUser = dbUser
        self.bu_name = bu_name
        self.bu_desc = bu_desc
        try:
            self.authenticate()
        except:
            print "Couldn't login"
            sys.exit(2)
        self.cdb = pyrax.cloud_databases
        self.cdbinst = None
        self.dbObj = None
        self.userObj = None
        self.backup = None

    def authenticate(self):
        """Authenticate using credentials in config file, or fall back to
            prompting the user for the credentials."""
        try:
            pyrax.set_credential_file(self.credsFile)
            print "Authentication SUCCEEDED!"
        except exc.AuthenticationFailed:
            print ("Can't seem to find the right key on my keyring... ")
            print "Authentication Failed using the " + \
                "credentials in " + str(self.credsFile)
            self.raxLoginPrompt()
        except exc.FileNotFound:
            print ("I seem to have misplaced my keyring... Awkward...")
            print "No config file found: " + str(self.credsFile)
            self.raxLoginPrompt()
        return

    def raxLoginPrompt(self):
        """Prompt the user for a login name and API Key to use for logging
            into the API."""
        print ("I really hate to ask...but...can I borrow your key?")
        self.raxUser = raw_input('Username: ')
        self.raxAPIKey = getpass.getpass('API Key: ')
        try:
            pyrax.set_credentials(self.raxUser, self.raxAPIKey)
            print "Authentication SUCCEEDED!"
        except exc.AuthenticationFailed:
            print "Authentication Failed using the " + \
                "Username and API Key provided!"
            sys.exit(1)
        return

    def connect_instance(self):
        """Connect to the CloudDB Instance."""
        try:
            self.cdbinst = self.cdb.find(name=self.dbInst)
        except exc.NotFound:
            print("Can't find instance: %s" % e)
            sys.exit(1)
        try:
            self.dbObj = self.cdbinst.get_database(self.dbName)
        except exc.NoSuchDatabase:
            print("Can't find database: %s" % self.dbName)
            sys.exit(1)
        try:
            self.userObj = self.cdbinst.get_user(self.dbUser)
        except exc.NoSuchDatabaseUser:
            print("Can't find user: %s" % self.dbUser)
            sys.exit(1)
        return

    def refresh_info(self):
        """Refresh the backup instance info."""
        self.backup = self.backup.manager.find(name=self.bu_name)
        return

    def create_backup(self):
        """Create the backup and watch it until it completes."""
        self.backup = self.cdbinst.create_backup(self.bu_name,
                                                 description=self.bu_desc)
        print("Creating backup for DB '%s'" % self.dbName)
        self.refresh_info()
        utils.wait_for_build(self.backup, "status", ['COMPLETED', 'FAILED'],
                             interval=5, attempts=0, verbose=True)
        return


def main():
    """Parse the command line arguments and launch the backup."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-c', '--config', dest='configFile',
                        help="Location of the config file",
                        default=credsFile)
    parser.add_argument('-i', '--instance', dest='dbInst',
                        help="Name of the Database Instance", required=True)
    parser.add_argument('-d', '--database', dest='dbName',
                        help="Name of the Database", required=True)
    parser.add_argument('-u', '--user', dest='dbUser',
                        help="Name of the Database User", required=True)
    parser.add_argument('-bn', '--backup-name', dest='bu_name',
                        help="Name of the backup", default='backup')
    parser.add_argument('-bd', '--backup-description', dest='bu_desc',
                        help="Description of the backup", default=None)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", action="count", default=0,
                       help="Increase verbosity. \
                       Supply twice for increased effect.")
    group.add_argument("-q", "--quiet", action="count", default=0,
                       help="Decrease verbosity. Supply twice for \
                       increased effect.")
    parser.add_argument("--version", action="version",
                        version="%s %s by %s. License: %s" %
                        (__appname__, __version__, __author__, __license__))
    # parser.add_argument("positional_argument", action="store",
    #                     help="Helptext")
    # -- more args --
    args = parser.parse_args()

    log_levels = [logging.CRITICAL, logging.ERROR, logging.WARNING,
                  logging.INFO, logging.DEBUG]
    log_index = 2 + (args.verbose if args.verbose <= 2 else 2) - \
                    (args.quiet if args.quiet <= 2 else 2)
    logging.basicConfig(level=log_levels[log_index],
                        format="%(asctime)s %(levelname)s %(message)s")

    log.debug("CLI arguments: %s" % args)

    try:
        log.debug("Establishing connection to the API")
        raxConn = CloudDB(args.configFile, args.bu_name, args.bu_desc,
                          args.dbInst, args.dbName, args.dbUser)
    except:
        print "Couldn't login"
        sys.exit(2)

    log.debug("Logged in")
    log.debug("Connecting to Instance: %s" % args.dbInst)
    raxConn.connect_instance()
    log.debug("DB Instance: %s" % raxConn.cdbinst)
    log.debug("DB Name: %s" % raxConn.dbObj)
    log.debug("DB User: %s" % raxConn.userObj)
    log.debug("Creating the Backup: %s" % args.bu_name)
    raxConn.create_backup()

    return

if __name__ == "__main__":
    main()
