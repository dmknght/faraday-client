"""
Faraday Penetration Test IDE
Copyright (C) 2013  Infobyte LLC (http://www.infobytesec.com/)
See the file 'doc/LICENSE' for the license information
"""
from faraday.client.plugins import core
import re
import os
import sys
import random

try:
    import xml.etree.cElementTree as ET
    import xml.etree.ElementTree as ET_ORIG
    ETREE_VERSION = ET_ORIG.VERSION
except ImportError:
    import xml.etree.ElementTree as ET
    ETREE_VERSION = ET.VERSION

ETREE_VERSION = [int(i) for i in ETREE_VERSION.split(".")]

current_path = os.path.abspath(os.getcwd())

__author__ = "Morgan Lemarechal"
__copyright__ = "Copyright 2014, Faraday Project"
__credits__ = ["Morgan Lemarechal"]
__license__ = ""
__version__ = "1.0.0"
__maintainer__ = "Morgan Lemarechal"
__email__ = "morgl@infobytesec.com"
__status__ = "Development"


class WcscanParser:
    """
    The objective of this class is to parse an xml file generated by the wcscan tool.
    TODO: Handle errors.
    TODO: Test wcscan output version. Handle what happens if the parser doesn't support it.
    TODO: Test cases.
    @param wcscan_filepath A proper simple report generated by wcscan
    """

    def __init__(self, output):
        self.scaninfo = {}
        self.result = {}
        tree = ET.parse(output)
        root = tree.getroot()
        for scan in root.findall(".//scan"):
            infos = {}
            for info in scan.attrib:
                infos[info] = scan.attrib[info]
                self.scaninfo[scan.attrib['file']] = infos

            item = {}
            if scan.attrib['type'] == "phpini":
                for carac in scan:
                    item[carac.tag] = [carac.text, carac.attrib['rec'], ""]

            if scan.attrib['type'] == "webconfig":
                id = 0
                for carac in scan:
                    id += 1
                    item[id] = [carac.text, carac.attrib['rec'],
                                carac.attrib['option'], carac.tag]

            self.result[scan.attrib['file']] = item


class WcscanPlugin(core.PluginBase):
    """
    Example plugin to parse wcscan output.
    """

    def __init__(self):
        super().__init__()
        self.id = "Wcscan"
        self.name = "Wcscan XML Output Plugin"
        self.plugin_version = "0.0.2"
        self.version = "0.30"
        self._completition = {
            "": "wcscan [-h] [-r] [-host HOST] [-port PORT] [--xml XMLOUTPUT] [--version] files [files ...]",
            "-h": "show this help message and exit",
            "-r": "enable the recommendation mode",
            "--host": "to give the IP address of the conf file owner",
            "--port": "to give a associated port",
            "--xml": "enabled the XML output in a specified file",
            "--version": "Show program's version number and exit",
        }

        self.options = None
        self._current_output = None
        self.current_path = None
        self._command_regex = re.compile(
            r'^(sudo wcscan|wcscan|\.\/wcscan).*?')

        global current_path
        self._output_file_path = os.path.join(self.data_path, "%s_%s_output-%s.xml" % (self.get_ws(),
                                                                                       self.id,
                                                                                       random.uniform(1, 10)))

    def canParseCommandString(self, current_input):
        if self._command_regex.match(current_input.strip()):
            return True
        else:
            return False

    def parseOutputString(self, output, debug=False):
        """
        This method will discard the output the shell sends, it will read it from
        the xml where it expects it to be present.
        NOTE: if 'debug' is true then it is being run from a test case and the
        output being sent is valid.
        """
        if debug:
            parser = WcscanParser(self._output_file_path)
        else:

            if not os.path.exists(self._output_file_path):
                return False
            parser = WcscanParser(self._output_file_path)

            for file in parser.scaninfo:
                host = parser.scaninfo[file]['host']
                port = parser.scaninfo[file]['port']
                h_id = self.createAndAddHost(host)
                if(re.match("(^[2][0-5][0-5]|^[1]{0,1}[0-9]{1,2})\.([0-2][0-5][0-5]|[1]{0,1}[0-9]{1,2})\.([0-2][0-5][0-5]|[1]{0,1}[0-9]{1,2})\.([0-2][0-5][0-5]|[1]{0,1}[0-9]{1,2})$", host)):
                    i_id = self.createAndAddInterface(h_id,
                                                      host,
                                                      ipv4_address=host)
                else:
                    i_id = self.createAndAddInterface(h_id,
                                                      host,
                                                      ipv6_address=host)

                s_id = self.createAndAddServiceToInterface(
                    h_id, i_id, "http", protocol="tcp", ports=port)
                for vuln in parser.result[file]:
                    if parser.scaninfo[file]['type'] == "phpini":
                        v_id = self.createAndAddVulnToService(h_id, s_id,
                                                              parser.scaninfo[file][
                                                                  'file'] + ":" + vuln,
                                                              desc="{} : {}\n{}".format(vuln,
                                                                                        str(parser.result[
                                                                                            file][vuln][0]),
                                                                                        str(parser.result[file][vuln][1])),
                                                              severity=0)

                    if parser.scaninfo[file]['type'] == "webconfig":
                        v_id = self.createAndAddVulnToService(h_id, s_id,
                                                              parser.scaninfo[file][
                                                                  'file'] + ":" + str(parser.result[file][vuln][3]),
                                                              desc="{} : {} = {}\n{}".format(str(parser.result[file][vuln][3]),
                                                                                             str(parser.result[
                                                                                                 file][vuln][2]),
                                                                                             str(parser.result[
                                                                                                 file][vuln][0]),
                                                                                             str(parser.result[file][vuln][1])),
                                                              severity=0)
        del parser

        return True

    xml_arg_re = re.compile(r"^.*(--xml\s*[^\s]+).*$")

    def processCommandString(self, username, current_path, command_string):
        """
        Adds the parameter to get output to the command string that the
        user has set.
        """

        arg_match = self.xml_arg_re.match(command_string)

        if arg_match is None:
            return "%s --xml %s" % (command_string, self._output_file_path)
        else:
            return re.sub(arg_match.group(1),
                          r"-xml %s" % self._output_file_path,
                          command_string)


def createPlugin():
    return WcscanPlugin()


# I'm Py3
