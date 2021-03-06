# Copyright 2021 Thomas Lin
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
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
                ipMeta = ujson.dumps(ipMeta) # Convert for response
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
    # Uses IP metadata to craft a custom string w/ format: IP (city, region, country)
    def createName(self, ipMeta):
        assert type(ipMeta) is dict
        city = ipMeta.get('city')
        region = ipMeta.get('region')
        country = ipMeta.get('country_name')

        if city == region:
            metaVals = [city, country]
        else:
            metaVals = [city, region, country]

        return "%s (%s)" % (ipMeta['ip'], ', '.join(metaVals))

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
                            'name': self.createName(ipMeta),
                            'latitude': float(loc[0]),
                            'longitude': float(loc[1])  }
            except KeyError as err:
                print("ERROR: %s; ensure entry was obtained from ipinfo:\n%s" % (err, allMeta[i]))
                continue
            except Exception as err:
                print("ERROR: Unknown exception:\n%s" % err)
                continue

            retList.append(tmpDict)

        # Use ujson to convert to string to ensure compatibility w/ JSON's double-quotes
        return make_response(ujson.dumps(retList), RespHeaders)

rest_api.add_resource(IPMetadata, '/<string:ip>')
rest_api.add_resource(AllIPMetadata, '/all')

