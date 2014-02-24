#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: javiergayala
# @Date:   2014-02-19 14:15:21
# @Last Modified by:   javiergayala
# @Last Modified time: 2014-02-24 13:09:33

"""challenge5.py"""

__appname__ = "challenge5.py"
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
    """Class for connecting and manipulating CloudDB for challenge 5."""
    def __init__(self, credsFile):
        super(CloudDB, self).__init__()
        self.credsFile = credsFile
        try:
            self.authenticate()
        except:
            print "Couldn't login"
            sys.exit(2)
        self.cdb = pyrax.cloud_databases
        self.dbs = {}
        self.cdbinst = None

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

    def choose_flavors(self):
        print("Choose a flavor of Cloud DB:")
        for flav in self.cdb.list_flavors():
            print("%s: %s" % (flav.id, flav.name))
        self.flavor = raw_input("Flavor: ")
        while not self.flavor.isdigit():
            self.flavor = raw_input("Flavor: ")
        self.disk = raw_input("How many GBs (GeeBees) should the disk " +
                              "be? (Numbers only): ")
        while not self.disk.isdigit():
            self.disk = raw_input("How many GBs (GeeBees) should the disk " +
                                  "be? (Numbers only): ")
        self.flavor = int(self.flavor)
        self.disk = int(self.disk)
        return

    def check_name(self):
        self.name = raw_input('Enter Name for CDB Instance: ')
        dbinst_exists = None
        try:
            self.cdb.find(name=self.name)
            dbinst_exists = True
        except exc.NotFound:
            dbinst_exists = False
        if dbinst_exists is True:
            print("The name '%s' is already in use." % self.name)
            ans = raw_input('Would you like to use a variant such '
                            'as %s-1 instead? [y/n]: ' % self.name)
            if ans.lower() == 'y':
                self.name = self.name + "-1"
            else:
                print("Can not proceed with a duplicate name")
                sys.exit(1)
        return

    def create_instance(self):
        try:
            self.check_name()
        except Exception, e:
            raise e
        try:
            print("Building Instance %s" % self.name)
            self.cdbinst = self.cdb.create(self.name, flavor=self.flavor,
                                           volume=self.disk)
        except Exception as e:
            raise e
        utils.wait_until(self.cdbinst, "status", ['ACTIVE', 'ERROR'],
                         interval=5, attempts=0, verbose=True)
        return

    def create_dbs(self):
        numdbs = raw_input("How many databases would you like to create?: ")
        while not numdbs.isdigit():
            numdbs = raw_input("How many databases would you like to " +
                               "create?: ")
        basename = raw_input("What base name should be used for " +
                             "the new DB's?: ")
        if not self.cdbinst:
            self.create_instance()
            pass
        for x in xrange(1, int(numdbs) + 1):
            dbname = basename
            if x != 1:
                dbname = basename + str(x)
            self.dbs[dbname] = self.cdbinst.create_database(dbname)
        print("URL for your CloudDB Instance: %s\n" %
              self.cdbinst.links[0]['href'])
        return


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-c', '--config', dest='configFile',
                        help="Location of the config file",
                        default=credsFile)
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
        raxConn = CloudDB(args.configFile)
    except:
        print "Couldn't login"
        sys.exit(2)

    log.debug("Logged in")
    raxConn.choose_flavors()
    raxConn.create_dbs()

    return

if __name__ == "__main__":
    main()
