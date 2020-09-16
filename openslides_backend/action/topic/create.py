from typing import Iterable

from ...models.topic import Topic
from ...shared.interfaces import WriteRequestElement
from ...shared.patterns import FullQualifiedId
from ..action import register_action
from ..action_interface import ActionPayload
from ..agenda_item.agenda_creation import AGENDA_PREFIX, agenda_creation_properties
from ..agenda_item.create import AgendaItemCreate
from ..base import DataSet
from ..default_schema import DefaultSchema
from ..generics import CreateAction

create_schema = DefaultSchema(Topic()).get_create_schema(
    properties=["meeting_id", "title", "text", "attachment_ids"],
    required_properties=["meeting_id", "title"],
)

create_schema["items"]["properties"].update(agenda_creation_properties)


@register_action("topic.create")
class TopicCreate(CreateAction):
    """
    Action to create simple topics that can be shown in the agenda.
    """

    model = Topic()
    schema = create_schema

    def create_write_request_elements(
        self, dataset: DataSet
    ) -> Iterable[WriteRequestElement]:
        agenda_item_creation = []

        for content_object_element in dataset["data"]:
            agenda_create_flag = content_object_element["instance"].get(
                f"{AGENDA_PREFIX}create"
            )
            meeting_id = content_object_element["instance"].get("meeting_id")
            if not self.check_agenda_creation(agenda_create_flag, meeting_id):
                continue

            additional_relation_models = {
                FullQualifiedId(
                    self.model.collection, content_object_element["new_id"]
                ): content_object_element["instance"]
            }
            action = AgendaItemCreate(
                "agenda_item.create",
                self.permission,
                self.database,
                additional_relation_models,
            )
            agenda_item_payload_element = {
                "content_object_id": f"{str(self.model.collection)}/{content_object_element['new_id']}",
            }
            for extra_field in agenda_creation_properties.keys():
                if extra_field == f"{AGENDA_PREFIX}create":
                    # This field should not be provided to the AgendaItemCreate action.
                    continue
                prefix_len = len(AGENDA_PREFIX)
                extra_field_without_prefix = extra_field[prefix_len:]
                value = content_object_element["instance"].pop(extra_field, None)
                if value is not None:
                    agenda_item_payload_element[extra_field_without_prefix] = value
            agenda_item_payload: ActionPayload = [agenda_item_payload_element]
            agenda_item_creation.append((action, agenda_item_payload))

        yield from super().create_write_request_elements(dataset)

        for action, agenda_item_payload in agenda_item_creation:
            yield from action.perform(agenda_item_payload, self.user_id)

    def check_agenda_creation(self, flag: bool = None, meeting_id: int = None) -> bool:
        # For topics this should always return True.
        return True
