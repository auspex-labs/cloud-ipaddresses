"""
Copyright 2024 Auspex Labs Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.


This script collects the advertised IP addresses from the top cloud providers and aggregates them into a single file.
"""

import json
import re
from ipaddress import ip_network, collapse_addresses
import requests

AWS_SOURCE = "https://ip-ranges.amazonaws.com/ip-ranges.json"

AZURE_SOURCE = "https://www.microsoft.com/en-us/download/confirmation.aspx?id=56519"

GPC_SOURCE = "https://www.gstatic.com/ipranges/cloud.json"

OCEAN_SOURCE = "http://digitalocean.com/geo/google.csv"

ORACLE_SOUCE = "https://docs.oracle.com/iaas/tools/public_ip_ranges.json"

LINODE_SOURCE = "https://geoip.linode.com/"

IPV4_FILE = "cloud_networks_4.json"

IPV6_FILE = "cloud_networks_6.json"


def aws(url: str = AWS_SOURCE):

    aws_ranges = json.loads(requests.get(url).content)

    aws_ipv4prefixes = set()
    for prefix in aws_ranges["prefixes"]:
        aws_ipv4prefixes.add(ip_network(prefix["ip_prefix"]))

    aws_ipv6prefixes = set()
    for prefix in aws_ranges["ipv6_prefixes"]:
        aws_ipv6prefixes.add((ip_network(prefix["ipv6_prefix"])))

    return aws_ipv4prefixes, aws_ipv6prefixes


def azure(url: str = AZURE_SOURCE):

    azure_address_page = requests.get(url)

    azure_ranges = json.loads(requests.get(re.findall(r"https://download.*?\.json", azure_address_page.text)[0]).content)

    az_ipv4prefixes = set()
    az_ipv6prefixes = set()

    for prefix in azure_ranges["values"]:
        for network in prefix["properties"]["addressPrefixes"]:
            try:
                net = ip_network(network)
            except ValueError:
                continue
            if net.version == 4:
                az_ipv4prefixes.add(net)
            elif net.version == 6:
                az_ipv6prefixes.add(net)
            else:
                continue

    return az_ipv4prefixes, az_ipv6prefixes


def gpc(url: str = GPC_SOURCE):

    gpc_ranges = json.loads(requests.get(url).content)

    gpc_ipv4prefixes = set()
    gpc_ipv6prefixes = set()

    for prefix in gpc_ranges["prefixes"]:
        if prefix.get("ipv4Prefix") is not None:
            gpc_ipv4prefixes.add(ip_network(prefix.get("ipv4Prefix")))
        if prefix.get("ipv6Prefix") is not None:
            gpc_ipv6prefixes.add(ip_network(prefix.get("ipv6Prefix")))

    return gpc_ipv4prefixes, gpc_ipv6prefixes


def ocean(url: str = OCEAN_SOURCE):

    ocean_ranges = requests.get(url).content

    do_ipv4prefixes = set()
    do_ipv6prefixes = set()

    for prefix in ocean_ranges.splitlines():
        try:
            net = ip_network(prefix.decode("utf-8").split(",")[0])
        except ValueError:
            continue
        if net.version == 4:
            do_ipv4prefixes.add(net)
        elif net.version == 6:
            do_ipv6prefixes.add(net)
        else:
            continue

    return do_ipv4prefixes, do_ipv6prefixes


def oracle(url: str = ORACLE_SOUCE):

    oracle_ranges = json.loads(requests.get(url).content)

    orc_ipv4prefixes = set()
    orc_ipv6prefixes = set()

    # TODO Needs better variable names
    for cidrs in oracle_ranges["regions"]:
        for cidr in cidrs["cidrs"]:
            try:
                net = ip_network(cidr["cidr"])
            except ValueError:
                continue
            if net.version == 4:
                orc_ipv4prefixes.add(net)
            elif net.version == 6:
                orc_ipv6prefixes.add(net)
            else:
                continue

    return orc_ipv4prefixes, orc_ipv6prefixes


def linode(url: str = LINODE_SOURCE):

    linode_ranges = requests.get(url).content

    lin_ipv4prefixes = set()
    lin_ipv6prefixes = set()

    for prefix in linode_ranges.splitlines():
        if prefix.decode("utf-8")[0] == "#":
            continue

        try:
            net = ip_network(prefix.decode("utf-8").split(",")[0])
        except ValueError:
            continue
        if net.version == 4:
            lin_ipv4prefixes.add(net)
        elif net.version == 6:
            lin_ipv6prefixes.add(net)
        else:
            continue

    return lin_ipv4prefixes, lin_ipv6prefixes


def write_networks(networks, network_file) -> None:

    with open(network_file, "w", encoding='utf-8') as open_file:
        try:
            json.dump(networks, open_file, indent=4, sort_keys=True)
        except json.JSONDecodeError:
            pass

    open_file.close()


ipv4prefixes = set()
ipv6prefixes = set()

aws4, aws6 = aws()
azure4, azure6 = azure()
gpc4, gpc6 = gpc()
ocean4, ocean6 = ocean()
oracle4, oracle6 = oracle()
linode4, linode6 = linode()

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

ipv4nets = list(collapse_addresses(ipv4prefixes))
ipv6nets = list(collapse_addresses(ipv6prefixes))

ipv4nets = [str(i) for i in ipv4nets]
ipv6nets = [str(i) for i in ipv6nets]

write_networks(ipv4nets, IPV4_FILE)
write_networks(ipv6nets, IPV6_FILE)
