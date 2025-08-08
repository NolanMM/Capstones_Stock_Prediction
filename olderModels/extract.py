import json

def extract_text_from_ipynb(ipynb_filepath, txt_filepath):
    """
    Extracts all text content from an ipynb file and saves it to a text file.

    Args:
        ipynb_filepath (str): The path to the ipynb file.
        txt_filepath (str): The path to the output text file.
    """
    try:
        with open(ipynb_filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
         print(f"Error: File not found: {ipynb_filepath}")
         return
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {ipynb_filepath}")
        return
    
    text_content = []
    for cell in data['cells']:
        if cell['cell_type'] == 'markdown':
            text_content.extend(cell['source'])
        elif cell['cell_type'] == 'code':
            text_content.extend(cell['source'])
            if 'outputs' in cell:
                for output in cell['outputs']:
                    if output['output_type'] == 'stream' and output['name'] == 'stdout':
                        text_content.extend(output['text'])
                    elif output['output_type'] == 'execute_result' or output['output_type'] == 'display_data':
                        text_content.extend(output['data'].get('text/plain', []))
    
    with open(txt_filepath, 'w', encoding='utf-8') as outfile:
        outfile.write("".join(text_content))

if __name__ == '__main__':
    ipynb_filepath = 'Walk-Forward.ipynb' 
    txt_filepath = 'Walk-Forward.txt'
    extract_text_from_ipynb(ipynb_filepath, txt_filepath)
    print(f"Text content extracted from '{ipynb_filepath}' and saved to '{txt_filepath}'")