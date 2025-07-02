#!/usr/bin/env python3

from flask import request, session, jsonify
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import UnprocessableEntity
from config import bcrypt
from config import app, db, api
from models import User, Recipe

class Signup(Resource):
    def post(self):
        data = request.get_json()
        
        username = data.get('username')
        password = data.get('password')
        image_url = data.get('image_url')
        bio = data.get('bio')

        if not username or not password:
            return {'errors': ['Username and password are required.']}, 422

        try:
            new_user = User(
                username=username,
                image_url=image_url,
                bio=bio
            )
            new_user.password_hash = password  # triggers the setter that hashes

            db.session.add(new_user)
            db.session.commit()

            session['user_id'] = new_user.id

            return {
                'id': new_user.id,
                'username': new_user.username,
                'image_url': new_user.image_url,
                'bio': new_user.bio
            }, 201

        except IntegrityError:
            db.session.rollback()
            return {'errors': ['Username already exists.']}, 422

        except Exception as e:
            return {'errors': [str(e)]}, 422

class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')

        if user_id:
            user = User.query.get(user_id)
            if user:
                return {
                    'id': user.id,
                    'username': user.username,
                    'image_url': user.image_url,
                    'bio': user.bio
                }, 200

        return {'error': 'Unauthorized'}, 401

class Login(Resource):
    def post(self):
        data = request.get_json()

        if not data:
            return {'error': 'No input data provided'}, 400

        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return {'error': 'Username and password required'}, 400

        user = User.query.filter_by(username=username).first()

        if user and user.authenticate(password):
            session['user_id'] = user.id
            return {
                'id': user.id,
                'username': user.username,
                'image_url': user.image_url,
                'bio': user.bio
            }, 200

        return {'error': 'Unauthorized'}, 401

class Logout(Resource):
    def delete(self):
        if session.get('user_id'):
            session.pop('user_id')
            return {}, 204
        return {'error': 'Unauthorized'}, 401



class RecipeIndex(Resource):
    def get(self):
        # ✅ Require login to view recipes
        user_id = session.get('user_id')

        if not user_id:
            return {'error': 'Unauthorized'}, 401

        recipes = Recipe.query.all()
        return [recipe.to_dict() for recipe in recipes], 200

    def post(self):
        user_id = session.get('user_id')

        if not user_id:
            return {'error': 'Unauthorized'}, 401

        data = request.get_json()

        title = data.get('title')
        instructions = data.get('instructions')
        minutes = data.get('minutes_to_complete')

        if not title or not instructions:
            return {'errors': ['Title and instructions are required.']}, 422

        try:
            new_recipe = Recipe(
                title=title,
                instructions=instructions,
                minutes_to_complete=minutes,
                user_id=user_id
            )

            db.session.add(new_recipe)
            db.session.commit()

            return new_recipe.to_dict(), 201

        except Exception as e:
            db.session.rollback()
            return {'errors': [str(e)]}, 422


# api.add_resource(Signup, '/signup', endpoint='signup')
# api.add_resource(CheckSession, '/check_session', endpoint='check_session')
# api.add_resource(Login, '/login', endpoint='login')
# api.add_resource(Logout, '/logout', endpoint='logout')
# api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


if __name__ == '__main__':
    app.run(port=5555, debug=True)