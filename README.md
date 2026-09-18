# Zibanitu
BAM Files and CSV File comparison
** ZIBANITU : COMPARATEUR BAM/SNPplex **

------------------------------------------ FRENCH VERSION -------------------------------------------------------

A partir d'un répertoire contenant des fichiers BAM, d'un SNPplex.csv regroupant sur chaque ligne les SNP de patients dont on veut confirmer l'identité et d'un tableau de concordance.csv regroupant les positions les plus fréquemment observées ; l'executable compare le génotype observé dans le bam et celui observé dans le fichier csv du patient correspondant, pour les SNP du tableau de concordance donné.
Il rend un taux de concordance entre les deux fichiers (bam et SNPplex) et si ce taux est inférieur strict à 80%, il compare le fichier bam aux autres lignes du SNPplex.csv afin de relever une possible erreur d'étiquetage du patient.
 
En sortie, il produit un rapport global sous l'intitulé "global_report_IV_{date_de_la_comparaison}" et un fichier csv intitulé "detailed_report_{date}".

Dans le rapport global, chaque ligne représente la comparaison pour un patient donné.
Il se compose de 7 colonnes :
 - Patient_ID : Identité du patient récupéré du fichier BAM
 - Rate : ratio de concordance entre le génotype du csv et celui du BAM divisé par le nombre total de SNP extraits du tableau de concordance.
 - Match State : Si le ratio est supérieur à 12/15, l'indicateur visuel considère que la concordance est effective. Sinon, une croix y apparaît.
 - Match : joue le même rôle que l'indicateur visuel mais sous forme verbeuse.
 - Depth : indique si la profondeur de lecture est suffisante - supérieure à 15 actuellement - et affiche "LOW" dans le cas contraire.
 - Bases low depth : si la profondeur de lecteur est insuffisante, affiche les bases concernées (chr:position - génotype (profondeur observée)).
 - REMARQUES : affiche 2 choses en particulier. 
	1/ Si le bam et le csv sont discordants mais que le bam semble concordant avec un autre csv, on obtient dans cette cas "ATTENTION Possible inversion avec {ID du patient avec lequel l'inversion semble avoir lieu (taux : {taux} %)}".
	2/ Si des allèles sont manquants dans le fichier csv du SNPplex, la case retourne "Positions manquantes dans le SNPplex : {chr}:{position}"  

Dans le rapport détaillé, on retrouve l'ensemble des analyses pour chaque patient avec chaque ligne représentant une position du SNPplex.
On y retrouve l4 colonnes :
 - ID_Patient_BAM
 - SNP_ID : sous la forme {rang}_{chromosome}
 - CHROM : le chromosome concerné
 - POS : la position concernée
 - GT_CSV : le génotype du csv
 - GT_BAM : le génotype du BAM
 - Match : "OK" si concordant, "DISCORDANT" sinon.
 - Depth
 - Bases : toutes les bases observées à cette position (pas uniquement les deux majoritaires).
 - Visuel : indicateur visuel de la concordance
 - Depth Indicator : indicateur de la profondeur
 - ID_Patient_Alternatif : si le fichier BAM et CSV ont une concordance inférieure à 80%, cette colonne retourne l'ID du patient alternatif dont le CSV correspond davantage au fichier BAM initial.
 - Taux_alternatif
 - Match_State

L'utilisation est possible en ligne de commande (CLI) ou via une interface utilisateur (GUI).


**Structure du dossier**

SNP_Comparateur/
├── Zibanitu.exe						      ← ou .py si non compilé
├── config.yaml							      ← Fichier de configuration
├── tableau_concordance.csv      			  ← Table de correspondance Rang / Chromosome / Position
├── README.txt/md                 			  ← Fichier actuellement ouvert
├── rapports/                    			  ← Créé automatiquement à l'exécution


**Configuration (config.yaml)**

Tous les chemins et paramètres de l’outil sont définis dans - config.yaml - :

chemins:
  dossier_rapports_par_defaut: "C:/.../Identitovigilance_{date}"	← Emplacement du dossier de rapports
  dossier_csv: "N:/.../CSV_FOLDER"									← Emplacement du fichier CSV
  dossier_bam: "\\...\BAM\PATH"										← Emplacement du dossier des runs avec les fichiers BAM
  tableau_concordance: "N:/.../tableau_concordance.csv"				← Emplacement du tableau de concordance

parametres:
  profondeur_min: 15          		← Profondeur minimale pour un SNP fiable
  seuil_confiance: 0.75       		← Seuil pour appeler un homozygote
  taux_defini : 80 (en pourcentage)	← Taux de concordance défini
  nom_colonne_position : "hg38"		← Intitulé de la colonne regroupant les positions des SNPplex dans le tableau de concordance
  nom_colonne_chr : "Chr"		← Intitulé de la colonne regroupant les chromosomes des SNPplex dans le tableau de concordance

Les chemins et les paramètres du fichier config.yaml sont modifiables. 
!!!! ATTENTION La présentation doit rester la même (par exemple le seuil de confiance est normalisé donc si on change le seuil, il faut qu'il soit établi entre 0 et 1). 
!!!! ATTENTION Les chemins ont deux écritures possibles mais toujours entre guillemets : 
 - écriture avec un backslash : toujours doubler le nombre de backslash sinon, l'executable plantera. C'est l'écriture naturelle de Windows, donc lorsque l'on copie le chemin pour le coller dans le fichier, on double bien chaque backslash.
 - écriture avec slash forward : possible mais déconseillé pour éviter de vous embrouiller. Si vous faites un copier-coller, pas besoin de doubler les slashs mais il faut les orienter dans l'autre sens.


**Utilisation via interface graphique**

Double-cliquer sur **Zibanitu.exe**
Ou lancer via Python :

    python Zibanitu.py

Interface :
- Sélection du fichier CSV
- Sélection du fichier BAM ou du dossier patients
- Sélection du tableau de concordance
- Lancement de l’analyse
- Résultats enregistrés en CSV et PDF dans un dossier de rapport

**Utilisation en ligne de commande**

Exemple fichier unique :

    python Zibanitu.py --bam_path chemin/fichier.bam --csv_path chemin/fichier.csv  --tableau_concordance chemin/concordance.csv 

Exemple en mode batch (dossier complet) :

    python Zibanitu.py --dossier_bam chemin/dossier/ --csv_path chemin/fichier.csv  --tableau_concordance chemin/concordance.csv

**Sorties**

- Un rapport détaillé 'detailed_report_{date}.csv' qui regroupe tous les résultats détaillés
- Un fichier 'global_report_{date}.pdf' qui regroupe les résultats globaux
- Tous les rapports sont stockés dans le dossier configuré

**Pré-requis (si non compilé)**

- Python ≥ 3.8
- Modules : pandas, bamnostic, tkinter, PyYAML, biopython, reportlab

Installation :

    pip install -r requirements.txt

Si besoin de compiler, il faut installer le module PyInstaller via : 
  pip install pyinstaller

** DEBUGGAGE **

En cas d'erreur ou de problèmes avec l'executable, un fichier log l'accompagne et se trouve normalement dans le même dossier. Il permet de suivre l'analyse pour essayer de déterminer la cause de l'erreur.
Ce fichier log est intitulé JOURNAL et s'ouvre dans un éditeur de texte de type NOTEPAD ou Bloc-notes.
Il permet de suivre chaque analyse et enregistre tous les logs qu'ils soient de type logging.INFO jusqu'à logging.ERROR.
Ce journal est écrasé à chaque lancement de l'executable pour éviter de surcharger ce fichier.

**Affichage console pour DEBUGGAGE**

Dans le cas où une erreur survient mais n'est pas affiché dans l'interface graphique (la fenêtre visuelle), il est possible d'obtenir la console avec les sorties PRINT. 

!! ATTENTION : pour faire cela, il est nécessaire de pouvoir compiler à nouveau le script après la modification !!
Il faut donc disposer d'un éditeur de code source ou un éditeur + un compilateur ET il faut installer PyInstaller pour pouvoir compiler le fichier Zibanitu.spec.

Pour ce faire : 
 - Ouvrir le fichier Zibanitu.spec dans un éditeur de texte.
 - Dans " exe = EXE( [...] )", chercher "console=False" et remplacer par "console=True".
 - Sauvegarder et fermer le fichier.
Pour compiler à nouveau :
 - Dans un terminal de commande (powershell ou cmd), se placer dans le dossier contenant le fichier Zibanitu.spec. 
 - Pour cela : cd "C:\Exemple\De\Chemin"
 - Puis entrer : & "C:\Exemple\De\Chemin" PyInstaller Zibanitu.spec

L'executable sera mis à jour et la console s'affichera en fond.


------------------------------------------ ENGLISH VERSION -------------------------------------------------------


# Zibanitu
BAM Files and CSV File comparison
** ZIBANITU : COMPARATEUR BAM/SNPplex **

Given a directory containing BAM files, an SNPplex.csv file listing on each line the SNPs of patients whose identities you want to confirm, and a concordance.csv table listing the most frequently observed positions; the executable compares the genotype observed in the BAM file with the one observed in the corresponding patient’s CSV file for the SNPs listed in the given concordance table.
It returns a concordance rate between the two files (BAM and SNPplex), and if this rate is strictly less than 80%, it compares the BAM file to the other rows in the SNPplex.csv file to identify a possible patient mislabeling error.

As output, it generates a summary report titled “global_report_IV_{comparison_date}” and a CSV file titled “detailed_report_{date}”.

In the global report, each row represents the comparison for a given patient.
It consists of 7 columns :
 - Patient_ID : patient identity retrieved from the BAM file.
 - Rate : concordance ratio between the genotype in the CSV file and that in the BAM file, divided by the total number of extracted SNP from the concordance table.
 - Match State : If the ratio is greater than 12 out of 15 SNPs, visual indicator considers the match to be valid. Otherwise, cross appears there.
 - Match: serves the same purpose as the visual indicator but in verbose form.
 - Depth: indicates whether the read depth is sufficient—currently greater than 15—and displays “LOW” if it is not.
 - Low-depth bases: If the read depth is insufficient, displays the affected bases (chr:position - genotype (observed depth)).
 - NOTES: Displays two specific items.
	1/ If the BAM and CSV files are inconsistent but the BAM appears to match another CSV file, the message “WARNING: Possible inversion with {ID of the patient with whom the inversion appears to occur (rate: {rate} %)}” is displayed.
	2/ If alleles are missing from the SNPplex CSV file, the box returns “Missing positions in SNPplex: {chr}:{position}”


The detailed report contains all the analyses for each patient, with each row representing a SNPplex position.
It contains the following 14 columns:
 - ID_Patient_BAM
 - SNP_ID: in the format {rank}_{chromosome}
 - CHROM: the chromosome in question
 - POS: the position in question
 - GT_CSV: the genotype from the CSV file
 - GT_BAM: the genotype from the BAM file
 - Match: “OK” if matching, “DISCORDANT” otherwise.
 - Depth
 - Bases: all bases observed at this position (not just the two most frequent ones).
 - Visual: visual indicator of agreement
 - Depth Indicator: depth indicator
 - Alternative_Patient_ID: if the BAM and CSV files have less than 80% agreement, this column returns the ID of the alternative patient whose CSV file matches the original BAM file more closely.
 - Alternative_Rate
 - Match_State

The tool can be used via the command line (CLI) or through a graphical user interface (GUI).


**Folder Structure**

SNP_Comparator/
├── Zibanitu.exe                              							← or .py if not compiled
├── config.yaml                                 	 					← Configuration file
├── correspondence_table.csv                    						← Correspondence table: Rank / Chromosome / Position
├── README.txt/md                               						← File currently open
├── reports/                                  							← Created automatically upon execution


**Configuration (config.yaml)**

All paths and settings for the tool are defined in - config.yaml - :

paths:
  default_reports_folder: “C:/.../Identitovigilance_{date}”				← Location of the reports folder
  csv_folder: “N:/.../CSV_FOLDER”                                    	← Location of the CSV file
  bam_folder: “\\...\BAM\PATH”                                       	← Location of the runs folder containing the BAM files
  alignment_table: “N:/.../alignment_table.csv”               	 		← Location of the alignment table

parameters:
  min_depth: 15                  										← Minimum depth for a reliable SNP
  confidence_threshold: 0.75       										← Threshold for classifying a homozygote
  defined_rate: 80 (as a percentage)									← Defined concordance rate
  position_column_name: “hg38”        									← Name of the column containing the SNPplex positions in the concordance table
  chr_column_name: “Chr”        										← Name of the column containing the chromosomes of the SNPplexes in the concordance table


The paths and parameters in the config.yaml file can be modified.
!!!! WARNING: The format must remain the same (for example, the confidence threshold is normalized, so if you change the threshold, it must be between 0 and 1).
!!!! WARNING: Paths can be written in two ways, but must always be enclosed in quotation marks:
 - Backslash notation: Always double the number of backslashes; otherwise, the executable will crash. This is the standard Windows notation, so when you copy the path to paste it into the file, be sure to double each backslash.
 - Forward slash notation: possible but not recommended to avoid confusion. If you copy and paste, you don’t need to double the slashes, but you must reverse their direction.


**Using the Graphical User Interface**

Double-click **Zibanitu.exe**
Or run it via Python:

    python Zibanitu.py

Interface:
- Select the CSV file
- Select the BAM file or the patients folder
- Select the alignment table
- Run the analysis
- Results saved as CSV and PDF in a report folder

**Command-Line Usage**

Example for a single file:

    python Zibanitu.py --bam_path path/file.bam --csv_path path/file.csv  --mapping_table path/mapping.csv

Batch mode example (entire folder):

    python Zibanitu.py --bam_folder path/folder/ --csv_path path/file.csv  --alignment_table path/alignment.csv

**Output**

- A detailed report ‘detailed_report_{date}.csv’ containing all detailed results
- A file ‘global_report_{date}.pdf’ containing the overall results
- All reports are stored in the configured folder

**Prerequisites (if not pre-compiled)**

- Python ≥ 3.8
- Modules: pandas, bamnostic, tkinter, PyYAML, biopython, reportlab

Installation:

    pip install -r requirements.txt

If compilation is required, install the PyInstaller module using:
  pip install pyinstaller

**DEBUGGING**

If an error or problem occurs with the executable, a log file is generated and is normally located in the same folder. This log file allows you to track the analysis to try to determine the cause of the error.
This log file is named JOURNAL and can be opened in a text editor such as NOTEPAD or Notepad.

It allows you to track each analysis and records all logs, ranging from logging.INFO to logging.ERROR.
This log is overwritten each time the executable is launched to prevent the file from becoming too large.

**Console Output for Debugging**

If an error occurs but is not displayed in the graphical user interface (the visual window), you can view the console output containing the PRINT statements.
!! WARNING: To do this, you must be able to recompile the script after making changes !!
You must therefore have a source code editor or an editor plus a compiler, AND you must install PyInstaller to be able to compile the Zibanitu.spec file.

To do this:
 - Open the Zibanitu.spec file in a text editor.
 - In “exe = EXE( [...] )”, find “console=False” and replace it with “console=True”.
 - Save and close the file.

To recompile:
 - In a command prompt (PowerShell or cmd), navigate to the folder containing the Zibanitu.spec file.
 - To do this: cd “C:\Example\Path”
 - Then enter: & “C:\Example\Path” PyInstaller Zibanitu.spec

The executable will be updated and the console will appear in the background.

Auteur
---------
Créé par Elza Bersanoukaeva dans le cadre du stage au laboratoire de génétique - sous la direction du Docteur Francou Bruno
Date : Juillet 2025
