# -*- coding: utf-8 -*-
# This file is part of INSPIRE.
# Copyright (C) 2015 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Implements a workflow for testing."""


from invenio_oaiharvester.tasks.records import convert_record_to_json

from invenio_deposit.models import DepositionType
from invenio_workflows.definitions import RecordWorkflow
from invenio_workflows.tasks.logic_tasks import (
    workflow_if,
    workflow_else,
)


from invenio_workflows.tasks.workflows_tasks import log_info

from inspire.dojson.hep import hep2marc

from inspire.modules.converter.tasks import convert_record

from inspire.modules.workflows.tasks.classifier import (
    filter_core_keywords,
    classify_paper,
)
from inspire.modules.workflows.tasks.matching import(
    exists_in_inspire_or_rejected,
    exists_in_holding_pen,
    save_identifiers_to_kb,
    delete_self_and_stop_processing,
    arxiv_set_category_field
)
from inspire.modules.workflows.tasks.submission import halt_record_with_action

from inspire.modules.workflows.models import Payload, create_payload
from inspire.modules.workflows.tasks.actions import (
    was_approved,
    add_core,
)
from inspire.modules.oaiharvester.tasks.arxiv import (
    arxiv_plot_extract,
    arxiv_fulltext_download,
    arxiv_author_list,
)
# from inspire.modules.refextract.tasks import extract_journal_info
from inspire.modules.predicter.tasks import (
    guess_coreness
)
from inspire.modules.workflows.tasks.submission import (
    send_robotupload,
    finalize_record_sip,
)


class harvesting_fixture(RecordWorkflow, DepositionType):

    """A test workflow for the Payload class."""

    model = Payload

    workflow = [
        # First we perform conversion from OAI-PMH XML to MARCXML
        convert_record("oaiarXiv2inspire_nofilter.xsl"),

        # Then we convert from MARCXML to SmartJSON object
        # TODO: Use DOJSON when we are ready to switch from bibfield
        convert_record_to_json,
        create_payload,
        workflow_if(exists_in_inspire_or_rejected()),
        [
            delete_self_and_stop_processing,
            # update_existing_record_oaiharvest(),
        ],
        workflow_else,
        [
            workflow_if(exists_in_holding_pen("harvesting_fixture_kb")),
            [
                # update_old_object("harvesting_fixture_kb"),
                delete_self_and_stop_processing,
            ],
            workflow_else,
            [
                # FIXME: Remove this when elasticsearch filtering is ready
                arxiv_set_category_field,
                save_identifiers_to_kb("harvesting_fixture_kb"),
                arxiv_plot_extract,
                arxiv_fulltext_download(),
                # arxiv_refextract, FIXME Need to fix extractutils + new linker
                arxiv_author_list("authorlist2marcxml.xsl"),
                # extract_journal_info, FIXME Need to fix extractutils
                classify_paper(
                    taxonomy="HEPont",
                    only_core_tags=False,
                    spires=True,
                    with_author_keywords=True,
                ),
                filter_core_keywords(filter_kb="antihep"),
                guess_coreness("new_astro_model.pickle"),
                halt_record_with_action(action="arxiv_approval",
                                        message="Accept article?"),
                workflow_if(was_approved),
                [
                    add_core,
                    finalize_record_sip(processor=hep2marc),
                    send_robotupload(),
                ],
                workflow_else,
                [
                    log_info("Record rejected"),
                ],
            ],
        ],
    ]
