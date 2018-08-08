# -*- coding: utf-8 -*-
# Copyright 2016-2018 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from hamcrest import assert_that
from hamcrest import equal_to
from hamcrest import has_entries
from xivo_test_helpers import until

from .helpers.base import IntegrationTest
from .helpers.wait_strategy import (
    CtidNgConnectionsOkWaitStrategy,
    CtidNgEverythingOkWaitStrategy,
    CtidNgUpWaitStrategy,
)


class TestStatusARIStops(IntegrationTest):

    asset = 'basic_rest'
    wait_strategy = CtidNgConnectionsOkWaitStrategy()

    def test_given_ari_stops_when_status_then_ari_fail(self):
        self.stop_service('ari')

        def ari_is_down():
            result = self.ctid_ng.status()
            assert_that(result['connections']['ari'], equal_to('fail'))

        until.assert_(ari_is_down, tries=5)


class TestStatusNoRabbitMQ(IntegrationTest):

    asset = 'no_rabbitmq'
    wait_strategy = CtidNgUpWaitStrategy()

    def test_given_no_rabbitmq_when_status_then_rabbitmq_fail(self):
        result = self.ctid_ng.status()

        assert_that(result['connections']['bus_consumer'], equal_to('fail'))


class TestStatusRabbitMQStops(IntegrationTest):

    asset = 'basic_rest'
    wait_strategy = CtidNgConnectionsOkWaitStrategy()

    def test_given_rabbitmq_stops_when_status_then_rabbitmq_fail(self):
        self.stop_service('rabbitmq')

        def rabbitmq_is_down():
            result = self.ctid_ng.status()
            assert_that(result['connections']['bus_consumer'], equal_to('fail'))

        until.assert_(rabbitmq_is_down, tries=5)


class TestStatusAllOK(IntegrationTest):

    asset = 'real_asterisk'
    wait_strategy = CtidNgEverythingOkWaitStrategy()

    def test_given_auth_and_ari_and_rabbitmq_when_status_then_status_ok(self):

        def all_ok():
            result = self.ctid_ng.status()
            assert_that(result, has_entries(
                connections=has_entries(
                    ari='ok',
                    bus_consumer='ok',
                ),
                service_token='ok',
            ))

        until.assert_(all_ok, tries=10)
