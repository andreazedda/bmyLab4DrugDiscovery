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
import hashlib

print(Fore.CYAN + '[binding_visualizer] Starting script...' + Style.RESET_ALL)

# Load general settings
# general_settings = pu.load_general_settings()

# Load configuration settings
# get name of the current module
module_name = os.path.splitext(os.path.basename(__file__))[0]
this_script_folder_path = os.path.dirname(os.path.realpath(__file__))
config_path = os.path.join(this_script_folder_path, module_name + ".yaml")
print(Fore.CYAN + f"[INFO] Loading configuration from {config_path}" + Style.RESET_ALL)
if not os.path.exists(config_path):
    print(Fore.RED + f"Configuration file {config_path} not found." + Style.RESET_ALL)
    exit(1)
with open(config_path, "r") as config_file:
    config = yaml.safe_load(config_file)
print(Fore.GREEN + "[SUCCESS] Configuration loaded successfully." + Style.RESET_ALL)


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
        print(Fore.CYAN + f"[INFO] Fetching PDB data for ID: {pdb_id}" + Style.RESET_ALL)
        # Log the request attempt
        logging.info("Fetching PDB data for ID: %s", pdb_id)

        # Make a request to the PDB URL
        response = requests.get(pdb_url, timeout=10)
        print(Fore.CYAN + f"[INFO] HTTP GET {pdb_url} status: {response.status_code}" + Style.RESET_ALL)

        # Raise an exception if the request was unsuccessful
        response.raise_for_status()

        print(Fore.GREEN + f"[SUCCESS] PDB data fetched for {pdb_id}." + Style.RESET_ALL)
        # Log successful data fetching
        logging.info("PDB data fetched successfully.")
        return response.text
    except requests.exceptions.RequestException as error:
        # Log the error if fetching fails
        logging.error("Error fetching PDB data: %s", error)
        print(Fore.RED + "Error fetching PDB data. Check the log file for details." + Style.RESET_ALL)
        print(Fore.YELLOW + f"[ERROR] {error}" + Style.RESET_ALL)
        raise

def file_hash(path):
    """Return SHA256 hash of a file."""
    print(Fore.CYAN + f"[INFO] Calculating SHA256 for {path}" + Style.RESET_ALL)
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    hash_val = h.hexdigest()
    print(Fore.GREEN + f"[SUCCESS] SHA256 for {path}: {hash_val}" + Style.RESET_ALL)
    return hash_val

def parse_pdb_header(pdb_data):
    """Extract method, resolution, ligands, chains from PDB header."""
    print(Fore.CYAN + "[INFO] Parsing PDB header for metadata..." + Style.RESET_ALL)
    method = None
    resolution = None
    ligands = set()
    chains = set()
    for line in pdb_data.splitlines():
        if line.startswith('EXPDTA'):
            method = line[10:].strip()
        elif line.startswith('REMARK   2') and 'RESOLUTION.' in line:
            parts = line.split()
            for i, p in enumerate(parts):
                if p == 'RESOLUTION.':
                    try:
                        resolution = parts[i+1] + ' ' + parts[i+2]
                    except Exception:
                        pass
        elif line.startswith('HET   '):
            het_code = line[7:10].strip()
            if het_code and het_code != 'HOH':
                ligands.add(het_code)
        elif line.startswith('COMPND') and 'CHAIN:' in line:
            chain_part = line.split('CHAIN:')[1].split(';')[0]
            for c in chain_part.split(','):
                chains.add(c.strip())
    print(Fore.GREEN + f"[SUCCESS] Parsed header: method={method}, resolution={resolution}, ligands={ligands}, chains={chains}" + Style.RESET_ALL)
    return {
        'method': method,
        'resolution': resolution,
        'ligands': sorted(ligands),
        'chains': sorted(chains)
    }

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
    print(Fore.CYAN + f"[INFO] Initializing 3Dmol viewer with width={width}, height={height}" + Style.RESET_ALL)
    # Log that the viewer is being initialized
    logging.info("Initializing 3Dmol viewer.")

    # Create a viewer with specified dimensions
    viewer = py3Dmol.view(width=width, height=height)
    print(Fore.CYAN + "[INFO] Adding model to viewer..." + Style.RESET_ALL)
    viewer.addModel(pdb_data, 'pdb')

    print(Fore.CYAN + "[INFO] Setting visualization styles..." + Style.RESET_ALL)
    # Set visualization styles
    viewer.setStyle({'chain': 'A'}, chain_style)
    viewer.setStyle({'resn': 'BOR'}, residue_style)

    print(Fore.CYAN + "[INFO] Zooming and rendering viewer..." + Style.RESET_ALL)
    # Adjust the zoom to focus on the loaded structure
    viewer.zoomTo()
    # Set hoverable with a callback to display labels for atoms, and clear labels on unhover
    print(Fore.CYAN + "[INFO] Setting hoverable labels..." + Style.RESET_ALL)
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
    print(Fore.GREEN + "[SUCCESS] 3Dmol viewer rendered." + Style.RESET_ALL)

    # Prepare additional HTML info with more color and information
    # Fetch PDB link
    pdb_id = config['pdb_id']
    pdb_link = f"https://www.rcsb.org/structure/{pdb_id}"
    config_file_info = config_path
    user = getpass.getuser()
    host = platform.node()
    print(Fore.CYAN + f"[INFO] Collecting dependency versions..." + Style.RESET_ALL)
    deps = {
        'py3Dmol': pkg_resources.get_distribution('py3Dmol').version if pkg_resources.working_set.by_key.get('py3dmol') else 'N/A',
        'requests': pkg_resources.get_distribution('requests').version if pkg_resources.working_set.by_key.get('requests') else 'N/A',
        'pyyaml': pkg_resources.get_distribution('pyyaml').version if pkg_resources.working_set.by_key.get('pyyaml') else 'N/A',
    }
    try:
        import subprocess
        print(Fore.CYAN + "[INFO] Getting git commit hash..." + Style.RESET_ALL)
        git_hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], cwd=this_script_folder_path).decode().strip()
    except Exception:
        git_hash = 'N/A'
    pdb_title = ''
    for line in pdb_data.splitlines():
        if line.startswith('TITLE '):
            pdb_title += line[10:].strip() + ' '
    pdb_title = pdb_title.strip()
    print(Fore.CYAN + "[INFO] Parsing PDB header for method, resolution, ligands, chains..." + Style.RESET_ALL)
    # --- New: Parse header ---
    pdb_meta = parse_pdb_header(pdb_data)
    print(Fore.CYAN + "[INFO] Calculating script and config SHA256 hashes..." + Style.RESET_ALL)
    # --- New: Hashes ---
    script_hash = file_hash(__file__)
    config_hash = file_hash(config_path)
    print(Fore.CYAN + "[INFO] Reading inline YAML config..." + Style.RESET_ALL)
    # --- New: Inline YAML ---
    with open(config_path, 'r') as f:
        config_yaml = f.read()
    # --- New: Download timestamp ---
    pdb_download_time = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    print(Fore.CYAN + "[INFO] Checking for Bio.PDB (biopython) availability..." + Style.RESET_ALL)
    try:
        from Bio.PDB import PDBParser, NeighborSearch
        biopython_available = True
        print(Fore.GREEN + "[SUCCESS] Bio.PDB available. Binding site mapping enabled." + Style.RESET_ALL)
    except ImportError:
        biopython_available = False
        print(Fore.YELLOW + "[WARNING] Bio.PDB not available. Binding site mapping disabled." + Style.RESET_ALL)
    def get_binding_site_residues(pdb_path, ligand_code, cutoff=5.0):
        if not biopython_available:
            print(Fore.YELLOW + "[binding_visualizer] Skipping binding site mapping (Bio.PDB not available)." + Style.RESET_ALL)
            return []
        print(Fore.CYAN + f"[INFO] Mapping binding site for ligand {ligand_code} with cutoff {cutoff} Å..." + Style.RESET_ALL)
        parser = PDBParser(QUIET=True)
        structure = parser.get_structure('PDB', pdb_path)
        atoms = [atom for atom in structure.get_atoms()]
        ns = NeighborSearch(atoms)
        ligand_atoms = [atom for atom in structure.get_atoms() if atom.parent.resname == ligand_code]
        binding_residues = set()
        for atom in ligand_atoms:
            for neighbor in ns.search(atom.coord, cutoff):
                res = neighbor.parent
                if res.get_id()[0] == " " and res.resname != ligand_code:
                    binding_residues.add((res.parent.id, res.id[1], res.resname))
        print(Fore.GREEN + f"[SUCCESS] Found {len(binding_residues)} binding site residues." + Style.RESET_ALL)
        return sorted(binding_residues)
    def fetch_rcsb_validation(pdb_id):
        print(Fore.CYAN + f"[INFO] Fetching RCSB validation for {pdb_id}..." + Style.RESET_ALL)
        try:
            url = f"https://validate-rcsb-1.wwpdb.org/api/validation/entry/{pdb_id.lower()}"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                print(Fore.GREEN + f"[SUCCESS] Validation data fetched." + Style.RESET_ALL)
                return resp.json()
        except Exception:
            print(Fore.YELLOW + f"[WARNING] Validation fetch failed." + Style.RESET_ALL)
            pass
        return None
    def fetch_rcsb_citation(pdb_id):
        print(Fore.CYAN + f"[INFO] Fetching RCSB citation for {pdb_id}..." + Style.RESET_ALL)
        try:
            url = f"https://data.rcsb.org/rest/v1/core/entry/{pdb_id.lower()}"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                print(Fore.GREEN + f"[SUCCESS] Citation data fetched." + Style.RESET_ALL)
                return resp.json()
        except Exception:
            print(Fore.YELLOW + f"[WARNING] Citation fetch failed." + Style.RESET_ALL)
            pass
        return None
    ligand_code = config.get('ligand', 'BOR')
    binding_site_cfg = config.get('binding_site_detection', {'enabled': False})
    mutation_list = config.get('mutations', [])
    therapies = config.get('therapies', [])
    pathways = config.get('pathways', [])
    literature = config.get('literature', [])
    print(Fore.CYAN + f"[INFO] Saving PDB to temp file for biopython: {pdb_id}.pdb" + Style.RESET_ALL)
    # --- Save PDB to temp file for biopython ---
    pdb_temp_path = os.path.join(this_script_folder_path, f"{pdb_id}.pdb")
    with open(pdb_temp_path, 'w') as f:
        f.write(pdb_data)
    binding_residues = []
    if binding_site_cfg.get('enabled', False) and biopython_available:
        cutoff = float(binding_site_cfg.get('cutoff_angstrom', 5.0))
        print(Fore.CYAN + f"[INFO] Running binding site detection (cutoff={cutoff})..." + Style.RESET_ALL)
        # --- Binding site detection ---
        binding_residues = get_binding_site_residues(pdb_temp_path, ligand_code, cutoff)
    else:
        print(Fore.YELLOW + "[WARNING] Binding site detection not enabled or Bio.PDB unavailable." + Style.RESET_ALL)
    print(Fore.CYAN + f"[INFO] Fetching RCSB validation/citation..." + Style.RESET_ALL)
    # --- RCSB validation/citation ---
    validation = fetch_rcsb_validation(pdb_id)
    citation = fetch_rcsb_citation(pdb_id)
    mutation_table_html = ""
    if mutation_list:
        print(Fore.CYAN + f"[INFO] Overlaying {len(mutation_list)} mutations..." + Style.RESET_ALL)
        mutation_table_html = "<table style='border-collapse:collapse;width:100%;margin-bottom:8px;'><tr><th>Chain</th><th>ResNum</th><th>Mutation</th><th>Effect</th></tr>"
        for m in mutation_list:
            mutation_table_html += f"<tr><td>{m.get('chain')}</td><td>{m.get('resnum')}</td><td>{m.get('mutation')}</td><td>{m.get('effect','')}</td></tr>"
        mutation_table_html += "</table>"
    binding_table_html = ""
    if binding_residues:
        print(Fore.CYAN + f"[INFO] Generating binding site table..." + Style.RESET_ALL)
        binding_table_html = "<table style='border-collapse:collapse;width:100%;margin-bottom:8px;'><tr><th>Chain</th><th>ResNum</th><th>ResName</th></tr>"
        for chain, resnum, resname in binding_residues:
            binding_table_html += f"<tr><td>{chain}</td><td>{resnum}</td><td>{resname}</td></tr>"
        binding_table_html += "</table>"
    therapies_html = ""
    if therapies:
        print(Fore.CYAN + f"[INFO] Adding {len(therapies)} therapies to table..." + Style.RESET_ALL)
        therapies_html = "<table style='border-collapse:collapse;width:100%;margin-bottom:8px;'><tr><th>Name</th><th>Ligand</th><th>Phase</th><th>MM Relevance</th><th>Resistance Mutations</th></tr>"
        for t in therapies:
            therapies_html += f"<tr><td>{t.get('name')}</td><td>{t.get('pdb_ligand')}</td><td>{t.get('clinical_phase','')}</td><td>{t.get('mm_relevance','')}</td><td>{', '.join(t.get('resistance_mutations',[]))}</td></tr>"
        therapies_html += "</table>"
    pathways_html = ""
    if pathways:
        print(Fore.CYAN + f"[INFO] Adding {len(pathways)} pathways to table..." + Style.RESET_ALL)
        pathways_html = "<ul>"
        for p in pathways:
            kegg = f"<a href='https://www.kegg.jp/dbget-bin/www_bget?{p.get('kegg_id')}' target='_blank'>{p.get('kegg_id')}</a>" if p.get('kegg_id') else ''
            reactome = f"<a href='https://reactome.org/content/detail/{p.get('reactome_id')}' target='_blank'>{p.get('reactome_id')}</a>" if p.get('reactome_id') else ''
            pathways_html += f"<li>{p.get('name','')} {kegg} {reactome}</li>"
        pathways_html += "</ul>"
    literature_html = ""
    if literature:
        print(Fore.CYAN + f"[INFO] Adding {len(literature)} literature references..." + Style.RESET_ALL)
        literature_html = "<ul>"
        for l in literature:
            doi = f"<a href='https://doi.org/{l.get('doi')}' target='_blank'>{l.get('doi')}</a>" if l.get('doi') else ''
            pmid = f"<a href='https://pubmed.ncbi.nlm.nih.gov/{l.get('pmid')}' target='_blank'>{l.get('pmid')}</a>" if l.get('pmid') else ''
            literature_html += f"<li>{l.get('title','')} {doi} {pmid}</li>"
        literature_html += "</ul>"
    validation_html = ""
    if validation:
        outliers = validation.get('geometry_quality', {}).get('ramachandran_outliers', {}).get('percent', None)
        validation_html = f"<div style='color:#b03a2e;'><b>Validation:</b> Ramachandran outliers: {outliers}%</div>" if outliers is not None else ''
        print(Fore.CYAN + f"[INFO] Validation summary: Ramachandran outliers: {outliers}%" + Style.RESET_ALL)
    citation_html = ""
    if citation:
        try:
            pub = citation['rcsb_primary_citation']
            title = pub.get('title','')
            doi = pub.get('doi','')
            citation_html = f"<div><b>Citation:</b> <a href='https://doi.org/{doi}' target='_blank'>{title}</a></div>"
            print(Fore.CYAN + f"[INFO] Citation: {title} (DOI: {doi})" + Style.RESET_ALL)
        except Exception:
            print(Fore.YELLOW + f"[WARNING] Citation parsing failed." + Style.RESET_ALL)
            pass
    print(Fore.CYAN + f"[INFO] Preparing HTML info panel..." + Style.RESET_ALL)
    info_html = f"""
    <div style='font-family:Arial,sans-serif;font-size:14px;color:#333;margin-bottom:10px;'>
        <h2 style='color:#2a5298;margin-top:0;'>PDB Structure Viewer</h2>
        <div style='margin-bottom:8px;'><span style='color:#1e8449;font-weight:bold;'>PDB ID:</span> <span style='color:#154360;'><a href='https://www.rcsb.org/structure/{pdb_id}' target='_blank'>{pdb_id}</a></span></div>
        <div style='margin-bottom:8px;'><span style='color:#76448a;font-weight:bold;'>Title:</span> <span style='color:#154360;'>{pdb_title}</span></div>
        <div style='margin-bottom:8px;'><span style='color:#76448a;font-weight:bold;'>Experimental Method:</span> <span style='color:#154360;'>{pdb_meta['method']}</span></div>
        <div style='margin-bottom:8px;'><span style='color:#76448a;font-weight:bold;'>Resolution:</span> <span style='color:#154360;'>{pdb_meta['resolution']}</span></div>
        <div style='margin-bottom:8px;'><span style='color:#76448a;font-weight:bold;'>Ligands:</span> <span style='color:#154360;'>{', '.join(pdb_meta['ligands'])}</span></div>
        <div style='margin-bottom:8px;'><span style='color:#76448a;font-weight:bold;'>Chains:</span> <span style='color:#154360;'>{', '.join(pdb_meta['chains'])}</span></div>
        <div style='margin-bottom:8px;'><span style='color:#b9770e;font-weight:bold;'>Viewer size:</span> <span style='color:#154360;'>{width} x {height}</span></div>
        <div style='margin-bottom:8px;'><span style='color:#2874a6;font-weight:bold;'>Chain style:</span> <span style='color:#154360;'>{chain_style}</span></div>
        <div style='margin-bottom:8px;'><span style='color:#a93226;font-weight:bold;'>Residue style:</span> <span style='color:#154360;'>{residue_style}</span></div>
        <div style='margin-bottom:8px;'><span style='color:#884ea0;font-weight:bold;'>Generated:</span> <span style='color:#154360;'>{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</span></div>
        <div style='margin-bottom:8px;'><span style='color:#117864;font-weight:bold;'>Script:</span> <span style='color:#154360;'>{os.path.basename(__file__)}</span></div>
        <div style='margin-bottom:8px;'><span style='color:#2874a6;font-weight:bold;'>Config file:</span> <span style='color:#154360;'>{os.path.basename(config_path)}</span></div>
        <div style='margin-bottom:8px;'><span style='color:#b03a2e;font-weight:bold;'>Python version:</span> <span style='color:#154360;'>{os.sys.version.split()[0]}</span></div>
        <div style='margin-bottom:8px;'><span style='color:#229954;font-weight:bold;'>Platform:</span> <span style='color:#154360;'>{platform.system()} {platform.release()}</span></div>
        <div style='margin-bottom:8px;'><span style='color:#d35400;font-weight:bold;'>User/Host:</span> <span style='color:#154360;'>{user}@{host}</span></div>
        <div style='margin-bottom:8px;'><span style='color:#2874a6;font-weight:bold;'>PDB Downloaded:</span> <span style='color:#154360;'>{pdb_download_time}</span></div>
        <div style='margin-bottom:8px;'><span style='color:#2874a6;font-weight:bold;'>Script SHA256:</span> <span style='color:#154360;'>{script_hash}</span></div>
        <div style='margin-bottom:8px;'><span style='color:#2874a6;font-weight:bold;'>Config SHA256:</span> <span style='color:#154360;'>{config_hash}</span></div>
        <div style='margin-bottom:8px;'><span style='color:#2874a6;font-weight:bold;'>Instructions:</span> <span style='color:#154360;'>Drag to rotate, scroll to zoom, double-click to center. Hover over atoms for details.</span></div>
        <div style='margin-bottom:8px;'><span style='color:#2874a6;font-weight:bold;'>Dependencies:</span> <span style='color:#154360;'>{', '.join([f'{k} {v}' for k,v in deps.items()])}</span></div>
        <div style='margin-bottom:8px;'><span style='color:#2874a6;font-weight:bold;'>Git commit:</span> <span style='color:#154360;'>{git_hash}</span></div>
        <div style='margin-bottom:8px;'><span style='color:#2874a6;font-weight:bold;'>Downloads:</span> <span style='color:#154360;'><a href='https://files.rcsb.org/download/{pdb_id}.pdb'>PDB file</a> | <a href='binding_visualizer.yaml'>YAML config</a></span></div>
        <details style='margin-bottom:8px;'><summary style='font-weight:bold;color:#2874a6;'>Show YAML Config</summary><pre style='background:#fff;border:1px solid #ccc;border-radius:4px;padding:8px;'>{config_yaml}</pre></details>
        {validation_html}
        {citation_html}
        {binding_table_html}
        {mutation_table_html}
        {therapies_html}
        {pathways_html}
        {literature_html}
        <div style='font-size:12px;color:#888;'>Visualization generated by <b>binding_visualizer.py</b> using <b>py3Dmol</b>.<br>Contact: <a href='mailto:your.email@example.com'>your.email@example.com</a><br>Copyright &copy; {datetime.datetime.now().year}</div>
    </div>
    """
    # --- Interactive Controls Injection ---
    # Prepare JS arrays for chains, ligands, mutations
    js_chains = pdb_meta['chains']
    js_ligands = pdb_meta['ligands']
    js_mutations = [
        {'chain': m.get('chain'), 'resnum': m.get('resnum'), 'mutation': m.get('mutation')}
        for m in mutation_list
    ]
    controls_html = (
        "<div style='margin:16px 0;padding:12px 16px;background:#f8f9fa;border-radius:8px;border:1px solid #e1e4e8;'>"
        "<b>Interactive Controls:</b>"
        "<div style='margin-top:8px;'>"
        "<label for='chain-select'>Chain:</label>"
        "<select id='chain-select'>"
        + ''.join([f"<option value='{c}'>{c}</option>" for c in js_chains]) +
        "</select>"
        "<button onclick=\"updateChain()\">Show Only</button>"
        "</div>"
        "<div style='margin-top:8px;'>"
        "<label for='ligand-select'>Ligand:</label>"
        "<select id='ligand-select'>"
        + ''.join([f"<option value='{l}'>{l}</option>" for l in js_ligands]) +
        "</select>"
        "<button onclick=\"highlightLigand()\">Highlight</button>"
        "</div>"
        "<div style='margin-top:8px;'>"
        "<label for='mutation-select'>Mutation:</label>"
        "<select id='mutation-select'>"
        + ''.join([f"<option value='{m['chain']}:{m['resnum']}'>{m['mutation']} ({m['chain']}:{m['resnum']})</option>" for m in js_mutations]) +
        "</select>"
        "<button onclick=\"highlightMutation()\">Highlight</button>"
        "</div>"
        "</div>"
        "<script>"
        "function updateChain() {"
        "  var chain = document.getElementById('chain-select').value;"
        "  if(typeof viewer === 'undefined') return;"
        "  viewer.setStyle({}, {});"
        "  viewer.setStyle({chain: chain}, {stick: {}});"
        "  viewer.render();"
        "}"
        "function highlightLigand() {"
        "  var ligand = document.getElementById('ligand-select').value;"
        "  if(typeof viewer === 'undefined') return;"
        "  viewer.setStyle({}, {});"
        "  viewer.setStyle({resn: ligand}, {stick: {colorscheme: 'yellowCarbon'}});"
        "  viewer.render();"
        "}"
        "function highlightMutation() {"
        "  var sel = document.getElementById('mutation-select').value;"
        "  var parts = sel.split(':');"
        "  if(parts.length !== 2 || typeof viewer === 'undefined') return;"
        "  var chain = parts[0];"
        "  var resi = parseInt(parts[1]);"
        "  viewer.setStyle({}, {});"
        "  viewer.setStyle({chain: chain, resi: resi}, {stick: {colorscheme: 'magentaCarbon'}});"
        "  viewer.render();"
        "}"
        "window.addEventListener('viewerReady', function(e) { window.viewer = e.detail.viewer; });"
        "</script>"
    )
    print(Fore.CYAN + f"[INFO] Saving visualization HTML to {output_html}" + Style.RESET_ALL)
    # Save the visualization to an HTML file, prepending info
    with open(output_html, 'w') as html_file:
        html = viewer._make_html()
        # Patch: assign viewer globally in JS after creation
        # Find the viewer variable name (e.g., viewer_12345) and assign to window.viewer
        import re
        match = re.search(r'var (viewer_\d+) = null;', html)
        viewer_var = match.group(1) if match else 'viewer'
        # Patch the JS: after createViewer, assign to window.viewer
        html = re.sub(
            rf'(\$3Dmolpromise\.then\(function\(\) \{{\s*{viewer_var} = \$3Dmol\.createViewer\([^)]+\);)',
            rf'\1\nwindow.viewer = {viewer_var};',
            html
        )
        # Insert info_html and controls_html after <body> if possible
        if '<body>' in html:
            html = html.replace('<body>', '<body>' + info_html + controls_html, 1)
        else:
            html = info_html + controls_html + html
        html_file.write(html)
    logging.info("Visualization saved to %s", output_html)
    print(Fore.GREEN + f"Visualization saved to {output_html}. Open this file in a browser to view the structure." + Style.RESET_ALL)
    # Optionally: Export JSON metadata
    if config.get('export_json', False):
        print(Fore.CYAN + f"[INFO] Exporting JSON metadata for {pdb_id}" + Style.RESET_ALL)
        meta = dict(
            pdb_id=pdb_id,
            title=pdb_title,
            method=pdb_meta['method'],
            resolution=pdb_meta['resolution'],
            ligands=pdb_meta['ligands'],
            chains=pdb_meta['chains'],
            binding_residues=binding_residues,
            mutations=mutation_list,
            therapies=therapies,
            pathways=pathways,
            literature=literature,
            validation=validation,
            citation=citation,
            script_hash=script_hash,
            config_hash=config_hash,
            git_hash=git_hash,
            user=user,
            host=host,
            python_version=os.sys.version.split()[0],
            platform=f"{platform.system()} {platform.release()}",
            timestamp=datetime.datetime.now().isoformat()
        )
        with open(os.path.join(this_script_folder_path, f"{pdb_id}_metadata.json"), 'w') as jf:
            json.dump(meta, jf, indent=2)
        print(Fore.GREEN + f"[SUCCESS] JSON metadata exported to {pdb_id}_metadata.json" + Style.RESET_ALL)

def main():
    print(Fore.CYAN + "[INFO] Starting binding_visualizer main workflow..." + Style.RESET_ALL)
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
        print(Fore.CYAN + f"[INFO] Fetching PDB data for {config['pdb_id']}..." + Style.RESET_ALL)
        # Fetch the PDB data using the helper
        pdb_data = fetch_pdb_data(config['pdb_id'])
        print(Fore.CYAN + f"[INFO] Visualizing structure for {config['pdb_id']}..." + Style.RESET_ALL)
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
        print(Fore.GREEN + f"[SUCCESS] Workflow completed for {config['pdb_id']}!" + Style.RESET_ALL)
    except Exception as error:
        logging.error("An error occurred in the main function: %s", error)
        print(Fore.RED + "An error occurred. Traceback is shown below:" + Style.RESET_ALL)
        print(Fore.YELLOW + traceback.format_exc() + Style.RESET_ALL)

# Execute the main function if the script is run as the main module
if __name__ == "__main__":
    main()
