#!/usr/bin/env python3
import os
import json

# Map folder to pipeline name
folder_map = {
    'pipeline_04_customerprofilesales': 'dragon_customerprofilesales',
    'pipeline_06_partsharecontribution': 'dragon_partsharecontribution',
    'pipeline_19_ustk2': 'dragon_ustk2',
    'pipeline_23_sdue_fabric': 'so2w_dragon_sdue_fabric',
    'pipeline_25_dragon_L3': 'dragon_L3',
    'pipeline_26_dragon_L2': 'dragon_L2',
    'pipeline_27_dragon_L1': 'dragon_L1',
    'pipeline_28_dragon_SAP': 'dragon_SAP',
    'pipeline_35_customerprofilesales_cloudera': 'dragon_customerprofilesales_cloudera',
    'pipeline_05_datarevenue': 'dragon_datarevenue',
    'pipeline_07_motorkux': 'dragon_motorkux',
    'pipeline_08_monitoringbku': 'dragon_monitoring_bku',
    'pipeline_13_niguri_partstock': 'dragon_niguri_partstock',
    'pipeline_14_nms_handleleasing': 'dragon_nms_handleleasing',
    'pipeline_15_marketsharedata': 'dragon_marketsharedata',
    'pipeline_17_astrapay': 'dragon_astrapay',
    'pipeline_18_trigger_pbi_refresh': 'dragon_trigger_pbi_refresh',
    'pipeline_20_leadtimesalesheader_fromspk': 'dragon_leadtimesalesheader_fromspk',
    'pipeline_21_customerpersona_segmentation': 'dragon_customerpersona_segmentation',
    'pipeline_24_smartstock': 'so2w_smartstock',
    'pipeline_09_monitoring_stnk_bpkb': 'dragon_monitoring_stnk_bpkb',
    'pipeline_10_monitoringkuitansiall': 'dragon_monitoringkuitansi_all',
    'pipeline_11_data_mekanik': 'dragon_data_mekanik',
    'pipeline_prospecttossu': 'dragon_prospecttossu',
    'pipeline_ro_leads': 'dragon_ro_leads',
    'pipeline_16_report_bd': 'dragon_report_bd',
    'pipeline_dbt': 'dbt',
    'pipeline_prd_leadsfunnel_crmh1': 'prd_leadsfunnel_crmh1',
    'pipeline_prd_pcd_h3_upload_file': 'prd_pcd_h3_upload_file',
    'pipeline_prd_mastermaindealer': 'prd_mastermaindealer',
    'pipeline_prd_union_masterdealer': 'prd_union_masterdealer',
    'pipeline_prd_union_mastergroupdealer': 'prd_union_mastergroupdealer',
    'pipeline_prd_customerprofilesales': 'prd_customerprofilesales',
    'pipeline_prd_customerprofileservice_star': 'prd_customerprofileservice_star',
    'pipeline_prd_customerprofileservice_union': 'prd_customerprofileservice_union',
    'pipeline_prd_pkbservicefinal_integrasi': 'prd_pkbservicefinal_integrasi',
    'pipeline_prd_sdue_quickwin': 'prd_sdue_quickwin',
    'pipeline_target_lcr_file': 'target_lcr_file',
    'pipeline_targetsalesinout_file': 'targetsalesinout_file',
    'pipeline_astranet_file_marketsharedata': 'pipeline_astranet_file_marketsharedata',
    'pipeline_astranet_file_threshold_nms': 'pipeline_astranet_file_threshold_nms',
    'pipeline_astranet_file_marketsharedatatype': 'pipeline_astranet_file_marketsharedatatype',
    'pipeline_customerprofilesales_delta': 'customerprofilesales_delta',
    'pipeline_masterunittype_star': 'masterunittype_star',
    'pipeline_masterunittype_union': 'masterunittype_union',
    'pipeline_prod_mastersalesperson': 'prod_mastersalesperson',
    'pipeline_landing_databricks_motorkux': 'landing_databricks_motorkux',
    'pipeline_synapse': 'dragoncloudera_synapse',
    'pipeline_leads_funnel_management': 'dragon_leads_funnel_management',
    'pipeline_sdue_datamart_quickwin': 'sdue_datamart_quickwin___pkbservice',
    'pipeline_grape_targetsales': 'pipeline_grape_targetsales',
    'pipeline_transformation_astranet_file_leads_ahm': 'pipeline_transformation_astranet_file_leads_ahm',
    'pipeline_dragon_l2_py': 'dragon_l2_py',
    'pipeline_fab_dragon_customerprofilesales': 'fab_dragon_customerprofilesales',
    'pipeline_prod_customerprofilesales_object_prompt_dr': 'prod_customerprofilesales_object_prompt_dr',
    'pipeline_prd_region': 'prd_region',
    'pipeline_prd_pkbservicefinal_star': 'prd_pkbservicefinal_star',
    'pipeline_sap_pssu': 'sap_pssu',
    'pipeline_sap_ustk': 'sap_ustk',
    'pipeline_sap_zmb51_fabric': 'sap_zmb51_fabric',
    'pipeline_sap_zpygsdq00010_fabric': 'sap_zpygsdq00010_fabric',
}

with open('data/pipelines.json') as f:
    pipelines = json.load(f)

updated = 0
for p in ['P1', 'P2', 'P3']:
    base = f'../converted_scripts/{p}'
    if not os.path.exists(base):
        continue
    for folder in os.listdir(base):
        path = os.path.join(base, folder)
        if not os.path.isdir(path):
            continue
        
        # Count files
        files = 0
        for r, d, fs in os.walk(path):
            files += len([f for f in fs if f.endswith(('.sql', '.py'))])
        
        if files == 0:
            continue
        
        # Get pipeline name
        pipe_name = folder_map.get(folder, folder.replace('pipeline_', ''))
        
        if pipe_name not in pipelines:
            print(f"[SKIP] {folder} -> {pipe_name} not in pipelines.json")
            continue
        
        pipe = pipelines[pipe_name]
        old_done = pipe.get('status_counts', {}).get('Done', 0)
        total = pipe.get('total_tasks', len(pipe.get('tasks', [])))
        skip = pipe.get('status_counts', {}).get('SKIP', 0)
        countable = total - skip
        
        if countable <= 0:
            continue
        
        # Update Done count based on converted files (cap at countable)
        new_done = min(files, countable)
        
        if new_done > old_done:
            belum = countable - new_done
            pipe['status_counts'] = {'Done': new_done}
            if skip > 0:
                pipe['status_counts']['SKIP'] = skip
            if belum > 0:
                pipe['status_counts']['Belum Convert'] = belum
            print(f"[{p}] {pipe_name}: Done {old_done} -> {new_done} (files={files}, total={total}, skip={skip})")
            updated += 1

with open('data/pipelines.json', 'w') as f:
    json.dump(pipelines, f, indent=2)

print(f"\nUpdated {updated} pipelines")

# Summary
total = sum(p.get('total_tasks', 0) for p in pipelines.values())
done = sum(p.get('status_counts', {}).get('Done', 0) for p in pipelines.values())
skip = sum(p.get('status_counts', {}).get('SKIP', 0) for p in pipelines.values())
print(f"\nTotal tasks: {total}")
print(f"Done: {done}")
print(f"SKIP: {skip}")
print(f"Total Tasks (excl SKIP): {total - skip}")
