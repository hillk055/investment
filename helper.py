import time


class PortfolioManager:

    def __init__(self, portfolio):
        self.portfolio = portfolio

    def withdraw(self, amount, optimal_withdrawal_method):
        money_needed = amount
        current_index = 0

        while money_needed > 0 and current_index < len(optimal_withdrawal_method):

            method = optimal_withdrawal_method[current_index]
            asset = self.portfolio[method]

            # Handle list-type assets e.g. dividend_stocks (list of dicts)
            if isinstance(asset, list):
                for item in asset:
                    if money_needed <= 0:
                        break
                    if item['Value'] <= money_needed:
                        money_needed -= item['Value']
                        item['Value'] = 0
                    else:
                        item['Value'] -= money_needed
                        money_needed = 0

            # Handle single asset dictionaries (normal accounts)
            else:
                if asset['Value'] <= money_needed:
                    money_needed -= asset['Value']
                    asset['Value'] = 0
                else:
                    asset['Value'] -= money_needed
                    money_needed = 0

            current_index += 1

        return self.portfolio

class CapitalGainsTax:

    def __init__(self, tax_bracket='higher'):

        self.current_capital_gains = 0
        self.max_non_taxable = 3000
        self.tax_bracket = tax_bracket
        self.taxable_amount = 0

    def capital_gains_tax(self, capital_gain):

        self.current_capital_gains += capital_gain
        if self.current_capital_gains < self.max_non_taxable:
            return capital_gain
        else:
            taxable_amount = self.current_capital_gains - self.max_non_taxable
            self.current_capital_gains = 3000
            if self.tax_bracket.lower() == 'higher':
                return taxable_amount * 0.76 + self.current_capital_gains
            else:
                return taxable_amount * 0.82 + self.current_capital_gains


'''cp = CapitalGainsTax('higher')
non_taxable_amount = cp.capital_gains_tax(2000)
print(non_taxable_amount)
capital_gains_after_tax = cp.capital_gains_tax(2000)
print(capital_gains_after_tax)'''


class CalculateDiv:

    def __init__(self, values, tax_bracket='higher'):

        self.values = values
        self.tax_bracket = tax_bracket
        self.current_div = 0
        self.personal_allowance: int = 500
        self.div_return = 0

    @staticmethod
    def str_to_float(x):
        x = float(x.replace('%', ''))/100
        return x

    def calc_dividend(self):

        updated = []
        for index, val in enumerate(self.values['dividend_stocks']):

            x = val['Value'] * self.str_to_float(val['yield'])

            # Need to add the highest tax rate payer
            taxable_div = x - self.personal_allowance

            if self.tax_bracket.lower() == 'higher':
                dividends_after_tax = taxable_div * 0.6625
            elif self.tax_bracket.lower() == 'additional':
                pass
            else:
                dividends_after_tax = taxable_div * 0.9125
            if val['acc']:
                new_values = val['Value'] + dividends_after_tax + self.personal_allowance
            else:
                new_values = val['Value']
                self.div_return += dividends_after_tax + self.personal_allowance

            updated.append((index, new_values))
            self.personal_allowance = max(0, self.personal_allowance - x)

        for x, y in updated:
            self.values['dividend_stocks'][x]['Value'] = y
        return self.values['dividend_stocks'], self.div_return


portfolio = {'cash_isa': {'Value': 67_000, 'Tax Free': True, 'yield': '3.5%', 'income_type': 'capital_gains'},
                 'savings': {'Value': 214_109.000, 'Tax Free': False, 'yield': '3.5%', 'income_type': 'capital_gains'},
                 'current_account': {'Value': 22_440, 'Tax Free': False, 'yield': '0.01%', 'income_type': 'capital_gains'},
                 'pension': {'Value': 670_000, 'Tax Free': False, 'yield': '7.5%', 'income_type': 'income'},
                 'premium_bonds': {'Value': 50_000, 'Tax Free': True, 'yield': '3.5%', 'income_type': 'capital_gains'},
                 'dividend_stocks': [{'Value': 80_000, 'Tax Free': False, 'yield': '5%', 'income_type': 'income', 'acc': False}, {'Value': 80_000, 'Tax Free': False, 'yield': '5%', 'income_type': 'income', 'acc': True}]
                 }
def tax_with_ni(income):
    total_income = income
    total_tax_to_pay = 0
    total_ni_to_pay = 0

    # ---- PERSONAL ALLOWANCE ----
    personal_allowance = 12_570
    if income > 100_000:
        personal_allowance = max(0, personal_allowance - (income - 100_000) / 2)

    # ---- INCOME TAX ----
    if income > 125_140:
        total_tax_to_pay += (income - 125_140) * 0.45
        income = 125_140

    if 50_270 < income <= 125_140:
        total_tax_to_pay += (income - 50_270) * 0.40
        income = 50_270

    if personal_allowance < income <= 50_270:
        total_tax_to_pay += (income - personal_allowance) * 0.20

    # ---- NATIONAL INSURANCE ----
    # Reset income for NI, since NI doesn't use personal allowance adjustments
    ni_income = total_income

    if ni_income > 50_270:
        total_ni_to_pay += (50_270 - 12_570) * 0.08  # 8% between £12,570–£50,270
        total_ni_to_pay += (ni_income - 50_270) * 0.02  # 2% above £50,270
    elif ni_income > 12_570:
        total_ni_to_pay += (ni_income - 12_570) * 0.08

    # ---- TOTAL DEDUCTIONS ----
    take_home_pay = total_income - total_tax_to_pay - total_ni_to_pay

    return {
        "Income": total_income,
        "Tax": round(total_tax_to_pay, 2),
        "National Insurance": round(total_ni_to_pay, 2),
        "Net pay": round(take_home_pay, 2)
    }

def main():
    pass

if __name__ == "__main__":
    main()
