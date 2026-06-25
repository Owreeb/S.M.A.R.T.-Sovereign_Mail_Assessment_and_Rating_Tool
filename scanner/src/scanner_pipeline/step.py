from abc import ABC, abstractmethod
import asyncio
import ipaddress
import ssl
from typing import Type

import pandas as pd

import dns.asyncresolver
import dns.reversename

from src.scanner_pipeline.asn_bulk import lookup_asn_bulk

resolver = dns.asyncresolver.Resolver()


class Step(ABC):
    def __init__(self, concurrency: int = 20):
        self.semaphore = asyncio.Semaphore(concurrency)

    @property
    @abstractmethod
    def input_col() -> str:
        pass

    @property
    @abstractmethod
    def required_step() -> Type["Step"]:
        pass

    @abstractmethod
    async def get(self, data) -> list[dict]:
        pass

    async def _monitor(self, tasks: list[asyncio.Task]) -> None:
        while True:
            open_tasks = sum(not task.done() for task in tasks)
            total_tasks = len(tasks)

            print(f"{type(self).__name__} Step open tasks: {open_tasks}/{total_tasks}")

            if open_tasks == 0:
                break

            await asyncio.sleep(1)

    async def _run_task(self, value) -> list[dict]:
        async with self.semaphore:
            try:
                results = await self.get(value)  # returns list[dict]

                for row in results:
                    row["error"] = None

                return results

            except Exception as exc:
                return [
                    {
                        self.input_col: value,
                        "error": str(exc),
                    }
                ]

    async def get_func(self, input: pd.Series) -> pd.DataFrame:
        tasks = [asyncio.create_task(self._run_task(value)) for value in input]

        monitor_task = asyncio.create_task(self._monitor(tasks))

        task_results = await asyncio.gather(*tasks)
        results = [row for result_list in task_results for row in result_list]

        await monitor_task

        return pd.DataFrame(results)

    def preprocess(self, data: pd.DataFrame) -> pd.DataFrame:
        if self.input_col not in data.columns:
            raise ValueError(f"Input column '{self.input_col}' not found in data")

        data = data.dropna(subset=[self.input_col])
        data = data.drop_duplicates(subset=[self.input_col])
        return data

    def postprocess(self, data: pd.DataFrame) -> pd.DataFrame:
        data = data.drop_duplicates()
        return data

    async def scan(self, data: pd.DataFrame) -> pd.DataFrame:
        preprocessed_data = self.preprocess(data)
        results = await self.get_func(preprocessed_data[self.input_col])
        postprocessed_results = self.postprocess(results)
        return postprocessed_results


class Domain(Step):
    required_step = None
    input_col = None

    async def get(self, data) -> pd.DataFrame:
        pass


class Combiner(Step):
    required_step = Domain
    input_col = ["website_domain", "email_domain"]

    async def get(self, value):
        pass

    async def scan(self, data: pd.DataFrame):
        return pd.concat(
            [data["website_domain"], data["email_domain"]],
            ignore_index=True
        ).dropna().drop_duplicates().to_frame("domain")



class MX(Step):
    required_step = Combiner
    input_col = "domain"

    async def get(self, domain: str) -> list[dict]:
        answers = await resolver.resolve(domain, "MX")

        return [
            {
                self.input_col: domain,
                "mx_domain": str(r.exchange).rstrip("."),
            }
            for r in answers
        ]


class IP(Step):
    required_step = MX
    input_col = "mx_domain"

    async def get(self, domain: str) -> list[dict]:
        loop = asyncio.get_running_loop()

        addrinfo = await loop.getaddrinfo(domain, None)

        return [{self.input_col: domain, "ip": info[4][0]} for info in addrinfo]


class ASN(Step):
    required_step = IP
    input_col = "ip"

    async def scan(self, data: pd.DataFrame) -> pd.DataFrame:
        # Team Cymru rate-limits per-IP DNS on large runs, so look the whole
        # batch up in one bulk WHOIS connection instead. get() below is kept as
        # the per-IP DNS fallback.
        data = self.preprocess(data)
        ips = list(data[self.input_col])
        if not ips:
            return pd.DataFrame(columns=["ip", "asn", "owner", "prefix", "country", "error"])

        looked = await asyncio.to_thread(lookup_asn_bulk, ips)

        rows = []
        for ip in ips:
            info = looked.get(ip)
            if info is None:
                rows.append({"ip": ip, "asn": None, "owner": None,
                             "prefix": None, "country": None, "error": "no asn data"})
            else:
                rows.append({"ip": ip, "asn": info["asn"], "owner": info["asn_org"],
                             "prefix": None, "country": info["country_code"], "error": None})
        return self.postprocess(pd.DataFrame(rows))

    async def get(self, ip: str):
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
        answers2 = await resolver.resolve(f"AS{asn}.asn.cymru.com", "TXT")

        txt2 = answers2[0].to_text().strip('"')

        parts2 = [p.strip() for p in txt2.split("|")]

        return [
            {
                self.input_col: ip,
                "asn": asn,
                "owner": parts2[4] if len(parts2) > 4 else None,
                "prefix": parts[1] if len(parts) > 1 else None,
                "country": parts[2] if len(parts) > 2 else None,
            }
        ]


class SMTP(Step):
    required_step = MX
    input_col = "mx_domain"

    ports = [25, 587, 465]
    timeout = 1.5

    async def get(self, domain: str):
        for port in self.ports:
            try:
                kwargs = {"ssl": ssl.create_default_context()} if port == 465 else {}

                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(domain, port, **kwargs),
                    timeout=self.timeout,
                )

                try:
                    banner = await asyncio.wait_for(
                        reader.readline(),
                        timeout=self.timeout,
                    )

                    return [
                        {
                            self.input_col: domain,
                            "smtp_banner": banner.decode(errors="replace").strip(),
                            "port": port,
                        }
                    ]

                finally:
                    writer.close()
                    await writer.wait_closed()

            except Exception:
                continue

        raise RuntimeError("No SMTP Found")

class IMAP(Step):
    required_step = Combiner
    input_col = "domain"

    timeout = 2

    prefixes = [
        "imap",
        "mail",
        "webmail",
        "exchange",
    ]

    ports = [143, 993]

    async def get(self, domain: str):
        for prefix in self.prefixes:
            host = f"{prefix}.{domain}"

            for port in self.ports:
                try:
                    kwargs = {"ssl": True} if port == 993 else {}

                    reader, writer = await asyncio.wait_for(
                        asyncio.open_connection(host, port, **kwargs),
                        timeout=self.timeout,
                    )

                    try:
                        banner = await asyncio.wait_for(
                            reader.read(1024),
                            timeout=self.timeout,
                        )

                        return [{
                            self.input_col: domain,
                            "imap_host": host,
                            "port": port,
                            "banner": banner.decode(
                                errors="replace"
                            ).strip()[:200],
                        }]

                    finally:
                        writer.close()
                        await writer.wait_closed()

                except Exception:
                    continue

        raise RuntimeError("No IMAP Found")


class PTR(Step):
    required_step = IP
    input_col = "ip"

    async def get(self, ip: str) -> list[dict]:
        reverse_name = dns.reversename.from_address(ip)
        answer = await resolver.resolve(reverse_name, "PTR")

        return [
            {
                self.input_col: ip,
                "ptr": str(record.target).rstrip("."),
            }
            for record in answer
        ]


class SPF(Step):

    required_step = Combiner
    input_col = "domain"

    async def get(self, domain: str) -> list[dict]:

        answer = await resolver.resolve(domain, "TXT")

        return [
            {
                self.input_col: domain,
                "spf": str(record).strip('"'),
            }
            for record in answer
            if str(record).strip('"').startswith("v=spf1")
        ]

if __name__ == "__main__":
    domain = MX()
    print(type(domain))
