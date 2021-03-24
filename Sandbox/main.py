import matplotlib.pyplot as plt

from Sandbox.DataPoint import DataPoint
from Sandbox.load_data import load_interest_rate, load_national_prices, load_wage_growth, load_cost_factor_of_purchase, \
    load_regional_prices, calculate_marginal_cost_increase, interest_to_cost
from Sandbox.run_model import run_model, run_breakpoint_model, run_price_trend_model, run_wage_correlation_model


# TODO sjekk rentedata - har brukt foliorente 91-93 selv om det står at det ikke var styringsrenten. Styringsrenten opp på 25% i 1992.
# TODO - vurder: K/L antar at utgiftene til bolig er prosentvis konstant. Dette er trolig ikke tilfelle.
# TODO ... kan vurdere å gjøre analyser på hvordan marginal lønnsvekst påvirker budsjettet til bolig.

# TODO sjekk data for andre fylker enn oslo. Undersøk om at K/L er stigende over tid.
#  Hypotese 1) K/L stiger pga tilbud/etterspørsel.
#  H2) byggekostnad
#  H3) Lønnsøkning fører til høyere andel av lønnen går til bolig
#  H4) Foreldre hjelper oftere til enn før med kjøp til barn (relatert til h1))


def calculate_total_price(prices, cost_factors):
    result = []
    for i in range(0, len(prices)):
        result.append(DataPoint(prices[i].date, prices[i].value * cost_factors[i].value))
    return result


def calculate_total_price_adjusted_for_wage_growth(costs, wages):
    result = []
    for i in range(0, len(costs)):
        result.append(DataPoint(costs[i].date, costs[i].value / wages[i].value))
    return result


def dates(timeseries):
    return list(map(lambda x: x.date, timeseries))


def values(timeseries):
    return list(map(lambda x: x.value, timeseries))


def display_stats(price_index, min_year):
    interest_rates = load_interest_rate(min_year)
    wage_growth = load_wage_growth(min_year)
    cost_factor = load_cost_factor_of_purchase(min_year)
    total_prices = calculate_total_price(price_index, cost_factor)
    prices_adjusted_for_wage = calculate_total_price_adjusted_for_wage_growth(total_prices, wage_growth)

    plt.plot(dates(price_index), values(price_index), label="Prisindeks (P)")
    plt.plot(dates(interest_rates), values(interest_rates), label="Rente (r)")
    plt.plot(dates(wage_growth), values(wage_growth), label="Lønnsvekst (L)")
    plt.plot(dates(cost_factor), values(cost_factor), label="Kostnadsfaktor (c)")
    plt.plot(dates(total_prices), values(total_prices), label="Totalkostnad (K) = P*c")
    plt.plot(dates(prices_adjusted_for_wage), values(prices_adjusted_for_wage), label="K/L")

    plt.xlabel('Tid')
    plt.ylabel('Verdi')
    plt.title('P, r, L, P_f og K')
    plt.legend()
    plt.show()


def plot_wages_to_prices(price_index, wage_growth):
    # Observed
    y = values(price_index)
    x = values(wage_growth)

    # Results from estimation
    plt.plot([1, 1.7], [0.922, 3.4525], label="Estimert", c="red")

    plt.scatter(x, y, label="Observasjoner")
    plt.title('Sammenheng prisvekst og lønnsvekst')
    plt.xlabel('Lønnsnivå')
    plt.ylabel('Boligpris')
    plt.legend()
    plt.show()


def plot_price_growth(price_index):
    # Observed
    plt.plot(dates(price_index), values(price_index), label="Prisindeks")

    # Estimated
    estimated_slope = 0.008
    endpoint_estimated = 1 + estimated_slope * len(price_index)
    plt.plot([dates(price_index)[0], dates(price_index)[-1]], [1, endpoint_estimated], label="Estimert", c="red")

    plt.xlabel('Tid')
    plt.ylabel('Boligpris')
    plt.legend()
    plt.show()


def plot_changepoint_analysis(absolute_prices):
    start_value = absolute_prices[0].value

    # Observed
    plt.plot(dates(absolute_prices), values(absolute_prices), label="Prisindeks")


    # Estimated
    estimated_changepoint_index = 100
    estimated_changepoint = absolute_prices[estimated_changepoint_index]
    change_date = estimated_changepoint.date
    change_date_value = estimated_changepoint.value
    plt.scatter(change_date, change_date_value, label="Knekkpunkt", c="green", s=70)

    #
    scale = 0.1
    a1 = 0.082 * scale
    a2 = -0.054 * scale

    p_top = 1 + a1 * estimated_changepoint_index
    p_end = change_date_value + a2 * (len(absolute_prices) - estimated_changepoint_index)

    plt.plot([dates(absolute_prices)[0], dates(absolute_prices)[estimated_changepoint_index]], [start_value, p_top], label="Tidlig trend", c="red")
    plt.plot([dates(absolute_prices)[estimated_changepoint_index], dates(absolute_prices)[-1]], [change_date_value, p_end], label="Sen trend", c="red")

    plt.xlabel('Tid')
    plt.ylabel('Boligpris')
    plt.legend()
    plt.show()


def plot_marginal_cost_increase(marginal_cost_increase):
    plt.plot(range(16), marginal_cost_increase)

    plt.xlabel('rente')
    plt.ylabel('Prisendring ved 1% renteøkning')
    plt.title('Marginal kostnadsendsøkning ved rentestigning')
    plt.legend()
    plt.show()


def plot_interest_to_cost():
    costs = []
    for r in range(16):
        cost = interest_to_cost(r)
        costs.append(cost)

    plt.plot(range(16), costs)

    plt.plot([0.01, 0.01], [0, costs[0]], c="red")
    plt.plot([1, 1], [0, costs[1]], c="red")

    plt.plot([8, 8], [0, costs[8]], c="red")
    plt.plot([9, 9], [0, costs[9]], c="red")

    plt.xlabel('rente')
    plt.ylabel('Kostnad')
    plt.title('Totalkostnad av boligkjøp')
    plt.legend()
    plt.axis([0, 15, 0, 3])
    plt.show()


def get_region(regions_prices, region):
    return (next((x for x in regions_prices if x.region == region), None)).prices


def absolute_to_relative_prices(prices):
    relative_prices = []
    for i in range(1, len(prices)):
        relative_prices.append(DataPoint(prices[i-1].date, prices[i].value - prices[i-1].value))
    return relative_prices


def monthly_to_quarterly(values_list):
    return values_list[0::3]



regions = [
    # 1992
    'Hele landet',
    'Oslo med Baerum',
    'Akershus uten Baerum',
    # 2005
    'Bergen',
    'Trondheim',
    'Stavanger',
    'Vestfold og Telemark og Viken uten Akershus',
    'Innlandet',
    'Agder og Rogaland uten Stavanger',
    'Moere og Romsdal og Vestland uten Bergen',
    'Trondelag uten Trondheim',
    'Nord-Norge',
]


national_price_index = load_national_prices(1992)
display_stats(national_price_index, 1992)
#plot_marginal_cost_increase(calculate_marginal_cost_increase())
#plot_interest_to_cost()

# run_price_trend_model(national_price_index)
# run_wage_correlation_model(monthly_to_quarterly(national_price_index), monthly_to_quarterly(load_wage_growth(1992)))

regional_prices = load_regional_prices()
# display_stats(get_region(regional_prices, "Stavanger"), 2005)
# stavanger_absolute_prices = get_region(regional_prices, "Stavanger")
# stavanger_relative_prices = absolute_to_relative_prices(stavanger_absolute_prices)
# run_breakpoint_model(stavanger_relative_prices)



# plot_wages_to_prices(national_price_index, load_wage_growth(1992))
# plot_price_growth(national_price_index)
# plot_changepoint_analysis(stavanger_absolute_prices)
