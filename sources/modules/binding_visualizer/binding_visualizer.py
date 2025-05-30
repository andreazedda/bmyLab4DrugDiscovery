import py3Dmol
import requests
import logging
from colorama import Fore, Style
import traceback
import yaml
import json
import os
import datetime
import platform
import getpass
import pkg_resources

# Load general settings
# general_settings = pu.load_general_settings()

# Load configuration settings
# get name of the current module
module_name = os.path.splitext(os.path.basename(__file__))[0]
this_script_folder_path = os.path.dirname(os.path.realpath(__file__))
config_path = os.path.join(this_script_folder_path, module_name + ".yaml")
if not os.path.exists(config_path):
    print(Fore.RED + f"Configuration file {config_path} not found." + Style.RESET_ALL)
    exit(1)
with open(config_path, "r") as config_file:
    config = yaml.safe_load(config_file)
# with open(os.path.join(general_settings['configs_path'], module_name + ".yaml"), "r") as config_file:
#     config = yaml.safe_load(config_file)


def fetch_pdb_data(pdb_id):
    """
    Fetches PDB data for the given ID from the RCSB PDB database.

    Args:
        pdb_id (str): The PDB ID of the structure to be fetched.

    Returns:
        str: PDB file data as a string if the request is successful.

    Raises:
        requests.exceptions.RequestException: If an error occurs during the request.
    """
    pdb_url = f"https://files.rcsb.org/download/{pdb_id}.pdb"
    try:
        # Log the request attempt
        logging.info("Fetching PDB data for ID: %s", pdb_id)

        # Make a request to the PDB URL
        response = requests.get(pdb_url, timeout=10)

        # Raise an exception if the request was unsuccessful
        response.raise_for_status()

        # Log successful data fetching
        logging.info("PDB data fetched successfully.")
        return response.text
    except requests.exceptions.RequestException as error:
        # Log the error if fetching fails
        logging.error("Error fetching PDB data: %s", error)
        print(Fore.RED + "Error fetching PDB data. Check the log file for details." + Style.RESET_ALL)
        raise

def visualize_structure(pdb_data, width, height, chain_style, residue_style, output_html):
    """
    Visualizes the PDB structure using py3Dmol.

    Args:
        pdb_data (str): The PDB data string that contains the molecular structure.
        width (int): Width of the viewer window.
        height (int): Height of the viewer window.
        chain_style (dict): Visualization style for the chain.
        residue_style (dict): Visualization style for the residue.
        output_html (str): Path to the output HTML file to save the visualization.

    Functionality:
        - Creates a viewer window using py3Dmol.
        - Loads the PDB data into the viewer.
        - Sets visualization styles for different parts of the molecule.
        - Saves the viewer as an HTML file.
    """
    # Log that the viewer is being initialized
    logging.info("Initializing 3Dmol viewer.")

    # Create a viewer with specified dimensions
    viewer = py3Dmol.view(width=width, height=height)

    # Load the PDB data into the viewer
    viewer.addModel(pdb_data, 'pdb')

    # Set visualization styles
    viewer.setStyle({'chain': 'A'}, chain_style)
    viewer.setStyle({'resn': 'BOR'}, residue_style)

    # Adjust the zoom to focus on the loaded structure
    viewer.zoomTo()

    # Set hoverable with a callback to display labels for atoms, and clear labels on unhover
    viewer.setHoverable({}, True, "function(atom, viewer) { \
        if(atom) { \
            viewer.addLabel(atom.chain + ' - ' + atom.resn, { \
                position: { x: atom.x, y: atom.y, z: atom.z }, \
                backgroundColor: 'black', \
                fontColor: 'white', \
                fontSize: 10, \
                showBackground: true \
            }); \
        } \
    }", "function(atom, viewer) { viewer.removeAllLabels(); }")

    # Enable user interaction such as rotation and zoom
    viewer.setBackgroundColor('white')
    viewer.zoom(1.2)
    viewer.render()

    # Prepare additional HTML info with more color and information
    # Fetch PDB link
    pdb_id = config['pdb_id']
    pdb_link = f"https://www.rcsb.org/structure/{pdb_id}"
    # Get config file info
    config_file_info = config_path
    # Get user and host info
    user = getpass.getuser()
    host = platform.node()
    # Get dependency versions
    deps = {
        'py3Dmol': pkg_resources.get_distribution('py3Dmol').version if pkg_resources.working_set.by_key.get('py3dmol') else 'N/A',
        'requests': pkg_resources.get_distribution('requests').version if pkg_resources.working_set.by_key.get('requests') else 'N/A',
        'pyyaml': pkg_resources.get_distribution('pyyaml').version if pkg_resources.working_set.by_key.get('pyyaml') else 'N/A',
    }
    # Get script version (git commit hash if available)
    try:
        import subprocess
        git_hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], cwd=this_script_folder_path).decode().strip()
    except Exception:
        git_hash = 'N/A'
    # Try to get PDB title from the PDB data
    pdb_title = ''
    for line in pdb_data.splitlines():
        if line.startswith('TITLE '):
            pdb_title += line[10:].strip() + ' '
    pdb_title = pdb_title.strip()

    info_html = f"""
    <div style='font-family: Arial, sans-serif; margin-bottom: 10px; background: #f5f7fa; border-radius: 8px; box-shadow: 0 2px 8px #0001; padding: 18px;'>
        <h2 style='color: #2a5298; margin-top: 0;'>PDB Structure Viewer</h2>
        <div style='margin-bottom: 8px;'>
            <span style='color: #1e8449; font-weight: bold;'>PDB ID:</span> <span style='color: #154360;'><a href='{pdb_link}' target='_blank'>{pdb_id}</a></span>
        </div>
        {f"<div style='margin-bottom: 8px;'><span style='color: #76448a; font-weight: bold;'>Title:</span> <span style='color: #154360;'>{pdb_title}</span></div>" if pdb_title else ''}
        <div style='margin-bottom: 8px;'>
            <span style='color: #b9770e; font-weight: bold;'>Viewer size:</span> <span style='color: #154360;'>{width} x {height}</span>
        </div>
        <div style='margin-bottom: 8px;'>
            <span style='color: #2874a6; font-weight: bold;'>Chain style:</span> <span style='color: #154360;'>{json.dumps(chain_style)}</span>
        </div>
        <div style='margin-bottom: 8px;'>
            <span style='color: #a93226; font-weight: bold;'>Residue style:</span> <span style='color: #154360;'>{json.dumps(residue_style)}</span>
        </div>
        <div style='margin-bottom: 8px;'>
            <span style='color: #884ea0; font-weight: bold;'>Generated:</span> <span style='color: #154360;'>{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</span>
        </div>
        <div style='margin-bottom: 8px;'>
            <span style='color: #117864; font-weight: bold;'>Script:</span> <span style='color: #154360;'>binding_visualizer.py</span>
        </div>
        <div style='margin-bottom: 8px;'>
            <span style='color: #2874a6; font-weight: bold;'>Config file:</span> <span style='color: #154360;'>{config_file_info}</span>
        </div>
        <div style='margin-bottom: 8px;'>
            <span style='color: #b03a2e; font-weight: bold;'>Python version:</span> <span style='color: #154360;'>{os.sys.version.split()[0]}</span>
        </div>
        <div style='margin-bottom: 8px;'>
            <span style='color: #229954; font-weight: bold;'>Platform:</span> <span style='color: #154360;'>{platform.system()} {platform.release()}</span>
        </div>
        <div style='margin-bottom: 8px;'>
            <span style='color: #d35400; font-weight: bold;'>User/Host:</span> <span style='color: #154360;'>{user}@{host}</span>
        </div>
        <div style='margin-bottom: 8px;'>
            <span style='color: #2874a6; font-weight: bold;'>Instructions:</span> <span style='color: #154360;'>Drag to rotate, scroll to zoom, double-click to center. Hover over atoms for details.</span>
        </div>
        <div style='margin-bottom: 8px;'>
            <span style='color: #2874a6; font-weight: bold;'>Dependencies:</span> <span style='color: #154360;'>py3Dmol {deps['py3Dmol']}, requests {deps['requests']}, pyyaml {deps['pyyaml']}</span>
        </div>
        <div style='margin-bottom: 8px;'>
            <span style='color: #2874a6; font-weight: bold;'>Git commit:</span> <span style='color: #154360;'>{git_hash}</span>
        </div>
        <div style='font-size: 12px; color: #888;'>Visualization generated by <b>binding_visualizer.py</b> using <b>py3Dmol</b>.<br>Contact: <a href='mailto:your.email@example.com'>your.email@example.com</a><br>Copyright &copy; {datetime.datetime.now().year}</div>
    </div>
    """
    # Save the visualization to an HTML file, prepending info
    with open(output_html, 'w') as html_file:
        html = viewer._make_html()
        # Insert info_html after <body> if possible
        if '<body>' in html:
            html = html.replace('<body>', '<body>' + info_html, 1)
        else:
            html = info_html + html
        html_file.write(html)

    # Log the completion of visualization
    logging.info("Visualization saved to %s", output_html)
    print(Fore.GREEN + f"Visualization saved to {output_html}. Open this file in a browser to view the structure." + Style.RESET_ALL)

def main():
    """
    Main function to execute the PDB data fetching and visualization workflow.

    Workflow:
        - Uses settings from configuration files for PDB ID, viewer dimensions, and visualization styles.
        - Fetches the PDB data using `fetch_pdb_data`.
        - Visualizes the data using `visualize_structure`.
        - Handles any exceptions, logs errors, and prints a traceback for debugging.
    """
    # Initialize logging configuration
    logging.basicConfig(
        filename=os.path.join(this_script_folder_path, "binding_visualizer.log"),
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    try:
        # Fetch the PDB data using the helper function
        pdb_data = fetch_pdb_data(config['pdb_id'])

        # Visualize the structure using the fetched data
        output_html = os.path.join(this_script_folder_path, f"{config['pdb_id']}_structure_viewer.html")
        visualize_structure(
            pdb_data, 
            config['viewer']['width'], 
            config['viewer']['height'], 
            config['visualization']['chain_style'], 
            config['visualization']['residue_style'], 
            output_html
        )
    except Exception as error:
        # Log if an error occurs in the main function
        logging.error("An error occurred in the main function: %s", error)

        # Print a red error message with the traceback details
        print(Fore.RED + "An error occurred. Traceback is shown below:" + Style.RESET_ALL)
        print(Fore.YELLOW + traceback.format_exc() + Style.RESET_ALL)

# Entry point for script execution
if __name__ == "__main__":
    main()
