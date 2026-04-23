build:
	cd coordo-ts && npm install && npm run build
	mkdir -p coordo-py/coordo/static/
	cp -r coordo-ts/dist/* coordo-py/coordo/static/

catalog:
	# All 4 Trees - Inventaire forestier
	uv run coordo load kobotoolbox --add data/all4trees/inventaire/20250213_Inventaire_ID_QuestionnaireK.xlsx data/all4trees/inventaire/20251017_Inventaire_ID_Donnees.xlsx --package catalog/inventaire
	uv run coordo load file --add data/all4trees/inventaire/dens_bois.csv --package catalog/inventaire
	uv run coordo add-foreignkey ind.ess_arb dens_bois.ess_arb --package catalog/inventaire
	uv run coordo load file --add data/all4trees/inventaire/inventaire_external.csv --package catalog/inventaire
	uv run coordo add-foreignkey inventaire_id._id inventaire_external.index --package catalog/inventaire
	uv run coordo load file --add data/all4trees/inventaire/dens_bois_mort.csv --package catalog/inventaire
	uv run coordo add-foreignkey ind.decomp dens_bois_mort.decomp --package catalog/inventaire
	uv run coordo load file --add data/all4trees/inventaire/constants.csv --package catalog/inventaire
	uv run coordo load file --add data/all4trees/inventaire/meteo.csv --package catalog/inventaire
	uv run coordo add-foreignkey inventaire_id.for meteo.strat --package catalog/inventaire

	# All 4 Trees - Enquête ménage
	uv run coordo load kobotoolbox --add data/all4trees/enquete/20240808_EnqueteMenage_CDF_QuestionnaireK.xlsx data/all4trees/enquete/20241007_EnqueteMenage_CDF_Donnees.csv --package catalog/enquete
	uv run coordo load file --add data/all4trees/enquete/socio_eco_gps.csv --package catalog/enquete
	uv run coordo add-foreignkey enquete_menage_cdf.admi2 socio_eco_gps.admi2 --package catalog/enquete

	# Seed - Survey
	uv run coordo load file --add data/seed/survey.zip --package catalog/seed