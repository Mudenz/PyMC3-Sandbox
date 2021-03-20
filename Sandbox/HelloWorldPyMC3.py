import matplotlib.pyplot as plt

from Sandbox.DataPoint import DataPoint
from Sandbox.load_data import load_interest_rate, load_national_prices, load_wage_growth, load_cost_factor_of_purchase, \
    load_regional_prices
from Sandbox.run_model import run_model



# TODO sjekk rentedata - har brukt foliorente 91-93 selv om det står at det ikke var styringsrenten. Styringsrenten opp på 25% i 1992.
# TODO - vurder: K/L antar at utgiftene til bolig er prosentvis konstant. Dette er trolig ikke tilfelle.
# TODO ... kan vurdere å gjøre analyser på hvordan marginal lønnsvekst påvirker budsjettet til bolig.

# TODO sjekk data for andre fylker enn oslo. Undersøk om at K/L er stigende over tid.
    #  Hypotese 1) K/L stiger pga tilbud/etterspørsel.
    #  H2) byggekostnad
    #  H3) Lønnsøkning fører til høyere andel av lønnen går til bolig
    #  H4) Foreldre hjelper oftere til enn før med kjøp til barn (relatert til h1))
# TODO Sett opp K(t) = a*L(t) og estimer a.

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


regional_prices = load_regional_prices()
price_index = load_national_prices()
interest_rates = load_interest_rate()
wage_growth = load_wage_growth()
cost_factor = load_cost_factor_of_purchase()
total_prices = calculate_total_price(price_index, cost_factor)
prices_adjusted_for_wage = calculate_total_price_adjusted_for_wage_growth(total_prices, wage_growth)

plt.plot(dates(price_index), values(price_index), label="Prisindeks (P)")
plt.plot(dates(interest_rates), values(interest_rates), label="Rente (r)")
plt.plot(dates(wage_growth), values(wage_growth), label="Lønnsvekst (L)")
plt.plot(dates(cost_factor), values(cost_factor), label="Kostnadsfaktor (P_f)")
plt.plot(dates(total_prices), values(total_prices), label="Totalkostnad (K)")
plt.plot(dates(prices_adjusted_for_wage), values(prices_adjusted_for_wage), label="K/L")

plt.xlabel('Tid')
plt.ylabel('Verdi')
plt.title('P, r, L, P_f og K')
plt.legend()
plt.show()

# run_model()
