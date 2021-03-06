"""
Faraday Penetration Test IDE
Copyright (C) 2013  Infobyte LLC (http://www.infobytesec.com/)
See the file 'doc/LICENSE' for the license information

"""
import re
import time

from faraday_client.model.workspace import Workspace
from faraday_client.persistence.server.models import create_workspace, get_workspaces_names, get_workspace, delete_workspace
from faraday_client.persistence.server.server_io_exceptions import Unauthorized
from faraday_client.model.guiapi import notification_center

from faraday_client.config.configuration import getInstanceConfiguration
CONF = getInstanceConfiguration()


class WorkspaceException(Exception):
    pass


class WorkspaceManager:
    """
    This class is in charge of creating, deleting and opening workspaces
    """

    def __init__(self, mappersManager, *args, **kwargs):
        self.mappersManager = mappersManager
        self.active_workspace = None

    def getWorkspacesNames(self):
        """Returns the names of the workspaces as a list of strings"""
        return get_workspaces_names()

    def createWorkspace(self, name, desc, start_date=int(time.time() * 1000),
                        finish_date=int(time.time() * 1000), customer=""):
        # XXX: DEPRECATE NEXT LINE
        workspace = Workspace(name, desc)
        try:
            create_workspace(name, description=desc, start_date=start_date,
                             finish_date=finish_date, customer=customer)
        except Unauthorized:
            raise WorkspaceException(
                ("You're not authorized to create workspaces\n"
                 "Make sure you're an admin and you're logged in, "
                 "running faraday with the --login option."))
        except Exception as e:
            raise WorkspaceException(str(e))
        self.mappersManager.createMappers(name)
        self.setActiveWorkspace(workspace)
        notification_center.workspaceChanged(workspace)
        return name

    def openWorkspace(self, name):
        """Open a workspace by name. Returns the workspace. Raises an
        WorkspaceException if something went wrong along the way.
        """
        if name not in get_workspaces_names():
            raise WorkspaceException("Workspace %s wasn't found" % name)

        try:
            workspace = get_workspace(name)
        except Unauthorized:
            raise WorkspaceException(
                ("You're not authorized to access this workspace\n"
                 "Make sure you're an authorized user for this "
                 "workspace and you're logged in, "
                 "running faraday with the --login option."))
        except Exception as e:
            notification_center.DBConnectionProblem(e)
            raise WorkspaceException(str(e))
        self.mappersManager.createMappers(name)
        self.setActiveWorkspace(workspace)
        notification_center.workspaceChanged(workspace)
        return workspace

    def removeWorkspace(self, name):
        if name in self.getWorkspacesNames():
            try:
                return delete_workspace(name)
            except Unauthorized:
                notification_center.showDialog("You are not authorized to "
                                               "delete this workspace. \n")

    def setActiveWorkspace(self, workspace):
        self.active_workspace = workspace

    def getActiveWorkspace(self):
        return self.active_workspace

    def workspaceExists(self, name):
        return name in self.getWorkspacesNames()

    def isActive(self, name):
        return self.active_workspace.getName() == name

    def isWorkspaceNameValid(self, ws_name):
        """Returns True if the ws_name is valid, else if it's not"""
        letters_or_numbers = r"^[a-z0-9][a-z0-9\_\$()\+\-\/]*$"
        regex_name = re.match(letters_or_numbers, ws_name)
        if regex_name:
            return True
        else:
            return False


# I'm Py3
