from async_cache import AsyncCache
import pandas as pd
import asyncio
import dns.asyncresolver

resolver = dns.asyncresolver.Resolver()
cache = AsyncCache()


async def fetch_mx(domain: str):
    answers = await resolver.resolve(domain, "MX")
    return [str(r.exchange).rstrip(".") for r in answers]


async def fetch_ip(host: str):
    answers = await resolver.resolve(host, "A")
    return [r.address for r in answers]


async def main():

    cache.load(
        r"C:\Projekte\S.M.A.R.T.-Sovereign_Mail_Assessment_and_Rating_Tool\scanner\cache_dump.json"
    )
    df = pd.read_csv(
        r"C:\Projekte\S.M.A.R.T.-Sovereign_Mail_Assessment_and_Rating_Tool\data-kbtPx.csv"
    )

    domains = df["Behördendomains"].dropna().astype(str).tolist()

    tasks = [
        cache.get("mx", domain, lambda d=domain: fetch_mx(d)) for domain in domains
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    mx_domains = []
    for key, value in cache.cache.items():
        mx_domains = mx_domains + value

    tasks = [
        cache.get("ip", mx_domain, lambda d=mx_domain: fetch_ip(d))
        for mx_domain in mx_domains
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    cache.save(
        r"C:\Projekte\S.M.A.R.T.-Sovereign_Mail_Assessment_and_Rating_Tool\scanner\cache_dump.json"
    )
    print(results)


if __name__ == "__main__":
    asyncio.run(main())
