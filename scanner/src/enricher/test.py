import asyncio
import pandas as pd
import dns.asyncresolver
import ssl

import smtplib
import socket
from ipwhois import IPWhois

import sqlite3
import imaplib

from .singelflight import SingleFlight

sf = SingleFlight(max_concurrency=20)

# -----------------------------
# DNS Resolver (async)
# -----------------------------
resolver = dns.asyncresolver.Resolver()

# Limit concurrency (VERY important)
sem = asyncio.Semaphore(20)


# -----------------------------
# Extract domain (optional helper)
# -----------------------------
def extract_domain(url: str) -> str:
    return (
        url.lower()
        .replace("https://", "")
        .replace("http://", "")
        .replace("www.", "")
        .split("/")[0]
    )

# -----------------------------
# A Records (IP resolution for host)
# -----------------------------
async def resolve_ips(host):
    try:
        loop = asyncio.get_running_loop()
        addrinfo = await loop.getaddrinfo(host, None)
        return list({info[4][0] for info in addrinfo})
    except Exception as e:
        return [str(e)]


# -----------------------------
# ASN lookup (blocking -> thread)
# -----------------------------
async def get_asn_info(ip):
    def _lookup():
        try:
            obj = IPWhois(ip)
            res = obj.lookup_rdap()
            return {
                "asn": res.get("asn"),
                "asn_org": res.get("asn_description"),
                "network": res.get("network", {}).get("name"),
                "country": res.get("asn_country_code"),
            }
        except Exception as e:
            return str(e)

    return await asyncio.to_thread(_lookup)


# -----------------------------
# SMTP banner (optional, blocking)
# -----------------------------
async def get_smtp_banner(host):
    def _banner():
        try:
            with socket.create_connection((host, 25), timeout=5) as s:
                return s.recv(1024).decode(errors="ignore")
        except Exception as e:
            return str(e)

    return await asyncio.to_thread(_banner)


async def get_ptr(ip):
    def _lookup():
        try:
            return socket.gethostbyaddr(ip)[0]
        except Exception as e:
            return str(e)

    return await asyncio.to_thread(_lookup)

# -----------------------------
# IMAP fingerprinting
# -----------------------------
async def get_imap_info(host):
    def _imap():
        result = {
            "banner": None,
            "capabilities": None,
            "error": None,
            "port": None,
        }

        # --- Versuch 1: IMAPS (993) ---
        try:
            imap = imaplib.IMAP4_SSL(host, 993, timeout=5)
            result["banner"] = imap.welcome.decode(errors="ignore")
            typ, caps = imap.capability()
            result["capabilities"] = caps
            result["port"] = 993
            imap.logout()
            return result
        except Exception as e:
            result["error"] = str(e)

        # --- Versuch 2: STARTTLS (143) ---
        try:
            imap = imaplib.IMAP4(host, 143, timeout=5)
            imap.starttls()
            result["banner"] = imap.welcome.decode(errors="ignore")
            typ, caps = imap.capability()
            result["capabilities"] = caps
            result["port"] = 143
            imap.logout()
            return result
        except Exception as e:
            result["error"] = str(e)

        return result

    return await asyncio.to_thread(_imap)

async def get_tls_cert(host, port=25):
    def _fetch():
        try:
            context = ssl.create_default_context()

            with smtplib.SMTP(host, port, timeout=5) as server:
                server.ehlo()

                # STARTTLS nur wenn unterstützt
                if server.has_extn("starttls"):
                    server.starttls(context=context)
                    server.ehlo()

                cert = server.sock.getpeercert()

                return {
                    "subject": cert.get("subject"),
                    "issuer": cert.get("issuer"),
                    "san": cert.get("subjectAltName"),
                }

        except Exception as e:
            return str(e)

    return await asyncio.to_thread(_fetch)

# -----------------------------
# Process ONE domain
# -----------------------------
async def process_domain(domain):
    async with sem:
        mx_records = await get_mx(domain)

        # Resolve IPs for MX hosts
        ip_lists = await asyncio.gather(*[resolve_ips(mx) for mx in mx_records])

        ips = list({ip for sub in ip_lists for ip in sub})

        # ASN lookup
        asn_data = await asyncio.gather(*[get_asn_info(ip) for ip in ips])

        # SMTP banner (optional)
        smtp_data = await asyncio.gather(*[get_smtp_banner(mx) for mx in mx_records])

        ptr_data = await asyncio.gather(*[get_ptr(ip) for ip in ips])

        tls_data = await asyncio.gather(
            *[get_tls_cert(mx) for mx in mx_records]
        )

        # IMAP (neu)
        imap_data = await asyncio.gather(
            *[get_imap_info(mx) for mx in mx_records]
        )

        return {
            "domain": domain,
            "mx_records": mx_records,
            "ips": ips,
            "asn": asn_data,
            "smtp_banner": smtp_data,
            "ptr": ptr_data,
            "tls": tls_data,
            "imap": imap_data,
        }


# -----------------------------
# Process DataFrame row
# -----------------------------
async def process_row(row):
    result = await process_domain(row["root_domain"])

    return {
        "name": row["name"],
        "website": row["website"],
        "root_domain": row["root_domain"],
        "federal_state": row["federal_state"],
        "profil": row["profil"],
        **result,
    }


# -----------------------------
# MAIN PIPELINE
# -----------------------------
async def run_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    tasks = [process_row(row) for row in df.to_dict("records")]
    results = await asyncio.gather(*tasks)
    return pd.DataFrame(results)


async def _fetch_mx(domain):
    try:
        answers = await resolver.resolve(domain, "MX")
        return [str(r.exchange).rstrip(".") for r in answers]
    except Exception as e:
        return [str(e)]

async def get_mx(domain):
    return await sf.get_or_fetch(
        key=("mx", domain),
        fetch_fn=lambda: _fetc_hmx(domain),
    )


if __name__ == "__main__":
    # get table from db
    conn = sqlite3.connect(
    "D:\\Projekte\\S.M.A.R.T.-Sovereign_Mail_Assessment_and_Rating_Tool\\scanner\\database\\domainlist.db"
    )

    df = pd.read_sql_query("SELECT * FROM osm_names", conn)

    df = df[(df["website"].notna())][["name", "website", "federal_state", "profil"]]
    df["root_domain"] = df["website"].apply(extract_domain)

    tasks = [get_mx(domain) for domain in df["root_domain"]]
    results = asyncio.gather(*tasks)

