from __future__ import division
import argparse
from collections import defaultdict
import csv
from itertools import combinations
import pandas as pd
from pandas.api.types import is_numeric_dtype
from typing import Any, Generator

########## GLOBALS ##########
HEADER = ('NUM_FEATURES', 'CONCAT_FEATURES', 'IRREDUCIBLE_ERROR')

########## NORMALIZATION ##########

def _median_norm__inplace(col: pd.DataFrame) -> pd.DataFrame:
    median = col.median()
    col[:] = (col >= median).astype(int)
    return col

def normalize__inplace(mtx: pd.DataFrame) -> pd.DataFrame:
    # only do median normalization for numeric values
    numeric_cols = mtx.select_dtypes(include="number")

    for col_name, col in numeric_cols.iteritems():
        mtx[col_name] = _median_norm__inplace(col)
       

########## VARIANCE HELPERS ##########

def _combinations_gen(features: pd.DataFrame, size_of: int) -> Generator:
    for comb in combinations(features, size_of):
        yield pd.DataFrame(comb)

def _compute_values_for_mutually_exclusive_groups(features: pd.DataFrame, outcomes: pd.DataFrame) -> list[pd.DataFrame]:
    rows_to_vals = defaultdict(list)
    for i, row_tup in enumerate(features.itertuples(index=False, name=None)):
        outcome = outcomes[i]
        rows_to_vals[row_tup].append(outcome)
    return [
        pd.DataFrame(vals)
        for vals in rows_to_vals.values()
    ]

def _compute_exp_cond_variance(grouped_outcomes: list[pd.DataFrame]) -> float:
    exp_cond_variance = 0
    total_vals = 0
    for outcome_group in grouped_outcomes:
        num_vals = len(outcome_group)
        variance = outcome_group.var()
        total_vals += num_vals
        exp_cond_variance += variance*num_vals
    return exp_cond_variance / total_vals


########## VARIANCE ENTRYPOINTS ##########

def compute_variances_for_groups_of_size(
        features: pd.DataFrame,
        outcomes: pd.DataFrame,
        size_of: int,
        csv_writer,
    ) -> pd.DataFrame:
    for comb in _combinations_gen(features, size_of):
        csv_writer.writerow(
            (
                size_of,
                ', '.join(comb.columns.values),
                _compute_exp_cond_variance(
                    _compute_values_for_mutually_exclusive_groups(comb, outcomes)
                )
            )   
        )


########## IRREDUCIBLE ERROR ENTRYPOINT ##########

def irreducible_error_entrypoint(
    data_filepath: str,
    results_filepath: str,
    outcome_colname: str,
    group_sizes: list[int]
) -> None:
    # need to consider if this needs more cleaning
    data = pd.read_csv(data_filepath, header=0)

    # do I drop the outcome before or after min max? here I am doing it before, but ask
    outcomes = data[outcome_colname]
    features = data.drop(outcome_colname, axis=1)
    data = normalize__inplace(data)

    with open(results_filepath, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(HEADER)

        for size_of in group_sizes:
            compute_variances_for_groups_of_size(features, outcomes, size_of, csv_writer)


########## MAIN ##########

def main() -> None:
    sim_cli = argparse.ArgumentParser(description="A program to compute irreducible error.")
    sim_cli.add_argument(
        "-data", "--data_filepath",
        type=str, help="filepath to CSV file for the data", required=True,
    )
    sim_cli.add_argument(
        "-res", "--results_filepath",
        type=str, help="filepath to CSV file to write results to", required=True,
    )
    sim_cli.add_argument(
        "-out", "--outcome_colname",
        type=str, help="The name of the column that is the outcome/dependent variable", required=True,
    )
    sim_cli.add_argument(
        "-sizes", "--sizes_of_groups",
        nargs='*', type=int, help="The sizes of the combinations that we will get for features", required=True,
    )
    
    args = sim_cli.parse_args()
    assert(args.size_of_groups), "Must have some sizes to run on!"

    return irreducible_error_entrypoint(
        args.data_filepath,
        args.results_filepath,
        args.outcome_colname,
        args.sizes_of_groups,
    )
    



if __name__ == "__main__":
    main()
