import sys
import os
import random
from rdkit import Chem

sys.path.append(os.getcwd())
from src.pubchem_utils import fetch_properties_by_cids
from src.rdkit_utils import is_small_organic_molecule

def test_sampling():
    random.seed(42)
    # 100개 샘플링
    test_cids = [random.randint(1, 120000000) for _ in range(100)]
    df = fetch_properties_by_cids(test_cids)
    
    if df is None or df.empty:
        print("No data fetched from PubChem for these CIDs.")
        return
        
    print(f"Fetched {len(df)} compounds out of 100 requested.")
    
    for i, row in df.head(10).iterrows():
        smiles = row.get("CanonicalSMILES")
        mw = row.get("MolecularWeight")
        cid = row.get("CID")
        
        print(f"\nCID: {cid}")
        print(f"SMILES: {smiles}")
        print(f"MW: {mw}")
        
        if not isinstance(smiles, str):
            print("FAILED: No SMILES string.")
            continue
            
        mol = Chem.MolFromSmiles(smiles)
        if not mol:
            print("FAILED: RDKit cannot parse SMILES.")
            continue
            
        if not is_small_organic_molecule(mol):
            # 원인 분석을 위해 더 자세히 출력
            has_carbon = any(atom.GetSymbol() == 'C' for atom in mol.GetAtoms())
            allowed_elements = {'C', 'H', 'O', 'N', 'S', 'B', 'F', 'Cl', 'Br', 'I'}
            invalid_atoms = [atom.GetSymbol() for atom in mol.GetAtoms() if atom.GetSymbol() not in allowed_elements]
            
            print(f"FAILED Organic check: Has C? {has_carbon}, Invalid atoms: {invalid_atoms}")
            continue
            
        heavy_atoms = mol.GetNumHeavyAtoms()
        print(f"Heavy Atoms: {heavy_atoms}")
        
        if not (50 <= float(mw) <= 600):
            print(f"FAILED MW check: {mw}")
        elif not (3 <= heavy_atoms <= 80):
            print(f"FAILED Heavy Atoms check: {heavy_atoms}")
        else:
            print("SUCCESS: Valid organic molecule!")

if __name__ == "__main__":
    test_sampling()
