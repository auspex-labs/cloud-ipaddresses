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


This script collects the advertised IP addresses from the top cloud providers and aggregates them into separate files for IPv4 and IPv6 addresses.
"""

import json
import re
from ipaddress import ip_network, collapse_addresses
import requests

# Cloud providers' IP ranges sources
AWS_SOURCE = "https://ip-ranges.amazonaws.com/ip-ranges.json"
AZURE_DOWNLOAD_PAGE = "https://www.microsoft.com/en-us/download/confirmation.aspx?id=56519"
GPC_SOURCE = "https://www.gstatic.com/ipranges/cloud.json"
OCEAN_SOURCE = "http://digitalocean.com/geo/google.csv"
ORACLE_SOURCE = "https://docs.oracle.com/iaas/tools/public_ip_ranges.json"
LINODE_SOURCE = "https://geoip.linode.com/"

# Output files
IPV4_FILE = "cloud_networks_4.json"
IPV6_FILE = "cloud_networks_6.json"


def fetch_aws_ip_ranges(url: str):
    """
    Fetches IP ranges from AWS.

        Args:
            url (str): The URL to the JSON file containing the IP ranges.

        Returns:
            ipv4prefixes (set): A set of IPv4 prefixes.
            ipv6prefixes (set): A set of IPv6 prefixes.
    """
    response = requests.get(url, timeout=10).json()
    ipv4prefixes: set = {ip_network(prefix["ip_prefix"]) for prefix in response.get("prefixes", [])}
    ipv6prefixes: set = {ip_network(prefix["ipv6_prefix"]) for prefix in response.get("ipv6_prefixes", [])}
    return ipv4prefixes, ipv6prefixes


def fetch_azure_ip_ranges(url: str):
    """
    Fetches IP ranges from Azure by first navigating the download page to find the actual JSON file URL.
    
        Args:
            url (str): The URL to the download page.

        Returns:
            ipv4prefixes (set): A set of IPv4 prefixes.
            ipv6prefixes (set): A set of IPv6 prefixes.
    """
    download_page: str = requests.get(url, timeout=10).text
    json_url = re.search(r"https://download.microsoft.com/download/.*?\.json", download_page)
    if json_url:
        response = requests.get(json_url.group(), timeout=10).json()
        ipv4prefixes, ipv6prefixes = set(), set()
        for value in response.get("values", []):
            for ip_range in value.get("properties", {}).get("addressPrefixes", []):
                try:
                    network = ip_network(ip_range)
                    if network.version == 4:
                        ipv4prefixes.add(network)
                    else:
                        ipv6prefixes.add(network)
                except ValueError:
                    continue
    return ipv4prefixes, ipv6prefixes


def fetch_gcp_ip_ranges(url: str):
    """
    Fetches IP ranges from GCP.

        Args:
            url (str): The URL to the JSON file containing the IP ranges.
        
        Returns:
            ipv4prefixes (set): A set of IPv4 prefixes.
            ipv6prefixes (set): A set of IPv6 prefixes.
        
    """
    response = requests.get(url, timeout=10).json()
    ipv4prefixes = {ip_network(prefix["ipv4Prefix"]) for prefix in response.get("prefixes", []) if "ipv4Prefix" in prefix}
    ipv6prefixes = {ip_network(prefix["ipv6Prefix"]) for prefix in response.get("prefixes", []) if "ipv6Prefix" in prefix}
    return ipv4prefixes, ipv6prefixes

def fetch_digital_ocean_ip_ranges(url: str):
    """
    Fetches IP ranges from DigitalOcean.

        Args:
            url (str): The URL to the CSV file containing the IP ranges.

        Returns:
            ipv4prefixes (set): A set of IPv4 prefixes.
            ipv6prefixes (set): A set of IPv6 prefixes.
    """
    response: list = requests.get(url, timeout=10).text.splitlines()
    ipv4prefixes, ipv6prefixes = set(), set()
    for line in response:
        parts: list = line.split(",")
        try:
            network = ip_network(parts[0])
            if network.version == 4:
                ipv4prefixes.add(network)
            else:
                ipv6prefixes.add(network)
        except ValueError:
            continue
    return ipv4prefixes, ipv6prefixes


def fetch_oracle_ip_ranges(url: str):
    """
    Fetches IP ranges from Oracle.
    
        Args:
            url (str): The URL to the JSON file containing the IP ranges.
        
        Returns:
            ipv4prefixes (set): A set of IPv4 prefixes.
            ipv6prefixes (set): A set of IPv6 prefixes.
    """
    response = requests.get(url, timeout=10).json()
    ipv4prefixes, ipv6prefixes = set(), set()
    for region in response.get("regions", []):
        for cidr in region.get("cidrs", []):
            try:
                network = ip_network(cidr["cidr"])
                if network.version == 4:
                    ipv4prefixes.add(network)
                else:
                    ipv6prefixes.add(network)
            except ValueError:
                continue
    return ipv4prefixes, ipv6prefixes


def fetch_linode_ip_ranges(url: str):
    """
    Fetches IP ranges from Linode.
    
        Args:
            url (str): The URL to the JSON file containing the IP ranges.

        Returns:
            ipv4prefixes (set): A set of IPv4 prefixes.
            ipv6prefixes (set): A set of IPv6 prefixes.
    
    """
    response: list = requests.get(url, timeout=10).text.splitlines()
    ipv4prefixes, ipv6prefixes = set(), set()
    for line in response:
        if line.startswith("#"):
            continue
        try:
            network = ip_network(line.split(",")[0])
            if network.version == 4:
                ipv4prefixes.add(network)


def write_networks(networks, network_file) -> None:

    with open(network_file, "w", encoding='utf-8') as open_file:
        try:
            json.dump(networks, open_file, indent=4, sort_keys=True)
        except json.JSONDecodeError:
            pass

    open_file.close()


# ipv4prefixes = set()
# ipv6prefixes = set()

# aws4, aws6 = aws()
# azure4, azure6 = azure()
# gpc4, gpc6 = gpc()
# ocean4, ocean6 = ocean()
# oracle4, oracle6 = oracle()
# linode4, linode6 = linode()

# ipv4prefixes.update(aws4)
# ipv4prefixes.update(azure4)
# ipv4prefixes.update(gpc4)
# ipv4prefixes.update(ocean4)
# ipv4prefixes.update(oracle4)

# ipv6prefixes.update(aws6)
# ipv6prefixes.update(azure6)
# ipv6prefixes.update(gpc6)
# ipv6prefixes.update(ocean6)
# ipv6prefixes.update(oracle6)

# ipv4nets = list(collapse_addresses(ipv4prefixes))
# ipv6nets = list(collapse_addresses(ipv6prefixes))

# ipv4nets = [str(i) for i in ipv4nets]
# ipv6nets = [str(i) for i in ipv6nets]

# write_networks(ipv4nets, IPV4_FILE)
# write_networks(ipv6nets, IPV6_FILE)
