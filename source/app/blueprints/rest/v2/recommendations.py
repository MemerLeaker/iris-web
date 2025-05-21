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

from flask import Blueprint

from app.blueprints.rest.endpoints import response_api_not_found
from app.blueprints.rest.endpoints import response_api_success
from app.blueprints.rest.endpoints import response_api_deleted
from app.blueprints.rest.endpoints import response_api_error
from app.blueprints.access_controls import ac_api_requires
from app.blueprints.access_controls import ac_api_return_access_denied
from app.business.recommendations import recommendations_delete
from app.business.recommendations import recommendations_get
from app.business.errors import ObjectNotFoundError
from app.business.errors import BusinessProcessingError
from app.models.authorization import CaseAccessLevel
from app.schema.marshables import CaseRecommendationSchema
from app.iris_engine.access_control.utils import ac_fast_check_current_user_has_case_access


recommendations_blueprint = Blueprint('recommendations',
                            __name__,
                            url_prefix='/recommendations')


@recommendations_blueprint.get('/<int:identifier>')
@ac_api_requires()
def get_case_recommendation(identifier):

    try:
        recommendation = recommendations_get(identifier)

        if not ac_fast_check_current_user_has_case_access(recommendation.recommendation_case_id, [CaseAccessLevel.read_only, CaseAccessLevel.full_access]):
            return ac_api_return_access_denied(caseid=recommendation.recommendation_case_id)

        recommendation_schema = CaseRecommendationSchema()
        return response_api_success(recommendation_schema.dump(recommendation))
    except ObjectNotFoundError:
        return response_api_not_found()


@recommendations_blueprint.delete('/<int:identifier>')
@ac_api_requires()
def delete_case_recommendation(identifier):

    try:
        recommendation = recommendations_get(identifier)

        if not ac_fast_check_current_user_has_case_access(recommendation.recommendation_case_id, [CaseAccessLevel.full_access]):
            return ac_api_return_access_denied(caseid=identifier)

        recommendations_delete(recommendation)
        return response_api_deleted()
    except ObjectNotFoundError:
        return response_api_not_found()
    except BusinessProcessingError as e:
        return response_api_error(e.get_message())
