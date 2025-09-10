# Zibanitu
BAM Files and CSV File comparison
** ZIBANITU : COMPARATEUR BAM/SNPplex **

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
├── tableau_concordance.csv      	← Table de correspondance Rang / Chromosome / Position
├── README.txt/md                 ← Fichier actuellement ouvert
├── rapports/                    	← Créé automatiquement à l'exécution



**Configuration (config.yaml)**

Tous les chemins et paramètres de l’outil sont définis dans - config.yaml - :

chemins:
  dossier_rapports_par_defaut: "C:/.../Identitovigilance_{date}"	← Emplacement du dossier de rapports
  dossier_csv: "N:/.../EXOME Illumina"					← Emplacement du fichier CSV
  dossier_bam: "\\...\Cytogenetique\runs_nextseq1000"			← Emplacement du dossier des runs avec les fichiers BAM
  tableau_concordance: "N:/.../tableau_concordance.csv"			← Emplacement du tableau de concordance

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


Auteur
---------
Créé par Elza Bersanoukaeva dans le cadre du stage au laboratoire de génétique - sous la direction du Docteur Francou Bruno
Date : Juillet 2025
