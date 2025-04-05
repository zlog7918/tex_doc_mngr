from .users import route_user_bluebrint
from test_utils import TestingUnitBlueprint

route_blueprint=TestingUnitBlueprint(
    route_user_bluebrint,
)
