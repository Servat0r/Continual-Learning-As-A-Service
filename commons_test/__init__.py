from .base_datatypes import *
from .generators import *
from .metadata import *
from .datatypes import *
from .documents import *
from .builds import *
from application import *
from .routes import bp as dummy_bp


app = create_app()
app.register_blueprint(dummy_bp)