# This file is part of PyBOSSA.
#
# PyBOSSA is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyBOSSA is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with PyBOSSA.  If not, see <http://www.gnu.org/licenses/>.

from flask import Blueprint
from flask import render_template
from flask import request
from flask import abort
from flask import flash
from flask import redirect
from flask import url_for
from flaskext.login import login_required, current_user
from flaskext.wtf import Form, TextField

import pybossa.model as model
from pybossa.util import admin_required
from sqlalchemy import or_, func
import json


blueprint = Blueprint('admin', __name__)


@blueprint.route('/featured')
@blueprint.route('/featured/<int:app_id>', methods=['POST', 'DELETE'])
@login_required
@admin_required
def featured(app_id=None):
    """List featured apps of PyBossa"""
    if request.method == 'GET':
        apps = model.Session.query(model.App).all()
        featured = model.Session.query(model.Featured).all()
        return render_template('/admin/applications.html', apps=apps,
                featured=featured)
    if request.method == 'POST':
        f = model.Featured()
        f.app_id = app_id
        # Check if the app is already in this table
        tmp = model.Session.query(model.Featured)\
                .filter(model.Featured.app_id == app_id)\
                .first()
        if (tmp == None):
            model.Session.add(f)
            model.Session.commit()
            return json.dumps(f.dictize())
        else:
            return json.dumps({'error': 'App.id %s already in Featured table'\
                    % app_id})
    if request.method == 'DELETE':
        f = model.Session.query(model.Featured)\
                .filter(model.Featured.app_id == app_id)\
                .first()
        if (f):
            model.Session.delete(f)
            model.Session.commit()
            return "", 204
        else:
            return json.dumps({'error': 'App.id %s is not in Featured table'\
                    % app_id})


class SearchForm(Form):
    user = TextField('User')


@blueprint.route('/users', methods=['GET', 'POST'])
@login_required
@admin_required
def users(user_id=None):
    """Manage users of PyBossa"""
    form = SearchForm(request.form)
    users = model.Session.query(model.User)\
            .filter(model.User.admin == 1)\
            .filter(model.User.id != current_user.id)\
            .all()

    if request.method == 'POST' and form.user.data:
        query = '%' + form.user.data.lower() + '%'
        found = model.Session.query(model.User)\
                .filter(or_(func.lower(model.User.name).like(query),\
                            func.lower(model.User.fullname).like(query)))\
                .filter(model.User.id != current_user.id)\
                .all()
        if not found:
            flash("<strong>Ooops!</strong> We didn't find a user "\
                  "matching your query: <strong>%s</strong>" % form.user.data)
            flash("Try with the Full name or his user or nick name", "info")
        return render_template('/admin/users.html', found=found, users=users,
                title="Manage Admin Users", form=form)

    return render_template('/admin/users.html', found=[], users=users,
            title="Manage Admin Users", form=form)


@blueprint.route('/users/add/<int:user_id>')
@login_required
@admin_required
def add_admin(user_id=None):
    """Add admin flag for user_id"""
    if user_id:
        user = model.Session.query(model.User)\
                .get(user_id)
        if user:
            user.admin = 1
            model.Session.commit()
            return redirect(url_for(".users"))
        else:
            return abort(404)


@blueprint.route('/users/del/<int:user_id>')
@login_required
@admin_required
def del_admin(user_id=None):
    """Del admin flag for user_id"""
    if user_id:
        user = model.Session.query(model.User)\
                .get(user_id)
        if user:
            user.admin = 0
            model.Session.commit()
            return redirect(url_for('.users'))
        else:
            return abort(404)
    else:
        return abort(404)
