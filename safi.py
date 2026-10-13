import re
import socket
import ipaddress
import subprocess
import streamlit as st

# Streamlit Page Setup
st.set_page_config(page_title="Automated Recon & Vulnerability Scanner", layout="wide")

st.title("🛡️ Automated Network Recon & Vulnerability Analysis Tool")
st.write("Developed by **Safiuddin (MajorMunna)** | VAPT & SOC Security Specialist")

st.markdown("---")

# User Input Interface
target = st.text_input("Enter Target IP Address or Domain Name:", placeholder="e.g. 192.168.1.1 or scanme.nmap.org").strip()

if st.button("🚀 Start Recon & Scan"):
    if not target:
        st.warning("Please enter a valid IP or Domain first.")
    else:
        ip_pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
        domain_pattern = r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        
        resolved_target = target
        
        # -------------------------------------------------------------
        # STEP 1: TARGET VALIDATION & ENUMERATION
        # -------------------------------------------------------------
        st.header("1. Target Resolution & Subdomain Enumeration")
        
        if re.match(ip_pattern, target):
            st.info(f"📍 IP Address detected: **{target}**")
            st.write("Skipping Subfinder subdomain resolution.")
            resolved_target = target
            
        elif re.match(domain_pattern, target):
            st.info(f"🌐 Domain detected: **{target}**. Running Subfinder enumeration...")
            
            # Subfinder execution
            try:
                subfinder_cmd = ["subfinder", "-d", target, "-silent"]
                subfinder_process = subprocess.run(subfinder_cmd, capture_output=True, text=True)
                subdomains = [sub for sub in subfinder_process.stdout.strip().splitlines() if sub]
                
                st.subheader(f"Discovered Subdomains ({len(subdomains)})")
                if subdomains:
                    st.code("\n".join(subdomains), language="text")
                else:
                    st.write("No subdomains found.")
            except Exception as e:
                st.warning(f"Subfinder execution skipped/failed: {e}")

            # IP Resolution via Python socket
            st.write("Resolving main target IP address...")
            try:
                resolved_target = socket.gethostbyname(target)
                st.success(f"Resolved IP Address: **{resolved_target}**")
            except Exception as e:
                resolved_target = target
                st.warning(f"Could not resolve domain to IP, using raw target: {target}")
        else:
            st.error("Invalid Input! Please enter a valid Domain or IP address.")
            st.stop()

        st.markdown("---")

        # -------------------------------------------------------------
        # STEP 2: NETWORK & SUBNET INFORMATION
        # -------------------------------------------------------------
        st.header("2. Network Information Summary")
        try:
            # Native Python Subnet Calculation (Replaces Linux ipcalc)
            ip_obj = ipaddress.ip_interface(f"{resolved_target}/24")
            net_obj = ip_obj.network
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Target Address", str(resolved_target))
                st.metric("Network Address", f"{net_obj.network_address}/24")
                st.metric("Subnet Mask", str(net_obj.netmask))
            with col2:
                st.metric("Broadcast Address", str(net_obj.broadcast_address))
                st.metric("Usable Host Range", f"{net_obj.network_address + 1} - {net_obj.broadcast_address - 1}")
                st.metric("Total Hosts", str(net_obj.num_addresses - 2))
        except Exception as e:
            st.write(f"Network calculation info unavailable for {resolved_target}: {e}")

        st.markdown("---")

        # -------------------------------------------------------------
        # STEP 3: PORT & VERSION SCAN
        # -------------------------------------------------------------
        st.header("3. Port & Service Version Scan")
        st.write(f"Running Nmap Port Scan on **{resolved_target}**...")
        
        # Sudo removed for Streamlit Cloud Compatibility
        nmap_scan_cmd = ["nmap", "-sV", "-F", resolved_target]
        
        with st.spinner("Scanning open ports and services..."):
            conf3 = subprocess.run(nmap_scan_cmd, capture_output=True, text=True)
        
        st.code(conf3.stdout, language="bash")

        # Extract Open Ports
        open_ports_match = re.findall(r"(\d+)/tcp\s+open", conf3.stdout)
        
        st.markdown("---")

        # -------------------------------------------------------------
        # STEP 4: VULNERABILITY SCANNING
        # -------------------------------------------------------------
        st.header("4. Vulnerability Assessment & CVE Extraction")
        
        if open_ports_match:
            ports_str = ",".join(open_ports_match)
            st.write(f"Running Nmap Vuln Scripts on Open Ports: **{ports_str}**...")
            
            vuln_cmd = ["nmap", "-Pn", "-T4", "-p", ports_str, "--script", "vuln", resolved_target]
            
            with st.spinner("Executing vulnerability scripts (NSE)..."):
                conf4 = subprocess.run(vuln_cmd, capture_output=True, text=True)
            
            # Extract Vuln Name & CVEs
            pattern = r"\|\s*VULNERABLE:\s*\n\|\s*(.+?)\n.*?CVE:(CVE-\d{4}-\d+|CVE-\d{7})"
            matches = list(re.finditer(pattern, conf4.stdout, re.DOTALL))
            
            if matches:
                st.error(f"Found {len(matches)} Potential Vulnerabilities!")
                for match in matches:
                    vuln_name = match.group(1).strip()
                    cve_id = match.group(2).strip()
                    
                    st.warning(f"**Vulnerability:** {vuln_name}\n\n**CVE ID:** `{cve_id}`")
            else:
                st.success("No critical structured vulnerabilities (CVEs) found on open ports.")
                
            with st.expander("Show Raw Vulnerability Scan Output"):
                st.code(conf4.stdout, language="bash")
        else:
            st.info("No open TCP ports discovered to run vulnerability scripts.")
