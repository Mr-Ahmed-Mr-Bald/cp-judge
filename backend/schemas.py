from pydantic import BaseModel, ConfigDict, field_validator

class ProblemListItem(BaseModel):

  id: int
  slug: str
  title: str
  time_limit_ms: int
  memory_limit_mb: int
  tags: list[str]

  @field_validator("tags", mode="wrap")
  @classmethod
  def flatten_tags(cls, v):
    try:
      return [t.name for t in v]
    except (AttributeError, TypeError) as e:
      raise ValueError(f"Expected a list of tag objects. Got {v}") from e


class ProblemDetail(ProblemListItem):
  test_count: int
  statement_md: str