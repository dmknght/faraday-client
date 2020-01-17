"""
Faraday Penetration Test IDE
Copyright (C) 2013  Infobyte LLC (http://www.infobytesec.com/)
See the file 'doc/LICENSE' for the license information

"""
from faraday_client.plugins.plugin import PluginXMLFormat
from faraday_client.model import api
import re
import os
import sys

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


class X1XmlParser:
    """
    The objective of this class is to parse an xml file generated by the x1 tool.

    TODO: Handle errors.
    TODO: Test x1 output version. Handle what happens if the parser doesn't support it.
    TODO: Test cases.

    @param x1_xml_filepath A proper xml generated by x1
    """

    def __init__(self, xml_output):

        tree = self.parse_xml(xml_output)
        if tree:
            self.items = list(self.get_items(tree))
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
        except SyntaxError as err:
            print("SyntaxError: %s. %s" % (err, xml_output))
            return None

        return tree

    def get_items(self, tree):
        """
        @return items A list of Host instances
        """

        for node in tree.findall('results/landscape/system/component'):
            yield Item(node)


class Item:
    """
    An abstract representation of a Item


    @param item_node A item_node taken from an x1 xml tree
    """

    def __init__(self, item_node):
        self.node = item_node

        self.name = self.get_text_from_subnode('name')
        self.host = self.get_text_from_subnode('host')
        self.vclass = self.get_text_from_subnode('class')

        self.connector = self.node.find('connector')
        self.cname = self.connector.get('name')
        data = self.cname.split("/")
        self.port, self.protocol = data[0].split()
        self.srvname = data[1]

        self.cresults = self.getResults(self.connector)
        self.results = self.getResults(self.node)

    def getResults(self, tree):
        """
        :param tree:
        """
        for self.issues in tree.findall('modResults/moduleResult'):
            yield Results(self.issues)

    def get_text_from_subnode(self, subnode_xpath_expr):
        """
        Finds a subnode in the host node and the retrieves a value from it.

        @return An attribute value
        """
        sub_node = self.node.find(subnode_xpath_expr)
        if sub_node is not None:
            return sub_node.text

        return None


class Results():

    def __init__(self, issue_node):
        self.node = issue_node
        self.id = self.get_text_from_subnode('id')
        self.name = self.get_text_from_subnode('name')

        self.category = self.get_text_from_subnode('category')
        self.trendingStatus = self.get_text_from_subnode('trendingStatus')
        self.description = self.get_text_from_subnode('description')
        self.risk = self.get_text_from_subnode('risk')
        self.resolution = self.get_text_from_subnode('solution')
        self.ref = []
        for r in issue_node.findall('refs/reference'):

            self.ref.append(r.get('type') + "-" + r.get('text'))

    def get_text_from_subnode(self, subnode_xpath_expr):
        """
        Finds a subnode in the host node and the retrieves a value from it.

        @return An attribute value
        """
        sub_node = self.node.find(subnode_xpath_expr)
        if sub_node is not None:
            return sub_node.text

        return None


class X1Plugin(PluginXMLFormat):
    """
    Example plugin to parse x1 output.
    """

    def __init__(self):
        super().__init__()
        self.identifier_tag = ["session", "landscapePolicy"]
        self.id = "X1"
        self.name = "Onapsis X1 XML Output Plugin"
        self.plugin_version = "0.0.1"
        self.version = "Onapsis X1 2.56"
        self.framework_version = "1.0.0"
        self.options = None
        self._current_output = None
        self._command_regex = re.compile(r'^(sudo x1|\.\/x1).*?')

        global current_path
        self._output_file_path = os.path.join(self.data_path, "x1_output-%s.xml" % self._rid)

    def parseOutputString(self, output, debug=False):

        parser = X1XmlParser(output)
        for item in parser.items:
            h_id = self.createAndAddHost(item.host, item.name)
            i_id = self.createAndAddInterface(
                h_id, item.host, ipv4_address=item.host, hostname_resolution=[item.vclass])
            s_id = self.createAndAddServiceToInterface(h_id, i_id, item.srvname,
                                                       item.protocol,
                                                       ports=[str(item.port)],
                                                       status="open")
            for v in item.results:
                desc = v.description
                v_id = self.createAndAddVulnToService(h_id, s_id, v.name, desc=desc,
                                                      ref=v.ref, severity=v.risk, resolution=v.resolution)

            for v in item.cresults:
                desc = v.description
                v_id = self.createAndAddVulnToService(h_id, s_id, v.name, desc=desc,
                                                      ref=v.ref, severity=v.risk, resolution=v.resolution)

        del parser

    def processCommandString(self, username, current_path, command_string):
        return None

    def setHost(self):
        pass


def createPlugin():
    return X1Plugin()


# I'm Py3
