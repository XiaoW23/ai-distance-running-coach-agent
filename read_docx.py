import zipfile
import xml.etree.ElementTree as ET
import sys
import io

# set stdout to utf-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def extract_text_from_docx(docx_path):
    try:
        with zipfile.ZipFile(docx_path) as docx:
            xml_content = docx.read('word/document.xml')
        
        tree = ET.fromstring(xml_content)
        namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        
        paragraphs = []
        for paragraph in tree.findall('.//w:p', namespaces):
            texts = [node.text for node in paragraph.findall('.//w:t', namespaces) if node.text]
            if texts:
                paragraphs.append(''.join(texts))
        
        return '\n'.join(paragraphs)
    
    except Exception as e:
        return f"Error: {e}"

if __name__ == '__main__':
    if len(sys.argv) > 1:
        path = sys.argv[1]
        text = extract_text_from_docx(path)
        with open('extracted_doc.txt', 'w', encoding='utf-8') as f:
            f.write(text)
        print("Done. Saved to extracted_doc.txt")
    else:
        print("Usage: python read_docx.py <path_to_docx>")
