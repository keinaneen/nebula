from fastapi import Depends
from pydantic import Field
from nxtools import xml

import nebula
from server.dependencies import current_user
from server.models import RequestModel, ResponseModel
from server.request import APIRequest


class ActionsRequestModel(RequestModel):
    ids: list[int]


class ActionItemModel(ResponseModel):
    id: int = Field(..., title="Action ID")
    name: str = Field(..., title="Action name")


class ActionsResponseModel(ResponseModel):
    actions: list[ActionItemModel] = Field(
        default_factory=list,
        title="Actions",
        description="List of available actions",
    )


class ActionsRequest(APIRequest):
    """List available actions for given list of assets"""

    name: str = "actions"
    title: str = "Get available actions"
    response_model = ActionsResponseModel

    async def handle(
        self,
        request: ActionsRequestModel,
        user: nebula.User = Depends(current_user),
    ) -> ActionsResponseModel:

        result = []

        query = """
            SELECT id, service_type, title, settings
            FROM actions
            ORDER BY title ASC
        """

        async for row in nebula.db.iterate(query):
            # TODO: implement ACL
            action_settings = xml(row["settings"])

            if allow_if_elm := action_settings.findall("allow_if"):
                allow_if_cond = allow_if_elm[0].text

                for id_asset in request.ids:
                    asset = await nebula.Asset.load(id_asset)
                    assert asset
                    if not eval(allow_if_cond):
                        break
                else:
                    result.append(
                        ActionItemModel(
                            id=row["id"],
                            name=row["title"],
                        )
                    )
        nebula.log.info(f"Actions for assets {request.ids} are {result}")
        return ActionsResponseModel(actions=result)
