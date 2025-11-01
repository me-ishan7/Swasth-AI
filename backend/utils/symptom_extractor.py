# placeholder
import pandas as pd
import re

class SymptomExtractor:
    def __init__(self, mapping_csv_path="data/symptom_disease.csv"):
        self.df = pd.read_csv(mapping_csv_path)
        # Build symptom list
        self.symptom_sets = []
        for _, row in self.df.iterrows():
            # normalize and split
            syms = [s.strip().lower() for s in str(row['symptoms']).split(',') if s.strip()]
            self.symptom_sets.append((set(syms), row['disease'], row.get('recommendation', "")))

    def extract_symptoms_from_text(self, text: str):
        text_l = text.lower()
        found = set()
        # naive: match symptom tokens in text
        for symset, _, _ in self.symptom_sets:
            for s in symset:
                # word boundary matching
                if re.search(r'\b' + re.escape(s) + r'\b', text_l):
                    found.add(s)
        return list(found)

    def diagnose(self, extracted_symptoms):
        extracted_set = set([s.lower() for s in extracted_symptoms])
        # exact match preference: find rule where all symptoms appear
        for symset, disease, rec in self.symptom_sets:
            if symset.issubset(extracted_set) and len(symset) > 0:
                return {"disease": disease, "recommendation": rec, "match_type": "rule_full"}
        # fallback: partial matches by score
        best = None
        best_score = 0
        for symset, disease, rec in self.symptom_sets:
            score = len(symset.intersection(extracted_set))
            if score > best_score:
                best_score = score
                best = {"disease": disease, "recommendation": rec}
        if best_score > 0:
            best["match_type"] = "rule_partial"
            best["score"] = best_score
            return best
        return {"disease": "Unknown", "recommendation": "Please consult a doctor for proper evaluation.", "match_type": "none"}
