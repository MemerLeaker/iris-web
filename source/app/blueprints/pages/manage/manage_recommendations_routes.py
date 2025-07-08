#  IRIS Source Code
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

from typing import Union

from flask import Blueprint
from flask import Response
from flask import url_for
from flask import render_template
from werkzeug.utils import redirect

from app.datamgmt.manage.manage_recommendations_db import get_recommendation_by_id
from app.forms import AddRecommendationForm
from app.models.authorization import Permissions
from app.blueprints.responses import response_error
from app.blueprints.access_controls import ac_requires

manage_recommendations_blueprint = Blueprint('manage_recommendations',
                                            __name__,
                                            template_folder='templates')


@manage_recommendations_blueprint.route('/manage/recommendations/update/<int:recommendation_id>/modal',
                                       methods=['GET'])
@ac_requires(Permissions.server_administrator, no_cid_required=True)
def update_recommendation_modal(recommendation_id: int, caseid: int, url_redir: bool) -> Union[str, Response]:
    """Update an evidence type

    Args:
        evidence_type_id (int): evidence type id
        caseid (int): case id
        url_redir (bool): redirect to url

    Returns:
        Flask Response object or str
    """
    if url_redir:
        return redirect(url_for('manage_recommendations_blueprint.update_recommendation_modal',
                                recommendation_id=recommendation_id, caseid=caseid))

    recommendation_form = AddRecommendationForm()
    recommendation = get_recommendation_by_id(recommendation_id)
    if not recommendation:
        return response_error(f"Invalid recommendation ID {recommendation_id}")

    recommendation_form.name.render_kw = {'value': recommendation_form.title}
    recommendation_form.description.render_kw = {'value': recommendation.description}

    return render_template("modal_add_recommendation.html", form=recommendation_form,
                           recommendation=recommendation)


@manage_recommendations_blueprint.route('/manage/recommendations/add/modal', methods=['GET'])
@ac_requires(Permissions.server_administrator, no_cid_required=True)
def add_recommendation_modal(caseid: int, url_redir: bool) -> Union[str, Response]:
    """Add an evidence type

    Args:
        caseid (int): case id
        url_redir (bool): redirect to url

    Returns:
        Flask Response object or str
    """
    print("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")

    if url_redir:
        return redirect(url_for('manage_recommendations_blueprint.add_recommendation_modal',
                                caseid=caseid))

    recommendation_form = AddRecommendationForm()

    return render_template("modal_add_recommendation.html", form=recommendation_form, recommendation=None)
