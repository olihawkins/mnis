"""Build the record of the columns each function returns.

The package exists to return dataframes with a known shape, so the shape of
every dataframe it returns is recorded here and checked by the tests. A
change to the columns or their types is then something a developer has to
make deliberately, by rebuilding this file, rather than something which can
happen without anyone noticing.

The schemas are built from the saved payloads, so this does not read from
the live API. Run this module after making a deliberate change to what a
function returns:

    python tests/fixtures/build_schemas.py

Review the resulting diff. If it holds a change you did not intend, that
change is a bug.
"""

# Imports ---------------------------------------------------------------------

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parents[2] / "src"))
sys.path.insert(0, str(pathlib.Path(__file__).parents[1]))

from conftest import load_payload

import mnis

from mnis import raw_lords
from mnis import raw_mps
from mnis import utility

# Constants -------------------------------------------------------------------

SCHEMAS = pathlib.Path(__file__).parent / "schemas.json"

NOT_DATA_FUNCTIONS = ["clear_cache", "get_timeout", "set_timeout"]


# Build schemas ---------------------------------------------------------------


def build_schemas() -> dict:
    """Return the columns and types each function returns."""
    utility.fetch_query_data = load_payload
    schemas = {}

    for name in mnis.__all__:
        if name in NOT_DATA_FUNCTIONS:
            continue
        mnis.clear_cache()
        result = getattr(mnis, name)()
        if not hasattr(result, "schema"):
            continue
        schemas[name] = [
            [column, str(dtype)] for column, dtype in result.schema.items()]

    for module in (raw_mps, raw_lords):
        for name in dir(module):
            if not name.endswith("_raw"):
                continue
            mnis.clear_cache()
            result = getattr(module, name)()
            schemas[name] = [
                [column, str(dtype)]
                for column, dtype in result.schema.items()]

    return dict(sorted(schemas.items()))


if __name__ == "__main__":
    schemas = build_schemas()
    SCHEMAS.write_text(json.dumps(schemas, indent=1) + "\n")
    print(f"recorded the schemas of {len(schemas)} datasets")
