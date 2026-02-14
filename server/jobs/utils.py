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
        
        r_pattern = re.compile(r'^(param_\w+)\s*<-\s*(.*)$')

        for line in first_cell['source']:
            line = line.strip()
            match = r_pattern.match(line)
            if match:
                name = match.group(1)
                value = match.group(2).strip('"\'')
                
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
    
def parse_notebook_parameters_from_payload(param_list, request_data_items, request_files=None):
    final_payload = {}
    for param in param_list:
        var_name = param.get('name')
        if not var_name:
            continue
        
        val = param.get('default', '')
        if isinstance(val, str) and len(val) >= 2 and val.startswith(('"', "'")) and val.endswith(('"', "'")):
            val = val[1:-1]
        
        if val in [None, 'null']:
            val = ''
            
        final_payload[var_name] = val
    
    for key, value in request_data_items:
        if key not in (request_files or []): 
            final_payload[key] = value

    for key, val in final_payload.items():
        if isinstance(val, str):
            v_clean = val.strip()
            
            if v_clean.lower() == 'true':
                final_payload[key] = True
            elif v_clean.lower() == 'false':
                final_payload[key] = False
            elif v_clean.isdigit() or (v_clean.startswith('-') and v_clean[1:].isdigit()):
                final_payload[key] = int(v_clean)
            else:
                try:
                    final_payload[key] = float(v_clean)
                except ValueError:
                    final_payload[key] = val
    return final_payload