import argparse, re, sys, os, yaml, logging, traceback
from pathlib import Path
import pandas as pd
from collections import Counter
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import date
import bamnostic as bs
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import threading

def init_logging(config):
    
    """Initialise un logging dans un dossier accessible en écriture."""
    
    # 1. Chemin depuis config.yaml si présent
    log_path_cfg = None
    try:
        log_path_cfg = config.get("chemins", {}).get("log_file", None)
    except Exception:
        log_path_cfg = None
    
    date_du_jour = date.today().isoformat()

    # 2. Résolution : si fourni → Path absolu
    if log_path_cfg:
        log_file = Path(log_path_cfg)
        if log_file.is_dir() or not log_file.suffix:
            log_file = log_file / f"journal_{date_du_jour}.log"
        
        if not log_file.is_absolute():
            base_dir = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent
            log_file = base_dir / log_file
    else:
        base_dir = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent
        log_file = base_dir / f"journal_{date_du_jour}.log"

    # 4. Créer le dossier si besoin
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # 5. Configurer logging *explicite* (ne pas dépendre de basicConfig implicite)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    logger.handlers.clear()

    # File handler
    fh = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    fh.setLevel(logging.DEBUG)

    fmt = logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    fh.setFormatter(fmt)

    logger.addHandler(fh)

    # Optionnel : log en console *si* mode non-noconsole (utile dev)
    if not getattr(sys, 'frozen', False) or sys.stdout:
        sh = logging.StreamHandler(sys.stdout)
        sh.setLevel(logging.INFO)
        sh.setFormatter(fmt)
        logger.addHandler(sh)

    logger.debug(f"Logging initialisé. Fichier log : {log_file}")
    return log_file

def dataframe_to_pdf(df, path, config=None, resume_global=None):

    """Génère un PDF contenant un tableau à partir d'un Tableau de données."""

    if config is None:
        config = CONFIG

    doc = SimpleDocTemplate(str(path), pagesize=landscape(A4), leftMargin=10, rightMargin=10, topMargin=15, bottomMargin=15)

    elements = []
    styles = getSampleStyleSheet()
    wrap_style = ParagraphStyle("wrap", fontSize=8, leading=10)
    italic_style = ParagraphStyle("italic", parent=styles["Normal"], fontName="Helvetica-Oblique", fontSize=10)

    if config:
        elements.append(Paragraph(f"IV Global Report {date.today().isoformat()}", styles["Title"]))
        elements.append(Spacer(1, 12))

        parametres = config.get("parametres", {})

        libelles = {
                "profondeur_min": "Profondeur de lecture minimale",
                "seuil_heterozygotie": "Seuil hétérozygotie",
                "taux_defini": "Taux seuil de discordance",
                "profondeur_autorisee": "Nombre de SNPs à faible profondeur autorisés",}

        parametres_filtres = {k: v for k, v in parametres.items() if k in libelles}

        if parametres_filtres:
            elements.append(Paragraph("Paramètres utilisés :", italic_style))
            for cle, val in parametres_filtres.items():
                libelle = libelles.get(cle, cle.replace('_', ' ').capitalize())
                texte = f"• {libelle} : {val}"
                elements.append(Paragraph(texte, italic_style))
            elements.append(Spacer(1, 12))

            if resume_global:
                for cle, val in resume_global.items():
                    ligne_resume = f"• {cle} : {val}"
                    elements.append(Paragraph(ligne_resume, italic_style))
                elements.append(Spacer(1, 12))
    else:
        elements.append(Paragraph(f"IV Global Report {date.today().isoformat()}", styles["Title"]))
        elements.append(Spacer(1, 12))

        if resume_global:
            for cle, val in resume_global.items():
                ligne_resume = f"• {cle} : {val}"
                elements.append(Paragraph(ligne_resume, italic_style))
            elements.append(Spacer(1, 12))

    data = [df.columns.tolist()]
    nb_colonnes = len(df.columns)
    colWidths = []

    for i in range(nb_colonnes):
        if i >= nb_colonnes - 1 :
            colWidths.append(250)
        elif i == nb_colonnes - 2 :
            colWidths.append(150)
        else:
            colWidths.append(60)
    for ligne in df.values.tolist():
        row = []
        for val in ligne:
            if isinstance(val, str) and len(val) > 60:
                row.append(Paragraph(val.replace("\n", "<br/>"), wrap_style))
            else:
                row.append(val)
        data.append(row)

    table = Table(data, repeatRows=1, colWidths=colWidths)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('BACKGROUND', (0,1), (-1,-1), colors.whitesmoke),
    ]))
    elements.append(table)

    doc.build(elements)

def generer_pdf_final(chemin_personnalise=None, config=None, resume_global=None):
    logging.debug(f"generer_pdf_final appelé avec chemin_personnalise={chemin_personnalise}")
    dossier = dossier_rapp(chemin_personnalise)
    date_str = date.today().isoformat()
    csv_temp = dossier / f"global_report_IV_{date_str}.csv"
    rapport_path = dossier / f"global_report_IV_{date_str}.pdf"
    logging.debug(f"CSV attendu : {csv_temp}")
    logging.debug(f"PDF de sortie : {rapport_path}")

    if not csv_temp.exists():
        logging.warning(f"Impossible de générer PDF : CSV {csv_temp} introuvable.")
        return

    try:
        df = pd.read_csv(csv_temp)
        logging.debug(f"CSV chargé : {df.shape[0]} lignes, {df.shape[1]} colonnes.")
    except Exception:
        logging.error("Lecture CSV échouée:\n" + traceback.format_exc())
        return

    try:
        dataframe_to_pdf(df, rapport_path, config=None, resume_global=resume_global)
        logging.info(f"PDF généré : {rapport_path}")
    except Exception:
        logging.error("Erreur dans dataframe_to_pdf:\n" + traceback.format_exc())
        return

    try:
        os.remove(csv_temp)
        logging.debug("CSV temporaire supprimé.")
    except Exception:
        logging.warning("Suppression CSV temporaire échouée:\n" + traceback.format_exc())

def charger_config(nom_fichier="config.yaml"):

    """Charge un fichier de configuration YAML placé à côté du script ou de l'exécutable."""
    
    try:
        dossier_base = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent
        chemin_config = dossier_base / nom_fichier
        with open(chemin_config, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"[ERREUR] Impossible de charger la configuration : {e}")
        return {}

def verifier_config(config):

    """Vérifie que le fichier de configuration contient toutes les clés nécessaires."""

    erreurs = []

    if "chemins" not in config:
        erreurs.append("Section 'chemins' manquante.")
    else:
        chemins_requis = [
            "dossier_rapports_par_defaut",
            "fichier_csv",
            "dossier_bam",
            "tableau_concordance"
        ]
        for chemin in chemins_requis:
            if chemin not in config["chemins"]:
                erreurs.append(f"Clé 'chemins/{chemin}' manquante.")

    if "parametres" not in config:
        erreurs.append("Section 'parametres' manquante.")
    else:
        if "profondeur_min" not in config["parametres"]:
            erreurs.append("Clé 'parametres/profondeur_min' manquante.")
        if "seuil_heterozygotie" not in config["parametres"]:
            erreurs.append("Clé 'parametres/seuil_heterozygotie' manquante.")
        if "taux_defini" not in config["parametres"]:
            erreurs.append("Clé 'parametres/taux_defini' manquante.")
        if "nom_colonne_position" not in config["parametres"]:
            erreurs.append("Clé 'parametres/nom_colonne_position' manquante.")
        if "nom_colonne_chr" not in config["parametres"]:
            erreurs.append("Clé 'parametres/nom_colonne_chr' manquante.")
        if "profondeur_autorisee" not in config["parametres"]:
            erreurs.append("Clé 'parametres/profondeur_autorisee' manquante.")
        if "nom_colonne_samplename" not in config["parametres"]:
            erreurs.append("Clé 'parametres/nom_colonne_samplename' manquante.")
        if "nom_colonne_rang" not in config["parametres"]:
            erreurs.append("Clé 'parametres/nom_colonne_rang' manquante.")
    if erreurs:
        message = "\n".join(f"- {e}" for e in erreurs)
        raise ValueError(f"Fichier config.yaml invalide :\n{message}")

def get_parametre(nom, default=None):

    """Accès aux paramètres numériques du fichier config"""

    try:
        return CONFIG["parametres"].get(nom, default)
    except Exception:
        return default

def get_chemin(nom, default=None):

    """Accès aux chemins du fichier config"""

    try:
        return CONFIG["chemins"].get(nom, default)
    except Exception:
        return default

def extraire_id(identite):
    
    """Extrait l'ID numérique du patient à partir d'une chaîne de caractères."""

    matches = re.findall(r"\d{9}", str(identite))
    return matches[0] if matches else None

def dossier_rapp(chemin_personnalise=None):

    """Crée un dossier de rapports avec la date actuelle."""

    config = charger_config()
    if chemin_personnalise:
        base = Path(chemin_personnalise)
    else:
        base = Path(config.get("chemins", {}).get("dossier_rapports_par_defaut", "C:/Users/user/Documents/rapports"))
    
    date_str = date.today().isoformat()
    chemin = base / (f"identitovigilance_{date_str}")
    chemin.mkdir(parents=True, exist_ok=True)
    return chemin

def ajouter_rapport_global(resume, chemin_personnalise=None):

    """Permet d'obtenir un dossier avec un rapport global des résultats"""
    
    dossier = dossier_rapp(chemin_personnalise)
    date_str = date.today().isoformat()
    csv_temp = dossier / f"global_report_IV_{date_str}.csv"

    if csv_temp.exists():
        ancien_resume = pd.read_csv(csv_temp)
        resume_total = pd.concat([ancien_resume, resume], ignore_index=True)
    else:
        resume_total = resume.copy()

    resume_total.to_csv(csv_temp, index=False)

def ouvrir_dossier_rap():

    """Ouvre le dossier de rapports par défaut ou personnalisé."""

    chemin = dossier_rapp()
    os.startfile(chemin)

def analyse_dossier_parent(dossier_bam):
    
    """ Explore le sous-dossier du Run sélectionné pour trouver les fichiers BAM associés à un patient. """
    
    dossier_bam = Path(dossier_bam)

    chemin_analysis = dossier_bam / "Analysis" / "1" / "Data"
    if chemin_analysis.is_dir():
        dossier_bam = chemin_analysis

    bam_paths = []

    for fichier_bam in dossier_bam.rglob("*.bam"):
        id_patient = extraire_id(fichier_bam.name)
        if id_patient:
            bam_paths.append(fichier_bam)

    return bam_paths

def bam_vide(bam_path):

    """Retourne True si le fichier BAM est vide (aucune lecture alignée)."""

    try:
        with bs.AlignmentFile(bam_path, "rb") as bamfile:
            for _ in bamfile:
                return False
        return True
    except Exception:
        return True

def extraire_fichiers(bam_path, csv_path, tableau_concordance):

    """Extrait la ligne du CSV correspondant au fichier BAM selon l'ID patient."""

    samplename = str(get_parametre("nom_colonne_samplename", "Sample Name")).strip()
    rang = str(get_parametre("nom_colonne_rang", "Rang")).strip()

    try :
        id_patient = "".join([c for c in Path(bam_path).stem if c.isdigit()])

        if isinstance(tableau_concordance, str):
            tableau_concordance = pd.read_csv(tableau_concordance, dtype=str, sep=";", encoding="utf-8")
            tableau_concordance.columns = tableau_concordance.columns.str.strip()

        if "Rang" not in tableau_concordance.columns:
            print("[ERREUR] La colonne 'Rang' est introuvable. Colonnes présentes :", tableau_concordance.columns.tolist())
            raise KeyError("La colonne 'Rang' est absente ou mal nommée dans le fichier de concordance.")

        tableau_concordance[f"{rang}"] = tableau_concordance["Rang"].astype(str).str.strip()
        tableau_concordance[f"{rang}"] = pd.to_numeric(tableau_concordance[f"{rang}"], errors="coerce")

        if isinstance(csv_path, str):
            csv_files = pd.read_csv(csv_path, sep=";", dtype=str, encoding="utf-8")
        else:
            csv_files = csv_path
        
        if samplename not in csv_files.columns:
            raise KeyError(f"La colonne '{samplename}' est absente du fichier CSV.")


        if csv_files[f"{samplename}"].str.contains("H2O", case=False, na=False).any():
            ligne_h2o = csv_files[csv_files[f"{samplename}"].str.contains("H2O")]
            series_ligne_h2o = ligne_h2o.iloc[0]

            for val in series_ligne_h2o.index :
                contenu = str(series_ligne_h2o[val]).strip()
                cel_pas_vides = re.match(r"^(\d{1,2})_([ATCG])$", contenu, re.IGNORECASE)
                if cel_pas_vides :
                    logging.error(f"Problème avec le blanc, {contenu} trouvé" )
                    raise ValueError("Le blanc n'est pas vide.")
                else :
                    continue

        if samplename not in csv_files.columns:
            raise KeyError("La colonne 'Sample Name' est absente du fichier CSV.")
        else :
            csv_files["ID_NUM"] = csv_files[f"{samplename}"].apply(extraire_id)

        if isinstance(csv_path, pd.DataFrame) and len(csv_path) == 1:
            csv_row = csv_path.iloc[0]
        else:
            ligne_patient = csv_files[csv_files["ID_NUM"] == id_patient]
            if ligne_patient.empty:
                logging.warning(f"Patient ID {id_patient} non trouvé dans le CSV. BAM ignoré.")
                return None, None, None, None
            csv_row = ligne_patient.iloc[0]
    except Exception as e :
        raise RuntimeError(f"Erreur lors de l'extraction des fichiers : {e}")
    
    return csv_row, tableau_concordance, bam_path, id_patient

def id_bam_csv(bam_path, csv_files):

    """Vérifie la présence de tous les BAM et de tous les CSV:
        - ids_bam_sans_csv : IDs trouvés dans les BAMs mais absents du CSV
        - ids_csv_sans_bam : IDs présents dans le CSV mais sans fichier BAM associé """
    
    samplename = get_parametre("nom_colonne_samplename", "Sample Name").strip()
    
    ids_bam = set()
    for chemin in bam_path:
        id_bam = extraire_id(Path(chemin).stem)
        if id_bam:
            ids_bam.add(id_bam)

    df_csv_sansH20 = csv_files[~csv_files[f"{samplename}"].str.contains("H2O", case=False, na=False)].copy()
    df_csv_sansH20["ID_NUM"] = df_csv_sansH20[f"{samplename}"].apply(extraire_id)
    ids_csv = set(df_csv_sansH20["ID_NUM"].dropna().unique())

    ids_csv_sans_bam = ids_csv - ids_bam
    ids_bam_sans_csv = ids_bam - ids_csv

    if ids_bam_sans_csv:
        logging.warning(f"IDs BAM sans CSV correspondant : {ids_bam_sans_csv}")
    if ids_csv_sans_bam:
        logging.warning(f"IDs CSV sans BAM correspondant : {ids_csv_sans_bam}")

    return ids_bam_sans_csv, ids_csv_sans_bam

def extraire_donnees(csv_row, tableau_concordance, bam_path, id_patient):

    """Extrait les données des SNPs à partir du tableau de concordance et du fichier csv du patient."""

    nom_colonne_position = str(get_parametre("nom_colonne_position")).strip()
    nom_colonne_chr = str(get_parametre("nom_colonne_chr")).strip()
    nom_colonne_rang = str(get_parametre("nom_colonne_rang", "Rang")).strip()

    SNPx = {}
    snp_vides =[]
    
    colonnes = csv_row.index
    dico_alleles_csv = {}

    for cellules_alleles in colonnes :
        valeur = str(csv_row[cellules_alleles]).strip()
        match = re.match(r"^(\d{1,2})_([ACGT])$", valeur, re.IGNORECASE)
        if match :
            rang = int(match.group(1))
            base = match.group(2).upper()
            if rang not in dico_alleles_csv:
                dico_alleles_csv[rang] = [base]
            else:
                dico_alleles_csv[rang].append(base)
    
    for rang, valeurs in dico_alleles_csv.items() :
        if len(valeurs) == 1:
            dico_alleles_csv[rang] = 2 * valeurs

    rangs_valides = set(tableau_concordance[f"{nom_colonne_rang}"].dropna().astype(int))

    for rang_snp, bases in dico_alleles_csv.items():
        if rang_snp not in rangs_valides:
            continue

        ligne_concordance = tableau_concordance[tableau_concordance[f"{nom_colonne_rang}"] == rang_snp]
        if ligne_concordance.empty:
            raise ValueError(f"Rang {rang_snp} non trouvé dans le tableau de concordance.")
        
        ligne_concordance = ligne_concordance.iloc[0]

        position = None
        chromosome = None

        for col in ligne_concordance.index:
            if str(col).strip().startswith(f"{nom_colonne_chr}"):
                raw_chr = ligne_concordance[col]
                chromosome = str(int(raw_chr)) if not pd.isna(raw_chr) else None
            elif str(col).strip().startswith(f"{nom_colonne_position}"):
                raw_pos = ligne_concordance[col]
                position = int(raw_pos) if not pd.isna(raw_pos) else None
        
        if chromosome is None or position is None:
            raise ValueError(f"Coordonnées manquantes pour le SNP de rang {rang_snp}.")

        if chromosome is None or position is None:
            print(ligne_concordance.to_string())
            raise ValueError(f"Coordonnées manquantes pour {rang_snp} dans le tableau de concordance.")

        snp_id = f"{rang_snp}_{chromosome}"
    
        SNPx[snp_id] = {"CHROM": chromosome, "RANG": rang_snp, "POS" : position, "ALLELES": tuple(bases)}

    regions = []
    for snp_id, info in SNPx.items():
        region = f"{info['CHROM']}:{info['POS']}-{info['POS']}"
        regions.append(region)
    
    rangs_absents = rangs_valides - dico_alleles_csv.keys()
    for rang_absent in rangs_absents:
        ligne = tableau_concordance[tableau_concordance[f"{nom_colonne_rang}"] == rang_absent]
        if not ligne.empty:
            ligne = ligne.iloc[0]
            chromosome = ligne.get(f"{nom_colonne_chr}", "?")
            position = ligne.get(f"{nom_colonne_position}", "?")
            snp_vides.append((chromosome, position))
    
    return bam_path, id_patient, SNPx, regions, snp_vides

def normaliser_chr(region_chr, bam_file):

    """Essaie d'ajuster automatiquement le nom du chromosome en fonction de ceux du BAM."""

    if region_chr in bam_file.references:
        return region_chr
    elif f"chr{region_chr}" in bam_file.references:
        return f"chr{region_chr}"
    elif region_chr.startswith("chr") and region_chr[3:] in bam_file.references:
        return region_chr[3:]
    elif region_chr.upper() in bam_file.references:
        return region_chr.upper()
    else:
        raise ValueError(f"[ERREUR] Le chromosome '{region_chr}' n'a pas de correspondance dans le BAM.")

def obtenir_bases_bam(bam_path, regions):

    """Récupère les bases du fichier BAM pour les régions spécifiées."""

    base_counts = {}

    try:
        bam_file = bs.AlignmentFile(bam_path, "rb")
    except FileNotFoundError:
        raise FileNotFoundError(f"Le fichier BAM '{bam_path}' n'existe pas ou n'est pas accessible.")

    for region in regions:
        region_chr, region_pos_intervalle = region.split(":")
        start, _ = map(int, region_pos_intervalle.split("-"))
        pos = start  # ici start == end car on donne une position unique sous forme X-Y
        bases = []

        region_chr = normaliser_chr(region_chr, bam_file)

        try:
            for read in bam_file.fetch(region_chr, pos-1, pos):
                                
                if read.is_unmapped or read.is_secondary or read.is_supplementary:
                    continue
                
                ref_pos = read.pos
                query_pos = 0
                for op in read.cigar:
                    try:
                        type_operation, length = op[:2]
                    except Exception as e:
                        print(f"[ERREUR] CIGAR non standard dans {read.query_name} : {op}")
                        continue
                    
                    if type_operation == 0:  # Match
                        for i in range(length):
                            if ref_pos == pos - 1 and query_pos < len(read.query_sequence):
                                base = read.query_sequence[query_pos]
                                bases.append(base)
                            ref_pos += 1
                            query_pos += 1
                    elif type_operation == 1: # Insertion
                        query_pos += length
                    elif type_operation == 2: # Deletion
                        ref_pos += length
            
            if bases:
                comptage = Counter(bases)
                base_counts[(region_chr, pos)] = dict(comptage)
            else:
                base_counts[(region_chr, pos)] = {}
        except ValueError as e:
            print(f"[DEBUG] Erreur lors de la récupération des bases pour {region}: {e}")
    
    bam_file.close()
    return base_counts

def analyser_snp(SNPx, base_counts, id_patient):

    """Analyse les SNPs et compare les génotypes du fichier BAM avec ceux du CSV."""

    profondeur_min = get_parametre("profondeur_min", 15)
    seuil_heterozygotie = get_parametre("seuil_heterozygotie", 0.75)
    
    resultats = []

    for snp_id, info in SNPx.items():
        valeur_chromosome = info["CHROM"]
        chrom = valeur_chromosome if valeur_chromosome.startswith("chr") else "chr" + valeur_chromosome
        position = info["POS"]
        alleles_csv = tuple(sorted(info["ALLELES"]))

        comptage_snp = Counter(base_counts.get((chrom, position), {}))
        most_common = comptage_snp.most_common(2)
 
        if len(comptage_snp) == 0:
            genotype_bam = "ABSENCE_DE_GENOTYPE"
        else:
            total = sum(comptage_snp.values())
            base_prems, frequence_prems = most_common[0]

            if len(most_common) == 1 or frequence_prems >= seuil_heterozygotie * total:
                genotype_bam = base_prems * 2
            elif len(most_common) >= 2 :
                base_seconde, frequence_seconde = most_common[1]
                if frequence_seconde >= seuil_heterozygotie * total:
                    genotype_bam = base_seconde * 2
                elif frequence_prems != frequence_seconde and frequence_prems < seuil_heterozygotie * total and frequence_seconde < seuil_heterozygotie * total:
                    genotype_bam = "".join(sorted([base_prems, base_seconde]))
                elif frequence_prems == frequence_seconde:
                    genotype_bam = "".join(sorted([base_prems, base_seconde]))
                else:
                    genotype_bam = "NO_CALL"

        genotype_csv = "".join(alleles_csv)
        match = "OK" if genotype_bam == genotype_csv else ("NO_CALL" if genotype_bam == "NO_CALL" else "DISCORDANT")

        chr_num_digit = re.findall(r"(\d+)", chrom)
        chr_num = chr_num_digit[0] if chr_num_digit else ""
        
        resultats.append({
            "ID_Patient_BAM": id_patient,
            "SNP_ID": snp_id,
            "CHROM": chr_num,
            "POS": position,
            "GT_CSV": genotype_csv,
            "GT_BAM": genotype_bam,
            "Match": match,
            "Depth": sum(comptage_snp.values()),
            "Bases": dict(comptage_snp)
        })

    df_resultats = pd.DataFrame(resultats)
    df_resultats["Visuel"] = df_resultats["Match"].map({"OK": "V", "DISCORDANT": "X", "NO_CALL": "?"})
    df_resultats["Depth Indicator"] = df_resultats["Depth"].apply(lambda x: "OK" if x >= profondeur_min else "!!!")
    df_resultats["ID_Patient_BAM"] = id_patient
    
    for col in ["GT_CSV", "GT_BAM"]:
        df_resultats[col] = df_resultats[col].str.upper()

    return df_resultats

def analyse_conco(df_resultats, id_patient, tableau_concordance, snp_vides):

    """Analyse le taux de concordance entre les génotypes du BAM et ceux du CSV pour un patient donné."""

    taux_defini = get_parametre("taux_defini", 90)
    profondeur_min = get_parametre("profondeur_min", 15)
    profondeur_autorisee = get_parametre("profondeur_autorisee", 5)

    remarques=[]
    long_SNP = len(tableau_concordance)
    total_calls = len(df_resultats)
    concordants = df_resultats[df_resultats["Match"] == "OK"]

    taux = (len(concordants) / long_SNP) * 100 if long_SNP > 0 else 0

    low_depth_snps = df_resultats[df_resultats["Depth"] < profondeur_min]
    
    resume = pd.DataFrame({
        "Patient_ID": [id_patient],
        "Rate": [f"{len(concordants)} / {long_SNP}" if long_SNP > 0 else "0"],
        "Match State": ["\u2714"] if taux >= taux_defini else ["X"],
        "Match": ["OK"] if taux >= taux_defini else ["DISCORDANT"],
        "Depth (N)": [f"Low ({len(low_depth_snps)})" if (df_resultats["Depth Indicator"] == "!!!").any() else "OK"]})
        
    if not low_depth_snps.empty:
        bases_formatees = []
        base_str = f"Bases à faible profondeur : \n"
        for _, row in low_depth_snps.iterrows():
            base_str += f"chr{row['CHROM']}:{row['POS']} - {row['GT_BAM']} ({row['Depth']})\n"
        bases_formatees.append(base_str)
        remarques.append("\n".join(bases_formatees))
    
    if len(low_depth_snps) > profondeur_autorisee:
        logging.warning(f"Patient {id_patient} - Trop de SNPs à faible profondeur ({len(low_depth_snps)})")
        remarques.append(f"Trop de SNPs à faible profondeur ({len(low_depth_snps)})")

    if long_SNP != total_calls :
        remarques_formatees = "\n".join([f"chr{chrom}:{pos}" for chrom, pos in snp_vides])
        remarques.append(f"Positions manquantes dans le SNPplex : \n{remarques_formatees}\n")

    resume["REMARQUES"] = ["\n".join(remarques) if remarques else " "]
    
    logging.info(f"Patient {id_patient} - Taux de concordance : {float(taux):.1f}%")

    return taux, resume

def analyse_discor(bam_path, csv_path, tableau_concordance):

    """Analyse les SNP discordants et compare le fichier BAM avec le CSV d'autres patients."""

    taux_defini = get_parametre("taux_defini", 90)
    samplename= str(get_parametre("nom_colonne_samplename", "Sample Name")).strip()

    try:
        csv_row, tableau_concordance, bam_path, id_patient = extraire_fichiers(bam_path, csv_path, tableau_concordance)
        nom_patient_passe = csv_row[f"{samplename}"].strip()
        bam_path, id_patient, SNPx, regions, snp_vides = extraire_donnees(csv_row, tableau_concordance, bam_path, id_patient)
        base_counts = obtenir_bases_bam(bam_path, regions)
    except Exception as e:
        raise KeyError(f"Erreur d'extraction : {e}")

    df_resultats = analyser_snp(SNPx, base_counts, id_patient)
    taux, _ = analyse_conco(df_resultats, id_patient, tableau_concordance, snp_vides)

    if taux < taux_defini :
        
        csv_all = pd.read_csv(csv_path, sep=";")
        csv_all.columns = csv_all.columns.str.strip()
        meilleur_taux = taux
        meilleur_patient = id_patient

        for _, ligne in csv_all.iterrows():

            if ligne[f"{samplename}"] == nom_patient_passe:
                continue
            nom_autre_patient = ligne[f"{samplename}"]
            id_alt = extraire_id(nom_autre_patient)

            try:
                _, _, SNPx_alt, regions_alt, snp_vides_alt = extraire_donnees(ligne, tableau_concordance, bam_path, id_alt)
                base_counts_alt = obtenir_bases_bam(bam_path, regions_alt)
                resultats_alt = analyser_snp(SNPx_alt, base_counts_alt, nom_autre_patient)
                taux_alt, _ = analyse_conco(resultats_alt, nom_autre_patient, tableau_concordance, snp_vides_alt)

                if taux_alt > meilleur_taux :
                    meilleur_taux = taux_alt
                    meilleur_patient = nom_autre_patient
            except Exception as e:
                print(f"[!] Erreur lors du test avec {nom_autre_patient} : {e}")
                logging.warning(f"[!] Erreur lors du test avec {nom_autre_patient} : {e}")

        if meilleur_patient != id_patient:
            id_autre_patient = extraire_id(meilleur_patient)
            df_resultats["ID_Patient_Alternatif"] = id_autre_patient
            df_resultats["Taux Alternatif"] = f"{float(meilleur_taux):.1f}"
            df_resultats["Match State"] = "OK" if meilleur_taux >= taux_defini else "DISCORDANT"

    return meilleur_taux, df_resultats

def traitement_fichier_bam(bam_path, csv_path, tableau_concordance, chemin_personnalise=None):

    """Traite un fichier BAM et un CSV pour analyser les SNPs et générer un rapport global."""

    logging.info(f"Analyse du fichier : {bam_path}")

    taux_defini = get_parametre("taux_defini", 90)

    try:
        csv_row, tableau_concordance, bam_path, id_patient = extraire_fichiers(bam_path, csv_path, tableau_concordance)
    except ValueError :
        return
    except Exception as e:
        raise ValueError(f"Erreur lors de l'analyse : {e}")
    
    try :
        bam_path, id_patient, SNPx, regions, snp_vides = extraire_donnees(csv_row, tableau_concordance, bam_path, id_patient)
        bases_counts = obtenir_bases_bam(bam_path, regions)
        df_resultats = analyser_snp(SNPx, bases_counts, id_patient)
        taux, resume = analyse_conco(df_resultats, id_patient, tableau_concordance, snp_vides)
    except Exception as e:
        logging.error(f"Erreur lors de l'analyse des SNPs : {e}")
        return None, None, []
    
    Patients_discordants=[]

    if taux < taux_defini :
        Patients_discordants.append((id_patient, taux))
        logging.warning(f"Patient {id_patient} - Discordance détectée : {float(taux):.1f}%")
        taux, df_resultats = analyse_discor(bam_path, csv_path, tableau_concordance)
        
        if "ID_Patient_Alternatif" in df_resultats.columns:
            patient_alt = df_resultats["ID_Patient_Alternatif"].iloc[0]
            taux_alt = df_resultats["Taux Alternatif"].iloc[0]
            remarque = f"ATTENTION Possible inversion avec {patient_alt} (taux : {float(taux_alt):.1f}%)"
        else:
            remarque = " "
        
        if "REMARQUES" not in resume.columns:
            resume["REMARQUES"] = ["-"]

        ancienne_remarque = resume["REMARQUES"][0] if resume["REMARQUES"][0] != "-" else " "
        if ancienne_remarque:
            resume["REMARQUES"] = [f"{ancienne_remarque}\n{remarque}"]
        else:
            resume["REMARQUES"] = [remarque]

    for col in ["ID_Patient_Alternatif", "Taux Alternatif", "Match State"]:
        if col not in df_resultats.columns:
            df_resultats[col] = " "
    
    ajouter_rapport_global(resume, chemin_personnalise)
    rapport_chemin = dossier_rapp(chemin_personnalise) / f"detailed_report_{date.today().isoformat()}.csv"

    if not rapport_chemin.exists():
        df_resultats.to_csv(rapport_chemin, index=False)
    else:
        df_resultats.to_csv(rapport_chemin, mode='a', header=False, index=False)

    return taux, df_resultats, Patients_discordants

def main():

    parser = argparse.ArgumentParser(description="Analyse SNP à partir d'un fichier BAM et d'un CSV.")
    parser.add_argument("--bam_path", type=str, help="Chemin vers le fichier BAM.")
    parser.add_argument("--dossier_bam", type=str, help="Répertoire patients")
    parser.add_argument("--csv_path", type=str, help="Chemin vers le fichier CSV.")
    parser.add_argument("--tableau_concordance", type=str, default="tableau_concordance.csv",
                        help="Chemin vers le fichier Excel de concordance (par défaut : tableau_concordance.csv).")
    args = parser.parse_args()

    taux_defini = get_parametre("taux_defini", 90)

    if args.dossier_bam :
        try :
            liste_bam = analyse_dossier_parent(args.dossier_bam)
            for fichier_bam in liste_bam:
                try :
                    taux, df_resultats, _ = traitement_fichier_bam(fichier_bam, args.csv_path, args.tableau_concordance)
                    if taux >= taux_defini :
                        print(f"Profil conforme pour {fichier_bam.name} avec un taux de concordance de {taux:.1f}%")
                        print(df_resultats[["SNP_ID", "POS", "GT_CSV", "GT_BAM", "Bases", "Depth", "Visuel", "Depth Indicator"]])
                    elif taux < taux_defini :
                        print("Profil non conforme.")
                        nombre_discordants = (df_resultats["Match"] != "OK").sum()
                        print(f"SNP discordants : {nombre_discordants}")
                        print(df_resultats[df_resultats["Match"] == "DISCORDANT"][["SNP_ID", "POS", "GT_CSV", "GT_BAM", "Bases", "Depth", "Visuel", "Depth Indicator"]])
                    return taux, df_resultats
                except Exception as e :
                    logging.error(f"[ERREUR] BAM ignoré :\n{traceback.format_exc()}")
                    continue
        except Exception as e :
            logging.error(f"Erreur : {e}")
            return
    elif args.bam_path :
        try:
            taux, df_resultats, _ = traitement_fichier_bam(args.bam_path, args.csv_path, args.tableau_concordance)
            if taux < taux_defini :
                print("Profil non conforme.")
                nombre_discordants = (df_resultats["Match"] != "OK").sum()
                print(f"SNP discordants : {nombre_discordants}")
                print(df_resultats[df_resultats["Match"] == "DISCORDANT"][["SNP_ID", "POS", "GT_CSV", "GT_BAM", "Bases", "Depth", "Visuel", "Depth Indicator"]])
                return taux, df_resultats
        except Exception as e:
            logging.error("Erreur inattendue : " + traceback.format_exc())
            return
    else :
        raise FileNotFoundError("Pas de fichier ni de dossier bam")

def interface():

    csv_path = ""
    bam_path = ""
    tableau_concordance = ""
    dossier_bam = ""
    etat_initial = "Aucun fichier sélectionné"
    chemin_rapports = None

    def center_window(window, width=580, height=500):
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = int((screen_width - width) / 2)
        y = int((screen_height - height) / 2)
        window.geometry(f"{width}x{height}+{x}+{y}")

    def choisir_dossier_rapport():
        nonlocal chemin_rapports
        chemin_rapports = filedialog.askdirectory(title="Choisissez le dossier de stockage des rapports")
        if chemin_rapports:
            label_dossier_rapport.config(text=Path(chemin_rapports).name, fg="#799068")
        etat_bouton()

    def trouver_fichier_bam():
        nonlocal bam_path
        fichier_bam = filedialog.askopenfilename(
            title="Sélectionnez le fichier BAM",
            filetypes=[("Fichier BAM", "*.bam")],
            initialdir=get_chemin("dossier_bam", "")
            )
        if not fichier_bam:
            messagebox.showwarning("Aucun fichier sélectionné", "Veuillez sélectionner un fichier BAM valide.")
            return
        bam_path = fichier_bam
        label_bam.config(text=f"{Path(bam_path).name}", fg="#799068")
        etat_bouton()

    def trouver_dossier_bam():
        nonlocal dossier_bam
        dossier_bam = filedialog.askdirectory(title="Choisir le dossier patients", initialdir=get_chemin("dossier_bam", ""))
        if not dossier_bam:
            messagebox.showwarning("Aucun dossier sélectionné", "Veuillez sélectionner un dossier contenant des fichiers BAM.")
            return
        label_dossier_bam.config(text=f"{Path(dossier_bam).name}", fg="#799068")
        etat_bouton()

    def trouver_fichier_csv():
        nonlocal csv_path
        fichier_csv = filedialog.askopenfilename(
            title="Sélectionnez le fichier CSV",
            filetypes=[("Fichier CSV", "*.csv")],
            initialdir=get_chemin("fichier_csv", ""))
        if not fichier_csv :
            messagebox.showwarning("Aucun fichier sélectionné", "Veuillez sélectionner un fichier CSV valide.")
            return
        csv_path = fichier_csv
        label_csv.config(text=f"{Path(csv_path).name}", fg="#799068")
        etat_bouton()
    
    def trouver_tableau_conco():
        nonlocal tableau_concordance
        tableau_concordance = filedialog.askopenfilename(
            title='Sélectionnez le fichier concordance',
            filetypes=[("Fichier CSV", "*.csv")],
            initialdir=get_chemin("tableau_concordance", ""))
        if not tableau_concordance :
            messagebox.showwarning("Aucun fichier sélectionné", "Veuillez sélectionner un fichier de concordance valide.")
            return
        label_tableau.config(text=f"{Path(tableau_concordance).name}", fg="#799068")
        etat_bouton()

    def reinitialiser_champs():
        nonlocal csv_path, bam_path, tableau_concordance, dossier_bam
        csv_path = bam_path = tableau_concordance = dossier_bam = ""
        for label in [label_csv, label_tableau, label_dossier_bam]:
            label.config(text=etat_initial, fg="#875346")
        etat_bouton()

    def etat_bouton():
        if (bam_path or dossier_bam) and csv_path and tableau_concordance:
            bouton4.config(state="normal")
        else:
            bouton4.config(state="disabled")

    def analyse_batch():
        samplename = get_parametre("nom_colonne_samplename", "Sample Name").strip()

        if not dossier_bam:
            if bam_path and csv_path:
                try:
                    taux, df_resultats, _ = traitement_fichier_bam(bam_path, csv_path, tableau_concordance, chemin_rapports)
                    root.quit()
                    return taux, df_resultats
                except Exception as e:
                    messagebox.showerror("Erreur d'analyse", str(e))
                    logging.error("Erreur inattendue interface :\n" + traceback.format_exc())
                    return
            else:
                messagebox.showwarning("Chemins manquants", "Veuillez sélectionner un fichier BAM, CSV et un tableau de concordance.")
                return
        else:
            liste_bam = analyse_dossier_parent(dossier_bam)
            if not liste_bam:
                messagebox.showwarning("Aucun fichier BAM trouvé", "Le dossier sélectionné ne contient aucun fichier BAM associé à un identifiant patient.")
                return

            try:
                patients_ok = []
                total_discordants = []
                progress_bar["maximum"] = len(liste_bam)
                variable_progress.set(0)
                main_frame.update_idletasks()

                for fichier_bam in liste_bam:
                    try:
                        taux, df_resultats, Patients_discordants = traitement_fichier_bam(fichier_bam, csv_path, tableau_concordance, chemin_rapports)

                        if taux is None:
                            continue

                        if Patients_discordants:
                            total_discordants.extend(Patients_discordants)
                        else:
                            patients_ok.append((fichier_bam.name, taux))

                        variable_progress.set(variable_progress.get() + 1)
                        maj_progression()
                        main_frame.update_idletasks()
                    
                    except ValueError as ve:
                        messagebox.showerror("Erreur d'analyse", str(ve))
                        logging.warning(f"Analyse interrompue à cause du blanc H2O : {ve}")
                        root.quit()
                        return
                    
                    except Exception as e:
                        logging.error(f"[ERREUR] BAM '{fichier_bam.name}' ignoré : {e}")
                        messagebox.showerror("Erreur d'analyse", str(e))
            
                resume = f"{len(patients_ok)} fichiers analysés avec succès.\n"
                resume += f"{len(total_discordants)} discordants en première instance.\n\n"

                if patients_ok:
                    resume += "Initialement concordants :\n"
                    for nom, taux in patients_ok:
                        resume += f" - {nom} : {taux:.1f}%\n"
                if total_discordants:
                    resume += "\nInitialement discordants :\n"
                    for patient, taux in total_discordants:
                        resume += f" - Pour l'ID {patient}, concordance initiale : {taux:.1f}%\n"

                messagebox.showinfo("Analyse batch terminée", resume)

                df_csv = pd.read_csv(csv_path, sep=";", dtype=str, encoding="utf-8")
                ids_bam_sans_csv, ids_csv_sans_bam = id_bam_csv(liste_bam, df_csv)
                
                resume_global_data = [
                    ("Nombre de Patients du SNPplex trouvés", len(df_csv[~df_csv[f"{samplename}"].str.contains("H2O", case=False, na=False)])),
                    ("Nombre de Fichiers BAM trouvés", len(liste_bam))]
                
                if ids_bam_sans_csv or ids_csv_sans_bam:
                    resume_global_data.extend([
                        ("ID Patients issus du SNPplex sans BAM trouvé", ", ".join(sorted(ids_csv_sans_bam)) if ids_csv_sans_bam else "Aucun"),
                        ("ID Patients BAM sans ligne dans le SNPplex correspondante", ", ".join(sorted(ids_bam_sans_csv)) if ids_bam_sans_csv else "Aucun")
                    ])
                resume_global = dict(resume_global_data)

                generer_pdf_final(chemin_rapports, config=CONFIG, resume_global=resume_global)
                root.quit()

            except Exception as e:
                messagebox.showerror("Erreur pendant l'analyse", str(e))
    
        bouton4.config(state="normal", text="Lancer l'analyse")

    def lancer_analyse():
        bouton4.config(state="disabled", text="Analyse en cours...")
        thread = threading.Thread(target=analyse_batch, daemon=True)
        thread.start()
    
    def maj_progression():
        texte_progression.set(f"{variable_progress.get()} / {progress_bar['maximum']}")

    
    root = tk.Tk()
    root.title("Comparateur BAM_SNP")
    root.configure(bg="#f6dbbc")
    center_window(root)

    
    main_frame = tk.Frame(root, bg="#f6dbbc", padx=20, pady=20)
    main_frame.pack(expand=True, fill="both")

    tk.Label(main_frame, text="Analyse de concordance BAM/SNP",
         font=("Ink Journal", 22, "bold"), bg="#f6dbbc", fg="#8d4136").grid(row=0, column=0, columnspan=2, pady=(0, 20))

    ligne = 1

    tk.Button(main_frame, text="📄 Fichier CSV", command=trouver_fichier_csv, font=("Convection", 11, 'bold'), bg="#BED3AF").grid(row=ligne, column=0, sticky="ew", padx=3, pady=5)
    label_csv = tk.Label(main_frame, text=etat_initial, font=('Convection', 9,'bold'), fg="#875346", bg="#f6dbbc")
    label_csv.grid(row=ligne, column=1, sticky="w")
    ligne += 1
    
    tk.Button(main_frame, text="📄 Tableau de concordance", command=trouver_tableau_conco, font=("Convection", 11, 'bold'), bg="#BED3AF").grid(row=ligne, column=0, sticky="ew", padx=3, pady=5)
    label_tableau = tk.Label(main_frame, text=etat_initial, font=('Convection', 9,'bold'), fg="#875346", bg="#f6dbbc")
    label_tableau.grid(row=ligne, column=1, sticky="w")
    ligne += 1

    tk.Button(main_frame, text="📁 Dossier patients", command=trouver_dossier_bam, font=("Convection", 11, 'bold'), bg="#BED3AF").grid(row=ligne, column=0, sticky="ew", padx=3, pady=5)
    label_dossier_bam = tk.Label(main_frame, text=etat_initial, font=('Convection', 9,'bold'), fg="#875346", bg="#f6dbbc")
    label_dossier_bam.grid(row=ligne, column=1, sticky="w")
    ligne += 1
    
    tk.Button(main_frame, text="📄 Fichier BAM", command=trouver_fichier_bam, font=("Convection", 11, 'bold'), bg="#BED3AF").grid(row=ligne, column=0, sticky="ew", padx=3, pady=5)
    label_bam = tk.Label(main_frame, text=etat_initial, font=('Convection', 9,'bold'), fg="#875346", bg="#f6dbbc")
    label_bam.grid(row=ligne, column=1, sticky="w")
    ligne += 1

    bouton4 = tk.Button(main_frame, text="▶ Lancer l'analyse", command=lancer_analyse, state="disabled",
                    font=("Convection", 11, 'bold'), bg="#875346", fg="white", disabledforeground="white")
    bouton4.grid(row=ligne, column=0, columnspan=2, sticky="ew", padx=3, pady=(20, 10))
    ligne += 1
    ligne += 1

    tk.Button(main_frame, text="📁 Dossier par défaut du rapport", command=ouvrir_dossier_rap, font=("Convection", 11, 'bold'), bg="#BED3AF").grid(row=ligne, column=0, columnspan=2, sticky="ew", padx=3, pady=5)
    ligne += 1

    tk.Button(main_frame, text="📁 Choisir un dossier spécifique de rapport", command=choisir_dossier_rapport, font=("Convection", 11, 'bold'), bg="#BED3AF").grid(row=ligne, column=0, sticky="ew", padx=3, pady=5)
    label_dossier_rapport = tk.Label(main_frame, text=etat_initial, font=('Convection', 9,'bold'), fg="#875346", bg="#f6dbbc")
    label_dossier_rapport.grid(row=ligne, column=1, sticky="w")
    ligne += 1

    tk.Button(main_frame, text="♻ Réinitialiser", command=reinitialiser_champs, font=("Convection", 11, 'bold'), bg="#d3b94f").grid(row=ligne, column=0, columnspan=2, sticky="ew", padx=3, pady=5)
    ligne += 1

    style = ttk.Style()
    style.layout("TProgressbar", [
        ("Horizontal.Progressbar.trough", {
            "children": [("Horizontal.Progressbar.pbar", {"side": "left", "sticky": "ns"})],
            "sticky": "ew"}),
        ("Horizontal.Progressbar.label", {"side": "left", "sticky": ""})])
    style.configure("TProgressbar", text="0 / 0", anchor="center")

    texte_progression = tk.StringVar(value="0 / 0")
    variable_progress = tk.IntVar(value=0)
    progress_bar = ttk.Progressbar(main_frame, orient="horizontal", length=300, mode="determinate", style="TProgressbar", variable=variable_progress)
    progress_bar.grid(row=ligne, column=0, columnspan=2, pady=(10, 0))
    ligne += 1
    label_progression = tk.Label(main_frame, textvariable=texte_progression, font=('Convection', 9), bg="#f6dbbc", fg="#875346")
    label_progression.grid(row=ligne, column=0, columnspan=2, pady=(0, 10))


    main_frame.mainloop()
    logging.info("Fermeture interface Tkinter.")
    logging.shutdown()
    sys.exit()

if __name__ == "__main__":

    CONFIG = charger_config()
    verifier_config(CONFIG)
    if not CONFIG:
        print("[AVERTISSEMENT] Fichier de configuration manquant ou invalide. Valeurs par défaut utilisées.")

    log_file_path = init_logging(CONFIG)
    frozen = getattr(sys, 'frozen', False)
    logging.info(f"Démarrage de Zibanitu - Comparateur Bam/Snp - (frozen={frozen})")
    logging.info(f"Fichier log : {log_file_path}")

    try:
        if len(sys.argv) > 1:
            main()
        else:
            interface()
    except Exception:
        logging.error("Crash non intercepté :\n" + traceback.format_exc())
        raise
    finally:
        logging.shutdown()
