build:
	cd coordo-ts && npm install && npm run build
	mkdir -p coordo-py/coordo/static/
	cp -r coordo-ts/dist/* coordo-py/coordo/static/

catalog:
	# All 4 Trees - Inventaire forestier
	uv run coordo add kobotoolbox data/all4trees/inventaire_for/20260422_InventaireForestier_DonneesK.xlsx --form data/all4trees/inventaire_for/20260519_InventaireForestier_QuestionnaireK.xlsx --package catalog/inventaire_for
	uv run coordo add file data/all4trees/inventaire_for/20260422_InventaireForestier_DonneesExternes.xlsx --package catalog/inventaire_for

	uv run coordo add foreignkey adu for_dw decay decay --package catalog/inventaire_for
	uv run coordo add foreignkey inv_for for_samp proj proj --package catalog/inventaire_for
	uv run coordo add foreignkey inv_for for_pop typ typ --package catalog/inventaire_for
	uv run coordo add foreignkey inv_for for_weath loc2 loc2 --package catalog/inventaire_for
	uv run coordo add foreignkey inv_for for_soil _id _index --package catalog/inventaire_for
	uv run coordo add foreignkey adu for_sp adu_sp adu_sp --package catalog/inventaire_for
	uv run coordo add foreignkey tsbf_001 for_mf_tax1 tsbf_tax1 tax1 --package catalog/inventaire_for
	uv run coordo add foreignkey barba_001 for_mf_tax1 barbA_tax1 tax1 --package catalog/inventaire_for
	uv run coordo add foreignkey barbb_001 for_mf_tax1 barbB_tax1 tax1 --package catalog/inventaire_for
	uv run coordo add foreignkey barbc_001 for_mf_tax1 barbC_tax1 tax1 --package catalog/inventaire_for
	uv run coordo add foreignkey barbd_001 for_mf_tax1 barbD_tax1 tax1 --package catalog/inventaire_for
	uv run coordo add foreignkey tsbf_001 for_mf_tax2 tsbf_tax2 tax2 --package catalog/inventaire_for
	uv run coordo add foreignkey barba_001 for_mf_tax2 barbA_tax2 tax2 --package catalog/inventaire_for
	uv run coordo add foreignkey barbb_001 for_mf_tax2 barbB_tax2 tax2 --package catalog/inventaire_for
	uv run coordo add foreignkey barbc_001 for_mf_tax2 barbC_tax2 tax2 --package catalog/inventaire_for
	uv run coordo add foreignkey barbd_001 for_mf_tax2 barbD_tax2 tax2 --package catalog/inventaire_for
	uv run coordo add foreignkey tsbf_001 for_mf_tax3 tsbf_tax3 tax3 --package catalog/inventaire_for
	uv run coordo add foreignkey barba_001 for_mf_tax3 barbA_tax3 tax3 --package catalog/inventaire_for
	uv run coordo add foreignkey barbb_001 for_mf_tax3 barbB_tax3 tax3 --package catalog/inventaire_for
	uv run coordo add foreignkey barbc_001 for_mf_tax3 barbC_tax3 tax3 --package catalog/inventaire_for
	uv run coordo add foreignkey barbd_001 for_mf_tax3 barbD_tax3 tax3 --package catalog/inventaire_for

	# All 4 Trees - Inventaire Biologique
	uv run coordo add kobotoolbox data/all4trees/inventaire_bio/20260422_InventaireBiologique_DonneesK.xlsx --form data/all4trees/inventaire_bio/20260519_InventaireBiologique_QuestionnaireK.xlsx --package catalog/inventaire_bio
	uv run coordo add file data/all4trees/inventaire_bio/20260422_InventaireBiologique_DonneesExternes.xlsx --package catalog/inventaire_bio

	uv run coordo add foreignkey inv_bio bio_samp proj proj --package catalog/inventaire_bio
	uv run coordo add foreignkey inv_bio bio_pop year year --package catalog/inventaire_bio
	uv run coordo add foreignkey inv_001 bio_sp tax3 tax3 --package catalog/inventaire_bio

	# All 4 Trees - Enquête ménage
	uv run coordo add kobotoolbox data/all4trees/enquete/20260422_EnqueteMenage_DonneesK.csv --form data/all4trees/enquete/20260519_EnqueteMenage_QuestionnaireK.xlsx --package catalog/enquete
	uv run coordo add file data/all4trees/enquete/20260422_EnqueteMenage_DonneesExternes.xlsx --package catalog/enquete

	uv run coordo add foreignkey enquete_menage enq_samp proj proj --package catalog/enquete
	uv run coordo add foreignkey enquete_menage enq_pop typ typ --package catalog/enquete
	uv run coordo add foreignkey enquete_menage enq_gps loc2 loc2 --package catalog/enquete
	uv run coordo add foreignkey enquete_menage enq_fw fw_cod fw_cod --package catalog/enquete
	uv run coordo add foreignkey enquete_menage enq_coal coal_unit coal_unit --package catalog/enquete

	# Seed - Survey
	uv run coordo add file data/seed/survey.zip --package catalog/seed
	uv run coordo add file data/seed/suivi_sites_reboises.zip --package catalog/seed
	uv run coordo add file data/seed/ident_sites.zip --package catalog/seed
	uv run coordo add file data/seed/reboisement_id.zip --package catalog/seed
	uv run coordo add file data/seed/sensib_communautaire.zip --package catalog/seed
