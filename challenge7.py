#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: javiergayala
# @Date:   2014-02-26 10:43:04
# @Last Modified by:   javiergayala
# @Last Modified time: 2014-02-28 13:29:55


"""challenge7.py"""

__appname__ = "challenge7.py"
__author__ = "javiergayala"
__version__ = "0.1"
__license__ = "GNU GPL 3.0 or later"

import os
import sys
import getpass
import time
import logging
import argparse
import ConfigParser
from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver
from libcloud.loadbalancer.base import Member, Algorithm
from libcloud.loadbalancer.types import State
from libcloud.loadbalancer.types import Provider as ProviderLB
from libcloud.loadbalancer.providers import get_driver as get_lbdriver

log = logging.getLogger(__name__)
credsFile = os.path.expanduser('~') + '/.rackspace_cloud_credentials'
lbErrorPage = """
<html><head><title> Cloud LB Error Page </title> <style type="text/css" media=
"screen">body{padding:20px;text-align:center;background:#fff}.msgbox{position
    :absolute;width:400px;height:400px;left:50%;top:50%;margin-left:-200px;
    margin-top:-200px;border-radius:0 79px 0 79px;-moz-border-radius:0 79px;
    -webkit-border-radius:0 79px 0 79px;border:8px solid #000;
    background-color:#cf2d36}.innerbox{position:relative;margin-top:-75px;
        margin-left:-400px;top:50%;left:50%;overflow:hidden;}p{width:40%;
            padding-left:30%;} </style> </head> <body> <div class='msgbox'>
            <div class='innerbox'> <h1> Whoops! </h1> <h3> Warning! Achtung!
             Peligro! </h3> <p>For the record, I <em>told</em> our dev that
             pushing untested code into production in the middle of the day
              was a bad idea....</p> </div> </div> </body></html>
"""


class Challenge7(object):
    """Class for creating 2 servers and 1 LB for Challenge 7.

    Instance Variables:
    self.credsFile -- Location of the file containing the credentials
    self.raxAPIKey -- API Key to use for authenticating
    self.raxUser -- Username to use for authenticating
    self.raxRegion -- Region to build devices
    self.flavor -- Flavor to use for the servers
    self.image -- Image to use for the servers
    self.numServers -- Number of servers to build
    self.newSvrs -- List of the newly built servers
    self.svrBaseName -- Base hostname to use for the servers
    self.domain -- Domain name
    self.svrsCreated -- List containing the servers that were created
    self.lbname -- Name to use for the LB
    self.lbObj -- Object representing the created LB
    self.lbPort -- Port used by the LB
    self.lbProtocol -- Protocol used by the LB
    self.lbErrorPage -- HTML used for the LB Error Page

    Methods:
    self.authenticate() -- Authenticate with Rackspace Cloud
    self.raxLoginPrompt() -- Prompt for user credentials
    self.parseConfig() -- Parse the config file for credentials & region
    self.list() -- List & prompt for the available flavors and images
    self.createServer() -- Create a new server
    self.createLB() -- Create a new LB and set error page if defined
    """
    def __init__(self, credsFile=credsFile, raxAPIKey=None, raxUser=None,
                 raxRegion='ord', flavor='2',
                 image='2ab974de-9fe5-4f5b-9d58-766a59f3de61', numServers=2,
                 svrBaseName='chall7', domain='test.com', svrsCreated=[],
                 lbname='chall7-lb', lbObj=None, lbPort=80, lbProtocol='HTTP',
                 lbErrorPage=None):
        super(Challenge7, self).__init__()
        self.credsFile = credsFile
        self.raxAPIKey = raxAPIKey
        self.raxUser = raxUser
        self.raxRegion = raxRegion
        self.flavor = flavor
        self.image = image
        self.numServers = numServers
        self.newSvrs = []
        self.svrBaseName = svrBaseName
        self.domain = domain
        self.svrsCreated = svrsCreated
        self.lbname = lbname
        self.lbObj = lbObj
        self.lbPort = lbPort
        self.lbProtocol = lbProtocol
        self.lbErrorPage = lbErrorPage
        try:
            self.authenticate()
        except:
            print "Couldn't login"
            log.debug("User: %s" % self.raxUser)
            log.debug("API: %s" % self.raxAPIKey)
            log.debug("Region: %s" % self.raxRegion)
            sys.exit(2)

    def authenticate(self):
        """Authenticate using credentials in config file, or fall back to
            prompting the user for the credentials."""
        self.parseConfig()
        log.debug("User: %s" % self.raxUser)
        log.debug("API Key: %s" % self.raxAPIKey)
        if (self.raxUser is None) or (self.raxAPIKey is None):
            self.raxLoginPrompt()
        try:
            self.driver = get_driver(Provider.RACKSPACE)
            self.lbdriv = get_lbdriver(ProviderLB.RACKSPACE)
            self.conn = self.driver(self.raxUser, self.raxAPIKey,
                                    region=self.raxRegion)
            self.lbcn = self.lbdriv(self.raxUser, self.raxAPIKey,
                                    region=self.raxRegion)
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
        """Parse the config file for credentials and region."""
        config = ConfigParser.ConfigParser()
        try:
            log.debug("Trying to read file: %s" % self.credsFile)
            config.read(self.credsFile)
        except Exception, e:
            return
        config.read(self.credsFile)
        log.debug("Config file read")
        try:
            log.debug("Trying to read username from %s" % self.credsFile)
            self.raxUser = config.get('rackspace_cloud', 'username')
            log.debug("Trying to read APIKey from %s" % self.credsFile)
            self.raxAPIKey = config.get('rackspace_cloud', 'api_key')
            log.debug("Setting region to: %s"
                      % config.get('rackspace_cloud', 'region').lower())
            self.raxRegion = config.get('rackspace_cloud', 'region').lower()
        except ConfigParser.NoOptionError:
            log.debug("Missing an option in the config file")
        return

    def list(self):
        """List the available images and flavors, and prompt the user
        to ask which to use for creating the new servers."""
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
        """Create a new server"""
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
        self.newSvrs = self.conn.wait_until_running(self.svrsCreated,
                                                    wait_period=5,
                                                    timeout=600,
                                                    ssh_interface='public_ips')
        log.debug("Servers Online")
        return

    def createLB(self):
        """Create a new LB, attach the servers to it, and attach an error
        page if one is defined."""
        members = []
        self.createServer()
        for i in self.newSvrs:
            log.debug("Adding member %s" % i[0].name)
            members.append(Member(i[0].uuid, i[0].private_ips[0], str(80)))
        log.debug("Members added")
        members = tuple(members)
        log.debug("Creating LB %s" % self.lbname)
        lb = self.lbcn.create_balancer(name=self.lbname,
                                       port=self.lbPort,
                                       protocol=self.lbProtocol,
                                       algorithm=Algorithm.ROUND_ROBIN,
                                       members=members)
        print("Waiting for the load-balancer to become available...")
        while True:
            self.lbObj = self.lbcn.get_balancer(balancer_id=lb.id)
            if self.lbObj.state == State.RUNNING:
                break
            print("Load-balancer not ready yet, sleeping 20 seconds...")
            time.sleep(20)
        print("Load-balancer is ready!")
        if self.lbErrorPage is not None:
            print("Updating Error Page on LB")
            self.lbObj = self.lbcn.ex_update_balancer_error_page(self.lbObj,
                                                                 self.lbErrorPage)
        print("LB Creation Complete!")
        print("LB ID: %s" % self.lbObj.id)
        print("LB Name: %s" % self.lbObj.name)
        print("LB IP: %s" % self.lbObj.ip)
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
    args = parser.parse_args()

    log_levels = [logging.CRITICAL, logging.ERROR, logging.WARNING,
                  logging.INFO, logging.DEBUG]
    log_index = 2 + (args.verbose if args.verbose <= 2 else 2) - \
                    (args.quiet if args.quiet <= 2 else 2)
    logging.basicConfig(level=log_levels[log_index],
                        format="%(asctime)s %(levelname)s %(message)s")

    log.debug("CLI arguments: %s" % args)
    raxConn = Challenge7(credsFile, lbErrorPage=lbErrorPage)
    raxConn.createLB()

    return

if __name__ == "__main__":
    main()
