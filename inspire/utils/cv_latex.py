# -*- coding: utf-8 -*-
#
# This file is part of INSPIRE.
# Copyright (C) 2015 CERN.
#
# INSPIRE is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# INSPIRE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with INSPIRE. If not, see <http://www.gnu.org/licenses/>.
#
# In applying this licence, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization
# or submit itself to any jurisdiction.

import re
import time

from invenio.base.globals import cfg


class MissingRequiredFieldError(LookupError):

    """Base class for exceptions in this module.
    The exception should be raised when the specific,
    required field doesn't exist in the record.
    """

    def _init_(self, field):
        self.field = field

    def _str_(self):
        return "Missing field: " + self.field


class Cv_latex(object):
    """Class used to output CV LaTex format.
    TODO Fix the citation number latex
    e.g %245 citations counted in INSPIRE as of 21 Aug 2015
    """

    def __init__(self, record):
        self.record = record
        self.arxiv_field = self._get_arxiv_field()

    def format(self):
        """Return CV LaTex export for single record."""
        formats = {
            'record': self._format_record,
        }
        return formats['record']()

    def _format_record(self):
        required_fields = ['title', 'author', 'arxiv']
        optional_fields = ['doi', 'publi_info', 'url']
        try:
            return self._format_entry(required_fields, optional_fields)
        except MissingRequiredFieldError as e:
            raise e

    def _format_entry(self, req, opt):
        """
        :raises: MissingRequiredFieldError
        """
        out = '%\cite{' + self._get_citation_key() + '}<br/>'
        out += r'\item%{' + self._get_citation_key() + '}<br/>'
        out += self._fetch_fields(req, opt) + '<br/>'
        return out

    def _get_citation_key(self):
        """Returns citation key for CV LaTex"""
        if 'system_control_number' in self.record:
            result = []
            citation_key = ''
            for field in self.record['system_control_number']:
                if 'institute' in field and \
                    (field['institute'] == 'INSPIRETeX' or
                     field['institute'] == 'SPIRESTeX'):
                    result.append(field)
            for key in result:
                if key['institute'] in ('INSPIRETeX', 'SPIRESTeX'):
                    if 'system_control_number' in key:
                        citation_key = key['system_control_number']
                    elif 'value' in key:
                        citation_key = key['value']
                    elif 'obsolete' in key:
                        citation_key = key['obsolete']
                    else:
                        citation_key = ''
                if not result:
                    return ''
            if isinstance(citation_key, list):
                for element in citation_key:
                    return element.replace(' ', '')
            else:
                return citation_key.replace(' ', '')
        else:
            return ''

    def _fetch_fields(self, req_fields, opt_fields=[]):
        fields = {
            'author': self._get_author,
            'title': self._get_title,
            'arxiv': self._get_arxiv,
            'doi': self._get_doi,
            'publi_info': self._get_publi_info,
            'url': self._get_url,
        }
        out = ''
        for field in req_fields:
            value = fields[field]()
            if value:
                out += self._format_output_row(field, value)
            # RAISE EXCEPTION HERE IF REQ FIELD IS MISSING
        for field in opt_fields:
            value = fields[field]()
            if value:
                out += self._format_output_row(field, value)
        return out

    def _format_output_row(self, field, value):
        out = ''
        if field == 'author':
            if len(value) == 1:
                out += u'&nbsp;&nbsp;\\\\{{}}{1}.<br/>'.format(field, value[0])
            elif len(value) > 8:
                out += u'&nbsp;&nbsp;\\\\{{}}{1}'.format(field, value[0])
                if 'collaboration' in self.record:
                    try:
                        if 'collaboration' in self.record['collaboration'][0]:
                            collaboration = self.record['collaboration'][0]['collaboration']
                            if 'Collaboration' in collaboration:
                                out += u' {\it et al.} [' + collaboration + '].<br/>'
                            else:
                                out += u' {\it et al.} [' + collaboration + ' Collaboration].<br/>'
                    except IndexError:
                        pass
                else:
                    out += u' {\it et al.}.<br/>'
            else:
                out += u'&nbsp;&nbsp;\\\\{{}}{} and {}.<br/>'.format(
                    ', '.join(value[:-1]), value[-1]
                )
        elif field == 'title':
            out += u'{1}<br/>'.format(field, value)
        elif field == 'publi_info':
            out += u'  \\\\{{}}{1}.'.format(field, value)
            if self._get_date():
                out += ' %(' + str(self._get_date()) + ')<br/>'
        elif field == 'arxiv':
            out += u'&nbsp;&nbsp;\\\\{{}}{1}.<br/>'.format(field, value)
        elif field == 'doi':
            out += u'&nbsp;&nbsp;&nbsp;&nbsp;\\\\{{}}{1}.<br/>'.format(
                field, value)
        elif field == 'url':
            out += u' %\href{{{1}}}{{HEP entry}}.<br/>'.format(field, value)
        return out

    def _get_arxiv_field(self):
        """Return arXiv field if exists"""
        if 'report_number' in self.record:
            for field in self.record['report_number']:
                if ('source' in field and field['source'] == 'arXiv') \
                    or 'arxiv_category' in field or \
                    ('primary' in field and
                        field['primary'].upper().startswith('ARXIV:')):
                    return field

    def _get_author(self):
        """Return list of name(s) of the author(s)."""
        re_last_first = re.compile(
            r'^(?P<last>[^,]+)\s*,\s*(?P<first_names>[^\,]*)(?P<extension>\,?.*)$'
        )
        re_initials = re.compile(r'(?P<initial>\w)([\w`\']+)?.?\s*')
        re_tildehyph = re.compile(
            ur'(?<=\.)~(?P<hyphen>[\u002D\u00AD\u2010-\u2014-])(?=\w)'
        )
        result = []
        if 'authors' in self.record:
            for author in self.record['authors']:
                if author['full_name']:
                    if isinstance(author['full_name'], list):
                        author_full_name = ' '.join(full_name for full_name
                                                    in author['full_name'])
                        first_last_match = re_last_first.search(
                            author_full_name)
                        if first_last_match:
                            first = re_initials.sub(
                                r'\g<initial>.~',
                                first_last_match.group('first_names')
                            )
                            first = re_tildehyph.sub(r'\g<hyphen>', first)
                            result.append(first +
                                          first_last_match.group('last') +
                                          first_last_match.group('extension'))
                    else:
                        first_last_match = re_last_first.search(
                            author['full_name'])
                        if first_last_match:
                            first = re_initials.sub(
                                r'\g<initial>.~',
                                first_last_match.group('first_names')
                            )
                            first = re_tildehyph.sub(r'\g<hyphen>', first)
                            result.append(first +
                                          first_last_match.group('last') +
                                          first_last_match.group('extension'))
        elif 'corporate_author' in self.record:
            if isinstance(self.record['corporate_author'], list):
                for corp_author in self.record['corporate_author']:
                    if 'corporate_author' in corp_author:
                        first_last_match = re_last_first.search(
                            corp_author['corporate_author'])
                        if first_last_match:
                            first = re_initials.sub(
                                r'\g<initial>.~',
                                first_last_match.group('first_names')
                            )
                            first = re_tildehyph.sub(r'\g<hyphen>', first)
                            result.append(first +
                                          first_last_match.group('last') +
                                          first_last_match.group('extension'))
            else:
                first_last_match = re_last_first.search(
                    self.record['corporate_author']
                    ['corporate_author']
                )
                if first_last_match:
                    first = re_initials.sub(
                        r'\g<initial>.~',
                        first_last_match.group('first_names')
                    )
                    first = re_tildehyph.sub(r'\g<hyphen>', first)
                    result.append(first +
                                  first_last_match.group('last') +
                                  first_last_match.group('extension'))
        return result

    def _get_title(self):
        """Return record titles"""
        record_title = ''
        if 'title' in self.record:
            if isinstance(self.record['title'], list):
                for title in self.record['title']:
                    if 'title' in title:
                        record_title = title['title']
                        break
            else:
                record_title = self.record['title']['title'].strip()
            return r"{\bf ``" + re.sub(
                r'(?<!\\)([#&%])', r'\\\1', record_title
            ) + "''}"
        else:
            return record_title

    def _get_publi_info(self):
        if 'publication_info' in self.record:
            journal_title, journal_volume, year, journal_issue, pages = \
                ('', '', '', '', '')
            for field in self.record['publication_info']:
                out = ''
                if 'journal_title' in field:
                    if isinstance(field['journal_title'], list):
                        journal_title = field['journal_title'][-1].replace(".", '.\\ ')
                    else:
                        journal_title = field['journal_title'].replace(".", '.\\ ')
                    if 'journal_volume' in field and not \
                            field['journal_title'] == 'Conf.Proc.':
                        journal_letter = ''
                        char_i = 0
                        for char in field['journal_volume']:
                            if char.isalpha():
                                char_i += 1
                            else:
                                break
                        journal_letter = field['journal_volume'][:char_i]
                        if journal_letter and journal_title != ' ':
                            journal_letter = ' ' + journal_letter
                        journal_volume = journal_letter + ' {\\bf ' + \
                            field['journal_volume'][char_i:] + '}'
                    if 'year' in field:
                        if isinstance(field['year'], list):
                            year = ' (' + field['year'][-1] + ')'
                        else:
                            year = ' (' + field['year'] + ')'
                    if 'journal_issue' in field:
                        if field['journal_issue']:
                            journal_issue = ', no. ' + field['journal_issue']
                    if 'page_artid' in field:
                        page_artid = ''
                        if field['page_artid']:
                            if isinstance(field['page_artid'], list):
                                    dashpos = field['page_artid'][-1].find('-')
                                    if dashpos > -1:
                                        page_artid = field['page_artid'][-1][:dashpos]
                                    else:
                                        page_artid = field['page_artid'][-1]
                            else:
                                dashpos = field['page_artid'].find('-')
                                if dashpos > -1:
                                    page_artid = field['page_artid'][:dashpos]
                                else:
                                    page_artid = field['page_artid']
                            pages = ', ' + page_artid
                    break
                else:
                    if 'pubinfo_freetext' in field and len(field) == 1:
                        return field['pubinfo_freetext']
            out += journal_title + journal_volume + journal_issue + \
                pages + year
            if out:
                return out

    def _get_url(self):
        return cfg['CFG_SITE_URL'] + '/record/' + \
            str(self.record['control_number'])

    def _get_arxiv(self):
        arxiv = ''
        if self.arxiv_field:
            if 'primary' in self.arxiv_field:
                arxiv = self.arxiv_field['primary']
                if 'arxiv_category' in self.arxiv_field:
                    arxiv += ' [' + self.arxiv_field['arxiv_category'] + ']'
        return arxiv

    def _get_doi(self):
        """Return doi"""
        if 'doi' in self.record:
            doi_list = []
            for doi in self.record['doi']:
                doi_list.append(doi['doi'])
            return ', '.join(doi for doi in list(set(doi_list)))
        else:
            return ''

    def _get_date(self):
        """Returns date looking for every case"""
        datestruct = ''
        if 'preprint_info' in self.record:
            for date in self.record['preprint_info']:
                if 'date' in date:
                    datestruct = self.parse_date(str(date['date']))
                break
            if datestruct:
                return self._format_date(datestruct)  # FIX ME ADD 0 IN THE DAY

        if self._get_arxiv_field():
            date = re.search('(\d+)',
                             self._get_arxiv_field()['primary']).groups()[0]
            if len(date) >= 4:
                year = date[0:2]
                if year > '90':
                    year = '19' + year
                else:
                    year = '20' + year
                date = year + date[2:4]  # FIX ME DONT ADD 00 AS A DAY
                date = self.parse_date(str(date))
                if date:
                    return self._format_date(date)

        if 'publication_info' in self.record:
            for field in self.record['publication_info']:
                if 'year' in field:
                    date = field['year']
                    if date:
                        datestruct = self.parse_date(str(date))
                    break
            if datestruct:
                return self._format_date(datestruct)

        if 'creation_modification_date' in self.record:
            for field in self.record['creation_modification_date']:
                date = field['creation_date']
                if date:
                    datestruct = self.parse_date(str(date))
                break
            if datestruct:
                return self._format_date(datestruct)

        if 'imprint' in self.record:
            for field in self.record['imprint']:
                if 'date' in field:
                    date = field['date']
                    if date:
                        datestruct = self.parse_date(str(date))
                    break
            if datestruct:
                return self._format_date(datestruct)

        if 'thesis' in self.record:
            for field in self.record['thesis']:
                if 'date' in field:
                    date = field['date']
                    if date:
                        datestruct = self.parse_date(str(date))
                    break
            if datestruct:
                return self._format_date(datestruct)
        return None

    def _format_date(self, datestruct):
        """Returns date formatted"""
        dummy_time = (0, 0, 44, 2, 320, 0)
        if len(datestruct) == 3:
            datestruct = tuple(datestruct[0:3]) + dummy_time
            return time.strftime("%b %-d, %Y", datestruct)
        elif len(datestruct) == 2:
            datestruct = tuple(datestruct[0:2]) + (1,) + dummy_time
            return time.strftime("%b %Y", datestruct)
        elif len(datestruct) == 1:
            return datestruct[0]
        return None

    def parse_date(self, datetext):
        """
        Reads in a date-string of either native spires (YYYYMMDD)
        or invenio style
        (YYYY-MM-DD). Then as much of the date as we have is returned
        in a tuple.
        @param datetext: date from record
        @type datetext: str
        @return: tuple of 1 or more integers, up to max (year, month, day).
            Otherwise None.
        """
        if datetext in [None, ""] or type(datetext) != str:
            return None
        datetext = datetext.strip()
        datetext = datetext.split(' ')[0]
        datestruct = []
        if "-" in datetext:
            # Looks like YYYY-MM-DD
            for date in datetext.split('-'):
                if date:
                    try:
                        datestruct.append(int(date))
                        continue
                    except ValueError:
                        pass
                break
        else:
            # Looks like YYYYMMDD
            try:
                # year - YYYY
                year = datetext[:4]
                if year == "":
                    return tuple(datestruct)
                datestruct.append(int(year))
                # month - MM
                month = datetext[4:6]
                if month == "":
                    return tuple(datestruct)
                datestruct.append(int(month))
                day = datetext[6:8]
                # day - DD
                if day == "":
                    return tuple(datestruct)
                datestruct.append(int(day))
            except ValueError:
                pass
        return tuple(datestruct)
