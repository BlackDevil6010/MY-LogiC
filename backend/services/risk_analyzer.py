import re
import torch
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification

class RiskAnalyzer:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        self.model_name = "nlpaueb/legal-bert-base-uncased"
        self.device = 0 if torch.cuda.is_available() else -1
        
        # Initialization logic (avoid downloading in test if not requested, but requested here)
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        # For a full production system you would fine tune and load that specifically
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name, num_labels=2, ignore_mismatched_sizes=True)
        self.classifier = pipeline("text-classification", model=self.model, tokenizer=self.tokenizer, device=self.device)
        
        self.clause_mappings = {
            "indemnification": ["indemnification", "indemnify", "hold harmless", "defense", "reimburse"],
            "termination": ["termination", "terminate", "expiration", "cancelled", "cancel", "notice period", "survival"],
            "confidentiality": ["confidentiality", "confidential", "non-disclosure", "nda", "proprietary information", "trade secret"],
            "limitation_of_liability": ["limitation of liability", "liable", "liability", "damage limit", "cap on liability", "consequential damages", "indirect damages"],
            "governing_law": ["governing law", "applicable law", "jurisdiction", "venue", "choice of law", "courts of"],
            "payment_terms": ["payment", "invoice", "fee", "price", "consideration", "remuneration", "billing", "charges", "stipend"],
            "warranty": ["warranty", "warranties", "guarantee", "representation", "disclaimer", "as is"],
            "force_majeure": ["force majeure", "act of god", "unforeseen circumstances", "beyond control", "natural disaster"],
            "non_compete": ["non-compete", "restrictive covenant", "non-solicitation", "non-disparagement"],
            "intellectual_property": ["intellectual property", "ipr", "copyright", "patent", "trademark", "proprietary", "ownership of work", "invention", "assignment of rights"],
            "dispute_resolution": ["dispute resolution", "arbitration", "mediation", "settlement", "litigation"],
            "assignment": ["assignment", "assign", "transfer rights", "successors"],
            "notices": ["notices", "communications", "written notice", "registered mail"],
            "severability": ["severability", "invalidity", "partial invalidity"],
            "entire_agreement": ["entire agreement", "merger", "integration", "supersedes", "whole agreement"]
        }
        
    def analyze_batch(self, clauses):
        results = []
        for idx, text in enumerate(clauses):
            # Strip leading/trailing whitespace including extra newlines
            text = text.strip()
            if not text: continue
            
            # Normalize text for better matching
            clean_text = " ".join(text.split()).lower()
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            header = lines[0].lower() if lines else ""
            
            clause_type = "general"
            
            # Step 1: Check header first with high priority
            header_clean = header.strip().lower()
            # Remove numbering like "1.", "1.1", "Article 1" for better matching
            header_clean = re.sub(r'^(article|section|item|clause|\d+[\.\)]*)[\d\.\s]*[:-]?\s*', '', header_clean)
            
            found = False
            for c_type, keywords in self.clause_mappings.items():
                # Check normalized header
                if any(kw == header_clean or header_clean.startswith(kw) for kw in keywords):
                    clause_type = c_type
                    found = True
                    break
            
            # Step 2: Check for specific keyword in header if direct match failed
            if not found:
                for c_type, keywords in self.clause_mappings.items():
                    if any(kw in header_clean for kw in keywords):
                        clause_type = c_type
                        found = True
                        break

            # Step 3: Check full clean_text if header check failed or was insufficient
            if not found or clause_type == "general":
                # Look specifically for "Subject of this clause is..." or standard header strings
                for c_type, keywords in self.clause_mappings.items():
                    # We check the first 100 chars of clean_text for better categorization
                    snippet = clean_text[:100]
                    if any(kw in snippet for kw in keywords):
                        clause_type = c_type
                        found = True
                        break
            
            # Step 4: Broad scan of full text for backup
            if not found:
                for c_type, keywords in self.clause_mappings.items():
                    if any(kw in clean_text for kw in keywords):
                        clause_type = c_type
                        break
                    
            risks = []
            # Improved simplified risk detection
            if any(k in clean_text for k in ["shall not be liable", "not responsible for", "total liability", "cap of"]):
                risks.append({
                    "category": "liability_exposure",
                    "severity": "high",
                    "confidence": 0.88,
                    "description": "Clause contains significant limitations on liability or broad waivers."
                })
            
            if any(k in clean_text for k in ["at any time", "without cause", "for any reason", "7 days notice", "immediate termination"]):
                risks.append({
                    "category": "termination_risk",
                    "severity": "medium",
                    "confidence": 0.75,
                    "description": "Asymmetrical or overly flexible termination rights detected."
                })

            if any(k in clean_text for k in ["indemnify", "hold harmless"]):
                risks.append({
                    "category": "indemnification_scope",
                    "severity": "high",
                    "confidence": 0.82,
                    "description": "Broad indemnification obligations could lead to unknown financial liability."
                })
                
            results.append({
                "segment_index": idx,
                "text": text,
                "clause_type": clause_type,
                "risks": risks
            })
            
        return results
