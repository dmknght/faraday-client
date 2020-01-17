"""
Faraday Penetration Test IDE
Copyright (C) 2013  Infobyte LLC (http://www.infobytesec.com/)
See the file 'doc/LICENSE' for the license information
"""
from faraday_client.plugins import core
from faraday_client.model import api
import re

__author__ = "Federico Kirschbaum"
__copyright__ = "Copyright 2013, Faraday Project"
__credits__ = ["Federico Kirschbaum"]
__license__ = ""
__version__ = "1.0.0"
__maintainer__ = "Federico Kirschbaum"
__email__ = "fedek@infobytesec.com"
__status__ = "Development"


class CmdArpScanPlugin(core.PluginBase):
    """
    This plugin handles arp-scan command.
    Basically inserts into the tree the ouput of this tool
    """

    def __init__(self):
        super().__init__()
        self.id = "arp-scan"
        self.name = "arp-scan network scanner"
        self.plugin_version = "0.0.2"
        self.version = "1.8.1"
        self.framework_version = "1.0.0"
        self.options = None
        self._current_output = None
        self._command_regex = re.compile(
            r'^(sudo arp-scan|\.\/arp-scan|arp-scan).*?')
        self._host_ip = None

    def parseOutputString(self, output, debug=False):

        host_info = re.search(
            r"(\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b)",
            output)

        host_mac_addr = re.search(r"([\dA-F]{2}(?:[-:][\dA-F]{2}){5})", output, re.IGNORECASE)

        if host_info is None:
            api.devlog("No hosts detected")
        else:

            for line in output.split('\n'):
                vals = line.split("\t")

                if len(vals) == 3:

                    if len(vals[0].split(".")) == 4:

                        host = vals[0]
                        h_id = self.createAndAddHost(host)
                        i_id = self.createAndAddInterface(h_id, host, ipv4_address=host, mac=vals[1])

        return True

    def processCommandString(self, username, current_path, command_string):
        return


def createPlugin():
    return CmdArpScanPlugin()
# I'm Py3
