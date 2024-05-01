from __future__ import division
import argparse
from collections import defaultdict
import csv
from itertools import combinations
import pandas as pd
import random
from typing import Any, Generator

########## GLOBALS ##########

HEADER = ['NUM_FEATURES', 'CONCAT_FEATURES', 'IRREDUCIBLE_ERROR']

########## NORMALIZATION ##########

def _median_norm(col: pd.DataFrame) -> pd.DataFrame:
    median = col.median()
    return (col >= median).astype(int)

def normalize__inplace(mtx: pd.DataFrame) -> pd.DataFrame:
    # only do median normalization for numeric values
    numeric_cols = mtx.select_dtypes(include="number")

    for col_name, col in numeric_cols.items():
        mtx[col_name] = _median_norm(col)
       

########## VARIANCE HELPERS ##########

def _combinations_gen(features: pd.DataFrame, size_of: int) -> Generator:
    # groups of the column names
    for i, comb_colnames in enumerate(combinations(features.columns.tolist(), size_of)):
        # print(i)
        if random.random() < 0.8:
            continue
        # actually get the group of columns
        comb = features[list(comb_colnames)]
        yield comb

def _compute_irreducible__mutates(features: pd.DataFrame, outcomes: pd.DataFrame) -> list[pd.DataFrame]:
    group_by_colnames = features.columns.tolist()
    num_rows = features.shape[0]
    features.insert(len(group_by_colnames), "outcome", outcomes)
    agg_by_group = features.groupby(group_by_colnames).agg(['count', 'var'])
    variances_by_group = agg_by_group[('outcome', 'var')].fillna(0)
    counts_by_group = agg_by_group[('outcome', 'count')]
    return ((variances_by_group * counts_by_group) / num_rows).sum()



########## VARIANCE ENTRYPOINTS ##########

def compute_variances_for_groups_of_size(
        features: pd.DataFrame,
        outcomes: pd.DataFrame,
        size_of: int,
        csv_writer,
    ) -> pd.DataFrame:
    colnames = features.columns.tolist()
    colname_to_int = {
        colname: i
        for i, colname in enumerate(colnames)
    }
    num_cols = len(colnames)
    
    for comb in _combinations_gen(features, size_of):
        # set which columns are included to be written to csv
        included = [0]*num_cols
        for colname in comb.columns.tolist():
            idx = colname_to_int[colname]
            included[idx] = 1

        csv_writer.writerow(
            [
                size_of,
                ', '.join(comb.columns.tolist()),
                _compute_irreducible__mutates(comb, outcomes)
            ] + included   
        )


########## IRREDUCIBLE ERROR ENTRYPOINT ##########

def irreducible_error_entrypoint(
    data_filepath: str,
    results_filepath: str,
    outcome_colname: str,
    numbers_of_features: list[int]
) -> None:
    # need to consider if this needs more cleaning
    data = pd.read_csv(data_filepath, header=0)

    # do I drop the outcome before or after min max? here I am doing it before, but ask
    outcomes = data[outcome_colname]
    features = data.drop(outcome_colname, axis=1)
    data = normalize__inplace(data)

    with open(results_filepath, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        header = HEADER + features.columns.tolist()
        csv_writer.writerow(header)

        for size_of in numbers_of_features:
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
        "-numf", "--numbers_of_features",
        nargs='*', type=int, help="The sizes of the combinations that we will get for features. The sizes of features ew do nChoose for.", required=True,
    )
    
    args = sim_cli.parse_args()
    assert(args.numbers_of_features), "Must have some sizes to run on!"

    return irreducible_error_entrypoint(
        args.data_filepath,
        args.results_filepath,
        args.outcome_colname,
        args.numbers_of_features,
    )
    

if __name__ == "__main__":
    main()
