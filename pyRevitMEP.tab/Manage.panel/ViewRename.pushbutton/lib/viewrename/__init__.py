CLASS_NAMES = ("ViewPlan", "View3D", "ViewSection", "ViewSheet", "ViewDrafting")

# Suggestions pre-filled in the editor and used as a last resort by the apply tool when
# neither the model, nor the legacy parameter, nor the user config has any pattern.
DEFAULT_PATTERNS = {
    "ViewPlan": (
        "name(ORG_Métier)_name(ORG_Métier_Sous_catégorie)_PE_bip(PLAN_VIEW_LEVEL)_bip(VIEWER_VOLUME_OF_INTEREST_CROP)"
    ),
    "View3D": "name(ORG_Métier)_name(ORG_Métier_Sous_catégorie)_3D",
    "ViewSection": "name(ORG_Métier)_name(ORG_Métier_Sous_catégorie)_CP",
}
