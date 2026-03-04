import os
import PyPDF2
import docx

class FileParser:
    @staticmethod
    def parse_file(filepath):
        ext = os.path.splitext(filepath)[1].lower()
        if ext == '.pdf':
            return FileParser._parse_pdf(filepath)
        elif ext == '.docx':
            return FileParser._parse_docx(filepath)
        elif ext == '.txt':
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            raise ValueError(f"Unsupported file extension: {ext}")
            
    @staticmethod
    def _parse_pdf(filepath):
        text = ""
        with open(filepath, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text() + "\n"
        return text
        
    @staticmethod
    def _parse_docx(filepath):
        doc = docx.Document(filepath)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return '\n'.join(full_text)
