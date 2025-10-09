[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/auspex-labs/cloud-ipaddresses.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/auspex-labs/cloud-ipaddresses/context:python)
[![Total alerts](https://img.shields.io/lgtm/alerts/g/auspex-labs/cloud-ipaddresses.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/auspex-labs/cloud-ipaddresses/alerts/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

# Cloud IP Addresses

A Python utility that collects and aggregates advertised IP address ranges from major cloud providers. The tool fetches current IP ranges, collapses overlapping networks, and outputs separate JSON files for IPv4 and IPv6 addresses.

## Features

- **Multi-Provider Support**: Fetches IP ranges from AWS, Azure, GCP, DigitalOcean, Oracle Cloud, and Linode
- **Automatic Retry Logic**: Exponential backoff retry mechanism for handling transient network failures
- **Graceful Degradation**: Continues execution even if individual providers fail
- **Network Optimization**: Automatically collapses overlapping CIDR ranges
- **Comprehensive Error Handling**: Robust exception handling with detailed error messages
- **Type Safety**: Full type annotations for better code reliability

## Supported Cloud Providers

| Provider | IPv4 Support | IPv6 Support | Source |
|----------|--------------|--------------|--------|
| AWS | ✓ | ✓ | Official JSON feed |
| Microsoft Azure | ✓ | ✓ | Official download page |
| Google Cloud Platform | ✓ | ✓ | Official JSON feed |
| DigitalOcean | ✓ | ✓ | GeoIP CSV feed |
| Oracle Cloud | ✓ | ✓ | Official JSON feed |
| Linode | ✓ | ✓ | GeoIP feed |

## Installation

### Requirements

- Python 3.12 or higher
- pip (Python package manager)

### Install Dependencies

```bash
pip install -r requirements.txt
```

The following packages will be installed:
- `requests` - HTTP library for API calls
- `certifi` - SSL certificate validation
- `urllib3` - HTTP client
- `charset-normalizer` - Character encoding detection
- `idna` - Internationalized domain names

## Usage

### Basic Usage

Run the script to fetch and aggregate IP ranges from all providers:

```bash
python3 cloud_addresses.py
```

### Output

The script generates two JSON files:

- `cloud_networks_4.json` - Aggregated IPv4 CIDR ranges
- `cloud_networks_6.json` - Aggregated IPv6 CIDR ranges

### Example Output

```
✓ AWS: 7031 IPv4, 2226 IPv6
✓ Azure: 37943 IPv4, 13700 IPv6
✓ GCP: 796 IPv4, 47 IPv6
✓ DigitalOcean: 1039 IPv4, 145 IPv6
✓ Oracle: 982 IPv4, 0 IPv6
✓ Linode: 4587 IPv4, 94 IPv6

Total: 5008 IPv4, 2943 IPv6
Success rate: 6/6
```

### Output File Format

JSON arrays containing CIDR notation strings:

```json
[
    "1.178.1.0/24",
    "3.2.34.0/26",
    "3.5.140.0/22",
    ...
]
```

## Configuration

### Retry Settings

Modify retry behavior by adjusting constants in `cloud_addresses.py`:

```python
MAX_RETRIES = 3              # Number of retry attempts
RETRY_BACKOFF_BASE = 2       # Exponential backoff base (seconds)
```

Retry delays: 1s, 2s, 4s (exponential backoff)

### Output Files

Customize output file names:

```python
IPV4_FILE = "cloud_networks_4.json"
IPV6_FILE = "cloud_networks_6.json"
```

## Use Cases

- **Security**: Identify traffic originating from cloud providers
- **Firewall Rules**: Create allowlists or blocklists for cloud infrastructure
- **Network Monitoring**: Track and analyze cloud provider IP usage
- **Compliance**: Maintain updated records of cloud service IP ranges
- **Threat Intelligence**: Correlate IP addresses with cloud infrastructure

## Error Handling

The tool implements graceful degradation:

- Individual provider failures don't stop execution
- Failed providers are tracked and reported
- Successful providers contribute to the final output
- Detailed error messages for troubleshooting

## Development

### Code Style

This project uses:
- `black` for code formatting (line length: 132)
- `ruff` for linting
- Google Python Style Guide for docstrings

### Running Linters

```bash
ruff check . --fix
black -l 132 -t py312 .
```

### CI/CD

GitHub Actions automatically runs linting on all pull requests and commits to the main branch.

## License

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

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Acknowledgments

This tool aggregates publicly available IP range data from cloud providers. All data sources are official or publicly documented endpoints.