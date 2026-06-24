import asyncio
import sqlite3
import pandas as pd

from src.scanner_pipeline.step import Step, MX, Domain, IP, ASN, SPF, SMTP, IMAP, Combiner, PTR
from pathlib import Path


# Hat eine Liste von Steps, die alle Schrittweise abgearbeitet werden

# Für jeden Step muss er passende Daten finden und übergeben und step starten.

# Es werden nur fertige Steps durchsucht, 

class Registry:
    queue: list[Step]
    results: dict[Step, pd.DataFrame]

    def __init__(self, *steps: Step):
        self.queue = list(steps)
        self.results = {}

    async def run_queue(self):
        """
        Durchlaufe alle Schritte, finde den ersten Schritt mit passenden Daten und starte diesen Schritt. Sobald der Schritt fertig ist, speichere die Ergebnisse und starte den nächsten Schritt.
        """
        while self.queue:
            step = self.find_step()
            data = self.results[step.required_step]
            # run step
            self.results[type(step)] = await step.scan(data)
            # save step data
            self.queue.remove(step)
            

    def find_step(self):
        for step in self.queue:
            if step.required_step in self.results:
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
            Combiner(),
            PTR(),
            SPF(),
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
        domain_df: pd.DataFrame=None,
        database: str | Path=None,
        query: str=None,
        export_results: bool=False,
        export_path: str=None,
    ):
        if domain_df:
            registry = cls.from_domain_df(domain_df)
        elif database:
            registry = cls.from_sqlite(database, query)
        asyncio.run(registry.run_queue())

        if export_results:
            registry.export_results(export_path)
        return registry
    
    @classmethod
    def create_testing_registry(cls):
        export_path="/home/julian/Projects/S.M.A.R.T.-Sovereign_Mail_Assessment_and_Rating_Tool/scanner/exports"
        registry = Registry()
        registry.results[ASN] = pd.read_csv(export_path+"/asn.csv")
        registry.results[Combiner] = pd.read_csv(export_path+"/combiner.csv")
        registry.results[ASN] = pd.read_csv(export_path+"/asn.csv")
        registry.results[Domain] = pd.read_csv(export_path+"/domain.csv")
        registry.results[IMAP] = pd.read_csv(export_path+"/imap.csv")
        registry.results[IP] = pd.read_csv(export_path+"/ip.csv")
        registry.results[MX] = pd.read_csv(export_path+"/mx.csv")
        registry.results[PTR] = pd.read_csv(export_path+"/ptr.csv")
        registry.results[SMTP] = pd.read_csv(export_path+"/smtp.csv")

        return registry


if __name__ == "__main__":
    
    registry = Registry.from_sqlite(
        "/home/julian/Projects/S.M.A.R.T.-Sovereign_Mail_Assessment_and_Rating_Tool/scanner/database/SMART.db",
        "SELECT * FROM org_domain_history"
    )
    registry.results[Domain] = registry.results[Domain].sample(100)
    asyncio.run(registry.run_queue())
    registry.export_results("/home/julian/Projects/S.M.A.R.T.-Sovereign_Mail_Assessment_and_Rating_Tool/scanner/test_exports")
    # registry = Registry.create_testing_registry()
    print(registry.results)
