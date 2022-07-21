import requests
import json


class DDnsV6(object):
    def __init__(self):
        self.config = None

    def get_ipv6(self):
        '''
        get ipv6 address from callmev6.tain.one
        '''
        url = 'https://callmev6.tain.one'
        r = requests.get(url)
        ip = r.text
        # remove '\n' from ipv6 string
        ip = ip.replace('\n', '')
        return ip

    def get_record_id(self):
        url = 'https://api.cloudflare.com/client/v4/zones/%s/dns_records' % self.config['zoneId']
        headers = {
            'Content-type': 'application/json',
            'Authorization': 'Bearer %s' % self.config['authKey']
        }
        r = requests.get(url, headers=headers)
        result = json.loads(r.text)['result']
        recordIdIn = list(
            filter(lambda x: x['name'] == self.config['name'], result))
        if len(recordIdIn) == 0:
            print('no record found')
            return False
        recordId = recordIdIn[0]['id']
        self.config['recordId'] = recordId
        return recordId

    def update_dns_v6(self, ip):
        '''
        update dns record with cloudflare api
        Args:
            ip: ipv6 address
        '''
        url = 'https://api.cloudflare.com/client/v4/zones/%s/dns_records/%s' % (
            self.config['zoneId'], self.config['recordId'])
        print(url)
        headers = {
            'Content-type': 'application/json',
            'Authorization': 'Bearer %s' % self.config['authKey']
        }
        data = {
            "type": "AAAA",
            "name": "%s" % self.config['name'],
            "content": ip,
            "proxied": False,
            "ttl": 1
        }
        r = requests.put(url, headers=headers, json=data)
        return r.text

    def load_configuration(self):
        """
        load configuration from config.json, if not exist, create one and exit
        """
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
        except FileNotFoundError:
            with open('config.json', 'w') as f:
                config = {
                    "zoneId": "",
                    "recordId": "",
                    "authKey": "",
                    "name": ""
                }
                json.dump(config, f, sort_keys=True,
                          indent=4, separators=(',', ': '))
                print(
                    'config.json not found, created a default config.json, please edit it')
                print('now exit')
                exit()
        self.config = config
        return

    def create_dns_v6(self, ip):
        '''
        create dns record with cloudflare api
        '''
        url = 'https://api.cloudflare.com/client/v4/zones/%s/dns_records' % self.config['zoneId']
        print(url)
        headers = {
            'Content-type': 'application/json',
            'Authorization': 'Bearer %s' % self.config['authKey']
        }
        data = {
            "type": "AAAA",
            "name": "%s" % self.config['name'],
            "content": ip,
            "proxied": False,
            "ttl": 1
        }
        r = requests.post(url, headers=headers, json=data)
        return r.text


if __name__ == '__main__':
    """
    main function
    """
    ddnsv6 = DDnsV6()
    # load configuration
    ddnsv6.load_configuration()
    # get ipv6
    ipv6 = ddnsv6.get_ipv6()
    print(ipv6)

    # get record id from cloudflare
    config = ddnsv6.config
    # assert config['recordId'] null or empty
    if not config.__contains__('recordId') or len(config['recordId']) == 0:
        recordId = ddnsv6.get_record_id()
        if recordId:
            config['recordId'] = recordId
            with open('config.json', 'w') as f:
                json.dump(config, f, sort_keys=True,
                          indent=4, separators=(',', ': '))
        else:
            result = ddnsv6.create_dns_v6(ipv6)
            print(result)
            exit()

    result = ddnsv6.update_dns_v6(ipv6)
    print(result)
