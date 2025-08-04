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

import marshmallow

from flask import Blueprint
from flask import Response
from flask import request

from app import db
from app.datamgmt.manage.manage_recommendations_db import get_recommendations_list
from app.datamgmt.manage.manage_recommendations_db import get_recommendation_by_name
from app.datamgmt.manage.manage_recommendations_db import get_recommendation_by_id
#from app.datamgmt.manage.manage_evidence_types_db import verify_evidence_type_in_use
from app.iris_engine.utils.tracker import track_activity
from app.models.authorization import Permissions
from app.schema.marshables import GlobalRecommendationSchema
from app.blueprints.access_controls import ac_api_requires
from app.blueprints.responses import response_error
from app.blueprints.responses import response_success

manage_recommendations_rest_blueprint = Blueprint('manage_recommendations_rest', __name__)


@manage_recommendations_rest_blueprint.route('/manage/recommendations/list', methods=['GET'])
@ac_api_requires()
def list_recommendations() -> Response:
    """Get the list of recommendations

    Returns:
        Flask Response object

    """
    l_cl = get_recommendations_list()
    if not l_cl:
        return response_error("No recommendations available")
    
    return response_success("", data=l_cl)


# @manage_recommendations_rest_blueprint.route('/manage/recommendations/<str:recommendation_title>', methods=['GET'])
# @ac_api_requires()
# def get_recommendation(recommendation_title: str) -> Response:
#     """Get a recommendation

#     Args:
#         recommendation_id (int): recommendation ID
#         caseid (int): case id

#     Returns:
#         Flask Response object
#     """
#     recommendation_schema = CaseRecommendationSchema()
#     recommendation = get_recommendation_by_name(recommendation_title)
#     if recommendation is None:
#         return response_error(f"Invalid evidence type ID {recommendation_title}")

#     return response_success("", data=recommendation_schema.dump(recommendation))


@manage_recommendations_rest_blueprint.route('/manage/recommendations/update/<int:recommendation_id>',
                                            methods=['POST'])
@ac_api_requires(Permissions.server_administrator)
def update_recommendation(recommendation_id: int) -> Response:
    """Update a recommendation

    Args:
        recommendation_id (int): recommendation id

    Returns:
        Flask Response object
    """
    if not request.is_json:
        return response_error("Invalid request")

    recommendation = get_recommendation_by_id(recommendation_id)
    print(recommendation.title)

    if not recommendation:
        return response_error(f"Invalid recommendation ID {recommendation_id}")

    ccl = GlobalRecommendationSchema()

    try:
        data = request.get_json()

        #remapping frontend keys to backend keys
        if "recommendation_title" in data:
            data["title"] = data.pop("recommendation_title")
        if "recommendation_description" in data:
            data["description"] = data.pop("recommendation_description")
        if "recommendation_tags" in data:
            data["tags"] = data.pop("recommendation_tags")

        ccls = ccl.load(data, instance=recommendation)

        if ccls:
            track_activity(f"updated recommendation {ccls.title}")
            return response_success("Recommendation updated", ccl.dump(ccls))

    except marshmallow.exceptions.ValidationError as e:
        return response_error(msg="Data error", data=e.messages)

    return response_error("Unexpected error server-side. Nothing updated", data=recommendation)


@manage_recommendations_rest_blueprint.route('/manage/recommendations/add', methods=['POST'])
@ac_api_requires(Permissions.server_administrator)
def add_recommendation() -> Response:
    """Add a recommendation

    Returns:
        Flask Response object
    """
    print("BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB")
    if not request.is_json:
        return response_error("Invalid request")

    ccl = GlobalRecommendationSchema()

    try:
        data = request.get_json()

        #remapping frontend keys to backend keys
        if "recommendation_title" in data:
            data["title"] = data.pop("recommendation_title")
        if "recommendation_description" in data:
            data["description"] = data.pop("recommendation_description")
        if "recommendation_tags" in data:
            data["tags"] = data.pop("recommendation_tags")

        ccls = ccl.load(data)

        if ccls:
            db.session.add(ccls)
            db.session.commit()

            track_activity(f"added recommendation {ccls.title}")
            return response_success("Recommendation added", ccl.dump(ccls))

    except marshmallow.exceptions.ValidationError as e:
        return response_error(msg="Data error", data=e.messages)

    return response_error("Unexpected error server-side. Nothing added", data=None)


@manage_recommendations_rest_blueprint.route('/manage/recommendations/delete/<int:recommendation_id>',
                                            methods=['POST'])
@ac_api_requires(Permissions.server_administrator)
def delete_evidence_type(recommendation_id: int) -> Response:
    """Delete an recommendation

    Args:
        recommendation_id (int): recommendation id

    Returns:
        Flask Response object
    """
    # if verify_evidence_type_in_use(evidence_type_id):
    #     return response_error("Evidence type is in use. Please delete evidences using this type beforehand.")

    recommendation = get_recommendation_by_id(recommendation_id)
    if not recommendation:
        return response_error(f"Invalid recommendation ID {recommendation_id}")

    db.session.delete(recommendation)
    db.session.commit()

    track_activity(f"deleted recommendation {recommendation.title}")
    return response_success("Recommendation deleted")


@manage_recommendations_rest_blueprint.route('/manage/recommendations/search', methods=['POST'])
@ac_api_requires()
def search_recommendation():
    if not request.is_json:
        return response_error("Invalid request")

    recommendation_title = request.json.get('recommendation_title')
    if recommendation_title is None:
        return response_error("Invalid recommendation titlee. Got None")

    exact_match = request.json.get('exact_match', False)

    recommendation = search_recommendation(recommendation_title, exact_match=exact_match)
    if not recommendation:
        return response_error("No recommendation found")

    schema = GlobalRecommendationSchema(many=True)
    return response_success("", data=schema.dump(recommendation))
