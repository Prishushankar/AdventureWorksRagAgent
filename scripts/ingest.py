import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

load_dotenv()

from data.schema_data import TABLE_DESCRIPTIONS, TABLE_FOREIGN_KEYS, BUSINESS_LOGIC, VIEW_DESCRIPTIONS


def ingest_all() -> None:
    chroma_db_path = os.environ.get("CHROMA_DB_PATH", "./chroma_db")
    embedding_model = os.environ.get("EMBEDDING_MODEL", "BAAI/bge-base-en-v1.5")

    print(f"Starting schema ingestion into ChromaDB at {chroma_db_path}\n")

    chroma_client = chromadb.PersistentClient(path=chroma_db_path)
    hf_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=embedding_model,
    )
    collection = chroma_client.get_or_create_collection(
        name="adventureworks_schema",
        embedding_function=hf_ef,
    )

    print("--- Pass 1: Embedding Table Descriptions ---")
    for table_name, description in TABLE_DESCRIPTIONS.items():
        fk_list = TABLE_FOREIGN_KEYS.get(table_name, [])
        fk_strings = [
            f"{fk['column']}->{fk['references_table']}.{fk['references_column']}"
            for fk in fk_list
        ]
        fk_block = ",".join(fk_strings) if fk_strings else "none"

        document_text = (
            f"TBL:{table_name}|"
            f"PURP:{description}|"
            f"FKS:{fk_block}"
        )

        collection.upsert(
            ids=[f"table::{table_name}"],
            documents=[document_text],
            metadatas=[{
                "type": "table",
                "table_name": table_name,
                "schema": table_name.split(".")[0] if "." in table_name else "dbo",
            }],
        )
        print(f"  Table: {table_name}")

    print(f"\nTables done: {len(TABLE_DESCRIPTIONS)}")

    print("\n--- Pass 2: Embedding Business Logic Rules ---")
    for rule_name, rule_text in BUSINESS_LOGIC.items():
        document_text = f"RULE:{rule_name}|DETAIL:{rule_text}"
        collection.upsert(
            ids=[f"rule::{rule_name}"],
            documents=[document_text],
            metadatas=[{"type": "rule", "rule_name": rule_name}],
        )
        print(f"  Rule: {rule_name}")

    print(f"\nRules done: {len(BUSINESS_LOGIC)}")

    print("\n--- Pass 3: Embedding View Descriptions ---")
    for view_name, view_desc in VIEW_DESCRIPTIONS.items():
        document_text = f"VIEW:{view_name}|PURP:{view_desc}"
        collection.upsert(
            ids=[f"view::{view_name}"],
            documents=[document_text],
            metadatas=[{
                "type": "view",
                "view_name": view_name,
                "schema": view_name.split(".")[0],
            }],
        )
        print(f"  View: {view_name}")

    print(f"\nViews done: {len(VIEW_DESCRIPTIONS)}")

    yaml_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "config",
        "schema_adventureworks.yaml",
    )
    yaml_path = os.path.normpath(yaml_path)

    if os.path.exists(yaml_path):
        print(f"\n--- Pass 4: Supplementing from YAML ({yaml_path}) ---")
        with open(yaml_path, "r", encoding="utf-8") as f:
            yaml_data = yaml.safe_load(f)

        tables = yaml_data.get("tables", {})
        for table_name, table_meta in tables.items():
            yaml_desc = table_meta.get("description", "").strip()
            biz_logic_list = table_meta.get("business_logic", [])
            biz_logic_str = " | ".join(biz_logic_list) if biz_logic_list else ""

            if yaml_desc or biz_logic_str:
                document_text = (
                    f"TBL:{table_name}|"
                    f"YAML_DESC:{yaml_desc}|"
                    f"BIZ_LOGIC:{biz_logic_str}"
                )
                collection.upsert(
                    ids=[f"yaml::{table_name}"],
                    documents=[document_text],
                    metadatas=[{"type": "yaml_supplement", "table_name": table_name}],
                )
                print(f"  YAML supplement: {table_name}")
    else:
        print(f"\nYAML not found at {yaml_path} — skipping Pass 4.")

    total = (
        len(TABLE_DESCRIPTIONS)
        + len(BUSINESS_LOGIC)
        + len(VIEW_DESCRIPTIONS)
    )
    print(f"\nIngestion complete! {total} documents embedded into collection 'adventureworks_schema'.")
    print(f"   Tables : {len(TABLE_DESCRIPTIONS)}")
    print(f"   Rules  : {len(BUSINESS_LOGIC)}")
    print(f"   Views  : {len(VIEW_DESCRIPTIONS)}")


if __name__ == "__main__":
    ingest_all()
