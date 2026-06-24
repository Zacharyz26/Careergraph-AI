from dataclasses import dataclass

from fastapi import Header, HTTPException, status

from app.core.config import settings


@dataclass(frozen=True)
class WorkspaceUser:
    email: str
    name: str | None = None
    auth_provider: str = "header"


async def current_workspace_user(
    user_email: str | None = Header(default=None, alias="X-CareerGraph-User-Email"),
    user_name: str | None = Header(default=None, alias="X-CareerGraph-User-Name"),
) -> WorkspaceUser:
    email = user_email.strip().casefold() if user_email else ""
    if not email:
        if settings.environment.casefold() == "production":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="A workspace user is required.",
            )
        email = settings.workspace_default_user_email
    if "@" not in email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workspace user email is invalid.",
        )
    return WorkspaceUser(email=email, name=user_name, auth_provider="header")


def require_resource_owner(resource_user_id: str, current_user_id: str) -> None:
    """Minimal ownership guard to be integrated with authentication later."""
    if resource_user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this resource.",
        )
