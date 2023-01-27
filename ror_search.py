import os
import re
import sys
import csv
import urllib
import string
import itertools
import requests
from thefuzz import fuzz


def normalize_name(org_name):
    org_name = org_name.lower()
    org_name = re.sub(r'[^\w\s]', '', org_name)
    exclude = set(string.punctuation)
    org_name = ''.join(ch for ch in org_name if ch not in exclude)
    return org_name


def compare_names(first_name, second_name):
    mr_threshold = 90
    name_mr = fuzz.ratio(normalize_name(
        first_name), normalize_name(second_name))
    if name_mr > mr_threshold:
        return name_mr
    return ''


def ror_search(org_name):
    query_url = 'https://api.ror.org/organizations?query="' + \
        urllib.parse.quote_plus(org_name) + '"'
    ror_matches = []
    try:
        api_response = requests.get(query_url).json()
    except Exception:
        return [["API response error", "", "", "", "", ""]]
    if api_response['number_of_results'] != 0:
        results = api_response['items']
        for result in results:
            if 'organization' in result.keys():
                result = result['organization']
            ror_id = result['id']
            ror_name = result['name']
            city = ""
            if "city" in result["addresses"][0].keys():
                city = result["addresses"][0]["city"]
            country = result["country"]["country_name"]
            if city != "":
                address = city + ", " + country
            else:
                address = country
            aliases = result['aliases']
            labels = [label['label'] for label in result['labels']] if result['labels'] != [] else []
            name_mr = compare_names(ror_name, org_name)
            if name_mr:
                ror_matches.append([ror_id, ror_name, address, 'primary_name', name_mr])
            for alias in aliases:
                alias_mr = compare_names(ror_name, alias)
                if alias_mr:
                    ror_matches.append([ror_id, ror_name, address, 'alias', alias_mr])
            for label in labels:
                label_mr = compare_names(ror_name, label)
                if label_mr:
                    ror_matches.append([ror_id, ror_name, address, 'label', label_mr])
    ror_matches = list(ror_matches for ror_matches,
                       _ in itertools.groupby(ror_matches))
    if ror_matches == []:
        print("No matches in ROR found for", org_name)
    else:
        for match in ror_matches:
            print("Found match in ROR", match[0], "-", match[1])
    return ror_matches


def parse_and_search_member_file(f):
    header = ["member_id", "name", "location",
              "ror_id", "ror_name", "ror_address", "match_type", "name_mr"]
    outfile = "crossref_member_matches.csv"
    with open(outfile, 'w') as f_out:
        writer = csv.writer(f_out)
        writer.writerow(header)
    with open(f, encoding='utf-8-sig') as f_in:
        reader = csv.DictReader(f_in)
        for row in reader:
            member_id = row["member_id"]
            org_name = row["name"]
            print("Searching", member_id, "-", org_name, "...")
            ror_matches = ror_search(org_name)
            with open(outfile, 'a') as f_out:
                writer = csv.writer(f_out)
                if ror_matches == []:
                    writer.writerow(list(row.values()))
                else:
                    for match in ror_matches:
                        writer.writerow(list(row.values()) +  match)

if __name__ == '__main__':
    parse_and_search_member_file(sys.argv[1])










