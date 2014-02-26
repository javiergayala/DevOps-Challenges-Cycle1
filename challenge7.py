#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: javiergayala
# @Date:   2014-02-26 10:43:04
# @Last Modified by:   javiergayala
# @Last Modified time: 2014-02-26 15:26:42


"""challenge7.py"""

__appname__ = "challenge7.py"
__author__ = "javiergayala"
__version__ = "0.0"
__license__ = "GNU GPL 3.0 or later"

import logging
import argparse
import ConfigParser
from pprint import pprint
import os
import sys
import getpass
import time
from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver
from libcloud.loadbalancer.base import Member, Algorithm
from libcloud.loadbalancer.types import State
from libcloud.loadbalancer.types import Provider as ProviderLB
log = logging.getLogger(__name__)

credsFile = os.path.expanduser('~') + '/.rackspace_cloud_credentials'


class Challenge7(object):
    """docstring for Challenge7"""
    def __init__(self, credsFile):
        """Initialize the class

        Arguments:
        credsFile -- Location of the credentials file
        dbInst -- Name of the Cloud DB Instance to connect to
        dbName -- Name of the Cloud DB Database to use
        dbUser -- Name of the Cloud DB User to use
        bu_name -- Name of the backup
        bu_desc -- Description of the backup

        """
        super(Challenge7, self).__init__()
        self.credsFile = credsFile
        self.raxAPIKey = None
        self.raxUser = None
        self.raxRegion = None
        self.flavor = '2'
        self.image = '2ab974de-9fe5-4f5b-9d58-766a59f3de61'
        self.numServers = 2
        self.svrBaseName = 'chall7'
        self.domain = 'test.com'
        self.svrsCreated = []
        self.lbname = 'chall7-lb'
        self.lbObj = None
        self.lbPort = 80
        self.lbProtocol = 'HTTP'
        try:
            self.authenticate()
        except:
            print "Couldn't login"
            sys.exit(2)

    def authenticate(self):
        """Authenticate using credentials in config file, or fall back to
            prompting the user for the credentials."""
        log.debug("Begin parseConfig()")
        self.parseConfig()
        log.debug("End parseConfig()")
        log.debug("User: %s" % self.raxUser)
        log.debug("API Key: %s" % self.raxAPIKey)
        if (self.raxUser is None) or (self.raxAPIKey is None):
            self.raxLoginPrompt()
        try:
            self.driver = get_driver(Provider.RACKSPACE)
            self.lbdriv = get_driver(ProviderLB.RACKSPACE)
            self.conn = self.driver(self.raxUser, self.raxAPIKey)
            self.lbcn = self.lbdriv(self.raxUser, self.raxAPIKey)
            print "Authentication SUCCEEDED!"
        except Exception, e:
            print Exception, e
            raise e
        return

    def raxLoginPrompt(self):
        """Prompt the user for a login name and API Key to use for logging
            into the API."""
        print ("I really hate to ask...but...can I borrow your key?")
        self.raxUser = raw_input('Username: ')
        self.raxAPIKey = getpass.getpass('API Key: ')
        return

    def parseConfig(self):
        config = ConfigParser.ConfigParser()
        try:
            log.debug("Trying to read file: %s" % self.credsFile)
            config.read(self.credsFile)
        except Exception, e:
            return
        config.read(self.credsFile)
        log.debug("Config file read")
        try:
            self.raxUser = config.get('rackspace_cloud', 'username')
            self.raxAPIKey = config.get('rackspace_cloud', 'api_key')
            self.raxRegion = config.get('rackspace_cloud', 'region')
        except ConfigParser.NoOptionError:
            log.debug("Missing an option in the config file")
        return

    def list(self):
        counter = 0
        images = self.conn.list_images()
        flavors = self.conn.list_sizes()
        for i in images:
            print("%s: %s" % (counter, i.name))
            counter += 1
        self.image = images[int(raw_input("Select Image: "))]
        counter = 0
        for i in flavors:
            print("%s: %s" % (counter, i.name))
            counter += 1
        self.flavor = flavors[int(raw_input("Select Flavor: "))]
        return

    def createServer(self):
        print("Creating %s server(s)" % self.numServers)
        self.list()
        for i in xrange(0, self.numServers):
            svrName = '%s-%s.%s' % (self.svrBaseName, i, self.domain)
            self.svrsCreated.append(self.conn.create_node(name=svrName,
                                                          image=self.image,
                                                          size=self.flavor))
            log.debug("Created server: %s" % svrName)
        print("Server Creation requests sent. Waiting for servers to "
              "become available...")
        self.newServers = self.conn.wait_until_running(self.svrsCreated,
                                                       wait_period=5,
                                                       timeout=600,
                                                       ssh_interface='public_ips')
        log.debug("Servers Online")
        return

    def createLB(self):
        members = []
        self.createServer()
        for i in self.newServers:
            log.debug("Adding member %s" % i[0].name)
            members.append(Member(i[0].uuid, i[0].private_ips[0], 80))
        log.debug("Members added")
        members = tuple(members)
        log.debug("Creating LB %s" % self.lbname)
        lb = self.lbcn.create_balancer(name=self.lbname,
                                       algorithm=Algorithm.ROUND_ROBIN,
                                       port=self.lbPort,
                                       protocol=self.lbProtocol,
                                       members=members)
        print("Waiting for the load-balancer to become available...")
        while True:
            self.lbObj = self.lbcn.get_balancer(balancer_id=lb.id)
            if balancer.state == State.RUNNING:
                break
            print("Load-balancer not ready yet, sleeping 20 seconds...")
            time.sleep(20)
        print("Load-balancer is ready!")
        return


def main():
    parser = argparse.ArgumentParser(description=__doc__)
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
    raxConn = Challenge7(credsFile)
    raxConn.createLB()
    
    pass

if __name__ == "__main__":
    main()
