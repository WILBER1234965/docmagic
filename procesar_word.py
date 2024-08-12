from docx import Document
import os
import re

def reemplazar_texto_en_word(word_path, output_dir, df, replacements, filename_field):
    os.makedirs(output_dir, exist_ok=True)
    generated_files = []
    
    for i, row in df.iterrows():
        new_doc = Document(word_path)
        
        for para_index, para in enumerate(new_doc.paragraphs):
            for (selected_index, selected_text), column in replacements.items():
                if para_index == selected_index:
                    pattern = re.compile(r'\b' + re.escape(selected_text) + r'\b')
                    
                    for run in para.runs:
                        if pattern.search(run.text):
                            # Reemplazar el texto manteniendo el formato original
                            run.text = pattern.sub(str(row[column]), run.text)
        
        # Usar el campo seleccionado para el nombre del archivo
        nombre = row.get(filename_field, f'output_{i}').replace(' ', '_')
        output_path = f"{output_dir}/{nombre}_carta.docx"
        new_doc.save(output_path)
        generated_files.append(output_path)
    
    return generated_files
