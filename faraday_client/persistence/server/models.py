from persistence.server import server
from persistence.server.utils import (force_unique,
                                      get_host_properties,
                                      get_interface_properties,
                                      get_service_properties,
                                      get_vuln_properties,
                                      get_vuln_web_properties,
                                      get_note_properties,
                                      get_credential_properties,
                                      get_command_properties,
                                      WrongObjectSignature)
from model.diff import ModelObjectDiff

def _get_faraday_ready_objects(workspace_name, faraday_ready_object_dictionaries,
                               faraday_object_name):
    """Takes a workspace name, a faraday object ('hosts', 'vulns',
    'interfaces' or 'services') a row_name (the name of the row where
    the information about the objects live) and an arbitray number
    of params to customize to request.

    Return a list of faraday objects
    (_Host, _Interface, _Service, _Vuln, _WevVuln) which the same interface
    for getting attribuetes than those defined my the ModelController.
    """
    object_to_class = {'hosts': _Host,
                       'vulns': _Vuln,
                       'vulns_web': _VulnWeb,
                       'interfaces': _Interface,
                       'services': _Service,
                       'notes': _Note,
                       'credentials': _Credential,
                       'commands': _Command}

    appropiate_class = object_to_class[faraday_object_name]
    faraday_objects = []
    if faraday_ready_object_dictionaries:
        for object_dictionary in faraday_ready_object_dictionaries:
            faraday_objects.append(appropiate_class(object_dictionary, workspace_name))
    return faraday_objects

def _get_faraday_ready_hosts(workspace_name, hosts_dictionaries):
    return _get_faraday_ready_objects(workspace_name, hosts_dictionaries, 'hosts')

def _get_faraday_ready_vulns(workspace_name, vulns_dictionaries, vulns_type=None):
    if vulns_type:
        return _get_faraday_ready_objects(workspace_name, vulns_dictionaries, vulns_type)

    vulns = [vuln for vuln in vulns_dictionaries if vuln['value']['type'] == 'Vulnerability']
    web_vulns = [w_vuln for w_vuln in vulns_dictionaries if w_vuln['value']['type'] == 'VulnerabilityWeb']
    faraday_ready_vulns = _get_faraday_ready_objects(workspace_name, vulns, 'vulns')
    faraday_ready_web_vulns = _get_faraday_ready_objects(workspace_name, web_vulns, 'vulns_web')
    return faraday_ready_vulns + faraday_ready_web_vulns

def _get_faraday_ready_services(workspace_name, services_dictionaries):
    return _get_faraday_ready_objects(workspace_name, services_dictionaries, 'services')

def _get_faraday_ready_interfaces(workspace_name, interfaces_dictionaries):
    return _get_faraday_ready_objects(workspace_name, interfaces_dictionaries, 'interfaces')

def _get_faraday_ready_credentials(workspace_name, credentials_dictionaries):
    return _get_faraday_ready_objects(workspace_name, credentials_dictionaries, 'credentials')

def _get_faraday_ready_notes(workspace_name, notes_dictionaries):
    return _get_faraday_ready_objects(workspace_name, notes_dictionaries, 'notes')

def get_hosts(workspace_name, **params):
    """Take a workspace name and a arbitrary number of params to customize the
    request.

    Return a list of Host objects.
    """
    host_dictionaries = server.get_hosts(workspace_name, **params)
    return _get_faraday_ready_hosts(workspace_name, host_dictionaries)

def get_host(workspace_name, host_id):
    """Return the host by host_id. None if it can't be found."""
    return force_unique(get_hosts(workspace_name, couchid=host_id))

def get_all_vulns(workspace_name, **params):
    vulns_dictionaries = server.get_all_vulns(workspace_name, **params)
    return _get_faraday_ready_vulns(workspace_name, vulns_dictionaries)

def get_vulns(workspace_name, **params):
    """Take a workspace name and a arbitrary number of params to customize the
    request.

    Return a list of Vuln objects.
    """
    vulns_dictionaries = server.get_vulns(workspace_name, **params)
    return _get_faraday_ready_vulns(workspace_name, vulns_dictionaries, vulns_type='vulns')

def get_vuln(workspace_name, vuln_id):
    """Return the Vuln of id vuln_id. None if not found."""
    return force_unique(get_vulns(workspace_name, couchid=vuln_id))

def get_web_vulns(workspace_name, **params):
    """Take a workspace name and a arbitrary number of params to customize the
    request.

    Return a list of VulnWeb objects.
    """
    vulns_web_dictionaries = server.get_web_vulns(workspace_name, **params)
    return _get_faraday_ready_vulns(workspace_name, vulns_web_dictionaries, vulns_type='vulns_web')

def get_web_vuln(workspace_name, vuln_id):
    """Return the WebVuln of id vuln_id. None if not found."""
    return force_unique(get_web_vulns(workspace_name, couchid=vuln_id))

def get_interfaces(workspace_name, **params):
    """Take a workspace name and a arbitrary number of params to customize the
    request.

    Return a list of Interfaces objects
    """
    interfaces_dictionaries = server.get_interfaces(workspace_name, **params)
    return _get_faraday_ready_interfaces(workspace_name, interfaces_dictionaries)

def get_interface(workspace_name, interface_id):
    """Return the Interface of id interface_id. None if not found."""
    return force_unique(get_interfaces(workspace_name, couchid=interface_id))

def get_services(workspace_name, **params):
    """Take a workspace name and a arbitrary number of params to customize the
    request.

    Return a list of Services objects
    """
    services_dictionary = server.get_services(workspace_name, **params)
    return _get_faraday_ready_services(workspace_name, services_dictionary)

def get_service(workspace_name, service_id):
    """Return the Service of id service_id. None if not found."""
    return force_unique(get_services(workspace_name, couchid=service_id))

def get_credentials(workspace_name, **params):
    credentials_dictionary = server.get_credentials(workspace_name, **params)
    return _get_faraday_ready_credentials(workspace_name, credentials_dictionary)

def get_credential(workspace_name, credential_id):
    return force_unique(get_credentials(workspace_name, couchid=credential_id))

def get_notes(workspace_name, **params):
    notes_dictionary = server.get_notes(workspace_name, **params)
    return _get_faraday_ready_notes(workspace_name, notes_dictionary)

def get_note(workspace_name, note_id):
    return force_unique(get_notes(workspace_name, couchid=note_id))

def get_workspace(workspace_name):
    """Return the Workspace of id workspace_name. None if not found."""
    workspace = server.get_workspace(workspace_name)
    return _Workspace(workspace, workspace_name) if workspace else None

def get_object(workspace_name, object_signature, object_id):
    """Given a workspace name, an object_signature as string  and an arbitrary
    number of query params, return a list a dictionaries containg information
    about 'object_signature' objects matching the query.

    object_signature must be either 'hosts', 'vulns', 'interfaces'
    'services', 'credentials', 'notes' or 'commands'.
    Will raise an WrongObjectSignature error if this condition is not met.
    """
    object_to_func = {_Host.class_signature: get_host,
                      _Vuln.class_signature: get_vuln,
                      _VulnWeb.class_signature: get_web_vuln,
                      _Interface.class_signature: get_interface,
                      _Service.class_signature: get_service,
                      _Credential.class_signature: get_credential,
                      _Note.class_signature: get_note}
    try:
        appropiate_function = object_to_func[object_signature]
    except KeyError:
        raise WrongObjectSignature(object_signature)

    return appropiate_function(workspace_name, object_id)

def create_host(workspace_name, host):
    """Take a workspace_name and a host object and save it to the sever.

    Return the server's json response as a dictionary.
    """
    host_properties = get_host_properties(host)
    return server.create_host(workspace_name, **host_properties)

def update_host(workspace_name, host):
    host_properties = get_host_properties(host)
    return server.update_host(workspace_name, **host_properties)

def create_interface(workspace_name, interface):
    """Take a workspace_name and an interface object and save it to the sever.
    Return the server's json response as a dictionary.
    """
    interface_properties = get_interface_properties(interface)
    return server.create_interface(workspace_name, **interface_properties)

def update_interface(workspace_name, interface):
    interface_properties = get_interface_properties(interface)
    return server.update_interface(workspace_name, **interface_properties)

def create_service(workspace_name, service):
    """Take a workspace_name and a service object and save it to the sever.
    Return the server's json response as a dictionary.
    """
    service_properties = get_service_properties(service)
    return server.create_service(workspace_name, **service_properties)

def update_service(workspace_name, service):
    service_properties = get_service_properties(service)
    return server.update_service(workspace_name, **service_properties)

def create_vuln(workspace_name, vuln):
    """Take a workspace_name and an vulnerability object and save it to the
    sever. The rev parameter must be provided if you are updating the object.
    Return the server's json response as a dictionary.
    """
    vuln_properties = get_vuln_properties(vuln)
    return server.create_vuln(workspace_name, **vuln_properties)

def update_vuln(workspace_name, vuln):
    vuln_properties = get_vuln_properties(vuln)
    return server.update_vuln(workspace_name, **vuln_properties)

def create_vuln_web(workspace_name, vuln_web):
    """Take a workspace_name and an vulnerabilityWeb object and save it to the
    sever.
    Return the server's json response as a dictionary.
    """
    vuln_web_properties = get_vuln_web_properties(vuln_web)
    return server.create_vuln_web(workspace_name, **vuln_web_properties)

def update_vuln_web(workspace_name, vuln_web):
    vuln_web_properties = get_vuln_web_properties(vuln_web)
    return server.update_vuln_web(workspace_name, **vuln_web_properties)

def create_note(workspace_name, note):
    """Take a workspace_name and an note object and save it to the sever.
    Return the server's json response as a dictionary.
    """
    note_properties = get_note_properties(note)
    return server.create_note(workspace_name, **note_properties)

def update_note(workspace_name, note):
    note_properties = get_note_properties(note)
    return server.update_note(workspace_name, **note_properties)

def create_credential(workspace_name, credential):
    """Take a workspace_name and an credential object and save it to the sever.
    Return the server's json response as a dictionary.
    """
    credential_properties = get_credential_properties(credential)
    return server.create_credential(workspace_name, **credential_properties)

def update_credential(workspace_name, credential):
    credential_properties = get_credential_properties(credential)
    return server.update_credential(workspace_name, **credential_properties)

def create_command(workspace_name, command):
    command_properties = get_command_properties(command)
    return server.create_command(workspace_name, **command_properties)

def update_command(workspace_name, command):
    command_properties = get_command_properties(command)
    return server.update_command(workspace_name, **command_properties)

def create_object(workspace_name, object_signature, obj):
    object_to_func = {_Host.class_signature: create_host,
                      _Vuln.class_signature: create_vuln,
                      _VulnWeb.class_signature: create_vuln_web,
                      _Interface.class_signature: create_interface,
                      _Service.class_signature: create_service,
                      _Credential.class_signature: create_credential,
                      _Note.class_signature: create_note,
                      _Command.class_signature: create_command}
    try:
        appropiate_function = object_to_func[object_signature]
    except KeyError:
        raise WrongObjectSignature(object_signature)

    return appropiate_function(workspace_name, obj)

def update_object(workspace_name, object_signature, obj):
    object_to_func = {_Host.class_signature: update_host,
                      _Vuln.class_signature: update_vuln,
                      _VulnWeb.class_signature: update_vuln_web,
                      _Interface.class_signature: update_interface,
                      _Service.class_signature: update_service,
                      _Credential.class_signature: update_credential,
                      _Note.class_signature: update_note,
                      _Command.class_signature: update_command}
    try:
        appropiate_function = object_to_func[object_signature]
    except KeyError:
        raise WrongObjectSignature(object_signature)

    return appropiate_function(workspace_name, obj)

def create_workspace(workspace_name, **params):
    """Take the workspace_name and create the database first,
    then the workspace's document.
    Return the server's json response as a dictionary"""
    # XXX: For now we won't upload views
    server.create_database(workspace_name)
    return server.create_workspace(workspace_name, **params)

def get_hosts_number(workspace_name, **params):
    return server.get_hosts_number(workspace_name, **params)

def get_services_number(workspace_name, **params):
    return server.get_services_number(workspace_name, **params)

def get_interfaces_number(workspace_name, **params):
    return server.get_interfaces_number(workspace_name, **params)

def get_vulns_number(workspace_name, **params):
    return server.get_vulns_number(workspace_name, **params)

def delete_host(workspace_name, host_id):
    return server.delete_host(workspace_name, host_id)

def delete_interface(workspace_name, interface_id):
    return server.delete_interface(workspace_name, interface_id)

def delete_service(workspace_name, service_id):
    return server.delete_service(workspace_name, service_id)

def delete_vuln(workspace_name, vuln_id):
    return server.delete_vuln(workspace_name, vuln_id)

def delete_note(workspace_name, note_id):
    return server.delete_note(workspace_name, note_id)

def delete_credential(workspace_name, credential_id):
    return server.delete_credential(workspace_name, credential_id)

def delete_vuln_web(workspace_name, vuln_web):
    return server.delete_vuln(workspace_name, vuln_web)

def delete_command(workspace_name, command):
    return server.delete_command(workspace_name, command)

def delete_object(workspace_name, object_signature, obj_id):
    object_to_func = {_Host.class_signature: delete_host,
                      _Vuln.class_signature: delete_vuln,
                      _VulnWeb.class_signature: delete_vuln_web,
                      _Interface.class_signature: delete_interface,
                      _Service.class_signature: delete_service,
                      _Credential.class_signature: delete_credential,
                      _Note.class_signature: delete_note,
                      _Command.class_signature: delete_command}
    try:
        appropiate_function = object_to_func[object_signature]
    except KeyError:
        raise WrongObjectSignature(object_signature)

    return appropiate_function(workspace_name, obj_id)

def delete_workspace(workspace_name):
    return server.delete_workspace(workspace_name)

def get_workspaces_names():
    return server.get_workspaces_names()['workspaces']

def is_server_up():
    return server.is_server_up()

class ModelBase(object):
    def __init__(self, obj, workspace_name):
        self._workspace_name = workspace_name
        self.id = obj['id']
        self.name = obj['value']['name']
        self.description = obj['value']['description']
        self.owned = obj['value']['owned']
        self.owner = obj['value']['owner']
        self.metadata = obj['value']['metadata']

    @staticmethod
    def publicattrsrefs():
        return {'Description': 'description',
                'Name': 'name',
                'Owned': 'owned'}

    def needs_merge(self, new_obj):
        return ModelObjectDiff(self, new_obj).existDiff()

class _Host(ModelBase):
    """A simple Host class. Should implement all the methods of the
    Host object in Model.Host
    Any method here more than a couple of lines long probably represent
    a search the server is missing.
    """
    class_signature = 'Host'
    
    def __init__(self, host, workspace_name):
        ModelBase.__init__(self, host, workspace_name)
        self.server_id = host['_id']
        self.default_gateway = host['value']['default_gateway']
        self.os = host['value']['os']
        self.vuln_amount = int(host['value']['vulns'])

    @staticmethod
    def publicattrsrefs():
        publicattrs = dict(ModelBase.publicattrsrefs(), **{
            'Operating System' : 'os'
        })
        return publicattrs

    def __str__(self): return "{0} ({1})".format(self.name, self.vuln_amount)
    def getOS(self): return self.os
    def getName(self): return self.name
    def getVulnAmount(self): return self.vuln_amount
    def isOwned(self): return self.owned
    def getID(self): return self.id
    def getDescription(self): return self.description
    def getDefaultGateway(self): return self.default_gateway
    def getOwner(self): return self.owner
    def getMetadata(self): return self.metadata
    def getVulns(self):
        return get_all_vulns(self._workspace_name, target=self.name)
    def getInterface(self, interface_couch_id):
        service = get_interfaces(self._workspace_name, couchid=interface_couch_id)
        return service[0]
    def getAllInterfaces(self):
        return get_interfaces(self._workspace_name, host=self.server_id)
    def getServices(self):
        services = []
        interfaces = self.getAllInterfaces()
        for interface in interfaces:
            services.append(interface.getAllServices())
        return interfaces


class _Interface(ModelBase):
    """A simple Interface class. Should implement all the methods of the
    Interface object in Model.Host
    Any method here more than a couple of lines long probably represent
    a search the server is missing.
    """
    class_signature = 'Interface'

    def __init__(self, interface, workspace_name):
        self._server_id = interface['_id']
        self.hostnames = interface['value']['hostnames']
        self.ipv4 = interface['value']['ipv4']
        self.ipv6 = interface['value']['ipv6']
        self.mac = interface['value']['mac']
        self.network_segment = interface['value']['network_segment']
        self.ports = interface['value']['ports']
        # XXX FALTA: self.metadata = interface['value']['metadata']

    @staticmethod
    def publicattrsrefs():
        publicattrs = dict(ModelBase.publicattrsrefs(), **{
            'MAC Address' : 'mac',
            'IPV4 Settings' : 'ipv4',
            'IPV6 Settings' : 'ipv6',
            'Network Segment' : 'network_segment',
            'Hostnames' : 'hostnames'
        })
        return publicattrs

    def __str__(self): return "{0}".format(self.name)
    def getID(self): return self.id
    def getName(self): return self.name
    def getDescription(self): return self.description
    def getHostnames(self): return self.hostnames
    def getIPv4(self): return self.ipv4
    def getIPv6(self): return self.ipv6
    def getMAC(self): return self.mac
    def getNetworkSegment(self): return self.network_segment
    def isOwned(self): return self.owned
    #def getMetadata(self): return self.metadata

    def getService(self, service_couch_id):
        service = get_services(self._workspace_name, couchid=service_couch_id)
        return service[0]
    def getAllServices(self):
        return get_services(self._workspace_name, interface=self._server_id)
    def getVulns(self):
        vulns = []
        services = self.getAllServices()
        for service in services:
            vulns_in_service = service.getVulns()
            for vuln in vulns_in_service:
                vulns.append(vuln)
        return vulns

class _Service(ModelBase):
    """A simple Service class. Should implement all the methods of the
    Service object in Model.Host
    Any method here more than a couple of lines long probably represent
    a search the server is missing.
    """
    class_signature = 'Service'

    def __init__(self, service, workspace_name):
        self._server_id = service['_id']
        self.protocol = service['value']['protocol']
        self.ports =  service['value']['ports']
        self.version = service['value']['version']
        self.status = service['value']['status']
        self.vuln_amount = int(service['vulns'])
        #XXX: FALTA self.metadata = service['value']['metadata']

    @staticmethod
    def publicattrsrefs():
        publicattrs = dict(ModelBase.publicattrsrefs(), **{
            'Ports' : 'ports',
            'Protocol' : 'protocol',
            'Status' : 'status',
            'Version' : 'version',
        })
        return publicattrs


    def __str__(self): return "{0} ({1})".format(self.name, self.vuln_amount)
    def getID(self): return self.id
    def getName(self): return self.name
    def getDescription(self): return self.description
    def getStatus(self): return self.status
    def getPorts(self): return [self.ports]  # this is a list of one element in faraday
    def getVersion(self): return self.version
    def getProtocol(self): return self.protocol
    def isOwned(self): return self.owned
    def getVulns(self): return get_all_vulns(self._workspace_name, service=self.name)
    #def getMetadata(self): return self.metadata


class _Vuln(ModelBase):
    """A simple Vuln class. Should implement all the methods of the
    Vuln object in Model.Common
    Any method here more than a couple of lines long probably represent
    a search the server is missing.
    """
    class_signature = 'Vulnerability'

    def __init__(self, vuln, workspace_name):
        self.desc = vuln['value']['desc']
        self.data = vuln['value']['data']
        self.severity = vuln['value']['severity']
        self.refs = vuln['value']['refs']
        self.confirmed = vuln['value']['confirmed']

    @staticmethod
    def publicattrsrefs():
        publicattrs = dict(ModelBase.publicattrsrefs(), **{
            'Data' : 'data',
            'Severity' : 'severity',
            'Refs' : 'refs'
        })
        return publicattrs


    def getID(self): return self.id
    def getName(self): return self.name
    def getDescription(self): return self.description
    def getDesc(self): return self.desc
    def getData(self): return self.data
    def getSeverity(self): return self.severity
    def getRefs(self): return self.refs
    def getConfirmed(self): return self.confirmed
    def getMetadata(self): return self.metadata


class _VulnWeb(ModelBase):
    """A simple VulnWeb class. Should implement all the methods of the
    VulnWeb object in Model.Common
    Any method here more than a couple of lines long probably represent
    a search the server is missing.
    """
    class_signature = 'VulnerabilityWeb'

    def __init__(self, vuln_web, workspace_name):
        self.desc = vuln_web['value']['desc']
        self.data = vuln_web['value']['data']
        self.severity = vuln_web['value']['severity']
        self.refs = vuln_web['value']['refs']
        self.path = vuln_web['value']['path']
        self.website = vuln_web['value']['website']
        self.request = vuln_web['value']['request']
        self.response = vuln_web['value']['response']
        self.method = vuln_web['value']['method']
        self.pname = vuln_web['value']['pname']
        self.params = vuln_web['value']['params']
        self.query = vuln_web['value']['query']
        self.confirmed = vuln_web['value']['confirmed']
        self.resolution = vuln_web['value']['resolution']
        self.attachments = vuln_web['value']['_attachments']
        self.easeofresolution = vuln_web['value']['easeofresolution']
        self.hostnames = vuln_web['value']['hostnames']
        self.impact = vuln_web['value']['impact']
        self.service = vuln_web['value']['service']
        self.status = vuln_web['value']['status']
        self.tags = vuln_web['value']['tags']
        self.target = vuln_web['value']['target']
        self.parent = vuln_web['value']['parent']

    @staticmethod
    def publicattrsrefs():
        publicattrs = dict(ModelBase.publicattrsrefs(), **{
            'Data' : 'data',
            'Severity' : 'severity',
            'Refs' : 'refs',
            'Path' : 'path',
            'Website' : 'website',
            'Request' : 'request',
            'Response' : 'response',
            'Method' : 'method',
            'Pname' : 'pname',
            'Params' : 'params',
            'Query' : 'query'})
        return publicattrs

    def getID(self): return self.id
    def getName(self): return self.name
    def getDescription(self): return self.description
    def getDesc(self): return self.desc
    def getData(self): return self.data
    def getSeverity(self): return self.severity
    def getRefs(self): return self.refs
    def getPath(self): return self.path
    def getWebsite(self): return self.website
    def getRequest(self): return self.request
    def getResponse(self): return self.response
    def getMethod(self): return self.method
    def getPname(self): return self.pname
    def getParams(self): return self.params
    def getQuery(self): return self.query
    def getConfirmed(self): return self.confirmed
    def getResolution(self): return self.resolution
    def getAttachments(self): return self.attachments
    def getEaseOfResolution(self): return self.easeofresolution
    def getHostnames(self): return self.hostnames
    def getImpact(self): return self.impact
    def isOwned(self): return self.owned
    def getOwner(self): return self.owner
    def getService(self): return self.service
    def getStatus(self): return self.status
    def getTags(self): return self.tags
    def getTarget(self): return self.target
    def getMetadata(self): return self.metadata
    def getParent(self): return self.parent

class _Note(ModelBase):
    class_signature = 'Note'

    def __init__(self, note, workspace_name):
        self.text = note['value']['text']

    def getID(self): return self.id
    def getName(self): return self.name
    def getDescription(self): return self.description
    def getText(self): return self.text

class _Credential(ModelBase):
    class_signature = "Cred"

    def __init__(self, credential, workspace_name):
        self.username = credential['value']['username']
        self.password = credential['value']['password']

    def getID(self): return self.id
    def getUsername(self): return self.username
    def getPassword(self): return self.password

class _Command:
    class_signature = 'CommandRunInformation'
    def __init__(self, command, workspace_name):
        self._workspace_name = workspace_name
        self.id = command['id']
        self.command = command['value']['command']
        self.duration = command['value']['duration']
        self.hostname = command['value']['hostname']
        self.ip = command['value']['ip']
        self.itime = command['value']['itime']
        self.params = command['value']['params']
        self.user = command['value']['user']
        self.workspace = command['value']['workspace']

    def getID(self): return self.id
    def getCommand(self): return self.command
    def getDuration(self): return self.duration
    def getHostname(self): return self.hostname
    def getIP(self): return self.ip
    def getItime(self): return self.itime
    def getParams(self): return self.params
    def getUser(self): return self.user
    def getWorkspace(self): return self.workspace

class _Workspace:
    class_signature = 'Workspace'
    def __init__(self, workspace, workspace_name):
        self._id = workspace_name
        self.name = workspace['name']
        self.description = workspace['description']
        self.customer = workspace['customer']
        self.start_date = workspace['sdate']
        self.finish_date = workspace['fdate']

    def getID(self): return self._id
    def getName(self): return self.name
    def getDescription(self): return self.description
    def getCustomer(self): return self.customer
    def getStartDate(self): return self.start_date
    def getFinishDate(self): return self.finish_date

# NOTE: uncomment for test
# class SillyHost():
#     def __init__(self) :
#         import random; self.id = random.randint(0, 1000)
#         self.os = "Windows"
#     def getID(self): return self.id
#     def getOS(self): return self.os
#     def getDefaultGateway(self): return '192.168.1.1'
#     def getDescription(self): return "a description"
#     def getName(self): return "my name"
#     def isOwned(self): return False
#     def getOwner(self): return False
#     def getMetadata(self): return {'stuff': 'gives other stuff'}
