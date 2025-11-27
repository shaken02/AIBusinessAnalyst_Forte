"""Обработчик webhook событий от GitLab."""

import hmac
from typing import Any, Dict, Optional

from fastapi import Header, HTTPException, Request

from code_review_backend.config import config


def verify_webhook_signature(
    request_body: bytes,
    x_gitlab_token: Optional[str] = Header(None, alias="X-Gitlab-Token")
) -> bool:
    """
    Проверяет подпись webhook запроса от GitLab.
    
    Args:
        request_body: Тело запроса
        x_gitlab_token: Токен из заголовка X-Gitlab-Token
    
    Returns:
        True если подпись верна
    """
    if not config.gitlab.webhook_secret_token:
        return True
    
    if not x_gitlab_token:
        return False
    
    return hmac.compare_digest(
        x_gitlab_token,
        config.gitlab.webhook_secret_token
    )


def extract_mr_data(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Извлекает данные о Merge Request из webhook payload.
    
    Args:
        payload: Тело webhook запроса
    
    Returns:
        Словарь с данными MR или None если это не MR событие
    """
    object_kind = payload.get("object_kind")
    
    if object_kind != "merge_request":
        return None
    
    # GitLab может отправлять данные в разных местах
    mr_data = payload.get("object") or payload.get("object_attributes", {})
    if not mr_data:
        return None
    
    project = payload.get("project", {})
    action = payload.get("object_attributes", {}).get("action") or payload.get("action", "")
    
    return {
        "mr_iid": mr_data.get("iid"),
        "project_id": project.get("id") or project.get("project_id"),
        "mr_title": mr_data.get("title", ""),
        "mr_description": mr_data.get("description", ""),
        "author_name": mr_data.get("author", {}).get("name") or payload.get("user", {}).get("name", "Unknown"),
        "target_branch": mr_data.get("target_branch", ""),
        "source_branch": mr_data.get("source_branch", ""),
        "state": mr_data.get("state", ""),
        "action": action,
        "url": mr_data.get("url", "")
    }


def extract_push_data(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Извлекает данные о push событии из webhook payload.
    
    Args:
        payload: Тело webhook запроса
    
    Returns:
        Словарь с данными push или None если это не push событие
    """
    object_kind = payload.get("object_kind")
    
    if object_kind != "push":
        return None
    
    project = payload.get("project", {})
    ref = payload.get("ref", "")
    
    # Проверяем что это не push в main
    if ref.endswith("/main") or ref.endswith("/master"):
        return None
    
    commits = payload.get("commits", [])
    if not commits:
        return None
    
    return {
        "project_id": project.get("id"),
        "branch": ref.replace("refs/heads/", ""),
        "commits": commits,
        "author_name": commits[0].get("author", {}).get("name", "Unknown") if commits else "Unknown",
        "total_commits": len(commits)
    }
