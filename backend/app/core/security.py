from fastapi import HTTPException, status


def require_resource_owner(resource_user_id: str, current_user_id: str) -> None:
    """Minimal ownership guard to be integrated with authentication later."""
    if resource_user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this resource.",
        )
