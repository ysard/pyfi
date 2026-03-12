"""Readers for various datasets containing historical data

- Banque de France
- INSEE
- Yahoo finance

All readers are configured to use and provide monthly data.
Each reader is paired with functions that allow to search and retrieve specific data.
"""
# Standard imports
from datetime import datetime
from functools import lru_cache

# Custom imports
import pandas as pd

# Local imports
import commons as cm


__all__ = [
    "find_pel_rate",
    "find_inflation_rate",
    "find_livreta_rate",
    "find_sp500_rate",
    "find_av_rate",
]


# Sort AV rates in chronological order
ASSURANCE_VIE_RATES = dict(sorted(cm.ASSURANCE_VIE_RATES.items()))


@lru_cache
def load_banque_de_france_dataset(filepath: str) -> pd.core.frame.DataFrame:
    """Load data from any Banque de France dataset

    .. note:: Expected field formats:
        date: "2005-01-31"
        rate: "0,0"

    :return: Dataframe of data sorted by chronological order.
    """
    df = pd.read_csv(
        filepath,
        sep=";",
        skiprows=6,  # ignore header lines
        header=None,
        names=["date", "taux"],
    )

    # Remove unknown values "-" (inflation rates dataset only ?)
    df = df[df["taux"] != "-"]

    # Convert data types
    df["date"] = pd.to_datetime(df["date"])
    df["taux"] = df["taux"].str.replace(",", ".").astype(float) / 100

    # Chronological sort (oldest first)
    df = df.sort_values("date")

    return df


@lru_cache
def load_insee_dataset(filepath: str) -> pd.core.frame.DataFrame:
    """Load data from any Banque de France dataset

    .. note:: Expected field formats:
        date: "2005-01"
        rate: "0.0"
        quality code: "A"

    :return: Dataframe of data sorted by chronological order.
    """
    df = pd.read_csv(
        filepath,
        sep=";",
        skiprows=4,  # ignore header lines
        header=None,
        names=["date", "taux", "qual_code"],
    )

    # Convert data types
    df["date"] = pd.to_datetime(df["date"])
    # Convert dates without days, to end-of-month dates!
    df["date"] = df["date"].dt.to_period("M").dt.to_timestamp("M")
    df["taux"] = df["taux"] / 100

    # Chronological sort (oldest first)
    df = df.sort_values("date")

    return df


@lru_cache
def load_yahoo_finance_dataset(filepath: str) -> pd.core.frame.DataFrame:
    """Load data from Yahoo finance website (which now charges a fee to obtain the CSV file)

    Data obtained from https://cobwebscripts.com/tools/yfindler.html
    """
    df = pd.read_csv(
        filepath,
        sep=",",
        skiprows=1,  # ignore header lines
        header=None,
        names=["date", "open", "high", "low", "close", "adj_close", "volume"],
    )

    # Convert data types
    df["date"] = pd.to_datetime(df["date"])
    # => no date scaling, last line is the current day, penultimate is the current month
    # Ex: penultimate (incomplete march)
    # 494 2026-03-01 6824.359863 6901.009766 6710.419922 6816.629883 6816.629883 12521160000 -0.009049
    df["taux"] = df["close"].pct_change(1)

    # Chronological sort (oldest first)
    # => already done

    return df


def find_rate(df: pd.core.frame.DataFrame, searched_date: datetime) -> float:
    """Find the rate in the given dataset according to the current date

    .. note:: If the given date is before the first date in the dataset
        the first date is used. If the given date is after the last date
        in the dataset, the last date is used.

    :param df: Dataframe of data sorted by chronological order.
        See :meth:`load_banque_de_france_dataset`.
    """
    prev_date = None
    found_rate = None
    for date in df["date"]:
        if date >= searched_date:
            found_rate = float(df[df["date"] == date]["taux"].iloc[0])
            print(f"Rate found: {found_rate:.2f} from {date} ({searched_date})")
            break

        prev_date = date

    if found_rate is None:
        # should use the last value in dataset ?
        found_rate = float(df[df["date"] == prev_date]["taux"].iloc[0])
        print(
            f"Rate NOT found for {searched_date}! "
            f"Use last known value: {found_rate:.2f} from {prev_date}"
        )

    return found_rate


@lru_cache
def find_pel_rate(searched_date: datetime) -> float:
    """Find the official PEL rate according to the opening date"""
    df_pel_rates = load_banque_de_france_dataset(cm.PEL_RATES_FILEPATH)

    # Find the rate according to the current date
    return find_rate(df_pel_rates, searched_date)


@lru_cache
def find_inflation_rate(searched_date: datetime, ipch: bool = False) -> float:
    """Find the current inflation rate according to the given date"""
    if ipch:
        infl_rates = load_banque_de_france_dataset(cm.INFLATION_IPCH_RATES_FILEPATH)
    else:
        infl_rates = load_insee_dataset(cm.INFLATION_IPC_RATES_FILEPATH)

    # Find the rate according to the current date
    return find_rate(infl_rates, searched_date)


@lru_cache
def find_livreta_rate(searched_date: datetime) -> float:
    """Find the current livret A rate according to the given date"""
    livreta_rates = load_banque_de_france_dataset(cm.LIVRETA_RATES_FILEPATH)

    # Find the rate according to the current date
    return find_rate(livreta_rates, searched_date)


@lru_cache
def find_sp500_rate(searched_date: datetime) -> float:
    """Find the current S&P500 rate according to the given date"""
    sp500_rates = load_yahoo_finance_dataset(cm.SP500TR_RATES_FILEPATH)

    # Find the rate according to the current date
    return find_rate(sp500_rates, searched_date)


@lru_cache
def find_av_rate(searched_date: datetime):
    """Find the current AV annual rate according to the given date"""
    prev_year = None
    found_rate = None
    # WARNING: A sorted dict is assumed
    searched_year = searched_date.year
    for year, rate in ASSURANCE_VIE_RATES.items():
        if year >= searched_year:
            found_rate = rate
            print(f"Rate found: {found_rate:.4f} from {year} ({searched_year})")
            break

        prev_year = year

    if found_rate is None:
        found_rate = ASSURANCE_VIE_RATES[prev_year]
        print(
            f"Rate NOT found for {searched_year}! "
            f"Use last known value: {found_rate:.4f} from {prev_year}"
        )

    return found_rate
