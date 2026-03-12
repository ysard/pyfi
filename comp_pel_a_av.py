#!/usr/bin/env python3
"""Comparison of French investments: Life Insurance, PEL, Livret A, PEA (S&P 500),
based on historical data.
"""
# Standard imports
from datetime import datetime

# Custom imports
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import colormaps

# Local imports
import commons as cm
from readers import *
try:
    from simul import rendement_minimal_global

    EXT_MODULE_FOUND = True
except ModuleNotFoundError:
    EXT_MODULE_FOUND = False

# =============
# User settings
# =============

# Simulation settings
CAPITAL_INITIAL = 23000
DUREE_ANNEES = 26
DATE_DEBUT = "2000-01-01"

# Rates
# PEL rate, leave it to None for automatic selection
PEL_RATE = None

FRAIS_GESTION_AV = 0.00  # included in av rate
# Dataset used for inflation; see module's docstring, IPC is used if False.
IPCH = False

# Tax rates
PS = 0.172
IR_PFU = 0.128
IR_TMI = 0.11
IR_AV = 0.075
PFU = 0.30
PS_2026 = 0.186
PFU_2026 = 0.314

# False for standard taxation using PS and TMI
PFU_ENABLED = True
# TODO: evolution of TMI
# flat tax à 31.4% (12.8% impôt sur le revenu + 18.6% prélèvements sociaux)

# ====================
# End of user settings
# ====================

DT_PEL_START = datetime.strptime(DATE_DEBUT, "%Y-%m-%d")
# Used to trigger tax event after 10 years for PEL opened before 2011-03-01
PEL_YEARS_10 = None


def get_pel_net_interest(
    pel_amount: float,
    pel_rate: float,
    open_date: datetime,
    current_date: datetime,
    capital_initial: float = CAPITAL_INITIAL,
    pfu_enabled: bool=PFU_ENABLED,
    ir_tmi: float=IR_TMI,
) -> float:
    """Compute the monthly interest amount for the given PEL characteristics

    .. note:: The age of the contract and its creation date affect its taxation.
    """
    # pylint: disable=global-statement
    global PEL_YEARS_10

    interest = pel_amount * pel_rate / 12
    ps_rate = PS if current_date < datetime(2026, 1, 1) else PS_2026
    pfu_rate = PFU if current_date < datetime(2026, 1, 1) else PFU_2026

    age_years = (current_date - open_date).days / 365.25
    # print(age_years, current_date)

    full_taxation_rate = 1 - (pfu_rate if pfu_enabled else (ps_rate + ir_tmi))

    # PEL since 2018
    if open_date >= datetime(2018, 1, 1):
        return interest * full_taxation_rate

    # PEL 2011-2017
    if open_date >= datetime(2011, 3, 1):
        if age_years < 12:
            return interest * (1 - ps_rate)
        return interest * full_taxation_rate

    # PEL before 2011
    if int(age_years) == 10 and not PEL_YEARS_10:
        # Anniversary!
        # - PS tax first on interests
        # - Compute the interests for the current month after
        PEL_YEARS_10 = True

        print("10 years anniversary!! Tax PS from past interests", age_years)
        # pel_values[-1] - pel_values[0]
        accumulated_interests = pel_amount - capital_initial

        # Apply PS
        print(f"Interests accumulated before PS tax: {accumulated_interests:.2f}")
        social_contrib = accumulated_interests * ps_rate
        print(
            "Interests accumulated after PS tax: "
            f"{accumulated_interests - social_contrib:.2f} (theft: {social_contrib:.2f})"
        )

        # Total after tax
        pel_amount -= social_contrib
        # Recalculate interests on the new basis
        interest = pel_amount * pel_rate / 12

        # Tax & Return the balance of the operation
        return interest * (1 - ps_rate) - social_contrib

    if age_years < 10:
        return interest  # PS différés

    if age_years < 11:
        print("PS only")
        return interest * (1 - ps_rate)

    print("Full tax enabled")
    return interest * full_taxation_rate


def make_graphs(
    dates: pd.core.indexes.datetimes.DatetimeIndex,
    data: dict[str, list[float]],
    dt_pel_start: datetime = DT_PEL_START,
    show_av_withdrawal_sold: bool = True,
    show_pea_withdrawal_sold: bool = True,
    interactive=True,
):
    """Build graph according to the given label/values, using Matplotlib backend

    :param dates: Range of monthly dates on the period specified by the user.
    :param data: All datasets of values simulated values over the period.
        Dataset names as keys, values as values.
    :key dt_pel_start: PEL opening date (redundant with the first value in dates).
    :key show_av_withdrawal_sold: Show an indicator about the amount of net
        capital at the end of the AV contract. (default: True).
    :key show_pea_withdrawal_sold: Show an indicator about the amount of net
        capital at the end of the PEA contract. (default: True).
    :key interactive: Enable the matplotlib interactive graph
        (not compatible with streamlit app). (default: True).
    :return: matplotlib figure
    :rtype: <matplotlib.figure.Figure>
    """

    def show_h_limit(sold, title, color):
        """Show an horizontal indicator for the amount of net capital after full withdrawal"""
        ax.axhline(sold, c=color, linestyle="--", lw=0.9, alpha=0.5)
        plt.text(
            dates[0],
            sold,
            title,
            horizontalalignment="left",
        )

    fig = plt.figure()
    ax = fig.gca()

    # Get colors only to match the AV sold line colors
    colors = colormaps["tab10"].colors

    # Trace data
    _ = [
        plt.plot(dates, values, label=label, c=color)
        for color, (label, values) in zip(iter(colors), data.items())
    ]

    # AV limit: Net capital
    if show_av_withdrawal_sold:
        # WARNING: Beware with data renaming
        g = (
            (color, (label, av_values))
            for color, (label, av_values) in zip(iter(colors), data.items())
            if label.startswith("Assurance Vie")
        )
        av_annual_rate = find_av_rate(dates[-1])
        for color, (label, av_values) in g:
            print(f"{label}:")
            av_withdrawal_sold = get_av_withdrawal_sold(av_values, av_annual_rate)
            show_h_limit(av_withdrawal_sold, f"{label} solde final", color)

            # ax.axhline(av_withdrawal_sold, c=color, linestyle="--", lw=0.9, alpha=0.5)
            # plt.text(
            #     dates[0],
            #     av_withdrawal_sold,
            #     "AV solde final",
            #     horizontalalignment="right",
            # )

    if show_pea_withdrawal_sold:
        # WARNING: Beware with data renaming
        g = (
            (color, (label, av_values))
            for color, (label, av_values) in zip(iter(colors), data.items())
            if label.startswith("S&P500")
        )

        for color, (label, values) in g:
            pea_withdrawal_sold = get_pea_withdrawal_sold(dates[-1], values[-1])
            show_h_limit(pea_withdrawal_sold, f"{label} solde final", color)


    # PEL closure date (used to show an indicator only for PEL opened after 2011-03-01)
    dt_pel_closure = dt_pel_start.replace(year=dt_pel_start.year + 15)
    if dt_pel_start >= datetime(2011, 3, 1) and dt_pel_closure <= dates[-1]:
        # Forced closure
        ax.axvline(dt_pel_closure, color="blue", linestyle="--", lw=0.9, alpha=0.5)
        plt.text(
            dt_pel_closure,
            max(data["PEL"]),  # WARNING: Beware with data renaming
            "Fin PEL",
            rotation=90,
            verticalalignment="bottom",
        )

    # Initial capital as reference (1st val of any serie)
    capital_initial = next(iter(data.values()))[0]
    ax.axhline(capital_initial, color="grey", linestyle="--", lw=0.9, alpha=0.5)

    # xticks
    years = mdates.YearLocator(base=2)  # every 2 years
    years_fmt = mdates.DateFormatter("%Y")
    # format the ticks only for years on the major ticks
    ax.xaxis.set_major_locator(years)
    ax.xaxis.set_major_formatter(years_fmt)
    # Show 1st xaxis tick
    ax.set_xlim(xmin=dates[0].to_numpy().astype("datetime64[Y]"))
    plt.xticks(rotation=45)

    plt.legend()
    plt.title("Comparaison des placements : Assurance Vie, PEL, Livret A, PEA (S&P 500)")
    plt.xlabel("Années")
    plt.ylabel("Capital (€)")
    plt.grid()

    if interactive:
        plt.show()
    return fig


def make_plotly(
    dates: pd.core.indexes.datetimes.DatetimeIndex,
    data: dict[str, list[float]],
    dt_pel_start: datetime = DT_PEL_START,
    show_av_withdrawal_sold: bool = True,
    show_pea_withdrawal_sold: bool = True,
    **kwargs,
):
    """Build graph according to the given label/values, using Plotly backend

    :param dates: Range of monthly dates on the period specified by the user.
    :param data: All datasets of values simulated values over the period.
        Dataset names as keys, values as values.
    :key dt_pel_start: PEL opening date (redundant with the first value in dates).
    :key show_av_withdrawal_sold: Show an indicator about the amount of net
        capital at the end of the AV contract. (default: True).
    :key show_pea_withdrawal_sold: Show an indicator about the amount of net
        capital at the end of the PEA contract. (default: True).
    :return: plotly figure
    :rtype: <plotly.graph_objs._figure.Figure>
    """
    import plotly.express as px

    def show_h_limit(sold, title):
        """Show an horizontal indicator for the amount of net capital after full withdrawal"""
        fig.add_hline(
            y=sold,
            line_dash="dot",
            opacity=0.5,
            annotation_text=f"{title} ({int(sold)} €)",
            annotation_position="top left",
        )


    # Reshape data for plotly express
    df = pd.DataFrame(data, index=dates)
    df = df.reset_index().rename(columns={"index": "Date"})
    df_long = df.melt(id_vars="Date", var_name="Placement", value_name="Capital")

    # Main figure
    fig = px.line(
        df_long,
        x="Date",
        y="Capital",
        color="Placement",
        title="Comparaison des placements : Assurance Vie, PEL, Livret A, PEA (S&P 500)",
    )

    # Initial capital as reference (1st val of any serie)
    capital_initial = next(iter(data.values()))[0]

    fig.add_hline(
        y=capital_initial,
        line_dash="dash",
        opacity=0.4,
        annotation_text="Capital initial",
        annotation_position="bottom left",
    )

    # AV limit: Net capital
    if show_av_withdrawal_sold:
        av_annual_rate = find_av_rate(dates[-1])
        # WARNING: Beware with data renaming (sync in make_graphs)
        for label, values in data.items():
            if label.startswith("Assurance Vie"):
                av_withdrawal_sold = get_av_withdrawal_sold(values, av_annual_rate)

                show_h_limit(av_withdrawal_sold, f"{label} AV solde final")

    # PEA limit: Net capital
    if show_pea_withdrawal_sold:
        # WARNING: Beware with data renaming (sync in make_graphs)
        for label, values in data.items():
            if label.startswith("S&P500"):
                pea_withdrawal_sold = get_pea_withdrawal_sold(dates[-1], values[-1])

                show_h_limit(pea_withdrawal_sold, f"{label} solde final")

    # PEL closure date (used to show an indicator only for PEL opened after 2011-03-01)
    dt_pel_closure = dt_pel_start.replace(year=dt_pel_start.year + 15)
    if dt_pel_start >= datetime(2011, 3, 1) and dt_pel_closure <= dates[-1]:
        fig.add_vline(
            x=dt_pel_closure.timestamp() * 1000,
            line_dash="dash",
            opacity=0.5,
            annotation_text="Fin PEL",
            annotation_position="top",
        )

    fig.update_layout(
        xaxis_title="Années",
        yaxis_title="Capital (€)",
        hovermode="x unified",
        legend_title="",
        height=700,  # pixels
    )

    # xticks
    fig.update_xaxes(
        dtick="M24",  # tick tous les 2 ans
        tickformat="%Y",
        hoverformat="%B %Y"  # Title of the hover tooltip: month & year
    )

    fig.update_traces(
        hovertemplate="<b>%{fullData.name}</b><br>" +
                    # "Date: %{x|%b %Y}<br>" +
                    "Capital: %{y:,.0f} €<extra></extra>"
    )

    # Add final amounts | gains in legend
    for trace in fig.data:
        last_value = trace.y[-1]
        gains = last_value - capital_initial
        trace.name = f"{trace.name} ({last_value:.0f} €, {"+" if gains > 0 else ""}{gains:.0f} €)"

    return fig


def get_av_withdrawal_sold(
    av_values: list, av_annual_rate: float, years_duration: float = DUREE_ANNEES
) -> float:
    """Get the amount net of taxes in case of full liquidation of the AV

    :param av_values: Computed list of simulated values over the period
        (we need the amount of the primes to calculate the gains).
    :param av_annual_rate: Last annual_rate used to simulate optimal withdrawal
        and future rate to compensate taxation (not really used here).
        See :meth:`rendement_minimal_global`.
    """
    if not EXT_MODULE_FOUND:
        # Naive withdrawal tax on AV
        print(av_values[-1])
        print(av_values[-1] - av_values[0])
        av_gains = av_values[-1] - av_values[0]
        av_tax = av_gains * (PS + IR_AV)  # NOTE: 8 years supposed, < 152000
        av_withdrawal_sold = av_values[0] + av_gains - av_tax
        print(av_withdrawal_sold)
        return av_withdrawal_sold

    # Full withdrawal tax on AV
    *_, av_withdrawal_sold = rendement_minimal_global(
        encours=av_values[-1],
        primes=av_values[0],
        rachat=av_values[-1],  # Full withdrawal
        taux_ps=PS,
        taux_av=av_annual_rate,
        frais_av=0,
        horizon=1,
        couple=False,
        pre_2017=True,
        duration=years_duration,
        gains_post_2017=0,
        bareme_ir=None,
    )

    return av_withdrawal_sold


def get_pea_withdrawal_sold(current_date, gross_capital):
    """Get the amount net of taxes in case of a full liquidation of the PEA

    .. note:: We suppose that the PEA is 5 years old (no IR, just PS).
    """
    ps_rate = PS if current_date < datetime(2026, 1, 1) else PS_2026
    return gross_capital * (1 - ps_rate)


def get_real_returns(
    data: dict[str, list[float]],
    av_annual_rate: float,
    years_duration: float = DUREE_ANNEES,
):
    """Get average real yield for every given dataset

    Taux de croissance annuel composé / Compound annual growth rate (CAGR)

    :param data: All datasets of values simulated values over the period.
    :param av_annual_rate: Last annual_rate used to simulate optimal withdrawal
        and future rate to compensate taxation (not really used here).
        See :meth:`rendement_minimal_global`.
    """
    real_returns = {}
    for label, values in data.items():
        final_value = (
            get_av_withdrawal_sold(values, av_annual_rate)
            if "Assurance Vie" in label
            else values[-1]
        )
        real_return = (final_value / values[0]) ** (1 / years_duration) - 1

        real_returns[label] = round(real_return * 100, 2)

    # print(real_returns)
    return real_returns


def get_cagr_df(
    dates: pd.core.indexes.datetimes.DatetimeIndex,
    data: dict[str, list[float]],
    years_duration: float
) -> pd.DataFrame:
    """Build dataframe of CAGR for each given dataset

    :param dates: Range of monthly dates on the period specified by the user.
    :param data: All datasets of values simulated values over the period.
    :param years_duration: Duration of the study in years.
    """
    av_annual_rate = find_av_rate(dates[-1])

    returns = get_real_returns(
        data,
        av_annual_rate,
        years_duration=years_duration
    )

    # df_returns = pd.DataFrame.from_dict(
    #     returns,
    #     orient="index",
    #     columns=["CAGR réel"]
    # )
    # df_returns["CAGR réel"] = df_returns["CAGR réel"].map("{:.2f} %".format)

    summary = [
        {
            "Placement": label,
            "Capital final (€)": round(values[-1], 0),
            "Gains (€)": round(values[-1] - values[0], 0),
            "CAGR réel (%)": returns[label],
        }
        for label, values in data.items()
    ]
    df_summary = pd.DataFrame(summary)
    df_summary["CAGR réel (%)"] = df_summary["CAGR réel (%)"].map("{:.2f} %".format)

    return df_summary


def simulate(
    capital_initial: float = CAPITAL_INITIAL,
    start_date: str = DATE_DEBUT,
    years_duration: int = DUREE_ANNEES,
    ipch: bool = IPCH,
    dt_pel_start: datetime = DT_PEL_START,
    pel_rate: float = PEL_RATE,
    av_fees_rate: float = FRAIS_GESTION_AV,
    pfu_enabled: bool=PFU_ENABLED,
    ir_tmi: float=IR_TMI,
    **kwargs
) -> tuple[pd.core.indexes.datetimes.DatetimeIndex, dict[str, list[float]]]:
    """Simulate various investment envelopes (PEL, Livret A, Assurance Vie)

    A variation inflation corrected for each envelope is also simulated.

    :return: List of dates and dict of simulated data (dataset names as keys).
    """
    global PEL_YEARS_10
    PEL_YEARS_10 = None

    # Prepare structures for computed the values
    pel_wo_tax = capital_initial
    pel = capital_initial
    livret = capital_initial
    av = capital_initial
    sp500 = capital_initial

    # Normal values
    pel_values_wo_tax = [pel_wo_tax]
    pel_values = [pel]
    livret_values = [livret]
    av_values = [av]
    sp500_values = [sp500]

    # Inflation-adjusted values
    inflation_index = 1
    pel_real_values_wo_tax = [pel_wo_tax]
    pel_real_values = [pel]
    livret_real_values = [livret]
    av_real_values = [av]
    sp500_real_values = [sp500]

    # PEL fixed rate
    # Rate may be fixed globally by user
    pel_rate = pel_rate if pel_rate else find_pel_rate(dt_pel_start)

    # Generate the full range of dates (+1 for the initial value)
    # WARNING: Les intérêts ne sont PAS calculés au prorata des jours restants du premier mois
    # (considéré comme complet).
    dates = pd.date_range(start=start_date, periods=years_duration * 12 + 1, freq="ME")
    for date in dates[1:]:
        # -------- PEL --------
        # Always the same rate without tax (virtual)
        pel_wo_tax *= 1 + pel_rate / 12
        # Tax
        net_interest = get_pel_net_interest(
            pel,
            pel_rate,
            dt_pel_start,
            date,
            capital_initial=capital_initial,
            pfu_enabled=pfu_enabled,
            ir_tmi=ir_tmi
        )
        pel += net_interest

        # -------- Livret A --------
        livret_rate = find_livreta_rate(date)
        livret *= 1 + livret_rate / 12

        # -------- Assurance Vie --------
        av_annual_rate = find_av_rate(date)
        monthly_rate = (av_annual_rate - av_fees_rate) / 12
        av *= 1 + monthly_rate

        # -------- S&P 500 --------
        sp500_rate = find_sp500_rate(date)
        sp500 *= 1 + sp500_rate

        # Retain portfolio values
        pel_values_wo_tax.append(pel_wo_tax)
        pel_values.append(pel)
        livret_values.append(livret)
        av_values.append(av)
        sp500_values.append(sp500)

        # Apply inflation on gains & retain portfolio values
        annual_inflation = find_inflation_rate(date, ipch=ipch)
        monthly_inflation = annual_inflation / 12
        inflation_index *= 1 + monthly_inflation

        pel_real_values_wo_tax.append(pel_wo_tax / inflation_index)
        pel_real_values.append(pel / inflation_index)
        livret_real_values.append(livret / inflation_index)
        av_real_values.append(av / inflation_index)
        sp500_real_values.append(sp500 / inflation_index)

    data = {
        "PEL": pel_values,  # WARNING: Beware with data renaming (sync in make_graphs)
        "Livret A": livret_values,
        "Assurance Vie (€)": av_values,
        "PEL virtuel SANS taxes": pel_values_wo_tax,
        "S&P500": sp500_values,  # WARNING: Beware with data renaming (sync in make_graphs)
    }

    data.update(
        {
            "PEL (infl)": pel_real_values,
            "Livret A (infl)": livret_real_values,
            "Assurance Vie (€) (infl)": av_real_values,
            "PEL virtuel SANS taxes (infl)": pel_real_values_wo_tax,
            "S&P500 (infl)": sp500_real_values,
        }
    )

    _ = get_real_returns(data, av_annual_rate, years_duration=years_duration)

    return dates, data


def test_find_rates() -> None:
    """Test find* functions to ensure proper dataset interpretation"""

    found = find_pel_rate(datetime(2003, 8, 1))
    assert found == 0.025, found
    found = find_pel_rate(datetime(2003, 8, 31))
    assert found == 0.025, found
    found = find_pel_rate(datetime(2003, 7, 31))
    assert found == 0.0327, found

    # IPCH
    found = find_inflation_rate(datetime(2015, 4, 30), ipch=True)
    assert found == 0.001, found
    found = find_inflation_rate(datetime(2015, 3, 31), ipch=True)
    assert found == 0.0, found
    found = find_inflation_rate(datetime(2015, 3, 30), ipch=True)
    assert found == 0.0, found
    found = find_inflation_rate(datetime(2024, 7, 1), ipch=True)
    assert round(found, 3) == 0.027, found

    found = find_inflation_rate(datetime(2199, 3, 30), ipch=True)
    assert round(found, 3) == 0.007, found  # last known value 2025-12-31: 0.7

    found = find_inflation_rate(datetime(1900, 3, 30), ipch=True)
    assert round(found, 3) == 0.018, found  # first known value 1997-01-31: 1.8

    # IPC
    found = find_inflation_rate(datetime(2015, 4, 30))
    assert found == 0.001, found
    found = find_inflation_rate(datetime(2015, 3, 31))
    assert found == -0.001, found
    found = find_inflation_rate(datetime(2015, 3, 30), ipch=False)
    assert found == -0.001, found
    found = find_inflation_rate(datetime(2024, 7, 1))
    assert round(found, 3) == 0.022, found

    found = find_inflation_rate(datetime(2199, 3, 30))
    assert round(found, 3) == 0.007, found  # last known value 2025-12-31: 0.7

    found = find_inflation_rate(datetime(1900, 3, 30))
    assert round(found, 3) == 0.034, found  # first known value 1991-01: 3.4

    found = find_livreta_rate(datetime(2026, 2, 1))
    assert round(found, 3) == 0.015, found
    found = find_livreta_rate(datetime(2026, 1, 31))
    assert round(found, 3) == 0.017, found

    found = find_av_rate(datetime(2022, 2, 1))
    assert round(found, 3) == 0.025, found

    found = find_av_rate(datetime(1900, 2, 1))
    first_year = min(cm.ASSURANCE_VIE_RATES.keys())
    expected = cm.ASSURANCE_VIE_RATES[first_year]
    assert found == expected, f"{first_year}: {found} != {expected}"

    found = find_av_rate(datetime(2199, 2, 1))
    last_year = max(cm.ASSURANCE_VIE_RATES.keys())
    expected = cm.ASSURANCE_VIE_RATES[last_year]
    assert found == expected, f"{last_year}: {found} != {expected}"


    found = find_sp500_rate(datetime(2026, 2, 1))
    # SP500
    # assert round(found, 4) == round(-0.008668, 4), found
    # SP500 TR
    assert round(found, 4) == round(-0.007599, 4), found


def test_get_pea_tax():
    """Test taxation on withdrawal from a PEA"""

    # PS: 17.2%
    found = get_pea_withdrawal_sold(datetime(2025, 12, 31), 10000)
    assert found == 8280

    # PS: 18.6%
    found = get_pea_withdrawal_sold(datetime(2026, 1, 1), 10000)
    assert int(found) == 8140


if __name__ == "__main__":
    test_find_rates()
    test_get_pea_tax()
    make_graphs(*simulate())
