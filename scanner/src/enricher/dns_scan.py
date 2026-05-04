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
            return param, await func(param)

    results = await asyncio.gather(*(worker(p) for p in params))
    return dict(results)


async def get_mx(domain):
    try:
        answers = await resolver.resolve(domain, "MX")
        return {
            "status": "ok",
            "mx": [str(r.exchange).rstrip(".") for r in answers]
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

async def get_ip(mx_host):
    try:
        answers = await resolver.resolve(mx_host, "A")
        return {
            "status": "ok",
            "ips": [r.to_text() for r in answers]
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

def extract_domain(url: str) -> str:
    return (
        str(url)
        .lower()
        .replace("https://", "")
        .replace("http://", "")
        .replace("www.", "")
        .split("/")[0]
    )


async def main():
    df = pd.read_csv(r"C:\Projekte\S.M.A.R.T.-Sovereign_Mail_Assessment_and_Rating_Tool\data-kbtPx.csv")

    domains = df["Behördendomains"].dropna().astype(str).tolist()

    tasks = [get_mx_with_ips(domain) for domain in domains]

    await asyncio.gather(*tasks, return_exceptions=True)

    mx_results = await run_limited(get_mx, domains, limit=20)


    with open("mx_results.json", "w", encoding="utf-8") as f:
        json.dump(mx_results, f, indent=2, ensure_ascii=False)


    successful = {
        domain: data
        for domain, data in mx_results.items()
        if data["status"] == "ok"
    }

    all_mx = [mx for mx_list in successful.values() for mx in mx_list]
    unique_mx = list(set(all_mx))

    ip_results = await run_limited(get_ip, unique_mx, limit=20)

    print(ip_results)


if __name__ == "__main__":
    asyncio.run(main())