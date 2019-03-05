# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from flask import request
from xivo.tenant_flask_helpers import Tenant

from xivo_ctid_ng.auth import get_token_user_uuid_from_request
from xivo_ctid_ng.auth import required_acl
from xivo_ctid_ng.rest_api import AuthResource

from .schemas import (
    fax_creation_request_schema,
    user_fax_creation_request_schema,
)


class FaxesResource(AuthResource):

    def __init__(self, faxes_service):
        self._service = faxes_service

    @required_acl('ctid-ng.faxes.create')
    def post(self):
        tenant = Tenant.autodetect()
        fax_infos = fax_creation_request_schema.load(request.args).data
        self._service.send_fax(tenant.uuid, content=request.data, fax_infos=fax_infos)
        return '', 204


class UserFaxesResource(AuthResource):

    def __init__(self, auth_client, faxes_service):
        self._auth_client = auth_client
        self._service = faxes_service

    @required_acl('ctid-ng.users.me.faxes.create')
    def post(self):
        tenant = Tenant.autodetect()
        user_uuid = get_token_user_uuid_from_request(self._auth_client)
        fax_infos = user_fax_creation_request_schema.load(request.args).data
        self._service.send_fax_from_user(tenant.uuid, user_uuid, content=request.data, fax_infos=fax_infos)
        return '', 204