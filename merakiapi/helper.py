import logging
from datetime import datetime, timedelta
from meraki import DashboardAPI as MerakiAPI
from django.conf import settings


from dashboard import models as dm

_logger = logging.getLogger(__name__)


class Meraki(object):
    client = None
    def __init__(self):
        api = MerakiAPI(
            api_key=settings.MERAKI_API_KEY,
            base_url=settings.MERAKI_BASE_URL,
            output_log=False)
        self.client = api

    #T0DO: add type hint in the parameter customer_id
    def get_network_events_for_customer(self, customer_id: str, productType='appliance', startAt=None):
        """
        args:
            customer_id: str
            productType: str
            startAt: int
        returns: list of events
            { "result": 1=success, 0=failed,
              "message": 'message',
              "total": overall count of events,
              "data": [
                {
                  "network_id": "network_id",
                  "network_name": "network_name",
                  "total": count of events
                  "events": [
                    {
                        "ts": "2018-02-11T00:00:00.090210Z",
                        "eventType": "File Scanned",
                        "clientName": "COMPUTER-M-V78J",
                        "clientMac": "10:dd:b1:eb:88:f8",
                        "clientIp": "192.168.128.2",
                        "srcIp": "192.168.128.2",
                        "destIp": "119.192.233.48",
                        "protocol": "http",
                        "uri": "http://www.favorite-icons.com/program/FavoriteIconsUninstall.exe",
                        "canonicalName": "PUA.Win.Dropper.Kraddare::1201",
                        "destinationPort": 80,
                        "fileHash": "3ec1b9a95fe62aa25fc959643a0f227b76d253094681934daaf628d3574b3463",
                        "fileType": "MS_EXE",
                        "fileSizeBytes": 193688,
                        "disposition": "Malicious",
                        "action": "Blocked"
                    },
                    {
                        "ts": "2018-02-11T00:00:00.090210Z",
                        "eventType": "IDS Alert",
                        "deviceMac": "00:18:0a:01:02:03",
                        "clientMac": "A1:B2:C3:D4:E5:F6",
                        "srcIp": "1.2.3.4:34195",
                        "destIp": "10.20.30.40:80",
                        "protocol": "tcp/ip",
                        "priority": "2",
                        "classification": "4",
                        "blocked": true,
                        "message": "SERVER-WEBAPP JBoss JMX console access attempt",
                        "signature": "1:21516:9",
                        "sigSource": "",
                        "ruleId": "meraki:intrusion/snort/GID/1/SID/26267"
                    }
                  ]
                },
                {
                  "network": "network_id",
                  "events": []
                }
              ]
            }
        """

        network_events = {
            "result": 0,
            "message": 'message',
            "total": 0,
            "data": []
        }
        one_day = 86400
        # get seven_days_ago from current datetime
        seven_days_ago = datetime.now() - timedelta(days=7)
        seven_days_ago_str = seven_days_ago.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        total_events = 0
        try:
            customer = dm.Customer.objects.get(id=customer_id)
            customer_networks = customer.customernetwork_set.all()

            for cn in customer_networks:
                network_data = {}
                network_data["network_id"] = cn.network.network_id
                network_data["network_name"] = cn.network.name
                network_data["total"] = 0
                network_data["events"] = []
                network_event_count = 0
                cne = []

                try:
                    cne = self.client.appliance.getNetworkApplianceSecurityEvents(networkId=cn.network.network_id, timespan=one_day+2)
                except Exception as e:
                    print(f"error getting network events: {e}")
                    _logger.error(f"error getting network events: {e}", exc_info=True)


                for ne in cne:
                    total_events += 1
                    network_data["total"] += 1
                    network_data["events"].append(ne)

                network_events["data"].append(network_data)
                network_events["total"] = total_events
        except Exception as e:
            _logger.error(f"Error getting network events: {e}", exc_info=True)
            print(f"gg = Error getting network events: {e}")
            return network_events

        return network_events





