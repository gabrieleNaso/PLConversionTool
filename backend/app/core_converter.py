from __future__ import annotations

import sys
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[2] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from plc_converter import build_conversion_scaffold, build_target_profile


def get_target_profile() -> dict:
    return build_target_profile().to_dict()


def bootstrap_conversion(
    sequence_name: str | None,
    awl_source: str,
    include_fc_block: bool = True,
    source_name: str | None = None,
) -> dict:
    return build_conversion_scaffold(
        sequence_name=sequence_name,
        awl_source=awl_source,
        include_fc_block=include_fc_block,
        source_name=source_name,
    ).to_dict()
