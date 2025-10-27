import time

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from tax import tax_with_ni, CapitalGainsTax, CalculateDiv, PortfolioManager
import math


class InvestmentAppreciation:

    def __init__(self, salary, properties: {}, portfolio, money_needed, other_assets):

        # Default Params

        self.rental_income: float = 0
        self.property_value: float = 0
        self.salary_end: int = 20
        self.salary: int = 0
        self.other_assets = other_assets

        # If no plans to sell property -> self.rental_income_end = math.inf
        self.rental_income_end: float = math.inf

        self.properties = properties
        if len(self.properties.keys()) != 0:
            for key, value in self.properties.items():
                if not value['Owned']:
                    continue
                self.rental_income += value['Rent']
                self.property_value += value['Value']

        self.state_pension = 12_500

        # Non-long term incomes (SALARY, RENTAL)
        # Salary can either be given as a list of upcoming salaries or a fixed value
        self.salary = salary

        if isinstance(self.salary, list):
            self.salary_end = len(self.salary)
        else:
            self.salary = [self.salary] * self.salary_end

        self.portfolio = portfolio
        self.money_needed = money_needed
        self.time_period = 20  # Years
        self.inflation: float = 0.04
        self.networth_values = []

        other_asset_value = sum([x['Value'] for x in self.other_assets.values()])
        self.portfolio_value = 0

        for asset, data in self.portfolio.items():
            if asset == 'dividend_stocks':
                self.portfolio_value += sum(stock['Value'] for stock in data)
            else:
                # single value
                self.portfolio_value += data['Value']

        networth = self.property_value + other_asset_value + self.portfolio_value

        self.networth_values.append(networth)
        self.five_year_cost = 8000

    @staticmethod
    def convert_yield(x):

        perc_yield = x['yield']
        if isinstance(perc_yield, str) and '%' in perc_yield:
            perc_yield = perc_yield.replace('%', '')
            perc_yield = float(perc_yield) / 100
            total_yield = perc_yield * x['Value']

            return round(total_yield, 2)
        return perc_yield

    @staticmethod
    def calc_prem_bonds(x, acc=True, max_holding: int = 50_000):
        """
        Handles premium bond growth. Max holding is £50,000.
        If gains push it over £50k, overflow is returned for reinvestment elsewhere.
        """

        capital_gain = InvestmentAppreciation.convert_yield(x)

        if acc:
            new_value = x['Value'] + capital_gain

            # Case 1: Exceeds max allowable holding
            if new_value >= max_holding:
                overflow = new_value - max_holding
                x['Value'] = max_holding
                return x, overflow

            # Case 2: Under max holding → just grow normally
            else:
                x['Value'] = new_value
                return x, 0

        # If not accumulating, return full gain and unchanged value
        return x, capital_gain

    @staticmethod
    def convert_str_float(x):
        perc_yield = x['yield']
        if isinstance(perc_yield, str) and '%' in perc_yield:
            perc_yield = perc_yield.replace('%', '')
            perc_yield = float(perc_yield) / 100
            return perc_yield
        return x

    def property(self, i):

        if self.rental_income is None:
            return 0
        if i == self.rental_income_end:
            return

    def loop(self):

        """
        Assumptions:
        1) Interest added at the end of the year, lower bond estimate for savings
        2) All costs deducted before interest paid, in reality accumulated on a daily basis so interest amounts paid
        would be higher than calculated here.

        """
        networth = []

        # List in order of optimal payment methods
        withdrawal_order = ['current_account', 'cash_isa', 'savings', 'dividend_stocks', 'premium_bonds', 'pension']

        current_index = 0
        for i in range(1, 20):
            # Find the account to take the required money out of.
            money_needed = self.money_needed

            # Define salary if user has one
            try:
                salary = self.salary[i]
            except IndexError:
                salary = 0

            dv = CalculateDiv(self.portfolio, tax_bracket='higher')
            new, dividend_income = dv.calc_dividend()
            income_non_taxable = 0
            capital_gains_non_taxable = 0

            salary += self.rental_income + self.state_pension
            income_non_taxable += tax_with_ni(salary + self.rental_income + dividend_income)['Net pay']
            income_non_taxable += dividend_income

            # While the value of the current payment method is not enough shift to the next one and try again

            manager = PortfolioManager(self.portfolio)
            self.portfolio = manager.withdraw(45_000, withdrawal_order)

            # Value the capital gains, income and dividends all taxed differently for each asset
            # For every year reset the capital gains
            income_non_taxable = 0
            capital_gains_non_taxable = 0

            for asset, values in self.portfolio.items():

                # Calculate total capital gains and apply tax to yield capital gains net
                if asset == 'premium_bonds':
                    new_x, bond_gain = self.calc_prem_bonds(self.portfolio[asset])
                    capital_gains_non_taxable += bond_gain
                    self.portfolio[asset] = new_x

                elif asset == 'dividend_stocks':
                    continue

                else:
                    if values['Tax Free']:
                        self.portfolio[asset]['Value'] += self.convert_yield(self.portfolio[asset])
                    else:
                        # This has to get taxed
                        self.portfolio[asset]['Value'] += self.convert_yield(self.portfolio[asset])

            networth_this_year = income_non_taxable + capital_gains_non_taxable
            if i % 5 == 0 and i != 0:
                networth_this_year -= self.five_year_cost

            for asset, data in self.portfolio.items():
                if asset == 'dividend_stocks':
                    networth_this_year += sum(stock['Value'] for stock in data)
                else:
                    # single value
                    networth_this_year += data['Value']

            networth_this_year += sum([x['Value'] for x in self.other_assets.values()])
            networth_this_year += salary
            networth_this_year += self.property_value

            self.networth_values.append(networth_this_year)

        return self.networth_values


def main():
    sal1 = [78_000, 111_000, 108_000, 137_000, 137_000, 50_000, 36_000]
    sal2 = [0, 0]
    sal1 = [x * 1.4 for x in sal1]
    properties = {'property1': {'Owned': True, 'Rent': 0, 'Value': 0},
                  'property2': {'Owned': True, 'Rent': 9600, 'Value': 0}}
    other_assets = {'cars': {'Owned': True, 'Value': 0}}

    portfolio = {'cash_isa': {'Value': 67_000, 'Tax Free': True, 'yield': '3.5%', 'income_type': 'capital_gains'},
                 'savings': {'Value': 214_109.000, 'Tax Free': False, 'yield': '3.5%', 'income_type': 'capital_gains'},
                 'current_account': {'Value': 22_440, 'Tax Free': False, 'yield': '0.01%',
                                     'income_type': 'capital_gains'},
                 'pension': {'Value': 670_000, 'Tax Free': False, 'yield': '7.5%', 'income_type': 'income'},
                 'premium_bonds': {'Value': 50_000, 'Tax Free': True, 'yield': '3.5%', 'income_type': 'capital_gains'},
                 'dividend_stocks': [
                     {'Value': 80_000, 'Tax Free': False, 'yield': '5%', 'income_type': 'income', 'acc': False},
                     {'Value': 80_000, 'Tax Free': False, 'yield': '5%', 'income_type': 'income', 'acc': True}]
                 }

    inv = InvestmentAppreciation(portfolio=portfolio,
                                 salary=sal1,
                                 properties=properties,
                                 money_needed=45_000,
                                 other_assets=other_assets)

    inv2 = InvestmentAppreciation(portfolio=portfolio,
                                  salary=sal2,
                                  properties=properties,
                                  money_needed=45_000,
                                  other_assets=other_assets)
    inflation = 0.04
    nets = inv.loop()
    nets2 = inv2.loop()
    nets = [x * (1-inflation)**pos for pos, x in enumerate(nets, start=1)]
    nets2 = [x * (1-inflation)**pos for pos, x in enumerate(nets2, start=1)]
    print(nets)
    print(nets2)
    ''
    '''inv2 = InvestmentAppreciation(portfolio=portfolio, salary=sal2, property_metrics=properties, money_needed=45_000)

    nets2 = inv2.loop()
    print(nets)
    print(nets2)
    plt.plot(nets)
    plt.plot(nets2)
    plt.show()'''


if __name__ == "__main__":
    main()import time

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from tax import tax_with_ni, CapitalGainsTax, CalculateDiv, PortfolioManager
import math


class InvestmentAppreciation:

    def __init__(self, salary, properties: {}, portfolio, money_needed, other_assets):

        # Default Params

        self.rental_income: float = 0
        self.property_value: float = 0
        self.salary_end: int = 20
        self.salary: int = 0
        self.other_assets = other_assets

        # If no plans to sell property -> self.rental_income_end = math.inf
        self.rental_income_end: float = math.inf

        self.properties = properties
        if len(self.properties.keys()) != 0:
            for key, value in self.properties.items():
                if not value['Owned']:
                    continue
                self.rental_income += value['Rent']
                self.property_value += value['Value']

        self.state_pension = 12_500

        # Non-long term incomes (SALARY, RENTAL)
        # Salary can either be given as a list of upcoming salaries or a fixed value
        self.salary = salary

        if isinstance(self.salary, list):
            self.salary_end = len(self.salary)
        else:
            self.salary = [self.salary] * self.salary_end

        self.portfolio = portfolio
        self.money_needed = money_needed
        self.time_period = 20  # Years
        self.inflation: float = 0.04
        self.networth_values = []

        other_asset_value = sum([x['Value'] for x in self.other_assets.values()])
        self.portfolio_value = 0

        for asset, data in self.portfolio.items():
            if asset == 'dividend_stocks':
                self.portfolio_value += sum(stock['Value'] for stock in data)
            else:
                # single value
                self.portfolio_value += data['Value']

        networth = self.property_value + other_asset_value + self.portfolio_value

        self.networth_values.append(networth)
        self.five_year_cost = 8000

    @staticmethod
    def convert_yield(x):

        perc_yield = x['yield']
        if isinstance(perc_yield, str) and '%' in perc_yield:
            perc_yield = perc_yield.replace('%', '')
            perc_yield = float(perc_yield) / 100
            total_yield = perc_yield * x['Value']

            return round(total_yield, 2)
        return perc_yield

    @staticmethod
    def calc_prem_bonds(x, acc=True, max_holding: int = 50_000):
        """
        Handles premium bond growth. Max holding is £50,000.
        If gains push it over £50k, overflow is returned for reinvestment elsewhere.
        """

        capital_gain = InvestmentAppreciation.convert_yield(x)

        if acc:
            new_value = x['Value'] + capital_gain

            # Case 1: Exceeds max allowable holding
            if new_value >= max_holding:
                overflow = new_value - max_holding
                x['Value'] = max_holding
                return x, overflow

            # Case 2: Under max holding → just grow normally
            else:
                x['Value'] = new_value
                return x, 0

        # If not accumulating, return full gain and unchanged value
        return x, capital_gain

    @staticmethod
    def convert_str_float(x):
        perc_yield = x['yield']
        if isinstance(perc_yield, str) and '%' in perc_yield:
            perc_yield = perc_yield.replace('%', '')
            perc_yield = float(perc_yield) / 100
            return perc_yield
        return x

    def property(self, i):

        if self.rental_income is None:
            return 0
        if i == self.rental_income_end:
            return

    def loop(self):

        """
        Assumptions:
        1) Interest added at the end of the year, lower bond estimate for savings
        2) All costs deducted before interest paid, in reality accumulated on a daily basis so interest amounts paid
        would be higher than calculated here.

        """
        networth = []

        # List in order of optimal payment methods
        withdrawal_order = ['current_account', 'cash_isa', 'savings', 'dividend_stocks', 'premium_bonds', 'pension']

        current_index = 0
        for i in range(1, 20):
            # Find the account to take the required money out of.
            money_needed = self.money_needed

            # Define salary if user has one
            try:
                salary = self.salary[i]
            except IndexError:
                salary = 0

            dv = CalculateDiv(self.portfolio, tax_bracket='higher')
            new, dividend_income = dv.calc_dividend()
            income_non_taxable = 0
            capital_gains_non_taxable = 0

            salary += self.rental_income + self.state_pension
            income_non_taxable += tax_with_ni(salary + self.rental_income + dividend_income)['Net pay']
            income_non_taxable += dividend_income

            # While the value of the current payment method is not enough shift to the next one and try again

            manager = PortfolioManager(self.portfolio)
            self.portfolio = manager.withdraw(45_000, withdrawal_order)

            # Value the capital gains, income and dividends all taxed differently for each asset
            # For every year reset the capital gains
            income_non_taxable = 0
            capital_gains_non_taxable = 0

            for asset, values in self.portfolio.items():

                # Calculate total capital gains and apply tax to yield capital gains net
                if asset == 'premium_bonds':
                    new_x, bond_gain = self.calc_prem_bonds(self.portfolio[asset])
                    capital_gains_non_taxable += bond_gain
                    self.portfolio[asset] = new_x

                elif asset == 'dividend_stocks':
                    continue

                else:
                    if values['Tax Free']:
                        self.portfolio[asset]['Value'] += self.convert_yield(self.portfolio[asset])
                    else:
                        # This has to get taxed
                        self.portfolio[asset]['Value'] += self.convert_yield(self.portfolio[asset])

            networth_this_year = income_non_taxable + capital_gains_non_taxable
            if i % 5 == 0 and i != 0:
                networth_this_year -= self.five_year_cost

            for asset, data in self.portfolio.items():
                if asset == 'dividend_stocks':
                    networth_this_year += sum(stock['Value'] for stock in data)
                else:
                    # single value
                    networth_this_year += data['Value']

            networth_this_year += sum([x['Value'] for x in self.other_assets.values()])
            networth_this_year += salary
            networth_this_year += self.property_value

            self.networth_values.append(networth_this_year)

        return self.networth_values


def main():
    sal1 = [78_000, 111_000, 108_000, 137_000, 137_000, 50_000, 36_000]
    sal2 = [0, 0]
    sal1 = [x * 1.4 for x in sal1]
    properties = {'property1': {'Owned': True, 'Rent': 0, 'Value': 0},
                  'property2': {'Owned': True, 'Rent': 9600, 'Value': 0}}
    other_assets = {'cars': {'Owned': True, 'Value': 0}}

    portfolio = {'cash_isa': {'Value': 67_000, 'Tax Free': True, 'yield': '3.5%', 'income_type': 'capital_gains'},
                 'savings': {'Value': 214_109.000, 'Tax Free': False, 'yield': '3.5%', 'income_type': 'capital_gains'},
                 'current_account': {'Value': 22_440, 'Tax Free': False, 'yield': '0.01%',
                                     'income_type': 'capital_gains'},
                 'pension': {'Value': 670_000, 'Tax Free': False, 'yield': '7.5%', 'income_type': 'income'},
                 'premium_bonds': {'Value': 50_000, 'Tax Free': True, 'yield': '3.5%', 'income_type': 'capital_gains'},
                 'dividend_stocks': [
                     {'Value': 80_000, 'Tax Free': False, 'yield': '5%', 'income_type': 'income', 'acc': False},
                     {'Value': 80_000, 'Tax Free': False, 'yield': '5%', 'income_type': 'income', 'acc': True}]
                 }

    inv = InvestmentAppreciation(portfolio=portfolio,
                                 salary=sal1,
                                 properties=properties,
                                 money_needed=45_000,
                                 other_assets=other_assets)

    inv2 = InvestmentAppreciation(portfolio=portfolio,
                                  salary=sal2,
                                  properties=properties,
                                  money_needed=45_000,
                                  other_assets=other_assets)
    inflation = 0.04
    nets = inv.loop()
    nets2 = inv2.loop()
    nets = [x * (1-inflation)**pos for pos, x in enumerate(nets, start=1)]
    nets2 = [x * (1-inflation)**pos for pos, x in enumerate(nets2, start=1)]
    print(nets)
    print(nets2)
    ''
    '''inv2 = InvestmentAppreciation(portfolio=portfolio, salary=sal2, property_metrics=properties, money_needed=45_000)

    nets2 = inv2.loop()
    print(nets)
    print(nets2)
    plt.plot(nets)
    plt.plot(nets2)
    plt.show()'''


if __name__ == "__main__":
    main()
