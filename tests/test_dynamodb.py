"""Tests for the DynamoDB cost-analysis command."""

from unittest.mock import MagicMock, patch

import pytest

from aws_cloud_utilities.commands.dynamodb import (
    _build_summary,
    _collect_region,
    _compute_provisioned_cost,
    _describe_table,
    _list_tables_in_region,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_describe_response(
    name: str,
    billing_mode: str = "PROVISIONED",
    rcu: int = 10,
    wcu: int = 5,
    item_count: int = 100,
    size_bytes: int = 1024,
) -> dict:
    """Return a minimal describe_table response body."""
    tbl: dict = {
        "TableName": name,
        "ItemCount": item_count,
        "TableSizeBytes": size_bytes,
    }
    if billing_mode == "PAY_PER_REQUEST":
        tbl["BillingModeSummary"] = {"BillingMode": "PAY_PER_REQUEST"}
        tbl["ProvisionedThroughput"] = {"ReadCapacityUnits": 0, "WriteCapacityUnits": 0}
    else:
        tbl["ProvisionedThroughput"] = {
            "ReadCapacityUnits": rcu,
            "WriteCapacityUnits": wcu,
        }
    return {"Table": tbl}


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------


class TestComputeProvisionedCost:
    """Cost formula: (rcu + wcu) * 0.0072 * 24 * 30."""

    def test_zero_capacity(self):
        assert _compute_provisioned_cost(0, 0) == 0.0

    def test_known_values(self):
        # 5 RCU + 5 WCU = 10 units -> 10 * 0.0072 * 720 = 51.84
        result = _compute_provisioned_cost(5, 5)
        assert abs(result - 51.84) < 0.001

    def test_rcu_only(self):
        result = _compute_provisioned_cost(10, 0)
        assert abs(result - 10 * 0.0072 * 720) < 0.001


class TestDescribeTable:
    """_describe_table normalises the boto3 response."""

    def test_provisioned_table_has_numeric_cost(self):
        client = MagicMock()
        client.describe_table.return_value = _make_describe_response(
            "orders", rcu=5, wcu=5
        )

        record = _describe_table(client, "orders", "us-east-1")

        assert record is not None
        assert record["billing_mode"] == "PROVISIONED"
        assert record["rcu"] == 5
        assert record["wcu"] == 5
        assert record["estimated_monthly_cost"] is not None
        assert (
            abs(record["estimated_monthly_cost"] - _compute_provisioned_cost(5, 5))
            < 0.001
        )
        assert record["item_count"] == 100

    def test_on_demand_table_cost_is_none(self):
        client = MagicMock()
        client.describe_table.return_value = _make_describe_response(
            "events", billing_mode="PAY_PER_REQUEST"
        )

        record = _describe_table(client, "events", "us-west-2")

        assert record is not None
        assert record["billing_mode"] == "PAY_PER_REQUEST"
        assert record["estimated_monthly_cost"] is None

    def test_exception_returns_none(self):
        client = MagicMock()
        client.describe_table.side_effect = Exception("throttled")

        record = _describe_table(client, "missing", "us-east-1")

        assert record is None

    def test_missing_billing_mode_summary_defaults_to_provisioned(self):
        """A table with no BillingModeSummary should be treated as PROVISIONED."""
        client = MagicMock()
        # Simulate a table that has no BillingModeSummary key at all
        resp = {
            "Table": {
                "TableName": "legacy",
                "ItemCount": 0,
                "TableSizeBytes": 0,
                "ProvisionedThroughput": {
                    "ReadCapacityUnits": 20,
                    "WriteCapacityUnits": 10,
                },
            }
        }
        client.describe_table.return_value = resp

        record = _describe_table(client, "legacy", "us-east-1")

        assert record is not None
        assert record["billing_mode"] == "PROVISIONED"
        assert record["estimated_monthly_cost"] is not None


class TestListTablesInRegion:
    """_list_tables_in_region handles single-page and multi-page responses."""

    def test_single_page(self):
        client = MagicMock()
        client.list_tables.return_value = {"TableNames": ["a", "b"]}

        result = _list_tables_in_region(client)

        assert result == ["a", "b"]
        client.list_tables.assert_called_once_with()

    def test_pagination_followed(self):
        client = MagicMock()
        client.list_tables.side_effect = [
            {"TableNames": ["a", "b"], "LastEvaluatedTableName": "b"},
            {"TableNames": ["c"]},
        ]

        result = _list_tables_in_region(client)

        assert result == ["a", "b", "c"]
        assert client.list_tables.call_count == 2
        # Second call must pass the continuation token
        client.list_tables.assert_called_with(ExclusiveStartTableName="b")

    def test_empty_account(self):
        client = MagicMock()
        client.list_tables.return_value = {"TableNames": []}

        result = _list_tables_in_region(client)

        assert result == []


class TestCollectRegion:
    """_collect_region wires list + describe and uses threading."""

    def test_returns_records_for_tables(self):
        mock_auth = MagicMock()
        mock_client = MagicMock()
        mock_auth.get_client.return_value = mock_client
        mock_client.list_tables.return_value = {"TableNames": ["tbl1"]}
        mock_client.describe_table.return_value = _make_describe_response("tbl1")

        records = _collect_region(mock_auth, "us-east-1", workers=2)

        assert len(records) == 1
        assert records[0]["name"] == "tbl1"

    def test_returns_empty_on_list_error(self):
        mock_auth = MagicMock()
        mock_auth.get_client.side_effect = Exception("no credentials")

        records = _collect_region(mock_auth, "ap-south-1", workers=1)

        assert records == []

    def test_zero_tables_returns_empty(self):
        mock_auth = MagicMock()
        mock_client = MagicMock()
        mock_auth.get_client.return_value = mock_client
        mock_client.list_tables.return_value = {"TableNames": []}

        records = _collect_region(mock_auth, "eu-west-1", workers=2)

        assert records == []


class TestBuildSummary:
    """_build_summary computes totals, top-N, empty-but-expensive, and prefix groups."""

    def _provisioned(self, name: str, rcu: int, wcu: int, item_count: int = 10) -> dict:
        cost = _compute_provisioned_cost(rcu, wcu)
        return {
            "name": name,
            "region": "us-east-1",
            "billing_mode": "PROVISIONED",
            "rcu": rcu,
            "wcu": wcu,
            "item_count": item_count,
            "estimated_monthly_cost": cost,
        }

    def _on_demand(self, name: str) -> dict:
        return {
            "name": name,
            "region": "us-east-1",
            "billing_mode": "PAY_PER_REQUEST",
            "rcu": 0,
            "wcu": 0,
            "item_count": 50,
            "estimated_monthly_cost": None,
        }

    def test_totals_exclude_on_demand(self):
        tables = [
            self._provisioned("proj-orders", rcu=10, wcu=5),
            self._on_demand("proj-events"),
        ]

        summary = _build_summary(tables, top_n=10)

        assert summary["provisioned_tables"] == 1
        assert summary["on_demand_tables"] == 1
        assert summary["total_provisioned_rcu"] == 10
        assert summary["total_provisioned_wcu"] == 5
        expected_cost = _compute_provisioned_cost(10, 5)
        assert abs(summary["total_estimated_monthly_cost_usd"] - expected_cost) < 0.001

    def test_top_n_sorted_by_cost(self):
        tables = [
            self._provisioned("cheap", rcu=1, wcu=1),
            self._provisioned("expensive", rcu=100, wcu=100),
            self._provisioned("medium", rcu=10, wcu=10),
        ]

        summary = _build_summary(tables, top_n=2)

        names = [t["name"] for t in summary["top_expensive_tables"]]
        assert names[0] == "expensive"
        assert names[1] == "medium"
        assert len(names) == 2

    def test_empty_but_expensive_detection(self):
        tables = [
            self._provisioned("dead-table", rcu=50, wcu=50, item_count=0),
            self._provisioned("active-table", rcu=50, wcu=50, item_count=1000),
            self._provisioned(
                "tiny-dead", rcu=0, wcu=0, item_count=0
            ),  # cost==0, excluded
        ]

        summary = _build_summary(tables, top_n=10)

        empty_names = [t["name"] for t in summary["empty_but_expensive_tables"]]
        assert "dead-table" in empty_names
        assert "active-table" not in empty_names
        # tiny-dead has cost 0.0, not > 1.0, should be excluded
        assert "tiny-dead" not in empty_names

    def test_cost_by_prefix_grouping(self):
        tables = [
            self._provisioned("alpha-orders", rcu=10, wcu=0),
            self._provisioned("alpha-users", rcu=10, wcu=0),
            self._provisioned("beta-events", rcu=5, wcu=0),
        ]

        summary = _build_summary(tables, top_n=10)

        prefix_totals = summary["cost_by_project_prefix"]
        alpha_expected = _compute_provisioned_cost(10, 0) * 2
        beta_expected = _compute_provisioned_cost(5, 0)

        assert abs(prefix_totals["alpha"] - alpha_expected) < 0.001
        assert abs(prefix_totals["beta"] - beta_expected) < 0.001

    def test_empty_table_list(self):
        summary = _build_summary([], top_n=10)

        assert summary["total_tables"] == 0
        assert summary["total_estimated_monthly_cost_usd"] == 0.0
        assert summary["top_expensive_tables"] == []
        assert summary["empty_but_expensive_tables"] == []
        assert summary["cost_by_project_prefix"] == {}
