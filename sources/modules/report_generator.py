from yattag import Doc

def generate_gene_section(doc, gene, pathways):
    doc.line('h2', f'Gene: {gene}')
    doc.line('h3', 'Associated Pathways')
    with doc.tag('ul'):
        for pathway in pathways:
            doc.line('li', pathway)

def generate_drug_table(doc, drugs):
    doc.line('h3', 'Drugs and Therapies')
    with doc.tag('table', border="1"):
        with doc.tag('tr'):
            doc.line('th', 'Drug Name')
            doc.line('th', 'Drug ID')
        for drug in drugs:
            with doc.tag('tr'):
                doc.line('td', drug['name'])
                doc.line('td', drug['id'])

def generate_html_report(disease_info):
    doc, tag, text = Doc().tagtext()
    doc.asis('<!DOCTYPE html>')
    with tag('html'):
        with tag('head'):
            doc.line('title', 'Disease Report')
        with tag('body'):
            doc.line('h1', 'Disease Report')
            for gene, info in disease_info.items():
                generate_gene_section(doc, gene, info['pathways'])
                generate_drug_table(doc, info['drugs'])
    return doc.getvalue()

def main():
    disease_info = {
        "BRCA1": {
            "pathways": ["Pathway 1", "Pathway 2"],
            "drugs": [{"name": "Drug A", "id": "ID1"}, {"name": "Drug B", "id": "ID2"}]
        },
        "TP53": {
            "pathways": ["Pathway 3", "Pathway 4"],
            "drugs": [{"name": "Drug C", "id": "ID3"}, {"name": "Drug D", "id": "ID4"}]
        }
    }
    html_report = generate_html_report(disease_info)
    with open('disease_report.html', 'w') as file:
        file.write(html_report)

if __name__ == "__main__":
    main()
