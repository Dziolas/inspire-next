# -*- coding: utf-8 -*-
#
# This file is part of INSPIRE.
# Copyright (C) 2014, 2015 CERN.
#
# INSPIRE is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# INSPIRE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with INSPIRE. If not, see <http://www.gnu.org/licenses/>.
#
# In applying this licence, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization
# or submit itself to any jurisdiction.

"""MARC 21 model definition."""

from dojson import utils

from ..model import hep, hep2marc


@hep.over('edition', '^250..')
@utils.for_each_value
@utils.filter_values
def edition(self, key, value):
    """Edition Statement."""
    return {
        'edition': value.get('a')
    }


@hep2marc.over('250', 'edition')
@utils.for_each_value
@utils.filter_values
def edition2marc(self, key, value):
    """Edition Statement."""
    return {
        'a': value.get('edition'),
    }


@hep.over('imprint', '^260[_23].')
@utils.for_each_value
@utils.filter_values
def imprint(self, key, value):
    """Publication, Distribution, etc. (Imprint)."""
    return {
        'place': value.get('a'),
        'publisher': value.get('b'),
        'date': value.get('c'),
    }


@hep2marc.over('260', 'imprint')
@utils.for_each_value
@utils.filter_values
def imprint2marc(self, key, value):
    """Publication, Distribution, etc. (Imprint)."""
    return {
        'a': value.get('place'),
        'b': value.get('publisher'),
        'c': value.get('date'),
    }


@hep.over('defense_date', '^269..')
@utils.for_each_value
@utils.filter_values
def defense_date(self, key, value):
    """Date of defense of a thesis"""
    return {
        'date': value.get('c'),
    }


@hep2marc.over('269', 'defense_date')
@utils.for_each_value
@utils.filter_values
def defense_date2marc(self, key, value):
    """Date of defense of a thesis"""
    return {
        'c': value.get('date'),
    }


@hep.over('preprint_info', '^269..')
@utils.for_each_value
@utils.filter_values
def preprint_info(self, key, value):
    """Preprint info."""
    return {
        'date': value.get('c'),
    }


@hep2marc.over('269', 'preprint_info')
@utils.for_each_value
@utils.filter_values
def preprint_info2marc(self, key, value):
    """Preprint info."""
    return {
        'c': value.get('date'),
    }
