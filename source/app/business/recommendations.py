#  IRIS Source Code
#  Copyright (C) 2024 - DFIR-IRIS
#  contact@dfir-iris.org
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

from flask_sqlalchemy.pagination import Pagination

from app import db
from app.iris_engine.access_control.iris_user import iris_current_user
from app.datamgmt.case.case_recommendations_db import delete_recommendation
from app.datamgmt.case.case_recommendations_db import add_recommendation
from app.datamgmt.case.case_recommendations_db import get_recommendation
from app.datamgmt.case.case_recommendations_db import get_filtered_recommendations
from app.iris_engine.module_handler.module_handler import call_modules_hook
from app.iris_engine.utils.tracker import track_activity
from app.models.models import CaseRecommendations
from app.models.pagination_parameters import PaginationParameters
from app.schema.marshables import CaseRecommendationSchema
from app.business.errors import BusinessProcessingError
from app.business.errors import ObjectNotFoundError
from marshmallow.exceptions import ValidationError


def _load(request_data, **kwargs):
    try:
        add_recommendation_schema = CaseRecommendationSchema()
        return add_recommendation_schema.load(request_data, **kwargs)
    except ValidationError as e:
        raise BusinessProcessingError('Data error', e.messages)


def recommendations_delete(recommendation: CaseRecommendations):
    call_modules_hook('on_preload_recommendation_delete', data=recommendation.id)

    delete_recommendation(recommendation.id)
    call_modules_hook('on_postload_recommendation_delete', data=recommendation.id, caseid=recommendation.recommendation_case_id)
    track_activity(f'deleted recommendation "{recommendation.recommendation_title}"')


def recommendations_create(case_identifier: int, request_json: dict) -> (str, CaseRecommendations):

    request_data = call_modules_hook('on_preload_recommendation_create', data=request_json, caseid=case_identifier)

    recommendation = _load(request_data)

    crecommendation = add_recommendation(recommendation=recommendation,
                     user_id=iris_current_user.id,
                     caseid=case_identifier
                     )

    crecommendation = call_modules_hook('on_postload_recommendation_create', data=crecommendation, caseid=case_identifier)

    if crecommendation:
        track_activity(f'added recommendation "{crecommendation.recommendation_title}"', caseid=case_identifier)
        return f'Recommendation "{crecommendation.recommendation_title}" added', crecommendation
    raise BusinessProcessingError("Unable to create recommendation for internal reasons")


def recommendations_get(identifier) -> CaseRecommendations:
    recommendation = get_recommendation(identifier)
    if not recommendation:
        raise ObjectNotFoundError()
    return recommendation


def recommendations_filter(case_identifier, pagination_parameters: PaginationParameters) -> Pagination:
    return get_filtered_recommendations(case_identifier, pagination_parameters)


def recommendations_update(recommendation: CaseRecommendations, request_json):
    case_identifier = recommendation.recommendation_case_id
    request_data = call_modules_hook('on_preload_recommendation_update', data=request_json, caseid=case_identifier)

    request_data['id'] = recommendation.id
    recommendation = _load(request_data, instance=recommendation)

    recommendation.recommendation_userid_update = iris_current_user.id
    recommendation.recommendation_last_update = datetime.utcnow()


    #update_recommendations_state(caseid=case_identifier)

    db.session.commit()

    recommendation = call_modules_hook('on_postload_recommendation_update', data=recommendation, caseid=case_identifier)

    if not recommendation:
        raise BusinessProcessingError('Unable to update recommendation for internal reasons')

    track_activity(f'updated recommendation "{recommendation.recommendation_title}" (status {recommendation.status.status_name})', caseid=case_identifier)
    return recommendation
