import os
from keen import exceptions, persistence_strategies, scoped_keys
import keen
from keen.client import KeenClient
from keen.tests.base_test_case import BaseTestCase

__author__ = 'dkador'


class ClientTests(BaseTestCase):
    def setUp(self):
        super(ClientTests, self).setUp()
        keen._client = None
        keen.project_id = None
        keen.write_key = None
        keen.read_key = None

    def test_init(self):
        def positive_helper(project_id, **kwargs):
            client = KeenClient(project_id, **kwargs)
            self.assert_not_equal(client, None)
            self.assert_equal(project_id, client.project_id)
            return client

        def negative_helper(expected_exception, project_id,
                            **kwargs):
            try:
                KeenClient(project_id, **kwargs)
            except expected_exception as e:
                self.assert_true(str(e))
                return e

        # real strings for project id should work
        positive_helper("project_id")

        # non-strings shouldn't work
        e = negative_helper(exceptions.InvalidProjectIdError, 5)
        self.assert_equal(5, e.project_id)
        negative_helper(exceptions.InvalidProjectIdError, None)
        negative_helper(exceptions.InvalidProjectIdError, "")

        # test persistence strategies

        # if you don't ask for a specific one, you get the direct strategy
        client = positive_helper("project_id")
        self.assert_true(isinstance(client.persistence_strategy,
                                    persistence_strategies.DirectPersistenceStrategy))
        # specifying a valid one should work!
        client = positive_helper("project_id",
                                 persistence_strategy=None)
        self.assert_true(isinstance(client.persistence_strategy,
                                    persistence_strategies.DirectPersistenceStrategy))
        # needs to be an instance of a strategy, not anything else
        negative_helper(exceptions.InvalidPersistenceStrategyError,
                        "project_id", persistence_strategy="abc")
        # needs to be an instance of a strategy, not the class
        negative_helper(exceptions.InvalidPersistenceStrategyError,
                        "project_id",
                        persistence_strategy=persistence_strategies.DirectPersistenceStrategy)

    def test_direct_persistence_strategy(self):
        project_id = "5004ded1163d66114f000000"
        api_key = "2e79c6ec1d0145be8891bf668599c79a"
        write_key = scoped_keys.encrypt(api_key, {"allowed_operations": ["write"]})
        read_key = scoped_keys.encrypt(api_key, {"allowed_operations": ["read"]})
        client = KeenClient(project_id, write_key=write_key, read_key=read_key)
        client.add_event("python_test", {"hello": "goodbye"})
        client.add_event("python_test", {"hello": "goodbye"})
        client.add_events(
            {
                "sign_ups": [{
                    "username": "timmy",
                    "referred_by": "steve",
                    "son_of": "my_mom"
                }],
                "purchases": [
                    {"price": 5},
                    {"price": 6},
                    {"price": 7}
                ]}
        )

    def test_module_level_add_event(self):
        keen.project_id = "5004ded1163d66114f000000"
        api_key = "2e79c6ec1d0145be8891bf668599c79a"
        keen.write_key = scoped_keys.encrypt(api_key, {"allowed_operations": ["write"]})
        # client = KeenClient(project_id, write_key=write_key, read_key=read_key)
        keen.add_event("python_test", {"hello": "goodbye"})

    def test_module_level_add_events(self):
        keen.project_id = "5004ded1163d66114f000000"
        api_key = "2e79c6ec1d0145be8891bf668599c79a"
        keen.write_key = scoped_keys.encrypt(api_key, {"allowed_operations": ["write"]})
        # client = KeenClient(project_id, write_key=write_key, read_key=read_key)
        keen.add_events({"python_test": [{"hello": "goodbye"}]})

    def test_environment_variables(self):
        # try addEvent w/out having environment variables
        keen._client = None
        keen.project_id = None
        keen.write_key = None
        keen.read_key = None
        self.assert_raises(exceptions.InvalidEnvironmentError,
                           keen.add_event, "python_test", {"hello": "goodbye"})

        os.environ["KEEN_PROJECT_ID"] = "12345"

        self.assert_raises(exceptions.InvalidEnvironmentError,
                           keen.add_event, "python_test", {"hello": "goodbye"})

        # force client to reinitialize
        keen._client = None
        os.environ["KEEN_WRITE_KEY"] = "abcde"
        self.assert_raises(exceptions.KeenApiError,
                           keen.add_event, "python_test", {"hello": "goodbye"})

    def test_configure_through_code(self):
        keen.project_id = "123456"
        self.assert_raises(exceptions.InvalidEnvironmentError,
                           keen.add_event, "python_test", {"hello": "goodbye"})

        # force client to reinitialize
        keen._client = None
        keen.write_key = "abcdef"
        self.assert_raises(exceptions.KeenApiError,
                           keen.add_event, "python_test", {"hello": "goodbye"})


class QueryTests(BaseTestCase):
    def setUp(self):
        super(QueryTests, self).setUp()
        keen._client = None
        keen.project_id = "5004ded1163d66114f000000"
        api_key = "2e79c6ec1d0145be8891bf668599c79a"
        keen.write_key = scoped_keys.encrypt(api_key, {"allowed_operations": ["write"]})
        keen.read_key = scoped_keys.encrypt(api_key, {"allowed_operations": ["read"]})
        keen.add_event("query test", {"number": 5})
        keen.add_event("step2", {"number": 5})

    def tearDown(self):
        keen.project_id = None
        keen.write_key = None
        keen.read_key = None
        keen._client = None
        super(QueryTests, self).tearDown()

    def get_filter(self):
        return [{"property_name": "number", "operator": "eq", "property_value": 5}]

    def test_count(self):
        resp = keen.count("query test", timeframe="today", filters=self.get_filter())
        assert type(resp) is int

    def test_sum(self):
        resp = keen.sum("query test", target_property="number", timeframe="today")
        assert type(resp) is int

    def test_minimum(self):
        resp = keen.minimum("query test", target_property="number", timeframe="today")
        assert type(resp) is int

    def test_maximum(self):
        resp = keen.maximum("query test", target_property="number", timeframe="today")
        assert type(resp) is int

    def test_average(self):
        resp = keen.average("query test", target_property="number", timeframe="today")
        assert type(resp) is float

    def test_count_unique(self):
        resp = keen.count_unique("query test", target_property="number", timeframe="today")
        assert type(resp) is int

    def test_select_unique(self):
        resp = keen.select_unique("query test", target_property="number", timeframe="today")
        assert type(resp) is list

    def test_extraction(self):
        resp = keen.extraction("query test", timeframe="today")
        assert type(resp) is list

    def test_multi_analysis(self):
        resp = keen.multi_analysis("query test",
                                   analyses={"total": {"analysis_type": "sum", "target_property": "number"}},
                                   timeframe="today")
        assert type(resp) is dict
        assert type(resp["total"]) is int

    def test_funnel(self):
        step1 = {
            "event_collection": "query test",
            "actor_property": "number",
            "timeframe": "today"
        }
        step2 = {
            "event_collection": "step2",
            "actor_property": "number",
            "timeframe": "today"
        }
        resp = keen.funnel([step1, step2])
        assert type(resp) is list, resp

    def test_group_by(self):
        resp = keen.count("query test", timeframe="today", group_by="number")
        assert type(resp) is list

    def test_interval(self):
        resp = keen.count("query test", timeframe="this_2_days", interval="daily")
        assert type(resp) is list
