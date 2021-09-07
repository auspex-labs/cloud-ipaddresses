import re
import json
from ipaddress import ip_network

import requests

AWS_SOURCE = "https://ip-ranges.amazonaws.com/ip-ranges.json"

AZURE_SOURCE = "https://www.microsoft.com/en-us/download/confirmation.aspx?id=56519"

GPC_SOURCE = "https://www.gstatic.com/ipranges/cloud.json"

OCEAN_SOURCE = "http://digitalocean.com/geo/google.csv"

ORACLE_SOUCE = "https://docs.oracle.com/iaas/tools/public_ip_ranges.json"

IPV4_FILE = "cloud_networks_4.json"

IPV6_FILE = "cloud_networks_6.json"


def aws(url=AWS_SOURCE):

    aws_ranges = json.loads(requests.get(url).content)

    aws_ipv4prefixes = set()
    for prefix in aws_ranges["prefixes"]:
        aws_ipv4prefixes.add(ip_network(prefix["ip_prefix"]))

    aws_ipv6prefixes = set()
    for prefix in aws_ranges["ipv6_prefixes"]:
        aws_ipv6prefixes.add((ip_network(prefix["ipv6_prefix"])))

    return aws_ipv4prefixes, aws_ipv6prefixes


def azure(url=AZURE_SOURCE):

    azure_address_page = requests.get(url)

    azure_ranges = json.loads(requests.get(re.findall(r"https://download.*?\.json", azure_address_page.text)[0]).content)

    az_ipv4prefixes = set()
    az_ipv6prefixes = set()

    for prefix in azure_ranges["values"]:
        for network in prefix["properties"]["addressPrefixes"]:
            net = ip_network(network)
            if net.version == 4:
                az_ipv4prefixes.add(net)
            elif net.version == 6:
                az_ipv6prefixes.add(net)
            else:
                continue

    return az_ipv4prefixes, az_ipv6prefixes


def gpc(url=GPC_SOURCE):

    gpc_ranges = json.loads(requests.get(url).content)

    gpc_ipv4prefixes = set()
    gpc_ipv6prefixes = set()

    for prefix in gpc_ranges["prefixes"]:
        if prefix.get("ipv4Prefix") is not None:
            gpc_ipv4prefixes.add(ip_network(prefix.get("ipv4Prefix")))
        if prefix.get("ipv6Prefix") is not None:
            gpc_ipv6prefixes.add(ip_network(prefix.get("ipv6Prefix")))

    return ipv4prefixes, ipv6prefixes


def ocean(url=OCEAN_SOURCE):

    ocean_ranges = requests.get(url).content

    do_ipv4prefixes = set()
    do_ipv6prefixes = set()

    for prefix in ocean_ranges.splitlines():
        net = ip_network(prefix.decode("utf-8").split(",")[0])
        if net.version == 4:
            do_ipv4prefixes.add(net)
        elif net.version == 6:
            do_ipv6prefixes.add(net)
        else:
            continue

    return do_ipv4prefixes, do_ipv6prefixes


def oracle(url=ORACLE_SOUCE):

    oracle_ranges = json.loads(requests.get(url).content)

    orc_ipv4prefixes = set()
    orc_ipv6prefixes = set()

    for cidrs in oracle_ranges["regions"]:  # TODO Needs better variable names
        for cidr in cidrs["cidrs"]:
            net = ip_network(cidr["cidr"])
            if net.version == 4:
                orc_ipv4prefixes.add(net)
            elif net.version == 6:
                orc_ipv6prefixes.add(net)
            else:
                continue

    return ipv4prefixes, ipv6prefixes


def merge_networks(prefixes):

    cidr = list(prefixes)
    cidr.sort()
    cidr = [str(net) for net in cidr]

    # Find and merge adjacent CIDRs.

    networks = dict()

    for net in cidr:
        if int(net.split("/")[1]) not in networks.keys():
            networks.update({(int(net.split("/")[1])): []})
        networks[int(net.split("/")[1])].append(net)

    updates = True
    while updates:
        updates = False
        for mask in sorted(networks.copy(), reverse=False):
            for network in networks[mask].copy():
                complete = True
                for sub in ip_network(network).supernet().subnets():
                    if str(sub) not in networks[mask]:
                        complete = False
                if complete:
                    updates = True
                    supernet = str(ip_network(network).supernet())
                    if int(supernet.split("/")[1]) in networks:
                        networks[int(supernet.split("/")[1])].append(supernet)
                    else:
                        networks.update({(int(supernet.split("/")[1])): [supernet]})
                    for sub in ip_network(network).supernet().subnets():
                        networks[mask].remove(str(sub))

    # net_count = 0
    # for net in networks:
    #     net_count += len(networks[net])

    return networks


def write_networks(networks, network_file):

    with open(network_file, "w") as open_file:
        json.dump(networks, open_file, indent=4, sort_keys=True)


ipv4prefixes = set()
ipv6prefixes = set()

aws4, aws6 = aws()
azure4, azure6 = azure()
gpc4, gpc6 = gpc()
ocean4, ocean6 = ocean()
oracle4, oracle6 = oracle()

ipv4prefixes.update(aws4)
ipv4prefixes.update(azure4)
ipv4prefixes.update(gpc4)
ipv4prefixes.update(ocean4)
ipv4prefixes.update(oracle4)

ipv6prefixes.update(aws6)
ipv6prefixes.update(azure6)
ipv6prefixes.update(gpc6)
ipv6prefixes.update(ocean6)
ipv6prefixes.update(oracle6)

ipv4nets = merge_networks(ipv4prefixes)
ipv6nets = merge_networks(ipv6prefixes)

print(len(ipv4nets))


# write_networks(ipv4nets, IPV4_FILE)
# write_networks(ipv6nets, IPV6_FILE)
