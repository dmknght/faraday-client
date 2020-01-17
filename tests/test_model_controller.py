'''
Faraday Penetration Test IDE
Copyright (C) 2013  Infobyte LLC (http://www.infobytesec.com/)
See the file 'doc/LICENSE' for the license information

'''
from __future__ import absolute_import
from __future__ import print_function

from queue import Queue

import time

from unittest import mock
import pytest

from faraday_client.managers.mapper_manager import MapperManager
from faraday_client.model import Modelactions
from faraday_client.model.controller import ModelController
from tests.factories import (
    WorkspaceFactory,
    VulnerabilityFactory,
    HostFactory,
    VulnerabilityWebFactory,
    CredentialFactory,
    ServiceFactory
)

TEST_CASES = {
    'hosts': {
            'factory': HostFactory,
            'class_signature': 'Host',
            'expected_result': {}
        },
    'vulns': {
            'factory':VulnerabilityFactory,
            'class_signature': 'Vulnerability',
            'api_result': {
                'name': 'Vuln 1',
                'desc': 'Description',
                'data': 'Data',
                'severity': 'critical',
                'confirmed': True,
            },
        },
    'vulns': {
        'factory': VulnerabilityWebFactory,
        'class_signature': 'VulnerabilityWeb',
        'api_result': {
            'name': 'Vuln 1',
            'desc': 'Description',
            'data': 'Data',
            'severity': 'critical',
            'confirmed': True,
        },
    },
    'credential': {
        'factory': CredentialFactory,
        'class_signature': 'Cred',
        'api_result': {
            'name': 'test',
            'username': 'test',
            'password': 'test'
        },
    },
    'services': {
        'factory': ServiceFactory,
        'class_signature': 'Service',
        'api_result': {
            'name': 'SSH',
            'protocol': 'tcp',
            'ports': [22],
            'version': '2.1',
            'status': 'open'
        }
    }
}

def test_controller_stop_when_is_not_processing():
    mappers_manager = MapperManager()
    pending_actions = Queue()
    controller = ModelController(mappers_manager, pending_actions)
    assert controller.processing is False
    assert controller._must_stop is False
    controller.start()
    assert controller.is_alive()
    controller.stop()
    controller.join()
    assert controller._must_stop is True
    assert controller.is_alive() is False


def test_controller_cant_be_stopped_when_is_processing():
    """
        If someone tells the controller to stop and it is processing then it
        will stop when the processing finishes
    """

    mappers_manager = MapperManager()
    pending_actions = Queue()
    controller = ModelController(mappers_manager, pending_actions)
    assert controller.processing is False
    assert controller._must_stop is False
    controller.start()
    controller.processing = True
    controller.active_plugins_count = 1
    assert controller.is_alive()
    controller.stop()
    assert controller._must_stop is True
    assert controller.processing
    controller.join(timeout=2)
    assert controller.is_alive()
    controller.processing = False
    controller.join()
    assert controller.is_alive() is False


def test_controller_plugin_start_action_updates_internal_state():
    mappers_manager = MapperManager()
    pending_actions = Queue()
    controller = ModelController(mappers_manager, pending_actions)
    controller.start()
    controller.add_action((Modelactions.PLUGINSTART, "test", None))
    time.sleep(1)
    assert controller.active_plugins_count == 1
    assert controller.processing
    controller.add_action((Modelactions.PLUGINEND, "test", None))
    time.sleep(1)
    assert controller.active_plugins_count == 0
    assert controller.processing is False
    controller.stop()
    controller.join()
    assert controller.is_alive() is False

def test_only_start_plugin():
    mappers_manager = MapperManager()
    pending_actions = Queue()
    controller = ModelController(mappers_manager, pending_actions)
    controller._pluginStart('test', None)
    assert controller.active_plugins_count == 1
    assert controller.processing
    controller._pluginStart('test', None)
    assert controller.active_plugins_count == 2

def test_only_end_pluging():
    mappers_manager = MapperManager()
    pending_actions = Queue()
    controller = ModelController(mappers_manager, pending_actions)
    controller._pluginStart('test', None)
    controller._pluginEnd('test', None)
    assert controller.active_plugins_count == 0
    assert controller.processing is False

def test_end_pluging_multiple_times():
    mappers_manager = MapperManager()
    pending_actions = Queue()
    controller = ModelController(mappers_manager, pending_actions)
    controller._pluginEnd('test', None)
    controller._pluginEnd('test', None)
    assert controller.active_plugins_count == 0
    assert controller.processing is False



@pytest.mark.parametrize("url_endpoint, test_data", list(TEST_CASES.items()))
@mock.patch('faraday_client.persistence.server.server._get')
def test_find(get, url_endpoint, test_data, session):
    if 'api_result' in test_data:
        get.return_value = test_data['api_result']
    mappers_manager = MapperManager()
    pending_actions = Queue()
    controller = ModelController(mappers_manager, pending_actions)
    workspace = WorkspaceFactory.create()
    mappers_manager.createMappers(workspace.name)
    obj = test_data['factory'].create(workspace=workspace)
    session.add(obj)
    session.commit()
    result = controller.find(test_data['class_signature'], obj.id)
    assert get.called
    print(get.mock_calls[0][1][0])
    assert get.mock_calls[0][1][0].endswith(
        '/_api/v2/ws/{0}/{1}/{2}/'.format(workspace.name, url_endpoint, obj.id))


# I'm Py3
