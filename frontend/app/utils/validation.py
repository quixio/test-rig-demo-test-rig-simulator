import typing

from app.utils.exceptions import ValidationError


class Error422(typing.TypedDict):
    detail: list[dict]


def raise_from_422(errors: Error422):
    for err in errors["detail"]:
        loc = err.get("loc", [])
        # Ignore the first part (usually "body")
        if len(loc) > 1:
            field = loc[1]
        else:
            field = loc[-1]
        message = err.get("msg", "Invalid value")
        # TODO: Return all validation errors in one exception (field and non-field)
        raise ValidationError(field=field, message=message)
