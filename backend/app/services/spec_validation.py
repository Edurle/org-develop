"""Validation for UI spec element locators."""

import re

# Allowed locator types
_LOCATOR_TYPES = {"data-testid", "name"}

# Element roles
_ELEMENT_ROLES = {"interactive", "display"}

# data-testid naming pattern: {area}-{description}-{suffix}
_TESTID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(-[a-z][a-z0-9]*){1,4}$")

# Type suffixes for data-testid
_TYPE_SUFFIXES = {
    "btn", "input", "select", "checkbox", "radio", "switch",
    "link", "icon", "dialog", "form", "table", "list", "card",
    "tab", "menu", "tooltip", "badge", "alert", "text", "count",
}


def validate_ui_spec_content(content: dict) -> list[str]:
    """
    Validate UI spec content structure, including element locators.
    Returns list of warning/error messages. Empty list = valid.
    """
    messages: list[str] = []
    global_testids: set[str] = set()

    # Validate common_components if present
    common_components = content.get("common_components", [])
    component_ids: set[str] = set()
    for comp in common_components:
        comp_id = comp.get("component_id", "")
        if not comp_id:
            messages.append("Common component missing 'component_id'")
            continue
        if comp_id in component_ids:
            messages.append(f"Duplicate component_id: '{comp_id}'")
        component_ids.add(comp_id)
        msgs = _validate_elements(
            comp.get("elements", []), f"component:{comp_id}", global_testids
        )
        messages.extend(msgs)

    # Validate views
    views = content.get("views", [])
    if not views and not common_components:
        messages.append("UI spec must have at least one view or common_component")

    view_routes: set[str] = set()
    for view in views:
        route = view.get("route", "")
        if not route:
            messages.append("View missing 'route'")
        elif route in view_routes:
            messages.append(f"Duplicate view route: '{route}'")
        view_routes.add(route)

        # Check component references
        for comp_ref in view.get("components", []):
            if comp_ref not in component_ids:
                messages.append(
                    f"View '{route}' references undefined component: '{comp_ref}'"
                )

        msgs = _validate_elements(
            view.get("elements", []), f"view:{route}", global_testids
        )
        messages.extend(msgs)

    return messages


def _validate_elements(
    elements: list[dict], context: str, global_testids: set[str]
) -> list[str]:
    """Validate a list of element definitions."""
    messages: list[str] = []

    for i, elem in enumerate(elements):
        prefix = f"{context}:element[{i}]"

        # Validate role
        role = elem.get("role", "")
        if role not in _ELEMENT_ROLES:
            messages.append(f"{prefix}: invalid role '{role}'")

        # Validate description
        if not elem.get("description"):
            messages.append(f"{prefix}: missing description")

        # Validate locator
        locator = elem.get("locator", {})
        loc_type = locator.get("type", "")
        loc_value = locator.get("value", "")

        if loc_type not in _LOCATOR_TYPES:
            messages.append(
                f"{prefix}: invalid locator type '{loc_type}'. "
                f"Must be one of: {', '.join(_LOCATOR_TYPES)}"
            )
            continue

        if not loc_value:
            messages.append(f"{prefix}: missing locator value")
            continue

        # Validate data-testid format
        if loc_type == "data-testid":
            if loc_value in global_testids:
                messages.append(f"{prefix}: duplicate data-testid '{loc_value}'")
            global_testids.add(loc_value)

            if not _TESTID_PATTERN.match(loc_value):
                messages.append(
                    f"{prefix}: data-testid '{loc_value}' doesn't follow "
                    "naming convention: {area}-{description}-{type_suffix}"
                )

        # Validate name format
        if loc_type == "name":
            if not re.match(r"^[a-z][a-z0-9]*(-[a-z][a-z0-9]*)*$", loc_value):
                messages.append(
                    f"{prefix}: name '{loc_value}' should be lowercase "
                    "with hyphens"
                )

    return messages
