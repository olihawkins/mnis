"""Functions for combining related records in a dataframe"""

import polars as pl

# Combine party memberships ---------------------------------------------------


def combine_party_memberships(pm: pl.DataFrame) -> pl.DataFrame:
    """Combine consecutive records in a dataframe of party memberships.

    combine_party_memberships takes a dataframe of party memberships and
    combines historically consecutive memberships of the same party into a
    single continuous membership with the start date of the first membership
    and the end date of the last. Combining the memberships in this way
    means that party membership ids from the data platform are not included
    in the dataframe returned.

    :param pm: A dataframe containing party memberships as returned by one
        of the fetch party membership functions.
    :return: A dataframe of party memberships, with one row per party
        membership. The memberships are processed and combined so that there
        is only one party membership for a period of continuous membership
        within the same party.
    """

    # Check the party memberships dataframe has the expected structure
    required_columns = [
        "mnis_id",
        "given_name",
        "family_name",
        "display_name",
        "party_mnis_id",
        "party_name",
        "party_membership_start_date",
        "party_membership_end_date"]

    if pm.columns != required_columns:
        raise ValueError("pm does not have the expected columns")

    # Sort by mnis id and membership start date
    pm = pm.sort(
        ["mnis_id", "party_membership_start_date"],
        nulls_last=True,
        maintain_order=True)

    # Create unique combination of mnis_id and party_mnis_id and build an
    # id for consecutive memberships of the same party
    previous_per_par_id = ""
    group_id = 0
    per_par_mem_ids = []

    for row in pm.iter_rows(named=True):
        per_par_id = f"{row['mnis_id']}-{row['party_mnis_id']}"
        if per_par_id != previous_per_par_id:
            previous_per_par_id = per_par_id
            group_id = group_id + 1
        per_par_mem_ids.append(f"{per_par_id}-{group_id}")

    pm = pm.with_columns(
        pl.Series("per_par_mem_id", per_par_mem_ids, dtype=pl.String))

    # Group by person, party and consecutive membership, then take the
    # earliest start date and latest end date. As in R, the minimum and
    # maximum are null if any date in the group is null.
    group_columns = [
        "mnis_id",
        "given_name",
        "family_name",
        "display_name",
        "party_mnis_id",
        "party_name",
        "per_par_mem_id"]

    def min_max_with_nulls(column: str, agg: str) -> pl.Expr:
        agg_expr = (
            pl.col(column).min() if agg == "min" else pl.col(column).max())
        return (
            pl.when(pl.col(column).is_null().any())
            .then(pl.lit(None))
            .otherwise(agg_expr)
            .alias(column))

    return (
        pm
        .group_by(group_columns)
        .agg(
            min_max_with_nulls("party_membership_start_date", "min"),
            min_max_with_nulls("party_membership_end_date", "max"))
        .sort(group_columns, nulls_last=True)
        .sort(
            ["family_name", "party_membership_start_date"],
            nulls_last=True,
            maintain_order=True)
        .drop("per_par_mem_id"))
