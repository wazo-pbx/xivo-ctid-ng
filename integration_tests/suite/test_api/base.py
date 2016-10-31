# -*- coding: utf-8 -*-
# Copyright 2015-2016 by Avencall
# Copyright 2016 by Proformatique Inc.
# SPDX-License-Identifier: GPL-3.0+

import ari
import os
import logging
import time

from ari.exceptions import ARINotFound
from requests.packages import urllib3
from xivo_test_helpers.asset_launching_test_case import AssetLaunchingTestCase
from xivo_test_helpers.asset_launching_test_case import NoSuchService
from xivo_test_helpers.asset_launching_test_case import NoSuchPort

from .amid import AmidClient
from .ari_ import ARIClient
from .auth import AuthClient
from .bus import BusClient
from .chan_test import ChanTest
from .confd import ConfdClient
from .constants import ASSET_ROOT
from .ctid_ng import CtidNgClient
from .stasis import StasisClient
from .wait_strategy import CtidNgConnectionsOkWaitStrategy

logger = logging.getLogger(__name__)

urllib3.disable_warnings()
if os.environ.get('TEST_LOGS') != 'verbose':
    logging.getLogger('swaggerpy.client').setLevel(logging.WARNING)
    logging.getLogger('amqp').setLevel(logging.INFO)


class WrongClient(object):
    def __init__(self, client_name):
        self.client_name = client_name

    def __getattr__(self, member):
        raise Exception('Could not create client {}'.format(self.client_name))


class IntegrationTest(AssetLaunchingTestCase):

    assets_root = ASSET_ROOT
    service = 'ctid-ng'
    wait_strategy = CtidNgConnectionsOkWaitStrategy()

    @classmethod
    def setUpClass(cls):
        super(IntegrationTest, cls).setUpClass()
        cls.reset_clients()
        cls.reset_bus_client()
        cls.wait_strategy.wait(cls)

    @classmethod
    def reset_clients(cls):
        try:
            cls.amid = AmidClient('localhost', cls.service_port(9491, 'amid'))
        except (NoSuchService, NoSuchPort) as e:
            logger.debug(e)
            cls.amid = WrongClient('amid')
        try:
            cls.ari = ARIClient('localhost', cls.service_port(5039, 'ari'))
        except (NoSuchService, NoSuchPort) as e:
            logger.debug(e)
            cls.ari = WrongClient('ari')
        try:
            cls.auth = AuthClient('localhost', cls.service_port(9497, 'auth'))
        except (NoSuchService, NoSuchPort) as e:
            logger.debug(e)
            cls.auth = WrongClient('auth')
        try:
            cls.confd = ConfdClient('localhost', cls.service_port(9486, 'confd'))
        except (NoSuchService, NoSuchPort) as e:
            logger.debug(e)
            cls.confd = WrongClient('confd')
        try:
            cls.ctid_ng = CtidNgClient('localhost', cls.service_port(9500, 'ctid-ng'))
        except (NoSuchService, NoSuchPort) as e:
            logger.debug(e)
            cls.ctid_ng = WrongClient('ctid_ng')
        try:
            cls.stasis = StasisClient('localhost', cls.service_port(5039, 'ari'))
        except (NoSuchService, NoSuchPort) as e:
            logger.debug(e)
            cls.stasis = WrongClient('stasis')

    @classmethod
    def reset_bus_client(cls):
        '''
        The bus client is "special" because it has state: when calling
        listen_events(), it stores events in its members. If reset like the
        others, we lose this state.

        '''
        try:
            cls.bus = BusClient('localhost', cls.service_port(5672, 'rabbitmq'))
        except (NoSuchService, NoSuchPort) as e:
            logger.debug(e)
            cls.bus = WrongClient('bus')

    @classmethod
    def wait_for_ctid_ng_to_connect_to_bus(cls):
        time.sleep(4)


class RealAsteriskIntegrationTest(IntegrationTest):
    asset = 'real_asterisk'

    @classmethod
    def setUpClass(cls):
        super(RealAsteriskIntegrationTest, cls).setUpClass()
        cls.chan_test = ChanTest(cls.ari_config())

    @classmethod
    def ari_config(cls):
        return {
            'base_url': 'http://localhost:{port}'.format(port=cls.service_port(5039, 'ari')),
            'username': 'xivo',
            'password': 'xivo',
        }

    def setUp(self):
        super(RealAsteriskIntegrationTest, self).setUp()
        self.ari = ari.connect(**self.ari_config())

    def tearDown(self):
        self.clear_channels()
        super(RealAsteriskIntegrationTest, self).tearDown()

    def clear_channels(self):
        for channel in self.ari.channels.list():
            try:
                channel.hangup()
            except ARINotFound:
                pass
