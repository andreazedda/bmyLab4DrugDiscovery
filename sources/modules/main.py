import yaml
from disease_info_retriever import retrieve_disease_info
from report_generator import generate_html_report

def load_disease_name(config_file):
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    return config['disease_name']

def main():
    config_file = 'config.yaml'
    disease_name = load_disease_name(config_file)
    disease_info = retrieve_disease_info(disease_name)
    if disease_info:
        html_report = generate_html_report(disease_info)
        with open('disease_report.html', 'w') as file:
            file.write(html_report)
    else:
        print("No information found for the given disease.")

if __name__ == "__main__":
    main()
