"""Use-case: удаление объекта."""

from objects_app.repository.protocol import ObjectRepository


class DeleteObjectUseCase:
    def __init__(self, object_repo: ObjectRepository):
        self.object_repo = object_repo

    def execute(self, obj_id: int) -> None:
        self.object_repo.delete(obj_id)
