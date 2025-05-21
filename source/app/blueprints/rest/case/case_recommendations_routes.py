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

import marshmallow
from flask import Blueprint
from flask import request

from app import db
from app.blueprints.rest.endpoints import endpoint_deprecated
from app.iris_engine.access_control.iris_user import iris_current_user
from app.business.errors import BusinessProcessingError
from app.business.recommendations import recommendations_delete
from app.business.recommendations import recommendations_create
from app.business.recommendations import recommendations_get
from app.business.recommendations import recommendations_update
from app.datamgmt.case.case_recommendations_db import get_recommendation
from app.datamgmt.states import get_recommendations_state
from app.iris_engine.module_handler.module_handler import call_modules_hook
from app.iris_engine.utils.tracker import track_activity
from app.models.authorization import CaseAccessLevel
from app.schema.marshables import CaseRecommendationSchema
from app.blueprints.access_controls import ac_requires_case_identifier
from app.blueprints.access_controls import ac_api_requires
from app.blueprints.responses import response_error
from app.blueprints.responses import response_success

case_recommendations_rest_blueprint = Blueprint('case_recommendations_rest', __name__)


@case_recommendations_rest_blueprint.route('/case/recommendations/list', methods=['GET'])
@endpoint_deprecated('GET', '/api/v2/cases/<int:case_identifier>/recommendations')
@ac_requires_case_identifier(CaseAccessLevel.read_only, CaseAccessLevel.full_access)
@ac_api_requires()
def case_get_recommendations(caseid: int):

    output = []
   

    ret = {
        "recommendations": output,
        "state": get_recommendations_state(caseid=caseid)
    }

    return response_success("", data=ret)


@case_recommendations_rest_blueprint.route('/case/recommendations/state', methods=['GET'])
@ac_requires_case_identifier(CaseAccessLevel.read_only, CaseAccessLevel.full_access)
@ac_api_requires()
def case_get_recommendations_state(caseid: int):
    os = get_recommendations_state(caseid=caseid)
    if os:
        return response_success(data=os)
    return response_error('No recommendations state for this case.')


@case_recommendations_rest_blueprint.route('/case/recommendations/status/update/<int:cur_id>', methods=['POST'])
@ac_requires_case_identifier(CaseAccessLevel.full_access)
@ac_api_requires()
def case_recommendation_status_update(cur_id: int, caseid: int):
    recommendation = get_recommendation(recommendation_id=cur_id)
    if not recommendation:
        return response_error("Invalid recommendation ID for this case")

    if request.is_json:

        if update_recommendation_status(request.json.get('recommendation_status_id'), cur_id, caseid):
            recommendation_schema = CaseRecommendationSchema()

            return response_success("Recommendation status updated", data=recommendation_schema.dump(recommendation))
        return response_error("Invalid status")

    return response_error("Invalid request")


@case_recommendations_rest_blueprint.route('/case/recommendations/add', methods=['POST'])
@endpoint_deprecated('POST', '/api/v2/cases/<int:caseid>/recommendations')
@ac_requires_case_identifier(CaseAccessLevel.full_access)
@ac_api_requires()
def deprecated_case_add_recommendation(caseid: int):
    recommendation_schema = CaseRecommendationSchema()
    try:
        msg, recommendation = recommendations_create(case_identifier=caseid,
                                 request_json=request.get_json())
        return response_success(msg, data=recommendation_schema.dump(recommendation))
    except BusinessProcessingError as e:
        return response_error(e.get_message(), data=e.get_data())


@case_recommendations_rest_blueprint.route('/case/recommendations/<int:cur_id>', methods=['GET'])
@endpoint_deprecated('GET', '/api/v2/cases/<int:case_identifier>/recommendations/<int:cur_id>')
@ac_requires_case_identifier(CaseAccessLevel.read_only, CaseAccessLevel.full_access)
@ac_api_requires()
def deprecated_case_recommendation_view(cur_id: int, caseid: int):
    recommendation = get_recommendation(recommendation_id=cur_id)
    if not recommendation:
        return response_error('Invalid recommendation ID for this case')

    recommendation_schema = CaseRecommendationSchema()

    return response_success(data=recommendation_schema.dump(recommendation))


@case_recommendations_rest_blueprint.route('/case/recommendations/update/<int:cur_id>', methods=['POST'])
@endpoint_deprecated('PUT', '/api/v2/cases/<int:case_identifier>/recommendations/<int:identifier>')
@ac_requires_case_identifier(CaseAccessLevel.full_access)
@ac_api_requires()
def deprecated_case_edit_recommendation(cur_id: int, caseid: int):
    try:
        recommendation = get_recommendation(recommendation_id=cur_id)
        if not recommendation:
            return response_error(msg='Invalid recommendation ID for this case')

        recommendation = recommendations_update(recommendation, request.get_json())
        recommendation_schema = CaseRecommendationSchema()

        return response_success(msg='Recommendation updated', data=recommendation_schema.dump(recommendation))

    except marshmallow.exceptions.ValidationError as e:
        return response_error(msg='Data error', data=e.messages)


@case_recommendations_rest_blueprint.route('/case/recommendations/delete/<int:cur_id>', methods=['POST'])
@endpoint_deprecated('DELETE', '/api/v2/cases/<int:case_identifier>/recommendations/<int:cur_id>')
@ac_requires_case_identifier(CaseAccessLevel.full_access)
@ac_api_requires()
def deprecated_case_delete_recommendation(cur_id: int, caseid: int):
    try:
        recommendation = recommendations_get(identifier=cur_id)
        recommendations_delete(recommendation)
        return response_success('Recommendation deleted')
    except BusinessProcessingError as e:
        return response_error(msg=e.get_message(), data=e.get_data())