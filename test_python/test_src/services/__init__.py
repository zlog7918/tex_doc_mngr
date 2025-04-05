from .user import service_user_bluebrint
from test_utils import TestingUnitBlueprint

service_blueprint=TestingUnitBlueprint(
    service_user_bluebrint,
)
