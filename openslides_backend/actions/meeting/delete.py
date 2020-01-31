import fastjsonschema  # type: ignore

from ...models.meeting import Meeting
from ...shared.permissions.meeting import MEETING_CAN_MANAGE
from ...shared.schema import schema_version
from ..actions import register_action
from ..generics import DeleteAction

delete_meeting_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "title": "Delete meetings schema",
        "description": "An array of meetings to be deleted.",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {"id": Meeting().get_schema("id")},
            "required": ["id"],
        },
        "minItems": 1,
        "uniqueItems": True,
    }
)


@register_action("meeting.delete")
class MeetingDelete(DeleteAction):
    """
    Action to delete meetings.
    """

    model = Meeting()
    schema = delete_meeting_schema
    permission_reference = "committee_id"
    manage_permission = MEETING_CAN_MANAGE
