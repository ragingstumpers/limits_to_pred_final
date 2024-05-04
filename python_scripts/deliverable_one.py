from __future__ import division
import argparse
import csv
from enum import Enum
from itertools import combinations
import numpy as np
import pandas as pd
from typing import Any, Generator

########## GLOBALS ##########

HEADER = ['NUM_FEATURES', 'CONCAT_FEATURES', 'IRREDUCIBLE_ERROR']
NULL_STRINGS = {
    "nan", "NAN", "NaN", "null", "Null", "NULL", "n/a",
}
COL_CUSTOM_HANDLERS = {
    'age': lambda x: x.replace("90 (90+ in 1980 and 1990)", 100).replace("less than 1 year old", 0).astype('float64'),
    'uhrswork': lambda x: x.replace("99 (topcode)", 100).astype('float64')
}

class NormalizeOptions(Enum):
    median = 'median'
    quartile = 'quartile'
    decile = 'decile'


########## NORMALIZATION ##########

def _median_norm(col: pd.DataFrame) -> pd.DataFrame:
    median = col.median()
    return (col >= median).astype(int)

def _quartiles_norm(col: pd.DataFrame) -> pd.DataFrame:
    return pd.qcut(col, 4, duplicates='drop')

def _deciles_norm(col: pd.DataFrame) -> pd.DataFrame:
    return pd.qcut(col, 10, duplicates='drop')

NORM_OPTONS_TO_FN = {
    NormalizeOptions.median: _median_norm,
    NormalizeOptions.quartile: _quartiles_norm,
    NormalizeOptions.decile: _deciles_norm,
}

def normalize__inplace(features: pd.DataFrame, norm_option: NormalizeOptions) -> pd.DataFrame:
    # handle some specific cases
    for colname, handler in COL_CUSTOM_HANDLERS.items():
        features[colname] = handler(features[colname])

    normalizer = NORM_OPTONS_TO_FN[norm_option]
    # only do median normalization for numeric values
    numeric_cols = features.select_dtypes(include="number")
    for col_name, col in numeric_cols.items():
        features[col_name] = normalizer(col)
    return features
       

########## VARIANCE HELPERS ##########

def _combinations_gen(features: pd.DataFrame, size_of: int) -> Generator:
    # groups of the column names
    for i, comb_colnames in enumerate(combinations(features.columns.tolist(), size_of)):
        # actually get the group of columns
        comb = features[list(comb_colnames)]
        yield comb

def _compute_irreducible__mutates(features: pd.DataFrame, outcomes: pd.DataFrame) -> list[pd.DataFrame]:
    group_by_colnames = features.columns.tolist()
    num_rows = features.shape[0]
    features.insert(len(group_by_colnames), "outcomes", outcomes)
    agg_by_group = features.groupby(group_by_colnames).agg(['count', 'var'])
    variances_by_group = agg_by_group[('outcomes', 'var')].fillna(0)
    counts_by_group = agg_by_group[('outcomes', 'count')]
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
    numbers_of_features: list[int],
    log_outcomes: bool,
    norm_option: NormalizeOptions,
) -> None:
    # need to consider if this needs more cleaning
    data = pd.read_csv(data_filepath, header=0, na_filter=True, na_values=NULL_STRINGS)

    if log_outcomes:
        data[outcome_colname] = np.log(data[outcome_colname] + 1)

    outcomes = data[outcome_colname]
    features = data.drop(outcome_colname, axis=1)
    features = normalize__inplace(features, norm_option)

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
    sim_cli.add_argument(
        "-log", "--log_outcomes",
        type=bool, default=False, help="Should the outcome column have +1 then log applied to it.",
    )
    sim_cli.add_argument(
        "-norm", "--norm_option",
        type=str, choices=[nopt.value for nopt in NormalizeOptions],
        default=NormalizeOptions.median.value, help="What resolution to normalize the data.",
    )
    
    args = sim_cli.parse_args()
    assert(args.numbers_of_features), "Must have some sizes to run on!"

    return irreducible_error_entrypoint(
        args.data_filepath,
        args.results_filepath,
        args.outcome_colname,
        args.numbers_of_features,
        args.log_outcomes,
        NormalizeOptions(args.norm_option),
    )
    

if __name__ == "__main__":
    main()
