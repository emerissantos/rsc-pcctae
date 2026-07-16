from __future__ import annotations

from apps.integracoes.common.exceptions import IntegrationInvalidResponseError

from ..client import UFSBApiClient
from ..mappers import map_servidor
from ..schemas import ServidorInstitucionalDTO


class ServidoresUFSBService:
    def __init__(self, client: UFSBApiClient | None = None):
        self.client = client or UFSBApiClient()

    def list_by_id_institucional(self, id_institucional: int) -> list[ServidorInstitucionalDTO]:
        query_params = self.client.config.get("QUERY_PARAMS", {})
        param_name = query_params.get(
            "SERVIDOR_ID_INSTITUCIONAL",
            "id-institucional",
        )
        result = self.client.get(
            self.client.config["ENDPOINTS"]["SERVIDORES"],
            params={param_name: id_institucional},
        )
        payload = result.data
        if isinstance(payload, dict):
            records = [payload]
        elif isinstance(payload, list):
            records = payload
        else:
            raise IntegrationInvalidResponseError()

        servidores = [map_servidor(item) for item in records if isinstance(item, dict)]
        return [item for item in servidores if item.id_institucional == id_institucional]
