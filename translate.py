import os
import argparse
import sys
from tqdm import tqdm

# Required libraries
import docx
import openpyxl
import csv
import json
from bs4 import BeautifulSoup
from transformers import MarianMTModel, MarianTokenizer

def parse_args():
    parser = argparse.ArgumentParser(description="Translate files in a directory and its subdirectories.")
    parser.add_argument("input_dir", help="The path to the input directory.")
    parser.add_argument("output_dir", help="The path to the output directory.")
    parser.add_argument("--src_language", default="en", help="The source language (default: 'en').")
    parser.add_argument("--tgt_language", default="es", help="The target language (default: 'es').")
    return parser.parse_args()

# Initialize the model and tokenizer
args = parse_args()
model_name = f"Helsinki-NLP/opus-mt-{args.src_language}-{args.tgt_language}"
tokenizer = MarianTokenizer.from_pretrained(model_name)
model = MarianMTModel.from_pretrained(model_name)

# Translation function
def translate_text(text):
    # If the text is empty or contains only whitespace, return it as-is
    if not text.strip():
        return text

    # Tokenize and translate the text
    tokenized_text = tokenizer(text, return_tensors="pt")
    translated_tokens = model.generate(**tokenized_text)
    translated_text = tokenizer.decode(translated_tokens[0], skip_special_tokens=True)
    return translated_text

# File processing function
def process_files(input_dir, output_dir):
    files_to_process = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            file_path = os.path.join(root, file)
            files_to_process.append(file_path)

    progress_bar = tqdm(files_to_process, desc="Processing files", unit="file")
    for file_path in progress_bar:
        try:
            translate_file(file_path)
        except Exception as e:
            progress_bar.write(f"Error processing {file_path}: {e}")
            continue

def translate_file(file_path):
    file_ext = os.path.splitext(file_path)[1]
    if file_ext == ".docx":
        translate_docx(file_path)
    elif file_ext == ".xlsx":
        translate_xlsx(file_path)
    elif file_ext == ".csv":
        translate_csv(file_path)
    elif file_ext == ".json":
        translate_json(file_path)
    elif file_ext == ".html":
        translate_html(file_path)
    else:
        print(f"Unsupported file type: {file_ext}")

        
# file handlers

def translate_dict(obj):
    if isinstance(obj, dict):
        return {key: translate_dict(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [translate_dict(item) for item in obj]
    elif isinstance(obj, str):
        return translate_text(obj)
    else:
        return obj

   
# Define translation functions for each file type
def translate_docx(file_path):
    doc = docx.Document(file_path)
    for paragraph in doc.paragraphs:
        translated_text = translate_text(paragraph.text)
        paragraph.text = translated_text

    output_path = os.path.join(output_dir, os.path.relpath(file_path, input_dir))
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.save(output_path)

def translate_xlsx(file_path):
    workbook = openpyxl.load_workbook(file_path)
    for sheet in workbook.worksheets:
        for row in sheet:
            for cell in row:
                if isinstance(cell.value, str):
                    translated_text = translate_text(cell.value)
                    cell.value = translated_text

    output_path = os.path.join(output_dir, os.path.relpath(file_path, input_dir))
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    workbook.save(output_path)

def translate_csv(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        reader = csv.reader(file)
        rows = list(reader)

    translated_rows = []
    for row in rows:
        translated_row = [translate_text(cell) for cell in row]
        translated_rows.append(translated_row)

    output_path = os.path.join(output_dir, os.path.relpath(file_path, input_dir))
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(translated_rows)

def translate_json(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    translated_data = translate_dict(data)

    output_path = os.path.join(output_dir, os.path.relpath(file_path, input_dir))
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(translated_data, file, ensure_ascii=False, indent=2)

def translate_html(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file.read(), "html.parser")

    translate_soup(soup)

    output_path = os.path.join(output_dir, os.path.relpath(file_path, input_dir))
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as file:
        file.write(str(soup))

        
# Rest of the code remains the same

if __name__ == "__main__":
    input_dir = args.input_dir
    output_dir = args.output_dir

    if not os.path.exists(input_dir):
        print(f"Input directory '{input_dir}' does not exist.")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)
    process_files(input_dir, output_dir)
