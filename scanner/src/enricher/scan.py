from async_cache import AsyncCache
import sqlite3
import dns.asyncresolver
import pandas as pd
import asyncio
import ipaddress
from ipwhois import IPWhois

cache = AsyncCache(limit=20)

resolver = dns.asyncresolver.Resolver()


def extract_domain(url: str) -> str:
    return (
        url.lower()
        .replace("https://", "")
        .replace("http://", "")
        .replace("www.", "")
        .split("/")[0]
    )


async def get_mx(domain: str):
    answers = await resolver.resolve(domain, "MX")
    return [str(r.exchange).rstrip(".") for r in answers]

async def get_ip(host: str):
    loop = asyncio.get_running_loop()

    addrinfo = await loop.getaddrinfo(host, None)

    return list({
        info[4][0]
        for info in addrinfo
    })


async def get_asn(ip: str):
    addr = ipaddress.ip_address(ip)

    # IPv4
    if addr.version == 4:
        reversed_ip = ".".join(reversed(ip.split(".")))
        query = f"{reversed_ip}.origin.asn.cymru.com"

    # IPv6
    else:
        exploded = addr.exploded.replace(":", "")

        reversed_nibbles = ".".join(reversed(exploded))

        query = f"{reversed_nibbles}.origin6.asn.cymru.com"

    answers = await resolver.resolve(query, "TXT")

    txt = answers[0].to_text().strip('"')

    parts = [p.strip() for p in txt.split("|")]

    asn = parts[0]

    # ASN owner lookup
    answers2 = await resolver.resolve(
        f"AS{asn}.asn.cymru.com",
        "TXT"
    )

    txt2 = answers2[0].to_text().strip('"')

    parts2 = [p.strip() for p in txt2.split("|")]

    return {
        "asn": asn,
        "owner": parts2[4] if len(parts2) > 4 else None,
        "prefix": parts[1] if len(parts) > 1 else None,
        "country": parts[2] if len(parts) > 2 else None,
    }

async def resolve_ip(host):
    loop = asyncio.get_running_loop()
    addrinfo = await loop.getaddrinfo(host, None)
    return list({info[4][0] for info in addrinfo})

async def get_smtp(domain: str):
    reader = writer = None

    try:
        # 1) Connect timeout (wichtig gegen Hänger auf Port 25)
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(domain, 25), timeout=5
        )

        # 2) Banner lesen (auch mit Timeout abgesichert)
        banner = await asyncio.wait_for(reader.readline(), timeout=5)

        return banner.decode(errors="ignore").strip()

    except Exception:
        # wichtig: Exception wird nach oben durchgereicht
        # dein Cache entscheidet dann über storage
        raise

    finally:
        # 3) immer sauber schließen
        if writer is not None:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass


def clean_list(items):
    result = []

    for item in items:
        # Verschachtelte Listen rekursiv auflösen
        if isinstance(item, list):
            result.extend(clean_list(item))
            continue

        # None entfernen
        if item is None:
            continue

        # Strings trimmen
        if isinstance(item, str):
            item = item.strip()

            # Leere Strings entfernen
            if item == "":
                continue

        result.append(item)

    return result


async def main(domains):

    cache.load(
        r"/home/julian/Projects/S.M.A.R.T.-Sovereign_Mail_Assessment_and_Rating_Tool/scanner/cache_dump.json"
    )
    
    mx_tasks = [
        cache.get(domain, "mx", lambda d=domain: get_mx(d)) for domain in domains
    ]

    monitor_task = asyncio.create_task(cache.monitor())

    mx_results = await asyncio.gather(*mx_tasks, return_exceptions=True)

    mx_results = clean_list(mx_results)

    ip_task = [
        cache.get(domain, "ip", lambda d=domain: get_ip(d)) for domain in mx_results
    ] 

    ip_results = await asyncio.gather(*ip_task, return_exceptions=True)

    ip_results = clean_list(ip_results)

    smtp_task = [
        cache.get(domain, "smtp", lambda d=domain: get_smtp(d)) for domain in mx_results
    ]

    smtp_results = await asyncio.gather(*smtp_task, return_exceptions=True)

    asn_task = [
        cache.get(ip, "asn", lambda _ip=ip: get_asn(_ip)) for ip in ip_results
    ]

    asn_results = await asyncio.gather(*asn_task, return_exceptions=True)

    cache.save(
        r"/home/julian/Projects/S.M.A.R.T.-Sovereign_Mail_Assessment_and_Rating_Tool/scanner/cache_dump.json"
    )

    monitor_task.cancel()


def df_to_json(df: pd.DataFrame, path: str):
    rename_cols = {
        "name":"org",
        "website_domain":"domain",
        "category_tag":"category",
        "longitude":"lon",
        "latitude":"lat",
    }

    df.rename(columns=rename_cols, inplace=True)
    df.to_records()


if __name__ == "__main__":
    # Path der DB anpassen
    conn = sqlite3.connect(
            "/home/julian/Projects/S.M.A.R.T.-Sovereign_Mail_Assessment_and_Rating_Tool/scanner/database/raw_data.db"
        )

    df = pd.read_sql_query("SELECT * FROM bronze_table", conn)
    
    asyncio.run(main(df["website_domain"].to_list()))
