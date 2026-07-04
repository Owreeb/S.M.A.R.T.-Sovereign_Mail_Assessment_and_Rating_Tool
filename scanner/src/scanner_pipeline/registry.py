import asyncio
import sqlite3
import pandas as pd

from src.scanner_pipeline.step import (
    IMAPCombiner,
    Step,
    MX,
    Domain,
    IP,
    ASN,
    SPF,
    SMTP,
    IMAP,
    DomainCombiner,
    PTR,
)
from pathlib import Path


class Registry:
    queue: list[Step]
    results: dict[Step, pd.DataFrame]

    def __init__(self, *steps: Step):
        self.queue = list(steps)
        self.results = {}

    async def run_queue(self):
        while self.queue:
            print("=== RESULTS KEYS ===")
            for k in self.results.keys():
                print(k)

            print("=== QUEUE ===")
            for s in self.queue:
                print(type(s).__name__, s.required_steps)
            step = self.find_step()

            inputs = [
                self.results[required_step]
                for required_step in step.required_steps
            ]

            self.results[type(step)] = await step.scan(*inputs)

            self.queue.remove(step)

    def find_step(self):
        for step in self.queue:
            if all(req in self.results for req in step.required_steps):
                return step

        raise ValueError("No suitable step found")

    def export_results(self, path: str | Path):
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        for step, df in self.results.items():
            filename = f"{step.__name__.lower()}.csv"
            df.to_csv(path / filename, index=False)

    @classmethod
    def from_domain_df(cls, domain_df: pd.DataFrame):
        registry = cls(
            ASN(),
            IP(),
            MX(),
            SMTP(),
            IMAP(),
            DomainCombiner(),
            PTR(),
            SPF(),
            IMAPCombiner(),
        )

        registry.results[Domain] = domain_df
        return registry

    @classmethod
    def from_sqlite(
        cls,
        database: str | Path,
        query: str,
    ):
        conn = sqlite3.connect(database)

        try:
            domain_df = pd.read_sql_query(query, conn)
        finally:
            conn.close()

        return cls.from_domain_df(domain_df)

    @classmethod
    def create_and_run(
        cls,
        domain_df: pd.DataFrame = None,
        database: str | Path = None,
        query: str = None,
        export_results: bool = False,
        export_path: str = None,
    ):
        if domain_df is not None:
            registry = cls.from_domain_df(domain_df)
        elif database:
            registry = cls.from_sqlite(database, query)
        asyncio.run(registry.run_queue())

        if export_results:
            registry.export_results(export_path)
        return registry
