"""Клиент для работы с GitLab API."""

from typing import Any, Dict, List, Optional

import requests

from code_review_backend.config import config


class GitLabClient:
    """Клиент для взаимодействия с GitLab API."""
    
    def __init__(self):
        self.api_url = config.gitlab.api_url
        self.token = config.gitlab.access_token
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Выполняет HTTP запрос к GitLab API."""
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        
        response = requests.request(
            method=method,
            url=url,
            headers=self.headers,
            params=params,
            json=json_data,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    
    def get_mr_info(self, project_id: str, mr_iid: int) -> Dict[str, Any]:
        """Получает информацию о Merge Request."""
        endpoint = f"projects/{project_id}/merge_requests/{mr_iid}"
        return self._request("GET", endpoint)
    
    def get_mr_changes(self, project_id: str, mr_iid: int) -> Dict[str, Any]:
        """Получает изменения в Merge Request (diff)."""
        endpoint = f"projects/{project_id}/merge_requests/{mr_iid}/changes"
        return self._request("GET", endpoint)
    
    def get_mr_notes(self, project_id: str, mr_iid: int) -> List[Dict[str, Any]]:
        """Получает все комментарии (notes) в Merge Request."""
        endpoint = f"projects/{project_id}/merge_requests/{mr_iid}/notes"
        return self._request("GET", endpoint)
    
    def post_mr_comment(
        self,
        project_id: str,
        mr_iid: int,
        body: str,
        position: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Добавляет комментарий к Merge Request.
        
        Args:
            project_id: ID проекта
            mr_iid: IID Merge Request
            body: Текст комментария
            position: Позиция для inline комментария (опционально)
        """
        endpoint = f"projects/{project_id}/merge_requests/{mr_iid}/notes"
        data = {"body": body}
        if position:
            data["position"] = position
        return self._request("POST", endpoint, json_data=data)
    
    def update_mr_labels(self, project_id: str, mr_iid: int, labels: List[str]) -> Dict[str, Any]:
        """Обновляет лейблы Merge Request."""
        endpoint = f"projects/{project_id}/merge_requests/{mr_iid}"
        return self._request("PUT", endpoint, json_data={
            "labels": ",".join(labels)
        })
    
    def approve_mr(self, project_id: str, mr_iid: int) -> Dict[str, Any]:
        """Одобряет Merge Request."""
        endpoint = f"projects/{project_id}/merge_requests/{mr_iid}/approve"
        return self._request("POST", endpoint)
    
    def unapprove_mr(self, project_id: str, mr_iid: int) -> Dict[str, Any]:
        """Снимает одобрение с Merge Request."""
        endpoint = f"projects/{project_id}/merge_requests/{mr_iid}/unapprove"
        return self._request("POST", endpoint)
    
    def block_merge(self, project_id: str, mr_iid: int, reason: str = "") -> Dict[str, Any]:
        """Блокирует merge через установку блокирующего лейбла."""
        endpoint = f"projects/{project_id}/merge_requests/{mr_iid}"
        return self._request("PUT", endpoint, json_data={
            "labels": "ai-review-blocked",
            "merge_when_pipeline_succeeds": False
        })
    
    def unblock_merge(self, project_id: str, mr_iid: int) -> Dict[str, Any]:
        """Снимает блокировку merge."""
        endpoint = f"projects/{project_id}/merge_requests/{mr_iid}"
        mr_info = self.get_mr_info(project_id, mr_iid)
        current_labels = mr_info.get("labels", [])
        labels_without_block = [l for l in current_labels if l != "ai-review-blocked"]
        return self._request("PUT", endpoint, json_data={
            "labels": ",".join(labels_without_block) if labels_without_block else ""
        })
    
    def get_open_mrs_for_branch(self, project_id: str, source_branch: str) -> List[Dict[str, Any]]:
        """Получает список открытых MR для указанной ветки."""
        endpoint = f"projects/{project_id}/merge_requests"
        return self._request("GET", endpoint, params={
            "source_branch": source_branch,
            "state": "opened"
        })
    
    def compare_branches(self, project_id: str, from_branch: str, to_branch: str) -> Dict[str, Any]:
        """Сравнивает две ветки и возвращает diff."""
        endpoint = f"projects/{project_id}/repository/compare"
        return self._request("GET", endpoint, params={
            "from": from_branch,
            "to": to_branch
        })
