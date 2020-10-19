import json
from typing import Iterator, List, Tuple

import yaml

from superset.commands.base import BaseCommand
from superset.connectors.sqla.models import SqlaTable
from superset.datasets.commands.exceptions import DatasetNotFoundError
from superset.datasets.dao import DatasetDAO
from superset.utils.dict_import_export import IMPORT_EXPORT_VERSION, sanitize


class ExportDatasetsCommand(BaseCommand):
    def __init__(self, dataset_ids: List[int]):
        self.dataset_ids = dataset_ids

        # this will be set when calling validate()
        self._models: List[SqlaTable] = []

    @staticmethod
    def export_dataset(dataset: SqlaTable) -> Iterator[Tuple[str, str]]:
        database_slug = sanitize(dataset.database.database_name)
        dataset_slug = sanitize(dataset.table_name)
        file_name = f"datasets/{database_slug}/{dataset_slug}.yaml"

        payload = dataset.export_to_dict(
            recursive=True,
            include_parent_ref=False,
            include_defaults=True,
            export_uuids=True,
        )

        payload["version"] = IMPORT_EXPORT_VERSION
        payload["database_uuid"] = str(dataset.database.uuid)

        file_content = yaml.safe_dump(payload, sort_keys=False)
        yield file_name, file_content

        # include database as well
        file_name = f"databases/{database_slug}.yaml"

        payload = dataset.database.export_to_dict(
            recursive=False,
            include_parent_ref=False,
            include_defaults=True,
            export_uuids=True,
        )
        # TODO (betodealmeida): move this logic to export_to_dict once this
        # becomes the default export endpoint
        if "extra" in payload:
            try:
                payload["extra"] = json.loads(payload["extra"])
            except json.decoder.JSONDecodeError:
                pass

        payload["version"] = IMPORT_EXPORT_VERSION

        file_content = yaml.safe_dump(payload, sort_keys=False)
        yield file_name, file_content

    def run(self) -> Iterator[Tuple[str, str]]:
        self.validate()

        seen = set()
        for dataset in self._models:
            for file_name, file_content in self.export_dataset(dataset):
                # ignore repeated databases
                if file_name not in seen:
                    yield file_name, file_content
                    seen.add(file_name)

    def validate(self) -> None:
        self._models = DatasetDAO.find_by_ids(self.dataset_ids)
        if len(self._models) != len(self.dataset_ids):
            raise DatasetNotFoundError()
