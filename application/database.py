from flask_mongoengine import MongoEngine

db = MongoEngine()

__all__ = [
    'db',
    'MongoEngine',
]