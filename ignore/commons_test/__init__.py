from .resources import *
from application import *


app = create_app()
app.register_blueprint(dummy_bp)