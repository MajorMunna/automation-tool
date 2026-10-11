import re
import subprocess

# User input target (ip ba domain je kono ekti hote pare)
target = input("Enter IP address or Domain name: ").strip()

# 1. IP validation check
ip_pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
domain_pattern = r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

if re.match(ip_pattern, target):
    print(f"\n[+] IP Address detected: {target}.")
    print("[-]Skipping Subfinder & host resolution.")
    resolved_target = target
elif re.match(domain_pattern, target):
    print(f"\n[+] Domain name detected: {target}. Running Subfinder for subdomain enumeration...")
    try:
        # Subfinder run kora -silent flag diye jate shudhu sub-domain gulo ashe
        subfinder_cmd = ["subfinder", "-d", target, "-silent"]
        subfinder_process = subprocess.run(subfinder_cmd, capture_output=True, text=True, check=True)
        subdomains = subfinder_process.stdout.strip().splitlines()
        
        # Sub-domain gulo sundor vabe print kora
        print(f"\n========================================")
        print(f"DISCOVERED SUBDOMAINS ({len(subdomains)})")
        print("========================================")
        if subdomains:
            for sub in subdomains:
                print(f" └─ {sub}")
        else:
            print(" [-] No subdomains found.")
        print("========================================")
        
        # Domain theke main IP resolve kora Nmap scan-er jonno
        print(f"\n[+] Resolving main target address...")
        host_process = subprocess.run(["host", target], capture_output=True, text=True, check=True)
        ip_match = re.search(r"has address (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", host_process.stdout)
        if ip_match:
            resolved_target = ip_match.group(1)
            print(f"[+] Resolved IP: {resolved_target}")
        else:
            resolved_target = target
            print("[-] Could not resolve IP, using original domain.")
    except Exception as e:
        resolved_target = target
        print(f"[-] Error during Subfinder/Resolution: {e}")
else:
    print("\n[-] Invalid Input! Please enter a valid Domain or IP address.")
    exit()

command2 = ["ipcalc", f"{resolved_target}"]
conf2 = subprocess.run(command2, capture_output=True, text=True)
stdout = conf2.stdout

# Regex extraction
net_match = re.search(r"Network:\s+([\d\.]+)/(\d+)", stdout)
mask_match = re.search(r"Netmask:\s+([\d\.]+)", stdout)
hostmin_match = re.search(r"HostMin:\s+([\d\.]+)", stdout)
hostmax_match = re.search(r"HostMax:\s+([\d\.]+)", stdout)
bcast_match = re.search(r"Broadcast:\s+([\d\.]+)", stdout)
hosts_match = re.search(r"Hosts/Net:\s+(\d+)", stdout)

network = net_match.group(1) if net_match else "N/A"
prefix = net_match.group(2) if net_match else "N/A"
netmask = mask_match.group(1) if mask_match else "N/A"
host_min = hostmin_match.group(1) if hostmin_match else "N/A"
host_max = hostmax_match.group(1) if hostmax_match else "N/A"
broadcast = bcast_match.group(1) if bcast_match else "N/A"
total_hosts = hosts_match.group(1) if hosts_match else "N/A"

# Sundor kora format kora output
print("\n========================================")
print("SECTION 1: NETWORK INFORMATION SUMMARY")
print("========================================")
print(f" [+] Target Address   : {resolved_target}")
print(f" [+] Network Address  : {network}/{prefix}")
print(f" [+] Subnet Mask      : {netmask}")
print(f" [+] Broadcast Addr   : {broadcast}")
print(f" [+] Usable IP Range  : {host_min} - {host_max}")
print(f" [+] Total Hosts      : {total_hosts}")
print("========================================\n")

print("\n==========================================")
print("SECTION 2: Port and Version Scan")
print("==========================================")
print(f"[*] Target: {resolved_target}")
print("[*] Running Port scanning with version (Please wait...)")
# Sobgula flag eksathe: Stealth (-sS), Version (-sV), Decoy (-D RND:5), Fast Scan (-F)
command3 = ["sudo", "nmap", "-sS", "-sV", "-D", "RND:5", "-F", resolved_target]
conf3 = subprocess.run(command3, capture_output=True, text=True)
print(conf3.stdout)

print("\n========================================")
print(f"SECTION 3: VULNERABILITY SCAN")
print("========================================")
print(f"[*] Target: {resolved_target}")
print("[*] Running vulnerability scripts (Please wait...)")
open_ports_match = re.findall(r"(\d+)/tcp\s+open", conf3.stdout)
ports_str = ",".join(open_ports_match)
command4 = ["sudo", "nmap", "-Pn", "-T4", "-p", ports_str, "--script", "vuln", resolved_target]
conf4 = subprocess.run(command4, capture_output=True, text=True)
print("[+] Scan completed! Processing results...\n")
#print(conf4.stdout) 

# প্রতিটি ভালনারেবিলিটি ব্লক আলাদা করার জন্য আরও নিখুঁত প্যাটার্ন
nmap_output = conf4.stdout

# Pattern: Sudhu Vulnerability name ebong CVE capture korar jonno
pattern = r"\|\s*VULNERABLE:\s*\n\|\s*(.+?)\n.*?CVE:(CVE-\d{4}-\d+|CVE-\d{7})"

matches = re.finditer(pattern, nmap_output, re.DOTALL)

found = False
for match in matches:
    found = True
    vuln_name = match.group(1).strip()
    cve_id = match.group(2).strip()
    
    print(f"\n[+] Vulnerability: {vuln_name}")
    print(f"    └─ CVE: {cve_id}")

if not found:
    print("\n[-] No structured vulnerabilities found.")
