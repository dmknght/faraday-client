#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Faraday Penetration Test IDE
Copyright (C) 2013  Infobyte LLC (http://www.infobytesec.com/)
See the file 'doc/LICENSE' for the license information

'''
from __future__ import with_statement
from faraday.client.plugins import core
from faraday.client.model import api
import re
import os
import sys
import socket
import urllib
from bs4 import BeautifulSoup

try:
    import xml.etree.cElementTree as ET
    import xml.etree.ElementTree as ET_ORIG
    ETREE_VERSION = ET_ORIG.VERSION
except ImportError:
    import xml.etree.ElementTree as ET
    ETREE_VERSION = ET.VERSION

ETREE_VERSION = [int(i) for i in ETREE_VERSION.split(".")]

current_path = os.path.abspath(os.getcwd())

__author__ = "Francisco Amato"
__copyright__ = "Copyright (c) 2013, Infobyte LLC"
__credits__ = ["Francisco Amato"]
__license__ = ""
__version__ = "1.0.0"
__maintainer__ = "Francisco Amato"
__email__ = "famato@infobytesec.com"
__status__ = "Development"


class NetsparkerXmlParser(object):
    """
    The objective of this class is to parse an xml file generated by the netsparker tool.

    TODO: Handle errors.
    TODO: Test netsparker output version. Handle what happens if the parser doesn't support it.
    TODO: Test cases.

    @param netsparker_xml_filepath A proper xml generated by netsparker
    """

    def __init__(self, xml_output):
        self.filepath = xml_output

        tree = self.parse_xml(xml_output)
        if tree:
            self.items = [data for data in self.get_items(tree)]
        else:
            self.items = []

    def parse_xml(self, xml_output):
        """
        Open and parse an xml file.

        TODO: Write custom parser to just read the nodes that we need instead of
        reading the whole file.

        @return xml_tree An xml tree instance. None if error.
        """
        try:
            tree = ET.fromstring(xml_output)
        except SyntaxError, err:
            self.devlog("SyntaxError: %s. %s" % (err, xml_output))
            return None

        return tree

    def get_items(self, tree):
        """
        @return items A list of Host instances
        """
        for node in tree.findall("vulnerability"):
            yield Item(node)


class Item(object):
    """
    An abstract representation of a Item


    @param item_node A item_node taken from an netsparker xml tree
    """

    def re_map_severity(self, severity):
        if severity == "Important":
            return "high"
        return severity

    def __init__(self, item_node):
        self.node = item_node
        self.url = self.get_text_from_subnode("url")

        host = re.search(
            "(http|https|ftp)\://([a-zA-Z0-9\.\-]+(\:[a-zA-Z0-9\.&amp;%\$\-]+)*@)*((25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9])\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[0-9])|localhost|([a-zA-Z0-9\-]+\.)*[a-zA-Z0-9\-]+\.(com|edu|gov|int|mil|net|org|biz|arpa|info|name|pro|aero|coop|museum|[a-zA-Z]{2}))[\:]*([0-9]+)*([/]*($|[a-zA-Z0-9\.\,\?\'\\\+&amp;%\$#\=~_\-]+)).*?$", self.url)

        self.protocol = host.group(1)
        self.hostname = host.group(4)
        self.port = 80

        if self.protocol == 'https':
            self.port = 443
        if host.group(11) is not None:
            self.port = host.group(11)

        self.name = self.get_text_from_subnode("type")
        self.desc = self.get_text_from_subnode("description")
        self.severity = self.re_map_severity(self.get_text_from_subnode("severity"))
        self.certainty = self.get_text_from_subnode("certainty")
        self.method = self.get_text_from_subnode("vulnerableparametertype")
        self.param = self.get_text_from_subnode("vulnerableparameter")
        self.paramval = self.get_text_from_subnode("vulnerableparametervalue")
        self.reference = self.get_text_from_subnode("externalReferences")
        self.resolution = self.get_text_from_subnode("actionsToTake")
        self.request = self.get_text_from_subnode("rawrequest")
        self.response = self.get_text_from_subnode("rawresponse")
        if self.response:
            self.response = self.response.encode("ascii",errors="backslashreplace") 
        if self.request:
            self.request = self.request.encode("ascii",errors="backslashreplace") 
        if self.reference:
            self.reference = self.reference.encode("ascii",errors="backslashreplace") 


        self.kvulns = []
        for v in self.node.findall("knownvulnerabilities/knownvulnerability"):
            self.node = v
            self.kvulns.append(self.get_text_from_subnode(
                "severity") + "-" + self.get_text_from_subnode("title"))

        self.extra = []
        for v in item_node.findall("extrainformation/info"):
            self.extra.append(v.get('name') + ":" + v.text)

        self.node = item_node
        self.node = item_node.find("classification")
        self.owasp = self.get_text_from_subnode("OWASP")
        self.wasc = self.get_text_from_subnode("WASC")
        self.cwe = self.get_text_from_subnode("CWE")
        self.capec = self.get_text_from_subnode("CAPEC")
        self.pci = self.get_text_from_subnode("PCI")
        self.pci2 = self.get_text_from_subnode("PCI2")
        self.node = item_node.find("classification/CVSS")
        self.cvss = self.get_text_from_subnode("vector")

        self.ref = []
        if self.cwe:
            self.ref.append("CWE-" + self.cwe)
        if self.owasp:
            self.ref.append("OWASP-" + self.owasp)
        if self.reference:
            self.ref.extend(list(set(re.findall('https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', self.reference))))
        if self.cvss:
            self.ref.append(self.cvss)
    
        self.data = ""
        self.data += "\nKnowVulns: " + \
            "\n".join(self.kvulns) if self.kvulns else ""
        self.data += "\nWASC: " + self.wasc if self.wasc else ""
        self.data += "\nCertainty: " + self.certainty if self.certainty else ""
        self.data += "\nPCI: " + self.pci if self.pci else ""
        self.data += "\nPCI2: " + self.pci2 if self.pci2 else ""
        self.data += "\nCAPEC: " + self.capec if self.capec else ""
        self.data += "\nPARAM: " + self.param if self.param else ""
        self.data += "\nPARAM VAL: " + \
            repr(self.paramval) if self.paramval else ""
        self.data += "\nExtra: " + "\n".join(self.extra) if self.extra else ""

    def get_text_from_subnode(self, subnode_xpath_expr):
        """
        Finds a subnode in the host node and the retrieves a value from it.

        @return An attribute value
        """
        if self.node:
            sub_node = self.node.find(subnode_xpath_expr)
            if sub_node is not None:
                return sub_node.text

        return None


class NetsparkerPlugin(core.PluginBase):
    """
    Example plugin to parse netsparker output.
    """

    def __init__(self):
        core.PluginBase.__init__(self)
        self.id = "Netsparker"
        self.name = "Netsparker XML Output Plugin"
        self.plugin_version = "0.0.1"
        self.version = "Netsparker 3.1.1.0"
        self.framework_version = "1.0.0"
        self.options = None
        self._current_output = None
        self._command_regex = re.compile(
            r'^(sudo netsparker|\.\/netsparker).*?')

        global current_path
        self._output_file_path = os.path.join(self.data_path,
                                              "netsparker_output-%s.xml" % self._rid)

    def resolve(self, host):
        try:
            return socket.gethostbyname(host)
        except:
            pass
        return host

    def parseOutputString(self, output, debug=False):

        parser = NetsparkerXmlParser(output)
        first = True
        for i in parser.items:
            if first:
                ip = self.resolve(i.hostname)
                h_id = self.createAndAddHost(ip, hostnames=[ip])
                
                s_id = self.createAndAddServiceToHost(h_id, str(i.port),
                                                           protocol = str(i.protocol),
                                                           ports=[str(i.port)],
                                                           status="open")
                first = False
            
            v_id = self.createAndAddVulnWebToService(h_id, s_id, i.name, ref=i.ref, website=i.hostname, 
                                                     severity=i.severity, desc=BeautifulSoup(i.desc, "lxml").text,
                                                      path=i.url, method=i.method, request=i.request, response=i.response,
                                                     resolution=BeautifulSoup(i.resolution, "lxml").text,pname=i.param, data=i.data)

        del parser

    def processCommandString(self, username, current_path, command_string):
        return None

def createPlugin():
    return NetsparkerPlugin()

if __name__ == '__main__':
    parser = NetsparkerXmlParser(sys.argv[1])
    for item in parser.items:
        if item.status == 'up':
            print item
