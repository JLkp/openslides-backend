from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class AgendaItemActionTest(BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.set_models(
            {
                "meeting/20": {"is_active_in_organization_id": 1},
                "agenda_item/111": {"meeting_id": 20},
            }
        )
        response = self.request("agenda_item.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("agenda_item/111")

    def test_delete_wrong_id(self) -> None:
        self.set_models(
            {
                "meeting/20": {"is_active_in_organization_id": 1},
                "agenda_item/112": {"meeting_id": 20},
            }
        )
        response = self.request("agenda_item.delete", {"id": 111})
        self.assert_status_code(response, 400)
        self.assert_model_exists("agenda_item/112")

    def test_delete_topic(self) -> None:
        self.set_models(
            {
                "meeting/20": {"is_active_in_organization_id": 1},
                "topic/34": {"agenda_item_id": 111, "meeting_id": 20},
                "agenda_item/111": {"content_object_id": "topic/34", "meeting_id": 20},
            }
        )
        response = self.request("agenda_item.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("agenda_item/111")
        self.assert_model_deleted("topic/34")

    def test_delete_with_motion(self) -> None:
        self.set_models(
            {
                "meeting/20": {"is_active_in_organization_id": 1},
                "motion/34": {"agenda_item_id": 111, "meeting_id": 20},
                "agenda_item/111": {"content_object_id": "motion/34", "meeting_id": 20},
            }
        )
        response = self.request("agenda_item.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("agenda_item/111")
        self.get_model("motion/34")

    def test_delete_no_permissions(self) -> None:
        self.base_permission_test(
            {
                "motion/34": {"agenda_item_id": 111, "meeting_id": 1},
                "agenda_item/111": {"content_object_id": "motion/34", "meeting_id": 1},
            },
            "agenda_item.delete",
            {"id": 111},
        )

    def test_delete_permissions(self) -> None:
        self.base_permission_test(
            {
                "motion/34": {"agenda_item_id": 111, "meeting_id": 1},
                "agenda_item/111": {"content_object_id": "motion/34", "meeting_id": 1},
            },
            "agenda_item.delete",
            {"id": 111},
            Permissions.AgendaItem.CAN_MANAGE,
        )
