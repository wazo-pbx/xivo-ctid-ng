# -*- coding: utf-8 -*-
# Copyright 2015 by Avencall
# SPDX-License-Identifier: GPL-3.0+

import datetime
import logging
import iso8601

from functools import partial
from xivo_bus.collectd.calls.event import CallAbandonedCollectdEvent
from xivo_bus.collectd.calls.event import CallConnectCollectdEvent
from xivo_bus.collectd.calls.event import CallDurationCollectdEvent
from xivo_bus.collectd.calls.event import CallEndCollectdEvent
from xivo_bus.collectd.calls.event import CallStartCollectdEvent

from xivo_ctid_ng.core.ari_ import APPLICATION_NAME

logger = logging.getLogger(__name__)


class NullHandle(object):
    def close(self):
        pass


class CallsStasis(object):

    def __init__(self, ari_client, collectd, bus_publisher, services, xivo_uuid):
        self.ari = ari_client
        self.collectd = collectd
        self.bus_publisher = bus_publisher
        self.services = services
        self.xivo_uuid = xivo_uuid
        self.subscribe_all_channels_handle = NullHandle()

    def subscribe(self):
        self.ari.on_channel_event('StasisStart', self.stat_new_call)
        self.ari.on_channel_event('StasisStart', self.register_end_call_callbacks)
        self.ari.on_channel_event('StasisStart', self.bridge_connect_user)
        self.ari.on_channel_event('StasisStart', self.stat_connect_call)
        self.subscribe_all_channels_handle = self.ari.on_channel_event('StasisStart', self.subscribe_to_all_channel_events)

    def subscribe_to_all_channel_events(self, event_objects, event):
        self.subscribe_all_channels_handle.close()
        self.ari.applications.subscribe(applicationName=APPLICATION_NAME, eventSource='channel:')

    def bridge_connect_user(self, event_objects, event):
        if not is_connect_event(event):
            return

        channel = event_objects['channel']
        originator_channel_id = connect_event_originator(event)
        if not originator_channel_id:
            logger.error('tried to connect call %s but no originator found', channel.id)
            return

        logger.debug('connecting originator %s with callee %s', originator_channel_id, channel.id)
        originator_channel = self.ari.channels.get(channelId=originator_channel_id)
        channel.answer()
        originator_channel.answer()
        this_channel_id = channel.id
        bridge = self.ari.bridges.create(type='mixing')
        bridge.addChannel(channel=originator_channel_id)
        bridge.addChannel(channel=this_channel_id)

    def stat_new_call(self, event_objects, event):
        if is_connect_event(event):
            return

        app, app_instance = get_stasis_start_app(event)
        channel = event_objects['channel']
        logger.debug('sending stat for new call %s', channel.id)
        self.collectd.publish(CallStartCollectdEvent(app, app_instance, channel.id))

    def register_end_call_callbacks(self, event_objects, event):
        if is_connect_event(event):
            return

        app, app_instance = get_stasis_start_app(event)
        channel = event_objects['channel']
        logger.debug('registering end callbacks for call %s', channel.id)
        channel.on_event('ChannelDestroyed', partial(self.stat_end_call, app, app_instance))
        channel.on_event('ChannelDestroyed', partial(self.stat_call_duration, app, app_instance))
        channel.on_event('ChannelDestroyed', partial(self.stat_abandoned_call, app, app_instance))

    def stat_connect_call(self, event_objects, event):
        if not is_connect_event(event):
            return

        app, app_instance = get_stasis_start_app(event)
        channel = event_objects['channel']
        logger.debug('sending stat for connecting call %s', channel.id)
        self.collectd.publish(CallConnectCollectdEvent(app, app_instance, channel.id))

    def stat_end_call(self, app, app_instance, channel, event):
        logger.debug('sending stat for ended call %s', channel.id)
        self.collectd.publish(CallEndCollectdEvent(app, app_instance, channel.id))

    def stat_call_duration(self, app, app_instance, channel, event):
        start_time = channel.json['creationtime']
        start_datetime = iso8601.parse_date(start_time)

        end_time = event['timestamp']
        end_datetime = iso8601.parse_date(end_time)

        logger.debug('sending stat for duration of call %s', channel.id)
        duration = (end_datetime - start_datetime).seconds
        self.collectd.publish(CallDurationCollectdEvent(app, app_instance, channel.id, duration))

    def stat_abandoned_call(self, app, app_instance, channel, event):
        connected = channel.json['connected']
        if not connected.get('number'):
            logger.debug('sending stat for abandoned call %s', channel.id)
            self.collectd.publish(CallAbandonedCollectdEvent(app, app_instance, channel.id))


def get_stasis_start_app(event):
    if 'args' not in event:
        return None, None
    if len(event['args']) < 1:
        return None, None
    return event['application'], event['args'][0]


def is_connect_event(event):
    if 'args' not in event:
        return False
    if len(event['args']) < 2:
        return False
    return event['args'][1] == 'dialed_from'


def connect_event_originator(event):
    if 'args' not in event:
        return None
    if len(event['args']) < 3:
        return None
    return event['args'][2]
