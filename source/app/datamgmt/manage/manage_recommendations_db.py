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
from sqlalchemy import func
from typing import List

from app.models.models import Recommendation


def get_recommendations_list() -> List[dict]:
    """Get a list of recommendations

    Returns:
        List[dict]: List of recommendations
    """
    recommendations = Recommendation.query.with_entities(
        Recommendation.id,
        Recommendation.title,
        Recommendation.description,
    ).all()

    print(f"recommendations: {recommendations}")

    c_cl = [row._asdict() for row in recommendations]
    return c_cl


def get_recommendation_by_name(cur_name: str) -> Recommendation:
    """Get a recommendation

    Args:
        cur_name (str): recommendation title

    Returns:
        Recommendation: Recommendation title
    """
    recommendation = Recommendation.query.filter_by(name=cur_name).first()
    return recommendation

def get_recommendation_by_id(id: int) -> Recommendation:
    """Get a recommendation

    Args:
        id (int): recommendation id

    Returns:
        Recommendation: Recommendation title
    """
    recommendation = Recommendation.query.filter_by(id=id).first()
    return recommendation


def search_recommendation_by_name(name: str, exact_match: bool = False) -> List[dict]:
    """Search for a recommendation by title

    Args:
        name (str): recommendation name
        exact_match (bool, optional): Exact match. Defaults to False.

    Returns:
        List[dict]: List of recommendations
    """
    if exact_match:
        query_filter = (func.lower(Recommendation.title) == name.lower())
    else:
        query_filter = (Recommendation.title.ilike(f'%{name}%'))

    return Recommendation.query.filter(query_filter).all()
