from __future__ import absolute_import
from flask_restful import Resource
from flask import request, make_response
from flask_api import status
from . import rest_api

import etcd3
import ujson

# etcd client
etcd = etcd3.client()

class IpMetadata(Resource):
    def get(self, ip):
        # TODO: Validate IP address... for now just use it

        metadata = etcd.get(ip)[0]
        if not metadata:
            return make_response('{}') # Or return error?

        metadata = ujson.loads(metadata)

        retMsg = "You called GET w/ key %s! Result: %s" % (ip, metadata)
        return make_response(retMsg)

    def put(self, ip):
        return self.post(ip)

    def post(self, ip):
        body = request.get_data()
        if not body:
            retMsg = "Missing JSON body with service name and metadata"
            return make_response(retMsg, status.HTTP_400_BAD_REQUEST)

        try:
            metadata = ujson.loads(body) # Transform into dict for validation purposes
        except Exception as err:
            retMsg = str(err)
            return make_response(retMsg, status.HTTP_400_BAD_REQUEST)

        # TODO: Validate metadata... for now, just store body into etcd

        # Transform back into string and store into etcd
        etcd.put(ip, ujson.dumps(metadata))

        retMsg = "You called PUT w/ key %s!" % ip
        return make_response(retMsg)

rest_api.add_resource(IpMetadata, '/<string:ip>')

