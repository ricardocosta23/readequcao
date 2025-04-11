import os
import logging
from flask import Flask, request, abort, jsonify, render_template, url_for, redirect, flash
import requests
from datetime import datetime
import json
from werkzeug.utils import secure_filename
from utils.monday_api import get_monday_data, update_monday_item
from utils.date_formatter import formatar_data, convert_date_to_monday_format
import pandas as pd 

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize the Flask application
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key_for_development")

# Configure API key from environment variables
API_KEY = os.environ.get("MONDAY_API_KEY", "eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjQxMDM1MDMyNiwiYWFpIjoxMSwidWlkIjo1NTIyMDQ0LCJpYWQiOiIyMDI0LTA5LTEzVDExOjUyOjQzLjAwMFoiLCJwZXIiOiJtZTp3cml0ZSIsImFjdGlkIjozNzk1MywicmduIjoidXNlMSJ9.hwTlwMwtbhKdZsYcGT7UoENBLZUAxnfUXchj5RZJBz4")
API_URL = "https://api.monday.com/v2"
MONDAY_BOARD_ID = 7307869243

# Configure file upload settings
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'csv', 'png', 'jpg', 'jpeg'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

# Define a filter for the Jinja2 template engine
def replace_none(valor):
    if valor is None or valor == "None" or valor == "" or valor == '""':
        return ''
    return valor

app.jinja_env.filters['replace_none'] = replace_none

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET'])
def home():
    logger.info("Home page accessed")
    return redirect(url_for('readequacao'))

@app.route('/readequacao', methods=['GET', 'POST'])
def readequacao():
    result = None

    if request.method == 'POST':

        num_negocio = request.form.get('negocio')
        logger.info(f"Searching for business number: {num_negocio}")

        if not num_negocio:
            flash("Por favor, insira um número de negócio", "danger")
            return render_template('readequacao.html')

        query = """
        query {
          items_page_by_column_values(
            limit: 50,
            board_id: %d,
            columns: [{ column_id: "texto__1", column_values: ["%s"] }]
          ) {
            items {
              id
              name
              column_values {
                id
                text
                value
              }
            }
          }
        }
        """ % (MONDAY_BOARD_ID, num_negocio)

        try:
            monday_response = get_monday_data(query, API_KEY, API_URL)
            items = monday_response.get('data', {}).get('items_page_by_column_values', {}).get('items', [])

            if items:
                item = items[0]
                name = item.get('name')
                item_id = item.get('id')

                # Define the columns we want to retrieve
                column_ids = [
                    "texto0__1", "lista_suspensa3__1", "data__1", "date3__1", 
                    "date9__1", "date7__1", "texto16__1", "dup__of_op__o_1c0__1", 
                    "dup__of_op__o_2c__1", "dup__of_op__o_3c9__1",
                    "dup__of_op__o_1a__1", "text0__1", "dup__of_op__o_1c5__1",
                    "dup__of_op__o_1c__1", "dup__of_op__o_3a__1", "dup__of_op__o_3b__1",
                    "dup__of_op__o_3c4__1", "dup__of_op__o_3c__1"
                ]
                column_values = {col_id: None for col_id in column_ids}

                # Extract column values from the item
                for column in item.get('column_values', []):
                    if column['id'] in column_ids:
                        # For dropdown columns, we need to check text first
                        if column['id'] == 'lista_suspensa3__1':
                            column_values[column['id']] = column.get('text')
                        else:
                            column_values[column['id']] = column.get('text') or column.get('value')

                # Create result dictionary with column values
                result = {
                    "item_id": item_id,
                    "name": name,
                    "texto0__1": column_values.get('texto0__1'),
                    "lista_suspensa3__1": column_values.get('lista_suspensa3__1'),
                    "data__1": column_values.get('data__1'),
                    "date3__1": column_values.get('date3__1'),
                    "date9__1": column_values.get('date9__1'),
                    "date7__1": column_values.get('date7__1'),
                    "texto16__1": column_values.get('texto16__1'),
                    "dup__of_op__o_1c0__1": column_values.get('dup__of_op__o_1c0__1'),
                    "dup__of_op__o_2c__1": column_values.get('dup__of_op__o_2c__1'),
                    "dup__of_op__o_3c9__1": column_values.get('dup__of_op__o_3c9__1'),
                    "dup__of_op__o_1a__1": column_values.get('dup__of_op__o_1a__1'),
                    "dup__of_op__o_1c5__1": column_values.get('dup__of_op__o_1c5__1'),
                    "dup__of_op__o_1c__1": column_values.get('dup__of_op__o_1c__1'),
                    "dup__of_op__o_3a__1": column_values.get('dup__of_op__o_3a__1'),
                    "dup__of_op__o_3b__1": column_values.get('dup__of_op__o_3b__1'),
                    "dup__of_op__o_3c4__1": column_values.get('dup__of_op__o_3c4__1'),
                    "dup__of_op__o_3c__1": column_values.get('dup__of_op__o_3c__1'),
                    "text0__1": column_values.get('text0__1'),
                }


                # Format date values for display
                result['data__1'] = formatar_data(result['data__1'])
                result['date3__1'] = formatar_data(result['date3__1'])
                result['date9__1'] = formatar_data(result['date9__1'])
                result['date7__1'] = formatar_data(result['date7__1'])

                logger.debug(f"Found item: {name} with ID: {item_id}")
            else:
                flash("Nenhum negócio encontrado com esse número", "warning")
                logger.warning(f"No business found with number: {num_negocio}")

        except Exception as e:
            flash(f"Erro ao buscar dados: {str(e)}", "danger")
            logger.error(f"Error retrieving data from Monday.com: {str(e)}")

    return render_template('readequacao.html', result=result)



@app.route('/submit_readequacao', methods=['POST'])
def submit_readequacao():
    try:
        # Get form data
        item_id = request.form.get('item_id')
        result_name = request.form.get('result_name')

        # Get date values
        novaDataEntregaAEREO = request.form.get('novaDataEntregaAEREO')
        novaDataEntregaTERRESTRE = request.form.get('novaDataEntregaTERRESTRE')
        novaDataEntregaCRIACAO = request.form.get('novaDataEntregaCRIACAO')
        novaDataEntregaSALES = request.form.get('novaDataEntregaSALES')

        # Get option values
        novaOpcao1A = request.form.get('novaOpcao1A')
        novaOpcao1B = request.form.get('novaOpcao1B')
        novaOpcao1C = request.form.get('novaOpcao1C')
        novaOpcao2A = request.form.get('novaOpcao2A')
        novaOpcao2B = request.form.get('novaOpcao2B')
        novaOpcao2C = request.form.get('novaOpcao2C')
        novaOpcao3A = request.form.get('novaOpcao3A')
        novaOpcao3B = request.form.get('novaOpcao3B')
        novaOpcao3C = request.form.get('novaOpcao3C')
        novaOpcao4A = request.form.get('novaOpcao4A')
        novaOpcao4B = request.form.get('novaOpcao4B')
        novaOpcao4C = request.form.get('novaOpcao4C')

        # Get file if uploaded
        file = request.files.get('file')

        logger.debug(f"Submitting readequacao for item ID: {item_id}")
        logger.debug(f"Form data: {request.form}")
        logger.debug(f"Form data: {file}")
        # Prepare column values for Monday.com update
        column_values = {}

        # Convert dates from DD/MM/YYYY to YYYY-MM-DD format for Monday.com API
        if novaDataEntregaAEREO and novaDataEntregaAEREO != "None":
            data__1 = convert_date_to_monday_format(novaDataEntregaAEREO)
            if data__1:
                column_values["data__1"] = {"date": data__1}

        if novaDataEntregaTERRESTRE and novaDataEntregaTERRESTRE != "None":
            date9__1 = convert_date_to_monday_format(novaDataEntregaTERRESTRE)
            if date9__1:
                column_values["date9__1"] = {"date": date9__1}

        if novaDataEntregaCRIACAO and novaDataEntregaCRIACAO != "None":
            date3__1 = convert_date_to_monday_format(novaDataEntregaCRIACAO)
            if date3__1:
                column_values["date3__1"] = {"date": date3__1}

        if novaDataEntregaSALES and novaDataEntregaSALES != "None":
            date7__1 = convert_date_to_monday_format(novaDataEntregaSALES)
            if date7__1:
                column_values["date7__1"] = {"date": date7__1}

        # Add text values to column_values only if they exist
        if novaOpcao1A and novaOpcao1A != "None":
            column_values["texto16__1"] = novaOpcao1A

        if novaOpcao2A and novaOpcao2A != "None":
            column_values["dup__of_op__o_1c0__1"] = novaOpcao2A

        if novaOpcao3A and novaOpcao3A != "None":
            column_values["dup__of_op__o_2c__1"] = novaOpcao3A

        if novaOpcao4A and novaOpcao4A != "None":
            column_values["dup__of_op__o_3c9__1"] = novaOpcao4A

        if novaOpcao1B and novaOpcao1B != "None":
            column_values["dup__of_op__o_1a__1"] = novaOpcao1B

        if novaOpcao1C and novaOpcao1C != "None":
            column_values["text0__1"] = novaOpcao1C

        if novaOpcao2B and novaOpcao2B != "None":
            column_values["dup__of_op__o_1c5__1"] = novaOpcao2B

        if novaOpcao2C and novaOpcao2C != "None":
            column_values["dup__of_op__o_1c__1"] = novaOpcao2C

        if novaOpcao3B and novaOpcao3B != "None":
            column_values["dup__of_op__o_3a__1"] = novaOpcao3B

        if novaOpcao3C and novaOpcao3C != "None":
            column_values["dup__of_op__o_3b__1"] = novaOpcao3C

        if novaOpcao4B and novaOpcao4B != "None":
            column_values["dup__of_op__o_3c4__1"] = novaOpcao4B

        if novaOpcao4C and novaOpcao4C != "None":
            column_values["dup__of_op__o_3c__1"] = novaOpcao4C

        # Generate a summary of changes for texto_longo_17__1 column
        summary_text = "Resumo das Mudanças:\n\n"
        changes_found = False

        # Check for date changes
        original_data__1 = request.form.get('original_data__1')
        if novaDataEntregaAEREO and novaDataEntregaAEREO != "None" and novaDataEntregaAEREO != original_data__1:
            summary_text += f"- Data de entrega AÉREO foi alterada de {original_data__1 or '-'} para {novaDataEntregaAEREO}\n"
            changes_found = True

        original_date9__1 = request.form.get('original_date9__1')
        if novaDataEntregaTERRESTRE and novaDataEntregaTERRESTRE != "None" and novaDataEntregaTERRESTRE != original_date9__1:
            summary_text += f"- Data de entrega TERRESTRE foi alterada de {original_date9__1 or '-'} para {novaDataEntregaTERRESTRE}\n"
            changes_found = True

        original_date3__1 = request.form.get('original_date3__1')
        if novaDataEntregaCRIACAO and novaDataEntregaCRIACAO != "None" and novaDataEntregaCRIACAO != original_date3__1:
            summary_text += f"- Data de entrega CRIAÇÃO foi alterada de {original_date3__1 or '-'} para {novaDataEntregaCRIACAO}\n"
            changes_found = True

        original_date7__1 = request.form.get('original_date7__1')
        if novaDataEntregaSALES and novaDataEntregaSALES != "None" and novaDataEntregaSALES != original_date7__1:
            summary_text += f"- Data de entrega SALES foi alterada de {original_date7__1 or '-'} para {novaDataEntregaSALES}\n"
            changes_found = True

        # Check for option changes
        original_texto16__1 = request.form.get('original_texto16__1')
        if novaOpcao1A and novaOpcao1A != "None" and novaOpcao1A != original_texto16__1:
            summary_text += f"- Opção 1A foi alterada de {original_texto16__1 or '-'} para {novaOpcao1A}\n"
            changes_found = True

        original_dup__of_op__o_3c9__1 = request.form.get('original_dup__of_op__o_3c9__1')
        if novaOpcao4A and novaOpcao4A != "None" and novaOpcao4A != original_dup__of_op__o_3c9__1:
            summary_text += f"- Opção 4A foi alterada de {original_dup__of_op__o_3c9__1 or '-'} para {novaOpcao4A}\n"
            changes_found = True

        original_dup__of_op__o_3c4__1 = request.form.get('original_dup__of_op__o_3c4__1')
        if novaOpcao4B and novaOpcao4B != "None" and novaOpcao4B != original_dup__of_op__o_3c4__1:
            summary_text += f"- Opção 4B foi alterada de {original_dup__of_op__o_3c4__1 or '-'} para {novaOpcao4B}\n"
            changes_found = True

        original_dup__of_op__o_3c__1 = request.form.get('original_dup__of_op__o_3c__1')
        if novaOpcao4C and novaOpcao4C != "None" and novaOpcao4C != original_dup__of_op__o_3c__1:
            summary_text += f"- Opção 4C foi alterada de {original_dup__of_op__o_3c__1 or '-'} para {novaOpcao4C}\n"
            changes_found = True

        # Add more options following the same pattern
        original_dup__of_op__o_1c0__1 = request.form.get('original_dup__of_op__o_1c0__1')
        if novaOpcao2A and novaOpcao2A != "None" and novaOpcao2A != original_dup__of_op__o_1c0__1:
            summary_text += f"- Opção 2A foi alterada de {original_dup__of_op__o_1c0__1 or '-'} para {novaOpcao2A}\n"
            changes_found = True

        original_dup__of_op__o_2c__1 = request.form.get('original_dup__of_op__o_2c__1')
        if novaOpcao3A and novaOpcao3A != "None" and novaOpcao3A != original_dup__of_op__o_2c__1:
            summary_text += f"- Opção 3A foi alterada de {original_dup__of_op__o_2c__1 or '-'} para {novaOpcao3A}\n"
            changes_found = True

        # If no changes found, note that in the summary
        if not changes_found:
            summary_text += "Nenhuma alteração em data ou destino foi realizada."

        # Get the additional messages from the textarea field
        mensagens = request.form.get('mensagens', '').strip()

        # Create the complete content for texto_longo_17__1
        final_text = summary_text

        # Add the mensagens if not empty
        if mensagens:
            final_text += "\n\nMensagens do comercial:\n" + mensagens

        # Add file information if a file was provided
        if file and allowed_file(file.filename):
            final_text += f"\n\nArquivo anexado: {file.filename}"

        # Add this content to the texto_longo_17__1 column (only if we have changes, messages, or a file)
        if changes_found or mensagens or (file and allowed_file(file.filename)):
            # Long text columns in Monday.com need a specific format with the "text" property
            column_values["texto_longo_17__1"] = {"text": final_text}
            logger.info(f"Generated content for texto_longo_17__1 column: {final_text}")

        # Update the item in Monday.com
        logger.debug(f"Updating item with column values: {column_values}")
        update_result = update_monday_item(item_id, MONDAY_BOARD_ID, column_values, API_KEY, API_URL)

        if update_result:
            logger.info(f"Successfully updated item: {item_id}")

            # Handle planilha file upload
            planilha = request.files.get('planilha')
            if planilha and allowed_file(planilha.filename):
                filename = secure_filename(planilha.filename)
                temp_path = os.path.join('/tmp', filename)
                planilha.save(temp_path)

                headers = {"Authorization": API_KEY, 'API-version':'2023-10'}
                url = "https://api.monday.com/v2/file"
                query = f'mutation add_file($file: File!) {{add_file_to_column (item_id: {item_id}, column_id: "arquivos22__1", file: $file) {{id}}}}'

                payload = {
                    'query': query,
                    'variables': '{}'
                }
                map_json = '{"variables.file": ["variables.file"]}'
                payload['map'] = map_json

                with open(temp_path, 'rb') as file_handle:
                    file_content = file_handle.read()
                    files = {
                        'variables.file': (filename, file_content, 'application/octet-stream')
                    }

                response = requests.post(url, headers=headers, data=payload, files=files)

                if response.ok:
                    logger.info("Planilha uploaded successfully!")
                    flash("Planilha anexada com sucesso!", "success")
                else:
                    logger.error(f"Planilha upload failed: {response.text}")
                    flash("Upload da planilha falhou", "warning")

                if os.path.exists(temp_path):
                    os.remove(temp_path)

            # Handle file upload if file was provided
            if file and allowed_file(file.filename):

                filename = secure_filename(file.filename)
                logger.info(f"Uploading file: {filename} to item: {item_id}")
                # Use the same API_KEY that's already defined at the top of the file
                try:
                    # Save file temporarily

                    temp_path = os.path.join('/tmp', filename)
                    file.save(temp_path)
                    print(f"File saved to: {temp_path}")
                    # First upload the file to Monday.com's file storage
                    headers = {"Authorization": API_KEY, 'API-version':'2023-10'}
                    url = "https://api.monday.com/v2/file"

                    # Format the payload according to the Monday.com API requirements
                    # The query uses the $file variable and specifies the column_id and item_id
                    query = f'mutation add_file($file: File!) {{add_file_to_column (item_id: {item_id}, column_id: "arquivos9__1", file: $file) {{id}}}}'

                    payload = {
                        'query': query,
                        'variables': '{}'
                    }

                    # The map is a JSON string that maps the file parameter in the request to the variable in the query
                    map_json = '{"variables.file": ["variables.file"]}'
                    payload['map'] = map_json

                    logger.info(f"Upload query: {query}")
                    logger.info(f"Upload payload: {payload}")

                    # Format the files parameter - use 'variables.file' as key to match the map
                    with open(temp_path, 'rb') as file_handle:
                        file_content = file_handle.read()
                        files = {
                            'variables.file': (filename, file_content, 'application/octet-stream')
                        }

                    # Make the API request with both payload and files parameters
                    response = requests.post(url, headers=headers, data=payload, files=files)
                    logger.info(f"Upload response status: {response.status_code}")                              


                    if response.ok:
                        try:
                            # Get the response data
                            response_data = response.json()
                            logger.info(f"Upload response: {response_data}")

                            # Check if we have a successful upload in the response
                            # Monday.com API typically returns data.add_file_to_column.id for successful uploads
                            if 'data' in response_data and 'add_file_to_column' in response_data['data']:
                                file_data = response_data['data']['add_file_to_column']
                                if file_data and 'id' in file_data:
                                    asset_id = file_data['id']
                                    logger.info(f"File uploaded successfully, asset ID: {asset_id}")
                                    logger.info("File attached successfully!")
                                    flash("Arquivo anexado com sucesso!", "success")
                                else:
                                    logger.info("File uploaded but couldn't find ID in response")
                                    flash("Arquivo enviado com sucesso!", "success")
                            # Even without the expected structure, if we got a 200 OK the file was probably uploaded successfully
                            elif response.status_code == 200:
                                logger.info("File upload response structure was different than expected, but got a 200 OK")
                                flash("Arquivo enviado com sucesso!", "success")
                            else:
                                logger.error(f"Unexpected upload response structure: {response_data}")
                                flash("Erro ao processar upload do arquivo", "warning")
                        except Exception as e:
                            logger.error(f"Error processing upload response: {e}")
                            logger.error(f"Response text: {response.text}")
                            flash(f"Erro ao processar resposta de upload: {str(e)}", "warning")
                    else:
                        logger.error(f"File upload failed: {response.text}")
                        flash("Upload do arquivo falhou", "warning")

                    # Clean up temporary file
                    if os.path.exists(temp_path):
                        os.remove(temp_path)

                except Exception as e:
                    logger.error(f"Erro no upload do arquivo: {str(e)}")
                    flash(f"Erro ao enviar arquivo: {str(e)}", "warning")

            # Create item in the tracking board
            new_board_id = 8914145280
            # Get the original searched business number and responsible person
            num_negocio = request.form.get('negocio')
            if not num_negocio:  # Fallback to getting it from the form data
                num_negocio = result_name.split('-')[0].strip() if result_name else "Unknown"

            # Get and log the responsible person
            responsavel_comercial = request.form.get('result_lista_suspensa3__1')
            logger.info(f"Responsável Comercial: {responsavel_comercial}")

            # Create new item mutation
            create_item_query = """
            mutation ($board_id: ID!, $group_id: String, $item_name: String!, $column_values: JSON!) {
                create_item (
                    board_id: $board_id, 
                    group_id: $group_id, 
                    item_name: $item_name,
                    column_values: $column_values
                ) {
                    id
                }
            }
            """

            # Get client IP address
            client_ip = request.remote_addr
            if request.headers.get('X-Forwarded-For'):
                client_ip = request.headers.get('X-Forwarded-For').split(',')[0]


            # Format values for the new item
            item_name = f"{num_negocio}"
            column_values = {
                "long_text_mkpxyghy": final_text,  # Summary of changes
                "long_text_mkpxffnh": mensagens if mensagens else "",  # Messages
                "text_mkpx7153": client_ip,  # IP address
                "text_mkpxeg0n": responsavel_comercial  # Responsável comercial
            }

            variables = {
                "board_id": new_board_id,
                "group_id": "topics",  # Default group in Monday.com
                "item_name": item_name,
                "column_values": json.dumps(column_values, ensure_ascii=False)
            }

            try:
                # Create new item in tracking board
                logger.info(f"Creating tracking item with variables: {variables}")
                tracking_response = get_monday_data(create_item_query, API_KEY, API_URL, variables)
                logger.info(f"Tracking response: {tracking_response}")

                if tracking_response and tracking_response.get('data', {}).get('create_item', {}).get('id'):
                    tracking_item_id = tracking_response['data']['create_item']['id']
                    logger.info(f"Created tracking item {tracking_item_id} for business number {num_negocio}")
                    flash("Dados atualizados com sucesso!", "success")
                else:
                    error_msg = f"Failed to create tracking item. Response: {tracking_response}"
                    logger.error(error_msg)
                    flash("Dados atualizados, mas houve um erro ao criar o item de rastreamento", "warning")
            except Exception as e:
                logger.error(f"Error creating tracking item: {str(e)}")
                flash("Dados atualizados, mas houve um erro ao criar o item de rastreamento", "warning")

            # Return response regardless of tracking item creation
            return render_template('success.html', item_id=item_id, result_name=result_name)
        else:
            flash("Falha ao atualizar dados no Monday.com", "danger")
            logger.error("Failed to update item in Monday.com")
            return render_template('error.html', error="Falha ao atualizar dados no Monday.com")

    except Exception as e:
        logger.error(f"Error in submit_readequacao: {str(e)}")
        flash(f"Erro ao processar o formulário: {str(e)}", "danger")
        return render_template('error.html', error=str(e))

@app.errorhandler(413)
def request_entity_too_large(error):
    flash("Arquivo muito grande. Tamanho máximo: 16MB", "danger")
    return redirect(url_for('readequacao'))

@app.errorhandler(404)
def page_not_found(error):
    return render_template('error.html', error="Página não encontrada"), 404

@app.errorhandler(500)
def internal_server_error(error):
    return render_template('error.html', error="Erro interno do servidor"), 500

@app.route('/datacadneg', methods=['POST', 'GET'])
def datacadneg():
    if request.method == 'POST':
        try:
            data = request.get_json()

            # Monday.com webhooks may send a challenge for verification
            if 'challenge' in data:
                return jsonify({'challenge': data['challenge']})

            # Get the pulse_id (item_id) from the webhook data
            event = data.get('event', {})
            pulse_id = event.get('pulseId')

            if not pulse_id:
                logger.error("No pulse_id found in webhook data")
                return jsonify({"error": "No pulse_id found in webhook data"}), 400

            logger.info(f"Received webhook for item ID: {pulse_id}")

            # Query Monday.com API to get specifically the dup__of_avisos_____1 column value (MirrorValue type)
            query = """
            query ($item_id: [ID!]) {
              items(ids: $item_id) {
                column_values(ids: ["dup__of_avisos_____1"]) {
                  id
                  ... on MirrorValue {
                    display_value
                  }
                }
              }
            }
            """

            variables = {"item_id": pulse_id}

            try:
                # Get the data from Monday.com using variables
                monday_response = get_monday_data(query, API_KEY, API_URL, variables)

                # Print the response for debugging
                logger.info(f"Monday.com response for dup__of_avisos_____1: {json.dumps(monday_response, indent=2)}")

                items = monday_response.get('data', {}).get('items', [])

                if not items:
                    error_msg = f"Item {pulse_id} not found on Monday.com. Verifique se o ID do item está correto e se você tem acesso a ele."
                    logger.error(error_msg)
                    return jsonify({"error": error_msg}), 404

                # Extract the date value from the dup__of_avisos_____1 column
                date_value = None
                column_values = items[0].get('column_values', [])

                if column_values:
                    column = column_values[0]  # Deve ter apenas uma coluna, a dup__of_avisos_____1

                    # Para MirrorValue, o valor está em display_value
                    if column.get('display_value'):
                        date_value = column.get('display_value')
                        logger.info(f"Found date value in dup__of_avisos_____1 (display_value): {date_value}")
                    # Verificações alternativas para compatibilidade
                    elif column.get('text'):
                        date_value = column.get('text')
                        logger.info(f"Found date value in dup__of_avisos_____1 (text): {date_value}")
                    elif column.get('value'):
                        try:
                            value_json = json.loads(column.get('value'))
                            if 'date' in value_json:
                                date_value = value_json['date']
                                logger.info(f"Found date value in dup__of_avisos_____1 (value.date): {date_value}")
                        except Exception as e:
                            logger.error(f"Erro ao analisar valor JSON da coluna: {str(e)}")

                # Se não encontrou o valor, registre essa informação detalhada
                if not date_value:
                    logger.info(f"Valor da coluna dup__of_avisos_____1 não encontrado ou vazio para o item {pulse_id}")

                    # Retorne uma resposta explicativa sem tentar buscar mais dados
                    return jsonify({
                        "message": "Webhook recebido e processado. A coluna 'dup__of_avisos_____1' está vazia, portanto não foi necessário atualizar a coluna 'date_mkpr7chx'.",
                        "item_id": pulse_id,
                        "status": "skipped"
                    }), 200

                # Calculate the new date (one day before)
                new_date = None
                from utils.date_formatter import subtract_one_day
                new_date = subtract_one_day(date_value)

                if not new_date:
                    error_msg = f"Falha ao calcular nova data para o valor: {date_value}. Verifique se o formato da data é válido (YYYY-MM-DD)."
                    logger.error(error_msg)
                    return jsonify({"error": error_msg}), 400

                # Atualizar a coluna date_mkpr7chx diretamente usando uma mutação GraphQL
                # Não usar o update_monday_item pois ele faz o duplo escape do JSON
                mutation = """
                mutation ($item_id: ID!, $board_id: ID!, $column_values: JSON!) {
                  change_multiple_column_values (
                    item_id: $item_id, 
                    board_id: $board_id, 
                    column_values: $column_values
                  ) {
                    id
                  }
                }
                """

                # Preparar variáveis para a mutação
                variables = {
                    "item_id": pulse_id,
                    "board_id": 7383259135,
                    "column_values": json.dumps({"date_mkpr7chx": {"date": new_date}})
                }

                try:
                    # Fazer a chamada para a API do Monday.com
                    monday_response = get_monday_data(mutation, API_KEY, API_URL, variables)

                    # Log da resposta para depuração
                    logger.info(f"Monday.com mutation response: {json.dumps(monday_response, indent=2)}")

                    # Verificar se a atualização foi bem-sucedida
                    if monday_response.get('data', {}).get('change_multiple_column_values', {}) is not None:
                        success_msg = f"Item {pulse_id} atualizado com sucesso. Nova data: {new_date}"
                        logger.info(success_msg)
                        return jsonify({"success": True, "message": success_msg}), 200
                    else:
                        # Se houver erros específicos na resposta, incluí-los na mensagem
                        error_details = ""
                        if 'errors' in monday_response:
                            for error in monday_response.get('errors', []):
                                error_details += f" {error.get('message', '')}."

                                # Verificar se há informações sobre a coluna específica
                                if 'extensions' in error and 'error_data' in error['extensions']:
                                    error_data = error['extensions']['error_data']
                                    if 'column_id' in error_data:
                                        error_details += f" Coluna problemática: {error_data['column_id']}."

                        error_msg = f"Falha ao atualizar o item {pulse_id}.{error_details} Verifique se a coluna 'date_mkpr7chx' existe no quadro e se você tem permissões para atualizá-la."
                        logger.error(error_msg)
                        return jsonify({"error": error_msg}), 500
                except Exception as e:
                    error_msg = f"Erro ao atualizar o item no Monday.com: {str(e)}"
                    logger.error(error_msg)
                    return jsonify({"error": error_msg}), 500

            except Exception as e:
                error_msg = f"Erro ao processar webhook: {str(e)}. Por favor, verifique os logs para mais detalhes."
                logger.error(f"Error processing webhook: {str(e)}")
                return jsonify({"error": error_msg}), 500

        except Exception as e:
            error_msg = f"Erro ao analisar dados do webhook: {str(e)}. Verifique se o formato JSON está correto."
            logger.error(f"Error parsing webhook data: {str(e)}")
            return jsonify({"error": error_msg}), 400

    elif request.method == 'GET':
        # Return a simple response for GET requests (testing purposes)
        return jsonify({"message": "The datacadneg webhook endpoint is working. Use POST for webhook data."}), 200

    else:
        abort(400)

# App config values
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH  # Set the max file upload size



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
