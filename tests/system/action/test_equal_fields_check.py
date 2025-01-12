from openslides_backend.action.generics.create import CreateAction
from openslides_backend.action.generics.update import UpdateAction
from openslides_backend.action.util.action_type import ActionType
from openslides_backend.action.util.register import register_action
from openslides_backend.models import fields
from openslides_backend.models.base import Model
from openslides_backend.shared.patterns import Collection

from .base import BaseActionTestCase


class FakeModelEFA(Model):
    collection = Collection("fake_model_ef_a")
    verbose_name = "fake model for equal field check a"
    id = fields.IntegerField()

    b_id = fields.RelationField(
        to={Collection("fake_model_ef_b"): "meeting_id"},
    )
    c_id = fields.RelationField(
        to={Collection("fake_model_ef_c"): "meeting_id"},
    )


class FakeModelEFB(Model):
    collection = Collection("fake_model_ef_b")
    verbose_name = "fake model for equal field check b"
    id = fields.IntegerField()

    meeting_id = fields.RelationField(to={Collection("fake_model_ef_a"): "b_id"})

    c_id = fields.RelationField(
        to={Collection("fake_model_ef_c"): "b_id"},
        equal_fields="meeting_id",
    )
    c_ids = fields.RelationListField(
        to={Collection("fake_model_ef_c"): "b_ids"},
        equal_fields="meeting_id",
    )
    c_generic_id = fields.GenericRelationField(
        to={Collection("fake_model_ef_c"): "b_generic_id"},
        equal_fields="meeting_id",
    )
    c_generic_ids = fields.GenericRelationListField(
        to={Collection("fake_model_ef_c"): "b_generic_ids"},
        equal_fields="meeting_id",
    )


class FakeModelEFC(Model):
    collection = Collection("fake_model_ef_c")
    verbose_name = "fake model for equal field check c"
    id = fields.IntegerField()

    meeting_id = fields.RelationField(to={Collection("fake_model_ef_a"): "c_id"})

    b_id = fields.RelationField(
        to={Collection("fake_model_ef_b"): "c_id"},
    )
    b_ids = fields.RelationListField(
        to={Collection("fake_model_ef_b"): "c_ids"},
    )
    b_generic_id = fields.GenericRelationField(
        to={Collection("fake_model_ef_b"): "c_generic_id"},
    )
    b_generic_ids = fields.GenericRelationListField(
        to={Collection("fake_model_ef_b"): "c_generic_ids"},
    )


@register_action("fake_model_ef_b.create", action_type=ActionType.BACKEND_INTERNAL)
class FakeModelEFBCreateAction(CreateAction):
    model = FakeModelEFB()
    schema = {}  # type: ignore
    skip_archived_meeting_check = True


@register_action("fake_model_ef_b.update", action_type=ActionType.BACKEND_INTERNAL)
class FakeModelEFBUpdateAction(UpdateAction):
    model = FakeModelEFB()
    schema = {}  # type: ignore
    skip_archived_meeting_check = True


class TestEqualFieldsCheck(BaseActionTestCase):
    def test_simple_pass(self) -> None:
        self.set_models(
            {
                "fake_model_ef_a/1": {"c_id": 1},
                "fake_model_ef_c/1": {"meeting_id": 1},
            }
        )
        response = self.request("fake_model_ef_b.create", {"meeting_id": 1, "c_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("fake_model_ef_b/1")

    def test_simple_fail(self) -> None:
        self.set_models(
            {
                "fake_model_ef_a/1": {},
                "fake_model_ef_a/2": {"c_id": 1},
                "fake_model_ef_c/1": {"meeting_id": 2},
            }
        )
        response = self.request("fake_model_ef_b.create", {"meeting_id": 1, "c_id": 1})
        self.assert_status_code(response, 400)
        self.assertIn(
            "The following models do not belong to meeting 1: ['fake_model_ef_c/1']",
            response.json["message"],
        )
        self.assert_model_not_exists("fake_model_ef_b/1")

    def test_simple_update_pass(self) -> None:
        self.set_models(
            {
                "fake_model_ef_a/1": {"b_id": 1, "c_id": 1},
                "fake_model_ef_b/1": {"meeting_id": 1, "c_id": 1},
                "fake_model_ef_c/1": {"meeting_id": 1, "b_id": 1},
                "fake_model_ef_c/2": {"meeting_id": 1},
            }
        )
        response = self.request("fake_model_ef_b.update", {"id": 1, "c_id": 2})
        self.assert_status_code(response, 200)
        self.assert_model_exists("fake_model_ef_b/1", {"c_id": 2})

    def test_list_pass(self) -> None:
        self.set_models(
            {
                "fake_model_ef_a/1": {"c_id": 1},
                "fake_model_ef_c/1": {"meeting_id": 1},
            }
        )
        response = self.request(
            "fake_model_ef_b.create", {"meeting_id": 1, "c_ids": [1]}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("fake_model_ef_b/1")

    def test_list_fail(self) -> None:
        self.set_models(
            {
                "fake_model_ef_a/1": {},
                "fake_model_ef_a/2": {"c_id": 1},
                "fake_model_ef_c/1": {"meeting_id": 2},
            }
        )
        response = self.request(
            "fake_model_ef_b.create", {"meeting_id": 1, "c_ids": [1]}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "The following models do not belong to meeting 1: ['fake_model_ef_c/1']",
            response.json["message"],
        )
        self.assert_model_not_exists("fake_model_ef_b/1")

    def test_generic_pass(self) -> None:
        self.set_models(
            {
                "fake_model_ef_a/1": {"c_id": 1},
                "fake_model_ef_c/1": {"meeting_id": 1},
            }
        )
        response = self.request(
            "fake_model_ef_b.create",
            {"meeting_id": 1, "c_generic_id": "fake_model_ef_c/1"},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("fake_model_ef_b/1")

    def test_generic_fail(self) -> None:
        self.set_models(
            {
                "fake_model_ef_a/1": {},
                "fake_model_ef_a/2": {"c_id": 1},
                "fake_model_ef_c/1": {"meeting_id": 2},
            }
        )
        response = self.request(
            "fake_model_ef_b.create",
            {"meeting_id": 1, "c_generic_id": "fake_model_ef_c/1"},
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "The following models do not belong to meeting 1: ['fake_model_ef_c/1']",
            response.json["message"],
        )
        self.assert_model_not_exists("fake_model_ef_b/1")

    def test_generic_list_pass(self) -> None:
        self.set_models(
            {
                "fake_model_ef_a/1": {"c_id": 1},
                "fake_model_ef_c/1": {"meeting_id": 1},
            }
        )
        response = self.request(
            "fake_model_ef_b.create",
            {"meeting_id": 1, "c_generic_ids": ["fake_model_ef_c/1"]},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("fake_model_ef_b/1")

    def test_generic_list_fail(self) -> None:
        self.set_models(
            {
                "fake_model_ef_a/1": {},
                "fake_model_ef_a/2": {"c_id": 1},
                "fake_model_ef_c/1": {"meeting_id": 2},
            }
        )
        response = self.request(
            "fake_model_ef_b.create",
            {"meeting_id": 1, "c_generic_ids": ["fake_model_ef_c/1"]},
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "The following models do not belong to meeting 1: ['fake_model_ef_c/1']",
            response.json["message"],
        )
        self.assert_model_not_exists("fake_model_ef_b/1")
