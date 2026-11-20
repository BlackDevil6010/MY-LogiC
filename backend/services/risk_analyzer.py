import re
import requests
import os
import logging

logger = logging.getLogger(__name__)


class RiskAnalyzer:

    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        # Hugging Face LegalBERT inference endpoint (optional enhancement)
        self.api_url = "https://api-inference.huggingface.co/models/nlpaueb/legal-bert-base-uncased"
        self.hf_token = os.getenv("HF_TOKEN")
        self.headers = {"Authorization": f"Bearer {self.hf_token}"} if self.hf_token else {}

        self.clause_mappings = {
            "indemnification": ["indemnification", "indemnify", "hold harmless", "defense", "reimburse"],
            "termination": ["termination", "terminate", "expiration", "cancelled", "cancel", "notice period", "survival"],
            "confidentiality": ["confidentiality", "confidential", "non-disclosure", "nda", "proprietary information", "trade secret"],
            "limitation_of_liability": ["limitation of liability", "liable", "liability", "damage limit", "cap on liability"],
            "governing_law": ["governing law", "applicable law", "jurisdiction", "venue", "choice of law"],
            "payment_terms": ["payment", "invoice", "fee", "price", "billing", "charges", "interest"],
            "warranty": ["warranty", "guarantee", "representation", "disclaimer", "as is", "merchantability"],
            "force_majeure": ["force majeure", "act of god", "unforeseen circumstances", "beyond control"],
            "non_compete": ["non-compete", "restrictive covenant", "non-solicitation", "exclusivity"],
            "intellectual_property": ["intellectual property", "copyright", "patent", "trademark", "ownership", "work for hire"],
            "dispute_resolution": ["dispute resolution", "arbitration", "mediation", "litigation"],
            "assignment": ["assignment", "assign", "transfer rights", "successors"],
            "notices": ["notices", "communications", "written notice"],
            "severability": ["severability", "invalidity", "unenforceable"],
            "entire_agreement": ["entire agreement", "merger", "integration", "supersedes"]
        }

    def hf_classify(self, text):
        """Optional HF classification. Fails fast if HF_TOKEN is not set or API is slow."""
        if not self.hf_token:
            return None

        payload = {"inputs": text[:512]}
        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=2.0
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception:
            return None

    def analyze_batch(self, clauses):
        results = []

        for idx, text in enumerate(clauses):
            text = text.strip()
            if not text:
                continue

            clean_text = " ".join(text.split()).lower()
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            header = lines[0].lower() if lines else ""

            clause_type = "general"

            header_clean = re.sub(
                r'^(article|section|item|clause|\d+[\.\)]*)[\d\.\s]*[:-]?\s*',
                '',
                header.strip().lower()
            )

            found = False

            # 1. Check header first
            for c_type, keywords in self.clause_mappings.items():
                if any(kw in header_clean for kw in keywords):
                    clause_type = c_type
                    found = True
                    break

            # 2. Check first 100 characters
            if not found:
                snippet = clean_text[:100]
                for c_type, keywords in self.clause_mappings.items():
                    if any(kw in snippet for kw in keywords):
                        clause_type = c_type
                        found = True
                        break

            # 3. Check full clause text
            if not found:
                for c_type, keywords in self.clause_mappings.items():
                    if any(kw in clean_text for kw in keywords):
                        clause_type = c_type
                        break

            # Comprehensive risk detection
            risks = []

            # Limitation of liability risk
            if any(k in clean_text for k in ["shall not be liable", "not responsible for", "total liability", "cap of", "exceed the amount paid"]):
                risks.append({
                    "category": "liability_exposure",
                    "severity": "high",
                    "confidence": 0.88,
                    "description": "Clause contains significant limitations on liability or monetary caps."
                })

            # Termination risk
            if any(k in clean_text for k in ["at any time", "without cause", "for convenience", "immediate termination", "without prior notice"]):
                risks.append({
                    "category": "termination_risk",
                    "severity": "medium",
                    "confidence": 0.82,
                    "description": "One-sided or immediate termination rights detected."
                })

            # Indemnification risk
            if any(k in clean_text for k in ["indemnify", "hold harmless", "defend and hold"]):
                risks.append({
                    "category": "indemnification_scope",
                    "severity": "high",
                    "confidence": 0.85,
                    "description": "Broad indemnification and defense obligations detected."
                })

            # Perpetual confidentiality risk
            if "confidential" in clean_text and any(k in clean_text for k in ["in perpetuity", "perpetual", "indefinitely"]):
                risks.append({
                    "category": "confidentiality_duration",
                    "severity": "critical",
                    "confidence": 0.92,
                    "description": "Perpetual confidentiality obligation detected, which is often commercially unreasonable."
                })

            # Warranty disclaimer risk
            if any(k in clean_text for k in ["as is", "with all faults", "no warranties of any kind", "disclaims all warranties"]):
                risks.append({
                    "category": "warranty_disclaimer",
                    "severity": "medium",
                    "confidence": 0.78,
                    "description": "Full disclaimer of express and implied warranties detected."
                })

            # Non-compete / exclusivity risk
            if any(k in clean_text for k in ["non-compete", "shall not engage in any competing", "exclusive provider", "restrictive covenant"]):
                risks.append({
                    "category": "restrictive_covenants",
                    "severity": "high",
                    "confidence": 0.80,
                    "description": "Restrictive covenant or non-compete clause that may limit business operations."
                })

            results.append({
                "segment_index": idx,
                "text": text,
                "clause_type": clause_type,
                "risks": risks
            })

        return results
