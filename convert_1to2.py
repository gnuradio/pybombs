#!/usr/bin/env python
#
# Copyright 2015-2016 Free Software Foundation, Inc.
#
# This file is part of PyBOMBS
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
"""
Conversion tool for PyBOMBS1 recipes to PyBOMBS2 style (YAML).
"""

import re
import os
import sys
import yaml

HEADER = """#
# This file is part of PyBOMBS
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

"""

input_file = sys.argv[1]
output_dir = sys.argv[2]
output_file = os.path.join(output_dir, os.path.basename(input_file))

print "Converting `{0}' => `{1}'".format(input_file, output_file)

# 1) Do some regexing on the raw file
input_data = open(input_file).read()
# Vars:
input_data = re.sub('^var\s+([a-z_]+)\s+=\s+(.*)$', 'vars:\n  \\1: \\2', input_data, flags=re.MULTILINE)
# Multiline crap:
input_data = re.sub("^([a-z_]+)\\s+{([^}]+)[\\s\n]+}", r"\1: |\2", input_data, flags=re.MULTILINE|re.DOTALL)
# Tabs don't work with YAML:
input_data = input_data.replace('\t', '    ')

# 2) Parse the rest as yaml
data = yaml.safe_load(input_data)
if data.get('depends'):
    data['depends'] = data['depends'].split(' ')
satisfy_keys = [x for x in data.keys() if x.startswith('satisfy')]
if len(satisfy_keys):
    data['satisfy'] = {}
    for k in satisfy_keys:
        satisfy_type = k.split('_')[1]
        data['satisfy'][satisfy_type] = data[k]
        data.pop(k)
if data.has_key('source'):
    data['source'] = re.sub(r'^([a-z]+)://(.*)', r'\1+\2', data['source'], count=1)

open(output_file, 'w').write(HEADER + yaml.dump(data, default_flow_style=False))
