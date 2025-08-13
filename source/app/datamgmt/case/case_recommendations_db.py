#  IRIS Source Code
#  Copyright (C) 2021 - Airbus CyberSecurity (SAS)
#  ir@cyberactionlab.net
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 3 of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

from datetime import datetime
from sqlalchemy import desc
from sqlalchemy import and_

from app import db
from app.iris_engine.access_control.iris_user import iris_current_user
from app.datamgmt.conversions import convert_sort_direction
from app.datamgmt.manage.manage_attribute_db import get_default_custom_attributes
from app.datamgmt.manage.manage_users_db import get_users_list_restricted_from_case
from app.models.models import CaseRecommendations
from app.models.cases import Cases
from app.models.models import GlobalRecommendation
from app.models.authorization import User
from app.models.pagination_parameters import PaginationParameters


def get_filtered_recommendations(case_identifier, pagination_parameters: PaginationParameters):

    query = CaseRecommendations.query.filter(
        CaseRecommendations.recommendation_case_id == case_identifier
    ).order_by(
        desc(CaseRecommendations.recommendation_title)
    )

    sort_by = pagination_parameters.get_order_by()
    if sort_by is not None:
        order_func = convert_sort_direction(pagination_parameters.get_direction())

        if hasattr(CaseRecommendations, sort_by):
            query = query.order_by(order_func(getattr(CaseRecommendations, sort_by)))

    return query.paginate(page=pagination_parameters.get_page(), per_page=pagination_parameters.get_per_page(), error_out=False)


def get_recommendation(recommendation_id: int) -> CaseRecommendations:
    return CaseRecommendations.query.filter(CaseRecommendations.id == recommendation_id).first()


def add_recommendation(recommendation, user_id, caseid):
    recommendation.recommendation_case_id = caseid
    # recommendation.recommendation_userid_open = user_id
    # recommendation.recommendation_userid_update = user_id

    # recommendation.custom_attributes = recommendation.custom_attributes if recommendation.custom_attributes else get_default_custom_attributes('recommendation')

    db.session.add(recommendation)
    db.session.commit()


    return recommendation

def import_recommendation(global_recommendation_id: int, case_id: int) -> CaseRecommendations: ##TODO
    global_recommendation = GlobalRecommendation.getby_id(global_recommendation_id)
    recommendation = CaseRecommendations(
        recommendation_case_id=case_id,
        recommendation_title=global_recommendation.recommendation_title,
        recommendation_description=global_recommendation.recommendation_description,
    )

    db.session.add(recommendation)
    db.session.commit()

    return recommendation

def delete_recommendation(recommendation_id):
    with db.session.begin_nested():

        CaseRecommendations.query.filter(
            CaseRecommendations.id == recommendation_id
        ).delete()


def get_recommendations_cases_mapping(open_cases_only=False):
    condition = Cases.close_date == None if open_cases_only else True

    return CaseRecommendations.query.filter(
        condition
    ).with_entities(
        CaseRecommendations.recommendation_case_id
    ).join(
        CaseRecommendations.case
    ).all()
