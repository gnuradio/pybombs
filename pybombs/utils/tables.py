#
# Copyright 2016 Free Software Foundation, Inc.
#
# This file is part of GNU Radio
#
# PyBOMBS is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# PyBOMBS is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PyBOMBS; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
#
""" Utilities for printing tables """

from __future__ import print_function
from functools import reduce

def print_table(headers, data, col_order=None, sort_by=None):
    """
    Print a table.
    """
    def get_max_column_widths(cols, headers, data):
        return {col_id: reduce(lambda a, x: max(a, len(str(x[col_id]))), data, len(str(headers[col_id]))) for col_id in cols}
    def print_header(cols, headers, max_widths):
        hdr_len = 0
        for col_id in col_order:
            format_string = "{0:" + str(max_widths[col_id]) + "}  "
            hdr_title = format_string.format(headers[col_id])
            print(hdr_title, end="")
            hdr_len += len(str(hdr_title))
        print("")
        print("-" * hdr_len)
    def sort_data(data, cols, sort_by):
        return sorted(data, key=lambda k: k[sort_by])
    def print_data(cols, data, max_widths):
        for row in data:
            for col_id in cols:
                format_string = "{{0:{width}}}  ".format(width=max_widths[col_id])
                print(format_string.format(row[col_id]), end="")
            print("")
        print("")
    # Go, go, go!
    if col_order is None:
        col_order = headers.keys()
    max_widths = get_max_column_widths(col_order, headers, data)
    if sort_by is not None:
        data = sort_data(data, col_order, sort_by)
    print_header(col_order, headers, max_widths)
    print_data(col_order, data, max_widths)


if __name__ == "__main__":
    headers = {'h1': "Header 1", 'h2': "Header 2"}
    data = (
            {'h1': 'foo', 'h2': 'bar'},
            {'h1': 'baz', 'h2': 'zasdlfjasldkfjaskdfjasldkfj'},
    )
    print_table(headers, data)
    print_table(headers, data, ('h1', 'h2'))
    print_table(headers, data, ('h2', 'h1'), 'h1')
    print_table(headers, data, sort_by='h2')

