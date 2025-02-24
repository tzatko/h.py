#!/usr/bin/env python3
"""
I often need basic domain information in a clear, human-readable form.
This async version uses parallel DNS queries for better speed.
Saved as: ~/bin/h.py
alias h='~/bin/h.py'
Usage: h.py domain.name

2019-09-09 Tomas Zatko https://keybase.io/wo_ody
2025-02-23 rewritten for async
"""

import sys, asyncio
from termcolor import colored
import dns.asyncresolver
import dns.reversename

# Helper: Perform a reverse lookup for an IP.
async def get_ptr(ip):
    try:
        rev = dns.reversename.from_address(ip)
        answers = await dns.asyncresolver.resolve(rev, "PTR")
        return [str(rdata) for rdata in answers]
    except Exception:
        return None

# Process A records for IPv4.
async def process_a(domain):
    try:
        answers = await dns.asyncresolver.resolve(domain, "A")
        tasks = [asyncio.create_task(get_ptr(str(rdata))) for rdata in answers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for rdata, ptrs in zip(answers, results):
            if not ptrs:
                print("A:\t{} -> {} -> {}".format(domain, rdata, colored('? ? ?', 'red')))
            else:
                for ptr in ptrs:
                    print("A:\t{} -> {} -> {}".format(domain, rdata, ptr))
    except Exception:
        print("A:\t{} -> {}".format(domain, colored('? ? ?', 'red')))

# Process MX records (IPv4) and their reverse lookups.
async def process_mx(domain, record_type="A"):
    try:
        mx_answers = await dns.asyncresolver.resolve(domain, "MX")
        tasks = [asyncio.create_task(process_mx_record(rdata, record_type)) for rdata in mx_answers]
        await asyncio.gather(*tasks)
    except Exception:
        print("MX:\t{}".format(colored('? ? ?', 'red')))

async def process_mx_record(rdata, record_type):
    pref = rdata.preference
    exchange = str(rdata.exchange)
    try:
        answers = await dns.asyncresolver.resolve(exchange, record_type)
        tasks = [asyncio.create_task(get_ptr(str(ip))) for ip in answers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for ip, ptrs in zip(answers, results):
            if not ptrs:
                print("MX: {}\t{} -> {} -> {}".format(pref, exchange, ip, colored('? ? ?', 'red')))
            else:
                for ptr in ptrs:
                    print("MX: {}\t{} -> {} -> {}".format(pref, exchange, ip, ptr))
    except Exception:
        print("MX: {}\t{} -> {}".format(pref, exchange, colored('? ? ?', 'red')))

# Process NS records and their reverse lookups.
async def process_ns(domain, record_type="A"):
    try:
        ns_answers = await dns.asyncresolver.resolve(domain, "NS")
        tasks = [asyncio.create_task(process_ns_record(str(rdata), record_type)) for rdata in ns_answers]
        await asyncio.gather(*tasks)
    except Exception:
        print("NS:\t{}".format(colored('? ? ?', 'red')))

async def process_ns_record(ns_name, record_type):
    try:
        answers = await dns.asyncresolver.resolve(ns_name, record_type)
        tasks = [asyncio.create_task(get_ptr(str(ip))) for ip in answers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for ip, ptrs in zip(answers, results):
            if not ptrs:
                print("NS: {} -> {} -> {}".format(ns_name, ip, colored('? ? ?', 'red')))
            else:
                for ptr in ptrs:
                    print("NS: {} -> {} -> {}".format(ns_name, ip, ptr))
    except Exception:
        print("NS: {} -> {}".format(ns_name, colored('? ? ?', 'red')))

# Process AAAA records for IPv6.
async def process_aaaa(domain):
    try:
        answers = await dns.asyncresolver.resolve(domain, "AAAA")
        tasks = [asyncio.create_task(get_ptr(str(rdata))) for rdata in answers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for rdata, ptrs in zip(answers, results):
            if not ptrs:
                print("AAAA:\t{} -> {} -> {}".format(domain, rdata, colored('? ? ?', 'red')))
            else:
                for ptr in ptrs:
                    print("AAAA:\t{} -> {} -> {}".format(domain, rdata, ptr))
    except Exception:
        print("AAAA:\t{} -> {}".format(domain, colored('? ? ?', 'red')))

# Process TXT and SOA records.
async def process_txt(domain):
    try:
        answers = await dns.asyncresolver.resolve(domain, "TXT")
        for rdata in answers:
            print("TXT:\t{}".format(rdata))
    except Exception:
        print("TXT:\t{}".format(colored('? ? ?', 'red')))

async def process_soa(domain):
    try:
        answers = await dns.asyncresolver.resolve(domain, "SOA")
        for rdata in answers:
            print("SOA:\t{}".format(rdata))
    except Exception:
        print("SOA:\t{}".format(colored('? ? ?', 'red')))

# Main asynchronous function: schedule all lookups concurrently.
async def main(domain):
    print(colored('IPv4:\n', 'green'))
    await process_a(domain)
    print("")
    await process_mx(domain, "A")
    print("")
    await process_ns(domain, "A")
    print("\n")
    print(colored('IPv6:\n', 'green'))
    await process_aaaa(domain)
    print("")
    # Also process MX for IPv6.
    await process_mx(domain, "AAAA")
    print("")
    # And NS for IPv6.
    await process_ns(domain, "AAAA")
    print("\n")
    print(colored('Other:\n', 'green'))
    await process_txt(domain)
    print("")
    await process_soa(domain)
    print("")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(colored('Usage: {} domain.name'.format(sys.argv[0]), 'red'))
        sys.exit(-1)
    domain = sys.argv[1]
    asyncio.run(main(domain))
