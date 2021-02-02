"""
Faraday Penetration Test IDE
Copyright (C) 2013  Infobyte LLC (http://www.infobytesec.com/)
See the file 'doc/LICENSE' for the license information

"""
"""
This module will help us to retrieve information
about the app state and system information and
report it to developers to be able to get information about
a crash or bug
"""
import sys
import traceback
import threading
import requests
import faraday_client.model.guiapi
from io import StringIO
from faraday_client.gui.customevents import ShowExceptionCustomEvent
from faraday_client.config.configuration import getInstanceConfiguration
import json
import time

try:
    import pip
except ImportError:
    pass

CONF = getInstanceConfiguration()


def get_crash_log():
    pass


def get_system_info():
    pass


def exception_handler(obj_type, value, tb):
    """
    This is a custom exception handler to replace the python original one.
    The idea is to show the user a dialog with the information and let him/her
    decide wether to send the developers a report with additional info.
    The report is created and sent using the callback.
    Since this handler may be called from threads, the dialog must be created
    using gtk idle_add or signals to avoid issues.
    """
    import hashlib
    import platform
    import distro

    text = StringIO()
    traceback.print_exception(obj_type, value, tb, file=text)
    error_name = text.getvalue().split('\n')[-2]

    excepts = f"{text.getvalue()}".encode('utf-8')
    exception_hash = hashlib.sha256(excepts).hexdigest()
    os_dist = " ".join(distro.linux_distribution())
    python_version = platform.python_version()
    faraday_version = CONF.getVersion()

    modules_info = ""
    try:
        modules_info = ",".join(["%s=%s" % (x.key, x.version)
                                 for x in pip.get_installed_distributions()])
    except (ImportError, AttributeError):
        pass

    python_dist = f"Python {python_version} - Modules: [ {modules_info} ]"

    description = f"""
OS: {os_dist}
Faraday client: {faraday_version}
Python version: {python_dist}
Hash: {exception_hash}
Exception:\n{excepts.decode('utf-8')}"""

    event = ShowExceptionCustomEvent(description, reportToDevelopers, error_name)
    faraday_client.model.guiapi.postCustomEvent(event)
    text.seek(0)
    text.truncate()
    del text


def reportToDevelopers(name=None, *description):
    try:

        uri = CONF.getTktPostUri()
        headers = json.loads(CONF.getApiParams())
        params = json.loads(CONF.getApiParams())

        params['description'] = description[1]

        if name is not None:
            params['summary'] = name
        else:
            params['summary'] = 'autoreport %s' % time.time()

        resp = requests.post(uri,
                             headers=headers,
                             data=params, timeout=1, verify=True)

        model.api.devlog("Report sent to faraday server")

    except Exception as e:
        model.api.devlog("Error reporting to developers:")
        model.api.devlog(e)


def installThreadExcepthook():
    """
    Workaround for sys.excepthook thread bug from
    http://spyced.blogspot.com/2007/06/workaround-for-sysexcepthook-bug.html
    (https://sourceforge.net/tracker/?func=detail&atid=105470&aid=1230540&group_id=5470).
    Call once from __main__ before creating any threads.
    If using psyco, call psyco.cannotcompile(threading.Thread.run)
    since this replaces a new-style class method.
    """
    init_old = threading.Thread.__init__

    def init(self, *args, **kwargs):
        init_old(self, *args, **kwargs)
        run_old = self.run

        def run_with_except_hook(*args, **kw):
            try:
                run_old(*args, **kw)
            except Exception as e:
                if isinstance(e, (KeyboardInterrupt, SystemExit)):
                    raise
                sys.excepthook(*sys.exc_info())

        self.run = run_with_except_hook

    threading.Thread.__init__ = init

# I'm Py3
