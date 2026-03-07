import os
import re
import requests


class RiskAnalyzer:

    def __init__(self):
        self.api_url = "https://api-inference.huggingface.co/models/nlpaueb/legal-bert-base-uncased"
        self.headers = {
            "Authorization": f"Bearer {os.getenv('HF_TOKEN')}"
        }

    def hf_classify(self, text):
        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json={"inputs": text},
                timeout=15
            )

            if response.status_code == 200:
                return response.json()

            return {"error": "HuggingFace API error"}

        except Exception as e:
            return {"error": str(e)}

    def analyze_batch(self, clauses):

        results = []

        for idx, text in enumerate(clauses):

            text = text.strip()
            if not text:
                continue

            clean_text = text.lower()

            clause_type = "general"

            if "terminate" in clean_text:
                clause_type = "termination"
            elif "indemnify" in clean_text:
                clause_type = "indemnification"
            elif "confidential" in clean_text:
                clause_type = "confidentiality"

            risks = []

            if "shall not be liable" in clean_text:
                risks.append({
                    "category": "liability_exposure",
                    "severity": "high",
                    "confidence": 0.9,
                    "description": "Limitation of liability detected."
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
