import os 
import requests
import json
import csv
import sys


def get_releases():
    """
    Fetch all release data from GitHub for dbt-core, returning a list of dictionaries.
    Handles pagination to get all releases, not just the first 30.
    """
    url = (
        "https://api.github.com/repos/"+
        f"{os.getenv('REPO_COMPANY')}"+ "/"+
        f"{os.getenv('REPO_NAME')}"+"/releases"
    )
    
    all_releases = []
    while url:
        response = requests.get(url)
        response.raise_for_status()
        all_releases.extend(response.json())
        
        # Check for next page in Link header
        url = None
        if 'Link' in response.headers:
            links = requests.utils.parse_header_links(response.headers['Link'])
            for link in links:
                if link['rel'] == 'next':
                    url = link['url']
                    break
    
    return all_releases


def flatten_dict(d, parent_key=''):
    """
    Recursively flattens a nested dictionary using underscores, e.g.
      { "foo": { "bar": "value" } }
    becomes
      { "foo_bar": "value" }
    
    Lists are left unstructured.
    """
    items = {}
    for k, v in d.items():
        # Build new key (with underscore if there's already a parent_key)
        new_key = f"{parent_key}_{k}" if parent_key else k

        if isinstance(v, dict):
            # Recursively flatten nested dictionaries
            items.update(flatten_dict(v, new_key))
        elif isinstance(v, list):
            # Leave lists unstructured
            items[new_key] = v
        else:
            # String/number/boolean/etc. - just assign
            items[new_key] = v
    return items


def flatten_list_of_dicts(data):
    """
    Applies flatten_dict to each element in a list of dicts.
    Assumes 'data' is a list of JSON objects.
    """
    flattened_list = []
    for obj in data:
        flattened_list.append(flatten_dict(obj))
    return flattened_list

def write_csv_to_stdout(flattened_data):
    all_keys = set()
    for obj in flattened_data:
        all_keys.update(obj.keys())
    # Sort them so columns appear in a stable order
    all_keys = sorted(all_keys)
    
    # 4. Write out as CSV
    #    Use QUOTE_MINIMAL to avoid quoting everything, which sometimes confuses CSV readers.
    writer = csv.DictWriter(
        sys.stdout, 
        fieldnames=all_keys,  
    )
    writer.writeheader()
    writer.writerows(flattened_data)

if __name__ == '__main__':
    releases = get_releases()
    flattened_data = flatten_list_of_dicts(releases)
    write_csv_to_stdout(flattened_data)