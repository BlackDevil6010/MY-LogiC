import re

class ClauseExtractor:
    @staticmethod
    def extract_clauses(text):
        """
        Segment text into logical clauses using heuristics:
        - regex numbering patterns (e.g., "1.", "1.1", "Article 1", "Section 1")
        - header detection
        - double newlines
        """
        # Look for Article/Section headers, or all-caps headers, or numbered headers
        # Fixed: Move global flags (?m) to the very start of the expression
        split_pattern = r'(?m)(?:\n(?=(?:Article|Section|Item|Clause)\s+\d+|[\d\.]+\s|[A-Z]\.|\([a-z]\)|[A-Z][A-Z\s]{5,}\n))|(?:^(?=(?:Article|Section|Item|Clause)\s+\d+|[\d\.]+\s|[A-Z]\.))'
        raw_segments = re.split(split_pattern, text)
        
        clauses = []
        for segment in raw_segments:
            cleaned = segment.strip()
            if len(cleaned) > 20:
                clauses.append(cleaned)
                
        if not clauses:
            raw_segments = text.split('\n\n')
            for segment in raw_segments:
                cleaned = segment.strip()
                if len(cleaned) > 20:
                    clauses.append(cleaned)
                    
        return clauses
