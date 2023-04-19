from typing import Any, Protocol, runtime_checkable, Type, TypeVar


_T = TypeVar("_T")


@runtime_checkable
class Snapshotable(Protocol):
    """Classes adhering to this protocol must implement the schism snapshot method. Snapshotables need to be able to
    return a dictionary of attributes names & their values that are a snapshot of the current state of the instance.
    These snapshots are used for serialization of the instance."""

    def __schism_snapshot__(self: _T) -> dict[str, Any]:
        """Creates a dictionary of attribute names & their values that are a snapshot of the current state of the
        instance. These snapshots are used for serialization of the instance."""


@runtime_checkable
class FromSnapshotable(Protocol):
    """Classes adhering to this protocol must implement the schism from snapshot method. FromSnapshotables need to be
    able to create a new instance of the class from a snapshot dictionary, loading the attribute names and assigning
    them the provided values."""

    @classmethod
    def __schism_from_snapshot__(cls: Type[_T], state: dict[str, Any]) -> _T:
        """Creates an instance of the class from a snapshot dictionary, loading the attribute names and assigning them
        the provided values."""


@runtime_checkable
class Serializable(Snapshotable, FromSnapshotable, Protocol):
    """Classes adhering to this protocol must implement both the Snapshotable and FromSnapshotable protocols."""
