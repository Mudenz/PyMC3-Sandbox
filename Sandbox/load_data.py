import csv
from pathlib import Path

from Sandbox.MultiValueDataPoint import MultiValueDataPoint
from Sandbox.RegionPrices import RegionPrices
from .DataPoint import DataPoint
import datetime


def load_national_prices(min_year):
    cutoff_date = datetime.date(2003, 1, 2)
    index_monthly = load_monthly_index()
    index_quarterly = load_quarterly_index(cutoff_date)
    index = transform_index(index_quarterly, index_monthly)
    index = crop_value(index, min_year)
    index = normalize(index)

    return adjust_for_inflation(index, load_inflation(min_year))


def load_regional_prices():
    regional_prices_flat = load_multi_point_file("Boligindeks regionalt.csv", 0, 1, 2)
    regions = get_regions(regional_prices_flat)
    regional_prices = get_regional_prices(regional_prices_flat, regions)
    transform_regional_prices(regional_prices)

    return regional_prices


def load_interest_rate(min_year):
    interest = load_file("renteutvikling fra 2001.csv", 0, 1)
    interest = transform_interest_rates(interest, min_year)

    return crop_value(interest, min_year)


def load_wage_growth(min_year):
    wage = load_file("lonnsvekst.csv", 0, 1)
    wage = transform_wage(wage)
    wage = crop_value(wage, min_year)
    wage = normalize(wage)

    return adjust_for_inflation(wage, load_inflation(min_year))


def load_inflation(min_year):
    inflation = load_file("lonnsvekst.csv", 0, 3)
    inflation = string_to_dates(inflation)
    inflation = crop_value(inflation, min_year)
    inflation = transform_inflation(inflation)

    return normalize(inflation)


# total cost of loan as a multiple of price. With 0 net interes rate this will return 1.
def load_cost_factor_of_purchase(min_year):
    interest = load_interest_rate(min_year)
    return calculate_total_loan_cost_factor(interest)


def load_file(file_name, first_col_nr, second_col_nr):
    relative_path_1 = "data/" + file_name
    mod_path = Path(__file__).parent.parent
    file_path = (mod_path / relative_path_1).resolve()
    return load_csv(file_path, first_col_nr, second_col_nr)


def load_multi_point_file(file_name, first_col_nr, second_col_nr, third_col_nr):
    relative_path_1 = "data/" + file_name
    mod_path = Path(__file__).parent.parent
    file_path = (mod_path / relative_path_1).resolve()
    return load_tri_col_csv(file_path, first_col_nr, second_col_nr, third_col_nr)


def load_csv(file_path, first_col_nr, second_col_nr):
    result = []
    with open(file_path) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=';')
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                print(f'Column names are {", ".join(row)}')
            elif len(row) > second_col_nr:
                result.append(DataPoint(row[first_col_nr], float((row[second_col_nr]).replace(",", "."))))
            else:
                print("exmpty row:")
                print(row)
            line_count += 1
        print(f'Processed {line_count} lines.')
    return result


def load_tri_col_csv(file_path, first_col_nr, second_col_nr, third_col_nr):
    result = []
    with open(file_path) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=';')
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                print(f'Column names are {", ".join(row)}')
            elif len(row) > second_col_nr:
                result.append(MultiValueDataPoint(row[first_col_nr], row[second_col_nr],
                                                  float((row[third_col_nr]).replace(",", "."))))
            else:
                print("exmpty row:")
                print(row)
            line_count += 1
        print(f'Processed {line_count} lines.')
    return result


def transform_index(first_index, second_index):
    first_end_value = first_index[-1].value

    # transform to get overlapping values
    second_index = list(map(lambda x: DataPoint(x.date, x.value * first_end_value / 100), second_index))

    # remove data point that overlaps
    second_index.pop(0)

    return first_index + second_index


def load_monthly_index():
    index = load_file("boligpris index fra 2003.csv", 0, 1)
    return list(map(lambda x: DataPoint(parse_date(x.date), x.value), index))


def parse_date(date_as_string):
    return datetime.datetime.strptime(date_as_string, '%d.%m.%Y').date()


def load_quarterly_index(cutoff_date):
    index_quarterly = load_file("kvartalsvis index.csv", 0, 1)
    result = quarterly_to_monthly(index_quarterly)
    result = list(filter(lambda x: x.date < cutoff_date, result))

    return result


def quarterly_to_monthly(index_quarterly):
    result = []
    for i in range(0, len(index_quarterly)):
        quarter = index_quarterly[i]
        year = int(quarter.date[0:4])
        quarter_number = int(quarter.date[5])
        if i == 0:
            value_at_start_of_quarter = quarter.value
            value_at_end_of_quarter = quarter.value
        else:
            value_at_start_of_quarter = index_quarterly[i - 1].value
            value_at_end_of_quarter = quarter.value
        for month_in_quarter in range(1, 4):
            month = (quarter_number - 1) * 3 + month_in_quarter
            date = datetime.date(year, month, 1)

            value_increase_quarter = value_at_end_of_quarter - value_at_start_of_quarter
            avg = value_increase_quarter / 3
            value = value_at_start_of_quarter + avg * (month_in_quarter - 1)

            result.append(DataPoint(date, value))
    last_data_point = result[-1]
    last_date = last_data_point.date
    if last_date.month == 12:
        date = datetime.date(last_date.year + 1, 1, 1)
        value = index_quarterly[-1].value
        result.append(DataPoint(date, value))
    else:
        date = datetime.date(last_date.year, last_date.month + 1, 1)
        value = index_quarterly[-1].value
        result.append(DataPoint(date, value))
    return result


def get_regions(regional_prices):
    regions = []
    for region in regional_prices:
        if region.category not in regions:
            regions.append(region.category)
    return regions


def get_regional_prices(flat_prices, regions):
    sorted_prices = []
    for region in regions:
        prices = list(filter(lambda x: x.category == region and x.value != 0, flat_prices))
        if prices[0].date == "2005K1":
            start_year = 2005
        elif prices[0].date == "1992K1":
            start_year = 1992
        else:
            raise ValueError("unexpected start")

        sorted_prices.append(RegionPrices(region, prices, start_year))
    return sorted_prices


def transform_regional_prices(regional_prices):
    for region in regional_prices:
        region.prices = quarterly_to_monthly(region.prices)
        region.prices = crop_value(region.prices, region.start_year)
        region.prices = adjust_for_inflation(region.prices, load_inflation(region.start_year))
    normalize_regional_prices(regional_prices)


def normalize_regional_prices(regional_prices):
    for region in regional_prices:
        start_value = region.prices[0].value
        region.prices = list(map(lambda p: DataPoint(p.date, p.value / start_value), region.prices))


def calculate_total_loan_cost_factor(interest_rates):
    result = []
    interest_margin = 2
    for interest in interest_rates:
        net_interest_rate = interest.value + interest_margin
        cost = interest_to_cost(net_interest_rate)
        result.append(DataPoint(interest.date, cost))
    return result


def calculate_marginal_cost_increase():
    marginal_cost_increase = []
    for i in range(16):
        r1 = i
        r2 = (i + 1)
        c1 = interest_to_cost(r1)
        c2 = interest_to_cost(r2)
        relative_cost_increase = c2 / c1
        cost_increase_percent = (relative_cost_increase - 1) * 100
        marginal_cost_increase.append(cost_increase_percent)
    return marginal_cost_increase


def interest_to_cost(interest):
    # Created from quadratic regression of values from sbanken loan calculator
    # Uses 30 year payback, 0.85 debt ratio
    return 1.01307 + 0.112859 * interest + 0.00696783 * interest * interest


# day -> month
def transform_interest_rates(interest_rates, min_year):
    for rate in interest_rates:
        rate.date = parse_date(rate.date)
    result = []
    for year in range(min_year, 2020):
        for month in range(1, 13):
            date = datetime.date(year, month, 1)
            result.append(DataPoint(date, find_interest_rate_for_day(date, interest_rates)))
    return result


def find_interest_rate_for_day(day, interest_rates):
    before_date = list(filter(lambda x: x.date <= day, interest_rates))
    before_date.sort(key=lambda r: r.date)
    return before_date[len(before_date) - 1].value


# yearly -> monthly
def transform_wage(wage):
    result = []
    for i in range(1, len(wage)):
        # start on year 1991 as value is denoted at end of year
        year = wage[i].date
        year_end = wage[i].value
        year_start = wage[i - 1].value
        increase_in_year = year_end - year_start
        avg_montly_increase = increase_in_year / 12
        for month in range(1, 13):
            # subtract 1 from month as date is at start
            value_for_month = year_start + avg_montly_increase * (month - 1)
            date = datetime.date(int(year), month, 1)
            result.append(DataPoint(date, value_for_month))
    return result


# yearly -> monthly
# TODO vurder å del på 100 på alle verdiene
def transform_inflation(inflation):
    result = []
    index_current = 100
    for inflation_for_year in inflation[0:]:
        year_start = index_current
        year_end = index_current * ((100 + inflation_for_year.value) / 100)
        index_current = year_end
        avg_monthly_change = (year_end - year_start) / 12
        for month in range(1, 13):
            date = datetime.date(inflation_for_year.date.year, month, 1)
            value = (year_start + avg_monthly_change * (month - 1))
            result.append(DataPoint(date, value))
    return result


def string_to_dates(data_points):
    return list(map(lambda x: DataPoint(datetime.date(int(x.date), 1, 1), x.value), data_points))


def crop_value(data, min_year):
    max_date = datetime.date(2019, 12, 1)
    min_date = datetime.date(min_year, 1, 1)
    return list(filter(lambda p: max_date >= p.date >= min_date, data))


def normalize(data):
    first_element_value = data[0].value
    return list(map(lambda p: DataPoint(p.date, p.value / first_element_value), data))


def adjust_for_inflation(data, inflation):
    result = []
    for i in range(0, len(data)):
        value = data[i].value / inflation[i].value
        result.append(DataPoint(data[i].date, value))
    return result
