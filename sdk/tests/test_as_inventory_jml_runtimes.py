"""SDK-level GQL tests for the JML event (JmlPolicyRuntime) reads on AndromedaInventory.

The queries are built against a real (minimal) schema, so a wrong root or field raises at
construction. Two schemas: one with the fields added in #20563 (skipReason,
ruleEvaluationReason) and one without, as an older apiserver serves it.
"""
from unittest.mock import MagicMock

import pytest
from gql.transport.exceptions import TransportQueryError
from graphql import build_schema, print_ast

from sdk.as_inventory import AndromedaInventory

_SDL = """
input Filter { equals: String icontains: String }
input TimestampFilter { greaterThanOrEquals: String }
input PageArgs { pageSize: Int skip: Int }
input JmlPolicyRuntimeFilters {
  isDryRun: Boolean identityId: Filter eventType: Filter policyName: Filter
  startedAt: TimestampFilter completedAt: TimestampFilter or: JmlPolicyRuntimeFilters
}
input JmlActionRuntimeFilters { attemptCount: Filter status: Filter }
input JmlRuleRuntimeFilters { jmlRuleId: Filter }

type PageInfo { count: Int }
type JmlPolicy { id: String name: String }
type JmlRule { id: String name: String }
type Provider { id: String name: String }
type HrIdentityInfo {
  hireDate: String terminationDate: String department: String positionTitle: String
  managerName: String
}
type Identity { name: String orgInfo: HrIdentityInfo }
type ChangedAttributeNode { name: String oldValue: String newValue: String }
type TriggerSpecificationNode {
  eventType: String triggerType: String totalAttemptCount: Int identityId: String
  provider: Provider changedAttributes: [ChangedAttributeNode!] identity: Identity
}
type ExecutionStatus { status: String startedAt: String completedAt: String }
type JmlPolicyRuntimeActionStatusSummary { status: String count: Int }
type JmlPolicyRuntimeSummary {
  totalActionCount: Int actionsGroupedByStatus: [JmlPolicyRuntimeActionStatusSummary!]
}
type ErrorDetails { errorCode: String errorMessage: String }
type JmlActionRuntimeNode {
  actionType: String status: String attemptCount: Int scheduledAt: String
  startedAt: String completedAt: String parentJmlRule: JmlRule errorDetails: ErrorDetails
  %(skip_reason)s
}
type JmlActionRuntimeEdge { node: JmlActionRuntimeNode! }
type JmlActionRuntimeConnection { edges: [JmlActionRuntimeEdge!]! pageInfo: PageInfo! }
type ConditionGroupEvaluation { results: [Boolean!] }
type JmlRuleRuntimeNode {
  jmlRuleId: String ruleEvaluationStatus: String jmlRule: JmlRule
  conditionEvaluations: [ConditionGroupEvaluation!]
  %(rule_reason)s
}
type JmlRuleRuntimeEdge { node: JmlRuleRuntimeNode! }
type JmlRuleRuntimeConnection { edges: [JmlRuleRuntimeEdge!] pageInfo: PageInfo }
type JmlPolicyRuntimeNode {
  id: String jmlPolicy: JmlPolicy triggerSpecification: TriggerSpecificationNode
  executionStatus: ExecutionStatus policyRuntimeSummary: JmlPolicyRuntimeSummary
  actions(pageArgs: PageArgs, filters: JmlActionRuntimeFilters): JmlActionRuntimeConnection
  rules(pageArgs: PageArgs, filters: JmlRuleRuntimeFilters): JmlRuleRuntimeConnection
}
type JmlPolicyRuntimeEdge { node: JmlPolicyRuntimeNode! }
type JmlPolicyRuntimeConnection { edges: [JmlPolicyRuntimeEdge!]! pageInfo: PageInfo }
type Query {
  JmlPolicyRuntimes(pageArgs: PageArgs, filters: JmlPolicyRuntimeFilters): JmlPolicyRuntimeConnection
  JmlPolicyRuntime(id: String!): JmlPolicyRuntimeNode
}
"""
_NEW = _SDL % {"skip_reason": "skipReason: String", "rule_reason": "ruleEvaluationReason: String"}
_OLD = _SDL % {"skip_reason": "", "rule_reason": ""}


def _inventory(sdl=_NEW, data=None, error=None):
    """Inventory whose execute() returns `data` (or raises `error`)."""
    inv = AndromedaInventory.__new__(AndromedaInventory)
    inv.gql_client = MagicMock()
    inv.gql_client.schema = build_schema(sdl)
    if error is not None:
        inv.gql_client.execute.side_effect = error
    else:
        inv.gql_client.execute.return_value.formatted = {"data": data}
    return inv


def _query_text(inv):
    return print_ast(inv.gql_client.execute.call_args[0][0])


def _error(data, errors):
    return TransportQueryError(errors[0]["message"], errors=errors, data=data)


# --- list ---

def test_runtimes_query_and_parse():
    conn = {"pageInfo": {"count": 1}, "edges": [{"node": {"id": "rt1"}}]}
    inv = _inventory(data={"JmlPolicyRuntimes": conn})
    got, incomplete = inv.get_jml_policy_runtimes({"isDryRun": False}, page_size=25, skip=100)
    assert got == conn and incomplete == []
    text = _query_text(inv)
    assert "JmlPolicyRuntimes(" in text and "skip: 100" in text and "pageSize: 25" in text
    assert "changedAttributes" in text and "policyRuntimeSummary" in text


def test_runtimes_keep_partial_data_when_a_nested_field_fails():
    conn = {"pageInfo": {"count": 1}, "edges": [{"node": {"id": "rt1", "jmlPolicy": None}}]}
    inv = _inventory(error=_error({"JmlPolicyRuntimes": conn}, [
        {"message": "Object of type jml policy with id p1 not found",
         "path": ["JmlPolicyRuntimes", "edges", 0, "node", "jmlPolicy"],
         "extensions": {"code": 404}}]))
    got, incomplete = inv.get_jml_policy_runtimes({}, page_size=25)
    assert got == conn
    assert incomplete == ["JmlPolicyRuntimes.edges.0.node.jmlPolicy"]


def test_runtimes_raise_when_nothing_came_back():
    inv = _inventory(error=_error(None, [{"message": "boom"}]))
    with pytest.raises(TransportQueryError):
        inv.get_jml_policy_runtimes({}, page_size=25)


# --- one event ---

def test_unknown_runtime_id_is_none():
    inv = _inventory(error=_error({"JmlPolicyRuntime": None}, [
        {"message": "Object of type jml policy runtime with id x not found",
         "path": ["JmlPolicyRuntime"], "extensions": {"code": 404}}]))
    assert inv.get_jml_policy_runtime_head("x") == (None, [])


def test_head_query():
    node = {"id": "rt1", "triggerSpecification": {"totalAttemptCount": 2}}
    inv = _inventory(data={"JmlPolicyRuntime": node})
    assert inv.get_jml_policy_runtime_head("rt1") == (node, [])
    text = _query_text(inv)
    assert 'JmlPolicyRuntime(id: "rt1")' in text and "totalAttemptCount" in text


def test_actions_ask_for_skip_reason_only_when_the_server_has_it():
    inv = _inventory(_NEW, data={"JmlPolicyRuntime": {"id": "rt1", "actions": None}})
    inv.get_jml_policy_runtime_actions("rt1", {"attemptCount": {"equals": "0"}}, page_size=100)
    assert "skipReason" in _query_text(inv)

    old = _inventory(_OLD, data={"JmlPolicyRuntime": {"id": "rt1", "actions": None}})
    old.get_jml_policy_runtime_actions("rt1", {"attemptCount": {"equals": "0"}}, page_size=100)
    text = _query_text(old)
    assert "skipReason" not in text and "errorDetails" in text


def test_rule_evaluations_ask_for_reason_only_when_the_server_has_it():
    inv = _inventory(_NEW, data={"JmlPolicyRuntime": {"id": "rt1", "rules": None}})
    inv.get_jml_policy_runtime_rule_evaluations("rt1", None, page_size=100)
    text = _query_text(inv)
    assert "ruleEvaluationReason" in text and "filters" not in text

    old = _inventory(_OLD, data={"JmlPolicyRuntime": {"id": "rt1", "rules": None}})
    old.get_jml_policy_runtime_rule_evaluations("rt1", {"jmlRuleId": {"equals": "r1"}}, page_size=100)
    text = _query_text(old)
    assert "ruleEvaluationReason" not in text and "conditionEvaluations" in text
    assert "jmlRuleId" in text and "filters" in text
