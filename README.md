# ThreatFeed

ThreatFeed is a repository designed to host, manage, and integrate external threat intelligence feeds into Google Chronicle (Google SecOps) and others. It provides an automated workflow to pull raw indicator lists from this repository and populate them as Reference Lists within Chronicle, along with a corresponding YARA-L rule to immediately begin detecting malicious activity based on those feeds.

## Repository Contents

- **`import_threat_feeds_to_chronicle.py`**: A Python automation script that authenticates with the Google Chronicle API using a Google Cloud service account. It fetches `raw.csv` files from specified subfolders within this GitHub repository (such as `Afraid_org`) and creates or updates Reference Lists in your Chronicle instance.
- **`threat_intel_domain_blocklist.yaral`**: A Chronicle YARA-L detection rule that monitors network telemetry (DNS lookups, HTTP requests, and network connections). It checks the destination hostnames against your imported Reference Lists (e.g., `%Afraid_org` or `%malicious_threat_intel_domains`) and triggers a High-severity alert when a match occurs.
- **`Afraid_org/`**: An example threat feed directory containing:
  - `raw.csv`: The raw list of malicious domains/indicators to be ingested by the Python script into Chronicle.
  - `iBoss-Afraid_org.csv`: A specifically formatted version of the feed intended for use with iBoss Secure Web Gateways.

## Getting Started

### 1. Configure the Import Script
Before running the import script, you must edit `import_threat_feeds_to_chronicle.py` to configure your environment:
- Add the target subfolders containing `raw.csv` files to `SUBFOLDERS_TO_IMPORT` (e.g., `"Afraid_org"`).
- Specify the path to your Google Cloud service account credentials JSON in `SERVICE_ACCOUNT_FILE`.
- Set your `CHRONICLE_API_BASE_URL` and `CHRONICLE_INSTANCE_PREFIX` based on your Chronicle environment.
- (Optional) Provide a `GITHUB_PAT` if your repository is private.

### 2. Install Prerequisites
Ensure you have the required Python libraries installed:
```bash
pip install requests google-auth
