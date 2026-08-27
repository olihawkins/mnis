"""Package constants"""

# API url ---------------------------------------------------------------------

MNIS_API = (
    "http://data.parliament.uk/membersdataplatform/services/mnis/"
    "members/query/"
)

# House within Parliament -----------------------------------------------------

HOUSE_COMMONS = "Commons"
HOUSE_LORDS = "Lords"

# XML missing data string -----------------------------------------------------

MISSING_VALUE_STRING = (
    'list(`@xsi:nil` = "true", '
    '`@xmlns:xsi` = "http://www.w3.org/2001/XMLSchema-instance")'
)

# Cache constants -------------------------------------------------------------

CACHE_MPS_RAW = "mps"
CACHE_COMMONS_MEMBERSHIPS_RAW = "commons_memberships"
CACHE_COMMONS_PARTY_MEMBERSHIPS_RAW = "commons_party_memberships"
CACHE_MPS_GOVERNMENT_ROLES_RAW = "mps_government_roles"
CACHE_MPS_OPPOSITION_ROLES_RAW = "mps_opposition_roles"
CACHE_MPS_PARLIAMENTARY_ROLES_RAW = "mps_parliamentary_roles"
CACHE_MPS_MAIDEN_SPEECHES_RAW = "mps_maiden_speeches"
CACHE_MPS_OTHER_PARLIAMENTS_RAW = "mps_other_parliaments"
CACHE_MPS_CONTESTED_ELECTIONS_RAW = "mps_contested_elections"
CACHE_MPS_ADDRESSES_RAW = "mps_addresses"

CACHE_LORDS_RAW = "lords"
CACHE_LORDS_MEMBERSHIPS_RAW = "lords_memberships"
CACHE_LORDS_PARTY_MEMBERSHIPS_RAW = "lords_party_memberships"
CACHE_LORDS_GOVERNMENT_ROLES_RAW = "lords_government_roles"
CACHE_LORDS_OPPOSITION_ROLES_RAW = "lords_opposition_roles"
CACHE_LORDS_PARLIAMENTARY_ROLES_RAW = "lords_parliamentary_roles"
CACHE_LORDS_MAIDEN_SPEECHES_RAW = "lords_maiden_speeches"
CACHE_LORDS_OTHER_PARLIAMENTS_RAW = "lords_other_parliaments"
CACHE_LORDS_CONTESTED_ELECTIONS_RAW = "lords_contested_elections"
CACHE_LORDS_ADDRESSES_RAW = "lords_addresses"

# Column names ----------------------------------------------------------------

# The columns of each dataset are specified explicitly rather than inferred
# from the data returned by the API. Inferring them means that a dataset is
# missing a column whenever the field behind it is absent from every record
# in a response, and that no columns can be determined at all when a
# response is empty. Note that the columns of the data outputs handled by
# extract_data_output are named with the field names used by MNIS, as the
# functions that use them rename the columns themselves.

COLUMNS_MPS = [
    "mnis_id",
    "given_name",
    "family_name",
    "display_name",
    "full_title",
    "current_status",
    "current_status_reason",
    "gender",
    "date_of_death"]

COLUMNS_LORDS = [
    "mnis_id",
    "given_name",
    "family_name",
    "display_name",
    "full_title",
    "lord_type",
    "current_status",
    "current_status_reason",
    "gender",
    "date_of_death"]

COLUMNS_COMMONS_MEMBERSHIPS = [
    "constituency_mnis_id",
    "constituency_name",
    "seat_incumbency_start_date",
    "seat_incumbency_end_date",
    "mnis_id"]

COLUMNS_LORDS_MEMBERSHIPS = [
    "house_name",
    "seat_incumbency_start_date",
    "seat_incumbency_end_date",
    "mnis_id"]

COLUMNS_PARTY_MEMBERSHIPS = [
    "party_mnis_id",
    "party_name",
    "party_membership_start_date",
    "party_membership_end_date",
    "mnis_id"]

COLUMNS_OTHER_PARLIAMENTS = [
    "other_parliaments_mnis_id",
    "other_parliaments_name",
    "other_parliaments_incumbency_start_date",
    "other_parliaments_incumbency_end_date",
    "mnis_id"]

COLUMNS_CONTESTED_ELECTIONS = [
    "contested_election_mnis_id",
    "contested_election_name",
    "contested_election_date",
    "contested_election_type",
    "contested_election_constituency",
    "mnis_id"]

COLUMNS_POSTS = [
    "mnis_id",
    "@Id",
    "Name",
    "StartDate",
    "EndDate",
    "IsUnpaid"]

COLUMNS_MAIDEN_SPEECHES = [
    "mnis_id",
    "House",
    "SpeechDate",
    "Hansard",
    "Subject"]

COLUMNS_ADDRESSES = [
    "mnis_id",
    "@Type_Id",
    "Type",
    "IsPreferred",
    "IsPhysical",
    "Note",
    "Address1",
    "Address2",
    "Address3",
    "Address4",
    "Address5",
    "Postcode",
    "Phone",
    "Fax",
    "Email",
    "OtherAddress"]

# API settings ----------------------------------------------------------------

API_PAUSE_TIME = 0.5

# The default number of seconds to wait for a response from MNIS. This is the
# starting value of the timeout setting, which can be changed with set_timeout.
API_TIMEOUT = 20

# A request that fails with a transient error is retried this many times,
# waiting for the given number of seconds before each retry in turn. Requests
# which fail for any other reason are not retried, as repeating them cannot
# change the outcome.
API_RETRIES = 5
API_RETRY_BACKOFF = [1, 2, 4, 8, 16]
API_RETRY_STATUSES = [429, 500, 502, 503, 504]
