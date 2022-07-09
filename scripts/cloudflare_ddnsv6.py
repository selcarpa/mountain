import requests

zoneId = ""
recordId = ""
authKey = ""
name = ""


def get_ipv6():
    '''
    获取自己的ipv6地址
    '''
    url = 'http://ipv6.icanhazip.com'
    r = requests.get(url)
    ip = r.text
    return ip


def getRecordId():
    url = 'https://api.cloudflare.com/client/v4/zones/%s/dns_records' % zoneId
    headers = {
        'Content-type': 'application/json',
        'Authorization': 'Bearer %s' % authKey
    }
    r = requests.get(url, headers=headers)
    print(r.text)
    return r.text


def cfDdnsv6(ip):
    '''
    使用cloudflare的ddns更新ip地址
    Args:
        ip: ip地址
    '''
    url = 'https://api.cloudflare.com/client/v4/zones/%s/dns_records/%s' % (
        zoneId, recordId)
    print(url)
    headers = {
        'Content-type': 'application/json',
        'Authorization': 'Bearer %s' % authKey
    }
    data = {
        "type": "AAAA",
        "name": "%s" % name,
        "content": ip,
        "proxied": False,
        "ttl": 1
    }
    r = requests.put(url, headers=headers, json=data)
    return r.text


if __name__ == '__main__':
    ipv6 = get_ipv6()
    print(ipv6)
    # 去除字符串中的换行符
    ipv6 = ipv6.replace('\n', '')

    # 获取cloudflare的record id
    # recordId = getRecordId()
    # print(recordId)

    result = cfDdnsv6(ipv6)
    print(result)
