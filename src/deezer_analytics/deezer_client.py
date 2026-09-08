"""Client HTTP pour l'API publique Deezer."""

from __future__ import annotations

from typing import Any

import requests
from requests import Response
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class DeezerAPIError(Exception):
    """Exception levée lorsqu'une requête vers l'API Deezer échoue."""


class DeezerClient:
    """Client permettant d'interagir avec l'API publique Deezer."""

    DEFAULT_BASE_URL = "https://api.deezer.com"
    DEFAULT_TIMEOUT = 10.0
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_BACKOFF_FACTOR = 1.0

    RETRY_STATUS_CODES = (429, 500, 502, 503, 504)

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
    ) -> None:
        if not base_url:
            raise ValueError("base_url doit être renseigné.")

        if timeout <= 0:
            raise ValueError("timeout doit être strictement positif.")

        if max_retries < 0:
            raise ValueError("max_retries doit être positif ou nul.")

        if backoff_factor < 0:
            raise ValueError("backoff_factor doit être positif ou nul.")

        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._session = self._create_session(
            max_retries=max_retries,
            backoff_factor=backoff_factor,
        )

    def _create_session(
        self,
        max_retries: int,
        backoff_factor: float,
    ) -> requests.Session:
        """Crée une session HTTP configurée avec une stratégie de retry."""

        retry_strategy = Retry(
            total=max_retries,
            connect=max_retries,
            read=max_retries,
            status=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=self.RETRY_STATUS_CODES,
            allowed_methods={"GET"},
            respect_retry_after_header=True,
            raise_on_status=False,
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)

        session = requests.Session()
        session.mount("https://", adapter)

        session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": "DeezerTechnicalTest",
            }
        )

        return session

    def _build_url(self, endpoint: str) -> str:
        """Construit l'URL complète d'un endpoint Deezer."""

        endpoint = endpoint.lstrip("/")

        if not endpoint:
            raise ValueError("un endpoint doit être renseigné.")

        return f"{self._base_url}/{endpoint}"

    def _extract_error_message(self, response: Response) -> str | None:
            """Extrait le message d'erreur fourni par l'API Deezer."""
    
            try:
                data = response.json()
            except ValueError:
                return None
    
            if not isinstance(data, dict):
                return None
    
            error = data.get("error")
    
            if not isinstance(error, dict):
                return None
    
            message = error.get("message")
    
            if isinstance(message, str) and message:
                return message
    
            return None

    def _raise_for_status(self, response: Response) -> None:
        """Transforme une réponse HTTP en exception si nécessaire."""

        if response.ok:
            return

        status_code = response.status_code
        error_message = self._extract_error_message(response)

        if error_message:
            message = (
                f"L'API Deezer a retourné HTTP {status_code} : "
                f"{error_message}"
            )
        else:
            message = (
                f"L'API Deezer a retourné HTTP {status_code} "
                f"({response.reason})."
            )

        raise DeezerAPIError(message)

    def get(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Effectue une requête GET vers l'API Deezer.

        Args:
            endpoint: Endpoint de l'API (par ex: /search).
            params: Paramètres de la requête.

        Returns:
            Réponse JSON décodée.

        Raises:
            DeezerAPIError: Si l'API retourne une erreur HTTP ou
                            une réponse JSON invalide.
        """

        url = self._build_url(endpoint)

        try:
            response = self._session.get(
                url,
                params=params,
                timeout=self._timeout,
            )
        except requests.RequestException as exc:
            raise DeezerAPIError(
                f"Erreur lors de la requête vers Deezer : {url}"
            ) from exc

        self._raise_for_status(response)

        try:
            data = response.json()
        except ValueError as exc:
            raise DeezerAPIError(
                f"La réponse de Deezer n'est pas un JSON valide : {url}"
            ) from exc

        if not isinstance(data, dict):
            raise DeezerAPIError(
                "La réponse de Deezer doit être un objet JSON."
            )

        return data

    def close(self) -> None:
        """Ferme la session HTTP."""

        self._session.close()

    def __enter__(self) -> DeezerClient:
        """Retourne le client pour l'utilisation avec with."""

        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: Any,
    ) -> None:
        """Ferme automatiquement la session."""

        self.close()
