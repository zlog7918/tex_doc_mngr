from .user import model_user_blueprint
from .utils import model_utils_blueprint
from test_utils import TestingUnitBlueprint

model_blueprint=TestingUnitBlueprint(
    model_user_blueprint,
    model_utils_blueprint,
)
