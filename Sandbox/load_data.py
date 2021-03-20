import csv
from pathlib import Path

from Sandbox.MultiValueDataPoint import MultiValueDataPoint
from Sandbox.RegionPrices import RegionPrices
from .DataPoint import DataPoint
import datetime


def load_national_prices():
    cutoff_date = datetime.date(2003, 1, 2)
    index_monthly = load_monthly_index()
    index_quarterly = load_quarterly_index(cutoff_date)
    index = transform_index(index_quarterly, index_monthly)
    index = crop_value(index)
    index = normalize(index)

    return adjust_for_inflation(index, load_inflation())


def load_regional_prices():
    # TODO transform quarterly -> monthly
    regional_prices_flat = load_multi_point_file("Boligindeks regionalt.csv", 0, 1, 2)
    regions = get_regions(regional_prices_flat)
    regional_prices = get_regional_prices(regional_prices_flat, regions)
    return regional_prices


def load_interest_rate():
    interest = load_file("renteutvikling fra 2001.csv", 0, 1)
    interest = transform_interest_rates(interest)

    return crop_value(interest)


def load_wage_growth():
    wage = load_file("lonnsvekst.csv", 0, 1)
    wage = transform_wage(wage)
    wage = crop_value(wage)
    wage = normalize(wage)

    return adjust_for_inflation(wage, load_inflation())


def load_inflation():
    inflation = load_file("lonnsvekst.csv", 0, 3)
    inflation = transform_inflation(inflation)
    inflation = crop_value(inflation)

    return normalize(inflation)


# total cost of loan as a multiple of price. With 0 net interes rate this will return 1.
def load_cost_factor_of_purchase():
    interest = load_interest_rate()
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
                result.append(MultiValueDataPoint(row[first_col_nr], row[second_col_nr], float((row[third_col_nr]).replace(",", "."))))
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
    result = []
    for i in range(0, len(index_quarterly)):
        quarter = index_quarterly[i]
        year = int(quarter.date[0:4])
        quarter_number = int(quarter.date[5])
        if i == 0:
            value_at_start_of_quarter = quarter.value
            value_at_end_of_quarter = quarter.value
        else:
            value_at_start_of_quarter = index_quarterly[i-1].value
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
        # TODO handle if needed
        raise RuntimeError ("handle this")
    else:
        date = datetime.date(last_date.year, last_date.month + 1, 1)
        value = index_quarterly[-1].value
        result.append(DataPoint(date, value))

    result = list(filter(lambda x: x.date < cutoff_date, result))

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


def calculate_total_loan_cost_factor(interest_rates):
    result = []
    interest_margin = 2
    loan_duration = 30
    loan_margin = 0.85
    for interest in interest_rates:
        net_interest_rate = interest.value + interest_margin
        interest_as_decimal = net_interest_rate / 100
        cost = 1 + 0.5 * loan_margin * loan_duration * interest_as_decimal
        result.append(DataPoint(interest.date, cost))
    return result


# day -> month
def transform_interest_rates(interest_rates):
    for rate in interest_rates:
        rate.date = parse_date(rate.date)
    result = []
    for year in range(1992, 2020):
        for month in range(1, 13):
            date = datetime.date(year, month, 1)
            result.append(DataPoint(date, find_interest_rate_for_day(date, interest_rates)))
    return result


def find_interest_rate_for_day(day, interest_rates):
    before_date = list(filter(lambda x: x.date <= day, interest_rates))
    before_date.sort(key=lambda r: r.date)
    return before_date[len(before_date)-1].value


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
    for inflation_for_year in inflation[1:]:
        year_start = index_current
        year_end = index_current * ((100 + inflation_for_year.value) / 100)
        index_current = year_end
        avg_monthly_change = (year_end - year_start) / 12
        for month in range(1, 13):
            date = datetime.date(int(inflation_for_year.date), month, 1)
            value = (year_start + avg_monthly_change * (month - 1))
            result.append(DataPoint(date, value))
    return result


def crop_value(data):
    max_date = datetime.date(2019, 12, 1)
    return list(filter(lambda p: p.date <= max_date, data))


def normalize(data):
    first_element_value = data[0].value
    return list(map(lambda p: DataPoint(p.date, p.value/first_element_value), data))


def adjust_for_inflation(data, inflation):
    result = []
    for i in range(0, len(data)):
        value = data[i].value / inflation[i].value
        result.append(DataPoint(data[i].date, value))
    return result
