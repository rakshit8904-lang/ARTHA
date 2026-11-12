"""Household-shared versus private items (goals, profile entries).

Household items: every member reads, owners write. Private items: only the
creator and household owners can see or edit them. Only the creator can
change who sees an item, so an owner cannot expose someone's private entry.
"""
from app.constants import ROLE_OWNER
from app.errors import Unauthorized

HOUSEHOLD, PRIVATE = "household", "private"
CHOICES = {HOUSEHOLD: "Everyone in this household", PRIVATE: "Only me (household owners can also see it)"}


def visible(query, model, user_id, role):
    if role == ROLE_OWNER:
        return query
    return query.filter((model.visibility == HOUSEHOLD) | (model.created_by == user_id))


def can_edit(item, user_id, role):
    return role == ROLE_OWNER or (item.visibility == PRIVATE and item.created_by == user_id)


def check_write(item, new_visibility, user_id, role):
    """item is None for a new entry. Raises Unauthorized when the change is not allowed."""
    if new_visibility not in CHOICES:
        raise ValueError("Choose who can see this.")
    if new_visibility == HOUSEHOLD and role != ROLE_OWNER:
        raise Unauthorized("Only household owners can add or share items with everyone. You can keep it private.")
    if item is None:
        return
    if not can_edit(item, user_id, role):
        raise Unauthorized("You can't change this item.")
    if new_visibility != item.visibility and item.created_by != user_id:
        raise Unauthorized("Only the person who created this can change who sees it.")
