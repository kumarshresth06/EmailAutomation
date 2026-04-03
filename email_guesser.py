import re
import requests
from bs4 import BeautifulSoup
from collections import Counter

class EmailDerivationService:
    def __init__(self, logger=None):
        self.logger = logger
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def log(self, msg):
        if self.logger:
            self.logger(msg)
        else:
            print(msg)

    def clean_domain(self, company_name):
        name = str(company_name).lower()
        # Remove common corporate suffixes BEFORE alphanumeric scrub
        for suffix in [' inc', ' llc', ' ltd', ' corp', ' incorporated', ' corporation', ' limited']:
            if name.endswith(suffix) or name.endswith(suffix+'.'):
                name = name.replace(suffix, '').replace(suffix+'.', '')
                
        name = re.sub(r'[^a-z0-9]', '', name)
        if not name:
            return None
        return f"{name}.com"

    def guess_email(self, first_name, last_name, company_name):
        domain = self.clean_domain(company_name)
        if not domain:
            self.log("[Derivation] Could not extract a valid domain from company name.")
            return None

        fname = str(first_name).lower().strip()
        lname = str(last_name).lower().strip()
        
        fname = re.sub(r'[^a-z]', '', fname)
        lname = re.sub(r'[^a-z]', '', lname)

        if not fname or not lname:
             self.log("[Derivation] Missing actionable First or Last Name.")
             return None

        # Baseline heuristic permutations
        heuristics = [
            f"{fname}.{lname}@{domain}",
            f"{fname}{lname}@{domain}",
            f"{fname[0]}{lname}@{domain}",
            f"{fname}@{domain}",
            f"{lname}@{domain}"
        ]

        query = f'"{first_name} {last_name}" "{company_name}" "@"{domain}'
        self.log(f"[Derivation] Querying Google mapping: {domain}...")
        
        try:
            url = f"https://www.google.com/search?q={requests.utils.quote(query)}"
            response = requests.get(url, headers=self.headers, timeout=5)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                text = soup.get_text()
                
                # Match against the exact localized domain safely
                pattern = r'[a-zA-Z0-9._%+-]+@' + re.escape(domain)
                matches = re.findall(pattern, text, re.IGNORECASE)
                
                if matches:
                    best_match = Counter(matches).most_common(1)[0][0]
                    # Only return if it explicitly contains our target's name elements to reduce false positives (like 'info@' or 'sales@')
                    bm_lower = best_match.lower()
                    if fname in bm_lower or lname in bm_lower:
                        self.log(f"[Derivation] Extracted exact match: {best_match}")
                        return best_match.lower()
            else:
                self.log(f"[Derivation] Search temporarily restricted (HTTP {response.status_code}).")
                
        except Exception as e:
            self.log(f"[Derivation] Search interrupted: {str(e)}")

        best_guess = heuristics[0]
        self.log(f"[Derivation] Defaulting to heuristic generation: {best_guess}")
        return best_guess
