#!/usr/bin/env python3

# gnucash-csv2html -- Convert CSV files exported by GnuCash to HTML format
# Copyright (C) 2019  Star Brilliant
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import argparse
import csv
import decimal
import enum
import html
import re
import sys
import typing
from typing import *


def print_entry(fo: typing.TextIO, entry: Optional[List[str]], splits: List[List[str]]) -> None:
    if entry is not None and len(splits) == 2 and not (splits[0][1] or splits[0][2] or splits[1][1] or splits[1][2]):
        entry[5] = splits[1][3]
        fo.write('        <tr class="{}" name="transaction-{}"><td class="col-date">{}</td><td class="col-num">{}</td><td class="col-description">{}</td><td class="col-transfer">{}</td><td class="col-debit">{}</td><td class="col-credit">{}</td><td class="col-balance">{}</td><td class="col-rate-price">{}</td></tr>\n'.format(*entry))
    else:
        if entry is not None:
            fo.write('        <tr class="{}" name="transaction-{}"><td class="col-date">{}</td><td class="col-num">{}</td><td class="col-description">{}</td><td class="col-transfer">{}</td><td class="col-debit">{}</td><td class="col-credit">{}</td><td class="col-balance">{}</td><td class="col-rate-price">{}</td></tr>\n'.format(*entry))
        for split in splits:
            fo.write('        <tr class="{}"><td class="col-date"></td><td class="col-action">{}</td><td class="col-memo">{}</td><td class="col-account">{}</td><td class="col-debit">{}</td><td class="col-credit">{}</td><td class="col-balance"></td><td class="col-rate-price">{}</td></tr>\n'.format(*split))


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description='Convert CSV files exported by GnuCash to HTML format.')
    parser.add_argument('input_csv', help='input CSV file')
    parser.add_argument('output_html', help='output HTML file')
    parser.add_argument('--credit', action='store_true', help='invert the sign of running balance')
    parser.add_argument('--script', action='append', default=[], metavar='JS_FILE', help='include JavaScript')
    parser.add_argument('--style', action='append', default=[], metavar='CSS_FILE', help='include CSS stylesheet')
    parser.add_argument('--title', help='title of the page')
    args = parser.parse_args()

    fi = open(argv[1], 'r', encoding='utf-8-sig', errors='replace')
    reader = csv.DictReader(fi, dialect='excel')
    fo = open(argv[2], 'w', encoding='utf-8')
    fo.write('<!DOCTYPE html>\n')
    fo.write('<!-- Generated by gnucash-csv2html              -->\n')
    fo.write('<!-- https://github.com/m13253/gnucash-csv2html -->\n')
    fo.write('<html>\n')
    fo.write('  <head>\n')
    fo.write('    <meta charset="utf-8" />\n')

    if args.title is not None:
        fo.write('    <title>{}</title>\n'.format(html.escape(args.title)))

    fo.write('    <style type="text/css">\n')
    fo.write('      body { margin: 0px; }\n')
    fo.write('      h1.ledger { font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 18pt; line-height: 1.375; font-weight: bold; margin: 6pt 6pt 6pt 6pt; }\n')
    fo.write('      table.ledger { border-collapse: collapse; font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; line-height: 1.375; width: 100%; }\n')
    fo.write('      table.ledger thead th { break-inside: avoid; font-weight: normal; padding: 0px 0.5em; page-break-inside: avoid; vertical-align: top; }\n')
    fo.write('      table.ledger thead th.col-date { border-top: 1.5pt solid; border-bottom: 1.5pt solid; }\n')
    fo.write('      table.ledger thead th.col-num { border-top: 1.5pt solid; border-bottom: 0.75pt solid; }\n')
    fo.write('      table.ledger thead th.col-action { border-bottom: 1.5pt solid; }\n')
    fo.write('      table.ledger thead th.col-description { border-top: 1.5pt solid; border-bottom: 0.75pt solid; }\n')
    fo.write('      table.ledger thead th.col-memo { border-bottom: 1.5pt solid; }\n')
    fo.write('      table.ledger thead th.col-transfer { border-top: 1.5pt solid; border-bottom: 0.75pt solid; }\n')
    fo.write('      table.ledger thead th.col-account { border-bottom: 1.5pt solid; }\n')
    fo.write('      table.ledger thead th.col-debit { border-top: 1.5pt solid; border-bottom: 1.5pt solid; border-right: 0.75pt solid; }\n')
    fo.write('      table.ledger thead th.col-credit { border-top: 1.5pt solid; border-bottom: 1.5pt solid; }\n')
    fo.write('      table.ledger thead th.col-balance { border-top: 1.5pt solid; border-bottom: 1.5pt solid; }\n')
    fo.write('      table.ledger thead th.col-rate-price { border-top: 1.5pt solid; border-bottom: 1.5pt solid; }\n')
    fo.write('      table.ledger thead th.col-rate-price div.align-block { display: inline-block; text-align: left; }\n')
    fo.write('      table.ledger tbody td { break-inside: avoid; padding: 0px 0.5em; page-break-inside: avoid; vertical-align: top; }\n')
    fo.write('      table.ledger tbody tr.row-entry-odd td { border-top: 0.75pt solid; border-bottom: 0.75pt solid; }\n')
    fo.write('      table.ledger tbody tr.row-entry-even td { border-top: 0.75pt solid; border-bottom: 0.75pt solid; }\n')
    fo.write('      table.ledger tbody tr:last-child td { border-bottom: 1.5pt solid; }\n')
    fo.write('      table.ledger tbody tr.row-split-first { break-before: avoid; page-break-before: avoid; }\n')
    fo.write('      table.ledger tbody tr.row-split-first td.col-date { border-top: none; }\n')
    fo.write('      table.ledger tbody tr.row-split-rest { break-before: avoid; page-break-before: avoid; }\n')
    fo.write('      table.ledger tbody tr.row-split-rest td { border-top: 0.75pt solid #999999; }\n')
    fo.write('      table.ledger tbody tr.row-split-rest td.col-date { border-top: none; }\n')
    fo.write('      table.ledger .col-date { text-align: right; white-space: pre; }\n')
    fo.write('      table.ledger .col-num { text-align: left; white-space: pre; }\n')
    fo.write('      table.ledger .col-action { text-align: right; white-space: pre; }\n')
    fo.write('      table.ledger .col-description { text-align: left; white-space: pre-wrap; width: 100%; }\n')
    fo.write('      table.ledger .col-memo { text-align: left; white-space: pre-wrap; width: 100%; }\n')
    fo.write('      table.ledger .col-transfer { text-align: right; white-space: pre; }\n')
    fo.write('      table.ledger .col-account { text-align: right; white-space: pre; }\n')
    fo.write('      table.ledger .col-debit { border-right: 0.75pt solid; text-align: right; white-space: pre; }\n')
    fo.write('      table.ledger .col-credit { text-align: right; white-space: pre; }\n')
    fo.write('      table.ledger .col-balance { text-align: right; white-space: pre; }\n')
    fo.write('      table.ledger .col-rate-price { text-align: right; white-space: pre; }\n')
    fo.write('      table.ledger span.symbol { color: #999999; }\n')
    fo.write('      table.ledger span.negative-symbol { color: #999999; }\n')
    fo.write('      table.ledger span.negative { font-weight: bold; }\n')
    fo.write('      @media not print {\n')
    fo.write('        table.ledger thead { background-color: #96b183; }\n')
    fo.write('        table.ledger tbody tr.row-entry-odd { background-color: #bfdeb9; }\n')
    fo.write('        table.ledger tbody tr.row-entry-even { background-color: #f6ffda; }\n')
    fo.write('        table.ledger tbody tr.row-split-first { background-color: #ede7d3; }\n')
    fo.write('        table.ledger tbody tr.row-split-first td.col-date { background-color: white; }\n')
    fo.write('        table.ledger tbody tr.row-split-rest { background-color: #ede7d3; }\n')
    fo.write('        table.ledger tbody tr.row-split-rest td.col-date { background-color: white; }\n')
    fo.write('        table.ledger span.symbol { color: #777777; }\n')
    fo.write('        table.ledger span.negative-symbol { color: #974e3d; }\n')
    fo.write('        table.ledger span.negative { color: #a40000; font-weight: normal; }\n')
    fo.write('      }\n')
    fo.write('      @media print {\n')
    fo.write('        table.ledger { font-size: 9pt; }\n')
    fo.write('      }\n')
    fo.write('      @page { margin: 1cm; }\n')
    fo.write('    </style>\n')

    for style in args.style:
        fo.write('    <link rel="stylesheet" type="text/css" href="{}" />\n'.format(html.escape(style)))

    fo.write('  </head>\n')
    fo.write('  <body>\n')

    if args.title is not None:
        fo.write('    <h1 class="ledger">{}</h1>\n'.format(html.escape(args.title)))

    fo.write('    <table class="ledger">\n')
    fo.write('      <thead>\n')
    fo.write('        <tr><th class="col-date" rowspan="2">Date</th><th class="col-num">Num</th><th class="col-description">Description</th><th class="col-transfer">Transfer</th><th class="col-debit" rowspan="2">Debit</th><th class="col-credit" rowspan="2">Credit</th><th class="col-balance" rowspan="2">Balance</th><th class="col-rate-price" rowspan="2"><div class="align-block">Rate/<br />Price</div></th></tr>\n')
    fo.write('        <tr><th class="col-action">Action</th><th class="col-memo">Memo</th><th class="col-account">Account</th></tr>\n')
    fo.write('      </thead>\n')
    fo.write('      <tbody>\n')

    balance: Dict[str, decimal.Decimal] = {}
    entry: Optional[List[str]] = None
    splits: List[List[str]] = []
    is_entry_odd = False

    for row in reader:
        row_transaction_id = row.get('Transaction ID', '') or ''

        if row_transaction_id:
            if len(splits) != 0:
                print_entry(fo, entry, splits)

            row_date = row.get('Date', '') or ''
            row_num = row.get('Number', '') or ''
            row_description = row.get('Description', '') or ''
            row_action = row.get('Action', '') or ''
            row_memo = row.get('Memo', '') or ''
            row_account = row.get('Full Account Name', '') or ''
            row_amount_with_sym = row.get('Amount With Sym', '') or ''
            row_amount_num = row.get('Amount Num.', '') or ''
            row_rate_price = row.get('Rate/Price', '') or ''

            amount_is_negative = row_amount_num.startswith('-') or (row_amount_num.startswith('(') and row_amount_num.endswith(')'))
            amount_abs = re.sub('[^.\\d]', '', row_amount_num)
            amount_symbol = re.sub('[- (),.\\d]', '', row_amount_with_sym)
            amount_decimal: Optional[decimal.Decimal] = None
            if amount_abs:
                amount_decimal = decimal.Decimal(amount_abs)

            if amount_decimal is None or amount_decimal.is_zero():
                row_debit = ''
                row_credit = ''
            elif amount_is_negative:
                row_debit = ''
                row_credit = '<span class="symbol">{}</span>{:,}'.format(html.escape(amount_symbol), amount_decimal)
                if row_account in balance:
                    if args.credit:
                        balance[row_account] += amount_decimal
                    else:
                        balance[row_account] -= amount_decimal
                else:
                    if args.credit:
                        balance[row_account] = amount_decimal
                    else:
                        balance[row_account] = -amount_decimal
            else:
                row_debit = '<span class="symbol">{}</span>{:,}'.format(html.escape(amount_symbol), amount_decimal)
                row_credit = ''
                if row_account in balance:
                    if args.credit:
                        balance[row_account] -= amount_decimal
                    else:
                        balance[row_account] += amount_decimal
                else:
                    if args.credit:
                        balance[row_account] = -amount_decimal
                    else:
                        balance[row_account] = amount_decimal
            if balance[row_account] < 0:
                row_balance = '<span class="negative-symbol">{}</span><span class="negative">{:,}</span>'.format(html.escape(amount_symbol), balance[row_account])
            else:
                row_balance = '<span class="symbol">{}</span>{:,}'.format(html.escape(amount_symbol), balance[row_account])

            is_entry_odd = not is_entry_odd
            entry = ['row-entry-odd' if is_entry_odd else 'row-entry-even', html.escape(row_transaction_id), html.escape(row_date), html.escape(row_num), html.escape(row_description), '', row_debit, row_credit, row_balance, html.escape(row_rate_price)]
            splits = [['row-split-first', html.escape(row_action), html.escape(row_memo), html.escape(row_account), row_debit, row_credit, html.escape(row_rate_price)]]

        else:
            row_action = row.get('Action', '') or ''
            row_memo = row.get('Memo', '') or ''
            row_account = row.get('Full Account Name', '') or ''
            row_amount_with_sym = row.get('Amount With Sym', '') or ''
            row_amount_num = row.get('Amount Num.', '') or ''
            row_rate_price = row.get('Rate/Price', '') or ''

            amount_is_negative = row_amount_num.startswith('-') or (row_amount_num.startswith('(') and row_amount_num.endswith(')'))
            amount_abs = re.sub('[^.\\d]', '', row_amount_num)
            amount_symbol = re.sub('[- (),.\\d]', '', row_amount_with_sym)
            amount_decimal = None
            if amount_abs:
                amount_decimal = decimal.Decimal(amount_abs)

            if amount_decimal is None or amount_decimal.is_zero():
                row_debit = ''
                row_credit = ''
            elif amount_is_negative:
                row_debit = ''
                row_credit = '<span class="symbol">{}</span>{:,}'.format(html.escape(amount_symbol), amount_decimal)
            else:
                row_debit = '<span class="symbol">{}</span>{:,}'.format(html.escape(amount_symbol), amount_decimal)
                row_credit = ''

            splits.append(['row-split-rest', html.escape(row_action), html.escape(row_memo), html.escape(row_account), row_debit, row_credit, html.escape(row_rate_price)])

    fi.close()
    if len(splits) != 0:
        print_entry(fo, entry, splits)

    fo.write('      </tbody>\n')
    fo.write('    </table>\n')

    for script in args.script:
        fo.write('    <script language="javascript" src="{}"></script>\n'.format(html.escape(script)))

    fo.write('  </body>\n')
    fo.write('</html>\n')
    fo.close()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
