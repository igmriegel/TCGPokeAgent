from scripts.audit_documentation import audit_repository


def test_canonical_documentation_matches_repository() -> None:
    assert [issue.render() for issue in audit_repository()] == []
