import asyncio
import sqlite3
import pandas as pd
import json
import dns.asyncresolver

resolver = dns.asyncresolver.Resolver()

async def run_limited(func, params, limit=20):
    semaphore = asyncio.Semaphore(limit)

    async def worker(param):
        async with semaphore:
            return await func(param)

    tasks = [asyncio.create_task(worker(p)) for p in params]
    return await asyncio.gather(*tasks)

async def get_mx(domain):
    try:
        answers = await resolver.resolve(domain, "MX")
        return [str(r.exchange).rstrip(".") for r in answers]
    except Exception as e:
        return [str(e)]
    
def extract_domain(url: str) -> str:
    return (
        url.lower()
        .replace("https://", "")
        .replace("http://", "")
        .replace("www.", "")
        .split("/")[0]
    )

async def main():
    conn = sqlite3.connect(
        "D:\\Projekte\\S.M.A.R.T.-Sovereign_Mail_Assessment_and_Rating_Tool\\scanner\\database\\domainlist.db"
    )

    df = pd.read_sql_query("SELECT * FROM osm_names", conn)

    df = df[(df["website"].notna())][["name", "website", "federal_state", "profil"]]
    df["root_domain"] = df["website"].apply(extract_domain)

    domains = df["root_domain"].tolist()
    results = await run_limited(get_mx, domains, limit=20)

    result_dict = dict(zip(domains, results))

    # als JSON speichern
    with open("mx_results.json", "w", encoding="utf-8") as f:
        json.dump(result_dict, f, indent=2, ensure_ascii=False)
        print(result_dict)


if __name__ == "__main__":
    asyncio.run(main())