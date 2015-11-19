# -*- coding: utf-8 -*-

# Copyright (C) 2015 Avencall
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

from hamcrest import assert_that
from hamcrest import contains
from hamcrest import contains_inanyorder
from hamcrest import has_entries

from .base import IntegrationTest
from .base import MockBridge
from .base import MockChannel


class TestListCalls(IntegrationTest):

    asset = 'basic_rest'

    def setUp(self):
        super(TestListCalls, self).setUp()
        self.reset_ari()
        self.reset_confd()

    def test_given_no_calls_when_list_calls_then_empty_list(self):
        calls = self.list_calls()

        assert_that(calls, contains())

    def test_given_some_calls_and_no_user_id_when_list_calls_then_list_calls_with_no_user_uuid(self):
        self.set_ari_channels(MockChannel(id='first-id'),
                              MockChannel(id='second-id'))

        calls = self.list_calls()

        assert_that(calls, contains_inanyorder(
            has_entries({'call_id': 'first-id',
                         'user_uuid': None}),
            has_entries({'call_id': 'second-id',
                         'user_uuid': None})))

    def test_given_some_calls_with_user_id_when_list_calls_then_list_calls_with_user_uuid(self):
        self.set_ari_channels(MockChannel(id='first-id'),
                              MockChannel(id='second-id'))
        self.set_ari_channel_variable({'first-id': {'XIVO_USERID': 'user1-id'},
                                       'second-id': {'XIVO_USERID': 'user2-id'}})
        self.set_confd_users({'user1-id': {'uuid': 'user1-uuid'},
                              'user2-id': {'uuid': 'user2-uuid'}})

        calls = self.list_calls()

        assert_that(calls, contains_inanyorder(
            has_entries({'call_id': 'first-id',
                         'user_uuid': 'user1-uuid'}),
            has_entries({'call_id': 'second-id',
                         'user_uuid': 'user2-uuid'})))

    def test_given_some_calls_when_list_calls_then_list_calls_with_status(self):
        self.set_ari_channels(MockChannel(id='first-id', state='Up'),
                              MockChannel(id='second-id', state='Ringing'))

        calls = self.list_calls()

        assert_that(calls, contains_inanyorder(
            has_entries({'call_id': 'first-id',
                         'status': 'Up'}),
            has_entries({'call_id': 'second-id',
                         'status': 'Ringing'})))

    def test_given_some_calls_when_list_calls_then_list_calls_with_bridges(self):
        self.set_ari_channels(MockChannel(id='first-id'),
                              MockChannel(id='second-id'))
        self.set_ari_bridges(MockBridge(id='first-bridge', channels=['first-id']),
                             MockBridge(id='second-bridge', channels=['second-id']))

        calls = self.list_calls()

        assert_that(calls, contains_inanyorder(
            has_entries({'call_id': 'first-id',
                         'bridges': ['first-bridge']}),
            has_entries({'call_id': 'second-id',
                         'bridges': ['second-bridge']})))
