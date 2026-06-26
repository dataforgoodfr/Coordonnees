build:
	cd coordo-ts && npm install && npm run build
	mkdir -p coordo-py/coordo/static/
	cp -r coordo-ts/dist/* coordo-py/coordo/static/

catalog:
	# All 4 Trees - Inventaire forestier
	uv run coordo add kobotoolbox data/all4trees/inventaire_for/20260519_InventaireForestier_QuestionnaireK.xlsx data/all4trees/inventaire_for/20260422_InventaireForestier_DonneesK.xlsx --package catalog/inventaire_for
	uv run coordo add file data/all4trees/inventaire_for/20260422_InventaireForestier_DonneesExternes.xlsx --package catalog/inventaire_for

	uv run coordo add foreignkey adu.decay for_dw.decay --package catalog/inventaire_for
	uv run coordo add foreignkey inv_for.proj for_samp.proj --package catalog/inventaire_for
	uv run coordo add foreignkey inv_for.typ for_pop.typ --package catalog/inventaire_for
	uv run coordo add foreignkey inv_for.loc2 for_weath.loc2 --package catalog/inventaire_for
	uv run coordo add foreignkey inv_for._id for_soil._index --package catalog/inventaire_for
	uv run coordo add foreignkey adu.adu_sp for_sp.adu_sp --package catalog/inventaire_for
	uv run coordo add foreignkey tsbf_001.tsbf_tax1 for_mf_tax1.tax1 --package catalog/inventaire_for
	uv run coordo add foreignkey barba_001.barbA_tax1 for_mf_tax1.tax1 --package catalog/inventaire_for
	uv run coordo add foreignkey barbb_001.barbB_tax1 for_mf_tax1.tax1 --package catalog/inventaire_for
	uv run coordo add foreignkey barbc_001.barbC_tax1 for_mf_tax1.tax1 --package catalog/inventaire_for
	uv run coordo add foreignkey barbd_001.barbD_tax1 for_mf_tax1.tax1 --package catalog/inventaire_for
	uv run coordo add foreignkey tsbf_001.tsbf_tax2 for_mf_tax2.tax2 --package catalog/inventaire_for
	uv run coordo add foreignkey barba_001.barbA_tax2 for_mf_tax2.tax2 --package catalog/inventaire_for
	uv run coordo add foreignkey barbb_001.barbB_tax2 for_mf_tax2.tax2 --package catalog/inventaire_for
	uv run coordo add foreignkey barbc_001.barbC_tax2 for_mf_tax2.tax2 --package catalog/inventaire_for
	uv run coordo add foreignkey barbd_001.barbD_tax2 for_mf_tax2.tax2 --package catalog/inventaire_for
	uv run coordo add foreignkey tsbf_001.tsbf_tax3 for_mf_tax3.tax3 --package catalog/inventaire_for
	uv run coordo add foreignkey barba_001.barbA_tax3 for_mf_tax3.tax3 --package catalog/inventaire_for
	uv run coordo add foreignkey barbb_001.barbB_tax3 for_mf_tax3.tax3 --package catalog/inventaire_for
	uv run coordo add foreignkey barbc_001.barbC_tax3 for_mf_tax3.tax3 --package catalog/inventaire_for
	uv run coordo add foreignkey barbd_001.barbD_tax3 for_mf_tax3.tax3 --package catalog/inventaire_for

	# All 4 Trees - Inventaire Biologique
	uv run coordo add kobotoolbox data/all4trees/inventaire_bio/20260519_InventaireBiologique_QuestionnaireK.xlsx data/all4trees/inventaire_bio/20260422_InventaireBiologique_DonneesK.xlsx --package catalog/inventaire_bio
	uv run coordo add file data/all4trees/inventaire_bio/20260422_InventaireBiologique_DonneesExternes.xlsx --package catalog/inventaire_bio

	uv run coordo add foreignkey inv_bio.proj bio_samp.proj --package catalog/inventaire_bio
	uv run coordo add foreignkey inv_bio.year bio_pop.year --package catalog/inventaire_bio
	uv run coordo add foreignkey inv_001.tax3 bio_sp.tax3 --package catalog/inventaire_bio

	# All 4 Trees - Enquête ménage
	uv run coordo add kobotoolbox data/all4trees/enquete/20260519_EnqueteMenage_QuestionnaireK.xlsx data/all4trees/enquete/20260422_EnqueteMenage_DonneesK.csv --package catalog/enquete
	uv run coordo add file data/all4trees/enquete/20260422_EnqueteMenage_DonneesExternes.xlsx --package catalog/enquete

	uv run coordo add foreignkey enquete_menage.proj enq_samp.proj --package catalog/enquete
	uv run coordo add foreignkey enquete_menage.typ enq_pop.typ --package catalog/enquete
	uv run coordo add foreignkey enquete_menage.loc2 enq_gps.loc2 --package catalog/enquete
	uv run coordo add foreignkey enquete_menage.fw_cod enq_fw.fw_cod --package catalog/enquete
	uv run coordo add foreignkey enquete_menage.coal_unit enq_coal.coal_unit --package catalog/enquete

	# Seed - Survey
	uv run coordo add file data/seed/survey.zip --package catalog/seed
	uv run coordo add file data/seed/suivi_sites_reboises.zip --package catalog/seed
	uv run coordo add file data/seed/ident_sites.zip --package catalog/seed
	uv run coordo add file data/seed/reboisement_id.zip --package catalog/seed
	uv run coordo add file data/seed/sensib_communautaire.zip --package catalog/seed