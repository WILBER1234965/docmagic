from flask import Flask, render_template, request, send_file, session, after_this_request
import os
import pandas as pd
from procesar_word import reemplazar_texto_en_word
from docx import Document
import zipfile
import shutil

app = Flask(__name__)
app.secret_key = 'clave_secreta'  # Necesaria para sesiones seguras

# Configuración de carpetas
UPLOAD_FOLDER = 'uploads/'
OUTPUT_FOLDER = 'output/'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/select_fields', methods=['POST'])
def select_fields():
    word_file = request.files['word_file']
    excel_file = request.files['excel_file']
    word_path = os.path.join(UPLOAD_FOLDER, word_file.filename)
    excel_path = os.path.join(UPLOAD_FOLDER, excel_file.filename)
    word_file.save(word_path)
    excel_file.save(excel_path)
    
    # Leer el contenido del documento Word
    doc = Document(word_path)
    word_content = []
    for i, para in enumerate(doc.paragraphs):
        word_content.append((i, para.text))
    
    # Leer columnas del Excel
    df = pd.read_excel(excel_path)
    columns = df.columns.tolist()
    
    # Guardar rutas de los archivos en la sesión para usarlos después
    session['word_path'] = word_path
    session['excel_path'] = excel_path
    
    return render_template('select_fields.html', word_content=word_content, columns=columns)

@app.route('/process', methods=['POST'])
def process():
    word_path = session.get('word_path')
    excel_path = session.get('excel_path')
    
    # Leer las selecciones del usuario
    replacements = {}
    for key, value in request.form.items():
        if key.startswith('replace_'):
            index, selected_text = key.split('_')[1], key.split('_')[2]
            replacements[(int(index), selected_text)] = value
    
    # Campo seleccionado para el nombre del archivo
    filename_field = request.form.get('filename_field')
    
    # Leer datos del Excel
    df = pd.read_excel(excel_path)
    
    # Generar los documentos
    generated_files = reemplazar_texto_en_word(word_path, OUTPUT_FOLDER, df, replacements, filename_field)
    
    # Crear un archivo ZIP que contenga todos los documentos generados
    zip_filename = "documentos_generados.zip"
    zip_filepath = os.path.join(OUTPUT_FOLDER, zip_filename)
    
    with zipfile.ZipFile(zip_filepath, 'w') as zipf:
        for file in generated_files:
            zipf.write(file, os.path.basename(file))
    
    @after_this_request
    def cleanup(response):
        try:
            # Eliminar los archivos generados después de crear el ZIP
            for file in generated_files:
                os.remove(file)
            
            # Eliminar archivos subidos y temporales después de generar el ZIP
            os.remove(word_path)
            os.remove(excel_path)

            # Limpiar el archivo ZIP después de haber sido enviado
            os.remove(zip_filepath)
            
            # Opcionalmente, limpiar el contenido de las carpetas después de la descarga
            shutil.rmtree(OUTPUT_FOLDER)
            shutil.rmtree(UPLOAD_FOLDER)
            os.makedirs(OUTPUT_FOLDER, exist_ok=True)
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        except Exception as e:
            print(f"Error al limpiar los archivos: {e}")
        return response
    
    return send_file(zip_filepath, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=False)
