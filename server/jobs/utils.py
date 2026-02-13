import json
import re

def parse_notebook_parameters(notebook_file):
    """
    Retrieve parameters from the first cell of a given notebook
    """
    try:
        notebook_file.seek(0)
        content = json.load(notebook_file)
        
        first_cell = next((c for c in content['cells'] if c['cell_type'] == 'code'), None)
        if not first_cell:
            return []

        parameters = []
        
        # Regex for R assignments
        r_pattern = re.compile(r'^(param_\w+)\s*<-\s*(.*)$')

        for line in first_cell['source']:
            line = line.strip()
            match = r_pattern.match(line)
            if match:
                name = match.group(1)
                value = match.group(2).strip('"\'')
                
                # Infer Types
                param_type = "string"
                if value.lower() in ['true', 'false', 't', 'f']:
                    param_type = "boolean"
                elif value.replace('.', '', 1).isdigit():
                    param_type = "number"

                parameters.append({
                    "name": name,
                    "default": value,
                    "type": param_type
                })
        return parameters

    except Exception as e:
        print(f"Error parsing notebook: {e}")
        return []