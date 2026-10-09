from dataclasses import asdict
from pathlib import Path
import copy
import json
import os
import subprocess
import sys

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "local-engine"))
from neoretail_local.customers import (
    automatic_tenants, customer_modules, load_customer_registry, resolve_customer, resolve_tenant,
)
from neoretail_local.settings import Settings

REGISTRY = ROOT / "local-engine/tests/fixtures/tenant_context_pending_registry.yaml"
AUTHORIZATION = ROOT / "local-engine/tests/fixtures/tenant_context_baseline_authorization.yaml"
EXPECTED = [("ambev", 142, "AMBEV"), ("pandurata", 17066, "PANDURATA"),
            ("lactalis", 290, "LACTALIS"), ("safira", 16868, "SAFIRA")]


def write_registry(tmp_path, mutate):
    document = copy.deepcopy(yaml.safe_load(REGISTRY.read_text(encoding="utf-8")))
    mutate(document)
    path = tmp_path / "customers.yaml"
    path.write_text(yaml.safe_dump(document), encoding="utf-8")
    return path


@pytest.mark.parametrize("key,customer_id,name", EXPECTED)
def test_same_context_by_key_id_name(key, customer_id, name):
    context = resolve_tenant(REGISTRY, key)
    assert context == resolve_customer(REGISTRY, customer_id) == resolve_tenant(REGISTRY, name.lower())
    assert context.tenant_key == key
    assert context.id_customer == customer_id
    assert context.nm_customer == name
    assert context.gold_schema == f"gold_{key}"
    assert context.partition == f"id_customer={customer_id}"


@pytest.mark.parametrize("selector", ["unknown", 999999, 0, -1, True, "gold_ambev", "142 OR 1=1"])
def test_unknown_tenant_fails_closed(selector):
    with pytest.raises(RuntimeError, match="Unknown"):
        resolve_tenant(REGISTRY, selector)


def test_baseline_remains_resolvable_but_not_automatic():
    ambev = resolve_tenant(REGISTRY, None)
    assert ambev == resolve_tenant(REGISTRY, "ambev")
    assert ambev.source_ready and ambev.enabled and not ambev.execution_active
    assert ambev.source_prefix == "FATO/CUSTOMER/DAILY/NM_CUSTOMER=AMBEV"
    assert ambev.source_layout == "partitioned_customer_daily_v1"
    with pytest.raises(RuntimeError, match="inactive"):
        resolve_tenant(REGISTRY, 142, automatic=True)


def test_automatic_selection_and_pending_pandurata():
    assert [c.tenant_key for c in automatic_tenants(REGISTRY, require_source=False)] == ["pandurata"]
    with pytest.raises(RuntimeError, match="pending source"):
        automatic_tenants(REGISTRY)
    for key in ("pandurata", "lactalis", "safira"):
        assert resolve_tenant(REGISTRY, key).enabled
        assert not resolve_tenant(REGISTRY, key).source_ready
        with pytest.raises(RuntimeError, match="pending source"):
            resolve_tenant(REGISTRY, key, require_source=True)
    for key in ("lactalis", "safira"):
        with pytest.raises(RuntimeError, match="inactive"):
            resolve_tenant(REGISTRY, key, automatic=True)


@pytest.mark.parametrize("field", ["id_customer", "tenant_key", "gold_schema", "nm_customer"])
def test_registry_rejects_duplicate_identity_fields(tmp_path, field):
    path = write_registry(tmp_path, lambda d: d["customers"][1].update({field: d["customers"][0][field]}))
    with pytest.raises(RuntimeError, match=f"Duplicate {field}"):
        load_customer_registry(path)


@pytest.mark.parametrize("field,value", [
    ("gold_schema", "gold.x"), ("gold_schema", 'gold";DROP SCHEMA gold;'),
    ("gold_schema", "GOLD"), ("gold_schema", "a" * 64),
    ("tenant_key", "bad-key"), ("id_customer", True), ("id_customer", "142"),
    ("id_customer", 1.2), ("id_customer", 9007199254740992),
    ("execution_active", "false"), ("enabled", 0),
    ("source_prefix", "<confirmar>"), ("source_prefix", "../other"),
    ("source_prefix", "/"), ("source_layout", ""),
])
def test_invalid_registry_record_rejected(tmp_path, field, value):
    path = write_registry(tmp_path, lambda d: d["customers"][0].update({field: value}))
    with pytest.raises(RuntimeError):
        load_customer_registry(path)


@pytest.mark.parametrize("field", ["source_prefix", "source_layout"])
def test_missing_source_blocks_execution_but_not_identity(tmp_path, field):
    path = write_registry(tmp_path, lambda d: d["customers"][0].pop(field))
    assert resolve_tenant(path, 142).id_customer == 142
    with pytest.raises(RuntimeError, match=field):
        resolve_tenant(path, 142, require_source=True)


def test_duplicate_yaml_keys_are_rejected(tmp_path):
    path = tmp_path / "customers.yaml"
    path.write_text(REGISTRY.read_text(encoding="utf-8") + "\ndefault_customer: 17066\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="Duplicate YAML key"):
        load_customer_registry(path)


def test_disabled_is_distinct_from_inactive(tmp_path):
    path = write_registry(tmp_path, lambda d: d["customers"][0].update(enabled=False))
    with pytest.raises(RuntimeError, match="disabled"):
        resolve_tenant(path, 142)


def test_key_name_ambiguity_rejected(tmp_path):
    path = write_registry(tmp_path, lambda d: d["customers"][1].update(nm_customer="AMBEV"))
    with pytest.raises(RuntimeError):
        load_customer_registry(path)
    path = write_registry(tmp_path, lambda d: d["customers"][1].update(nm_customer="ambev"))
    with pytest.raises(RuntimeError):
        load_customer_registry(path)


def test_authorization_is_separate_and_existing_access_preserved():
    document, contexts = load_customer_registry(REGISTRY)
    auth = yaml.safe_load((AUTHORIZATION).read_text(encoding="utf-8"))
    assert "customers" not in auth
    assert auth["users"][0]["allowed_customer_ids"] == [142]
    assert set(auth["customer_access"]) == {"ambev"}
    assert all("modules" not in row for row in document["customers"])
    assert customer_modules(AUTHORIZATION, contexts[0]) == (
        "visao_industria", "tarefas", "exportacao_diaria", "exportacao_mensal",
    )
    assert customer_modules(AUTHORIZATION, contexts[1]) == ()


def test_pipeline_settings_use_context_and_block_pending_source_before_credentials(monkeypatch):
    monkeypatch.setenv("CUSTOMERS_CONFIG_PATH", str(REGISTRY))
    monkeypatch.setenv("TENANTS_CONFIG", str(AUTHORIZATION))
    monkeypatch.delenv("AZURE_STORAGE_CONNECTION_STRING", raising=False)
    settings = Settings.from_env(require_blob=False, customer_selector="ambev")
    assert settings.tenant_context == resolve_tenant(REGISTRY, 142)
    assert settings.id_customer == 142 and "visao_industria" in settings.customer_modules
    for key in ("pandurata", "lactalis", "safira"):
        with pytest.raises(RuntimeError, match="pending source"):
            Settings.from_env(customer_selector=key)


def test_resolution_cli_does_not_start_data_pipeline():
    env = {**os.environ, "PYTHONPATH": str(ROOT / "local-engine"), "PYTHONDONTWRITEBYTECODE": "1"}
    command = [sys.executable, "-m", "neoretail_local.customers", "--config", str(REGISTRY)]
    result = subprocess.run([*command, "--tenant", "pandurata"], env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == asdict(resolve_tenant(REGISTRY, 17066))
    result = subprocess.run([*command, "--active", "--require-source"], env=env, capture_output=True, text=True)
    assert result.returncode != 0 and "pending source" in result.stderr


def test_automatic_runner_has_no_implicit_baseline():
    runner = (ROOT / "run-multitenant-refresh.ps1").read_text(encoding="utf-8")
    assert "[int[]]$CustomerIds = @()" in runner
    assert "--active --require-source" in runner
    assert runner.index("--active --require-source") < runner.index("foreach ($customerId")


def test_pipeline_cli_tenant_alias_blocks_pending_before_any_setup():
    env = {**os.environ, "PYTHONPATH": str(ROOT / "local-engine"), "PYTHONDONTWRITEBYTECODE": "1",
           "CUSTOMERS_CONFIG_PATH": str(REGISTRY)}
    result = subprocess.run(
        [sys.executable, "-m", "neoretail_local.pipeline", "--tenant", "pandurata", "--step", "00"],
        env=env, capture_output=True, text=True,
    )
    assert result.returncode != 0 and "pending source" in result.stderr
    assert "could not connect" not in result.stderr.lower()


def test_authorization_rejects_second_identity_catalog(tmp_path):
    path = tmp_path / "tenants.yaml"
    path.write_text(yaml.safe_dump({"version": "9.0", "customers": {"142": {"name": "other"}}}), encoding="utf-8")
    with pytest.raises(RuntimeError, match="Duplicate identity"):
        customer_modules(path, resolve_tenant(REGISTRY, 142))
