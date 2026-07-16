"""Tests for dual-readout option propagation."""

from __future__ import annotations

import json
from typing import Any, cast

import qxdriver_quel1.runtime.box_pool as box_pool_module
import qxdriver_quel1.sysconf.db as sysconf_db_module
from quel_ic_config import DualReadoutRoute
from qxdriver_quel1.runtime.box_pool import BoxPool
from qxdriver_quel1.sysconf import SystemConfigDatabase


def test_box_pool_create_maps_dual_readout_option_to_box_create(
    monkeypatch,
) -> None:
    """Given a dual-readout config option, when creating a box pool entry, then dual_readout_groups is passed."""
    create_calls: list[dict[str, Any]] = []

    class _FakeQuel1Box:
        @staticmethod
        def create(**kwargs: Any) -> object:
            create_calls.append(kwargs)
            return object()

    monkeypatch.setattr(box_pool_module, "Quel1Box", _FakeQuel1Box)
    monkeypatch.setattr(box_pool_module, "register_box", lambda box: None)
    monkeypatch.setattr(
        box_pool_module,
        "SequencerClient",
        lambda target_ipaddr, *, box: object(),
    )

    pool = BoxPool()
    pool.create(
        "B0",
        ipaddr_wss="10.0.0.2",
        ipaddr_sss="10.1.0.2",
        ipaddr_css="10.4.0.2",
        boxtype=cast(Any, "quel1-a"),
        config_options=["dual_readout_output_mxfe0"],
    )

    assert create_calls[0]["dual_readout_groups"] == {0}
    assert "config_options" not in create_calls[0]
    assert "dual_readout_routes" not in create_calls[0]


def test_system_config_database_preserves_and_maps_dual_readout_options(
    monkeypatch,
) -> None:
    """Given a stored dual-readout config option, when creating a box, then dual_readout_groups is passed."""
    create_calls: list[dict[str, Any]] = []

    class _FakeQuel1Box:
        @staticmethod
        def create(**kwargs: Any) -> object:
            create_calls.append(kwargs)
            return object()

    monkeypatch.setattr(sysconf_db_module, "Quel1Box", _FakeQuel1Box)
    monkeypatch.setattr(sysconf_db_module, "register_box", lambda box: None)

    sysdb = SystemConfigDatabase()
    sysdb.define_box(
        box_name="B0",
        ipaddr_wss="10.0.0.2",
        boxtype="quel1-a",
        config_options=["dual_readout_output_mxfe1"],
    )

    assert sysdb.box_settings["B0"].config_options == ["dual_readout_output_mxfe1"]

    sysdb.create_box("B0", reconnect=False)

    assert create_calls[0]["dual_readout_groups"] == {1}
    assert "config_options" not in create_calls[0]
    assert "dual_readout_routes" not in create_calls[0]


def test_box_pool_create_passes_dual_readout_routes_to_box_create(
    monkeypatch,
) -> None:
    """A runtime route is forwarded to the quelware box factory."""
    create_calls: list[dict[str, Any]] = []

    class _FakeQuel1Box:
        @staticmethod
        def create(**kwargs: Any) -> object:
            create_calls.append(kwargs)
            return object()

    monkeypatch.setattr(box_pool_module, "Quel1Box", _FakeQuel1Box)
    monkeypatch.setattr(box_pool_module, "register_box", lambda box: None)
    monkeypatch.setattr(
        box_pool_module,
        "SequencerClient",
        lambda target_ipaddr, *, box: object(),
    )

    route = DualReadoutRoute(group=1, donor_port=7)
    pool = BoxPool()
    pool.create(
        "B0",
        ipaddr_wss="10.0.0.2",
        ipaddr_sss="10.1.0.2",
        ipaddr_css="10.4.0.2",
        boxtype=cast(Any, "quel1-a"),
        config_options=["dual_readout_output_mxfe1"],
        dual_readout_routes=[route],
    )

    assert create_calls[0]["dual_readout_routes"] == [route]


def test_system_config_database_roundtrips_and_passes_dual_readout_routes(
    monkeypatch,
) -> None:
    """Stored route dictionaries normalize and survive database serialization."""
    create_calls: list[dict[str, Any]] = []

    class _FakeQuel1Box:
        @staticmethod
        def create(**kwargs: Any) -> object:
            create_calls.append(kwargs)
            return object()

    monkeypatch.setattr(sysconf_db_module, "Quel1Box", _FakeQuel1Box)
    monkeypatch.setattr(sysconf_db_module, "register_box", lambda box: None)

    route = DualReadoutRoute(group=1, donor_port=7)
    sysdb = SystemConfigDatabase()
    sysdb.define_box(
        box_name="B0",
        ipaddr_wss="10.0.0.2",
        boxtype="quel1-a",
        config_options=["dual_readout_output_mxfe1"],
        dual_readout_routes=[route],
    )

    assert sysdb.box_settings["B0"].dual_readout_routes == [route]
    serialized = json.loads(sysdb.asjson())
    assert serialized["box_settings"]["B0"]["dual_readout_routes"] == [
        {"group": 1, "donor_port": 7}
    ]

    restored = SystemConfigDatabase()
    restored.set(box_settings=serialized["box_settings"])
    assert restored.box_settings["B0"].dual_readout_routes == [route]
    restored.create_box("B0", reconnect=False)

    assert create_calls[0]["dual_readout_routes"] == [route]
