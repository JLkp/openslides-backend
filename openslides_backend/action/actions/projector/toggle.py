from typing import Any, Dict, List

from ....models.models import Projection, Projector
from ....permissions.permissions import Permissions
from ....shared.filters import And, FilterOperator
from ....shared.patterns import Collection, FullQualifiedId, string_to_fqid
from ....shared.schema import required_id_schema
from ...generics.update import UpdateAction
from ...util.assert_belongs_to_meeting import assert_belongs_to_meeting
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from ..projection.create import ProjectionCreate
from ..projection.delete import ProjectionDelete
from ..projection.update import ProjectionUpdate


@register_action("projector.toggle")
class ProjectorToggle(UpdateAction):
    """
    Action to toggle projections.
    """

    model = Projector()
    schema = DefaultSchema(Projection()).get_default_schema(
        title="Projector toggle stable schema",
        required_properties=["content_object_id", "meeting_id"],
        optional_properties=["options", "type", "stable"],
        additional_required_fields={
            "ids": {
                "type": "array",
                "items": required_id_schema,
                "uniqueItems": True,
                "minItems": 1,
            },
        },
    )
    permission = Permissions.Projector.CAN_MANAGE

    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        for instance in action_data:
            # check meeting ids from projector ids and content_object
            meeting_id = instance["meeting_id"]
            fqid_content_object = string_to_fqid(instance["content_object_id"])
            assert_belongs_to_meeting(
                self.datastore,
                [fqid_content_object]
                + [
                    FullQualifiedId(Collection("projector"), id)
                    for id in instance["ids"]
                ],
                meeting_id,
            )

            for projector_id in instance["ids"]:
                stable = instance.get("stable", False)
                filter_ = And(
                    FilterOperator("current_projector_id", "=", projector_id),
                    FilterOperator(
                        "content_object_id", "=", instance["content_object_id"]
                    ),
                    FilterOperator("stable", "=", stable),
                )
                if instance.get("type"):
                    filter_ = And(
                        filter_, FilterOperator("type", "=", instance["type"])
                    )
                result = self.datastore.filter(
                    Collection("projection"), filter_, ["id"]
                )
                if result:
                    projection_ids = [id_ for id_ in result]
                    if stable:
                        self.execute_other_action(
                            ProjectionDelete, [{"id": id_} for id_ in projection_ids]
                        )
                    else:
                        self.move_projections_to_history(projector_id, projection_ids)
                else:
                    data: Dict[str, Any] = {
                        "current_projector_id": projector_id,
                        "stable": stable,
                        "type": instance.get("type"),
                        "content_object_id": instance["content_object_id"],
                        "options": instance.get("options"),
                        "meeting_id": meeting_id,
                    }
                    self.execute_other_action(ProjectionCreate, [data])
        return []

    def move_projections_to_history(
        self, projector_id: int, projection_ids: List[int]
    ) -> None:
        max_weight = self.get_max_projection_weight(projector_id)
        for projection_id in projection_ids:
            self.execute_other_action(
                ProjectionUpdate,
                [
                    {
                        "id": int(projection_id),
                        "current_projector_id": None,
                        "history_projector_id": projector_id,
                        "weight": max_weight + 1,
                    }
                ],
            )
            max_weight += 1

    def get_max_projection_weight(self, projector_id: int) -> int:
        filter_ = FilterOperator("history_projector_id", "=", projector_id)
        maximum = self.datastore.max(Collection("projection"), filter_, "weight", "int")
        if maximum is None:
            maximum = 0
        return maximum