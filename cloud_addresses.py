"""Cloud IP Address Aggregator.

This module collects and aggregates advertised IP address ranges from major
cloud providers (AWS, Azure, GCP, DigitalOcean, Oracle, Linode) and outputs
them as separate JSON files for IPv4 and IPv6 addresses.

Copyright 2024 - 2025 Auspex Labs Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import json
import re
import time
from ipaddress import ip_network, collapse_addresses
import requests

# User Agent String for Microsoft Azure (required for download page access).
AZURE_HEADER = {
    "User-Agent": "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0"
}

# Cloud providers' IP ranges sources.
AWS_SOURCE = "https://ip-ranges.amazonaws.com/ip-ranges.json"
AZURE_DOWNLOAD_PAGE = "https://www.microsoft.com/en-us/download/confirmation.aspx?id=56519"
GPC_SOURCE = "https://www.gstatic.com/ipranges/cloud.json"
OCEAN_SOURCE = "https://www.digitalocean.com/geo/google.csv"
ORACLE_SOURCE = "https://docs.oracle.com/iaas/tools/public_ip_ranges.json"
LINODE_SOURCE = "https://geoip.linode.com/"

# Output files for IPv4 and IPv6 network ranges.
IPV4_FILE = "cloud_networks_4.json"
IPV6_FILE = "cloud_networks_6.json"

# Retry configuration for HTTP requests.
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2  # Exponential backoff base in seconds.


def retry_request(url: str, headers = None, timeout: int = 10) -> requests.Response:
    """Makes an HTTP GET request with exponential backoff retry logic.

    Args:
        url: The URL to fetch.
        headers: Optional HTTP headers dictionary.
        timeout: Request timeout in seconds.

    Returns:
        The requests.Response object.

    Raises:
        requests.RequestException: If all retry attempts fail.
    """
    last_exception = None

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.RequestException as err:
            last_exception = err
            if attempt < MAX_RETRIES - 1:
                wait_time = RETRY_BACKOFF_BASE ** attempt
                print(f"Retry {attempt + 1}/{MAX_RETRIES} for {url} after {wait_time}s: {err}")
                time.sleep(wait_time)
            else:
                print(f"All {MAX_RETRIES} retry attempts failed for {url}")

    raise last_exception # type: ignore


def fetch_aws_ip_ranges(url: str) -> tuple:
    """Fetches IP ranges from AWS.

    Args:
        url: The URL to the JSON file containing the IP ranges.

    Returns:
        A tuple containing two sets: (ipv4_prefixes, ipv6_prefixes).
    """
    try:
        response = retry_request(url).json()
        ipv4prefixes: set = {ip_network(prefix["ip_prefix"]) for prefix in response.get("prefixes", [])}
        ipv6prefixes: set = {ip_network(prefix["ipv6_prefix"]) for prefix in response.get("ipv6_prefixes", [])}
        return ipv4prefixes, ipv6prefixes
    except requests.RequestException as err:
        print(f"Error fetching AWS IP ranges: {err}")
        return set(), set()


def fetch_azure_ip_ranges(url: str) -> tuple:
    """Fetches IP ranges from Azure.

    Navigates the download page to find the actual JSON file URL, then
    fetches and parses the Azure IP ranges.

    Args:
        url: The URL to the Azure download page.

    Returns:
        A tuple containing two sets: (ipv4_prefixes, ipv6_prefixes).
    """
    ipv4prefixes, ipv6prefixes = set(), set()

    try:
        download_page: str = retry_request(url, headers=AZURE_HEADER).text
    except requests.RequestException as err:
        print(f"Error fetching Azure download page: {err}")
        return ipv4prefixes, ipv6prefixes

    json_url = re.search(r"https://download.microsoft.com/download/.*?\.json", download_page)
    if json_url:
        try:
            response = retry_request(json_url.group()).json()
        except requests.RequestException as err:
            print(f"Error fetching Azure IP ranges: {err}")
            return ipv4prefixes, ipv6prefixes
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


def fetch_gcp_ip_ranges(url: str) -> tuple:
    """Fetches IP ranges from GCP.

    Args:
        url: The URL to the JSON file containing the IP ranges.

    Returns:
        A tuple containing two sets: (ipv4_prefixes, ipv6_prefixes).
    """
    try:
        response = retry_request(url).json()
        ipv4prefixes = {ip_network(prefix["ipv4Prefix"]) for prefix in response.get("prefixes", []) if "ipv4Prefix" in prefix}
        ipv6prefixes = {ip_network(prefix["ipv6Prefix"]) for prefix in response.get("prefixes", []) if "ipv6Prefix" in prefix}
        return ipv4prefixes, ipv6prefixes
    except requests.RequestException as err:
        print(f"Error fetching GCP IP ranges: {err}")
        return set(), set()


def fetch_digital_ocean_ip_ranges(url: str) -> tuple:
    """Fetches IP ranges from DigitalOcean.

    Args:
        url: The URL to the CSV file containing the IP ranges.

    Returns:
        A tuple containing two sets: (ipv4_prefixes, ipv6_prefixes).
    """

    ipv4prefixes, ipv6prefixes = set(), set()

    try:
        response: list = retry_request(url).text.splitlines()
    except requests.RequestException as err:
        print(f"Error fetching DigitalOcean IP ranges: {err}")
        return ipv4prefixes, ipv6prefixes

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


def fetch_oracle_ip_ranges(url: str) -> tuple:
    """Fetches IP ranges from Oracle.

    Args:
        url: The URL to the JSON file containing the IP ranges.

    Returns:
        A tuple containing two sets: (ipv4_prefixes, ipv6_prefixes).
    """

    ipv4prefixes, ipv6prefixes = set(), set()

    try:
        response = retry_request(url).json()
    except requests.RequestException as err:
        print(f"Error fetching Oracle IP ranges: {err}")
        return ipv4prefixes, ipv6prefixes

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


def linode_ip_ranges(url: str) -> tuple:
    """Fetches IP ranges from Linode.

    Args:
        url: The URL to the file containing the IP ranges.

    Returns:
        A tuple containing two sets: (ipv4_prefixes, ipv6_prefixes).
    """

    ipv4prefixes, ipv6prefixes = set(), set()

    try:
        response: str = retry_request(url).text
    except requests.RequestException as err:
        print(f"Error fetching Linode IP ranges: {err}")
        return ipv4prefixes, ipv6prefixes

    for line in response.splitlines():
        if not line.startswith("#"):
            try:
                network = ip_network(line.split(",")[0], strict=False)
                if network.version == 4:
                    ipv4prefixes.add(network)
                elif network.version == 6:
                    ipv6prefixes.add(network)
            except ValueError:
                continue
    return ipv4prefixes, ipv6prefixes


def write_networks(networks: list, network_file: str) -> None:
    """Writes network addresses to a file in JSON format.

    Args:
        networks: A list of network addresses as strings.
        network_file: The name of the file to write to.
    """
    with open(network_file, "w", encoding="utf-8") as file:
        json.dump(networks, file, indent=4)


def main() -> None:
    """Main function to fetch, aggregate, and write cloud provider IP ranges.

    Fetches IP ranges from all supported cloud providers, aggregates and
    collapses overlapping ranges, then writes them to separate JSON files
    for IPv4 and IPv6 addresses.
    """
    providers = []
    failed_providers = []

    # Fetch from all providers with graceful degradation.
    aws4, aws6 = fetch_aws_ip_ranges(AWS_SOURCE)
    providers.append(("AWS", len(aws4), len(aws6)))
    if len(aws4) == 0 and len(aws6) == 0:
        failed_providers.append("AWS")

    azure4, azure6 = fetch_azure_ip_ranges(AZURE_DOWNLOAD_PAGE)
    providers.append(("Azure", len(azure4), len(azure6)))
    if len(azure4) == 0 and len(azure6) == 0:
        failed_providers.append("Azure")

    gcp4, gcp6 = fetch_gcp_ip_ranges(GPC_SOURCE)
    providers.append(("GCP", len(gcp4), len(gcp6)))
    if len(gcp4) == 0 and len(gcp6) == 0:
        failed_providers.append("GCP")

    ocean4, ocean6 = fetch_digital_ocean_ip_ranges(OCEAN_SOURCE)
    providers.append(("DigitalOcean", len(ocean4), len(ocean6)))
    if len(ocean4) == 0 and len(ocean6) == 0:
        failed_providers.append("DigitalOcean")

    oracle4, oracle6 = fetch_oracle_ip_ranges(ORACLE_SOURCE)
    providers.append(("Oracle", len(oracle4), len(oracle6)))
    if len(oracle4) == 0 and len(oracle6) == 0:
        failed_providers.append("Oracle")

    linode4, linode6 = linode_ip_ranges(LINODE_SOURCE)
    providers.append(("Linode", len(linode4), len(linode6)))
    if len(linode4) == 0 and len(linode6) == 0:
        failed_providers.append("Linode")

    # Print individual provider results.
    for name, ipv4_count, ipv6_count in providers:
        status = "✓" if name not in failed_providers else "✗"
        print(f"{status} {name}: {ipv4_count} IPv4, {ipv6_count} IPv6")

    # Aggregate and collapse ranges.
    ipv4p = aws4.union(azure4, gcp4, ocean4, oracle4, linode4)
    ipv6p = aws6.union(azure6, gcp6, ocean6, oracle6, linode6)

    ipv4nets = list(collapse_addresses(ipv4p))  # type: ignore
    ipv6nets = list(collapse_addresses(ipv6p))  # type: ignore

    ipv4nets = [str(i) for i in ipv4nets]
    ipv6nets = [str(i) for i in ipv6nets]

    # Print summary.
    print(f"\nTotal: {len(ipv4nets)} IPv4, {len(ipv6nets)} IPv6")
    if failed_providers:
        print(f"Failed providers: {', '.join(failed_providers)}")
    print(f"Success rate: {len(providers) - len(failed_providers)}/{len(providers)}")

    write_networks(ipv4nets, IPV4_FILE)
    write_networks(ipv6nets, IPV6_FILE)


if __name__ == "__main__":
    main()
