from pydantic import AliasChoices, BaseModel, ConfigDict, Field

type EntityID = int


class ValueObject(BaseModel):
    """Immutable domain concept defined entirely by its values. No identity."""

    model_config = ConfigDict(frozen=True)


class DomainEntity(BaseModel):
    """Long-lived domain concept with a unique identity and a lifecycle."""

    id: EntityID | None = Field(
        default=None,
        description="Globally unique entity primary key.",
        validation_alias=AliasChoices("id", "experiment_id", "problem_id"),
    )

    model_config = ConfigDict(populate_by_name=True)

    @property
    def experiment_id(self) -> EntityID | None:
        """Property alias for experiment_id."""
        return self.id
