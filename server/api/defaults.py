from __future__ import absolute_import
from flask_restful import Resource
from flask import request, make_response
from flask_api import status
from . import rest_api

import etcd3
import ujson
import ipaddress
import ipinfo

# etcd client
etcd = etcd3.client()

# Create ipinfo client/handler
apiKey = "KEY HERE"
ipHandler = ipinfo.getHandler(apiKey)

# Global values/functions
RespHeaders = { 'content-type': 'application/json; charset=UTF-8',
                'Access-Control-Allow-Origin': '*'} # Allow CORS

class IPMetadata(Resource):
    def get(self, ip):
        # Validate IP address
        try:
            ip = ipaddress.ip_address(ip)
        except Exception as err:
            return make_response(str(err), status.HTTP_400_BAD_REQUEST)

        if not ip.is_global:
            retMsg = "ERROR: IP address %s is not global % ip"
            return make_response(retMsg, status.HTTP_400_BAD_REQUEST)

        # Transform IP back to string for uniformity
        #   e.g. 192.168.01.10 => 192.168.1.10
        ip = str(ip)

        ipMeta = etcd.get(ip)[0]
        if not ipMeta:
            # Fetch and cache
            try:
                ipMeta = ipHandler.getDetails(ip).details
                self.storeMetadata(ip, ipMeta)
                ipMeta = str(ipMeta) # Convert for response
            except Exception as err:
                retMsg = "ERROR: Unable to get details for %s\n%s" % (ip, err)
                return make_response(retMsg, status.HTTP_503_SERVICE_UNAVAILABLE)
        else:
            # etcd returns byte array, convert to utf-8 string
            ipMeta = ipMeta.decode('utf-8')

        return make_response(ipMeta, RespHeaders)

    def storeMetadata(self, ip, ipMeta):
        assert type(ipMeta) is dict

        # TODO: Validate metadata? For now, just store body into etcd

        # Transform back into string and store into etcd
        etcd.put(ip, ujson.dumps(ipMeta))

        return


class AllIPMetadata(Resource):
    def get(self):
        retList = []
        allMeta = [res[0].decode('utf-8') for res in etcd.get_all()]
        for i in range(len(allMeta)):
            # Check if it's a dict
            try:
                ipMeta = ujson.loads(allMeta[i])
            except Exception as err:
                print("ERROR: The following is not properly formatted JSON:\n%s" % allMeta[i])
                continue

            # Extract relevant fields to create output expected by WorldMap
            try:
                loc = ipMeta['loc'].split(',')
                tmpDict = { 'key': ipMeta['ip'],
                            'name': ipMeta['ip'],
                            'latitude': float(loc[0]),
                            'longitude': float(loc[1])  }
            except KeyError as err:
                print("ERROR: %s; ensure entry was obtained from ipinfo:\n%s" % (err, allMeta[i]))
                continue
            except Exception as err:
                print("ERROR: Unknown exception:\n%s" % err)
                continue

            retList.append(tmpDict)

        return make_response(str(retList), RespHeaders)

rest_api.add_resource(IPMetadata, '/<string:ip>')
rest_api.add_resource(AllIPMetadata, '/all')

