from test_utils import TestingUnit
from models import model_blueprint
from routes import route_blueprint
from services import service_blueprint

tu=TestingUnit()
tu.add_blueprint(model_blueprint)
tu.add_blueprint(route_blueprint)
tu.add_blueprint(service_blueprint)
# print(tu._tests)
tu.exec()
