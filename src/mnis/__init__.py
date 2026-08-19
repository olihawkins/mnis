"""mnis: A package for downloading data from the Parliamentary Members Name
Information Service

The mnis package provides a suite of functions for downloading data from
the data platform for the UK Parliament.
"""

from mnis.contacts_lords import fetch_lords_blogs
from mnis.contacts_lords import fetch_lords_email_addresses
from mnis.contacts_lords import fetch_lords_facebook
from mnis.contacts_lords import fetch_lords_fax_numbers
from mnis.contacts_lords import fetch_lords_instagram
from mnis.contacts_lords import fetch_lords_office_addresses
from mnis.contacts_lords import fetch_lords_phone_numbers
from mnis.contacts_lords import fetch_lords_twitter
from mnis.contacts_lords import fetch_lords_websites
from mnis.contacts_mps import fetch_mps_blogs
from mnis.contacts_mps import fetch_mps_email_addresses
from mnis.contacts_mps import fetch_mps_facebook
from mnis.contacts_mps import fetch_mps_fax_numbers
from mnis.contacts_mps import fetch_mps_instagram
from mnis.contacts_mps import fetch_mps_office_addresses
from mnis.contacts_mps import fetch_mps_phone_numbers
from mnis.contacts_mps import fetch_mps_twitter
from mnis.contacts_mps import fetch_mps_websites
from mnis.elections import get_general_elections
from mnis.elections import get_general_elections_list
from mnis.lords import fetch_lords
from mnis.lords import fetch_lords_addresses
from mnis.lords import fetch_lords_contested_elections
from mnis.lords import fetch_lords_government_roles
from mnis.lords import fetch_lords_maiden_speeches
from mnis.lords import fetch_lords_memberships
from mnis.lords import fetch_lords_opposition_roles
from mnis.lords import fetch_lords_other_parliaments
from mnis.lords import fetch_lords_parliamentary_roles
from mnis.lords import fetch_lords_party_memberships
from mnis.mps import fetch_commons_memberships
from mnis.mps import fetch_mps
from mnis.mps import fetch_mps_addresses
from mnis.mps import fetch_mps_contested_elections
from mnis.mps import fetch_mps_government_roles
from mnis.mps import fetch_mps_maiden_speeches
from mnis.mps import fetch_mps_opposition_roles
from mnis.mps import fetch_mps_other_parliaments
from mnis.mps import fetch_mps_parliamentary_roles
from mnis.mps import fetch_mps_party_memberships

__all__ = [
    "fetch_commons_memberships",
    "fetch_lords",
    "fetch_lords_addresses",
    "fetch_lords_blogs",
    "fetch_lords_contested_elections",
    "fetch_lords_email_addresses",
    "fetch_lords_facebook",
    "fetch_lords_fax_numbers",
    "fetch_lords_government_roles",
    "fetch_lords_instagram",
    "fetch_lords_maiden_speeches",
    "fetch_lords_memberships",
    "fetch_lords_office_addresses",
    "fetch_lords_opposition_roles",
    "fetch_lords_other_parliaments",
    "fetch_lords_parliamentary_roles",
    "fetch_lords_party_memberships",
    "fetch_lords_phone_numbers",
    "fetch_lords_twitter",
    "fetch_lords_websites",
    "fetch_mps",
    "fetch_mps_addresses",
    "fetch_mps_blogs",
    "fetch_mps_contested_elections",
    "fetch_mps_email_addresses",
    "fetch_mps_facebook",
    "fetch_mps_fax_numbers",
    "fetch_mps_government_roles",
    "fetch_mps_instagram",
    "fetch_mps_maiden_speeches",
    "fetch_mps_office_addresses",
    "fetch_mps_opposition_roles",
    "fetch_mps_other_parliaments",
    "fetch_mps_parliamentary_roles",
    "fetch_mps_party_memberships",
    "fetch_mps_phone_numbers",
    "fetch_mps_twitter",
    "fetch_mps_websites",
    "get_general_elections",
    "get_general_elections_list",
]
