import json
from pathlib import Path

import networkx as nx


# Relationships that we currently know how to extract
# directly from the raw ESSOS SharpHound collection.
WALKABLE_RELATIONSHIPS = {
    "MemberOf",
    "Owns",
    "GenericAll",
    "GenericWrite",
    "WriteDacl",
    "WriteOwner",
    "AddKeyCredentialLink",
    "ReadGMSAPassword",
}


JSON_FILES = [
    "ESSOS_20240410083816_users.json",
    "ESSOS_20240410083816_groups.json",
    "ESSOS_20240410083816_computers.json",
    "ESSOS_20240410083816_domains.json",
    "ESSOS_20240410083816_ous.json",
    "ESSOS_20240410083816_containers.json",
    "ESSOS_20240410083816_gpos.json",
    "ESSOS_20240410083816_certtemplates.json",
    "ESSOS_20240410083816_aiacas.json",
    "ESSOS_20240410083816_enterprisecas.json",
    "ESSOS_20240410083816_ntauthstores.json",
    "ESSOS_20240410083816_rootcas.json",
]


def load_json(path):
    """Load one SharpHound JSON file."""
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)["data"]


def get_name(obj):
    """Get the BloodHound display name of an object."""
    return obj.get("Properties", {}).get(
        "name",
        obj.get("ObjectIdentifier")
    )


def build_attack_graph(data_dir):
    """
    Build a directed multigraph from the ESSOS SharpHound collection.

    Each edge stores:
        relationship
        source_name
        target_name
    """

    data_dir = Path(data_dir)

    graph = nx.MultiDiGraph()

    # ---------------------------------------------------------
    # 1. Load all available objects
    # ---------------------------------------------------------

    objects = []

    for filename in JSON_FILES:
        path = data_dir / filename

        if path.exists():
            objects.extend(load_json(path))

    # ---------------------------------------------------------
    # 2. Build object lookup
    # ---------------------------------------------------------

    object_lookup = {}

    for obj in objects:
        object_id = obj.get("ObjectIdentifier")

        if not object_id:
            continue

        object_lookup[object_id] = obj

        graph.add_node(
            object_id,
            name=get_name(obj),
        )

    # ---------------------------------------------------------
    # 3. Extract ACL relationships
    # ---------------------------------------------------------

    for target in objects:

        target_id = target.get("ObjectIdentifier")

        if not target_id:
            continue

        target_name = get_name(target)

        for ace in target.get("Aces", []):

            relationship = ace.get("RightName")
            source_id = ace.get("PrincipalSID")

            if not relationship or not source_id:
                continue

            if relationship not in WALKABLE_RELATIONSHIPS:
                continue

            # We only create the edge when the principal
            # actually exists in the collected objects.
            if source_id not in object_lookup:
                continue

            source_name = get_name(object_lookup[source_id])

            graph.add_edge(
                source_id,
                target_id,
                relationship=relationship,
                source_name=source_name,
                target_name=target_name,
                inherited=ace.get("IsInherited", False),
            )

    # ---------------------------------------------------------
    # 4. Extract group membership
    # ---------------------------------------------------------

    groups_path = data_dir / "ESSOS_20240410083816_groups.json"

    if groups_path.exists():

        groups = load_json(groups_path)

        for group in groups:

            group_id = group.get("ObjectIdentifier")

            if not group_id:
                continue

            group_name = get_name(group)

            for member in group.get("Members", []):

                member_id = member.get("ObjectIdentifier")

                if not member_id:
                    continue

                if member_id not in object_lookup:
                    continue

                member_name = get_name(object_lookup[member_id])

                graph.add_edge(
                    member_id,
                    group_id,
                    relationship="MemberOf",
                    source_name=member_name,
                    target_name=group_name,
                )

    return graph