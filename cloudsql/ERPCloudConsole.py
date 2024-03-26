import streamlit as st
import requests
import base64
import pandas as pd
from io import BytesIO
import configparser

# Set page configuration to wide mode by default
st.set_page_config(layout="wide")
pd.set_option("styler.render.max_elements", 50000000)
CONFIG_FILE = 'connections.ini'

# Function to save or update connection details to a properties file
def save_or_update_connection_details(url, username, password, connection_name):
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)

    if connection_name in config:
        # Update existing connection details
        config[connection_name] = {'url': url, 'username': username, 'password': password}
        st.sidebar.success(f"Updated connection details for {connection_name}")
    else:
        # Save new connection details
        config[connection_name] = {'url': url, 'username': username, 'password': password}
        st.sidebar.success(f"Created new connection: {connection_name}")

    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)
    
    # Refresh the list of saved connections and select the newly created connection
    # st.sidebar.clear_cache()
    st.experimental_rerun()
    # st.session_state.selected_connection = connection_name

# Function to load saved connections from the properties file
def load_saved_connections():
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)    
    return config.sections()

# Function to get connection details based on the selected connection
def get_connection_details(connection_name):
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    return config[connection_name]['url'], config[connection_name]['username'], config[connection_name]['password']

# Function to invoke SOAP API
# @st.cache_data(hash_funcs={requests.Response: lambda _: None})
def invoke_soap_api(payload , url , username , password):
    # Define the URL of the SOAP API endpoint
    url = f'{url}/xmlpserver/services/ExternalReportWSSService?WSDL'
    USERNAME = username
    PASSWORD = password

    # Define headers for the SOAP request
    headers = {'Content-Type': 'application/soap+xml'}

    # Make the POST request to invoke the SOAP API
    response = requests.request(method='POST', url=url, data=payload, headers=headers, auth=(USERNAME, PASSWORD))
    

    # Check if the request was successful
    if response.status_code == 200:
        return response
    else:
        st.error(f"Failed to invoke SOAP API. Status code: {response.status_code} {response.text}")

# Function to extract report bytes
def extract_report_bytes(response_text):
    start_tag = "<ns2:reportBytes>"
    end_tag = "</ns2:reportBytes>"
    start_index = response_text.find(start_tag)
    end_index = response_text.find(end_tag)
    if start_index != -1 and end_index != -1:
        return response_text[start_index + len(start_tag):end_index].strip()
    else:
        return None

# Function to decode base64 and display CSV
def decode_base64_and_display_csv(base64_data):
    # Decode base64 data
    decoded_data = base64.b64decode(base64_data)

    # Read the decoded data as CSV
    csv_data = pd.read_csv(BytesIO(decoded_data))
    
    # st.table(csv_data)
    # st.write(csv_data)
    
    st.session_state.csv_data = csv_data
    
    st.dataframe(csv_data.style.set_caption("Decoded CSV Data").set_table_styles([{
        'selector': 'th',
        'props': [('font-weight', 'bold')]
    }]), width=5000)

# Main function
def main():
    # Input fields for selecting saved connections
    saved_connections = load_saved_connections()    
    selected_connection = st.sidebar.selectbox('Select Connection:', saved_connections)
    connection_name = selected_connection

    # Get connection details based on the selected connection
    if selected_connection:
        # st.session_state.csv_data = ""
        url, username, password  = get_connection_details(selected_connection) 
    else:
        url, username, password , connection_name= '', '', '' ,''

    # Input fields for URL, username, and password
    connection_name = st.sidebar.text_input('Connection Name', value=connection_name)
    url_input = st.sidebar.text_input('API URL', value=url)
    username_input = st.sidebar.text_input('Username', value=username)
    password_input = st.sidebar.text_input('Password', type='password', value=password)

    # Save button to store or update connection details
    if st.sidebar.button('Save'):
        save_or_update_connection_details(url_input, username_input, password_input, connection_name)        

    # Input field for user to enter data
    user_input = st.text_area('Enter valid query', height=200)
    
    submit =  st.button('Run')

    # Button to submit the input data
    if submit:
        # Convert user input to base64
        base64_input = base64.b64encode(user_input.encode()).decode()

        # Construct the SOAP request payload with the base64 input
        soap_payload = f"""
        <soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:pub="http://xmlns.oracle.com/oxp/service/PublicReportService">
           <soap:Header/>
           <soap:Body>
              <pub:runReport>
                 <pub:reportRequest>
                    <pub:attributeFormat>csv</pub:attributeFormat>
                    <pub:flattenXML>false</pub:flattenXML>
                    <pub:parameterNameValues>
                       <pub:item>
                          <pub:name>query1</pub:name>
                          <pub:values>
                             <pub:item>{base64_input}</pub:item>
                          </pub:values>
                       </pub:item>
                    </pub:parameterNameValues>
                    <pub:reportAbsolutePath>/Custom/AACR/SampleReport.xdo</pub:reportAbsolutePath>
                    <pub:sizeOfDataChunkDownload>-1</pub:sizeOfDataChunkDownload>
                 </pub:reportRequest>
              </pub:runReport>
           </soap:Body>
        </soap:Envelope>
        """

        # Invoke the SOAP API with the constructed payload
        api_response = invoke_soap_api(soap_payload , url_input , username_input , password_input)
        if api_response:
            report_bytes = extract_report_bytes(str(api_response.text))
            # Replace None values with 'null' for better display
            report_bytes = report_bytes if report_bytes is not None else 'null'
            # Decode base64 response and display CSV data
            decode_base64_and_display_csv(report_bytes)
    # Set the selected connection to the newly created or updated connection
    else:
        if 'csv_data' not in st.session_state:
            st.session_state.csv_data = ""
        elif 'csv_data'  in st.session_state:
            try:
                st.dataframe(st.session_state.csv_data.style.set_caption("Decoded CSV Data").set_table_styles([{
                'selector': 'th',
                'props': [('font-weight', 'bold')]
                }]), width=5000)    
            except Exception as e:
                pass
    st.session_state.selected_connection = connection_name

if __name__ == '__main__':
    main()


if 'user_input' not in st.session_state:
        st.session_state.user_input = ""