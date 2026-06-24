import csv
import logging
from io import StringIO
import requests
from google.auth.transport.requests import AuthorizedSession
from google.oauth2 import service_account

"""
Prerequisites:
-------------
pip install requests google-auth

Before running, ensure you have set the configuration variables below.
"""

# ==========================================
# USER CONFIGURATION
# ==========================================

# 1. Edit this list to include the subfolders you want to import from GitHub.
# Each subfolder must contain a 'raw.csv' file.
SUBFOLDERS_TO_IMPORT = [
    "Subfolder1",
    "Subfolder2",
    # Add more subfolders here
]

# 2. GitHub Configuration
# The base URL pointing to the raw contents of your GitHub repository branch.
# If the branch name is 'master' instead of 'main', change it here.
GITHUB_REPO_RAW_BASE_URL = "https://raw.githubusercontent.com/1NobleCyber/ThreatFeed/main"

# If your GitHub repository is private, you will need a Personal Access Token (PAT).
# Provide it here. Leave empty "" if the repository is public.
GITHUB_PAT = ""

# 3. Chronicle API Configuration
# Path to your Google Cloud service account JSON credentials file
SERVICE_ACCOUNT_FILE = 'path/to/your-service-account.json'

# Your Chronicle API Region URL (e.g., "https://backstory.googleapis.com" or "https://europe-west2-backstory.googleapis.com")
CHRONICLE_API_BASE_URL = "https://backstory.googleapis.com"

# The Google Cloud Project ID, Location, and Instance ID for the V2 API
# You can find this in your Chronicle console or documentation.
# Format: projects/{project}/locations/{location}/instances/{instance}
CHRONICLE_INSTANCE_PREFIX = "projects/YOUR_PROJECT_ID/locations/YOUR_LOCATION/instances/YOUR_INSTANCE_ID"

# ==========================================

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_chronicle_session():
    """Authenticates and returns an AuthorizedSession for Chronicle API."""
    scopes = ['https://www.googleapis.com/auth/chronicle-backstory']
    try:
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=scopes)
        return AuthorizedSession(credentials)
    except Exception as e:
        logger.error(f"Failed to load credentials from {SERVICE_ACCOUNT_FILE}: {e}")
        return None

def fetch_github_csv(subfolder):
    """Fetches the raw.csv file from a specific subfolder in the GitHub repository."""
    url = f"{GITHUB_REPO_RAW_BASE_URL}/{subfolder}/raw.csv"
    logger.info(f"Fetching data from {url}")
    
    headers = {}
    if GITHUB_PAT:
        headers['Authorization'] = f"token {GITHUB_PAT}"
        
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        items = []
        # Parse CSV file
        csv_reader = csv.reader(StringIO(response.text))
        for row in csv_reader:
            if row:
                # Assuming the indicator is in the first column of the CSV.
                # If your CSV format is different (e.g., has headers), you may need to adjust this logic.
                item = row[0].strip()
                if item:
                    items.append(item)
                    
        logger.info(f"Successfully pulled {len(items)} items from {subfolder}/raw.csv")
        return items
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch data for {subfolder} from {url}: {e}")
        return []

def update_chronicle_reference_list(session, list_name, items):
    """Creates or updates a reference list in Google Chronicle with the provided items."""
    # List names in the API typically match the subfolder name, but sanitized to alphanumeric + underscores
    sanitized_name = "".join([c if c.isalnum() else "_" for c in list_name])
    full_list_path = f"{CHRONICLE_INSTANCE_PREFIX}/referenceLists/{sanitized_name}"
    
    url = f"{CHRONICLE_API_BASE_URL}/v2/lists"
    
    payload = {
        "name": full_list_path,
        "description": f"Imported from GitHub ThreatFeed: {list_name}",
        "lines": items,
        "content_type": "STRING" # Adjust to REGEX, CIDR, etc. based on your data if necessary
    }
    
    logger.info(f"Uploading {len(items)} items to Chronicle Reference List '{sanitized_name}'...")
    
    # Try POST first to create the list
    response = session.request("POST", url, json=payload)
    
    if response.status_code == 200:
        logger.info(f"Successfully created reference list '{sanitized_name}'.")
    elif response.status_code == 409:
        # Conflict: List already exists. Use PATCH to update it.
        logger.info(f"List '{sanitized_name}' already exists. Attempting to update via PATCH...")
        patch_url = f"{CHRONICLE_API_BASE_URL}/v2/{full_list_path}?updateMask=lines"
        response = session.request("PATCH", patch_url, json=payload)
        
        if response.status_code == 200:
            logger.info(f"Successfully updated existing reference list '{sanitized_name}'.")
        else:
            logger.error(f"Failed to update reference list '{sanitized_name}'. Status: {response.status_code}, Response: {response.text}")
    else:
        logger.error(f"Failed to create reference list '{sanitized_name}'. Status: {response.status_code}, Response: {response.text}")

def main():
    session = get_chronicle_session()
    if not session:
        logger.error("Could not authenticate with Google Chronicle. Please check your SERVICE_ACCOUNT_FILE path.")
        return

    for subfolder in SUBFOLDERS_TO_IMPORT:
        items = fetch_github_csv(subfolder)
        if items:
            update_chronicle_reference_list(session, subfolder, items)
        else:
            logger.warning(f"No items to import for {subfolder}, skipping Chronicle update.")

if __name__ == "__main__":
    main()
