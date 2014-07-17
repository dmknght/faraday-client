'''
Faraday Penetration Test IDE - Community Version
Copyright (C) 2013  Infobyte LLC (http://www.infobytesec.com/)
See the file 'doc/LICENSE' for the license information

'''

import json
import os
import shutil
import mockito
import threading
from urlparse import urlparse
import traceback
from couchdbkit import Server, ChangesStream, Database
from couchdbkit.resource import ResourceNotFound

from utils.logs import getLogger
from utils.decorators import trap_timeout
from managers.all import ViewsManager

from config.configuration import getInstanceConfiguration
CONF = getInstanceConfiguration()


class DBTYPE(object):
    COUCHDB = 1
    FS = 2


class DbManager(object):

    def __init__(self):
        self.couchmanager = CouchDbManager()
        self.fsmanager = FileSystemManager()
        self.dbs = {}
        self._loadDbs()

    def _loadDbs(self):
        self.dbs.update(self.fsmanager.getDbs())
        self.dbs.update(self.couchmanager.getDbs())

    def _getManagerByType(self, dbtype):
        if dbtype == DBTYPE.COUCHDB:
            manager = self.couchmanager
        else:
            manager = self.fsmanager
        return manager

    def getConnector(self, name):
        return self.dbs.get(name, None)

    def createDb(self, name, dbtype):
        if self.getConnector(name, None):
            return False
        manager = self._getManagerByType(dbtype)
        self.dbs[name] = manager.createDb(name)
        return True

    def getAllDbNames(self):
        return self.dbs.keys()

    def removeDb(self, name, dbtype):
        if self.getConnector(name, None):
            self.managers[dbtype].removeDb(name)
            del self.dbs[name]
            return True
        return False


class DbConnector(object):
    def __init__(self):
        # it could be used to notifiy some observer about changes in the db
        self.observers = []

    def saveDocument(self, document):
        raise NotImplementedError("DbConnector should not be used directly")

    def getDocument(self, documentId):
        raise NotImplementedError("DbConnector should not be used directly")

    def remove(self, documentId):
        raise NotImplementedError("DbConnector should not be used directly")

    def getDocsByFilter(self, parentId, type):
        raise NotImplementedError("DbConnector should not be used directly")


class FileSystemConnector(DbConnector):
    def __init__(self, base_path):
        super(FileSystemConnector, self).__init__()
        self.path = base_path

    def saveDocument(self, dic):
        try:
            filepath = os.path.join(self.path, "%s.json" % dic.get("_id"))
            getLogger(self).debug(
                "Saving document in local db %s" % self.path)
            with open(filepath, "w") as outfile:
                json.dump(dic, outfile, indent=2)
            return True
        except Exception:
            #log Exception?
            return False

    def getDocument(self, document_id):
        getLogger(self).debug(
            "Getting document for local db %s" % self.path)
        path = os.path.join(self.path, "%s.json" % document_id)
        document = open(path, "r")
        return json.loads(document.read())

    def remove(self, document_id):
        path = os.path.join(self.path, "%s.json" % document_id)
        if os.path.isfile(path):
            os.remove(path)

    def getDocsByFilter(self, parentId, type):
        result = []
        for name in os.listdir(self.path):
            path = os.path.join(self.path, name)
            document = open(path, "r")
            data = json.loads(document.read())
            if data.get("parent", None) == parentId:
                if data.get("type", None) == type:
                    result.append(name.split('.json')[0])
        return result


class CouchDbConnector(DbConnector):
    def __init__(self, db, seq_num=0):
        super(CouchDbConnector, self).__init__()
        self.db = db
        self.seq_num = seq_num
        self.mutex = threading.Lock()
        vmanager = ViewsManager()
        vmanager.addViews(self.db)

    #@trap_timeout
    def saveDocument(self, document):
        self.incrementSeqNumber()
        getLogger(self).debug(
            "Saving document in couch db %s" % self.db)
        return self.db.save_doc(document, use_uuids=True, force_update=True)

    #@trap_timeout
    def getDocument(self, document_id):
        getLogger(self).debug(
            "Getting document for couch db %s" % self.db)
        try:
            return self.db.get(document_id)
        except ResourceNotFound:
            return None

    #@trap_timeout
    def remove(self, document_id):
        if self.db.doc_exist(document_id):
            self.incrementSeqNumber()
            self.db.delete_doc(document_id)

    #@trap_timeout
    def getDocsByFilter(self, parentId, type):
        key = ['%s' % parentId, '%s' % type]
        docs_ids = [doc.get("value") for doc in self.db.view('mapper/byparentandtype', key=key)]
        return docs_ids

    def incrementSeqNumber(self):
        self.mutex.acquire()
        self.seq_num += 1
        self.mutex.release()

    #@trap_timeout
    def _compactDatabase(self):
        self.db.compact()


class AbstractPersistenceManager(object):
    def __init__(self):
        self.dbs = {}

    def createDb(self, name):
        if not self.getDb(name):
            self.dbs[name] = self._create(name)
            return self.dbs[name]
        return None

    def _loadDbs(self):
        raise NotImplementedError("AbstractPersistenceManager should not be used directly")

    def _create(self, name):
        raise NotImplementedError("AbstractPersistenceManager should not be used directly")

    def deleteDb(self, name):
        if self.getDb(name):
            self._delete(name)
            del self.dbs[name]
            return True
        return False

    def _delete(self, name):
        raise NotImplementedError("AbstractPersistenceManager should not be used directly")

    def getDbNames(self):
        return self.dbs.keys()

    def getDbs(self):
        return self.dbs

    def getDb(self, name):
        return self.dbs.get(name, None)


class FileSystemManager(AbstractPersistenceManager):
    """
    This is a file system manager for the workspace,
    it will load from the provided FS
    """
    def __init__(self, path=CONF.getPersistencePath()):
        super(FileSystemManager, self).__init__()
        getLogger(self).debug(
            "Initializing FileSystemManager for path [%s]" % path)
        self._path = path
        if not os.path.exists(self._path):
            os.mkdir(self._path)
        self._loadDbs()

    def _create(self, name):
        wpath = os.path.expanduser("~/.faraday/persistence/%s" % name)
        if not os.path.exists(wpath):
            os.mkdir(wpath)
            return FileSystemConnector(wpath)
        return None

    def _delete(self, name):
        if os.path.exists(os.path.join(self._path, name)):
            shutil.rmtree(os.path.join(self._path, name))

    def _loadDbs(self):
        for name in os.listdir(CONF.getPersistencePath()):
            if os.path.isdir(os.path.join(CONF.getPersistencePath(), name)):
                #if os.path.exists(os.path.join(CONF.getPersistencePath(), name, "%s.json" % name)):
                self.dbs[name] = FileSystemConnector(os.path.join(self._path,
                                                                  name))


class NoCouchDBError(Exception):
    pass


class NoConectionServer(object):
    """ Default to this server if no conectivity"""
    def create_db(*args):
        pass

    def all_dbs(*args, **kwargs):
        return []

    def get_db(*args):
        db_mock = mockito.mock(Database)
        mockito.when(db_mock).documents().thenReturn([])
        return db_mock

    def replicate(*args, **kwargs):
        pass

    def delete_db(*args):
        pass


class CouchDbManager(AbstractPersistenceManager):
    """
    This is a couchdb manager for the workspace,
    it will load from the couchdb databases
    """
    def __init__(self, uri):
        super(CouchDbManager, self).__init__()
        getLogger(self).debug(
            "Initializing CouchDBManager for url [%s]" % uri)
        self._lostConnection = False
        self.__uri = uri
        self.__serv = NoConectionServer()
        self._available = False
        try:
            if uri is not None:
                self.testCouchUrl(uri)
                url = urlparse(uri)
                getLogger(self).debug(
                    "Setting user,pass %s %s" % (url.username, url.password))
                self.__serv = Server(uri=uri)
                self.__serv.resource_class.credentials = (url.username, url.password)
                self._available = True
                self.pushReports()
                self._loadDbs()
        except:
            getLogger(self).warn("No route to couchdb server on: %s" % uri)
            getLogger(self).debug(traceback.format_exc())

    def _create(self, name):
        db = self.__serv.create_db(name.lower())
        return CouchDbConnector(db)

    def _delete(self, name):
        self.__serv.delete_db(name)

    #@trap_timeout
    def _loadDbs(self):
        for dbname in filter(lambda x: not x.startswith("_"), self.__serv.all_dbs()):
            getLogger(self).debug(
                "Asking couchdb for workspace [%s]" % dbname)
            db = self.__serv.get_db(dbname)
            seq = db.info()['update_seq']
            self.dbs[dbname] = CouchDbConnector(db, seq_num=seq)

    def pushReports(self):
        vmanager = ViewsManager()
        reports = os.path.join(os.getcwd(), "views", "reports")
        workspace = self.__serv.get_or_create_db("reports")
        vmanager.addView(reports, workspace)
        return self.__uri + "/reports/_design/reports/index.html"

    def isAvailable(self):
        return self._available

    def lostConnectionResolv(self):
        self._lostConnection = True
        self.__dbs.clear()
        self.__serv = NoConectionServer()

    def reconnect(self):
        ret_val = False
        ur = self.__uri
        if CouchDbManager.testCouch(ur):
            self.__serv = Server(uri = ur)
            self.__dbs.clear()
            self._lostConnection = False
            ret_val = True

        return ret_val

    @staticmethod
    def testCouch(uri):
        if uri is not None:
            host, port = None, None
            try:
                import socket
                url = urlparse(uri)
                proto = url.scheme
                host = url.hostname
                port = url.port

                port = port if port else socket.getservbyname(proto)
                s = socket.socket()
                s.settimeout(1)
                s.connect((host, int(port)))
            except:
                return False
            #getLogger(CouchdbManager).info("Connecting Couch to: %s:%s" % (host, port))
            return True

    def testCouchUrl(self, uri):
        if uri is not None:
            url = urlparse(uri)
            proto = url.scheme
            host = url.hostname
            port = url.port
            self.test(host, int(port))

    def test(self, address, port):
        import socket
        s = socket.socket()
        s.settimeout(1)
        s.connect((address, port))

    #@trap_timeout
    def replicate(self, workspace, *targets_dbs, **kwargs):
        getLogger(self).debug("Targets to replicate %s" % str(targets_dbs))
        for target_db in targets_dbs:
            src_db_path = "/".join([self.__uri, workspace])
            dst_db_path = "/".join([target_db, workspace])
            try:
                getLogger(self).info("workspace: %s, src_db_path: %s, dst_db_path: %s, **kwargs: %s" % (workspace, src_db_path, dst_db_path, kwargs))
                self.__peerReplication(workspace, src_db_path, dst_db_path, **kwargs)
            except ResourceNotFound as e:
                raise e
            except Exception as e:
                getLogger(self).error(e)
                raise 

    def __peerReplication(self, workspace, src, dst, **kwargs):
        mutual = kwargs.get("mutual", True)
        continuous = kwargs.get("continuous", True)
        ct = kwargs.get("create_target", True)

        self.__serv.replicate(workspace, dst, mutual = mutual, continuous  = continuous, create_target = ct)
        if mutual:
            self.__serv.replicate(dst, src, continuous = continuous, **kwargs)

    # def getLastChangeSeq(self, workspaceName):
    #     self.mutex.acquire()
    #     seq = self.__seq_nums[workspaceName]
    #     self.mutex.release()
    #     return seq

    # def setLastChangeSeq(self, workspaceName, seq_num):
    #     self.mutex.acquire()
    #     self.__seq_nums[workspaceName] = seq_num
    #     self.mutex.release()


    # #@trap_timeout
    # def waitForDBChange(self, db_name, since = 0, timeout = 15000):
    #     """ Be warned this will return after the database has a change, if
    #     there was one before call it will return immediatly with the changes
    #     done"""
    #     changes = []
    #     last_seq = max(self.getLastChangeSeq(db_name), since)
    #     db = self._getDb(db_name)
    #     with ChangesStream(db, feed="longpoll", since=last_seq, timeout=timeout) as stream:
    #         for change in stream:
    #             if change['seq'] > self.getLastChangeSeq(db_name):
    #                 self.setLastChangeSeq(db_name, change['seq'])
    #                 if not change['id'].startswith('_design'):
    #                     #fake doc type for deleted objects
    #                     doc = {'type': 'unknown', '_deleted': 'False', '_rev':[0]}
    #                     if not change.get('deleted'):
    #                         doc = self.getDocument(db_name, change['id'])
    #                     changes.append(change_factory.create(doc))
    #     if len(changes):
    #         getLogger(self).debug("Changes from another instance")
    #     return changes
