"""
ConnectorAdapter — abstract base for all data source connectors.

Every connector (SAP, Salesforce, NetSuite, …) inherits from ConnectorAdapter
and implements four methods:
  - validate()    — config/connectivity pre-flight
  - extract()     — yield Arrow RecordBatches from the source
  - land()        — write batches to Parquet in the bronze zone
  - schema_map()  — declare target Aurora schemas per logical entity

Design contract
---------------
* extract() must be a generator — do NOT materialise the full dataset in memory.
* land() writes partitioned Parquet under sink.root; returns the written paths.
* run() is the full pipeline: validate → extract → land.  Override only when
  the default orchestration order is wrong for a given source system.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Generic, Iterator, List, Optional, TypeVar

import pyarrow as pa
import pyarrow.parquet as pq

Source = TypeVar("Source")


@dataclass
class ParquetSink:
    """Describes where and how to write Parquet output."""

    root: Path
    partition_by: List[str] = field(default_factory=list)
    compression: str = "snappy"
    row_group_size: int = 100_000


@dataclass
class ConnectorResult:
    """Outcome of a full connector run."""

    source_system: str
    records_extracted: int
    files_written: List[Path]
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return not self.errors


class ConnectorAdapter(ABC, Generic[Source]):
    """
    Abstract base class for all data source connectors.

    Type parameter ``Source`` is the connector-specific config dataclass
    (e.g. SAPConfig, SalesforceConfig).  This keeps validate/extract
    type-safe without requiring a common config base class.
    """

    @property
    @abstractmethod
    def source_system(self) -> str:
        """Short snake_case identifier (e.g. 'sap_ecc', 'sap_s4', 'salesforce')."""

    @abstractmethod
    def validate(self, config: Source) -> List[str]:
        """
        Pre-flight validation of connection config and connectivity.
        Returns a list of error strings — empty means safe to extract.
        """

    @abstractmethod
    def extract(self, config: Source) -> Iterator[pa.RecordBatch]:
        """
        Yield Arrow RecordBatches from the source system.
        Batches share a single schema declared by schema_map().
        """

    @abstractmethod
    def schema_map(self) -> Dict[str, pa.Schema]:
        """
        Declare the Aurora target schema for each logical entity.

        Keys are Aurora entity names (e.g. 'fact_sales', 'fact_gl_journal').
        Values are the PyArrow schemas the connector guarantees to produce.
        """

    # ------------------------------------------------------------------
    # Concrete helpers — override only when the defaults are wrong
    # ------------------------------------------------------------------

    def land(
        self,
        batches: Iterator[pa.RecordBatch],
        sink: ParquetSink,
        entity: str = "default",
    ) -> List[Path]:
        """
        Write RecordBatches to partitioned Parquet under sink.root / entity.

        If sink.partition_by is non-empty, PyArrow Dataset API writes
        Hive-partitioned sub-directories; otherwise a single file is written.
        Returns the list of Parquet files created.
        """
        dest = sink.root / entity
        dest.mkdir(parents=True, exist_ok=True)

        tables: List[pa.Table] = []
        for batch in batches:
            tables.append(pa.Table.from_batches([batch]))

        if not tables:
            return []

        table = pa.concat_tables(tables)

        if sink.partition_by:
            import pyarrow.dataset as ds

            ds.write_dataset(
                table,
                base_dir=str(dest),
                format="parquet",
                partitioning=sink.partition_by,
                existing_data_behavior="overwrite_or_ignore",
            )
            written = list(dest.rglob("*.parquet"))
        else:
            out_file = dest / f"{entity}.parquet"
            pq.write_table(
                table,
                out_file,
                compression=sink.compression,
                row_group_size=sink.row_group_size,
            )
            written = [out_file]

        return written

    def run(self, config: Source, sink: ParquetSink) -> ConnectorResult:
        """Execute the full pipeline: validate → extract → land."""
        errors = self.validate(config)
        if errors:
            return ConnectorResult(
                source_system=self.source_system,
                records_extracted=0,
                files_written=[],
                errors=errors,
            )

        entity = next(iter(self.schema_map()), "default")
        batches = self.extract(config)
        written = self.land(batches, sink, entity=entity)

        total_rows = sum(
            pq.read_metadata(str(f)).num_rows for f in written if f.exists()
        )

        return ConnectorResult(
            source_system=self.source_system,
            records_extracted=total_rows,
            files_written=written,
        )
