import re
import requests
import os


class RiskAnalyzer:

    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):

        # LegalBERT model hosted on Hugging Face
        self.api_url = "https://api-inference.huggingface.co/models/nlpaueb/legal-bert-base-uncased"

        self.headers = {
            "Authorization": f"Bearer {os.getenv('HF_TOKEN')}"
        }

        self.clause_mappings = {
            "indemnification": ["indemnification", "indemnify", "hold harmless", "defense", "reimburse"],
            "termination": ["termination", "terminate", "expiration", "cancelled", "cancel", "notice period", "survival"],
            "confidentiality": ["confidentiality", "confidential", "non-disclosure", "nda", "proprietary information", "trade secret"],
            "limitation_of_liability": ["limitation of liability", "liable", "liability", "damage limit", "cap on liability"],
            "governing_law": ["governing law", "applicable law", "jurisdiction", "venue", "choice of law"],
            "payment_terms": ["payment", "invoice", "fee", "price", "billing", "charges"],
            "warranty": ["warranty", "guarantee", "representation", "disclaimer", "as is"],
            "force_majeure": ["force majeure", "act of god", "unforeseen circumstances", "beyond control"],
            "non_compete": ["non-compete", "restrictive covenant", "non-solicitation"],
            "intellectual_property": ["intellectual property", "copyright", "patent", "trademark", "ownership"],
            "dispute_resolution": ["dispute resolution", "arbitration", "mediation", "litigation"],
            "assignment": ["assignment", "assign", "transfer rights"],
            "notices": ["notices", "communications", "written notice"],
            "severability": ["severability", "invalidity"],
            "entire_agreement": ["entire agreement", "merger", "integration", "supersedes"]
        }

    def hf_classify(self, text):

        payload = {"inputs": text}

        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=15
            )

            if response.status_code == 200:
                return response.json()

            return {"error": f"HuggingFace API error: {response.status_code}"}

        except requests.exceptions.RequestException as e:
            return {"error": "Request failed", "details": str(e)}

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

            # Check header first
            for c_type, keywords in self.clause_mappings.items():
                if any(kw in header_clean for kw in keywords):
                    clause_type = c_type
                    found = True
                    break

            # Check first 100 characters
            if not found:
                snippet = clean_text[:100]
                for c_type, keywords in self.clause_mappings.items():
                    if any(kw in snippet for kw in keywords):
                        clause_type = c_type
                        found = True
                        break

            # Check full clause
            if not found:
                for c_type, keywords in self.clause_mappings.items():
                    if any(kw in clean_text for kw in keywords):
                        clause_type = c_type
                        break

            risks = []

            if any(k in clean_text for k in [
                "shall not be liable",
                "not responsible for",
                "total liability",
                "cap of"
            ]):
                risks.append({
                    "category": "liability_exposure",
                    "severity": "high",
                    "confidence": 0.88,
                    "description": "Clause contains significant limitations on liability."
                })

            if any(k in clean_text for k in [
                "at any time",
                "without cause",
                "for any reason",
                "immediate termination"
            ]):
                risks.append({
                    "category": "termination_risk",
                    "severity": "medium",
                    "confidence": 0.75,
                    "description": "Flexible termination rights detected."
                })

            if any(k in clean_text for k in [
                "indemnify",
                "hold harmless"
            ]):
                risks.append({
                    "category": "indemnification_scope",
                    "severity": "high",
                    "confidence": 0.82,
                    "description": "Broad indemnification obligations detected."
                })

            ai_analysis = self.hf_classify(text)

            results.append({
                "segment_index": idx,
                "text": text,
                "clause_type": clause_type,
                "risks": risks,
                "ai_analysis": ai_analysis
            })

        return results
