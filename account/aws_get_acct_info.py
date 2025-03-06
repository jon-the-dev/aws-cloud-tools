"""
This script will pull the contact information and alternate contacts for an AWS account.
"""

import boto3
import logging

logger = logging.getLogger()
logging.basicConfig(level=logging.ERROR)

acct_client = boto3.client("account")

acct_data = {}

response = acct_client.get_contact_information()

acct_data["contact_info"] = {}
for k, v in response["ContactInformation"].items():
    acct_data["contact_info"][k] = v
    logging.debug("%s => %s", k, v)

types = ["BILLING", "OPERATIONS", "SECURITY"]
acct_data["alternate_contacts"] = {}
for t in types:
    try:
        response = acct_client.get_alternate_contact(AlternateContactType=t)
        logging.debug(response)
        acct_data["alternate_contacts"][t] = response
    except RuntimeWarning as e:
        logging.error("Error with pulling %s AlternateContact", t)
        logging.error(e)

print(acct_data)
