#!/usr/bin/env python3
import json
from pathlib import Path

# Mapping from pipeline folder names to pipeline names in pipelines.json
pipeline_mapping = {
    "pipeline_04_customerprofilesales": "dragon_customerprofilesales",
    "pipeline_05_datarevenue": "dragon_datarevenue",
    "pipeline_06_partsharecontribution": "dragon_partsharecontribution",
    "pipeline_07_motorkux": "dragon_motorkux",
    "pipeline_08_monitoringbku": "dragon_monitoring_bku",
    "pipeline_09_monitoring_stnk_bpkb": "dragon_monitoring_stnk_bpkb",
    "pipeline_10_monitoringkuitansiall": "dragon_monitoringkuitansi_all",
    "pipeline_11_data_mekanik": "dragon_data_mekanik",
    "pipeline_13_niguri_partstock": "dragon_niguri_partstock",
    "pipeline_14_nms_handleleasing": "dragon_nms_handleleasing",
    "pipeline_15_marketsharedata": "dragon_marketsharedata",
    "pipeline_16_report_bd": "dragon_report_bd",
    "pipeline_17_astrapay": "dragon_astrapay",
    "pipeline_18_trigger_pbi_refresh": "dragon_trigger_pbi_refresh",
    "pipeline_19_ustk2": "dragon_ustk2",
    "pipeline_20_leadtimesalesheader_fromspk": "dragon_leadtimesalesheader_fromspk",
    "pipeline_21_customerpersona": "dragon_customerpersona",
    "pipeline_21_customerpersona_segmentation": "dragon_customerpersona_segmentation",
    "pipeline_23_sdue_fabric": "so2w_dragon_sdue_fabric",
    "pipeline_24_smartstock": "so2w_smartstock",
    "pipeline_25_dragon_L3": "dragon_L3",
    "pipeline_26_dragon_L2": "dragon_L2",
    "pipeline_27_dragon_L1": "dragon_L1",
    "pipeline_28_dragon_SAP": "dragon_SAP",
    "pipeline_29_dragon": "dragon",
    "pipeline_30_so2w_dragon": "so2w_dragon",
    "pipeline_31_so2w_dragon_2": "so2w_dragon_2",
    "pipeline_32_so2w_pss": "so2w_pss",
    "pipeline_33_so2w_ahass": "so2w_ahass",
    "pipeline_35_customerprofilesales_cloudera": "dragon_customerprofilesales_cloudera",
    "pipeline_astranet_file_marketsharedata": "pipeline_astranet_file_marketsharedata",
    "pipeline_astranet_file_marketsharedatatype": "pipeline_astranet_file_marketsharedatatype",
    "pipeline_astranet_file_threshold_nms": "pipeline_astranet_file_threshold_nms",
    "pipeline_customerprofilesales_delta": "customerprofilesales_delta",
    "pipeline_dbt": "dbt",
    "pipeline_dragon_l1": "dragon_dragon_l1",
    "pipeline_dragon_l2_py": "dragon_dragon_l2_py",
    "pipeline_dragons_data_merging": "dragons_data_merging",
    "pipeline_fab_dragon_customerprofilesales": "fab_dragon_customerprofilesales",
    "pipeline_grape_targetsales": "pipeline_grape_targetsales",
    "pipeline_landing_databricks_motorkux": "landing_databricks_motorkux",
    "pipeline_leads_funnel_management": "dragon_leads_funnel_management",
    "pipeline_masterunittype_star": "masterunittype_star",
    "pipeline_masterunittype_union": "masterunittype_union",
    "pipeline_prd_customerprofilesales": "prd_customerprofilesales",
    "pipeline_prd_customerprofileservice_star": "prd_customerprofileservice_star",
    "pipeline_prd_customerprofileservice_union": "prd_customerprofileservice_union",
    "pipeline_prd_leadsfunnel_crmh1": "prd_leadsfunnel_crmh1",
    "pipeline_prd_mastermaindealer": "prd_mastermaindealer",
    "pipeline_prd_pcd_h3_upload_file": "prd_pcd_h3_upload_file",
    "pipeline_prd_pkbservicefinal_integrasi": "prd_pkbservicefinal_integrasi",
    "pipeline_prd_pkbservicefinal_star___prd_pkbservicefinal_integrasi___delta_enhancement": "prd_pkbservicefinal_star___prd_pkbservicefinal_integrasi___delta_enhancement",
    "pipeline_prd_pkbservicefinal_star___prd_pkbservicefinal_integrasi___pkbservice_dr___prd_data_transaksi_pkb_dr_main___prd_data_transaksi_pkb_dr": "prd_pkbservicefinal_star___prd_pkbservicefinal_integrasi___pkbservice_dr___prd_data_transaksi_pkb_dr_main___prd_data_transaksi_pkb_dr",
    "pipeline_prd_sdue_quickwin": "prd_sdue_quickwin",
    "pipeline_prd_union_masterdealer": "prd_union_masterdealer",
    "pipeline_prd_union_mastergroupdealer": "prd_union_mastergroupdealer",
    "pipeline_prod_customerprofilesales_object_prompt_dr": "prod_customerprofilesales_object_prompt_dr",
    "pipeline_prod_mastersalesperson": "prod_mastersalesperson",
    "pipeline_prospecttossu": "dragon_prospecttossu",
    "pipeline_ro_leads": "dragon_ro_leads",
    "pipeline_sdue_datamart_quickwin": "sdue_datamart_quickwin___cpservice",
    "pipeline_synapse": "dragoncloudera_synapse",
    "pipeline_target_lcr_file": "target_lcr_file",
    "pipeline_targetsalesinout_file": "targetsalesinout_file",
    "pipeline_transformation_astranet_file_leads_ahm": "pipeline_transformation_astranet_file_leads_ahm",
}

# Load pipelines.json
with open('data/pipelines.json', 'r') as f:
    pipelines = json.load(f)

# Scan all pipeline folders in converted_scripts
base_path = Path("/Users/nioorlandotantio/Documents/work/Astra International/converted_scripts")

pipeline_file_counts = {}
for priority in ["P1", "P2", "P3"]:
    priority_path = base_path / priority
    if not priority_path.exists():
        continue

    for pipeline_dir in priority_path.glob("pipeline_*"):
        if pipeline_dir.is_dir():
            # Count actual files
            dag_files = list(pipeline_dir.rglob("*.py"))
            sql_files = list(pipeline_dir.rglob("*.sql"))
            
            pipeline_file_counts[pipeline_dir.name] = {
                "dag_count": len(dag_files),
                "sql_count": len(sql_files),
                "total_files": len(dag_files) + len(sql_files)
            }

# Update pipelines.json with actual file counts
for folder_name, counts in pipeline_file_counts.items():
    if folder_name in pipeline_mapping:
        pipeline_name = pipeline_mapping[folder_name]
        if pipeline_name in pipelines:
            print(f"Updating {pipeline_name} (from {folder_name}): total_files={counts['total_files']}, DAG={counts['dag_count']}, SQL={counts['sql_count']}")
            pipelines[pipeline_name]['total_tasks'] = counts['total_files']
            # If total_files is 0, set status_counts to empty
            if counts['total_files'] == 0:
                pipelines[pipeline_name]['status_counts'] = {}
                pipelines[pipeline_name]['tasks'] = []
        else:
            print(f"Pipeline {pipeline_name} not found in pipelines.json (from folder {folder_name})")
    else:
        print(f"No mapping for folder {folder_name}")

# Save updated pipelines.json
with open('data/pipelines.json', 'w') as f:
    json.dump(pipelines, f, indent=2)

print("pipelines.json updated with actual file counts")
