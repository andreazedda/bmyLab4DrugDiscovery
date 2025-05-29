import requests
import pandas as pd
from bioservices import KEGG, Reactome
from chembl_webresource_client.new_client import new_client

def get_gene_associations(disease_name):
    url = f"https://www.disgenet.org/api/gda/disease/{disease_name}"
    try:
        response = requests.get(url, allow_redirects=True)
        if response.status_code == 200:
            try:
                return response.json()
            except Exception as e:
                print(f"Errore nel parsing della risposta JSON: {e}\nRisposta: {response.text}")
                return None
        else:
            print(f"Errore nella richiesta a DisGeNET: codice {response.status_code}\nRisposta: {response.text}")
            return None
    except Exception as e:
        print(f"Errore nella connessione a DisGeNET: {e}")
        return None

def get_biological_pathways(genes):
    kegg = KEGG()
    reactome = Reactome()
    pathways = {}
    for gene in genes:
        kegg_pathways = kegg.get_pathway_by_gene(gene)
        reactome_pathways = reactome.query(gene)
        pathways[gene] = {
            "KEGG": kegg_pathways,
            "Reactome": reactome_pathways
        }
    return pathways

def get_drugs_and_therapies(genes):
    drug = new_client.target
    drugs = {}
    for gene in genes:
        res = drug.filter(target_synonym__icontains=gene)
        drugs[gene] = res
    return drugs

def retrieve_disease_info(disease_name):
    gene_associations = get_gene_associations(disease_name)
    if gene_associations:
        genes = [gene['geneSymbol'] for gene in gene_associations]
        pathways = get_biological_pathways(genes)
        drugs = get_drugs_and_therapies(genes)
        return {
            "genes": genes,
            "pathways": pathways,
            "drugs": drugs
        }
    else:
        return None

def main():
    disease_name = "Multiple Myeloma"
    disease_info = retrieve_disease_info(disease_name)
    if disease_info:
        df = pd.DataFrame(disease_info)
        df.to_html("disease_info.html")
    else:
        print("No information found for the given disease.")

if __name__ == "__main__":
    main()
