import asyncio
import sqlite3
import pandas as pd

from step import Step, MX, Domain, IP, ASN, SMTP, IMAP, Combiner
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



if __name__ == "__main__":

    conn = sqlite3.connect(
            "/home/julian/Projects/S.M.A.R.T.-Sovereign_Mail_Assessment_and_Rating_Tool/scanner/database/raw_data.db"
        )

    domain = pd.read_sql_query("SELECT * FROM bronze_table", conn)

    registry = Registry(
        ASN(),
        IP(),
        MX(),
        SMTP(),
        IMAP(),
        Combiner(),
    )
    registry.results[Domain] = domain
    asyncio.run(registry.run_queue())
    registry.export_results("/home/julian/Projects/S.M.A.R.T.-Sovereign_Mail_Assessment_and_Rating_Tool/scanner/src/scanner_pipeline/results")
