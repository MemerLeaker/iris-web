#  IRIS Source Code
#  Copyright (C) 2021 - Airbus CyberSecurity (SAS) - DFIR-IRIS Team
#  ir@cyberactionlab.net - contact@dfir-iris.org
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
from flask import redirect
from flask import render_template
from flask import url_for
from flask_wtf import FlaskForm

from app.iris_engine.access_control.iris_user import iris_current_user
from app.datamgmt.case.case_db import get_case
from app.datamgmt.case.case_recommendations_db import get_recommendation
from app.datamgmt.manage.manage_attribute_db import get_default_custom_attributes
from app.forms import CaseRecommendationForm
from app.models.authorization import CaseAccessLevel
from app.models.authorization import User
from app.models.models import CaseRecommendations
from app.blueprints.access_controls import ac_case_requires
from app.blueprints.responses import response_error

case_recommendations_blueprint = Blueprint('case_recommendations',
                                 __name__,
                                 template_folder='templates')


@case_recommendations_blueprint.route('/case/recommendations', methods=['GET'])
@ac_case_requires(CaseAccessLevel.read_only, CaseAccessLevel.full_access)
def case_recommendations(caseid, url_redir):
    if url_redir:
        return redirect(url_for('case_recommendations.case_recommendations', cid=caseid, redirect=True))

    form = FlaskForm()
    case = get_case(caseid)

    return render_template("case_recommendations.html", case=case, form=form)


@case_recommendations_blueprint.route('/case/recommendations/add/modal', methods=['GET'])
@ac_case_requires(CaseAccessLevel.full_access)
def case_add_recommendation_modal(caseid, url_redir):
    if url_redir:
        return redirect(url_for('case_recommendations.case_recommendations', cid=caseid, redirect=True))

    recommendation = CaseRecommendations()
    recommendation.custom_attributes = get_default_custom_attributes('recommendation')
    form = CaseRecommendationForm()

    return render_template("modal_add_case_recommendation.html", form=form, recommendation=recommendation, uid=iris_current_user.id, user_name=None,
                           attributes=recommendation.custom_attributes)


@case_recommendations_blueprint.route('/case/recommendations/<int:cur_id>/modal', methods=['GET'])
@ac_case_requires(CaseAccessLevel.read_only, CaseAccessLevel.full_access)
def case_recommendation_view_modal(cur_id, caseid, url_redir):
    if url_redir:
        return redirect(url_for('case_recommendations.case_recommendations', cid=caseid, redirect=True))

    form = CaseRecommendationForm()

    recommendation = get_recommendation(recommendation_id=cur_id)

    if not recommendation:
        return response_error("Invalid Recommendation ID for this case")

    form.recommendation_title.render_kw = {'value': recommendation.recommendation_title}
    form.recommendation_description.data = recommendation.recommendation_description
    #user_name, = User.query.with_entities(User.name).filter(User.id == recommendation.recommendation_userid_update).first()

    return render_template("modal_add_case_recommendation.html", form=form, recommendation=recommendation)#,
                           #user_name=user_name*/)
